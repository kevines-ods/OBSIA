#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Garde-plancher : refuse un diff qui baisse le niveau de qualité du projet.

Cinq gestes font passer un changement au vert sans le rendre meilleur : faire
taire un vérificateur, rendre un test plus facile, laisser du travail
inachevé, déplacer un seuil, négocier la règle. Ce script les cherche dans le
diff, et seulement eux.

Principe directeur : **resserrer est silencieux, desserrer est bruyant.**
Rien n'est signalé quand la barre monte.

Limite assumée, écrite ici parce que c'est ici que la règle vit : « une assertion
d'un test qui reste ne disparaît pas » se juge **par portée survivante**, sur
l'arbre syntaxique des deux versions : un test, une fonction d'aide, une méthode,
le module. Une aide qui perd son `assert` compte autant qu'un test qui perd son
`assertEqual` — et la carte garde les portées à zéro assertion, sinon perdre la
**dernière** ressemblerait à une fonction effacée.

Une portée renommée ou effacée n'est plus comparable, et le détecteur « un
`def test_` a disparu » a été **mesuré puis écarté** — 9 constats sur les 120
derniers commits, dont deux renommages purs, pour un seuil fixé d'avance à 3.
Ne le réinvente pas sans une nouvelle mesure.

Deux choses que cette comparaison emporte, et qu'il faut savoir avant de la
lire comme un défaut :
- **extraire** des assertions d'un test vers une aide — même légitime — allège
  le test, donc **rougit**. C'est voulu : sans cela, vider un test en déportant
  ses assertions dans une aide passerait au vert. Une extraction honnête
  s'acquitte.
- l'exception `E<n>` du tableau de CONSTRAINTS.md porte sur le **fichier** — un
  glob `fnmatch`, comme `.plancherignore` — pas sur le test ni sur la ligne :
  l'écrire pour acquitter une extraction couvre ce fichier pour cette règle,
  tests voisins compris. Ce n'est pas une exception de ligne déguisée.

Ce que le garde **ne sait pas peser** : il compte des nœuds, ni leur force ni
leur exécution. `self.assertEqual(v.refus.controle, "absence de secret")` qui
devient `self.assertTrue(True)` le laisse à 2 → 2, et il rend 0 ; une assertion
déplacée sous `if False:` ou dans une boucle `range(0)` compte pareil — elle est
comptée sans jamais s'exécuter. Une assertion comptée n'est pas une assertion
utile ; c'est une limite du comptage, elle n'est pas réparable ici, et elle
s'écrit pour ne pas être prise pour une garantie. Ce que le comptage attrape
quand même, dans le même voisinage : une assertion retirée d'un test ou d'une
aide, un test sauté sans condition (`test-allege`), un fichier de test effacé.

Il ne détecte PAS les secrets — c'est l'affaire du `.gitignore` posé par
`amorcage-du-projet` et d'un outil dédié. Il ne rapporte jamais la valeur
trouvée, seulement la règle et l'emplacement.

Sortie : 0 propre · 1 au moins une violation · 2 n'a pas pu tourner.
Un 2 ne doit jamais se lire comme un 0. Une **exception tracée** dans le tableau
de CONSTRAINTS.md ne fait pas échouer le contrôle : elle est annoncée en
avertissement, visible dans le journal, parce qu'une exception non vue est une
règle morte.

Usage :
    python3 garde_plancher.py                      # base : origin/main
    python3 garde_plancher.py --base main
    python3 garde_plancher.py --depot ~/un/projet
"""

import argparse
import ast
import fnmatch
import re
import subprocess
import sys
from pathlib import Path

EXTRAIT = 100                     # caractères d'extrait, au plus
IGNORE = ".plancherignore"        # un glob par ligne, chemins exemptés

# --- Les cinq gestes -------------------------------------------------------

# Une directive de neutralisation NUE éteint la règle entière ; une directive
# qui nomme un code (la même suivie d'un code, ou d'un identifiant entre
# crochets) vise ce code seul : c'est un réglage, pas une neutralisation, et le
# garde ne la signale pas.
SUPPRESSIONS = re.compile(
    r"@ts-ignore|@ts-nocheck|eslint-disable|biome-ignore|istanbul ignore"
    r"|#\s*noqa\b(?!\s*[:(=])|#\s*type:\s*ignore\b(?!\s*\[)"
    r"|#\s*pylint:\s*disable(?![-=:\w])|#\s*flake8:\s*noqa\b(?!\s*[:(=])"
    r"|nosemgrep|gitleaks:allow|//\s*nolint|#\[allow\(|@SuppressWarnings"
    r"|#\s*shellcheck\s+disable")

INACHEVE = re.compile(
    r"[Nn]ot implemented|NotImplementedError|unimplemented!\(|todo!\("
    r"|catch\s*\([\w\s]*\)\s*\{\s*\}|catch\s*\{\s*\}"
    r"|except[^\n:]*:\s*pass\b|\bTODO\b|\bFIXME\b")

TESTS_ALLEGES = re.compile(
    r"\.(skip|todo)\s*\(|\bxit\s*\(|\bxdescribe\s*\("
    r"|@pytest\.mark\.skip\b|@unittest\.skip\b|t\.Skip\(|#\[ignore\]")

FICHIER_DE_TEST = re.compile(r"(\.|_)(test|spec)\.|/tests?/|(^|/)test_")
ASSERTION = re.compile(r"\b(expect|assert|assert_eq!|should|require)\b")

CONTRAINTES = re.compile(r"CONSTRAINTS\.md$")
LIGNE_EXCEPTION = re.compile(r"^\|\s*(W|E)\d+\s*\|")
# « 4 560 » et « 4560 » sont le même nombre, et le millier se sépare de bien des
# façons : espace ordinaire, insécable (U+00A0), fine (U+2009), fine insécable
# (U+202F), tabulation… N'en connaître que trois est pire que rien : « 5 000 »
# écrit avec une espace fine se couperait en « 5 » puis « 000 », et un relèvement
# passerait en silence. `\s` couvre tout blanc — c'est exactement ce qu'il faut.
NOMBRE = re.compile(r"\d{1,3}(?:\s\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?")


def valeur_du_nombre(ecrit):
    """La valeur d'un nombre, quel que soit le blanc qui sépare ses milliers."""
    return float(re.sub(r"\s", "", ecrit).replace(",", "."))

