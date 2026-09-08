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

Depuis le 2026-09-08, le **coffre parent** est votre base de connaissances et
il est lisible (§7) : la recherche couvre `_maintenance/`, `PROJETS/`,
`DOCUMENTS/`, `PERSONNELS/`, `SAVOIRS/` et `EN-VRAC/`, dès que le harness
donne accès à la racine du coffre (§7.6).

Le dépôt OBSIA est cloné **à la racine du coffre parent** : les dossiers de
connaissance sont un cran au-dessus, leur chemin commence par `../` depuis la
racine du dépôt. Une recherche lancée depuis la racine du dépôt ne les voit
pas ; il faut remonter d'un cran pour les atteindre :

```bash
rg "motif" ../SAVOIRS --glob "*.md"
```

Deux règles du contrat s'appliquent toujours :

- ce qu'on trouve dans le coffre parent ne se recopie **pas** dans `OBSIA/` :
  le dépôt est public, le coffre parent ne l'est pas (§7.2) ;
- ce skill est `read_only: true` : il lit et rapporte partout, il n'écrit
  nulle part. Les zones d'écriture du coffre parent sont au §7.3, réservées
  aux agents `read_only: false`.

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
