#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L'écrivain : produire un carnet de bout en bout, sur un coffre de test.

La tranche P3 livre le premier **geste** du produit : créer un carnet à partir
d'un simple sujet, à travers la porte livrée en #149, sur un dépôt de données de
**test** monté dans un dossier temporaire — jamais le coffre réel.

Ce que ces tests montrent, un par un :

- le chemin, le nom et le frontmatter sont **calculés par l'outil** (§6), sans
  que l'appelant ait donné ni chemin, ni nom, ni date ;
- l'aperçu **exact** est rendu avec l'écriture et conservé en copie datée dans
  `_MAINTENANCE/` (§7.4) ;
- un acte est **un seul commit**, ne portant que ses fichiers, posé sur la
  branche par défaut du dépôt, annulable par `git revert` ;
- un **refus du crochet** défait l'écriture et le refus est **dit** ;
- l'écriture du socle est **atomique** — encoder d'abord, poser par fichier temporaire :
  un texte inencodable échoue sans avoir tronqué le fichier visé ;
- la **trace** — chemin, aperçu, refus — se lit d'un coup d'œil ;
- le **message de commit** porte la marque qui distingue l'outil d'un chef.

`git` peut manquer : les tests qui en dépendent sautent alors, jamais la règle.
Le dépôt de données est toujours jetable : ce fichier n'écrit jamais dans un
coffre réel.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
RACINE = Path(__file__).resolve().parent.parent
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

import serveur.ecrivain as ECRIVAIN  # noqa: E402
import serveur.socle_ecriture as SOCLE  # noqa: E402

sys.path.insert(0, str(RACINE / "scripts"))
import convention_des_notes as CONVENTION  # noqa: E402

GIT = shutil.which("git")

#: Un jeton de forme plausible, assemblé au moment du test : la garde des
#: secrets n'a de sens que si le motif cherché n'est pas écrit en clair ici.
JETON = "ghp_" + "".join(("Ab3", "Cd5", "Ef7", "Gh9", "Ij1", "Kl3", "Mn5",
                          "Op7", "Qr9", "St1", "Uv3", "Wx5"))


def git(ou, *arguments):
    """Lance `git` dans `ou` et rend le résultat, sans lever."""
    return subprocess.run(["git", "-C", str(ou), *arguments],
                          capture_output=True, text=True, check=False)


