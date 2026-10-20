"""Le banc de processus : ce qu'il compte, et le plafond qu'il défend."""
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import banc_de_processus as BANC  # noqa: E402

RACINE = Path(__file__).resolve().parent.parent


class TestLeCompteur(unittest.TestCase):
    """Le compteur compte les processus réellement lancés, pas les intentions."""

    def setUp(self):
        self.compteur = BANC.Compteur()
        self.compteur.installer()
        self.addCleanup(self.compteur.desinstaller)

    def test_un_popen_est_compte(self):
        avant = self.compteur.popen
        subprocess.run([sys.executable, "-c", "pass"], check=True)
        self.assertEqual(self.compteur.popen, avant + 1)

    def test_un_run_de_plusieurs_commandes_compte_chacune(self):
        avant = self.compteur.popen
        subprocess.run([sys.executable, "-c", "pass"], check=True)
        subprocess.run([sys.executable, "-c", "pass"], check=True)
        self.assertEqual(self.compteur.popen, avant + 2)

    def test_le_total_ne_compte_pas_deux_fois_les_posix_spawn(self):
        """`subprocess` s'appuie sur `os.posix_spawn` ici : compter les deux compte un processus deux fois.

        Mesuré sur la suite : 5 260 `Popen` et 211 `posix_spawn`, quand la mesure
        de référence ne comptait que des processus — les 211 sont les mêmes, vus
        d'un étage plus bas. Le total les ignore donc, mais le rapport les montre :
        un `posix_spawn` lancé sans `Popen` serait, lui, un processus de plus.
        """
        self.compteur.popen = 4
        self.compteur.system = 1
        self.compteur.posix_spawn = 2
        self.assertEqual(self.compteur.total(), 5)
        self.assertIn("posix_spawn=2", self.compteur.rapport())

    def test_desinstaller_rend_la_main(self):
        self.compteur.desinstaller()
        self.assertIs(subprocess.Popen, self.compteur._originaux["popen"])


class TestLePlafond(unittest.TestCase):
    """Le plafond est un chiffre mesuré, écrit une fois, et le même partout."""

    def test_le_plafond_est_le_chiffre_de_constraints(self):
        """`CONSTRAINTS.md` le dit, le banc le porte : les deux ne peuvent pas diverger."""
        contraintes = (RACINE / "CONSTRAINTS.md").read_text(encoding="utf-8")
        chiffre = "{:,}".format(BANC.PLAFOND).replace(",", " ")
        self.assertIn(chiffre, contraintes.replace("\u202f", " ")
                      .replace("\u00a0", " "),
                      "le plafond du banc n'est pas écrit dans CONSTRAINTS.md")

    def test_le_plafond_est_la_mesure_plus_deux_pour_cent(self):
        """5 183 processus mesurés le 2026-10-17, plus 2 % — arrondi vers le haut."""
        self.assertEqual(BANC.PLAFOND, 5_287)
        self.assertGreaterEqual(BANC.PLAFOND, BANC.MESURE * 1.02)
        self.assertLess(BANC.PLAFOND, BANC.MESURE * 1.03)

    def test_depasser_le_plafond_se_voit(self):
        self.assertFalse(BANC.depasse(5_287, 5_287))
        self.assertTrue(BANC.depasse(5_288, 5_287))


if __name__ == "__main__":
    unittest.main()
