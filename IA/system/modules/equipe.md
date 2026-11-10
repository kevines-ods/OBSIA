---
schema: 1
kind: module
name: equipe
description: Mener une équipe d'agents — le protocole d'orchestration (registres, tickets, blocage, reprise au carnet), applicable dans tout harness.
essentiel: false
question: Veux-tu que les agents sachent mener une équipe d'agents sur une même demande ?
requiert:
  - noyau
---

## Ce que ce module apporte

Le skill `orchestration-equipe` : le protocole qu'un gestionnaire suit pour
mener une équipe déclarée dans le coffre — et le schéma de son registre de
progression, que le harness lit sans le recopier.

## Pourquoi un module à part

Deux agents de deux modules le déclarent (`batisseur`, `construction` ;
`administrateur`, `administration-homelab`). Un skill n'a qu'un module : rangé
dans l'un, il manquerait aux profils qui installent l'autre seul. Les deux
modules le requièrent donc.
