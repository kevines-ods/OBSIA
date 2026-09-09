---
schema: 1
kind: skill
name: inventaire-de-lexistant
description: Inventorier ce qui existe déjà avant de construire — tentatives précédentes, dépôts, outils installés, notes du coffre — et en sortir trois listes : ce qu'on reprend, ce qu'on ne refait pas, ce qui est non négociable. À charger en toute première étape d'un projet de construction, avant même de poser une question sur le besoin. Lit et rapporte : n'écrit ni ne modifie rien.
type: outil
read_only: true
---

# Skill — Inventaire de l'existant

On ne repart jamais de zéro. Construire sans regarder les tentatives
précédentes, c'est refaire les mêmes choix et retrouver les mêmes limites —
et c'est ainsi qu'on accumule des outils qui ont « des choses bien » sans
qu'aucun soit le bon.

Ce skill n'est pas de l'archéologie. Il produit **trois listes**, rien d'autre.

## Procédure

### 1. Délimiter le sujet en une phrase

Avec l'utilisateur, avant de chercher. « Un outil pour X » suffit. Sans cette
phrase, le balayage ramène tout et ne conclut rien.

### 2. Balayer quatre sources

| Source | Ce qu'on y cherche | Comment |
| --- | --- | --- |
| le coffre parent | notes, décisions, comparatifs déjà écrits | recherche plein texte via `obsidian-manager` |
| la mémoire d'OBSIA | ce qui a déjà été tranché, et pourquoi | `mémoire/` — dossiers de projet et `expériences/` |
| les dépôts | tentatives précédentes, code réutilisable | `ls` du coffre parent, puis `git log` de chacun |
| la machine | ce qui est déjà installé et qui marche | l'inventaire logiciel du poste et des conteneurs |

```bash
rg -l "<motif du sujet>" ..                       # coffre parent, depuis OBSIA/
git -C <dépôt> log --oneline -20                  # ce qui a été fait, et quand
git -C <dépôt> log -1 --format=%cd                # date du dernier signe de vie
```

Un dépôt sans commit depuis des mois n'est pas mort : c'est une tentative
arrêtée, et **la raison de l'arrêt est l'information la plus utile de tout
l'inventaire**. Elle ne se devine pas — se la faire dire.

### 3. Une fiche de quatre lignes par tentative

- **Ce qu'elle fait bien** — précis, vérifié, pas « l'interface est sympa ».
- **Ce qui manque** — l'écart avec le besoin d'aujourd'hui.
- **Pourquoi elle s'est arrêtée** — demandé à l'utilisateur si le dépôt ne le dit pas.
- **Ce qu'on en reprend** — un morceau nommé, ou « rien ».

### 4. Sortir les trois listes

| Liste | Ce qu'elle contient | Ce qu'elle sert à éviter |
| --- | --- | --- |
| **À REPRENDRE** | code, idée, convention qui a fait ses preuves | réécrire ce qui marchait |
| **À NE PAS REFAIRE** | un choix qui a coûté, avec sa raison | reproduire l'échec sous un autre nom |
| **NON NÉGOCIABLE** | contrainte que rien ne fera bouger | découvrir le mur à la moitié du chantier |

### 5. Restituer et faire valider

Présenter les trois listes en tableau. Demander explicitement : *« Ce qu'on
reprend et ce qu'on condamne, c'est bien ça ? »* La porte 1 n'est franchie
qu'une fois cette confirmation obtenue.

## Pièges

- « Ça a l'air bien » n'est pas un constat : ouvrir, lire, vérifier.
- Une entrée « À NE PAS REFAIRE » sans raison écrite est inutilisable — elle
  sera réintroduite dans six mois par quelqu'un qui ne saura pas pourquoi.
- Ne pas juger la qualité du code : ce n'est ni le moment ni l'objet.
- Ne proposer **aucune** architecture ici. C'est la porte 4.

## Ce que ce skill ne fait pas

Il ne décide de rien, n'écrit aucun fichier et ne supprime aucun dépôt. Les
règles d'écriture sont au §2 de `../system/VAULT-CONTRACT.md`.
