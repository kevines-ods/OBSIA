#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génère un index par dossier du coffre parent.

Pour chacun des dossiers de premier niveau de `Mon coffre/` (_MAINTENANCE,
0-PROJETS, 0-MEMOIRES, 0-DOCUMENTS, 0-PERSONNELS, 0-SAVOIRS, 0-EN-VRAC), écrit
`Mon coffre/_MAINTENANCE/index-<dossier>.md` : une ligne par note, avec son
fichier, sa description, son type et ses tags.

Un index est fait pour décider d'ouvrir une note **sans l'ouvrir** — c'est ce
qui évite de charger huit notes pour en trouver une. C'est le pendant, pour le
coffre parent, des index de `IA/system/` : un fichier dérivé, produit par
script, jamais saisi à la main (VAULT-CONTRACT.md §11).

`0-MEMOIRES/` est indexé **en lecture seule** : l'indexeur ne fait que lire les
notes, y compris celles d'un chantier gelé, et n'écrit que `_MAINTENANCE/`. Un
dossier qui n'est jamais modifié se lit encore — c'est même tout l'intérêt de
l'indexer (§6, §11).

La description vient du frontmatter de la note (`description:`), et à défaut de
son premier titre : une note sans description n'est pas une erreur, l'index la
décrit seulement moins bien. Le passage rétroactif qui pose `type` et `tags` vit
dans `appliquer_convention_parent.py` ; il ne pose pas de description, qui
demande un jugement sur le contenu, et **il refuse d'écrire dans un chantier
gelé**.

Sécurité : n'écrit RIEN par défaut — l'aperçu d'abord, --appliquer ensuite
(§7.4). Les index ne portent aucune date : un fichier daté changerait à chaque
exécution et ne serait jamais « à jour ».