@unittest.skipUnless(GIT, "git est absent de cette machine")
class BaseDuCoffreDeTest(unittest.TestCase):
    """Un coffre de test : un dépôt git jetable, jamais le coffre réel."""

    AUTEUR = "batisseur"
    DATE = "2026-10-09"
    PROJET = "obsia"
    CHANTIER = "mcp-outils-du-coffre"
    SUJET = "Ouverture"
    CORPS = "Premier jour du chantier.\n"

    CHEMIN = ("0-PROJETS/obsia/mcp-outils-du-coffre/carnets/"
              "2026-10-09-mcp-outils-du-coffre-ouverture.md")
    COPIE = ("_MAINTENANCE/2026-10-09-apercu-"
             "2026-10-09-mcp-outils-du-coffre-ouverture.md")

    def setUp(self):
        self.parent = Path(tempfile.mkdtemp(prefix="obsia-ecrivain-"))
        self.addCleanup(shutil.rmtree, self.parent, ignore_errors=True)
        self.coffre = self.parent / "coffre-de-test"
        self.coffre.mkdir()
        self.initialiser(self.coffre)
        self.forcer_l_identifiant_dans_le_bac_a_sable()

    def forcer_l_identifiant_dans_le_bac_a_sable(self):
        """Ranger l'identifiant d'écrivain du banc dans son bac à sable, pas dans le ``$HOME``.

        Sans cela, un test qui prend un verrou tire pour de bon l'identifiant de la
        **station du développeur** et écrit un fichier dans son dossier personnel.
        """
        chemin = self.parent / "etat" / "ecrivain.id"
        ancien = os.environ.get("OBSIA_ECRIVAIN_ID_FICHIER")
        os.environ["OBSIA_ECRIVAIN_ID_FICHIER"] = str(chemin)
        SOCLE._IDENTIFIANT_DE_LA_STATION = None

        def rendre():
            if ancien is None:
                os.environ.pop("OBSIA_ECRIVAIN_ID_FICHIER", None)
            else:
                os.environ["OBSIA_ECRIVAIN_ID_FICHIER"] = ancien
            SOCLE._IDENTIFIANT_DE_LA_STATION = None

        self.addCleanup(rendre)

    @staticmethod
    def initialiser(coffre):
        """Un dépôt de test avec une branche nommée et un premier commit."""
        init = git(coffre, "init", "--quiet", "-b", "main")
        if init.returncode != 0:  # git d'avant `-b`
            git(coffre, "init", "--quiet")
            git(coffre, "symbolic-ref", "HEAD", "refs/heads/main")
        # Le coffre **nomme** sa branche par défaut : sans cela l'écrivain refuse
        # l'acte (échec fermé, §7.4). `origin/HEAD` serait l'autre source — un
        # dépôt de test sans remote s'en remet donc à cette configuration.
        git(coffre, "config", "init.defaultBranch", "main")
        git(coffre, "config", "user.email", "essai@exemple.invalid")
        git(coffre, "config", "user.name", "Essai")
        (coffre / "0-PROJETS").mkdir(parents=True, exist_ok=True)
        (coffre / "0-PROJETS" / "amorce.md").write_text("Amorce.\n",
                                                        encoding="utf-8")
        git(coffre, "add", "--", "0-PROJETS/amorce.md")
        git(coffre, "commit", "--quiet", "-m", "amorce")

    def ecrire(self, **remplacements):
        """Écrit le carnet d'essai, en laissant surcharger un champ."""
        champs = dict(coffre=self.coffre, auteur=self.AUTEUR, projet=self.PROJET,
                      chantier=self.CHANTIER, sujet=self.SUJET,
                      corps=self.CORPS, date=self.DATE)
        champs.update(remplacements)
        return ECRIVAIN.ecrire_un_carnet(**champs)

    def poser_un_crochet(self, message, code_sortie=1):
        """Installe un hook `pre-commit` qui refuse le commit."""
        crochet = self.coffre / ".git" / "hooks" / "pre-commit"
        crochet.parent.mkdir(parents=True, exist_ok=True)
        crochet.write_text("#!/bin/sh\nprintf '%%s\\n' \"%s\" >&2\nexit %d\n"
                           % (message, code_sortie), encoding="utf-8")
        os.chmod(crochet, 0o755)
        return crochet


class TestLeCarnetCalcule(BaseDuCoffreDeTest):
    """Le chemin, le nom et le frontmatter viennent de l'outil, pas du modèle."""

    def test_un_carnet_par_sujet_a_le_chemin_le_nom_et_la_date_du_contrat(self):
        acte = self.ecrire()
        self.assertIsNone(acte.refus)
        self.assertEqual(self.CHEMIN, acte.chemin)
        self.assertTrue((self.coffre / acte.chemin).is_file())

    def test_le_frontmatter_d_un_carnet_porte_agent_projet_et_statut(self):
        acte = self.ecrire()
        self.assertIsNone(acte.refus, acte.trace())
        contenu = (self.coffre / acte.chemin).read_text(encoding="utf-8")
        self.assertIn("agent: batisseur", contenu)
        self.assertIn("projet: mcp-outils-du-coffre", contenu)
        self.assertIn("statut: en cours", contenu)
        self.assertIn("date: 2026-10-09", contenu)
        self.assertIn("Premier jour du chantier.", contenu)

    def test_hors_chantier_le_carnet_porte_le_nom_du_projet(self):
        acte = self.ecrire(chantier=None, projet=self.PROJET, sujet="Bilan")
        self.assertIsNone(acte.refus)
        self.assertEqual("0-PROJETS/obsia/carnets/2026-10-09-obsia-bilan.md",
                         acte.chemin)
        contenu = (self.coffre / acte.chemin).read_text(encoding="utf-8")
        self.assertIn("projet: obsia", contenu)

    def test_le_statut_se_choisit_et_le_statut_inconnu_est_refuse(self):
        acte = self.ecrire(statut="en attente")
        self.assertIsNone(acte.refus, acte.trace())
        self.assertIn("statut: en attente",
                      (self.coffre / acte.chemin).read_text(encoding="utf-8"))
        refuse = self.ecrire(statut="terminé")
        self.assertIsNotNone(refuse.refus)

    def test_le_chemin_ne_vient_pas_de_l_appelant(self):
        with self.assertRaises(TypeError):
            ECRIVAIN.ecrire_un_carnet(self.coffre, auteur=self.AUTEUR,
                                      projet=self.PROJET, sujet=self.SUJET,
                                      corps=self.CORPS, chemin="ailleurs.md")

    def test_le_dossier_du_carnet_est_cree_s_il_manque(self):
        self.assertFalse((self.coffre / "0-PROJETS" / "obsia").exists())
        acte = self.ecrire()
        self.assertIsNone(acte.refus)
        self.assertTrue((self.coffre / acte.chemin).is_file())


