#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Applique la convention du coffre parent aux notes qui en manquent.

Lit un dossier du coffre parent et ajoute le frontmatter minimal aux notes qui
n'en ont pas, reprend les tags inline existants, et signale les tags qui
sortent du vocabulaire contrôlé (IA/system/tags-du-coffre-parent.md).

Par dossier, le `type` posé diffère : `0-SAVOIRS` → concept, `0-DOCUMENTS` → revue,
`0-PROJETS` → projet, `0-PERSONNELS` → personnel, `0-MEMOIRES` → note (le
catch-all « toute autre note classée » du registre). Pour `0-EN-VRAC`, aucun
`type` n'est figé : il est décidé au classement, quand la note rejoint sa
destination (skill `traitement-des-notes`). Un dossier dont le `type` est inconnu
n'est **pas** écrit — un frontmatter sans `type` resterait « partiel » à jamais :
il est seulement signalé.

Sécurité : ne modifie RIEN par défaut — l'aperçu d'abord, --appliquer ensuite.
Les fichiers qui ont déjà un frontmatter partiel ne sont pas réécrits, ils sont
signalés. Les fichiers `sommaire.md` et `README.md` sont écartés : ce sont des
fichiers de dossier, pas des notes, et l'installeur les a posés.

**Parcours.** La descente est récursive — les notes vivent sous
`0-PROJETS/<projet>/documents/` ou `0-MEMOIRES/<agent>/expériences/`, pas à plat
— et elle s'arrête sur la **frontière de mémoire** (dossier technique, ou tout
dossier contenant un `.git`, où le §3 s'applique hors mémoire §7.3). Cette
frontière est définie **une seule fois**, dans `scripts/convention_des_notes.py` :
elle n'est pas redite ici. La racine du coffre est dispensée — le coffre est
lui-même un dépôt — mais viser un sous-dossier hors mémoire
(`0-PROJETS/<projet>/code/`, un dossier sous un `.git`) est refusé : on ne pose de
frontmatter nulle part dans un autre dépôt.

**Chantiers gelés.** Sous `0-MEMOIRES/`, la mémoire des agents
(`0-MEMOIRES/préférences/`, `0-MEMOIRES/<agent>/expériences/`) est vivante, mais
un chantier clos ne se modifie plus jamais (VAULT-CONTRACT.md §6). Ce script le
constate par le chemin — sans lire la note ni deviner l'intention — et refuse
toute écriture dans un dossier gelé, même si `--dossier` le désigne explicitement.
La vivacité d'un `expériences/` se juge sur la liste des agents (`IA/agents/`) :
`0-MEMOIRES/<projet>/expériences/` est un chantier, pas de la mémoire d'agent. Le
dossier reste lisible : l'aperçu s'affiche, l'écriture non.

Bibliothèque standard uniquement ; outil de la machine, pas de CI.

Usage :
    python3 appliquer_convention_parent.py                 # 0-SAVOIRS, aperçu
    python3 appliquer_convention_parent.py --appliquer
    python3 appliquer_convention_parent.py --dossier=0-DOCUMENTS
    python3 appliquer_convention_parent.py --dossier=0-EN-VRAC
    python3 appliquer_convention_parent.py --racine /chemin/du/coffre
"""

import argparse
import sys
from pathlib import Path

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


sys.dont_write_bytecode = True
_RACINE_DEPOT = _racine_du_depot(Path(__file__))
if _RACINE_DEPOT is None:
    raise SystemExit("Dépôt OBSIA introuvable au-dessus de %s" % __file__)
if str(_RACINE_DEPOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_RACINE_DEPOT / "scripts"))

# La convention des notes vit dans le moteur partagé, en un seul exemplaire.
from convention_des_notes import (  # noqa: E402
    DOSSIERS_HORS_MEMOIRE, est_depot_imbrique, est_gele, extraire_frontmatter,
    liste_des_agents, lire_registre, notes_du_dossier, point_de_depart_ecarte,
    tags_inline)

# Dossiers de connaissance : un type est posé. 0-EN-VRAC en est absent : le type
# y est décidé au classement, pas figé d'avance. 0-MEMOIRES prend `note`, le
# catch-all du registre (« toute autre note classée ») : la mémoire vivante n'a
# pas de type plus précis, et un frontmatter sans type serait partiel à jamais.
TYPES = {"0-SAVOIRS": "concept", "0-DOCUMENTS": "revue",
         "0-PROJETS": "projet", "0-PERSONNELS": "personnel",
         "0-MEMOIRES": "note"}

# La frontière de mémoire, le parcours des notes, la lecture du frontmatter, le
# vocabulaire des tags et les règles de mémoire gelée viennent du moteur partagé
# `convention_des_notes` (`scripts/`) : une seule copie pour l'applicateur,
# l'indexeur, la porte d'entrée et `regenerate_sommaire.py`.


def trouver_racine_depot(script: Path) -> Path | None:
    """Remonte jusqu'au dossier qui contient IA/system/VAULT-CONTRACT.md."""
    return _racine_du_depot(script)