Un dossier qui contient un `.git` est un dépôt de projet : lui et ses
sous-dossiers sont écartés (§7.3 — le Markdown d'un dépôt n'est pas de la
connaissance, et ses dépendances feraient tomber l'unicité des noms, §6).

Bibliothèque standard uniquement ; outil de la machine, pas de CI.

Usage :
    python3 indexer_coffre_parent.py                # aperçu, n'écrit rien
    python3 indexer_coffre_parent.py --appliquer
    python3 indexer_coffre_parent.py --verifier     # n'écrit rien, sort 1 si périmé
    python3 indexer_coffre_parent.py --racine /chemin/du/coffre
"""

import argparse
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True

CONTRAT_REL = Path("IA") / "system" / "VAULT-CONTRACT.md"


def _racine_du_depot(depuis: Path) -> Path | None:
    """Le dossier du dépôt OBSIA le plus proche au-dessus de `depuis`."""
    d = depuis.resolve().parent
    for _ in range(10):
        if (d / CONTRAT_REL).is_file():
            return d
        if d.parent == d:
            break
        d = d.parent
    return None


_RACINE_DEPOT = _racine_du_depot(Path(__file__))
if _RACINE_DEPOT is None:
    raise SystemExit("Dépôt OBSIA introuvable au-dessus de %s" % __file__)
if str(_RACINE_DEPOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_RACINE_DEPOT / "scripts"))

# La convention des notes vit dans le moteur partagé, en un seul exemplaire.
from convention_des_notes import (  # noqa: E402
    corps, est_note, extraire_frontmatter, notes_du_dossier)

# Dossiers de premier niveau du coffre parent (§7.1), dans l'ordre d'affichage.
# `0-MEMOIRES/` porte les préférences et les expériences (vivantes) **et** les
# chantiers clos (gelés) : on les indexe, on ne les modifie jamais (§6).
DOSSIERS = ("0-SAVOIRS", "0-PERSONNELS", "0-PROJETS", "0-MEMOIRES", "0-DOCUMENTS",
            "0-EN-VRAC", "_MAINTENANCE")

LONGUEUR_DESCRIPTION = 140


def nom_index(dossier: str) -> str:
    """Nom du fichier d'index d'un dossier — `index-0-savoirs.md`, etc."""
    return "index-%s.md" % dossier.lstrip("_").lower()


INDEX_GENERES = {nom_index(d) for d in DOSSIERS}


def trouver_racine_depot(script: Path) -> Path | None:
    """Remonte jusqu'au dossier qui contient IA/system/VAULT-CONTRACT.md."""
    return _racine_du_depot(script)


def premiere_accroche(texte: str) -> str:
    """Titre de premier niveau, sinon première ligne utile du corps."""
    for ligne in corps(texte).splitlines():
        nu = ligne.strip()
        if not nu:
            continue
        if nu.startswith("# "):
            return nu[2:].strip()
        if nu.startswith(("#", "---", "|", ">")):
            continue
        return nu
    return ""


def retenir_note_de_l_index(nom: str) -> bool:
    """Ce que l'index liste : une note du coffre, sauf un index généré.

    L'indexeur s'aligne sur l'applicateur, comme le veut la phase 1 du plan
    (« il ne reste qu'une définition par règle partagée », `docs/PLAN.md`) :
    c'est ``est_note`` qui décide ce qu'est une note, en un seul exemplaire. Les
    **fichiers de dossier** (`sommaire.md`, `README.md`) que l'installeur pose
    n'en sont pas, et l'index cesse de les compter. L'indexeur n'ajoute qu'une
    règle, la sienne : écarter ses propres index, pour ne pas se compter
    lui-même.
    """
    return est_note(nom) and nom not in INDEX_GENERES


def ligne(chemin: Path) -> str:
    """Une note, une ligne de tableau. Les `|` du texte sont échappés."""
    def cellule(valeur: str) -> str:
        return valeur.replace("|", "\\|") or "—"

    texte = chemin.read_text(encoding="utf-8", errors="replace")
    fm, _ = extraire_frontmatter(texte)
    fm = fm or {}
    desc = str(fm.get("description") or "").strip() or premiere_accroche(texte)
    desc = re.sub(r"\s+", " ", desc).strip()
    if len(desc) > LONGUEUR_DESCRIPTION:
        desc = desc[:LONGUEUR_DESCRIPTION].rstrip() + "…"
    tags = fm.get("tags")
    tags_txt = (", ".join("`%s`" % t for t in tags)
                if isinstance(tags, list) and tags else "—")
    return "| `%s` | %s | %s | %s |" % (chemin.name, cellule(desc),
                                        cellule(str(fm.get("type") or "")),
                                        tags_txt)


def rendre(dossier_nom: str, dossier: Path) -> str:
    """Le contenu complet d'un index, pour un dossier donné."""
    notes = notes_du_dossier(dossier, retenir=retenir_note_de_l_index)
    L = ["# %s — Index de %s/" % (nom_index(dossier_nom), dossier_nom), "",
         "> Fichier **généré** par",
         "> `IA/skills/traitement-des-notes/scripts/indexer_coffre_parent.py` —",
         "> ne pas éditer à la main. Corriger la note, puis régénérer.", "",
         "| Fichier | Description | Type | Tags |",
         "| --- | --- | --- | --- |"]
    for n in notes:
        L.append(ligne(n))
    if not notes:
        L.append("| — | | | |")
    L += ["",
          "> Un index sert à décider d'ouvrir une note **sans l'ouvrir** : la",
          "> `description` vient du frontmatter, et à défaut du premier titre.",
          ""]
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--appliquer", action="store_true",
                    help="écrit les index (défaut : aperçu, n'écrit rien)")
    ap.add_argument("--verifier", action="store_true",
                    help="n'écrit rien, sort 1 si un index est périmé ou absent")
    ap.add_argument("--racine", type=Path, default=None,
                    help="racine du coffre parent (défaut : parent du dépôt OBSIA)")
    args = ap.parse_args()

    script = Path(__file__).resolve()
    racine_depot = trouver_racine_depot(script)
    if racine_depot is None:
        print("Dépôt OBSIA introuvable depuis %s" % script.parent, file=sys.stderr)
        return 1
    coffre = (args.racine or racine_depot.parent).resolve()
    sortie = coffre / "_MAINTENANCE"

    perimes: list[str] = []
    absents: list[str] = []
    ecrits = 0

    for nom in DOSSIERS:
        dossier = coffre / nom
        if not dossier.is_dir():
            absents.append(nom)
            continue
        cible = sortie / nom_index(nom)
        neuf = rendre(nom, dossier)
        ancien = cible.read_text(encoding="utf-8") if cible.is_file() else None
        if ancien == neuf:
            continue
        rel = cible.relative_to(coffre)
        if args.verifier:
            perimes.append(str(rel))
            continue
        if not args.appliquer:
            print("  ~ %s" % rel)
            continue
        sortie.mkdir(parents=True, exist_ok=True)
        cible.write_text(neuf, encoding="utf-8")
        print("  ~ %s" % rel)
        ecrits += 1

    if absents:
        print("Dossiers absents, non indexés : %s" % ", ".join(absents),
              file=sys.stderr)

    if args.verifier:
        if perimes:
            print("Index périmés ou absents (%d) :" % len(perimes),
                  file=sys.stderr)
            for p in perimes:
                print("  - %s" % p, file=sys.stderr)
            print("Lancer : python3 IA/skills/traitement-des-notes/scripts/"
                  "indexer_coffre_parent.py --appliquer", file=sys.stderr)
            return 1
        print("Index à jour.")
        return 0

    if args.appliquer:
        print("\nFait : %d index écrit(s)." % ecrits)
    else:
        print("\nAperçu — relancer avec --appliquer pour écrire. "
              "Rien n'a été modifié.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
