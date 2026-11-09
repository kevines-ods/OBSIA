---
schema: 1
kind: skill
name: orchestration-equipe
description: Mener en gestionnaire une équipe d'agents sur une demande — plan validé, un membre par tour, tickets bornés, blocage, limites, reprise au carnet. À charger quand une demande demande plusieurs agents de l'équipe déclarée, et à la reprise d'un tel travail. Ne vaut pas pour déléguer une seule tâche (contrat-delegation suffit) ni pour exécuter la boucle, qui reste au harness.
module: equipe
type: outil
read_only: false
---

# Skill — Orchestration d'une équipe

Ce skill est un **protocole** : ce que le gestionnaire écrit, décide et refuse.
Il ne tourne pas. La boucle — appeler un membre, attendre, relancer — est celle
du harness ; **appliqué à la main, l'utilisateur tient le rôle du harness** : il
fixe les valeurs, relance le tour, ouvre des sessions vierges.

## 1. Rôles

- **Le gestionnaire** : l'agent qui charge ce skill. Il tient le carnet du
  chantier ; il n'est donc jamais un agent en lecture seule.
- **Les membres** : les agents de l'équipe **déclarée dans le coffre**, que le
  harness lit à l'exécution. Ce skill n'en nomme aucun.

## 2. Le registre des tâches — au départ, puis après chaque blocage

1. **Les faits**, sous quatre titres : *donnés ou vérifiés*, *à chercher*,
   *à déduire*, *suppositions*.
2. **Le plan** : quelques étapes (cinq par défaut ; le harness peut resserrer),
   une ligne chacune — `<n>. [<membre>] <ce qu'il fait> -> <ce qu'il rend>`. Un
   membre n'y entre que si sa spécialité est requise.
3. **La revue du plan**, obligatoire : l'utilisateur approuve, ou révise avec
   des remarques ; une révision refait le plan, qui repasse en revue. Rien ne
   part avant l'approbation.

Le registre et chaque revue s'écrivent au carnet.

## 3. Le registre de progression — un par tour

Un objet JSON de cinq clés, chacune `{"reason": …, "answer": …}` :
`demande_satisfaite`, `en_boucle`, `progres`, `prochain_membre`, `consigne`.
Le schéma est la référence unique, destinée à être lue aussi par le harness :
`references/registre-de-progression.json`. Il ne se recopie pas.

- `demande_satisfaite` vrai : réponse finale (§9).
- Sinon : un ticket part au membre désigné, avec la consigne.

## 4. Choisir le membre

- Un membre de l'équipe déclarée, qui a sa fiche dans `IA/agents/`.
- Le gestionnaire ne se désigne jamais : ce qui relève de lui, il le fait.
- Un nom inconnu : la question se repose une fois, puis le travail s'arrête
  avec « où on en est ». Jamais de réponse inventée à la place d'un membre.

## 5. Le ticket

Le format de `contrat-delegation` (bloc ```delegation```, avec
`compte_rendu_attendu`, et au besoin `skills`, `mcp`). La consigne est
autosuffisante : le membre ne voit pas la conversation. Le gestionnaire y joint
les comptes rendus **qu'il choisit**, jamais l'historique entier. Un ticket
**qui écrit** attend la validation de l'utilisateur.

## 6. Blocage et remise à zéro

- Le **compteur de blocage** : +1 quand `progres` est faux ou `en_boucle` vrai,
  −1 sinon, jamais sous 0. **Il vit au carnet**, sur la ligne du tour (§8).
- Au-delà de la limite : nommer la cause du blocage en une phrase, refaire les
  faits **et** le plan — les deux formats du §2, jamais un seul —, nouvelle
  revue. La remise à zéro **demande au harness** de repartir de sessions
  vierges pour les membres.

## 7. Limites

Nombre de tours et de remises à zéro : **la règle est ici, les valeurs sont au
harness** (ou chez l'utilisateur, à la main). Une limite atteinte arrête le
travail avec « où on en est » — jamais un abandon muet. Le `budget` d'un
ticket est indicatif : aucun compteur de tokens n'existe ; un seuil voulu est
une estimation, notée au carnet, que l'utilisateur ou le harness tranche.

## 8. Le carnet, point de reprise

- À chaque tour, une ligne : tour, membre, statut du compte rendu, compteur de
  blocage.
- Une revue en attente y est marquée comme telle.
- À la reprise, le gestionnaire relit le carnet et ré-émet la revue en attente ;
  relancer le tour revient au harness.
- Les noms des membres sont les clés de la reprise : un membre absent ou
  renommé **interdit de reprendre**, et cela se dit.

## 9. La réponse finale

Un résumé, les constats avec leur source, la prochaine étape. **Un constat d'un
membre n'y passe qu'adossé à un chemin ou une commande que le gestionnaire a
relus** (`VAULT-CONTRACT.md` §10) : un compte rendu ne s'écrit jamais tel quel.

## 10. Garde-fous

Les six garde-fous arrêtés le 2026-11-07 avec l'utilisateur, en même temps que
la révision des visions qui place le protocole au cœur et l'exécution au
harness :

1. Aucun code, aucune boucle, aucun état dans le protocole du cœur.
2. L'état durable au carnet ; l'état de boucle ne survit pas à l'interface.
3. La composition n'entre jamais au cœur : déclarée au coffre, lue à l'exécution.
4. Le protocole entre par PR et relecture à trois, et reste applicable à la main.
5. Une seule source : le protocole dit la règle, le harness applique ses valeurs.
6. Aucune voie de délégation parallèle : ce que l'interface n'a pas conduit, elle
   le dit.

Et un septième, propre à ce skill : aucun agent n'y est nommé.
