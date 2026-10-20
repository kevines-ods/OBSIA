#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Le dépôt de données du coffre (§7.1) : un seul écrivain, une poussée notée,
une fraîcheur vérifiable.

Ces tests montent de vrais dépôts git dans un dossier temporaire — un distant
nu local tient lieu de NAS — et jugent le script par ses codes de sortie.
"""

import datetime as dt
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import depot_de_donnees as DD      # noqa: E402
import modules as MOD              # noqa: E402


def git(ou, *arguments):
    return subprocess.run(["git", "-C", str(ou), *arguments],
                          capture_output=True, text=True, check=False)


#: Un faux vérificateur : il note ses arguments, puis sort du code qu'on lui dit.
STUB = '''\
import pathlib, sys
ici = pathlib.Path(__file__).resolve().parent
(ici / "appele").write_text(" ".join(sys.argv[1:]), encoding="utf-8")
sys.exit(int((ici / "code").read_text().strip()))
'''


class BaseDepot(unittest.TestCase):
    def setUp(self):
        self.parent = Path(tempfile.mkdtemp(prefix="obsia-test-depot-"))
        self.addCleanup(shutil.rmtree, self.parent, ignore_errors=True)
        self.produit = self.parent / "OBSIA"
        (self.produit / "scripts").mkdir(parents=True)
        self.vault = self.parent

    def juger(self, fonction, *arguments):
        """Appelle le script en étouffant son bavardage : on juge son code.

        La fenêtre d'anti-rebond est annulée : ces tests jugent le code, pas le
        temps d'attente. L'attente elle-même est jugée plus bas, séparément.
        """
        with mock.patch.dict(os.environ, {DD.VARIABLE_REBOND: "0"}):
            with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                return fonction(*arguments)

    def ecrire_profil(self, **champs):
        lignes = ["%s: %s" % (cle, valeur) for cle, valeur in champs.items()]
        (self.produit / MOD.NOM_PROFIL).write_text("\n".join(lignes) + "\n",
                                                   encoding="utf-8")

    def ecrire_verificateur(self, code: int):
        dossier = self.produit / "scripts"
        (dossier / "verifier_coffre.py").write_text(STUB, encoding="utf-8")
        (dossier / "code").write_text(str(code), encoding="utf-8")

    def amorcer(self, distant: Path | None = None):
        """Un dépôt de données minimal, avec un commit, et son distant s'il y en a."""
        git(self.vault, "init", "--quiet")
        git(self.vault, "config", "user.email", "test@exemple.invalid")
        git(self.vault, "config", "user.name", "Test")
        (self.vault / "0-PROJETS").mkdir(parents=True, exist_ok=True)
        (self.vault / "0-PROJETS" / "note.md").write_text("Corps.\n", encoding="utf-8")
        git(self.vault, "add", "-A")
        git(self.vault, "commit", "--quiet", "-m", "amorce")
        if distant is not None:
            git(self.vault, "remote", "add", "origin", str(distant))

    def distant_nu(self) -> Path:
        nu = self.parent / "coffre.git"
        subprocess.run(["git", "init", "--bare", "--quiet", str(nu)],
                       capture_output=True, text=True, check=False)
        return nu


class TestEcrivainUnique(BaseDepot):
    """§7.1 : la mémoire s'écrit depuis une seule machine, celle du profil."""

    def test_l_ecrivain_declare_est_accepte(self):
        self.ecrire_profil(ecrivain=MOD.nom_machine())
        self.assertEqual(0, self.juger(DD.verifier_ecrivain, self.produit))

    def test_une_autre_machine_est_refusee(self):
        self.ecrire_profil(ecrivain="une-autre-machine")
        self.assertEqual(1, self.juger(DD.verifier_ecrivain, self.produit))

    def test_sans_ecrivain_declare_le_controle_avertit(self):
        self.ecrire_profil(distribution="debian")
        self.assertEqual(0, self.juger(DD.verifier_ecrivain, self.produit))