LIBELLES = {
    "verificateur-fait-taire": "un vérificateur a été fait taire",
    "test-allege": "un test a été rendu plus facile",
    "assertion-retiree": "une assertion a disparu d'un test qui reste",
    "test-supprime": "un fichier de test a été supprimé",
    "travail-inacheve": "du travail inachevé a été laissé",
    "seuil-desserre": "un seuil a été desserré",
    "seuil-modifie": "un seuil a changé, direction indéterminée",
    "seuil-disparu": "une ligne de seuil a disparu du tableau",
    "exception-ajoutee": "une exception a été tracée au plancher",
    "plancherignore-modifie": "le fichier d'exemption du plancher a changé",
    "budget-de-lectures": "le garde a lu plus de fichiers que son budget",
}

# --- Le budget de lectures -------------------------------------------------
#
# L'unité est **un fichier dont le garde a besoin du contenu, quel que soit le
# moyen** : la version d'une base et celle de l'arbre comptent pour deux, une
# relecture du même contenu pour une seule. Le compte est exactement ce que le
# garde a dû ouvrir pour juger ce diff, et il l'imprime.
LECTURES = set()

# Les deux lectures sans lesquelles le garde ne sait ni ce qu'il doit ignorer
# (`.plancherignore`, lu sur la base) ni ce qu'il doit excepter
# (`CONSTRAINTS.md`, lu dans l'arbre). Mesurées, pas supposées : le garde se
# compte lui-même, plume par plume.
LECTURES_FIXES = 2

# Un budget qu'une ligne d'exception peut lever n'est pas un budget.
NON_ACQUITTABLES = ("budget-de-lectures",)


def noter_lecture(origine, chemin):
    """Note une lecture. Deux fois le même contenu ne compte qu'une fois."""
    LECTURES.add((origine, str(chemin)))


def budget_de_lectures(modifies, ajoutes, supprimes):
    """Le plafond : deux lectures par fichier modifié, une par ajout ou retrait.

    Deux par fichier modifié parce qu'un fichier modifié se lit **deux fois** —
    la version de la base et celle de l'arbre —, et c'est ce qui permet de
    comparer les assertions d'un test survivant. Une par fichier ajouté ou
    supprimé, parce qu'il n'y a qu'une version à lire. Plus les deux lectures
    fixes.
    """
    return 2 * modifies + ajoutes + supprimes + LECTURES_FIXES


def git(args, depot, codes_ok=(0,)):
    """Renvoie la sortie de git, ou None si la commande échoue.

    `codes_ok` existe pour `diff --no-index`, qui sort en **1** dès qu'il
    trouve une différence — comme `diff`. Traiter ce 1 comme un échec faisait
    ignorer en silence tous les fichiers nouveaux, soit précisément ceux où
    un test mis en `skip` arrive le plus souvent.

    `core.quotePath=false` est posé sur **tous** les appels : sans lui, git
    *cite* les chemins non ASCII (`"ex\\303\\251mple.py"`). Le nom lu n'existe
    alors pas, `--no-index` échoue sur un fichier nouveau, et une neutralisation
    ou un test supprimé derrière une lettre accentuée échapperait au garde en
    silence. C'est le seul endroit où git est appelé : la garantie tient ici, ou
    pas.

    `quotePath` ne suffit pas pour tout : un nom portant un retour à la ligne,
    une tabulation, un guillemet ou un antislash est **toujours** cité, quel que
    soit le réglage. Pour ceux-là, la seule lecture juste est `-z` (séparateur
    NUL, chemin brut) — d'où :func:`chemins_nuls` et :func:`lignes_de_noms`.
    """
    try:
        fait = subprocess.run(
            ["git", "-c", "core.quotePath=false", "-C", str(depot)] + args,
            capture_output=True, text=True)
    except (FileNotFoundError, OSError):
        return None
    return fait.stdout if fait.returncode in codes_ok else None


