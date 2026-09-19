---
schema: 1
kind: module
name: diagrammes
description: Rendu de diagrammes Mermaid en SVG — flux, séquences, états, classes, entités.
essentiel: false
question: Veux-tu pouvoir produire des diagrammes en image ?
sondes:
  - commande:docker
  - commande:podman
  - commande:npx
  - commande:mmdc
requiert:
  - noyau
---

## Ce que ce module apporte

Le skill `mermaid` et sa chaîne de rendu.

## Pourquoi il est optionnel

Le rendu exige un moteur extérieur — un conteneur, ou `mmdc` via Node. Sur une
machine qui n'a ni l'un ni l'autre, le skill décrirait une procédure
inexécutable. Un skill qui ne peut pas s'exécuter vaut moins que son absence :
il occupe le contexte et fait échouer au moment le plus coûteux.