class TestAvantCommit(BaseDepot):
    """Le pre-commit du dépôt de données : l'écrivain, puis les carnets."""

    def test_le_controle_des_carnets_est_appele_sur_le_coffre(self):
        self.ecrire_profil(ecrivain=MOD.nom_machine())
        self.ecrire_verificateur(0)
        self.assertEqual(0, self.juger(DD.avant_commit, self.vault, self.produit))
        appele = (self.produit / "scripts" / "appele").read_text(encoding="utf-8")
        self.assertEqual("--coffre %s --carnets" % self.vault, appele)

    def test_un_carnet_fautif_refuse_le_commit(self):
        self.ecrire_profil(ecrivain=MOD.nom_machine())
        self.ecrire_verificateur(1)
        self.assertEqual(1, self.juger(DD.avant_commit, self.vault, self.produit))

    def test_un_ecrivain_etranger_arrete_avant_le_controle(self):
        self.ecrire_profil(ecrivain="une-autre-machine")
        self.ecrire_verificateur(0)
        self.assertEqual(1, self.juger(DD.avant_commit, self.vault, self.produit))
        self.assertFalse((self.produit / "scripts" / "appele").exists())

    def test_un_verificateur_absent_n_empeche_pas_le_commit(self):
        self.ecrire_profil(ecrivain=MOD.nom_machine())
        self.assertEqual(0, self.juger(DD.avant_commit, self.vault, self.produit))


class TestApresCommit(BaseDepot):
    """§7.1 : la poussée part après le commit, et son succès est daté."""

    def test_la_poussee_va_au_distant_et_note_l_instant(self):
        self.amorcer(distant=self.distant_nu())
        self.assertEqual(0, self.juger(DD.apres_commit, self.vault))
        marque = self.vault / ".git" / DD.FICHIER_DERNIERE_POUSSEE
        self.assertTrue(marque.is_file())
        branches = git(self.parent / "coffre.git", "branch", "--list").stdout
        self.assertTrue(branches.strip(), "le distant aurait dû recevoir une branche")

    def test_sans_distant_rien_ne_part_et_rien_n_est_note(self):
        self.amorcer()
        self.assertEqual(0, self.juger(DD.apres_commit, self.vault))
        self.assertFalse((self.vault / ".git" / DD.FICHIER_DERNIERE_POUSSEE).exists())

    def test_un_distant_injoignable_journalise_sans_lever(self):
        self.amorcer(distant=self.parent / "distant-inexistant" / "coffre.git")
        self.assertEqual(1, self.juger(DD.apres_commit, self.vault))
        journal = self.vault / ".git" / DD.FICHIER_JOURNAL
        self.assertTrue(journal.is_file())
        self.assertTrue(journal.read_text(encoding="utf-8").strip())


