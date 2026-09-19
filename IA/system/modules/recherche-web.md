---
schema: 1
kind: module
name: recherche-web
description: Recherche web par un méta-moteur auto-hébergé — SearXNG, sans compte ni traçage.
essentiel: false
question: Disposes-tu d'une instance SearXNG que les agents peuvent interroger ?
requiert:
  - noyau
---

## Ce que ce module apporte

Le MCP `searxng`.

## Pourquoi aucune sonde

L'instance est presque toujours distante, et la sonder impliquerait un appel
réseau — ce que l'installeur ne fait jamais (§13). La question suffit : qui a
une instance le sait.

## Sans ce module

Le skill `recherche` continue de fonctionner : il dit *où* chercher, en
commençant par le coffre. Seul le dernier recours — le web général par un
méta-moteur — devient indisponible.
