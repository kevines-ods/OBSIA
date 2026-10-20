"""Le mode embarqué de `generer_prompt.py` : un prompt autonome par agent.

Un poste distant ne porte ni le dépôt OBSIA ni le coffre parent : son prompt
n'a ni index à afficher ni noyau à désigner. Il doit donc porter l'en-tête qui
dit où l'agent opère, la règle des secrets, et le corps intégral du fichier
de l'agent — sa méthode tient en lui seul, sans renvoi vers ce que la machine
ne porte pas. Et comme il voyage, il ne doit porter **aucun chemin absolu**,
exactement comme l'AGENTS.md du coffre.

L'agent qui fonde le déploiement embarqué — `administrateur-mint` — est
versionné : les tests le lisent tel quel, plutôt que de fabriquer un coffre
de circonstance.
"""

import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True          # ne pas semer de __pycache__ dans le dépôt
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from generer_prompt import (RACINE_DEFAUT, chemins_absolus,     # noqa: E402
                            corps_declaratif, prompt_embarque,
                            regle_des_secrets)

AGENT = "administrateur-mint"
FICHIER_AGENT = RACINE_DEFAUT / "IA" / "agents" / f"{AGENT}.md"


class TestLePromptEmbarque(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prompt = prompt_embarque(RACINE_DEFAUT, AGENT)
        if cls.prompt is None:                      # lu avant chaque assert
            raise unittest.SkipTest(f"agent absent : {AGENT}")

    def test_il_dit_ou_l_agent_opere(self):
        self.assertIn("Tu opères sur un poste distant", self.prompt)

    def test_il_porte_le_corps_integral_de_l_agent(self):
        corps = corps_declaratif(FICHIER_AGENT)
        self.assertIsNotNone(corps)
        self.assertIn(corps, self.prompt)

    def test_le_frontmatter_n_y_entre_pas(self):
        self.assertNotIn("kind: agent", self.prompt)
        self.assertNotIn("read_only", self.prompt)
        self.assertIn("# Administrateur-mint", self.prompt)

    def test_il_porte_la_regle_des_secrets(self):
        regle = regle_des_secrets(RACINE_DEFAUT)
        if not regle:                     # un coffre de test sans noyau
            self.skipTest("noyau absent : règle des secrets vide")
        for ligne in regle.splitlines():
            self.assertIn(ligne, self.prompt)

    def test_il_n_indexe_rien_du_coffre(self):
        for absent in ("## Agents disponibles", "## Skills disponibles",
                       "## Tâches planifiées déclarées"):
            self.assertNotIn(absent, self.prompt)

    def test_il_ne_porte_aucun_chemin_absolu(self):
        # Cette garde vivait dans TestLesGardesDuModeEmbarque, où elle tenait
        # l'agent fondateur pour acquis : au public, il n'y est pas distribué,
        # et le test échouait au lieu de sauter. Elle vit ici, dans la classe
        # qui sait sauter — l'agent fondateur reste couvert là où il existe.
        self.assertEqual([], chemins_absolus(self.prompt))


class TestLesGardesDuModeEmbarque(unittest.TestCase):
    def test_agent_inconnu_rend_none(self):
        self.assertIsNone(prompt_embarque(RACINE_DEFAUT, "agent-inexistant"))

    def test_fichier_sans_frontmatter_rend_none(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            racine = Path(tmp)
            agents = racine / "IA" / "agents"
            agents.mkdir(parents=True)
            (agents / "sans-frontmatter.md").write_text(
                "Pas de frontmatter ici.\n", encoding="utf-8")
            self.assertIsNone(prompt_embarque(racine, "sans-frontmatter"))

    def test_aucun_chemin_absolu_de_machine(self):
        # `contradicteur` plutôt que l'agent fondateur : cette garde doit
        # tourner au public autant qu'à l'atelier, et le fondateur n'y est
        # pas distribué — sa propre garde vit une classe plus haut, où le
        # test sait sauter quand il manque.
        prompt = prompt_embarque(RACINE_DEFAUT, "contradicteur")
        self.assertIsNotNone(prompt)
        self.assertEqual([], chemins_absolus(prompt))


if __name__ == "__main__":
    unittest.main()