class TestPousseeSerializee(BaseDepot):
    """§7.1 : une salve de commits ne fait pas une salve de poussées."""

    def test_la_variable_suspend_la_poussee(self):
        self.amorcer(distant=self.distant_nu())
        os.environ[DD.VARIABLE_SUSPENSION] = "0"
        self.addCleanup(os.environ.pop, DD.VARIABLE_SUSPENSION, None)
        self.assertEqual(0, self.juger(DD.apres_commit, self.vault))
        self.assertFalse((self.vault / ".git" / DD.FICHIER_DERNIERE_POUSSEE).exists())
        self.assertFalse(git(self.parent / "coffre.git", "branch", "--list").stdout.strip())

    def test_la_marque_suspend_la_poussee(self):
        self.amorcer(distant=self.distant_nu())
        (self.vault / ".git" / DD.FICHIER_SUSPENSION).write_text("rebase en cours\n",
                                                                 encoding="utf-8")
        self.assertEqual(0, self.juger(DD.apres_commit, self.vault))
        self.assertFalse((self.vault / ".git" / DD.FICHIER_DERNIERE_POUSSEE).exists())
        self.assertFalse(git(self.parent / "coffre.git", "branch", "--list").stdout.strip())

    @unittest.skipIf(DD.fcntl is None, "flock indisponible sur cette plateforme")
    def test_un_verrou_deja_tenu_ecarte_la_poussee(self):
        """Le second pousseur sort sans attendre : la salve du premier vaut pour lui."""
        self.amorcer(distant=self.distant_nu())
        tenu = (self.vault / ".git" / DD.FICHIER_VERROU).open("a", encoding="utf-8")
        self.addCleanup(tenu.close)
        DD.fcntl.flock(tenu.fileno(), DD.fcntl.LOCK_EX | DD.fcntl.LOCK_NB)
        self.assertEqual(0, self.juger(DD.apres_commit, self.vault))
        self.assertFalse(git(self.parent / "coffre.git", "branch", "--list").stdout.strip())

    def test_le_verrou_est_relache_apres_la_poussee(self):
        self.amorcer(distant=self.distant_nu())
        self.assertEqual(0, self.juger(DD.apres_commit, self.vault))
        repris = DD.tenter_verrou(self.vault / ".git")
        try:
            self.assertIsNotNone(repris, "le verrou doit être libre après la poussée")
        finally:
            if repris is not None:
                repris.close()

    def test_un_commit_arrive_pendant_la_poussee_est_rattrape(self):
        """La pointe a bougé pendant la poussée : on repart pour un tour."""
        self.amorcer(distant=self.distant_nu())
        vrai = DD.pousser_vers_le_distant
        poussees = []

        def pousse_en_ajoutant_un_commit(coffre, git_dir, branche):
            poussees.append(branche)
            code = vrai(coffre, git_dir, branche)
            if len(poussees) == 1:      # un commit atterrit pendant la poussée
                (self.vault / "0-PROJETS" / "note.md").write_text("Suite.\n",
                                                                  encoding="utf-8")
                git(self.vault, "add", "-A")
                git(self.vault, "commit", "--quiet", "-m", "pendant la poussée")
            return code

        with mock.patch.object(DD, "pousser_vers_le_distant",
                               pousse_en_ajoutant_un_commit):
            self.assertEqual(0, self.juger(DD.apres_commit, self.vault))
        self.assertEqual(2, len(poussees), "une pointe qui bouge relance une poussée")
        self.assertEqual(git(self.vault, "rev-parse", "HEAD").stdout.strip(),
                         git(self.parent / "coffre.git", "rev-parse", "HEAD").stdout.strip())

    def test_la_fenetre_de_rebond_se_regle_par_l_environnement(self):
        with mock.patch.dict(os.environ, {DD.VARIABLE_REBOND: "1.5"}):
            self.assertEqual(1.5, DD.fenetre_de_rebond())
        with mock.patch.dict(os.environ, {DD.VARIABLE_REBOND: "pas un nombre"}):
            self.assertEqual(DD.FENETRE_REBOND, DD.fenetre_de_rebond())

    @unittest.skipIf(DD.fcntl is None, "flock indisponible sur cette plateforme")
    def test_un_echec_du_detenteur_est_repousse(self):
        """Un hoquet du distant ne condamne plus toute la salve (reprise bornée)."""
        self.amorcer(distant=self.distant_nu())
        vraie = DD.pousser_vers_le_distant
        essais = []

        def echoue_une_fois(coffre, git_dir, branche):
            essais.append(branche)
            return 1 if len(essais) == 1 else vraie(coffre, git_dir, branche)

        with mock.patch.object(DD, "pousser_vers_le_distant", echoue_une_fois):
            self.assertEqual(0, self.juger(DD.apres_commit, self.vault))
        self.assertEqual(2, len(essais), "la poussée échouée doit être retentée")
        self.assertTrue((self.vault / ".git" / DD.FICHIER_DERNIERE_POUSSEE).is_file())

    def test_une_salve_inachevee_se_distingue_du_succes(self):
        """Le plafond de tours atteint n'est pas un succès déguisé."""
        self.amorcer(distant=self.distant_nu())
        vraie = DD.pousser_vers_le_distant

        def pousse_et_avance(coffre, git_dir, branche):
            (self.vault / "0-PROJETS" / "note.md").write_text("encore.\n",
                                                              encoding="utf-8")
            git(self.vault, "add", "-A")
            git(self.vault, "commit", "--quiet", "-m", "la pointe bouge encore")
            return vraie(coffre, git_dir, branche)

        with mock.patch.object(DD, "TOURS_MAX", 1):
            with mock.patch.object(DD, "pousser_vers_le_distant", pousse_et_avance):
                self.assertEqual(DD.CODE_SALVE_INACHEVEE,
                                 self.juger(DD.apres_commit, self.vault))
        journal = (self.vault / ".git" / DD.FICHIER_JOURNAL).read_text(encoding="utf-8")
        self.assertIn("salve inachevée", journal)

    def test_la_suspension_est_journalisee_une_fois_puis_close(self):
        """Une marque ne peut plus arrêter la poussée sans laisser de trace."""
        self.amorcer(distant=self.distant_nu())
        journal = self.vault / ".git" / DD.FICHIER_JOURNAL_SUSPENSION
        os.environ[DD.VARIABLE_SUSPENSION] = "0"
        self.addCleanup(os.environ.pop, DD.VARIABLE_SUSPENSION, None)
        self.assertEqual(0, self.juger(DD.apres_commit, self.vault))
        self.assertEqual(0, self.juger(DD.apres_commit, self.vault))
        lignes = [l for l in journal.read_text(encoding="utf-8").splitlines() if l.strip()]
        self.assertEqual(1, len(lignes), "un épisode = une ligne, pas une par appel")
        self.assertIn("suspendue", lignes[0])
        os.environ.pop(DD.VARIABLE_SUSPENSION)
        self.assertEqual(0, self.juger(DD.apres_commit, self.vault))
        self.assertEqual(0, self.juger(DD.apres_commit, self.vault))
        lignes = [l for l in journal.read_text(encoding="utf-8").splitlines() if l.strip()]
        self.assertEqual(2, len(lignes), "la reprise se note une fois, puis se tait")
        self.assertIn("reprise", lignes[-1])

    def test_un_rebase_en_cours_suspend_la_poussee(self):
        """`rebase-merge` présent : on ne pousse pas un historique qu'on réécrit."""
        self.amorcer(distant=self.distant_nu())
        (self.vault / ".git" / "rebase-merge").mkdir()
        self.assertEqual(0, self.juger(DD.apres_commit, self.vault))
        self.assertFalse((self.vault / ".git" / DD.FICHIER_DERNIERE_POUSSEE).exists())
        self.assertFalse(git(self.parent / "coffre.git", "branch", "--list").stdout.strip())
        journal = (self.vault / ".git" / DD.FICHIER_JOURNAL_SUSPENSION).read_text(
            encoding="utf-8")
        self.assertIn("rebase en cours", journal)

    def test_un_rebase_fini_pousse_la_pointe(self):
        """`post-rewrite` : la réécriture est finie, on pousse malgré le marqueur."""
        self.amorcer(distant=self.distant_nu())
        (self.vault / ".git" / "rebase-merge").mkdir()
        self.assertEqual(0, self.juger(DD.apres_commit, self.vault, True))
        self.assertTrue((self.vault / ".git" / DD.FICHIER_DERNIERE_POUSSEE).is_file())

    def test_la_branche_est_lue_dans_l_etat_du_rebase(self):
        """HEAD détaché pendant un rebase : la branche se lit dans l'état."""
        self.amorcer()
        git(self.vault, "checkout", "--quiet", "--detach")
        (self.vault / ".git" / "rebase-merge").mkdir()
        (self.vault / ".git" / "rebase-merge" / "head-name").write_text(
            "refs/heads/ma-branche\n", encoding="utf-8")
        self.assertEqual("HEAD", git(self.vault, "rev-parse", "--abbrev-ref",
                                     "HEAD").stdout.strip())
        self.assertEqual("ma-branche", DD.branche_courante(self.vault))

    def test_le_verrou_est_commun_aux_worktrees(self):
        """Verrou et marque vivent dans le `.git` commun, pas celui du worktree."""
        self.amorcer()
        lien = Path(tempfile.mkdtemp(prefix="obsia-test-worktree-")) / "arbre"
        self.addCleanup(shutil.rmtree, lien.parent, ignore_errors=True)
        ajout = git(self.vault, "worktree", "add", "--quiet", "-b", "essai", str(lien))
        self.assertEqual(0, ajout.returncode, ajout.stderr)
        commun = DD.dossier_git_commun(lien)
        self.assertEqual((self.vault / ".git").resolve(), commun.resolve())
        self.assertNotEqual(DD.dossier_git(lien).resolve(), commun.resolve())


