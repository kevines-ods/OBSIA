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
— mais elle ne descend **jamais** dans un dossier technique : nom commençant par
`.` (`.git`, `.obsidian`, `.stversions`, `.opencode`…), `node_modules/`, ni
`code/`, le dépôt Git d'un projet, où le §3 s'applique — hors mémoire (§7.3).
Elle s'arrête surtout devant **tout dossier qui contient un `.git`** : un dépôt
imbriqué n'est jamais de la mémoire, quel que soit son nom. La racine du coffre
est dispensée — le coffre est lui-même un dépôt — mais viser un sous-dossier hors
mémoire (`0-PROJETS/<projet>/code/`, un dossier sous un `.git`) est refusé : on
ne pose de frontmatter nulle part dans un autre dépôt.

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
import os
import re
import sys
from pathlib import Path

CONTRAT_REL = Path("IA") / "system" / "VAULT-CONTRACT.md"
REGISTRE_REL = Path("IA") / "system" / "tags-du-coffre-parent.md"

TAG = re.compile(r"^[a-zà-ÿ][\wà-ÿ-]*$", re.UNICODE)
# Dossiers de connaissance : un type est posé. 0-EN-VRAC en est absent : le type
# y est décidé au classement, pas figé d'avance. 0-MEMOIRES prend `note`, le
# catch-all du registre (« toute autre note classée ») : la mémoire vivante n'a
# pas de type plus précis, et un frontmatter sans type serait partiel à jamais.
TYPES = {"0-SAVOIRS": "concept", "0-DOCUMENTS": "revue",
         "0-PROJETS": "projet", "0-PERSONNELS": "personnel",
         "0-MEMOIRES": "note"}

# Fichiers de dossier, jamais des notes : l'installeur les pose, on n'y touche pas.
FICHIERS_DE_DOSSIER = ("sommaire.md", "readme.md")

# Dossiers jamais parcourus par leur NOM, en plus de ceux qui commencent par `.` :
# `node_modules/` (cache d'outil) et `code/`, le dépôt Git d'un projet, où le §3 du
# contrat s'applique — hors mémoire (§7.3). C'est le filet : la règle de fond est le
# `.git` (ci-dessous), qui attrape tout dépôt imbriqué quel que soit son nom.
DOSSIERS_HORS_MEMOIRE = frozenset(("node_modules", "code"))

# La moitié vivante de 0-MEMOIRES/ (§6) : tout le reste y est gelé.
MEMOIRES = "0-MEMOIRES"
PREFERENCES = "préférences"
EXPERIENCES = "expériences"


def liste_des_agents(racine_depot: Path) -> set[str]:
    """Noms des agents, lus dans `IA/agents/` — la mémoire vivante d'un agent.

    `0-MEMOIRES/<nom>/expériences/` n'est vivant que si `<nom>` est un agent :
    sans cette liste, un dossier `expériences/` sous un projet passerait pour de
    la mémoire vivante, et la note serait écrite dans un chantier clos (§6).
    Liste vide (dossier absent) : rien n'est vivant — on refuse d'écrire plutôt
    que de se tromper.
    """
    try:
        return {p.stem for p in (racine_depot / "IA" / "agents").glob("*.md")}
    except OSError:
        return set()


def est_gele(chemin: Path, coffre: Path, agents: set[str]) -> bool:
    """Vrai si `chemin` tombe dans un chantier gelé de `0-MEMOIRES/`.

    `0-MEMOIRES/` porte deux mémoires, et une seule est gelée (§6) : les
    préférences et les expériences **d'un agent** se corrigent sur place, un
    chantier clos jamais. On le constate par le chemin, sans lire la note :
    sous `0-MEMOIRES/`, seuls `préférences/` et `<agent>/expériences/` sont
    vivants, `<agent>` devant figurer dans `agents` (les fichiers de
    `IA/agents/`). Tout ce qui est plus profond est un chantier — donc gelé, y
    compris ce qui ne devrait pas exister (mieux vaut refuser d'écrire que de se
    tromper).
    """
    try:
        parts = chemin.resolve().relative_to(coffre.resolve()).parts
    except ValueError:
        return False                      # hors du coffre : rien à geler
    if not parts or parts[0] != MEMOIRES:
        return False                      # pas la mémoire des chantiers
    if len(parts) == 1 or len(parts) == 2:
        return False                      # `0-MEMOIRES/`, `0-MEMOIRES/<projet>/`
    if parts[1] == PREFERENCES:
        return False                      # `0-MEMOIRES/préférences/…` : vivant
    if parts[1] in agents and parts[2] == EXPERIENCES:
        return False                      # `0-MEMOIRES/<agent>/expériences/…` : vivant
    return True                           # tout le reste : chantier gelé


def est_depot_imbrique(dossier: Path) -> bool:
    """Vrai si `dossier` est une racine de dépôt Git (dossier ou fichier `.git`).

    Le fichier `.git` compte : un sous-module ou un arbre de travail le porte à la
    place d'un dossier.
    """
    return (dossier / ".git").exists()


