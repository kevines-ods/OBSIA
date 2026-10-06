---
schema: 1
kind: module
name: linux-poste
description: Diagnostiquer et corriger un système Linux — services, journaux, charge, disque, mémoire, réseau.
essentiel: false
question: Veux-tu que les agents sachent diagnostiquer et réparer une machine Linux (services en panne, disque plein, journaux) ?
sondes:
  - commande:systemctl
  - commande:journalctl
requiert:
  - noyau
---

## Ce que ce module apporte

`diagnostic-linux` (lecture seule) et `remediation-linux` (correction). Ils
forment une paire ordonnée : le second refuse de s'exécuter sans un constat
écrit par le premier. Les séparer casserait cette garde.

## Gestionnaire de paquets

Les skills ne supposent pas de distribution : ils lisent `/etc/os-release` et
adaptent la commande. Le profil d'installation retient la distribution détectée
dans `obsia.local.yml`, ce qui évite de proposer `apt` sur une machine Arch.
