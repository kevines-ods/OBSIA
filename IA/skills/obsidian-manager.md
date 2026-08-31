---
schema: 1
kind: skill
name: obsidian-manager
description: Gérer le coffre Obsidian — recherche, rétroliens, résumés, index.
type: core
read_only: true
---

# Skill — Obsidian Manager

Compétence de gestion du coffre : recherche, rétroliens, résumés, mise à jour
des index.

**Ceci est un skill, pas un agent.** L'agent qui l'utilise principalement est
`assistant`.

## Procédure

1. Lire `../system/VAULT-CONTRACT.md`.
2. Localiser le ou les projets concernés via `/mémoire/<agent>/<projet>/sommaire.md` et les
   rétroliens.
3. Extraire le contexte pertinent, en citant systématiquement les chemins des
   fichiers utilisés.
4. Si les index sont désynchronisés : régénérer via
   `scripts/regenerate_sommaire.py`. Jamais à la main.

## Outils

Recherche plein texte dans les notes :

```bash
rg "motif" --glob "*.md"
```

> Attention : `--glob "!*.md"` **exclut** les fichiers Markdown. Dans un coffre
> Obsidian, cette forme ne cherche nulle part. Le motif correct est `"*.md"`.

Recherche insensible à la casse, en secours :

```bash
grep -ri "motif" .
```

Rétroliens : lister les fichiers contenant un lien vers la cible.

```bash
rg --glob "*.md" "\[\[cible\]\]"
```

Résumé d'une note : en extraire le titre, les décisions prises, et le statut.

## Contraintes

Ce skill est `read_only: true` : aucune écriture, aucun déplacement, aucune
suppression, y compris via patch. Il lit et il rapporte.

> Les autres contraintes (preview, archivage, sandbox) sont définies dans
> `../system/VAULT-CONTRACT.md`.
