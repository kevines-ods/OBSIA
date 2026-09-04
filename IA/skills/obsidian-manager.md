---
schema: 1
kind: skill
name: obsidian-manager
description: Interroger le coffre — recherche plein texte, rétroliens, résumé d'une note, état des index. À charger dès qu'il faut retrouver quelque chose dans le coffre, ou vérifier ce qui existe déjà avant d'écrire une note nouvelle. Lit et rapporte seulement : n'écrit, ne déplace ni ne supprime rien.
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

Un `sommaire.md` porte, pour chaque note, son statut et son résumé, extraits de
la note elle-même. Il est fait pour décider d'ouvrir une note **sans l'ouvrir** :
le lire d'abord, ouvrir ensuite, et seulement ce qui est nécessaire.

## Périmètre de recherche

Depuis le 2026-09-03, le **coffre parent** est lisible (§7) : la recherche ne
s'arrête donc plus à `OBSIA/`. Deux conséquences pratiques :

- une recherche lancée depuis la racine du dépôt ne voit **pas** le coffre
  parent ; il faut remonter d'un cran pour l'atteindre ;
- ce qu'on y trouve ne se recopie pas dans `OBSIA/` : le dépôt est public, le
  coffre parent ne l'est pas (§7).

Le coffre parent est en lecture seule, sauf `0-EN VRAC/`. Ce skill étant
`read_only: true`, il n'écrit de toute façon nulle part.

Vérifier que les index sont à jour sans rien écrire (sort en erreur s'ils sont
périmés) :

```bash
python3 scripts/regenerate_sommaire.py --verifier
```

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