def lire_ignores(depot, reference):
    """Les globs exemptés, lus à la **référence** (la base), pas dans l'arbre.

    Le script lui-même est exécuté depuis la base : le fichier d'exemption doit
    l'être aussi, sinon une PR élargirait ses propres exemptions avant d'être
    jugée. Un changement de ce fichier dans la PR est un constat à part entière.
    """
    contenu = git(["show", "%s:%s" % (reference, IGNORE)], depot)
    noter_lecture("base", IGNORE)
    if contenu is None:
        return []
    return [l.strip() for l in contenu.splitlines()
            if l.strip() and not l.startswith("#")]


def exempte(chemin, globs):
    return any(fnmatch.fnmatch(chemin, g) for g in globs)


def chemins_nuls(sortie):
    """Les chemins d'une sortie git `-z` : séparés par NUL, jamais cités.

    `-z` est la seule lecture qui rende un nom **brut**. Sans lui, un chemin qui
    porte un retour à la ligne se découpe en deux « fichiers » dont aucun
    n'existe, et ce qu'il portait échappe au garde sans un mot.
    """
    if not sortie:
        return []
    return [chemin for chemin in sortie.split("\0") if chemin]


def lignes_de_noms(jetons):
    """Reconstruit les lignes `état\\tchemin` d'un `diff --name-status -z`.

    Le format `-z` enchaîne des jetons bruts : `A\\0chemin\\0`, et
    `R100\\0ancien\\0nouveau\\0` pour un renommage. On relit le nombre de chemins
    d'après l'état (deux pour `R`/`C`, un sinon) plutôt que de deviner — un
    fichier nommé `A` ne doit pas se prendre pour un état.
    """
    lignes, i = [], 0
    while i < len(jetons):
        etat = jetons[i]
        combien = 2 if etat[:1] in ("R", "C") else 1
        lignes.append("\t".join([etat] + jetons[i + 1:i + 1 + combien]))
        i += 1 + combien
    return lignes


def decouper_diff(diff):
    """Renvoie (ajoutées, retirées) — chaque entrée est (fichier, texte)."""
    ajoutees, retirees, fichier = [], [], ""
    for ligne in diff.splitlines():
        if ligne.startswith("+++ "):
            fichier = ligne[4:].strip()
            # `b/chemin` en diff normal ; un lstrip("b/") mangerait `build/…`.
            if fichier.startswith("b/"):
                fichier = fichier[2:]
        elif ligne.startswith("--- ") or ligne.startswith("@@"):
            continue
        elif ligne.startswith("+"):
            ajoutees.append((fichier, ligne[1:]))
        elif ligne.startswith("-"):
            retirees.append((fichier, ligne[1:]))
    return ajoutees, retirees


# --- Les assertions, lues dans l'arbre -------------------------------------

# `ASSERTION` cherche `\bassert\b` : dans `self.assertEqual(…)`, le `\b` final
# bute sur le `E`, et la ligne retirée ne correspond à rien. Un test qui perd la
# moitié de ses assertions traversait donc le garde sans un mot, tandis qu'une
# ligne qui *mentionnait* `assert` était signalée. Un verdict qui protège pour
# le mauvais motif est un demi-verdict : pour un fichier Python qui existe
# encore, on compare désormais les deux versions **portée par portée**.
#
# Portée, pas test : la première formulation ne regardait que les `def test_*`
# et jetait la règle de ligne pour tout fichier analysable — une assertion
# retirée d'une fonction d'aide devenait donc invisible, alors que la règle de
# ligne la voyait. Le contrôle avait rétréci en croyant s'élargir.


def _est_une_assertion(noeud):
    """`assert x`, `self.assertX(…)`, `self.fail(…)` — ce qui fait échouer un test."""
    if isinstance(noeud, ast.Assert):
        return True
    if not isinstance(noeud, ast.Call):
        return False
    fonction = noeud.func
    if isinstance(fonction, ast.Attribute):
        return fonction.attr.startswith("assert") or fonction.attr == "fail"
    if isinstance(fonction, ast.Name):
        return fonction.id in ("assertRaises", "fail")
    return False


class _CompteurDAssertions(ast.NodeVisitor):
    """Compte les assertions **par portée** : module, classe, fonction, méthode.

    Une assertion appartient à la portée où elle est écrite, pas à celle qui
    l'englobe : sinon une assertion déplacée dans une fonction imbriquée
    resterait comptée au-dessus, et le déplacement passerait pour un statu quo.

    Toute fonction compte, pas seulement les `def test_*` : une aide qui perd son
    `assert` doit se voir exactement comme un test qui perd le sien. La première
    version de cette règle ne regardait que les tests, et la portée du contrôle
    avait **rétréci** là où elle croyait s'élargir.
    """

    def __init__(self):
        # `<module>` est inscrit d'emblée, et chaque portée s'inscrit en entrant :
        # une portée qui perd sa **dernière** assertion doit rester dans la carte,
        # sinon elle passerait pour une fonction effacée — donc pour rien.
        self.portees = {"<module>": 0}
        self.chemin = []

    def _noter(self):
        nom = ".".join(self.chemin) or "<module>"
        self.portees[nom] = self.portees.get(nom, 0) + 1

    def visit_Assert(self, noeud):
        # On ne descend pas dans le test : `assert self.assertTrue(…)` est une
        # assertion, pas deux.
        self._noter()

    def visit_Call(self, noeud):
        if _est_une_assertion(noeud):
            self._noter()
        self.generic_visit(noeud)

    def _entrer(self, noeud):
        self.chemin.append(noeud.name)
        self.portees.setdefault(".".join(self.chemin), 0)
        self.generic_visit(noeud)
        self.chemin.pop()

    visit_FunctionDef = visit_AsyncFunctionDef = visit_ClassDef = _entrer