def notes_du_dossier(dossier: Path) -> list[Path]:
    """Notes `.md` sous `dossier`, en profondeur mais hors dossiers techniques.

    L'élagage se fait **avant** de descendre :

    - un composant qui commence par `.` (`.git`, `.obsidian`, `.stversions`,
      `.opencode`…), un `node_modules/` ou un `code/` — la liste de noms ;
    - **tout dossier contenant un `.git`**, c'est-à-dire un dépôt imbriqué, quel
      que soit son nom : on ne pose jamais de frontmatter dans un autre dépôt.

    Le `dossier` de départ n'est pas filtré : le coffre peut être lui-même un
    dépôt, seule la descente s'arrête aux dépôts *imbriqués*. `os.walk` ne suit
    pas les liens symboliques, aucune boucle n'est possible. Les fichiers de
    dossier (`sommaire.md`, `README.md`) sont écartés : ce ne sont pas des notes.
    """
    notes: list[Path] = []
    for racine, dossiers, fichiers in os.walk(dossier):
        gardes: list[str] = []
        for d in dossiers:
            if d.startswith(".") or d in DOSSIERS_HORS_MEMOIRE:
                continue
            if est_depot_imbrique(Path(racine) / d):
                continue                  # dépôt Git imbriqué : hors mémoire
            gardes.append(d)
        dossiers[:] = gardes
        for nom in fichiers:
            if (nom.lower().endswith(".md")
                    and nom.lower() not in FICHIERS_DE_DOSSIER):
                notes.append(Path(racine) / nom)
    return sorted(notes)


def point_de_depart_ecarte(dossier: Path, coffre: Path) -> bool:
    """Le point de départ est-il hors mémoire (dépôt imbriqué, `code/`, `.`…) ?

    La racine du coffre est dispensée : le coffre est lui-même un dépôt Git, et
    le `--dossier=.` doit rester possible. Mais viser un sous-dossier que
    `notes_du_dossier` n'aurait jamais atteint — `0-PROJETS/<projet>/code/`, un
    dossier sous un `.git` — ouvrirait un dépôt à un frontmatter : on refuse.
    """
    try:
        parts = dossier.resolve().relative_to(coffre.resolve()).parts
    except ValueError:
        return False                      # hors du coffre : cas « introuvable »
    courant = coffre.resolve()
    for partie in parts:
        if partie.startswith(".") or partie in DOSSIERS_HORS_MEMOIRE:
            return True
        courant = courant / partie
        if est_depot_imbrique(courant):
            return True
    return False


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


SECTION_VOCABULAIRE = "## Vocabulaire"


def lire_registre(racine: Path) -> set[str]:
    """Tags du vocabulaire contrôlé, pris dans le registre versionné.

    Seule la table de la section « Vocabulaire » fait foi. Lire *toutes* les
    lignes de tableau du fichier ramassait aussi la table « Type d'une note » :
    `concept`, `revue`, `projet` et `note` passaient alors pour des tags, et une
    note taguée `#projet` était déclarée conforme. La section des **candidats**
    est écartée pour la raison inverse : ces mots ne sont pas encore validés.
    """
    try:
        texte = (racine / REGISTRE_REL).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return set()
    connus: set[str] = set()
    dans_section = False
    for ligne in texte.splitlines():
        if ligne.startswith("## "):
            dans_section = ligne.startswith(SECTION_VOCABULAIRE)
            continue
        if not dans_section or not ligne.startswith("| "):
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
    """Tags `#tag` du corps, hors blocs de code, titres et cibles de lien.

    Un tag n'est reconnu que précédé d'une **espace** (comme le veut Obsidian) :
    le `#` d'une ancre de lien (`[Sources](#sources)`) suit une parenthèse, celui
    d'un fragment d'URL (`…/page#section`) suit un mot — ni l'un ni l'autre n'est
    un tag. Un `#` en début de ligne n'en est pas un non plus : c'est un titre,
    écarté juste en dessous (la branche « début de ligne » d'un ancien motif était
    donc morte ; elle a été retirée, b1 de la relecture).
    """
    hors_blocs = re.sub(r"```.*?```", "", texte, flags=re.S)
    trouves: list[str] = []
    for ligne in hors_blocs.splitlines():
        if ligne.lstrip().startswith("#"):
            continue                       # titre Markdown, pas un tag
        # Conséquence assumée : un tag collé à une ponctuation — `(#docker)`,
        # `a,#docker` — n'est plus vu (b2 de la relecture). Obsidian non plus ne
        # le reconnaît pas ; ces formes se réécrivent avec une espace devant `#`.
        for m in re.finditer(r"(?<=\s)#([^\s#]+)", ligne):
            tag = m.group(1).rstrip(".,;:!?)('\"").lstrip("(['\"")
            if TAG.match(tag) and tag not in trouves:
                trouves.append(tag)
    return trouves


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
