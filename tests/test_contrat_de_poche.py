"""Ligne A2 (plan d'économie de contexte) : le contrat de poche.

Ce que reçoit un délégué qui écrit, à la place de l'`AGENTS.md` et du noyau
entier : les règles qui protègent l'acte d'écrire, extraites du noyau à
chaque appel (jamais stockées, donc jamais périmées), mot pour mot.
"""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from generer_prompt import (NOYAU, RACINE_DEFAUT, NoyauIncomplet,  # noqa: E402
                            SECTIONS_DE_POCHE, prompt_de_poche)


class TestContratDePoche(unittest.TestCase):
    def setUp(self):
        self.noyau = (RACINE_DEFAUT / NOYAU).read_text(encoding="utf-8")
        self.poche = prompt_de_poche(RACINE_DEFAUT)

    def test_il_porte_chaque_section_attendue(self):
        for niveau, numero, mot in SECTIONS_DE_POCHE:
            self.assertIn(f"{niveau} {numero} {mot}", self.poche)
        self.assertIn("## Écriture (§2)", self.poche)
        self.assertIn("sandbox", self.poche)

    def test_chaque_ligne_vient_du_noyau(self):
        en_tete = {"# Contrat de poche — délégué qui écrit", "## Écriture (§2)"}
        lignes_noyau = set(self.noyau.splitlines())
        for ligne in self.poche.splitlines():
            if ligne and ligne not in en_tete and not ligne.startswith("Extrait engendré"):
                self.assertIn(ligne, lignes_noyau, "ligne absente du noyau : recopie ?")

    def test_il_est_bien_plus_court_que_le_noyau(self):
        self.assertLess(len(self.poche), len(self.noyau) // 3)

    def test_sans_noyau_rien(self):
        vide = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, vide)
        self.assertIsNone(prompt_de_poche(vide))

    def _coffre_avec(self, noyau: str) -> Path:
        racine = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, racine)
        (racine / NOYAU).parent.mkdir(parents=True)
        (racine / NOYAU).write_text(noyau, encoding="utf-8")
        return racine

    def test_un_titre_reformule_leve(self):
        racine = self._coffre_avec(self.noyau.replace("## 9. Trace", "## 9. Journal"))
        with self.assertRaises(NoyauIncomplet):
            prompt_de_poche(racine)

    def test_une_renumerotation_leve(self):
        racine = self._coffre_avec(self.noyau.replace("### 7.3.1 Où", "### 7.3.2 Où"))
        with self.assertRaises(NoyauIncomplet):
            prompt_de_poche(racine)

    def test_7_3_s_arrete_avant_7_3_1(self):
        debut = self.poche.index("### 7.3 Écriture")
        fin = self.poche.index("### 7.3.1 Où")
        self.assertNotIn("### 7.4", self.poche[debut:fin])
        self.assertEqual(self.poche.count("### 7.3.1 Où"), 1)


    def test_les_phrases_de_fin_de_section_y_sont(self):
        # Une phrase protectrice proche de la fin de chaque section : un titre
        # intrus qui couperait la section ferait disparaître sa queue. Si le
        # noyau reformule l'une d'elles, ce test se relit avec lui.
        for phrase in ("sandbox",
                       "procédure dans un skill.",
                       "On n'y déplace ni n'y supprime rien.",
                       "son contenu ne migre jamais dans `OBSIA/`.",
                       "`contrat-memoire`.",
                       "séquence avant un commit : `contrat-verification`."):
            self.assertIn(phrase, self.poche)

    def test_poche_refuse_un_fichier_de_sortie(self):
        import subprocess
        r = subprocess.run([sys.executable, str(RACINE_DEFAUT / "scripts" / "generer_prompt.py"),
                            "--poche", "-o", "/dev/null"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)


if __name__ == "__main__":
    unittest.main()
