#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Applique la convention du coffre parent aux notes qui en manquent.

Lit un dossier du coffre parent et ajoute le frontmatter minimal aux notes qui
n'en ont pas, reprend les tags inline existants, et signale les tags qui
sortent du vocabulaire contrôlé (IA/system/tags-du-coffre-parent.md).

Par dossier, le `type` posé diffère : `SAVOIRS` → concept, `DOCUMENTS` → revue,
`PROJETS` → projet, `PERSONNELS` → personnel. Pour `EN-VRAC`, aucun `type`
n'est figé : il est décidé au classement, quand la note rejoint sa destination
(skill `traitement-des-notes`).

Sécurité : ne modifie RIEN par défaut — l'aperçu d'abord, --appliquer ensuite.
Les fichiers qui ont déjà un frontmatter partiel ne sont pas réécrits, ils sont
signalés. Bibliothèque standard uniquement ; outil de la machine, pas de CI.

Usage :
    python3 appliquer_convention_parent.py                 # SAVOIRS, aperçu
    python3 appliquer_convention_parent.py --appliquer
    python3 appliquer_convention_parent.py --dossier DOCUMENTS
    python3 appliquer_convention_parent.py --dossier EN-VRAC
    python3 appliquer_convention_parent.py --racine /chemin/du/coffre
"""

import argparse
import re
import sys
from pathlib import Path

CONTRAT_REL = Path("IA") / "system" / "VAULT-CONTRACT.md"
REGISTRE_REL = Path("IA") / "system" / "tags-du-coffre-parent.md"

TAG = re.compile(r"^[a-zà-ÿ][\wà-ÿ-]*$", re.UNICODE)
# Dossiers de connaissance : un type est posé. EN-VRAC en est absent : le type
# y est décidé au classement, pas figé d'avance.
TYPES = {"SAVOIRS": "concept", "DOCUMENTS": "revue",
         "PROJETS": "projet", "PERSONNELS": "personnel"}


def trouver_racine_depot(script: Path) -> Path | None:
    """Remonte jusqu'au dossier qui contient IA/system/VAULT-CONTRACT.md."""
    d = script.resolve().parent
    for _ in range(10):
        if (d / CONTRAT_REL).is_file():
            return d
        if d.parent == d:
            break
        d = d.parent
    return None


def lire_registre(racine: Path) -> set[str]:
    """Tags du vocabulaire contrôlé, pris dans le registre versionné."""
    try:
        texte = (racine / REGISTRE_REL).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return set()
    connus: set[str] = set()
    for ligne in texte.splitlines():
        if not ligne.startswith("| "):
            continue
        for m in re.finditer(r"`([^`]+)`", ligne):
            if TAG.match(m.group(1)):
                connus.add(m.group(1))
    return connus


def extraire_frontmatter(texte: str) -> tuple[dict | None, int]:
    """Frontmatter YAML minimal (scalaires et listes à tirets).

    Renvoie (dict, fin) où `fin` est l'index de la première ligne après le
    bloc, ou (None, 0) si le fichier ne commence pas par un frontmatter.
    """
    if not texte.startswith("---"):
        return None, 0
    fin = texte.find("\n---", 3)
    if fin == -1:
        return None, 0
    donnees: dict = {}
    cle_liste: str | None = None
    for ligne in texte[3:fin].splitlines():
        nu = ligne.strip()
        if not nu or nu.startswith("#"):
            continue
        if nu.startswith("- ") and cle_liste:
            donnees[cle_liste].append(nu[2:].strip())
            continue
        if ":" not in nu:
            continue
        cle, _, valeur = nu.partition(":")
        cle = cle.strip()
        valeur = valeur.strip()
        if not valeur:
            donnees[cle] = []
            cle_liste = cle
            continue
        cle_liste = None
        if valeur.lower() in ("true", "false"):
            donnees[cle] = valeur.lower() == "true"
        elif valeur.isdigit():
            donnees[cle] = int(valeur)
        else:
            donnees[cle] = valeur.strip("\"'")
    # fin pointe sur le "---" de clôture : passer après cette ligne
    retour = texte.find("\n", fin + 1)
    return donnees, (retour + 1 if retour != -1 else len(texte))