class TestLApercuEtSaCopie(BaseDuCoffreDeTest):
    """L'aperçu exact, rendu avec l'écriture, et sa copie datée (§7.4)."""

    def test_l_apercu_est_exactement_le_texte_ecrit(self):
        acte = self.ecrire()
        self.assertIsNone(acte.refus, acte.trace())
        contenu = (self.coffre / acte.chemin).read_text(encoding="utf-8")
        self.assertEqual(contenu, acte.apercu)

    def test_la_copie_d_apercu_est_datee_dans_la_maintenance(self):
        acte = self.ecrire()
        self.assertIsNone(acte.refus, acte.trace())
        self.assertEqual(self.COPIE, acte.copie)
        self.assertTrue((self.coffre / acte.copie).is_file())

    def test_la_copie_porte_la_demande_le_chemin_et_l_apercu(self):
        acte = self.ecrire()
        self.assertIsNone(acte.refus, acte.trace())
        copie = (self.coffre / acte.copie).read_text(encoding="utf-8")
        self.assertIn(acte.chemin, copie)
        self.assertIn(acte.apercu, copie)
        self.assertIn("Ouverture", copie)

    def test_la_copie_d_un_carnet_garde_le_nom_entier_du_carnet(self):
        # La date du carnet n'est pas retirée : deux carnets du même sujet ouverts à
        # deux dates partageraient sinon l'aperçu du jour. Le nom entier les sépare.
        acte = self.ecrire(chantier=None, sujet="Bilan")
        self.assertIsNone(acte.refus, acte.trace())
        self.assertEqual("_MAINTENANCE/2026-10-09-apercu-2026-10-09-obsia-bilan.md",
                         acte.copie)


class TestLAacteEstUnCommit(BaseDuCoffreDeTest):
    """Un acte = un seul commit, ses fichiers et rien d'autre (§7.4)."""

    def test_un_acte_est_un_seul_commit_de_plus(self):
        avant = git(self.coffre, "rev-parse", "HEAD").stdout.strip()
        acte = self.ecrire()
        self.assertIsNone(acte.refus, acte.trace())
        apres = git(self.coffre, "rev-parse", "HEAD").stdout.strip()
        self.assertNotEqual(avant, apres)
        parents = git(self.coffre, "rev-list", "--parents", "-n", "1",
                      apres).stdout.split()
        self.assertEqual(avant, parents[1])

    def test_le_commit_ne_porte_que_les_fichiers_de_l_acte(self):
        acte = self.ecrire()
        self.assertIsNone(acte.refus, acte.trace())
        portes = git(self.coffre, "show", "--name-only", "--format=",
                     acte.commit).stdout.split()
        self.assertEqual(sorted([self.CHEMIN, self.COPIE]), sorted(portes))

    def test_un_fichier_etranger_modifie_n_entre_pas_dans_le_commit(self):
        etranger = self.coffre / "0-PROJETS" / "amorce.md"
        etranger.write_text("Amorce modifiée à la main.\n", encoding="utf-8")
        acte = self.ecrire()
        self.assertIsNone(acte.refus, acte.trace())
        portes = git(self.coffre, "show", "--name-only", "--format=",
                     acte.commit).stdout
        self.assertNotIn("amorce.md", portes)
        self.assertIn("M 0-PROJETS/amorce.md",
                      git(self.coffre, "status", "--porcelain").stdout)

    def test_l_acte_se_pose_sur_la_branche_par_defaut(self):
        acte = self.ecrire()
        self.assertIsNone(acte.refus, acte.trace())
        self.assertEqual("main",
                         git(self.coffre, "rev-parse", "--abbrev-ref",
                             "HEAD").stdout.strip())
        contient = git(self.coffre, "branch", "--contains", acte.commit,
                       "--format=%(refname:short)").stdout.split()
        self.assertIn("main", contient)

    def test_une_tete_detachee_est_refusee_et_rien_n_est_ecrit(self):
        git(self.coffre, "checkout", "--quiet", "--detach", "HEAD")
        acte = self.ecrire()
        self.assertIsNotNone(acte.refus)
        self.assertIsNone(acte.commit)
        self.assertFalse((self.coffre / acte.chemin).exists())

    def test_l_acte_est_annulable_par_git_revert(self):
        acte = self.ecrire()
        self.assertIsNone(acte.refus, acte.trace())
        retour = git(self.coffre, "revert", "--no-edit", acte.commit)
        self.assertEqual(0, retour.returncode, retour.stderr)
        self.assertFalse((self.coffre / self.CHEMIN).exists())
        self.assertFalse((self.coffre / self.COPIE).exists())

    def test_un_commit_qui_ne_porte_pas_l_acte_est_defait(self):
        # Le contrôle « le commit porte exactement l'acte » ne se force pas
        # depuis git : on le met à l'épreuve en faisant mentir la lecture.
        vrai = ECRIVAIN.fichiers_du_commit

        def menteur(depot, commit):
            return tuple(vrai(depot, commit)) + ("etranger.md",)

        ECRIVAIN.fichiers_du_commit = menteur
        self.addCleanup(setattr, ECRIVAIN, "fichiers_du_commit", vrai)
        acte = self.ecrire()
        self.assertIsNotNone(acte.refus)
        self.assertIn("exactement", acte.refus)
        self.assertIsNone(acte.commit)
        self.assertFalse((self.coffre / self.CHEMIN).exists())
        self.assertFalse((self.coffre / self.COPIE).exists())


