---
schema: 1
kind: module
name: messagerie
description: Lire, chercher et envoyer des courriels depuis une boîte Gmail — documents produits joints, envoi toujours confirmé.
essentiel: false
question: Veux-tu que les agents puissent lire ta boîte Gmail et envoyer des courriels en ton nom ?
requiert:
  - noyau
---

## Ce que ce module apporte

Le MCP `gmail`.

## Pourquoi aucune sonde

Rien sur la machine ne dit qu'un compte Gmail existe ni qu'on veut le confier
à un agent : l'accès passe par une autorisation OAuth donnée dans le
navigateur. La question seule peut trancher.

## Sans ce module

Les documents produits restent dans le coffre parent ; l'utilisateur les
envoie lui-même.
