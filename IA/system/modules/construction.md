---
schema: 1
kind: module
name: construction
description: Construire des applications, sites et outils — l'agent batisseur et ses portes, de l'inventaire de l'existant à la mise en ligne.
essentiel: false
question: Veux-tu construire des applications, des sites ou des outils avec ce coffre ?
sondes:
  - commande:git
requiert:
  - noyau
---

## Ce que ce module apporte

L'agent `batisseur` et les quinze skills de sa chaîne : les six portes de
cadrage, l'amorçage, le plancher de qualité, la construction par tranches, les
tests d'abord, la vérification aux sources, l'investigation de bug, la
livraison Git et la mise en ligne. Plus le MCP `git-hub`.

## Pourquoi un seul module et pas quinze

Ces skills forment une procédure ordonnée : chacun nomme le suivant et refuse
de s'exécuter si le précédent n'a pas produit son document. En retirer un au
milieu ne laisse pas une chaîne plus courte — il laisse une chaîne cassée, qui
s'arrête sans rien dire.

## La sonde ne prouve rien

`git` est présent partout. Elle ne sert qu'à ne pas proposer ce module sur une
machine qui n'a même pas de quoi versionner.
