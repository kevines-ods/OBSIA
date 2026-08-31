#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Régénère automatiquement les sommaire.md depuis le système de fichiers.
À exécuter AVANT tout commit pour garder un diff Git fiable.

La racine du coffre est le dossier parent de ce script, c'est-à-dire la racine
du dépôt.

Usage :
    python scripts/regenerate_sommaire.py
"""
import os
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

def to_rel(p):
    """Convertit un chemin (abs ou relatif) en chemin relatif au coffre."""
    return os.path.relpath(p, ROOT)

def regen(path):
    full = os.path.join(ROOT, to_rel(path))
    parent = os.path.dirname(full)
    if not os.path.isfile(full) or not to_rel(path).endswith("sommaire.md"):
        return
    base = os.path.basename(to_rel(path))
    titre = base.split("—", 1)[1].strip() if "—" in base else "Sommaire"
    entries = []
    for d in sorted(os.listdir(parent)):
        p = os.path.join(parent, d)
        if os.path.isdir(p):
            entries.append("[%s](%s/)|sous-dossier" % (d, to_rel(p)))
        elif d.endswith(".md") and d != "sommaire.md":
            entries.append("[%s](%s)|note" % (d, to_rel(p)))
    out = "# " + titre + "\n\n"
    out += "> Généré automatiquement. Ne pas éditer à la main.\n\n"
    out += "## Contenu\n\n"
    out += "| Élément | Type |\n|---|---|\n"
    out += "\n".join(["| %s | %s |" % (e.split("|", 1)[0], e.split("|", 1)[1]) for e in entries]) + "\n"
    with open(full, "w", encoding="utf-8") as f:
        f.write(out)

print("Régénération des sommaires…")
created = 0
for dirpath, dirs, files in os.walk(ROOT):
    # La racine du dépôt est le coffre : écarter .git/, .github/ et consorts.
    dirs[:] = [d for d in dirs if not d.startswith(".")]
    # Création des sommaire.md manquants, uniquement sous mémoire/
    rel = to_rel(dirpath)
    in_memoire = "mémoire" in rel.split(os.sep)
    has_notes = any(f.endswith(".md") and f != "sommaire.md" for f in files)
    a_contenu = has_notes or bool(dirs)
    somm = os.path.join(dirpath, "sommaire.md")
    if in_memoire and a_contenu and not os.path.isfile(somm):
        with open(somm, "w", encoding="utf-8") as f:
            f.write("# Sommaire\n\n> Généré automatiquement. Ne pas éditer à la main.\n")
        created += 1
        print("  + créé %s" % to_rel(somm))
    for fl in files:
        if fl == "sommaire.md":
            regen(os.path.join(dirpath, fl))
print("Fait. (%d sommaire.md créés)" % created)