def bloc_frontmatter(type_note: str | None, tags: list[str]) -> str:
    """Bloc YAML minimal ; `type` absent si type_note est None (0-EN-VRAC)."""
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
    ap.add_argument("--dossier", default="0-SAVOIRS",
                    help="dossier du coffre parent à traiter (défaut : 0-SAVOIRS)")
    ap.add_argument("--racine", type=Path, default=None,
                    help="racine du coffre parent (défaut : parent du dépôt OBSIA)")
    args = ap.parse_args()

    script = Path(__file__).resolve()
    racine_depot = trouver_racine_depot(script)
    if racine_depot is None:
        print("Dépôt OBSIA introuvable depuis %s" % script.parent, file=sys.stderr)
        return 1
    agents = liste_des_agents(racine_depot)   # la mémoire vivante d'un agent
    coffre = (args.racine or racine_depot.parent).resolve()
    dossier = coffre / args.dossier
    if not dossier.is_dir():
        print("Dossier introuvable : %s" % dossier, file=sys.stderr)
        return 1
    # La racine du coffre est dispensée (le coffre est lui-même un dépôt) ; viser
    # un sous-dossier hors mémoire ne doit pas l'ouvrir pour autant.
    if point_de_depart_ecarte(dossier, coffre):
        print("Point de départ hors mémoire : %s est un dépôt ou un dossier "
              "technique — rien n'y est écrit." % dossier)
        return 0

    connus = lire_registre(racine_depot)
    gele = est_gele(dossier, coffre, agents)
    # Les notes de 0-PROJETS/ et 0-MEMOIRES/ vivent en sous-dossiers : sans
    # descente récursive, ces deux dossiers passent pour vides. `notes_du_dossier`
    # écarte en chemin les dossiers techniques (`.git`, `.stversions`,
    # `node_modules/`, `code/`…).
    notes = notes_du_dossier(dossier)
    if not notes:
        print("Aucune note Markdown dans %s" % dossier)
        return 0

    # Le `type` se décide par destination, sur le premier composant significatif
    # du chemin : `./0-MEMOIRES`, `0-MEMOIRES/` et `0-MEMOIRES/préférences`
    # donnent tous `0-MEMOIRES`. `.` ne donne rien : le type reste inconnu.
    morceaux = [m for m in args.dossier.replace("\\", "/").split("/")
                if m not in ("", ".")]
    dossier_haut = morceaux[0].upper() if morceaux else ""
    type_note = TYPES.get(dossier_haut)
    # Seul 0-EN-VRAC écrit sans `type` : le skill y prévoit « tags seulement », le
    # type étant décidé au classement. Partout ailleurs un `type` du registre est
    # requis ; sans lui, on signale au lieu d'écrire — sinon le frontmatter
    # resterait « partiel » à jamais.
    type_connu = type_note is not None or dossier_haut == "0-EN-VRAC"
    a_ecrire: list[tuple[Path, str]] = []
    gelees: int = 0
    sans_type: int = 0
    illisibles: list[Path] = []
    hors_globaux: dict[str, int] = {}

    print("Convention sur %s  (%d note(s))%s"
          % (dossier, len(notes),
             "  — chantier gelé, lecture seule" if gele else ""))
    for n in notes:
        rel = n.relative_to(coffre)
        try:
            info = analyser(n, connus)
        except (UnicodeDecodeError, OSError) as e:
            # Une note non UTF-8 (ou illisible) ne doit pas arrêter le lot.
            illisibles.append(rel)
            print("\n• %s\n   ⚠ illisible, ignorée : %s" % (rel, e))
            continue
        for t in info["hors"]:
            hors_globaux[t] = hors_globaux.get(t, 0) + 1
        print("\n• %s" % rel)
        print("   statut : %s" % info["statut"])
        if info["tags"]:
            print("   tags proposés : %s" % ", ".join("#%s" % t for t in info["tags"]))
        if info["hors"]:
            print("   ⚠ hors vocabulaire : %s" % ", ".join("#%s" % t for t in info["hors"]))
        if info["statut"] == "frontmatter à créer":
            # La descente atteint des chantiers gelés nichés sous un parent
            # vivant : on les écarte note par note, jamais en bloc (§6).
            if est_gele(n, coffre, agents):
                gelees += 1
                if not gele:
                    print("   ⛔ chantier gelé : non écrit (§6)")
                continue
            if not type_connu:
                sans_type += 1
                print("   ⛔ dossier sans `type` connu : non écrit")
                continue
            nouveau = bloc_frontmatter(type_note, info["tags"])
            a_ecrire.append((n, nouveau + "\n\n" + info["texte"]))

    if hors_globaux:
        print("\nTags hors vocabulaire (à ajouter au registre ou à retirer) :")
        for t, c in sorted(hors_globaux.items()):
            print("  #%s  (%d note(s))" % (t, c))

    if illisibles:
        print("\n%d note(s) illisible(s), ignorée(s) : %s"
              % (len(illisibles), ", ".join(str(r) for r in illisibles)))

    if gele:
        print("\nChantier gelé : lecture seule. %d frontmatter restent à créer, "
              "mais rien n'est écrit dans un dossier clos (§6)." % gelees)
        return 0

    if gelees:
        print("\n%d note(s) sous un chantier gelé : lecture seule, aucun "
              "frontmatter n'y est écrit (§6)." % gelees)

    if sans_type:
        print("\n%d note(s) dans un dossier sans `type` connu (%s) : aucun "
              "frontmatter n'y est écrit — il serait partiel à jamais. Choisir le "
              "type avec le skill `traitement-des-notes`." % (sans_type, args.dossier))

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
