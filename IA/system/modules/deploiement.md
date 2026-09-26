---
schema: 1
kind: module
name: deploiement
description: Empaqueter une application et la mettre en ligne derrière un reverse proxy — image, compose, labels de routage, secrets hors dépôt, retour arrière écrit d'avance.
essentiel: false
question: Veux-tu pouvoir mettre en ligne les applications que tu construis ?
requiert:
  - noyau
  - construction
  - conteneurs
  - controle-des-sauvegardes
---

## Ce que ce module apporte

Le skill `mise-en-ligne`.

## Pourquoi il est séparé de `construction`

Tout ce qu'on construit n'est pas destiné à être hébergé. Un outil en ligne de
commande, une bibliothèque, un script se livrent sans jamais toucher un reverse
proxy. Fondu dans `construction`, ce skill aurait imposé le module `conteneurs`
à qui n'héberge rien.

## Pourquoi il dépend de `sauvegardes`

Le skill exige une sauvegarde des volumes **vérifiée** avant la première mise
en ligne. Sans le skill qui sait la vérifier, cette exigence ne serait qu'une
phrase.