def assertions_par_portee(source):
    """Le nombre d'assertions de chaque portée d'une source, par nom qualifié.

    Une portée est une fonction — test, aide, méthode —, une classe, ou le module
    sous le nom `<module>`. None quand la source n'est pas du Python analysable :
    l'appelant retombe alors sur la règle de ligne. Se taire serait le seul vrai
    échec.
    """
    if source is None:
        return None
    try:
        arbre = ast.parse(source)
    except (SyntaxError, ValueError):
        return None
    compteur = _CompteurDAssertions()
    compteur.visit(arbre)
    return compteur.portees


def assertions_retirees(avant, apres):
    """Les portées qui **survivent** en perdant des assertions : (nom, avant, après).

    Un nom absent de la seconde version est effacé ou renommé : la règle ne le
    juge pas. Ce n'est pas un oubli laissé en route, c'est une mesure — détecter
    « un `def test_` a disparu » a rendu 9 constats sur les 120 derniers commits,
    dont deux renommages purs, pour un seuil fixé d'avance à 3 : le contrôle n'a
    pas été construit. Comparer par nom ne le réinvente pas en silence.
    """
    if avant is None or apres is None:
        return None
    return sorted((nom, combien, apres[nom]) for nom, combien in avant.items()
                  if nom in apres and apres[nom] < combien)


def _scopes_amoindris(fichier, depot, base):
    """Les portées amoindries d'un fichier, ou None si l'arbre n'est pas lisible.

    None n'est pas « rien à signaler » : c'est « je ne sais pas lire », et
    l'appelant reprend alors la règle de ligne de toujours. Un fichier supprimé,
    un fichier renommé, une source JavaScript, une base où le chemin n'existe
    pas encore — tous retombent là, et le garde n'y perd rien de ce qu'il voyait.
    """
    if not fichier.endswith(".py"):
        return None
    arbre = depot / fichier
    if not arbre.is_file():
        return None
    avant = assertions_par_portee(git(["show", "%s:%s" % (base, fichier)], depot))
    noter_lecture("base", fichier)
    apres = assertions_par_portee(arbre.read_text(encoding="utf-8", errors="replace"))
    noter_lecture("arbre", fichier)
    return assertions_retirees(avant, apres)


def signaler_assertions_retirees(retirees, depot, base, globs, noter):
    """Signale chaque assertion retirée, par portée survivante quand c'est possible.

    Le constat nomme la portée **qualifiée** et le compte : `TestEssai.test_x :
    2 → 1 assertions`, `_aide_avec_assert : 1 → 0 assertions`, `<module> : 1 → 0`.
    """
    par_fichier = {}
    for fichier, texte in retirees:
        if exempte(fichier, globs) or not FICHIER_DE_TEST.search(fichier):
            continue
        par_fichier.setdefault(fichier, []).append(texte)

    for fichier, textes in sorted(par_fichier.items()):
        amoindries = _scopes_amoindris(fichier, depot, base)
        if amoindries is None:
            for texte in textes:
                if ASSERTION.search(texte):
                    noter("assertion-retiree", fichier, texte)
            continue
        for nom, combien_avant, combien_apres in amoindries:
            noter("assertion-retiree", fichier,
                  "%s : %d → %d assertions" % (nom, combien_avant, combien_apres))


# --- Les tests qu'on n'exécute plus ----------------------------------------

# Le deuxième des cinq gestes a un motif incomplet : un test qu'on n'exécute
# plus ne perd aucune assertion, il cesse d'en exécuter. Deux formes seulement
# sont visées, parce qu'elles ne peuvent pas être honnêtes :
#   - un `skipIf`/`skipUnless` à **condition constante** — `True`, `False`, une
#     négation de l'un des deux : le saut ne dépend de rien, donc il est définitif ;
#   - un `self.skipTest(...)` **énoncé nu** dans le corps d'un test, hors de
#     tout `if`, `try` ou boucle : le test ne tourne jamais.
# Les sauts conditionnels sur l'environnement — `sys.platform == "win32"`,
# `shutil.which("git")` — sont légitimes : ils sont laissés tranquilles, sans
# quoi la règle serait bruyante et se ferait desserrer. Mesure d'avant-guerre :
# zéro constat sur les 120 derniers commits non-merges d'origin/main, alors que
# le dépôt porte une trentaine de `skipIf` conditionnels.
SAUTS_CONSTANTS = ("skipIf", "skipUnless")
_ENTETE_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def nom_appele(appel):
    """`unittest.skipIf` → « skipIf ». Le nom seul suffit : un `skipIf` tient
    sa condition en premier argument, d'où qu'il vienne."""
    fonction = appel.func
    return fonction.attr if isinstance(fonction, ast.Attribute) \
        else getattr(fonction, "id", "")


