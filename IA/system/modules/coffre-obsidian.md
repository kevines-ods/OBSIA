---
schema: 1
kind: module
name: coffre-obsidian
description: Travailler dans un coffre Obsidian parent — remplir et classer les notes brutes, cartographier les connaissances, tenir le registre des tags.
essentiel: false
question: Ce dépôt est-il cloné dans un coffre Obsidian dont les agents doivent tenir les notes ?
sondes:
  - parent:.obsidian
  - parent:-SAVOIRS
  - parent:-EN-VRAC
requiert:
  - noyau
---

## Ce que ce module apporte

Le traitement des notes du coffre parent décrit au §7 du contrat : remplir une
note d'`-EN-VRAC/`, la tagger au vocabulaire contrôlé, poser les rétroliens,
la classer, tenir `notes_remplies.md`. Et la vue d'ensemble : concepts,
orphelines, doublons, tags hors liste.

## Sans ce module

Le §7 du contrat reste écrit — il décrit une possibilité, pas une obligation.
Un coffre installé sans ce module travaille uniquement dans le dépôt : mémoire,
agents, skills, tâches. Les zones d'écriture du coffre parent ne s'ouvrent pas,
faute de skill pour y écrire.