def tags_inline(texte: str) -> list[str]:
    """Tags `#tag` du corps, hors blocs de code et hors titres."""
    hors_blocs = re.sub(r"```.*?```", "", texte, flags=re.S)
    trouves: list[str] = []
    for ligne in hors_blocs.splitlines():
        if ligne.lstrip().startswith("#"):
            continue                       # titre Markdown, pas un tag
        for m in re.finditer(r"#([^\s#]+)", ligne):
            tag = m.group(1).rstrip(".,;:!?)('\"").lstrip("(['\"")
            if TAG.match(tag) and tag not in trouves:
                trouves.append(tag)
    return trouves


def bloc_frontmatter(type_note: str | None, tags: list[str]) -> str:
    """Bloc YAML minimal ; `type` absent si type_note est None (EN-VRAC)."""
    lignes = ["---"]
    if type_note:
        lignes.append("type: %s" % type_note)
    if tags:
        lignes.append("tags:")
        lignes += ["  - %s" % t for t in tags]
    lignes.append("---")
    return "\n".join(lignes)


def analyser(chemin: Path, connus: set[str]) -> dict:
    """Décrit ce que la note mérite : créer, compléter, ou rien."""
    texte = chemin.read_text(encoding="utf-8")
    fm, apres = extraire_frontmatter(texte)
    inline = tags_inline(texte)
    tags = list(dict.fromkeys(inline))

    if fm is None:
        statut = "frontmatter à créer"
    elif not fm.get("type") or not fm.get("tags"):
        statut = "frontmatter partiel (à compléter, non réécrit)"
    else:
        statut = "à jour"
    hors = sorted(t for t in tags if t not in connus)
    return {"texte": texte, "fm": fm, "statut": statut,
            "tags": tags, "hors": hors}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--appliquer", action="store_true",
                    help="écrit les notes sans frontmatter (défaut : aperçu)")
    ap.add_argument("--dossier", default="SAVOIRS",
                    help="dossier du coffre parent à traiter (défaut : SAVOIRS)")
    ap.add_argument("--racine", type=Path, default=None,
                    help="racine du coffre parent (défaut : parent du dépôt OBSIA)")
    args = ap.parse_args()

    script = Path(__file__).resolve()
    racine_depot = trouver_racine_depot(script)
    if racine_depot is None:
        print("Dépôt OBSIA introuvable depuis %s" % script.parent, file=sys.stderr)
        return 1
    coffre = (args.racine or racine_depot.parent).resolve()
    dossier = coffre / args.dossier
    if not dossier.is_dir():
        print("Dossier introuvable : %s" % dossier, file=sys.stderr)
        return 1

    connus = lire_registre(racine_depot)
    notes = sorted(p for p in dossier.glob("*.md")
                   if p.is_file() and p.name.lower() not in ("sommaire.md",))
    if not notes:
        print("Aucune note Markdown dans %s" % dossier)
        return 0

    type_note = TYPES.get(args.dossier.upper())   # None pour EN-VRAC : pas de type figé
    a_ecrire: list[tuple[Path, str]] = []
    hors_globaux: dict[str, int] = {}

    print("Convention sur %s  (%d note(s))" % (dossier, len(notes)))
    for n in notes:
        info = analyser(n, connus)
        for t in info["hors"]:
            hors_globaux[t] = hors_globaux.get(t, 0) + 1
        rel = n.relative_to(coffre)
        print("\n• %s" % rel)
        print("   statut : %s" % info["statut"])
        if info["tags"]:
            print("   tags proposés : %s" % ", ".join("#%s" % t for t in info["tags"]))
        if info["hors"]:
            print("   ⚠ hors vocabulaire : %s" % ", ".join("#%s" % t for t in info["hors"]))
        if info["statut"] == "frontmatter à créer":
            nouveau = bloc_frontmatter(type_note, info["tags"])
            a_ecrire.append((n, nouveau + "\n\n" + info["texte"]))

    if hors_globaux:
        print("\nTags hors vocabulaire (à ajouter au registre ou à retirer) :")
        for t, c in sorted(hors_globaux.items()):
            print("  #%s  (%d note(s))" % (t, c))

    if args.appliquer:
        for n, neuf in a_ecrire:
            n.write_text(neuf, encoding="utf-8")
            print("~ %s" % n.relative_to(coffre))
        print("\nFait : %d frontmatter écrit(s)." % len(a_ecrire))
    else:
        print("\nAperçu : %d frontmatter à créer — relancer avec --appliquer pour"
              % len(a_ecrire))
        print("écrire. Rien n'a été modifié.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
