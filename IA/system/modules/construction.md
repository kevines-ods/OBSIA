---
schema: 1
kind: module
name: construction
description: Construire des applications, sites et outils, ou faire évoluer un projet existant — l'agent batisseur, ses portes de création et son parcours de reprise, de refactoring et de dette technique.
essentiel: false
question: Veux-tu que les agents t'aident à construire des applications, des sites ou des outils, ou à faire évoluer un projet existant ?
sondes:
  - commande:git
requiert:
  - noyau
  - controle-des-sauvegardes
---

## Ce que ce module apporte

L'agent `batisseur` et les skills de ses deux parcours. La création : les six
portes de cadrage — ou la voie rapide pour un petit outil —, l'amorçage, le
plancher de qualité, la construction par tranches, les tests d'abord, la
vérification aux sources, l'investigation de
bug, la livraison Git et la mise en ligne. L'évolution d'un projet existant :
la reprise, les tests de caractérisation, le refactoring sûr, la montée de
version, la dette technique, la migration de données et la documentation. Plus le MCP `git-hub`.

## Pourquoi un seul module et pas vingt-deux

Les deux parcours ont le même agent, `batisseur`. Celui de la création est une
procédure ordonnée : chaque skill nomme le suivant et refuse de s'exécuter si
le précédent n'a pas produit son document. En retirer un au milieu ne laisse
pas une chaîne plus courte — il laisse une chaîne cassée, qui s'arrête sans
rien dire.

Celui de l'évolution n'est pas une chaîne : ses skills se choisissent selon le
changement. Mais ils n'ont pas d'usage sans l'agent qui les enchaîne, et se
renvoient les uns aux autres (`dette-technique` vers `refactoring-sur` ou
`montee-de-version`). Un module à part ne s'installerait jamais seul : il
coûterait une question de plus à l'installation, sans rien apporter.

## Pourquoi il entraîne le contrôle des sauvegardes

`migration-de-donnees` et `mise-en-ligne` commencent par charger
`sauvegardes` : sans lui, leur première étape renverrait dans le vide.

## La sonde ne prouve rien

`git` est présent partout. Elle ne sert qu'à ne pas proposer ce module sur une
machine qui n'a même pas de quoi versionner.
