"""Le plancher du projet, mesuré — pas seulement déclaré.

`CONSTRAINTS.md` chiffre le niveau de qualité de `serveur/` et du **moteur
partagé**. Ce module **mesure** ces chiffres, pour qu'ils ne restent pas un vœu :

- le nombre de tests de la suite ne descend pas sous le plancher déclaré ;
- chaque contrôle de la porte a au moins un test nommé qui le cite ;
- `serveur/` et le moteur partagé n'importent que la bibliothèque standard ;
- ils ne nomment aucun harnais (§3) et ne portent aucun chemin de machine (§13).

Il ne teste pas le serveur : il teste la **tenue du plancher**. Les règles d'un
diff — ne pas faire taire un vérificateur, ne pas alléger un test, ne pas laisser
de travail inachevé, ne pas desserrer un seuil — sont d'un autre genre : elles se
lisent dans un *diff*, pas dans l'arbre, et c'est le rôle de `garde_plancher.py`.
"""

import ast
import re
import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
TESTS = RACINE / "tests"
SERVEUR = RACINE / "serveur"
SCRIPTS = RACINE / "scripts"
PORTE = SERVEUR / "porte_entree.py"
TESTS_DE_LA_PORTE = TESTS / "test_porte_entree.py"
CONSTRAINTS = RACINE / "CONSTRAINTS.md"

# Le **moteur partagé** : la convention des notes et la garde des secrets. Le
# serveur les importe, et les scripts du coffre appellent la même copie.
MOTEUR = (
    SCRIPTS / "convention_des_notes.py",
    SCRIPTS / "garde_secrets.py",
)

# Un nom de harnais dans le moteur ou le serveur serait une dépendance cachée :
# seule une fiche d'adaptation en nomme un (§3).
HARNAIS = ("opencode", "codex", "claude", "aionui", "gemini", "cursor",
           "copilot", "windsurf", "goose", "cline", "roo")

# Un chemin de machine ferait entrer un poste dans la règle (§13). On resserre :
# un chemin de home (`~/…`) compte toujours ; un chemin absolu ou Windows compte
# à partir de **deux** segments — une route d'API comme `/notes` n'est pas un
# chemin de machine. Un antislash unique en tête n'en est pas un non plus : c'est
# un ancrage de motif (`"\A…"`), pas un chemin Windows — il faut deux antislashs
# (chemin UNC) ou un lecteur (`C:`).
CHEMIN_DE_MACHINE = re.compile(
    r"^~/[A-Za-z0-9._-]"                      # chemin de home (`"~/"` seul est un préfixe)
    r"|^/[A-Za-z0-9._-]+/"                     # absolu, deux segments au moins
    r"|^\\\\[A-Za-z0-9._-]+\\"                 # chemin UNC
    r"|^[A-Za-z]:\\")                          # lecteur Windows


def _modules_de_la_bibliotheque():
    """Les noms de modules de la bibliothèque standard.

    `sys.stdlib_module_names` existe depuis Python 3.10, que visent la suite et
    le moteur. Sur un interpréteur plus ancien, on retombe sur
    `sys.builtin_module_names` : un contrôle partiel, jamais un contrôle éteint.
    """
    noms = getattr(sys, "stdlib_module_names", None)
    if noms is not None:
        return set(noms)
    return set(sys.builtin_module_names)


def _sous_plancher():
    """(chemin, texte) de tout le code sous plancher, sous-dossiers compris."""
    fichiers = sorted(SERVEUR.rglob("*.py")) + list(MOTEUR)
    return [(f, f.read_text(encoding="utf-8")) for f in fichiers]


def _ligne_de_seuil(libelle):
    """La ligne de `CONSTRAINTS.md` dont le premier libellé est exactement celui-là.

    Exactement : un libellé renommé ne doit pas laisser croire que le chiffre
    tient encore. Le garde compte un libellé disparu comme un seuil disparu, et
    ce test le dit ici plutôt que de retomber silencieusement sur autre chose.
    """
    for ligne in CONSTRAINTS.read_text(encoding="utf-8").splitlines():
        texte = ligne.strip()
        if not texte.startswith("|"):
            continue
        champs = [c.strip() for c in texte.strip("|").split("|")]
        if champs and champs[0] == libelle:
            return ligne
    return None


def _plancher_du_nombre_de_tests():
    """Le nombre déclaré dans `CONSTRAINTS.md`, ligne « Nombre de tests »."""
    ligne = _ligne_de_seuil("Nombre de tests")
    if ligne is None:
        raise AssertionError(
            "CONSTRAINTS.md n'a pas de ligne de seuil « Nombre de tests » (libellé "
            "exact) : le plancher n'est pas mesurable, et un plancher qu'on ne "
            "mesure pas n'existe pas.")
    trouve = re.search(r"≥\s*\**\s*(\d+)", ligne)
    if not trouve:
        raise AssertionError(
            "CONSTRAINTS.md : la ligne « Nombre de tests » ne porte pas de chiffre "
            "≥ : %r" % ligne)
    return int(trouve.group(1))


