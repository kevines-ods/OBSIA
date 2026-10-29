---
schema: 1
kind: module
name: sous-agents
description: Proposer, depuis OBSIA-UI, un sous-agent à contexte minimal qui lit pour l'agent appelant et ne part qu'après validation de l'utilisateur.
essentiel: false
question: Utilises-tu l'interface OBSIA-UI, et veux-tu que tes agents puissent y proposer un sous-agent qui lit pour eux, après ton accord ?
requiert:
  - noyau
---

## Ce que ce module apporte

Le MCP `proposer-un-sous-agent`.

## Pourquoi le découpage tombe là

L'outil n'existe que si l'interface OBSIA-UI le sert : sans elle, il ne répond
pas. Aucune sonde ne voit l'interface tourner ailleurs sur le réseau : la
question tranche.

## Sans ce module

Rien ne change : l'agent lit lui-même ce qu'il aurait confié.
