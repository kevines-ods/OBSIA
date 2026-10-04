"""Le générateur de sommaires lit une note sans prendre son frontmatter pour du texte."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True          # ne pas semer de __pycache__ dans le dépôt
SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))        # `scripts/` n'est pas un paquet

import regenerate_sommaire as RS        # noqa: E402


class TestFrontmatter(unittest.TestCase):
    def lire(self, texte):
        with tempfile.TemporaryDirectory() as d:
            chemin = Path(d) / "2026-10-02-projet-sujet.md"
            chemin.write_text(texte, encoding="utf-8")
            return RS.lire_note(str(chemin))

    def test_le_frontmatter_n_entre_pas_dans_le_resume(self):
        note = self.lire("---\nagent: assistant\nprojet: projet\nstatut: clos\n---\n\n"
                         "# Titre\n\nLe vrai chapeau de la note, en prose.\n")
        self.assertNotIn("agent:", note["resume"])
        self.assertIn("vrai chapeau", note["resume"])

    def test_le_statut_du_frontmatter_fait_foi(self):
        note = self.lire("---\nagent: assistant\nprojet: projet\nstatut: clos\n---\n\n"
                         "# Titre\n\n## Statut\n🟡 En attente — piste ouverte.\n")
        self.assertEqual(note["statut"], "clos")

    def test_sans_frontmatter_le_statut_du_corps_reste_lu(self):
        note = self.lire("# Titre\n\nChapeau.\n\n## Statut\n🟢 Livré et fusionné.\n")
        self.assertIn("Livré", note["statut"])


class TestZonesDEcriture(unittest.TestCase):
    """Où les sommaires se sèment — et surtout où ils ne se sèment pas (§2)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.racine = base / "OBSIA"
        self.coffre = base
        self.racine.mkdir()
        self._avant = (RS.RACINE, RS.COFFRE, RS.ANCIENNE_MEMOIRE)
        self.addCleanup(self._restaurer)
        RS.RACINE = str(self.racine)
        RS.COFFRE = str(self.coffre)
        RS.ANCIENNE_MEMOIRE = str(self.racine / "mémoire")

    def _restaurer(self):
        RS.RACINE, RS.COFFRE, RS.ANCIENNE_MEMOIRE = self._avant

    def dossier(self, relatif):
        chemin = self.coffre / relatif
        chemin.mkdir(parents=True, exist_ok=True)
        return chemin

    def test_les_projets_et_les_chantiers_geles_portent_des_sommaires(self):
        self.dossier("0-PROJETS")
        self.dossier("0-MEMOIRES")
        self.assertEqual([str(self.coffre / "0-MEMOIRES"), str(self.coffre / "0-PROJETS")],
                         RS.racines_de_memoire())

    def test_les_autres_zones_n_en_portent_pas(self):
        for nom in ("0-SAVOIRS", "0-DOCUMENTS", "0-PERSONNELS", "0-EN-VRAC",
                    "-PROJETS", "-SAVOIRS", "-EN-VRAC", "0-MAINTENANCE"):
            self.dossier(nom)
        self.assertEqual([], RS.racines_de_memoire())

    def test_l_ancienne_memoire_du_produit_est_encore_servie(self):
        """Tant que la bascule dure, ses sommaires existent là (§11)."""
        (self.racine / "mémoire" / "projets").mkdir(parents=True)
        self.assertEqual([str(self.racine / "mémoire")], RS.racines_de_memoire())

    def test_sans_coffre_ni_ancienne_memoire_il_n_y_a_rien_a_resumer(self):
        self.assertEqual([], RS.racines_de_memoire())

    def test_l_ancienne_memoire_du_coffre_parent_n_est_pas_servie(self):
        """`-PROJETS` n'a jamais porté de sommaire : la bascule n'en sème pas."""
        self.dossier("-PROJETS/obsia/allegement")
        self.assertEqual([], RS.racines_de_memoire())


if __name__ == "__main__":
    unittest.main()
