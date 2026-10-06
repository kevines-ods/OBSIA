#!/usr/bin/env python3
"""La relecture adverse a-t-elle eu lieu ?

Le §5 de `IA/skills/livraison-git.md` veut qu'un diff se soumette par pull
request, et que la relecture du diff appartienne à l'agent `contradicteur`, en
lecture seule et **dans une session neuve**. Le modèle de PR en porte la trace :
une ligne « Relecture : » pour le lien ou le résumé des constats, et une case
« Relu par le contradicteur ».

Ce script lit la description d'une PR sur l'entrée standard et sort en 1 tant
que la case n'est pas cochée. C'est un **signal**, pas un verrou : rien ici
n'empêche la fusion. Cocher la case éteint le voyant, et l'événement `edited`
relance le contrôle.

Une case reste une case : `- [x]`, `* [x]`, `+ [x]`, `1. [x]` et la phrase en
gras comptent toutes. Le contrôle refuse une relecture absente, pas une mise en
forme.

    printf '%s\\n' "$DESCRIPTION_DE_LA_PR" | python3 scripts/verifier_relecture.py

La description arrive par l'entrée standard, jamais par la ligne de commande :
une description suffirait à s'y injecter une commande.
"""

import re
import sys

# La phrase s'écrit ici une seule fois : le motif la lit, les tests aussi.
PHRASE = "Relu par le contradicteur"

# La puce d'une case n'est pas toujours un tiret : Markdown accepte `*` et `+`,
# et une liste ordonnée écrit `1.` ou `1)`. Toutes comptent — un contrôle qui
# refuse une forme valide rend un faux rouge, et un voyant qui crie à tort
# cesse d'être lu.
PUCE = r"(?:[-*+]|\d+[.)])"

# La phrase peut être mise en gras dans la case : `- [x] **Relu par …**`.
GRAS = r"\*{0,2}"

# La case du modèle s'écrit `- [ ] Relu par le contradicteur` ; cochée, elle
# devient `- [x]`. On accepte les deux casses, l'indentation, et une suite après
# la phrase — « (voir #12) » ne doit pas faire échouer le contrôle. Le script lit
# du texte, pas du Markdown : la même ligne recopiée dans un bloc de code
# compterait aussi. C'est un signal, pas une authentification.
CASE_COCHEE = re.compile(
    r"^[ \t]*%s[ \t]*\[[xX]\][ \t]*%s%s" % (PUCE, GRAS, re.escape(PHRASE)),
    re.MULTILINE | re.IGNORECASE)

# Ce qu'on affiche tant que la case n'est pas cochée : le geste à faire, et le
# rappel que le voyant rouge n'est pas une porte fermée.
INVITATION = """\
La case « {phrase} » n'est pas cochée dans la description de la PR.

Faire relire le diff par l'agent contradicteur, en session neuve (§5 de
IA/skills/livraison-git.md) ; renseigner la ligne « Relecture : » — lien ou
résumé des constats ; puis cocher la case : le contrôle repasse au vert.

C'est un signal, pas un verrou : la fusion reste possible."""


def relecture_declaree(texte: str) -> bool:
    """La description de la PR porte-t-elle la case cochée ?"""
    return CASE_COCHEE.search(texte or "") is not None


def main() -> int:
    if relecture_declaree(sys.stdin.read()):
        print("Relecture adverse déclarée.")
        return 0
    constat = INVITATION.format(phrase=PHRASE)
    print(constat)
    # L'annotation se lit dans l'onglet « Checks » sans ouvrir le journal.
    print("::error title=Relecture adverse manquante::%s"
          % constat.splitlines()[0])
    return 1


if __name__ == "__main__":
    sys.exit(main())
