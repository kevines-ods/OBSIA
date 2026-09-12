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

Il ne détecte PAS les secrets — c'est l'affaire du `.gitignore` posé par
`amorcage-du-projet` et d'un outil dédié. Il ne rapporte jamais la valeur
trouvée, seulement la règle et l'emplacement.

Sortie : 0 propre · 1 au moins une violation · 2 n'a pas pu tourner.
Un 2 ne doit jamais se lire comme un 0.

Usage :
    python3 garde_plancher.py                      # base : origin/main
    python3 garde_plancher.py --base main
    python3 garde_plancher.py --depot ~/un/projet
"""

import argparse
import fnmatch
import re
import subprocess
import sys
from pathlib import Path

EXTRAIT = 100                     # caractères d'extrait, au plus
IGNORE = ".plancherignore"        # un glob par ligne, chemins exemptés

# --- Les cinq gestes -------------------------------------------------------

SUPPRESSIONS = re.compile(
    r"@ts-ignore|@ts-nocheck|eslint-disable|biome-ignore|istanbul ignore"
    r"|#\s*noqa|#\s*type:\s*ignore|#\s*pylint:\s*disable|#\s*flake8:\s*noqa"
    r"|nosemgrep|gitleaks:allow|//\s*nolint|#\[allow\(|@SuppressWarnings"
    r"|#\s*shellcheck\s+disable")

INACHEVE = re.compile(
    r"[Nn]ot implemented|NotImplementedError|unimplemented!\(|todo!\("
    r"|catch\s*\([\w\s]*\)\s*\{\s*\}|catch\s*\{\s*\}"
    r"|except[^\n:]*:\s*pass\b|\bTODO\b|\bFIXME\b")

TESTS_ALLEGES = re.compile(
    r"\.(skip|todo)\s*\(|\bxit\s*\(|\bxdescribe\s*\("
    r"|@pytest\.mark\.skip|@unittest\.skip|t\.Skip\(|#\[ignore\]")

FICHIER_DE_TEST = re.compile(r"(\.|_)(test|spec)\.|/tests?/|(^|/)test_")
ASSERTION = re.compile(r"\b(expect|assert|assert_eq!|should|require)\b")

CONTRAINTES = re.compile(r"CONSTRAINTS\.md$")
LIGNE_EXCEPTION = re.compile(r"^\|\s*(W|E)\d+\s*\|")
NOMBRE = re.compile(r"\d+(?:[.,]\d+)?")

LIBELLES = {
    "verificateur-fait-taire": "un vérificateur a été fait taire",
    "test-allege": "un test a été rendu plus facile",
    "assertion-retiree": "une assertion a disparu d'un test qui reste",
    "test-supprime": "un fichier de test a été supprimé",
    "travail-inacheve": "du travail inachevé a été laissé",
    "seuil-desserre": "un seuil a été desserré",
    "seuil-modifie": "un seuil a changé, direction indéterminée",
    "exception-ajoutee": "une exception a été ajoutée au plancher",
}


def git(args, depot, codes_ok=(0,)):
    """Renvoie la sortie de git, ou None si la commande échoue.

    `codes_ok` existe pour `diff --no-index`, qui sort en **1** dès qu'il
    trouve une différence — comme `diff`. Traiter ce 1 comme un échec faisait
    ignorer en silence tous les fichiers nouveaux, soit précisément ceux où
    un test mis en `skip` arrive le plus souvent.
    """
    try:
        fait = subprocess.run(["git", "-C", str(depot)] + args,
                              capture_output=True, text=True)
    except (FileNotFoundError, OSError):
        return None
    return fait.stdout if fait.returncode in codes_ok else None


def lire_ignores(depot):
    fichier = Path(depot) / IGNORE
    if not fichier.is_file():
        return []
    return [l.strip() for l in fichier.read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.startswith("#")]


def exempte(chemin, globs):
    return any(fnmatch.fnmatch(chemin, g) for g in globs)


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


def analyser_seuils(ajoutees, retirees, constats):
    """Compare les lignes de CONSTRAINTS.md, clé à clé."""
    av = [(f, t) for f, t in retirees if CONTRAINTES.search(f)]
    ap = [(f, t) for f, t in ajoutees if CONTRAINTES.search(f)]
    for fichier, avant in av:
        cle = re.split(r"[|:]", avant)[1] if "|" in avant else avant[:20]
        jumelle = next((t for f, t in ap
                        if (re.split(r"[|:]", t)[1] if "|" in t else t[:20]) == cle), None)
        if jumelle is None:
            continue
        n_av, n_ap = NOMBRE.findall(avant), NOMBRE.findall(jumelle)
        for i, brut in enumerate(n_ap):
            if i >= len(n_av) or brut == n_av[i]:
                continue
            monte = float(brut.replace(",", ".")) > float(n_av[i].replace(",", "."))
            sens = sens_du_seuil(jumelle)
            if sens is None:
                constats.append(("seuil-modifie", fichier,
                                 "%s → %s" % (n_av[i], brut)))
            elif (sens == "baisse" and not monte) or (sens == "hausse" and monte):
                constats.append(("seuil-desserre", fichier,
                                 "%s → %s" % (n_av[i], brut)))
            break


def main():
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
    nouveaux = git(["ls-files", "--others", "--exclude-standard"], depot) or ""
    for f in filter(None, nouveaux.splitlines()):
        suivis += git(["diff", "--no-index", "--unified=0", "/dev/null", f],
                      depot, codes_ok=(0, 1)) or ""

    globs = lire_ignores(depot)
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
        if CONTRAINTES.search(fichier) and LIGNE_EXCEPTION.match(texte.strip()):
            noter("exception-ajoutee", fichier, texte)

    for fichier, texte in retirees:
        if exempte(fichier, globs):
            continue
        if FICHIER_DE_TEST.search(fichier) and ASSERTION.search(texte):
            noter("assertion-retiree", fichier, texte)

    # Un fichier de test supprimé ne laisse aucune ligne « retirée » attribuable.
    for ligne in (git(["diff", "--name-status", base, "--"], depot) or "").splitlines():
        etat, _, chemin = ligne.partition("\t")
        if etat.startswith("D") and FICHIER_DE_TEST.search(chemin) \
                and not exempte(chemin, globs):
            constats.append(("test-supprime", chemin.strip(), ""))

    analyser_seuils(ajoutees, retirees, constats)

    if not constats:
        print("garde-plancher : propre.")
        return 0

    print("garde-plancher : %d violation(s) du plancher.\n" % len(constats),
          file=sys.stderr)
    for regle, fichier, extrait in constats:
        print("  ✗ [%s] %s" % (regle, fichier), file=sys.stderr)
        print("      %s" % LIBELLES[regle], file=sys.stderr)
        if extrait:
            print("      → %s" % extrait, file=sys.stderr)
    print("\nChacun de ces gestes baisse la barre. Corriger le code, ou passer",
          file=sys.stderr)
    print("par une exception tracée dans CONSTRAINTS.md — qui sera signalée.",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
