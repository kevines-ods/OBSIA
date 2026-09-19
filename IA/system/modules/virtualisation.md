---
schema: 1
kind: module
name: virtualisation
description: Inspecter un hôte Proxmox — VM, conteneurs LXC, stockage, cluster, répartition des ressources. Lecture seule non négociable.
essentiel: false
question: Administres-tu un hôte Proxmox ?
sondes:
  - commande:pvesh
  - fichier:/etc/pve
requiert:
  - noyau
  - linux-poste
---

## Ce que ce module apporte

Le skill `proxmox`, en lecture seule absolue.

## La sonde se trompera souvent

Un hôte Proxmox s'administre presque toujours depuis une autre machine : la
sonde ne le verra pas. Elle ne sert qu'au cas où le coffre est installé sur
l'hôte lui-même. Partout ailleurs, c'est la question qui décide.
