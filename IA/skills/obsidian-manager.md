---
schema: 1
kind: skill
name: obsidian-manager
description: Interroger le dépôt OBSIA et le coffre parent `Mon coffre/` — recherche plein texte, rétroliens, résumé d'une note, état des index. À charger dès qu'il faut retrouver quelque chose, ou vérifier ce qui existe déjà avant d'écrire une note nouvelle. Lit et rapporte seulement : n'écrit, ne déplace ni ne supprime rien.
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
2. Localiser le ou les projets concernés via `mémoire/<agent>/<projet>/sommaire.md`
   et les rétroliens.
3. Extraire le contexte pertinent, en citant systématiquement les chemins des
   fichiers utilisés.
4. Si les index sont désynchronisés : le **dire**, sans y toucher. Ce skill
   est `read_only: true` — il constate, il ne répare pas (§10 du contrat).
   La commande de constat est plus bas (`--verifier`, qui n'écrit rien) ; la
   régénération relève d'une action assumée par l'agent, jamais d'un effet de
   bord de la recherche.

Un `sommaire.md` porte, pour chaque note, son statut et son résumé, extraits de
la note elle-même. Il est fait pour décider d'ouvrir une note **sans l'ouvrir** :
le lire d'abord, ouvrir ensuite, et seulement ce qui est nécessaire.

## Périmètre de recherche

Depuis le 2026-09-08, le **coffre parent** — `Mon coffre/` — est votre base de
connaissances et il est lisible (§7) : la recherche couvre
`Mon coffre/_maintenance/`, `PROJETS/`, `DOCUMENTS/`, `PERSONNELS/`,
`SAVOIRS/` et `EN-VRAC/`, dès que le harness donne accès à la racine du coffre
(§7.6).

Le dépôt est cloné **à la racine de ce coffre** : une recherche lancée depuis
la racine du dépôt ne voit que le dépôt. Il faut remonter d'un cran — c'est le
seul emploi de `..` que le §7 autorise, celui d'une commande :

```bash
rg "motif" ../SAVOIRS --glob "*.md"
```

Deux règles du contrat s'appliquent toujours :

- ce qu'on trouve dans le coffre parent ne se recopie **pas** dans `OBSIA/` :
  le dépôt est public, le coffre parent ne l'est pas (§7.2) ;
- ce skill est `read_only: true` : il lit et rapporte partout, il n'écrit
  nulle part. Les zones d'écriture du coffre parent sont au §7.3, réservées
  aux agents `read_only: false`.

Vérifier que les index sont à jour **sans rien écrire** — c'est la seule forme
que ce skill emploie, et celle que l'étape 4 de la procédure appelle (elle sort
en erreur si les index sont périmés) :

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