class TestFraicheur(BaseDepot):
    """La sonde qu'un moniteur push peut brancher (§7.1, M6)."""

    def test_sans_distant_il_n_y_a_rien_a_surveiller(self):
        self.amorcer()
        self.assertEqual(0, self.juger(DD.fraicheur, self.vault))

    def test_un_depot_jamais_pousse_est_signale(self):
        self.amorcer(distant=self.distant_nu())
        self.assertEqual(1, self.juger(DD.fraicheur, self.vault))

    def test_une_poussee_recente_est_fraiche(self):
        self.amorcer(distant=self.distant_nu())
        self.assertEqual(0, self.juger(DD.apres_commit, self.vault))
        self.assertEqual(0, self.juger(DD.fraicheur, self.vault))

    def test_une_poussee_vieille_de_trois_jours_est_perimee(self):
        self.amorcer(distant=self.distant_nu())
        vieux = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=72)
        (self.vault / ".git" / DD.FICHIER_DERNIERE_POUSSEE).write_text(
            vieux.isoformat(timespec="seconds"), encoding="utf-8")
        self.assertEqual(1, self.juger(DD.fraicheur, self.vault))

    def test_une_marque_illisible_est_signalee(self):
        self.amorcer(distant=self.distant_nu())
        (self.vault / ".git" / DD.FICHIER_DERNIERE_POUSSEE).write_text(
            "pas une date\n", encoding="utf-8")
        self.assertEqual(1, self.juger(DD.fraicheur, self.vault))

    def test_fraicheur_rappelle_depuis_quand_la_poussee_est_suspendue(self):
        """Une marque posée ne se découvre plus sans qu'on sache pourquoi."""
        self.amorcer(distant=self.distant_nu())
        (self.vault / ".git" / DD.FICHIER_SUSPENSION).write_text("x\n", encoding="utf-8")
        depuis = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        (self.vault / ".git" / DD.FICHIER_JOURNAL_SUSPENSION).write_text(
            "%s  suspendue  marque %s\n" % (depuis, DD.FICHIER_SUSPENSION),
            encoding="utf-8")
        erreur = StringIO()
        with redirect_stderr(erreur):
            DD.fraicheur(self.vault)
        self.assertIn("Poussée suspendue depuis %s" % depuis, erreur.getvalue())

    def test_fraicheur_rappelle_une_salve_inachevee(self):
        """Un « à jour » ne doit pas taire une salve arrêtée au plafond."""
        self.amorcer(distant=self.distant_nu())
        marque = self.vault / ".git" / DD.FICHIER_DERNIERE_POUSSEE
        maintenant = dt.datetime.now(dt.timezone.utc)
        marque.write_text((maintenant - dt.timedelta(minutes=10)).isoformat(
            timespec="seconds"), encoding="utf-8")
        journal = self.vault / ".git" / DD.FICHIER_JOURNAL
        journal.write_text("%s  main  %s (plafond de 10 tours)\n" % (
            maintenant.isoformat(timespec="seconds"), DD.MARQUEUR_SALVE_INACHEVEE),
            encoding="utf-8")
        erreur = StringIO()
        with redirect_stderr(erreur):
            self.assertEqual(0, DD.fraicheur(self.vault))
        self.assertIn("arrêtée au plafond", erreur.getvalue())
        # Antérieure à la dernière poussée réussie : plus rien à signaler.
        marque.write_text((maintenant + dt.timedelta(seconds=5)).isoformat(
            timespec="seconds"), encoding="utf-8")
        erreur = StringIO()
        with redirect_stderr(erreur):
            self.assertEqual(0, DD.fraicheur(self.vault))
        self.assertNotIn("arrêtée au plafond", erreur.getvalue())

    def test_fraicheur_rappelle_une_salve_inachevee_a_la_meme_seconde(self):
        """La marque et la ligne de plafond tombent dans la même seconde.

        C'est le cas normal : la poussée réussie pose la marque, puis la salve
        s'arrête au plafond aussitôt après, les deux horodatages à la seconde
        près — donc égaux. La marque doit être comprise, sinon la ligne est
        écartée et la salve inachevée reste sans écho.
        """
        self.amorcer(distant=self.distant_nu())
        seconde = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        (self.vault / ".git" / DD.FICHIER_DERNIERE_POUSSEE).write_text(
            seconde, encoding="utf-8")
        (self.vault / ".git" / DD.FICHIER_JOURNAL).write_text(
            "%s  main  %s (plafond de 10 tours)\n" % (
                seconde, DD.MARQUEUR_SALVE_INACHEVEE),
            encoding="utf-8")
        erreur = StringIO()
        with redirect_stderr(erreur):
            self.assertEqual(0, DD.fraicheur(self.vault))
        self.assertIn("arrêtée au plafond", erreur.getvalue())

    def test_fraicheur_ne_depend_pas_de_la_derniere_ligne_du_journal(self):
        """Un échec écrit après la ligne de plafond ne doit pas la masquer."""
        self.amorcer(distant=self.distant_nu())
        maintenant = dt.datetime.now(dt.timezone.utc)
        (self.vault / ".git" / DD.FICHIER_DERNIERE_POUSSEE).write_text(
            (maintenant - dt.timedelta(minutes=10)).isoformat(timespec="seconds"),
            encoding="utf-8")
        (self.vault / ".git" / DD.FICHIER_JOURNAL).write_text(
            "%s  main  %s (plafond de 10 tours)\n"
            "%s  main  poussée refusée (non-avance)\n" % (
                maintenant.isoformat(timespec="seconds"), DD.MARQUEUR_SALVE_INACHEVEE,
                (maintenant + dt.timedelta(seconds=1)).isoformat(timespec="seconds")),
            encoding="utf-8")
        erreur = StringIO()
        with redirect_stderr(erreur):
            self.assertEqual(0, DD.fraicheur(self.vault))
        self.assertIn("arrêtée au plafond", erreur.getvalue())
        self.assertIn("échouée", erreur.getvalue())


