---
schema: 1
kind: module
name: services-nextcloud
description: Agenda, tâches, notes et contacts sur une instance Nextcloud auto-hébergée — consulter, planifier et noter sans dépendre d'un service tiers.
essentiel: false
question: As-tu une instance Nextcloud dont les agents peuvent lire et tenir l'agenda, les tâches et les notes ?
requiert:
  - noyau
---

## Ce que ce module apporte

Le MCP `nextcloud`.

## Pourquoi aucune sonde

L'instance vit en général sur une autre machine, et l'accès passe par un mot
de passe d'application que seul l'utilisateur crée : rien sur la machine du
harness ne le révèle. La question seule peut trancher.

## Pourquoi un module à part

Il n'a de sens que pour qui héberge un Nextcloud. Le ranger dans
`messagerie` imposerait Gmail à qui veut seulement son agenda, et l'inverse.

## Sans ce module

Agenda et notes se tiennent hors des agents ; les notes durables restent dans
le coffre parent.
