#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Le dépôt de données du coffre (§7.1) : un seul écrivain, une poussée notée,
une fraîcheur vérifiable.

Ces tests montent de vrais dépôts git dans un dossier temporaire — un distant
nu local tient lieu de NAS — et jugent le script par ses codes de sortie.
"""

import datetime as dt
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

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
        """Appelle le script en étouffant son bavardage : on juge son code."""
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


if __name__ == "__main__":
    unittest.main()
