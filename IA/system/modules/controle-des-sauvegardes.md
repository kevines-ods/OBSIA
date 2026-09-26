---
schema: 1
kind: module
name: controle-des-sauvegardes
description: Vérifier que les sauvegardes existent, sont récentes, respectent la règle 3-2-1, et se restaurent réellement.
essentiel: false
question: Veux-tu que les agents vérifient tes sauvegardes avant toute action destructrice ?
requiert:
  - noyau
---

## Ce que ce module apporte

Le skill `sauvegardes`.

## Pourquoi le retenir même sans infrastructure

Ce skill se charge avant toute action risquant de détruire des données — ce qui
arrive sur un poste isolé comme sur un parc de machines. La réponse par défaut
est oui, et refuser est un choix qu'on fait les yeux ouverts.
