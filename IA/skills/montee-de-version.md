---
schema: 1
kind: skill
name: montee-de-version
description: Mettre à jour les dépendances, le cadriciel ou la version du langage d'un projet existant — lire les notes de version et les ruptures de compatibilité, avancer d'une version majeure à la fois, une dépendance majeure par lot, avec un retour arrière écrit d'avance. À charger pour mettre à jour, upgrader ou moderniser un projet, ou devant une dépendance obsolète, abandonnée ou vulnérable.
module: construction
type: outil
read_only: false
---

# Skill — Montée de version

Une mise à jour qui touche tout à la fois ne se débogue pas : quand ça casse,
dix causes sont possibles. Ce skill fait l'inverse — une rupture à la fois,
chacune comprise avant la suivante.

## Préalable

- La suite de tests est verte sur la version actuelle. Si la zone concernée
  n'est pas testée : `tests-de-caracterisation` d'abord.
- Le fichier de verrouillage (`package-lock.json`, `poetry.lock`,
  `Cargo.lock`…) est commité : c'est lui, le point de retour.

## Procédure

### 1. Dresser l'état

Lister ce qui est en retard, avec l'outil du langage :

```bash
npm outdated        # ou : pip list --outdated, cargo outdated, composer outdated
```

Classer chaque dépendance : **correctif** (x.y.Z), **mineure** (x.Y.z),
**majeure** (X.y.z), **abandonnée** (pas de version depuis plus d'un an, dépôt
archivé). Une dépendance abandonnée ne se met pas à jour : elle se remplace,
et c'est une décision à faire valider.

### 2. Ordonner les lots

1. les correctifs et mineures, en un lot — ils ne doivent rien casser ;
2. les majeures, **une par lot**, en commençant par celles dont d'autres
   dépendent (le langage, puis le cadriciel, puis le reste) ;
3. une majeure qui saute plusieurs versions se monte **une majeure à la
   fois** : 3 → 4 → 5, jamais 3 → 5.

### 3. Lire avant de monter

Pour chaque majeure : les notes de version et le guide de migration
officiels — `verification-aux-sources` s'applique. En sortir la liste des
ruptures qui **touchent ce projet** (chercher dans le code les API citées),
pas la liste complète.

### 4. Monter, adapter, vérifier

- monter la version, mettre à jour le verrou ;
- lancer les tests **avant** toute adaptation : les échecs dessinent la carte
  du travail ;
- adapter le code aux ruptures relevées, rien d'autre ;
- tests verts, avertissements de dépréciation lus : une dépréciation
  d'aujourd'hui est la rupture de la prochaine majeure.

### 5. Écrire le retour arrière

Dans la description de la PR : la commande exacte pour revenir (revenir au
commit précédent et réinstaller depuis le verrou), et ce qui ne se défait
pas — une migration de base de données déclenchée par la nouvelle version,
par exemple. Dans ce cas, charger `migration-de-donnees`.

Un lot = une branche = une PR (`livraison-git`).

## Rationalisations

| Ce qu'on se dit | La réalité |
| --- | --- |
| « je monte tout d'un coup, ce sera plus rapide » | au premier test rouge, tu ne sauras pas laquelle des douze mises à jour l'a cassé |
| « le guide de migration est long, je corrigerai au fil des erreurs » | les ruptures silencieuses — un défaut qui change, un comportement par défaut inversé — ne produisent aucune erreur |
| « de la 3 à la 5 directement, les intermédiaires ne servent à rien » | les avertissements de la 4 étaient la seule notice de ce que la 5 supprime |
| « ce ne sont que des avertissements de dépréciation » | ce sont les erreurs de la prochaine montée, annoncées gratuitement |
| « le verrou, je le régénérerai » | sans verrou commité, il n'y a pas de retour arrière exact |

## Ce que ce skill ne fait pas

Il ne choisit pas une nouvelle stack — c'est `choix-de-la-stack`. Le travail
sur le dépôt suit le §3 de `../system/VAULT-CONTRACT.md`.