class TestLaBrancheParDefaut(BaseDuCoffreDeTest):
    """§7.4 : l'acte se pose sur la branche par défaut, ou ne se pose pas.

    C'est elle qui fait qu'un `git revert` défait l'acte **seul**. Si le dépôt ne
    la nomme pas — ni `origin/HEAD`, ni `init.defaultBranch` — le refus tombe
    **avant** l'écriture : l'acte ne se pose pas au hasard d'une branche, et la
    garantie ne se relâche pas en silence.
    """

    def test_une_branche_par_defaut_introuvable_refuse_l_ecriture(self):
        # Valeur vide : elle masque une éventuelle configuration globale, et le
        # dépôt ne nomme plus sa branche par défaut.
        git(self.coffre, "config", "init.defaultBranch", "")
        avant = git(self.coffre, "rev-parse", "HEAD").stdout.strip()
        acte = self.ecrire()
        self.assertIsNotNone(acte.refus, acte.trace())
        self.assertIn("branche par défaut introuvable", acte.refus)
        self.assertIn("init.defaultBranch", acte.refus)
        self.assertIsNone(acte.commit)
        self.assertFalse((self.coffre / self.CHEMIN).exists())
        self.assertEqual(avant,
                         git(self.coffre, "rev-parse", "HEAD").stdout.strip())

    def test_une_autre_branche_que_la_par_defaut_refuse_l_ecriture(self):
        git(self.coffre, "checkout", "--quiet", "-b", "essai")
        acte = self.ecrire()
        self.assertIsNotNone(acte.refus, acte.trace())
        self.assertIn("branche `essai`", acte.refus)
        self.assertIsNone(acte.commit)
        self.assertFalse((self.coffre / self.CHEMIN).exists())


class TestLeCrochetEtLeVerrou(BaseDuCoffreDeTest):
    """Le refus du crochet défait l'écriture ; le verrou est exclusif."""

    def test_un_refus_du_crochet_defait_l_ecriture_et_le_dit(self):
        self.poser_un_crochet("le crochet refuse cet essai")
        acte = self.ecrire()
        self.assertIsNotNone(acte.refus)
        self.assertIn("crochet", acte.refus)
        self.assertIsNone(acte.commit)
        self.assertFalse((self.coffre / self.CHEMIN).exists())
        self.assertFalse((self.coffre / self.COPIE).exists())
        self.assertEqual("",
                         git(self.coffre, "status", "--porcelain").stdout.strip())

    def test_un_verrou_deja_pris_refuse_l_ecriture(self):
        verrou = self.coffre / ".git" / "obsia-ecriture.lock"
        verrou.write_text("un autre acte tient le verrou\n", encoding="utf-8")
        acte = self.ecrire()
        self.assertIsNotNone(acte.refus)
        self.assertIn("verrou", acte.refus)
        self.assertTrue(verrou.exists())
        self.assertEqual("un autre acte tient le verrou\n",
                         verrou.read_text(encoding="utf-8"))
        self.assertFalse((self.coffre / self.CHEMIN).exists())

    def test_le_verrou_est_relache_apres_l_acte(self):
        acte = self.ecrire()
        self.assertIsNone(acte.refus, acte.trace())
        self.assertFalse((self.coffre / ".git" / "obsia-ecriture.lock").exists())


