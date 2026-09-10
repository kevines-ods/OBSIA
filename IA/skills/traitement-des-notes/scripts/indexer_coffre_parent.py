#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génère un index par dossier du coffre parent.

Pour chacun des dossiers de premier niveau de `Mon coffre/` (_maintenance,
PROJETS, DOCUMENTS, PERSONNELS, SAVOIRS, EN-VRAC), écrit
`Mon coffre/_maintenance/index-<dossier>.md` : une ligne par note, avec son
fichier, sa description, son type et ses tags.

Un index est fait pour décider d'ouvrir une note **sans l'ouvrir** — c'est ce
qui évite de charger huit notes pour en trouver une. C'est le pendant, pour le
coffre parent, des index de `IA/system/` : un fichier dérivé, produit par
script, jamais saisi à la main (VAULT-CONTRACT.md §11).

La description vient du frontmatter de la note (`description:`), et à défaut de
son premier titre : une note sans description n'est pas une erreur, l'index la
décrit seulement moins bien. Le passage rétroactif qui pose `type` et `tags` vit
dans `appliquer_convention_parent.py` ; il ne pose pas de description, qui
demande un jugement sur le contenu.

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
import os
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True

CONTRAT_REL = Path("IA") / "system" / "VAULT-CONTRACT.md"

# Dossiers de premier niveau du coffre parent (§7.1), dans l'ordre d'affichage.
DOSSIERS = ("SAVOIRS", "PERSONNELS", "PROJETS", "DOCUMENTS",
            "EN-VRAC", "_maintenance")

LONGUEUR_DESCRIPTION = 140


def nom_index(dossier: str) -> str:
    """Nom du fichier d'index d'un dossier — `index-savoirs.md`, etc."""
    return "index-%s.md" % dossier.lstrip("_").lower()


INDEX_GENERES = {nom_index(d) for d in DOSSIERS}


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


def extraire_frontmatter(texte: str) -> dict:
    """Frontmatter YAML minimal (scalaires et listes à tirets).

    Même analyseur que `appliquer_convention_parent.py` : le format des notes du
    coffre parent est volontairement simple, et aucune dépendance externe n'est
    admise dans ce dépôt.
    """
    if not texte.startswith("---"):
        return {}
    fin = texte.find("\n---", 3)
    if fin == -1:
        return {}
    donnees: dict = {}
    cle_liste: str | None = None
    for ligne in texte[3:fin].splitlines():
        nu = ligne.strip()
        if not nu or nu.startswith("#"):
            continue
        if nu.startswith("- ") and cle_liste:
            donnees[cle_liste].append(nu[2:].strip().strip("'\""))
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
        donnees[cle] = valeur.strip("'\"")
    return donnees


def corps(texte: str) -> str:
    """Le texte situé après le frontmatter, s'il y en a un."""
    if not texte.startswith("---"):
        return texte
    fin = texte.find("\n---", 3)
    if fin == -1:
        return texte
    retour = texte.find("\n", fin + 1)
    return texte[retour + 1:] if retour != -1 else ""


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


def notes_du_dossier(dossier: Path) -> list[Path]:
    """Notes Markdown du dossier — dépôts de projet et index générés écartés."""
    trouves: list[Path] = []
    for chemin, sous, fichiers in os.walk(dossier):
        racine = Path(chemin)
        if (racine / ".git").exists():      # dépôt de projet : hors index (§7.3)
            sous[:] = []
            continue
        sous[:] = [s for s in sous if not s.startswith(".")]
        for nom in fichiers:
            if not nom.endswith(".md") or nom.startswith("."):
                continue
            if nom in INDEX_GENERES:        # un index ne se liste pas lui-même
                continue
            trouves.append(racine / nom)
    return sorted(trouves, key=lambda p: p.relative_to(dossier).as_posix())


def ligne(chemin: Path) -> str:
    """Une note, une ligne de tableau. Les `|` du texte sont échappés."""
    def cellule(valeur: str) -> str:
        return valeur.replace("|", "\\|") or "—"

    texte = chemin.read_text(encoding="utf-8", errors="replace")
    fm = extraire_frontmatter(texte)
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
    notes = notes_du_dossier(dossier)
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
    sortie = coffre / "_maintenance"

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