def condition_constante(appel):
    """Le premier argument est-il une constante littérale (ou sa négation) ?"""
    if not appel.args:
        return False
    premier = appel.args[0]
    if isinstance(premier, ast.Constant):
        return True
    return (isinstance(premier, ast.UnaryOp) and isinstance(premier.op, ast.Not)
            and isinstance(premier.operand, ast.Constant))


def tests_jamais_executes(arbre):
    """[(nom qualifié, forme, ligne)] pour un arbre déjà analysé.

    Deux étroitesses, pour ne pas confondre « je saute » avec « je saute quand
    il le faut » :
    - seule une **méthode de test** est regardée — une aide qui appelle
      `self.skipTest(…)` n'est pas un test, et la signaler apprendrait à
      acquitter ;
    - `self.skipTest` n'est relevé que comme énoncé **direct** du corps du test :
      sous un `if`, il est conditionnel, et c'est l'usage qu'on veut garder.
    """
    trouves = []
    connues = set()

    def derive_d_un_testcase(classe):
        for base in classe.bases:
            nom = base.attr if isinstance(base, ast.Attribute) else getattr(base, "id", "")
            if nom.endswith("TestCase") or nom in connues:
                return True
        return False

    def visiter(noeud, classes):
        for enfant in ast.iter_child_nodes(noeud):
            if isinstance(enfant, ast.ClassDef):
                if derive_d_un_testcase(enfant):
                    connues.add(enfant.name)
                    visiter(enfant, classes + [(enfant.name, True)])
                else:
                    visiter(enfant, classes + [(enfant.name, False)])
            elif isinstance(enfant, (ast.FunctionDef, ast.AsyncFunctionDef)):
                est_un_test = bool(classes) and classes[-1][1] \
                    and enfant.name.startswith("test")
                if est_un_test:
                    nom = ".".join([n for n, _ in classes] + [enfant.name])
                    for decorateur in enfant.decorator_list:
                        if isinstance(decorateur, ast.Call):
                            forme = nom_appele(decorateur)
                            if forme in SAUTS_CONSTANTS and condition_constante(decorateur):
                                trouves.append((nom, forme, decorateur.lineno))
                    for instruction in enfant.body:
                        if isinstance(instruction, ast.Expr) \
                                and isinstance(instruction.value, ast.Call) \
                                and nom_appele(instruction.value) == "skipTest":
                            trouves.append((nom, "skipTest", instruction.value.lineno))
                visiter(enfant, classes)
            else:
                visiter(enfant, classes)

    visiter(arbre, [])
    return trouves


def lignes_ajoutees(diff):
    """Les numéros de ligne ajoutés, par fichier — `--unified=0` les donne tels quels.

    Le hunk dit le premier numéro du côté droit ; chaque ligne `+` suit le sien.
    Un fichier neuf (`--- /dev/null`) se lit de la même façon.
    """
    par_fichier = {}
    fichier = None
    ligne = None
    for brute in diff.splitlines():
        if brute.startswith("+++ "):
            chemin = brute[4:].strip()
            fichier = chemin[2:] if chemin.startswith("b/") else chemin
            par_fichier.setdefault(fichier, set())
            ligne = None
            continue
        entete = _ENTETE_HUNK.match(brute)
        if entete:
            ligne = int(entete.group(1))
            continue
        if fichier is None or ligne is None:
            continue
        if brute.startswith("+"):
            par_fichier[fichier].add(ligne)
            ligne += 1
        elif brute.startswith(" "):
            ligne += 1
    return par_fichier


def signaler_tests_jamais_executes(diff, depot, globs, noter):
    """Signale les sauts définitifs **ajoutés** par ce diff, fichier de test seulement.

    Le constat nomme la forme et la portée : `skipTest : TestEssai.test_x (ligne 42)`.
    La ligne doit être dans le diff : un `skipTest` ancien, dans un fichier qu'on
    ne fait que traverser, n'est pas le fait de ce changement.
    """
    for fichier, lignes in sorted(lignes_ajoutees(diff).items()):
        if not FICHIER_DE_TEST.search(fichier) or exempte(fichier, globs):
            continue
        arbre = depot / fichier
        if not arbre.is_file():
            continue
        noter_lecture("arbre", fichier)
        try:
            source = arbre.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        try:
            parsed = ast.parse(source)
        except (SyntaxError, ValueError):
            continue
        for nom, forme, ligne in tests_jamais_executes(parsed):
            if ligne in lignes:
                noter("test-allege", fichier,
                      "%s : %s (ligne %d)" % (forme, nom, ligne))


def sens_du_seuil(texte):
    """« ≥ 80 % » : baisser desserre. « ≤ 200 ms » : monter desserre.

    Sans opérateur, la direction est indéterminée — un budget de latence qui
    baisse resserre, une couverture qui baisse desserre. Le script le dit
    plutôt que de deviner : c'est le seul endroit où il demande un humain.
    """
    if re.search(r"≥|>=|\bau moins\b|\bmin\b", texte):
        return "baisse"
    if re.search(r"≤|<=|\bau plus\b|\bmax\b|\bbudget\b", texte):
        return "hausse"
    return None


