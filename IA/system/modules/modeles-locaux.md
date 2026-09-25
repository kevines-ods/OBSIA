---
schema: 1
kind: module
name: modeles-locaux
description: Délégation de tâches simples à un modèle local servi par une API compatible OpenAI, sans lui transmettre le contexte du coffre.
essentiel: false
question: Disposes-tu d'un modèle local (llama-server, llama-swap, Ollama) auquel l'agent peut confier des tâches simples ?
sondes:
  - commande:llama-server
  - commande:llama-swap
  - commande:ollama
requiert:
  - noyau
---

## Ce que ce module apporte

Le skill `delegation-locale` et le MCP `modele-local`.

## Pourquoi le découpage tombe là

Le skill n'a de sens qu'avec le serveur, et le serveur qu'avec le skill : un
appel sans la procédure transmet trop de contenu et écrit sans relire. Les
deux vont ensemble, et rien d'autre dans le coffre n'en dépend.

Les sondes constatent un binaire de service de modèles ; elles ne savent pas
si le serveur tourne ailleurs sur le réseau, ni si l'utilisateur veut
déléguer. La question tranche.

## Sans ce module

Rien ne change : l'agent principal fait lui-même ce qu'il aurait délégué.
