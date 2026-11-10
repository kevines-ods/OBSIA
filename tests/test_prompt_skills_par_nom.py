"""Ligne A1 (plan d'économie de contexte) : le prompt du coffre (et donc
`AGENTS.md`) nomme les skills sans recopier leur description.

La Méthode (§10) choisit l'agent, lit sa fiche, puis le skill : la
description d'un skill vit dans son frontmatter et dans `skills-index.md`,
pas dans le prompt (§5). Un skill qu'aucun agent ne déclare n'est jamais omis.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from generer_prompt import construire_prompt  # noqa: E402

AGENTS = [{"name": "un-agent", "description": "Fait une chose.", "read_only": False,
           "skills": ["voie-rapide"]}]
SKILLS = [{"name": "voie-rapide", "description": "Juger si un petit outil saute les portes. Suite."},
          {"name": "isole", "description": "Personne ne le déclare."}]


class TestSkillsParNom(unittest.TestCase):
    def setUp(self):
        self.prompt = construire_prompt(AGENTS, SKILLS)

    def test_la_description_d_un_skill_n_est_pas_recopiee(self):
        self.assertNotIn("Juger si un petit outil", self.prompt)

    def test_le_skill_reste_nomme_sous_son_agent(self):
        self.assertIn("skills : voie-rapide", self.prompt)

    def test_la_description_de_l_agent_reste(self):
        self.assertIn("Fait une chose.", self.prompt)

    def test_le_renvoi_donne_le_chemin_entier_de_l_index(self):
        self.assertIn("OBSIA/IA/system/skills-index.md", self.prompt)

    def test_un_skill_sans_agent_est_nomme_a_part(self):
        self.assertIn("Déclarés par aucun agent : isole.", self.prompt)


if __name__ == "__main__":
    unittest.main()
