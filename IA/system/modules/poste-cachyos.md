---
schema: 1
kind: module
name: poste-cachyos
description: Optimiser un poste CachyOS — noyau et ordonnanceur, mémoire, btrfs et snapper, réseau, jeu, nettoyage.
essentiel: false
question: Veux-tu que les agents sachent optimiser et entretenir un ordinateur sous CachyOS ?
sondes:
  - distribution:cachyos
requiert:
  - noyau
  - linux-poste
---

## Ce que ce module apporte

Le skill `optimisation-cachyos`.

## Pourquoi un module à part

Ses commandes n'ont de sens que sur CachyOS : noyaux `linux-cachyos*`,
sched-ext, dépôts par niveau de CPU. Sur une autre distribution, il se
proposerait au mauvais moment et échouerait. Le correctif générique d'une
machine Linux reste dans `linux-poste`.

## La sonde se trompera souvent

Le poste s'administre volontiers depuis une autre machine — par SSH, depuis la
VM où tournent les agents. La sonde ne voit que la machine d'installation ;
ailleurs, c'est la question qui décide.
