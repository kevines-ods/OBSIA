---
schema: 1
kind: skill
name: refactoring-sur
description: Restructurer un code existant sans changer son comportement — renommer, extraire, déplacer, simplifier, découpler — par petits pas, tests verts à chaque pas, jamais mêlé à un ajout de fonctionnalité ni à une correction de bogue. À charger quand un code devient difficile à modifier, avant d'y ajouter une fonctionnalité, ou pour rembourser une dette relevée. Exige des tests qui figent le comportement avant de commencer.
module: construction
type: outil
read_only: false
---

# Skill — Refactoring sûr

Un refactoring change la **forme**, jamais le **comportement**. Dès qu'il
change aussi le comportement, ce n'est plus un refactoring : c'est une
réécriture, avec les risques d'une réécriture et sans ses précautions.

## Préalable — le filet

Aucun refactoring sans tests qui couvrent la zone. S'il n'y en a pas, charger
d'abord `tests-de-caracterisation`. Lancer la suite : elle doit être **verte**
avant le premier pas. Un refactoring commencé sur une suite rouge ne peut pas
prouver qu'il n'a rien cassé.

## Procédure

### 1. Nommer le but en une phrase

« Extraire le calcul de remise pour pouvoir y ajouter les codes promo. » Un
refactoring sans but s'étend jusqu'à toucher tout le fichier. Le but fixe
aussi l'arrêt : une fois atteint, on s'arrête, même si le reste est laid.

### 2. Avancer par pas atomiques

Un pas = **une** transformation nommée :

| Pas | Exemple |
| --- | --- |
| renommer | une variable, une fonction, un module |
| extraire | une fonction, une classe, une constante |
| déplacer | une fonction vers le module qui l'utilise |
| intégrer | une indirection qui ne sert plus |
| remplacer | un conditionnel par un dispatch, un paramètre booléen par deux fonctions |

Après **chaque** pas : lancer les tests. Vert, on continue ; rouge, on annule
le pas (`git restore .`, qui suppose chaque pas vert commité ou indexé par
`git add`) au lieu de le réparer. Un pas qu'on doit
réparer était trop grand : le recouper.

Préférer les outils de refactoring de l'éditeur ou du langage (renommage
sémantique) au rechercher-remplacer, qui renomme aussi les homonymes.

### 3. Commiter souvent

Un commit par pas, ou par petite série de pas du même genre. Si un problème
apparaît trois pas plus loin, `git bisect` le retrouve en secondes au lieu
d'une heure de lecture.

### 4. Ne rien ajouter en chemin

Pendant un refactoring, on **note** — on ne fait pas :

- un bogue repéré → une ligne dans `docs/DETTE.md` ou un ticket ; il se
  corrige après, avec `investigation-de-bug` ;
- une fonctionnalité qui « serait facile maintenant » → la tranche suivante ;
- une dépendance à mettre à jour → `montee-de-version`.

### 5. Livrer séparément

Le refactoring part dans sa propre branche et sa propre PR (`livraison-git`),
**avant** la fonctionnalité qu'il prépare. Une PR « refactoring + nouvelle
fonction » est illisible : le relecteur ne peut pas distinguer ce qui devait
changer de ce qui ne devait pas.

## Rationalisations

| Ce qu'on se dit | La réalité |
| --- | --- |
| « tant que j'y suis, je corrige ce bogue » | si un test casse, tu ne sauras plus si c'est le refactoring ou la correction |
| « je lancerai les tests à la fin » | au bout de vingt pas, le test rouge peut venir de n'importe lequel des vingt |
| « ce test est trop strict, je l'adapte » | un test de comportement qui doit changer pendant un refactoring dit que le comportement a changé |
| « tant qu'à faire, je nettoie tout le module » | le diff devient irrelisible, et la revue humaine se transforme en signature à l'aveugle |
| « le rechercher-remplacer ira plus vite » | il renommera aussi l'homonyme dans le module voisin, et aucun test ne le couvre |

## Ce que ce skill ne fait pas

Il ne change aucun comportement et ne livre aucune fonctionnalité. Le travail
sur le dépôt suit le §3 de `../system/VAULT-CONTRACT.md`.
