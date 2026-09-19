---
schema: 1
kind: module
name: planification
description: Tâches planifiées — registre `IA/tâches/`, instanciation en timers, réconciliation après un changement de machine ou de harness.
essentiel: false
question: Veux-tu que des actions se déclenchent toutes seules à heure fixe ?
sondes:
  - commande:systemctl
requiert:
  - noyau
---

## Ce que ce module apporte

Le skill `cron`, le registre `IA/tâches/` et son outillage d'instanciation.

## Une sonde qui ne prouve pas grand-chose

`systemctl` est présent sur presque toute machine Linux moderne : la sonde dit
que l'instanciation en timers est *possible*, pas qu'elle est *voulue*. La
question tranche, la sonde ne fait que proposer une réponse par défaut.