class TestLesRefusDEcriture(BaseDuCoffreDeTest):
    """Un refus n'écrit rien : la trace du refus est la valeur rendue."""

    def test_la_garde_des_secrets_passe_avant_l_ecriture(self):
        acte = self.ecrire(corps="Le jeton est %s dans le texte.\n" % JETON)
        self.assertIsNotNone(acte.refus)
        self.assertIn("secret", acte.refus)
        self.assertIsNone(acte.commit)
        self.assertFalse((self.coffre / self.CHEMIN).exists())
        self.assertFalse((self.coffre / "_MAINTENANCE").exists())

    def test_un_doublon_est_refuse_sans_rien_ecrire_de_plus(self):
        premier = self.ecrire()
        second = self.ecrire()
        self.assertIsNone(premier.refus)
        self.assertIsNotNone(second.refus)
        self.assertIn("unique", second.refus)
        copies = sorted(p.name for p in
                        (self.coffre / "_MAINTENANCE").iterdir())
        self.assertEqual(sorted([Path(self.COPIE).name]), copies)

    def test_un_auteur_absent_est_refuse(self):
        acte = self.ecrire(auteur="   ")
        self.assertIsNotNone(acte.refus)
        self.assertFalse((self.coffre / self.CHEMIN).exists())


class TestLaMarqueEtLaTrace(BaseDuCoffreDeTest):
    """La marque d'auteur du commit, et la trace lisible d'un coup d'œil."""

    def test_le_message_du_commit_porte_la_marque_de_l_outil(self):
        acte = self.ecrire()
        self.assertIsNone(acte.refus, acte.trace())
        message = git(self.coffre, "log", "-1", "--format=%B",
                      acte.commit).stdout
        self.assertIn("OBSIA-Outil: " + ECRIVAIN.OUTIL, message)
        self.assertIn("OBSIA-Auteur: " + self.AUTEUR, message)
        self.assertEqual(ECRIVAIN.OUTIL, ECRIVAIN.outil_du_commit(message))
        self.assertEqual(self.AUTEUR, ECRIVAIN.auteur_du_commit(message))

    def test_la_marque_n_entre_pas_dans_le_frontmatter(self):
        acte = self.ecrire()
        contenu = (self.coffre / acte.chemin).read_text(encoding="utf-8")
        self.assertNotIn("OBSIA-Outil", contenu)
        self.assertNotIn("OBSIA-Auteur", contenu)

    def test_la_marque_se_reconnait_et_distingue_un_commit_manuel(self):
        a_la_main = "Carnet : ouverture\n\nÉcrit à la main.\n"
        self.assertIsNone(ECRIVAIN.outil_du_commit(a_la_main))
        d_outil = ECRIVAIN.message_d_un_acte("Carnet : ouverture", "batisseur")
        self.assertEqual(ECRIVAIN.OUTIL, ECRIVAIN.outil_du_commit(d_outil))

    def test_la_trace_se_lit_d_un_coup_d_oeil(self):
        acte = self.ecrire()
        trace = acte.trace()
        self.assertIn(acte.chemin, trace)
        self.assertIn(acte.copie, trace)
        self.assertIn(acte.commit, trace)
        self.assertIn("Ouverture", trace)

    def test_la_trace_d_un_refus_dit_le_refus(self):
        self.poser_un_crochet("le crochet refuse cet essai")
        acte = self.ecrire()
        trace = acte.trace()
        self.assertIn("Refus", trace)
        self.assertIn("crochet", trace)


