---
schema: 1
kind: module
name: linux-poste
description: Diagnostiquer et corriger un système Linux — services, journaux, charge, disque, mémoire, réseau ; optimisation et entretien propres à CachyOS.
essentiel: false
question: Veux-tu que les agents sachent diagnostiquer et réparer une machine Linux (services en panne, disque plein, journaux) ?
sondes:
  - commande:systemctl
  - commande:journalctl
  - distribution:cachyos
requiert:
  - noyau
---

## Ce que ce module apporte

`diagnostic-linux` (lecture seule) et `remediation-linux` (correction). Ils
forment une paire ordonnée : le second refuse de s'exécuter sans un constat
écrit par le premier. Les séparer casserait cette garde.

Sur CachyOS, il apporte aussi `optimisation-cachyos`.

## Gestionnaire de paquets

Les skills ne supposent pas de distribution : ils lisent `/etc/os-release` et
adaptent la commande. Le profil d'installation retient la distribution détectée
dans `obsia.local.yml`, ce qui évite de proposer `apt` sur une machine Arch.

## Le cas CachyOS

`optimisation-cachyos` ne vaut que sur CachyOS : noyaux `linux-cachyos*`,
sched-ext, dépôts par niveau de CPU. Sur une autre distribution, il se
proposerait au mauvais moment et échouerait — la sonde `distribution:cachyos`
ne déclenche que ce cas particulier, le reste du module restant générique à
toute machine Linux.
