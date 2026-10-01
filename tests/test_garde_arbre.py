"""La garde du travail en parallèle (§2.1) — `.githooks/pre-commit.d/10-arbre-de-travail`.

Plusieurs agents partagent le dépôt. Ce qui doit être prouvé, c'est que la
garde **refuse** là où un commit s'égarerait : sur la branche par défaut,
partout ; dans l'arbre principal ou sous un préfixe d'agent inconnu, sur une
machine qui l'a demandé. Et qu'elle laisse passer le reste — un clone de la
distribution n'a pas à s'imposer des worktrees.

Les tests touchent le disque : la différence entre arbre principal et worktree
lié n'existe que dans un vrai dépôt git.
"""

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

GARDE = (Path(__file__).resolve().parent.parent
         / ".githooks" / "pre-commit.d" / "10-arbre-de-travail")


def git(dossier, *args):
    subprocess.run(["git", *args], cwd=dossier, check=True,
                   capture_output=True, text=True)


@unittest.skipUnless(shutil.which("git") and shutil.which("sh"), "git et sh requis")
class GardeArbre(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.depot = self.tmp / "depot"
        (self.depot / "IA" / "agents").mkdir(parents=True)
        for agent in ("assistant", "batisseur"):
            (self.depot / "IA" / "agents" / (agent + ".md")).write_text("x\n")
        git(self.depot, "init", "-q", "-b", "main")
        git(self.depot, "add", "-A")
        git(self.depot, "-c", "user.name=t", "-c", "user.email=t@example.com",
            "commit", "-q", "-m", "racine")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def accepte(self, dossier):
        return subprocess.run(["sh", str(GARDE)], cwd=dossier,
                              capture_output=True).returncode == 0

    def worktree(self, branche):
        chemin = self.tmp / branche.replace("/", "-")
        git(self.depot, "worktree", "add", "-q", "-b", branche, str(chemin))
        return chemin

    def test_branche_par_defaut_refusee_meme_sans_configuration(self):
        self.assertFalse(self.accepte(self.depot))

    def test_sans_configuration_une_branche_libre_passe(self):
        git(self.depot, "checkout", "-q", "-b", "essai")
        self.assertTrue(self.accepte(self.depot))

    def test_arbre_principal_refuse_meme_avec_le_bon_prefixe(self):
        git(self.depot, "config", "obsia.arbresSepares", "true")
        git(self.depot, "checkout", "-q", "-b", "assistant/essai")
        self.assertFalse(self.accepte(self.depot))

    def test_worktree_avec_prefixe_d_agent_passe(self):
        git(self.depot, "config", "obsia.arbresSepares", "true")
        self.assertTrue(self.accepte(self.worktree("batisseur/essai")))

    def test_worktree_avec_prefixe_inconnu_refuse(self):
        git(self.depot, "config", "obsia.arbresSepares", "true")
        self.assertFalse(self.accepte(self.worktree("fantome/essai")))

    def test_head_detache_n_est_pas_garde(self):
        git(self.depot, "config", "obsia.arbresSepares", "true")
        git(self.depot, "checkout", "-q", "--detach")
        self.assertTrue(self.accepte(self.depot))


if __name__ == "__main__":
    unittest.main()