# L'opérateur qui introduit un nombre, juste avant lui : « **≥ 87 %** »,
# « ≥ 1 test », « ≤ 4 560 mots ». « **100 %** » n'en a pas — un seuil peut
# s'écrire sans comparateur, et le garde continue de surveiller ceux-là.
_OPERATEUR = re.compile(r"(≥|>=|≤|<=|\bau moins\b|\bau plus\b|\bmin\b|\bmax\b)\s*$")


def nombres_et_comparateurs(ligne):
    """Chaque nombre de la ligne, avec l'opérateur qui l'introduit (ou None).

    Le comparateur fait partie du seuil : « ≥ 5 » et « ≤ 5 » ne disent pas la
    même chose du même chiffre. Les apparier par leur seul rang faisait passer
    un plafond qui remplace un plancher pour un seuil inchangé, et un nombre
    neuf glissé avant le seuil pour une baisse du seuil.
    """
    trouves = []
    for trouve in NOMBRE.finditer(ligne):
        avant = _OPERATEUR.search(ligne[:trouve.start()])
        trouves.append((avant.group(1) if avant else None, trouve.group(0)))
    return trouves


def _sens_du_comparateur(comparateur):
    """« ≥ » est un plancher, « ≤ » un plafond ; sans comparateur, None."""
    if comparateur is None:
        return None
    return "baisse" if comparateur in ("≥", ">=", "au moins", "min") else "hausse"


def _ecrire_nombres(nombres):
    """Les nombres avec leur comparateur : « ≥ 5 », « 100 », « ≥ 87 3 »."""
    return " ".join("%s %s" % (c, n) if c else n for c, n in nombres)


def _champs_tableau(ligne):
    """Les colonnes d'une ligne de tableau Markdown, ou None."""
    texte = ligne.strip()
    if not texte.startswith("|"):
        return None
    champs = [c.strip() for c in texte.strip("|").split("|")]
    if len(champs) < 2 or all(set(c) <= set("-: ") for c in champs):
        return None
    return champs


def ligne_de_seuil(ligne):
    """Les colonnes d'une ligne de seuil de CONSTRAINTS.md, ou None.

    Une ligne de seuil est une ligne de tableau qui porte un libellé et un
    chiffre. On écarte l'en-tête (« Dimension »), le séparateur, et le tableau
    des exceptions — qui a sa propre forme.
    """
    champs = _champs_tableau(ligne)
    if champs is None or _ligne_exception(ligne) or champs[0] == "Dimension":
        return None
    return champs


def _ligne_exception(texte):
    """Les colonnes d'une exception tracée, ou None si la ligne n'en est pas une.

    La forme est : identifiant, règle visée, fichier visé, raison. Une exception
    écrite autrement — une phrase, une ligne incomplète — ne compte pas : le
    garde ne lit que le tableau, il ne devine pas une intention.
    """
    texte = texte.strip()
    if not LIGNE_EXCEPTION.match(texte):
        return None
    champs = [c.strip() for c in texte.strip("|").split("|")]
    return champs if len(champs) >= 4 else None


def lire_exceptions(chemin):
    """Les exceptions tracées lues dans CONSTRAINTS.md, en (règle, fichier)."""
    if not Path(chemin).is_file():
        return []
    noter_lecture("arbre", chemin)
    exceptions = []
    for ligne in Path(chemin).read_text(encoding="utf-8").splitlines():
        champs = _ligne_exception(ligne)
        if champs:
            exceptions.append((champs[1], champs[2]))
    return exceptions


def couverte(constat, exceptions):
    """Le constat est-il couvert par une exception tracée (règle + fichier) ?

    Le fichier d'exception est un glob, comme dans `.plancherignore` ; la règle
    est le nom exact du constat, ou `*`.

    `budget-de-lectures` n'est jamais couvert : le coût du garde n'est pas un
    geste sur un fichier qu'une décision assumée peut lever, c'est le prix de
    tous les fichiers à la fois. Voir `NON_ACQUITTABLES`.
    """
    regle, fichier, _ = constat
    if regle in NON_ACQUITTABLES:
        return False
    return any(r in ("*", regle) and fnmatch.fnmatch(fichier, motif)
               for r, motif in exceptions)


