---
schema: 1
kind: module
name: administration-homelab
description: Administrer une infrastructure auto-hébergée — l'agent administrateur, la surveillance et les alertes, Nextcloud AIO et Home Assistant OS.
essentiel: false
question: Veux-tu que les agents t'aident à administrer tes serveurs à la maison (stockage réseau NAS, services auto-hébergés, sauvegardes, surveillance) ?
requiert:
  - noyau
  - linux-poste
  - virtualisation
  - conteneurs
  - controle-des-sauvegardes
---

## Ce que ce module apporte

L'agent `administrateur` et les skills qui n'ont de sens que pour lui :
`surveillance-et-alertes`, `nextcloud-aio`, `home-assistant-os`.

## Pourquoi le découpage tombe là

L'agent s'appuie sur des compétences qui servent aussi ailleurs — diagnostic
Linux, Proxmox, conteneurs, sauvegardes — et qui gardent leur propre module :
un bâtisseur qui déploie une application a besoin de `conteneurs-docker` sans
avoir de homelab. Ce module les **requiert** au lieu de les absorber.

Nextcloud AIO et Home Assistant OS sont ici plutôt que dans un module chacun :
ce sont des services qu'on administre, pas des outils qu'on construit, et un
module par produit multiplierait les questions pour un skill à la fois.

Aucune sonde : qu'une machine porte `ssh` ne dit pas qu'elle administre un
parc. C'est la question qui décide.

L'inventaire de l'infrastructure n'est **pas** dans ce module : il vit dans le
coffre parent (`Mon coffre/0-PERSONNELS/`), parce qu'il décrit l'utilisateur.
