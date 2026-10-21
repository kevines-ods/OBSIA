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
MODELE = (Path(__file__).resolve().parent.parent
          / ".github" / "pull_request_template.md")

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

    def test_un_libelle_invente_devant_la_phrase_ne_declare_rien(self):
        """La phrase doit venir **juste après** la case.

        C'est la trappe qui a éteint un voyant à tort : une ligne
        `- [x] Case « Relu par le contradicteur » — …` contient bien la phrase,
        mais pas là où le contrôle la lit. Ces deux libellés sont ceux qu'on
        écrit naturellement quand on reformule la case — les accepter ferait
        passer pour cochée n'importe quelle prose qui cite la phrase. Ce qui
        **suit** la phrase reste toléré (« — 0 bloquant », « (voir #12) ») :
        c'est la place de la phrase qui compte, pas ce qui l'entoure.
        """
        for libelle in ("- [x] Case « %s » — revient à un humain",
                        "- [x] Relecture : %s"):
            with self.subTest(libelle=libelle):
                self.assertFalse(RELECTURE.relecture_declaree(
                    corps(case=libelle % RELECTURE.PHRASE)))

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

    def test_le_rouge_dit_la_ligne_a_ecrire(self):
        """Le message doit montrer la ligne, pas seulement nommer la phrase.

        Sans elle, celui qui vient de cocher une ligne qui *contient* la phrase
        n'a aucun moyen de voir que c'est son libellé qui cloche : c'est
        exactement ce qui a rendu un voyant rouge illisible une fois déjà.
        """
        resultat = lancer(corps(CASE_VIDE))
        attendue = RELECTURE.LIGNE_ATTENDUE
        self.assertIn(attendue, resultat.stdout)
        # L'annotation se lit dans l'onglet « Checks » sans ouvrir le journal :
        # c'est souvent la seule chose qu'on voit, elle doit porter la ligne.
        annotation = [ligne for ligne in resultat.stdout.splitlines()
                      if ligne.startswith("::error")]
        self.assertEqual(1, len(annotation), resultat.stdout)
        self.assertIn(attendue, annotation[0])


class TestModeleDePR(unittest.TestCase):
    """Le modèle de PR et le contrôle ne doivent pas dériver l'un sans l'autre.

    Les tests ci-dessus fabriquent leur ligne avec `PHRASE` : ils sont d'accord
    avec le contrôle par construction, et le resteront quoi qu'il arrive au
    modèle. Seul un test qui **lit** le modèle attrape l'écart entre ce que le
    modèle demande d'écrire et ce que le contrôle sait reconnaître — l'écart qui
    a produit un rouge incompréhensible.
    """

    def test_le_modele_porte_la_case_attendue(self):
        lignes = [ligne for ligne
                  in MODELE.read_text(encoding="utf-8").splitlines()
                  if RELECTURE.PHRASE in ligne]
        self.assertEqual(1, len(lignes),
                         "le modèle doit porter la phrase une seule fois : %r"
                         % lignes)
        self.assertEqual("- [ ] %s" % RELECTURE.PHRASE, lignes[0].strip())

    def test_la_ligne_prescrite_est_celle_du_motif(self):
        """Le message ne doit pas prescrire une ligne que le contrôle refuse.

        `LIGNE_ATTENDUE` est écrite à partir de `PHRASE`, mais rien ne la
        rattache au **motif** : un mainteneur pourrait la « améliorer » — une
        autre puce, un libellé devant la phrase — et le message se mettrait à
        prescrire exactement ce qui vaut un rouge, soit le défaut que cette PR
        corrige, par l'autre bout. Le sens inverse (la ligne du modèle cochée
        satisfait le motif) est tenu par le test suivant.
        """
        self.assertTrue(RELECTURE.CASE_COCHEE.search(RELECTURE.LIGNE_ATTENDUE),
                        "le message prescrit %r, que le motif %r refuse"
                        % (RELECTURE.LIGNE_ATTENDUE, RELECTURE.CASE_COCHEE.pattern))

    def test_un_corps_issu_du_modele_et_coche_declare_la_relecture(self):
        """Le geste réel : partir du modèle, cocher sa case, soumettre."""
        texte = MODELE.read_text(encoding="utf-8").replace(
            CASE_VIDE, CASE_COCHEE)
        self.assertIn(CASE_COCHEE, texte)
        self.assertTrue(RELECTURE.relecture_declaree(texte))
        resultat = lancer(texte)
        self.assertEqual(0, resultat.returncode,
                         resultat.stdout + resultat.stderr)


if __name__ == "__main__":
    unittest.main()
