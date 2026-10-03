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


if __name__ == "__main__":
    unittest.main()