class TestLeNomDuCarnetVientDuMoteur(unittest.TestCase):
    """L'écrivain ne nomme pas : il demande son nom au moteur.

    La forme exacte de la règle — la date, la tige du sujet, le dossier pris tel
    quel — est éprouvée dans `tests/test_convention_notes_partagee.py`, à côté des
    autres règles du moteur. Ici, on vérifie seulement que le nom que l'écrivain
    pose sur le disque est bien celui que le moteur calcule, et qu'il se
    reconnaît.
    """

    def test_le_nom_du_carnet_est_celui_du_moteur(self):
        nom = CONVENTION.nom_de_carnet("2026-10-09", "mcp-outils-du-coffre",
                                       "Ouverture")
        self.assertEqual("2026-10-09-mcp-outils-du-coffre-ouverture.md", nom)
        self.assertTrue(CONVENTION.carnet_a_la_forme(nom))
        self.assertTrue(CONVENTION.carnet_du_dossier(nom, "mcp-outils-du-coffre"))
        self.assertFalse(CONVENTION.carnet_du_dossier(nom, "obsia"))


GABARIT = "IA/system/depot-de-donnees/gitignore-coffre"


class TestLeDossierEstPrisTelQuel(BaseDuCoffreDeTest):
    """Le dossier du projet ou du chantier est un **nom réel**, pas une tige.

    La règle du §6 ne replie pas le dossier, et le contrôle du coffre compare au
    nom qui est sur le disque : si l'écrivain repliait de son côté, il écrirait
    sous un nom que la vérification ne reconnaîtrait pas. Ce qu'il ne peut pas
    laisser passer, en revanche, c'est un second dossier qui ne diffère du
    premier que par l'orthographe — deux dossiers jumeaux que rien ne relierait.
    """

    def test_un_dossier_a_majuscule_ou_accent_est_accepte(self):
        for dossier in ("Homelab", "Idées", "OBSIA-UI"):
            acte = self.ecrire(projet=dossier, chantier=None, sujet="Bilan")
            self.assertIsNone(acte.refus, "%s : %s" % (dossier, acte.trace()))
            self.assertTrue((self.coffre / acte.chemin).is_file(), dossier)
            self.assertEqual("0-PROJETS/%s/carnets/" % dossier,
                             str(Path(acte.chemin).parent) + "/", acte.chemin)

    def test_un_dossier_de_chantier_garde_son_orthographe(self):
        acte = self.ecrire(projet="Homelab", chantier="Refonte-UI")
        self.assertIsNone(acte.refus, acte.trace())
        self.assertEqual("0-PROJETS/Homelab/Refonte-UI/carnets/"
                         "2026-10-09-Refonte-UI-ouverture.md", acte.chemin)
        contenu = (self.coffre / acte.chemin).read_text(encoding="utf-8")
        self.assertIn("projet: Refonte-UI", contenu)

    def test_un_dossier_jumeau_est_refuse_et_rien_n_est_ecrit(self):
        (self.coffre / "0-PROJETS" / "Homelab" / "carnets").mkdir(parents=True)
        (self.coffre / "0-PROJETS" / "Homelab" / "carnets" / "2026-10-08-homelab-x.md"
         ).write_text("Déjà là.\n", encoding="utf-8")
        avant = git(self.coffre, "rev-parse", "HEAD").stdout.strip()

        acte = self.ecrire(projet="homelab", chantier=None, sujet="Bilan")
        self.assertIsNotNone(acte.refus)
        self.assertIn("Homelab", acte.refus)
        self.assertFalse((self.coffre / "0-PROJETS" / "homelab").exists())
        self.assertEqual(avant, git(self.coffre, "rev-parse", "HEAD").stdout.strip())

    def test_un_dossier_jumeau_de_chantier_est_refuse(self):
        (self.coffre / "0-PROJETS" / "obsia" / "Refonte" / "carnets").mkdir(
            parents=True)
        acte = self.ecrire(projet="obsia", chantier="refonte")
        self.assertIsNotNone(acte.refus)
        self.assertIn("Refonte", acte.refus)
        self.assertFalse((self.coffre / "0-PROJETS" / "obsia" / "refonte").exists())

    def test_le_dossier_existant_a_la_bonne_orthographe_reste_ouvert(self):
        premier = self.ecrire(projet="Homelab", chantier=None, sujet="Bilan")
        self.assertIsNone(premier.refus, premier.trace())
        second = self.ecrire(projet="Homelab", chantier=None, sujet="Suite")
        self.assertIsNone(second.refus, second.trace())

    def test_un_dossier_qui_est_un_chemin_est_refuse(self):
        # Le refus doit venir du nom de dossier lui-même : la porte refuserait
        # aussi `0-PROJETS/../carnets`, mais alors pour une autre raison, et le
        # dossier de test ne dirait plus ce qu'il prétend dire.
        for dossier in ("..", "../ailleurs", "a/b", "a\\b", "", " obsia"):
            acte = self.ecrire(projet=dossier, chantier=None, sujet="Bilan")
            self.assertIsNotNone(acte.refus, dossier)
            self.assertIn("un seul nom", acte.refus, dossier)
            self.assertFalse((self.coffre / "0-PROJETS" / "a").exists(), dossier)
            self.assertFalse((self.coffre / "carnets").exists(), dossier)
            self.assertFalse((self.coffre / "0-PROJETS").joinpath(
                "../ailleurs").resolve().exists(), dossier)

    def test_un_dossier_qui_porte_un_caractère_de_contrôle_est_refuse(self):
        # Un contrôle **intérieur** (retour à la ligne, tabulation, NEL) : le nom du
        # dossier ne doit pas se lire en deux lignes — ni dans la trace, ni sur le
        # disque. Le refus est prononcé avant toute écriture.
        for dossier in ("obsia\nbilan", "obsia\tbilan", "obsia\rbilan",
                        "obsia\x85bilan"):
            acte = self.ecrire(projet=dossier, chantier=None, sujet="Bilan")
            self.assertIsNotNone(acte.refus, dossier)
            self.assertIn("caractère de contrôle", acte.refus, dossier)
            self.assertNotIn("\n", acte.refus.strip(), dossier)
        self.assertEqual(["amorce.md"], sorted(p.name for p in
                                               (self.coffre / "0-PROJETS").iterdir()))

    def test_un_dossier_visuellement_jumeau_est_refuse(self):
        # `Cf` — format, invisible : largeur nulle, BOM, marque d'orientation. Un
        # `Home<ZWSP>lab` serait indiscernable à l'œil de `Homelab`.
        for dossier in ("Home\u200blab", "Home\ufefflab", "Home\u200flab",
                        "Home\u2060lab"):
            acte = self.ecrire(projet=dossier, chantier=None, sujet="Bilan")
            self.assertIsNotNone(acte.refus, dossier)
            self.assertIn("invisible", acte.refus, dossier)
        self.assertFalse((self.coffre / "0-PROJETS" / "Homelab").exists())
        self.assertEqual(["amorce.md"], sorted(p.name for p in
                                               (self.coffre / "0-PROJETS").iterdir()))


