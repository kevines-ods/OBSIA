---
schema: 1
kind: module
name: revue
description: Relecture adverse en lecture seule absolue — chercher ce qui cloche dans un diff, auditer la sécurité d'un projet entier, et cross-examiner une décision avant qu'elle tienne.
essentiel: false
question: Veux-tu un agent relecteur qui vérifie le travail des autres et repère les erreurs et les failles de sécurité, sans rien modifier lui-même ?
requiert:
  - noyau
---

## Ce que ce module apporte

L'agent `contradicteur` et les skills `revue-de-code`, `audit-de-securite` et `relecture-adverse`.

## Pourquoi aucune sonde

Rien sur une machine ne dit si son propriétaire veut être contredit. C'est une
question de méthode de travail, pas de configuration.