class TestLigneDeCommande(BaseDepot):
    def test_avant_commit_en_ligne_de_commande(self):
        self.ecrire_profil(ecrivain=MOD.nom_machine())
        self.ecrire_verificateur(0)
        self.assertEqual(0, self.juger(DD.main, ["avant-commit", "--coffre",
                                                 str(self.vault), "--produit",
                                                 str(self.produit)]))

    def test_fraicheur_avec_seuil_en_ligne_de_commande(self):
        """Le seuil passe par la ligne de commande : à 1 h, deux heures sont trop."""
        self.amorcer(distant=self.distant_nu())
        self.assertEqual(0, self.juger(DD.apres_commit, self.vault))
        vieux = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=2)
        (self.vault / ".git" / DD.FICHIER_DERNIERE_POUSSEE).write_text(
            vieux.isoformat(timespec="seconds"), encoding="utf-8")
        self.assertEqual(1, self.juger(DD.main, ["fraicheur", "--coffre",
                                                 str(self.vault), "--heures", "1"]))
        self.assertEqual(0, self.juger(DD.main, ["fraicheur", "--coffre",
                                                 str(self.vault), "--heures", "48"]))

    def test_apres_rewrite_en_ligne_de_commande(self):
        """`post-rewrite` appelle `apres-rewrite`, qui pousse malgré le rebase."""
        self.amorcer(distant=self.distant_nu())
        (self.vault / ".git" / "rebase-merge").mkdir()
        self.assertEqual(0, self.juger(DD.main, ["apres-rewrite", "--coffre",
                                                 str(self.vault)]))
        self.assertTrue((self.vault / ".git" / DD.FICHIER_DERNIERE_POUSSEE).is_file())


class TestLaDocDuCrochetDitCeQuIlRelit(unittest.TestCase):
    """Ce que le crochet relit, et ce qu'il ne relit pas — écrit là où on le cherche.

    Les deux règles du crochet ne se ressemblent pas : un secret **nommé** n'est
    jugé que sur les lignes que le commit ajoute, tandis qu'un **bloc de base64**
    ou un **jeton isolé** sont relus dans le contenu **entier** de chaque fichier
    indexé. Cette asymétrie n'était écrite que dans la docstring de
    `garde_secrets.py`.

    Qui cherche pourquoi un vieux secret nommé tient bon ouvre ce fichier-ci, ne
    trouve rien, et conclut à une fuite ; une décision qu'on ne trouve pas se
    reprend par erreur. Ce test garde le paragraphe, pas sa formulation : il
    exige les deux moitiés et le renvoi vers l'autre fichier, et laisse la phrase
    se réécrire.
    """

    def test_l_asymetrie_est_dite_dans_la_docstring_du_crochet(self):
        doc = DD.__doc__ or ""
        self.assertIn("garde_secrets.py", doc)
        self.assertIn("ajoute", doc)
        self.assertIn("tout le contenu", doc)


if __name__ == "__main__":
    unittest.main()