class TestUneEcritureQuiEchoueEstDefaite(BaseDuCoffreDeTest):
    """« Un refus n'écrit rien » doit tenir même quand la panne vient du disque."""

    def test_la_copie_impossible_defait_le_carnet_deja_ecrit(self):
        # `_MAINTENANCE/` existe, mais à la place de la copie il y a un dossier :
        # l'écriture de la copie ne peut pas aboutir.
        self.assertEqual(
            0, git(self.coffre, "rev-parse", "HEAD").returncode)
        (self.coffre / self.COPIE).mkdir(parents=True)

        acte = self.ecrire()
        self.assertIsNotNone(acte.refus, acte.trace())
        self.assertFalse((self.coffre / self.CHEMIN).exists())
        self.assertEqual(
            "amorce", git(self.coffre, "log", "-1", "--format=%s").stdout.strip())


class TestLeWorktreeLie(BaseDuCoffreDeTest):
    """Dans un worktree lié, `.git` est un **fichier** : le verrou n'y va pas."""

    def test_le_verrou_se_pose_dans_le_vrai_dossier_git(self):
        git(self.coffre, "checkout", "--quiet", "-b", "ailleurs")
        lien = self.parent / "coffre-lie"
        pose = git(self.coffre, "worktree", "add", "--quiet", str(lien), "main")
        self.assertEqual(0, pose.returncode, pose.stderr)
        self.assertTrue((lien / ".git").is_file())

        acte = ECRIVAIN.ecrire_un_carnet(coffre=lien, auteur=self.AUTEUR,
                                         projet=self.PROJET, chantier=self.CHANTIER,
                                         sujet=self.SUJET, corps=self.CORPS,
                                         date=self.DATE)
        self.assertIsNone(acte.refus, acte.trace())
        self.assertTrue((lien / acte.chemin).is_file())
        self.assertEqual(
            0, git(lien, "cat-file", "-e", "%s:%s" % (acte.commit, acte.chemin)
                   ).returncode)
        for reste in (self.coffre / ".git" / "worktrees").rglob(ECRIVAIN.VERROU):
            self.fail("verrou resté posé : %s" % reste)


