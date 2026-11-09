"""Un agent en lecture seule ne déclare aucun skill qui écrit (§2)."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from verif_catalogue import verifier_references  # noqa: E402


class Ctx:
    def __init__(self):
        self.racine = Path(tempfile.mkdtemp())
        self.erreurs = []

    def erreur(self, chemin, message):
        self.erreurs.append(message)

    def avertir(self, chemin, message):
        pass


SKILLS = [{"name": "lit", "read_only": True, "_chemin": "lit.md"},
          {"name": "ecrit", "read_only": False, "_chemin": "ecrit.md"}]


class TestLectureSeule(unittest.TestCase):
    def test_un_agent_en_lecture_seule_qui_declare_un_skill_ecrivain_est_refuse(self):
        ctx = Ctx()
        verifier_references(ctx, [{"name": "relecteur", "read_only": True,
                                   "skills": ["lit", "ecrit"], "_chemin": "r.md"}], SKILLS)
        self.assertTrue(any("`ecrit`" in e for e in ctx.erreurs), ctx.erreurs)

    def test_un_agent_qui_ecrit_peut_le_declarer(self):
        ctx = Ctx()
        verifier_references(ctx, [{"name": "constructeur", "read_only": False,
                                   "skills": ["lit", "ecrit"], "_chemin": "c.md"}], SKILLS)
        self.assertFalse(any("lecture seule" in e for e in ctx.erreurs), ctx.erreurs)


if __name__ == "__main__":
    unittest.main()