def _est_refus(noeud):
    """Vrai si le nœud est un appel à `Refus(...)`."""
    if not isinstance(noeud, ast.Call) or not noeud.args:
        return False
    fonction = noeud.func
    nom = fonction.id if isinstance(fonction, ast.Name) else getattr(fonction, "attr", None)
    return nom == "Refus"


def _controles_de_la_porte():
    """Les noms de contrôle que la porte peut opposer (ses appels `Refus`)."""
    controles = set()
    for noeud in ast.walk(ast.parse(PORTE.read_text(encoding="utf-8"))):
        if not _est_refus(noeud):
            continue
        premier = noeud.args[0]
        if isinstance(premier, ast.Constant) and isinstance(premier.value, str):
            controles.add(premier.value)
    return controles


def _tests_qui_nomment(controle):
    """Les fonctions `test_*` dont le corps cite ce nom de contrôle."""
    source = TESTS_DE_LA_PORTE.read_text(encoding="utf-8")
    trouvees = set()
    for noeud in ast.walk(ast.parse(source)):
        if isinstance(noeud, ast.FunctionDef) and noeud.name.startswith("test_"):
            textes = {n.value for n in ast.walk(noeud)
                      if isinstance(n, ast.Constant) and isinstance(n.value, str)}
            if controle in textes:
                trouvees.add(noeud.name)
    return trouvees


class TestLePlancherDuProjet(unittest.TestCase):

    def test_le_nombre_de_tests_ne_descend_pas_sous_le_plancher(self):
        plancher = _plancher_du_nombre_de_tests()
        trouve = unittest.TestLoader().discover(str(TESTS)).countTestCases()
        self.assertGreaterEqual(
            trouve, plancher,
            "la suite ne compte que %d tests, sous le plancher de %d : un test a "
            "disparu, ou le chiffre de CONSTRAINTS.md a été baissé."
            % (trouve, plancher))

    def test_chaque_controle_de_la_porte_a_un_test_nomme(self):
        controles = _controles_de_la_porte()
        self.assertTrue(
            controles, "aucun contrôle lu dans la porte : le test ne mesure rien")
        sans_test = sorted(c for c in controles if not _tests_qui_nomment(c))
        self.assertEqual(
            sans_test, [],
            "ces contrôles de la porte n'ont aucun test nommé : %s" % sans_test)

    def test_le_serveur_et_le_moteur_n_importent_que_la_bibliotheque_standard(self):
        # Noms de modules disponibles sans rien installer : la bibliothèque
        # standard, plus le premier parti (le dépôt lui-même).
        premier = {f.stem for f in SERVEUR.rglob("*.py")}
        premier |= {f.stem for f in SCRIPTS.glob("*.py")}
        bibliotheque = _modules_de_la_bibliotheque()
        tiers = set()
        for _, texte in _sous_plancher():
            for noeud in ast.walk(ast.parse(texte)):
                if isinstance(noeud, ast.Import):
                    noms = [a.name.split(".")[0] for a in noeud.names]
                elif isinstance(noeud, ast.ImportFrom):
                    if noeud.level or not noeud.module:   # relatif ou `from .`
                        continue
                    noms = [noeud.module.split(".")[0]]
                else:
                    continue
                tiers |= {n for n in noms
                          if n not in bibliotheque and n not in premier}
        self.assertEqual(sorted(tiers), [],
                         "paquets hors bibliothèque standard : %s" % sorted(tiers))

    def test_aucun_refus_ne_porte_un_libelle_non_litteral(self):
        """Un libellé calculé échapperait à la mesure de couverture des contrôles."""
        flottants = []
        for noeud in ast.walk(ast.parse(PORTE.read_text(encoding="utf-8"))):
            if not _est_refus(noeud):
                continue
            premier = noeud.args[0]
            if not (isinstance(premier, ast.Constant) and isinstance(premier.value, str)):
                flottants.append(noeud.lineno)
        self.assertEqual(
            flottants, [],
            "ces appels `Refus` portent un libellé qui n'est pas une chaîne "
            "littérale : la couverture des contrôles ne les voit pas — lignes %s"
            % flottants)

    def test_aucun_nom_de_harnais_dans_le_serveur_ni_le_moteur(self):
        trouves = []
        for chemin, texte in _sous_plancher():
            for nom in HARNAIS:
                if re.search(r"\b%s\b" % re.escape(nom), texte, re.IGNORECASE):
                    trouves.append("%s : %s" % (chemin.name, nom))
        self.assertEqual(
            trouves, [],
            "harnais nommés hors des fiches d'adaptation (§3) : %s" % trouves)

    def test_aucun_chemin_de_machine_dans_le_serveur_ni_le_moteur(self):
        trouves = []
        for chemin, texte in _sous_plancher():
            for noeud in ast.walk(ast.parse(texte)):
                if isinstance(noeud, ast.Constant) and isinstance(noeud.value, str) \
                        and CHEMIN_DE_MACHINE.match(noeud.value):
                    trouves.append("%s:%d" % (chemin.name, noeud.lineno))
        self.assertEqual(
            trouves, [],
            "chemins de machine dans le produit (§13) : %s" % trouves)


if __name__ == "__main__":
    unittest.main()
