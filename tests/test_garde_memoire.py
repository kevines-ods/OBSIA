"""La garde de la mémoire hors dépôt (§6 et §7.1) —
`.githooks/pre-commit.d/30-memoire-hors-depot`.

La mémoire a quitté le dépôt produit. Ce qui doit être prouvé, c'est que la
garde **refuse** les trois formes revenues : l'ancien `mémoire/`, une zone de
coffre `0-…/`, et son ancien nom `-…/` (tolérance de bascule). Et qu'elle laisse
passer le reste — un fichier de `IA/`, une suppression (par laquelle passera la
migration), l'ancienne archive figée.

Les tests touchent le disque : l'index git est ce que la garde relit.
"""

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

GARDE = (Path(__file__).resolve().parent.parent
         / ".githooks" / "pre-commit.d" / "30-memoire-hors-depot")


def git(dossier, *args):
    subprocess.run(["git", *args], cwd=dossier, check=True,
                   capture_output=True, text=True)


@unittest.skipUnless(shutil.which("git") and shutil.which("sh"), "git et sh requis")
class GardeMemoire(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.depot = self.tmp / "depot"
        (self.depot / "IA" / "agents").mkdir(parents=True)
        (self.depot / "IA" / "agents" / "assistant.md").write_text("x\n")
        self.ecrire("mémoire/vieux.md", "à retirer un jour.\n")
        git(self.depot, "init", "-q", "-b", "main")
        git(self.depot, "config", "user.name", "t")
        git(self.depot, "config", "user.email", "t@exemple.invalid")
        git(self.depot, "add", "-A")
        git(self.depot, "commit", "-q", "-m", "racine")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def ecrire(self, relatif, contenu="x\n") -> Path:
        chemin = self.depot / relatif
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(contenu, encoding="utf-8")
        return chemin

    def accepte(self) -> bool:
        return subprocess.run(["sh", str(GARDE)], cwd=self.depot,
                              capture_output=True).returncode == 0

    def refus(self, relatif) -> bool:
        git(self.depot, "add", "--", relatif)
        return not self.accepte()

    def test_un_fichier_de_l_ancienne_memoire_est_refuse(self):
        self.ecrire("mémoire/notes.md")
        self.assertTrue(self.refus("mémoire/notes.md"))

    def test_une_zone_de_coffre_est_refusee(self):
        self.ecrire("0-PROJETS/un-projet/carnets/carnet.md")
        self.assertTrue(self.refus("0-PROJETS/un-projet/carnets/carnet.md"))

    def test_l_ancien_nom_de_zone_est_refuse(self):
        self.ecrire("-SAVOIRS/note.md")
        self.assertTrue(self.refus("-SAVOIRS/note.md"))

    def test_un_fichier_ordinaire_passe(self):
        self.ecrire("IA/agents/nouveau.md")
        self.assertFalse(self.refus("IA/agents/nouveau.md"))

    def test_une_suppression_de_memoire_passe(self):
        """C'est par la suppression que la migration se fera."""
        git(self.depot, "rm", "-q", "mémoire/vieux.md")
        self.assertTrue(self.accepte())

    def test_l_ancienne_archive_figee_passe(self):
        self.ecrire(".archive/mémoire/vieux.md")
        self.assertFalse(self.refus(".archive/mémoire/vieux.md"))

    def test_un_fichier_a_plat_prefixe_0_n_est_pas_une_zone(self):
        """Une zone est un dossier : `0-note.md` n'est pas `0-PROJETS/`."""
        self.ecrire("0-note.md")
        self.assertFalse(self.refus("0-note.md"))

    def test_hors_depot_git_la_garde_se_tait(self):
        self.assertTrue(subprocess.run(["sh", str(GARDE)], cwd=self.tmp,
                                       capture_output=True).returncode == 0)


if __name__ == "__main__":
    unittest.main()