def analyser_seuils(ajoutees, retirees):
    """Le ratchet des seuils : un chiffre ne baisse pas sans qu'on le voie.

    Une ligne de seuil **disparue** ou dont le **libellé** a changé est un
    constat : le plancher ne peut pas s'évaporer par un renommage. Une ligne
    dont le chiffre baisse desserre ; l'exception tracée (traitée par l'appelant)
    la ramènera en avertissement, mais elle reste visible.

    Deux lignes ne s'apparient que si elles portent **autant de nombres** et que
    la suite de leurs **comparateurs** est la même : une ligne qui gagne ou perd
    un nombre n'est plus la même ligne, et un `≥` devenu `≤` n'est pas un seuil
    inchangé. Quand l'un des deux diffère, la direction est indéterminée et le
    garde le dit — refuser d'apparier vaut mieux que d'apparier de travers.

    Un seuil écrit **sans comparateur** (« **100 %** couverts ») reste surveillé :
    il s'apparie avec les autres nombres sans comparateur, et son sens est celui
    de la ligne. Ne garder que les nombres introduits par un comparateur
    laisserait filer celui-là.
    """
    constats = []
    av = [(f, t) for f, t in retirees if CONTRAINTES.search(f)]
    ap = [(f, t) for f, t in ajoutees if CONTRAINTES.search(f)]
    index = {}
    for f, t in ap:
        champs = ligne_de_seuil(t)
        if champs is not None:
            index.setdefault(champs[0], t)
    vus = set()
    for fichier, avant in av:
        champs_av = ligne_de_seuil(avant)
        if champs_av is None:
            continue
        libelle = champs_av[0]
        if libelle in vus:
            continue
        vus.add(libelle)
        apres = index.get(libelle)
        if apres is None:
            constats.append(("seuil-disparu", fichier, "libellé « %s »" % libelle))
            continue
        n_av = nombres_et_comparateurs(avant)
        n_ap = nombres_et_comparateurs(apres)
        if len(n_av) != len(n_ap):
            # Deux lignes ne s'apparient que si elles portent **autant de
            # nombres**. Apparier de position en position quand une ligne en
            # gagne un — « ≥ 87 % » devenu « ≥ 87 lignes, et ≥ 80 % » —
            # comparait les deux premiers et laissait le nouveau sans
            # vis-à-vis : la boucle passait au suivant, et un desserrement réel
            # traversait le garde sans constat ni avertissement.
            #
            # On refuse d'apparier, et on le **dit** : la direction est
            # indéterminée — deux nombres d'une même ligne ne mesurent pas
            # forcément la même chose, et le garde ne devine pas ce que le
            # chiffre nouveau mesure — mais le changement, lui, est vu. C'est
            # le seul verdict honnête.
            #
            # Ce refus ne peut qu'**ajouter** des constats : quand les deux
            # côtés portent autant de nombres, la comparaison est exactement
            # celle d'avant, nombre pour nombre. Un desserrement qui passait
            # est vu ; aucun de ceux qui étaient vus ne se perd.
            constats.append(("seuil-modifie", fichier,
                             "%s → %s" % (" ".join(n for _, n in n_av),
                                          " ".join(n for _, n in n_ap))))
            continue
        if [c for c, _ in n_av] != [c for c, _ in n_ap]:
            # Le comparateur fait partie du seuil. Quand la suite des
            # comparateurs change, rien ne dit quel nombre remplace lequel :
            # « ≥ 87 % » précédé d'un compte neuf, et « ≥ 87 % » devenu
            # « ≤ 87 % », se ressemblent nombre pour nombre — l'appariement par
            # position les faisait passer pour un seuil inchangé, ou annonçait
            # une baisse qui n'avait pas eu lieu. On refuse d'apparier, et le
            # constat montre les comparateurs, pas seulement les chiffres.
            constats.append(("seuil-modifie", fichier,
                             "%s → %s" % (_ecrire_nombres(n_av),
                                          _ecrire_nombres(n_ap))))
            continue
        sens_de_la_ligne = sens_du_seuil(apres)
        # Chaque nombre est examiné — pas d'arrêt au premier qui diffère : un
        # seuil relevé plus haut sur la ligne ne doit pas cacher un second seuil
        # qui baisse, et aucun des constats déjà vus ne se perd.
        for i, (comparateur, brut) in enumerate(n_ap):
            ecrit_av = n_av[i][1]
            # Un millier reformaté (« 4 560 » → « 4560 ») n'est pas un seuil qui
            # bouge : c'est le même nombre. On compare les valeurs, pas les
            # écritures — et on garde les écritures pour le constat.
            if valeur_du_nombre(brut) == valeur_du_nombre(ecrit_av):
                continue
            monte = valeur_du_nombre(brut) > valeur_du_nombre(ecrit_av)
            # Un nombre introduit par son propre comparateur se juge par lui ;
            # un seuil écrit sans comparateur (« **100 %** couverts ») garde le
            # sens de la ligne entière — c'est ce qui continue de le protéger.
            sens = _sens_du_comparateur(comparateur) or sens_de_la_ligne
            if sens is None:
                constats.append(("seuil-modifie", fichier,
                                 "%s → %s" % (ecrit_av, brut)))
            elif (sens == "baisse" and not monte) or (sens == "hausse" and monte):
                constats.append(("seuil-desserre", fichier,
                                 "%s → %s" % (ecrit_av, brut)))
    return constats


def _afficher(flux, marque, regle, fichier, extrait):
    print("  %s [%s] %s" % (marque, regle, fichier), file=flux)
    print("      %s" % LIBELLES[regle], file=flux)
    if extrait:
        print("      → %s" % extrait, file=flux)


