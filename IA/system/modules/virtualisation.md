---
schema: 1
kind: module
name: virtualisation
description: Inspecter un hôte Proxmox en lecture seule — VM, conteneurs LXC, stockage, ressources — puis y agir sous annonce — créer des machines, régler le démarrage, poser des hookscripts.
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

Deux skills qui forment une paire ordonnée, comme `diagnostic-linux` et
`remediation-linux` : `proxmox` constate, en lecture seule absolue ;
`administration-proxmox` agit, et ne se charge qu'après ce constat. Les séparer
garde le constat sûr pour un agent qui n'a pas le droit d'agir.

## La sonde se trompera souvent

Un hôte Proxmox s'administre presque toujours depuis une autre machine : la
sonde ne le verra pas. Elle ne sert qu'au cas où le coffre est installé sur
l'hôte lui-même. Partout ailleurs, c'est la question qui décide.
