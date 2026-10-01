"""La garde des noms interdits — `.githooks/pre-commit.d/20-noms-interdits`.

Elle relit les lignes **ajoutées** du commit contre la liste locale. Prouvé ici,
sur un vrai dépôt : un nom ajouté est refusé, un nom seulement retiré passe
(retirer une fuite ne doit pas être bloqué), un nom trop court est ignoré, et
sans liste rien n'est contrôlé.
"""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

GARDE = (Path(__file__).resolve().parent.parent
         / ".githooks" / "pre-commit.d" / "20-noms-interdits")


@unittest.skipUnless(shutil.which("git") and shutil.which("sh"), "git et sh requis")
class GardeNoms(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.depot = self.tmp / "depot"
        self.depot.mkdir()
        self.liste = self.tmp / "noms-interdits"
        self.liste.write_text("# hôtes\nposte-atelier\nia\n", encoding="utf-8")
        self.git("init", "-q", "-b", "main")
        (self.depot / "note.md").write_text("poste-atelier\n", encoding="utf-8")
        self.git("add", "-A")
        self.git("-c", "user.name=t", "-c", "user.email=t@example.com",
                 "commit", "-q", "--no-verify", "-m", "racine")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.depot, check=True, capture_output=True)

    def accepte(self, liste=None):
        env = dict(os.environ, OBSIA_NOMS_INTERDITS=str(liste or self.liste))
        return subprocess.run(["sh", str(GARDE)], cwd=self.depot, env=env,
                              capture_output=True).returncode == 0

    def ajouter(self, texte):
        (self.depot / "autre.md").write_text(texte, encoding="utf-8")
        self.git("add", "-A")

    def test_un_nom_ajoute_est_refuse(self):
        self.ajouter("À lancer sur Poste-Atelier.\n")
        self.assertFalse(self.accepte())

    def test_retirer_un_nom_passe(self):
        (self.depot / "note.md").write_text("le poste secondaire\n", encoding="utf-8")
        self.git("add", "-A")
        self.assertTrue(self.accepte())

    def test_un_nom_trop_court_est_ignore(self):
        self.ajouter("Voir IA/system/.\n")
        self.assertTrue(self.accepte())

    def test_sans_liste_rien_n_est_controle(self):
        self.ajouter("poste-atelier\n")
        self.assertTrue(self.accepte(self.tmp / "absente"))


if __name__ == "__main__":
    unittest.main()