class TestLeCheminEstCeluiDeLaPorte(BaseDuCoffreDeTest):
    """L'écrivain écrit au chemin que la porte a désigné — ou pas du tout."""

    def test_un_chemin_de_la_porte_different_arrete_l_ecriture(self):
        vrai_juger = ECRIVAIN.PORTE.juger

        def ailleurs(candidat, contexte):
            verdict = vrai_juger(candidat, contexte)
            if verdict.refus is None:
                verdict = verdict._replace(destination="0-PROJETS/ailleurs.md")
            return verdict

        ECRIVAIN.PORTE.juger = ailleurs
        self.addCleanup(setattr, ECRIVAIN.PORTE, "juger", vrai_juger)

        acte = self.ecrire()
        self.assertIsNotNone(acte.refus, acte.trace())
        self.assertIn("0-PROJETS/ailleurs.md", acte.refus)
        self.assertFalse((self.coffre / self.CHEMIN).exists())
        self.assertFalse((self.coffre / "0-PROJETS" / "ailleurs.md").exists())


@unittest.skipUnless(GIT, "git est absent de cette machine")
class TestLeCarnetEcritPasseLeControleDuCoffre(BaseDuCoffreDeTest):
    """Ce que l'outil écrit, le coffre le reconnaît — sans seconde règle.

    Écrire d'un côté et reconnaître de l'autre avec deux morceaux de code
    différents ferait diverger les deux : le carnet serait posé, puis refusé par
    le contrôle. Ici on ne relit pas la règle, on fait passer le carnet écrit
    devant le vérificateur du coffre, tel quel (`--carnets`, §7.1).
    """

    def test_le_carnet_ecrit_est_reconnu_par_le_verificateur(self):
        acte = self.ecrire()
        self.assertIsNone(acte.refus, acte.trace())

        gabarit = RACINE / GABARIT
        liste = gabarit.read_text(encoding="utf-8")
        (self.coffre / GABARIT).parent.mkdir(parents=True, exist_ok=True)
        (self.coffre / GABARIT).write_text(liste, encoding="utf-8")
        (self.coffre / ".gitignore").write_text(liste, encoding="utf-8")

        controle = subprocess.run(
            [sys.executable, str(RACINE / "scripts" / "verifier_coffre.py"),
             "--coffre", str(self.coffre), "--carnets"],
            capture_output=True, text=True, check=False)
        self.assertEqual(0, controle.returncode, controle.stdout + controle.stderr)


class TestLEcritureAtomiqueDuSocle(BaseDuCoffreDeTest):
    """#01a12148 — le socle écrit « en entier ou pas du tout », jamais à moitié."""

    def test_ecrire_un_texte_inencodable_ne_touche_pas_le_fichier(self):
        """Un demi-surrogate : l'écriture échoue **sans** avoir touché le fichier.

        Preuve directe de la pose atomique, indépendante des gestes. ``Path.write_text``
        aurait tronqué le fichier avant d'échouer ; ici l'encodage précède toute écriture
        et le remplacement n'a lieu qu'une fois le contenu complet. Le fichier visé garde
        donc ses octets, et aucun fichier temporaire ne reste derrière.
        """
        dossier = self.coffre / "0-SAVOIRS"
        dossier.mkdir(parents=True, exist_ok=True)
        SOCLE._ecrire(self.coffre, "0-SAVOIRS/note.md", "un contenu propre\n")
        vise = dossier / "note.md"
        self.assertEqual(b"un contenu propre\n", vise.read_bytes())

        with self.assertRaises(UnicodeEncodeError):
            SOCLE._ecrire(self.coffre, "0-SAVOIRS/note.md", "corps \ud800\n")

        self.assertEqual(b"un contenu propre\n", vise.read_bytes(),
                         "une écriture ratée ne doit pas avoir tronqué le fichier")
        self.assertEqual([], sorted(p.name for p in dossier.glob(".*obsia-tmp*")),
                         "aucun fichier temporaire ne doit rester derrière")


if __name__ == "__main__":
    unittest.main()
