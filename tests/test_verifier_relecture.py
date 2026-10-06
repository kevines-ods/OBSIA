"""`verifier_relecture.py` : ce qui compte comme relecture déclarée.

Le §5 de `IA/skills/livraison-git.md` veut que la relecture du `contradicteur`
précède la soumission, et le modèle de PR en porte la trace. Un voyant qui
passerait au vert sans la case cochée ne dirait rien de la relecture : ces tests
fixent ce qu'elle accepte, et surtout ce qu'elle refuse — une phrase en prose,
une case vide, une autre case cochée. Ce qu'elle accepte se compte en formes de
Markdown : une case valide refusée ferait un faux rouge.
"""

import re
import subprocess
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import verifier_relecture as RELECTURE                        # noqa: E402

SCRIPT = SCRIPTS / "verifier_relecture.py"

# La phrase vient du script : si elle changeait là-bas, ces tests la suivraient
# au lieu de la contredire en silence.
CASE_VIDE = "- [ ] %s" % RELECTURE.PHRASE
CASE_COCHEE = "- [x] %s" % RELECTURE.PHRASE


def corps(case: str = CASE_VIDE, relecture: str = "#12") -> str:
    """Une description de PR complète, telle que le modèle la propose."""
    return ("## Demande\n\nCorriger le tilt.\n\n"
            "## Ce que ça change\n\n- une puce\n\n"
            "## Comment le vérifier\n\nLe rejouer.\n\n"
            "## Relecture\n\nRelecture : %s\n\n%s\n" % (relecture, case))


def lancer(texte: str) -> subprocess.CompletedProcess:
    """Le script, comme le workflow l'appelle : le texte par l'entrée standard."""
    return subprocess.run([sys.executable, "-B", str(SCRIPT)],
                          input=texte, capture_output=True, text=True,
                          timeout=30)


class TestRelectureDeclaree(unittest.TestCase):
    """La lecture de la case, sans passer par la ligne de commande."""

    def test_une_case_cochee_declare_la_relecture(self):
        for cochee in ("- [x] %s" % RELECTURE.PHRASE,
                       "- [X] %s" % RELECTURE.PHRASE,
                       "* [x] %s" % RELECTURE.PHRASE,
                       "  - [x] %s" % RELECTURE.PHRASE,
                       "- [x] %s" % RELECTURE.PHRASE.upper(),
                       "- [x] %s (voir #12)" % RELECTURE.PHRASE):
            with self.subTest(cochee=cochee):
                self.assertTrue(RELECTURE.relecture_declaree(corps(cochee)))

    def test_la_puce_plus_declare_la_relecture(self):
        """`+ [x]` est une case valide : la refuser serait un faux rouge."""
        self.assertTrue(RELECTURE.relecture_declaree(
            corps("+ [x] %s" % RELECTURE.PHRASE)))

    def test_une_liste_numerotee_declare_la_relecture(self):
        """`1. [x]` et `1) [x]` sont des cases valides : même chose."""
        for forme in ("1. [x] %s", "1) [x] %s", "2. [x] %s"):
            with self.subTest(forme=forme):
                self.assertTrue(RELECTURE.relecture_declaree(
                    corps(forme % RELECTURE.PHRASE)))

    def test_la_phrase_en_gras_declare_la_relecture(self):
        """`- [x] **Relu par le contradicteur**` reste la même case cochée."""
        for forme in ("- [x] **%s**", "- [x] **%s** (voir #12)"):
            with self.subTest(forme=forme):
                self.assertTrue(RELECTURE.relecture_declaree(
                    corps(forme % RELECTURE.PHRASE)))

    def test_la_phrase_n_a_qu_une_seule_ecriture(self):
        """Le motif se construit à partir de PHRASE : pas deux orthographes."""
        self.assertIn(re.escape(RELECTURE.PHRASE),
                      RELECTURE.CASE_COCHEE.pattern)

    def test_une_case_vide_ne_declare_rien(self):
        self.assertFalse(RELECTURE.relecture_declaree(corps(CASE_VIDE)))

    def test_la_phrase_en_prose_ne_declare_rien(self):
        """« Relu par le contradicteur » écrit à la main n'est pas une case."""
        texte = corps(relecture="relu par le contradicteur, voir #12",
                      case="<!-- -->")
        self.assertFalse(RELECTURE.relecture_declaree(texte))

    def test_une_autre_case_cochee_ne_declare_rien(self):
        self.assertFalse(RELECTURE.relecture_declaree(
            corps(case="- [x] Les tests passent")))

    def test_une_description_vide_ne_declare_rien(self):
        for texte in ("", "\n\n", None):
            with self.subTest(texte=texte):
                self.assertFalse(RELECTURE.relecture_declaree(texte))


class TestSortie(unittest.TestCase):
    """Le code de sortie et le message, tels que le workflow les lit."""

    def test_case_cochee_sort_en_zero(self):
        resultat = lancer(corps(CASE_COCHEE))
        self.assertEqual(0, resultat.returncode, resultat.stdout + resultat.stderr)
        self.assertIn("déclarée", resultat.stdout)

    def test_case_vide_sort_en_un_et_dit_quoi_faire(self):
        resultat = lancer(corps(CASE_VIDE))
        self.assertEqual(1, resultat.returncode)
        self.assertIn(RELECTURE.PHRASE, resultat.stdout)
        self.assertIn("session neuve", resultat.stdout)
        self.assertIn("signal, pas un verrou", resultat.stdout)
        # L'annotation est ce qui se lit dans l'onglet « Checks ».
        self.assertIn("::error title=Relecture adverse manquante::", resultat.stdout)

    def test_entree_vide_sort_en_un(self):
        resultat = lancer("")
        self.assertEqual(1, resultat.returncode)
        self.assertIn("::error title=Relecture adverse manquante::", resultat.stdout)


if __name__ == "__main__":
    unittest.main()
