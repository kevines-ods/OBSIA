"""Le ménage des worktrees ne retire que le travail d'agent fusionné et propre.

La décision (`classer`) se prouve sans git. Un vrai dépôt, avec un distant,
prouve ensuite le calcul des faits (`examiner`), là où se logent les erreurs :
un worktree **neuf** sur `origin/main` descend lui aussi de la branche par
défaut, et doit rester (relecture adverse de la PR #291). Seul le worktree dont
la branche d'agent porte un commit fusionné, sans rien d'autre dedans, part.
"""

import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import ranger_worktrees  # noqa: E402
from ranger_worktrees import (  # noqa: E402
    GARDER, RETIRER, classer, fichiers_bloquants, hors_racine, lire_worktrees, main,
)

BON = {"principal": False, "present": True, "verrouille": False, "agent": True,
       "travail": True, "fusionne": True, "propre": True, "calme": True}


class Decision(unittest.TestCase):
    def test_tout_bon_se_retire(self):
        self.assertEqual(classer(BON)[0], RETIRER)

    def test_chaque_condition_garde(self):
        for cle, valeur in (("principal", True), ("present", False), ("verrouille", True),
                            ("agent", False), ("travail", False), ("fusionne", False),
                            ("propre", False), ("calme", False)):
            with self.subTest(cle=cle):
                self.assertEqual(classer(dict(BON, **{cle: valeur}))[0], GARDER)

    def test_fait_absent_garde(self):
        faits = dict(BON)
        del faits["travail"]
        self.assertEqual(classer(faits)[0], GARDER)

    def test_lecture_porcelaine(self):
        sortie = ("worktree /depot\nHEAD 111\nbranch refs/heads/main\n\n"
                  "worktree /w/a\nHEAD 222\nbranch refs/heads/batisseur/a\nlocked\n\n"
                  "worktree /w/b\nHEAD 333\ndetached\n")
        liste = lire_worktrees(sortie)
        self.assertEqual([w["principal"] for w in liste], [True, False, False])
        self.assertTrue(liste[1]["verrouille"])
        self.assertIsNone(liste[2]["branche"])

    def test_fichiers_ignores(self):
        self.assertEqual(fichiers_bloquants("!! scripts/__pycache__/\n"), [])
        self.assertEqual(fichiers_bloquants("!! .env\n"), ["!! .env"])
        self.assertEqual(fichiers_bloquants("?? note.md\n"), ["?? note.md"])

    def test_hors_racine(self):
        racine = Path("/home/x/obsia-worktrees")
        self.assertFalse(hors_racine("/home/x/obsia-worktrees/assistant-a", racine))
        self.assertTrue(hors_racine("/tmp/assistant-a", racine))


def g(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], check=True,
                          capture_output=True, text=True).stdout


class BoutEnBout(unittest.TestCase):
    """Un dépôt, son distant, et un worktree par cas."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        distant, self.depot = base / "distant.git", base / "depot"
        g(base, "init", "-q", "--bare", "-b", "main", str(distant))
        g(base, "clone", "-q", str(distant), str(self.depot))
        for cle, val in (("user.email", "t@example.invalid"), ("user.name", "t"),
                         ("commit.gpgsign", "false"), ("core.hooksPath", "/dev/null")):
            g(self.depot, "config", cle, val)
        (self.depot / ".gitignore").write_text(".env\n__pycache__/\n")
        g(self.depot, "add", ".gitignore")
        g(self.depot, "commit", "-q", "-m", "départ")
        g(self.depot, "push", "-q", "origin", "main")
        g(self.depot, "remote", "set-head", "origin", "main")
        self.wt = base / "wt"
        # Fusionnés : un commit chacun, puis fusion dans main poussée.
        for nom in ("fusionne", "modifie", "ignore", "cache", "verrou"):
            self.ouvrir(nom)
            g(self.wt / nom, "commit", "-q", "--allow-empty", "-m", nom)
            g(self.depot, "merge", "-q", "--no-ff", "-m", f"fusion {nom}", f"batisseur/{nom}")
        self.ouvrir("perso", branche="perso/perso")
        g(self.wt / "perso", "commit", "-q", "--allow-empty", "-m", "perso")
        g(self.depot, "merge", "-q", "--no-ff", "-m", "fusion perso", "perso/perso")
        g(self.depot, "push", "-q", "origin", "main")
        # Non fusionné, neuf, détaché : sur origin/main à jour.
        self.ouvrir("encours")
        g(self.wt / "encours", "commit", "-q", "--allow-empty", "-m", "en cours")
        self.ouvrir("neuf")
        g(self.depot, "worktree", "add", "-q", "--detach", str(self.wt / "detache"), "origin/main")
        (self.wt / "modifie" / "brouillon.txt").write_text("x")
        (self.wt / "ignore" / ".env").write_text("CLE=x")
        (self.wt / "cache" / "__pycache__").mkdir()
        (self.wt / "cache" / "__pycache__" / "m.pyc").write_text("x")
        g(self.depot, "worktree", "lock", str(self.wt / "verrou"))

    def ouvrir(self, nom, branche=None):
        g(self.depot, "worktree", "add", "-q", str(self.wt / nom),
          "-b", branche or f"batisseur/{nom}", "origin/main")

    def tearDown(self):
        self.tmp.cleanup()

    def lancer(self, *args, calme=-1):
        with mock.patch.object(ranger_worktrees, "CALME", calme), \
                redirect_stdout(io.StringIO()) as sortie:
            code = main([str(self.depot), *args], agents={"batisseur"})
        return code, sortie.getvalue()

    def test_apercu_ne_retire_rien(self):
        code, sortie = self.lancer()
        self.assertEqual(code, 0)
        self.assertIn("2 à retirer", sortie)
        self.assertTrue((self.wt / "fusionne").is_dir())

    def test_appliquer_ne_retire_que_le_travail_fusionne_propre(self):
        code, sortie = self.lancer("--appliquer")
        self.assertEqual(code, 0, sortie)
        for parti in ("fusionne", "cache"):
            self.assertFalse((self.wt / parti).exists(), parti)
        for reste in ("neuf", "detache", "encours", "modifie", "ignore", "perso", "verrou"):
            self.assertTrue((self.wt / reste).is_dir(), reste)
        self.assertTrue((self.wt / "ignore" / ".env").exists())
        branches = g(self.depot, "branch")
        self.assertNotIn("batisseur/fusionne", branches)
        self.assertIn("batisseur/neuf", branches)

    def test_activite_recente_garde(self):
        _, calmes = self.lancer()
        _, actifs = self.lancer(calme=3600)
        self.assertIn("2 à retirer", calmes)
        self.assertIn("0 à retirer", actifs)
        self.assertEqual(actifs.count("activité dans l'heure"), 2)

    def test_branche_partie_meme_si_main_local_en_retard(self):
        # La branche a été poussée (`push -u`), sa branche distante supprimée
        # à la fusion : son amont a disparu. `git branch -d` se compare alors au
        # `main` local, ici en arrière d'`origin/main` — il refuserait, et la
        # branche resterait orpheline (contre-relecture #291).
        g(self.depot, "config", "branch.batisseur/fusionne.merge", "refs/heads/batisseur/fusionne")
        g(self.depot, "reset", "-q", "--hard", "HEAD~6")
        code, sortie = self.lancer("--appliquer")
        self.assertEqual(code, 0, sortie)
        self.assertNotIn("batisseur/fusionne", g(self.depot, "branch"))

    def test_depot_illisible(self):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main([self.tmp.name + "/absent"]), 1)


if __name__ == "__main__":
    unittest.main()