def main():
    LECTURES.clear()
    a = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    a.add_argument("--base", default="origin/main",
                   help="référence de comparaison (défaut : origin/main)")
    a.add_argument("--depot", default=".", help="racine du dépôt à contrôler")
    opts = a.parse_args()
    depot = Path(opts.depot).expanduser().resolve()

    if git(["rev-parse", "--is-inside-work-tree"], depot) is None:
        print("garde-plancher : %s n'est pas un dépôt git" % depot, file=sys.stderr)
        return 2

    base = git(["merge-base", opts.base, "HEAD"], depot)
    if not base:
        print("garde-plancher : aucune base commune avec %s — rien à comparer"
              % opts.base, file=sys.stderr)
        return 2
    base = base.strip()

    suivis = git(["diff", "--unified=0", base, "--"], depot) or ""
    nouveaux = chemins_nuls(
        git(["ls-files", "-z", "--others", "--exclude-standard"], depot))
    for f in nouveaux:
        suivis += git(["diff", "--no-index", "--unified=0", "/dev/null", f],
                      depot, codes_ok=(0, 1)) or ""

    # Le fichier d'exemption est lu sur la BASE, comme le script lui-même.
    globs = lire_ignores(depot, opts.base)
    exceptions = lire_exceptions(depot / "CONSTRAINTS.md")

    ajoutees, retirees = decouper_diff(suivis)
    constats = []

    def noter(regle, fichier, texte):
        constats.append((regle, fichier, texte.strip()[:EXTRAIT]))

    for fichier, texte in ajoutees:
        if exempte(fichier, globs):
            continue
        if SUPPRESSIONS.search(texte):
            noter("verificateur-fait-taire", fichier, texte)
        if INACHEVE.search(texte):
            noter("travail-inacheve", fichier, texte)
        if TESTS_ALLEGES.search(texte):
            noter("test-allege", fichier, texte)

    signaler_assertions_retirees(retirees, depot, base, globs, noter)
    signaler_tests_jamais_executes(suivis, depot, globs, noter)

    # Un fichier de test supprimé ne laisse aucune ligne « retirée » attribuable ;
    # une exemption élargie serait alors invisible : les deux se lisent sur les
    # noms de fichiers, pas sur les lignes.
    etats = lignes_de_noms(
        chemins_nuls(git(["diff", "--name-status", "-z", base, "--"], depot)))
    for ligne in etats:
        etat, _, chemin = ligne.partition("\t")
        chemin = chemin.strip()
        if chemin == IGNORE:
            constats.append(("plancherignore-modifie", IGNORE, ""))
        elif etat.startswith("D") and FICHIER_DE_TEST.search(chemin) \
                and not exempte(chemin, globs):
            constats.append(("test-supprime", chemin, ""))
    for chemin in nouveaux:
        if chemin.strip() == IGNORE:
            constats.append(("plancherignore-modifie", IGNORE, ""))

    constats.extend(analyser_seuils(ajoutees, retirees))

    # Le garde se compte lui-même : ce qu'il a lu pour juger ce diff, contre ce
    # qu'il avait le droit de lire. Le compte est imprimé à chaque passage, et
    # un dépassement ne s'acquitte pas — voir `NON_ACQUITTABLES`.
    modifies = sum(1 for ligne in etats if ligne.startswith("M"))
    ajoutes = sum(1 for ligne in etats if ligne.startswith("A"))
    supprimes = sum(1 for ligne in etats if ligne.startswith("D"))
    plafond = budget_de_lectures(modifies=modifies, ajoutes=ajoutes,
                                 supprimes=supprimes)
    if len(LECTURES) > plafond:
        constats.append(("budget-de-lectures", "garde_plancher.py",
                         "%d lecture(s) pour un plafond de %d"
                         % (len(LECTURES), plafond)))

    # Une exception AJOUTÉE est annoncée, jamais cachée : c'est une décision
    # assumée, visible dans le journal. Elle ne fait pas échouer le contrôle.
    # Une phrase d'exception hors du tableau ne compte pas : elle ne couvre rien,
    # et le constat qu'elle prétendait lever reste un constat.
    avertissements = [("exception-ajoutee", f, t.strip()[:EXTRAIT])
                      for f, t in ajoutees
                      if CONTRAINTES.search(f) and _ligne_exception(t)]
    restants = []
    for constat in constats:
        if couverte(constat, exceptions):
            avertissements.append(constat)
        else:
            restants.append(constat)
    constats = restants

    if constats:
        print("garde-plancher : %d violation(s) du plancher.\n" % len(constats),
              file=sys.stderr)
        for regle, fichier, extrait in constats:
            _afficher(sys.stderr, "✗", regle, fichier, extrait)
        print("\nChacun de ces gestes baisse la barre. Corriger le code, ou tracer",
              file=sys.stderr)
        print("l'exception dans le tableau de CONSTRAINTS.md (une ligne à quatre",
              file=sys.stderr)
        print("colonnes : identifiant, règle, fichier, raison). Un mot hors de ce",
              file=sys.stderr)
        print("tableau ne lève rien.", file=sys.stderr)

    if avertissements:
        print("\ngarde-plancher : %d avertissement(s) — décision(s) assumée(s),"
              % len(avertissements))
        for regle, fichier, extrait in avertissements:
            _afficher(sys.stdout, "!", regle, fichier, extrait)

    # Le compte est public : c'est ce qui rend le budget vérifiable par celui
    # qui relit le diff, sans instrumenter le garde.
    print("\ngarde-plancher : %d lecture(s) pour un plafond de %d "
          "(%d modifié(s), %d ajouté(s), %d supprimé(s))."
          % (len(LECTURES), plafond, modifies, ajoutes, supprimes))

    if constats:
        return 1
    if not avertissements:
        print("garde-plancher : propre.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
