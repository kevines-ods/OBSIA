---
schema: 1
kind: contract
name: contrat-taches
description: Détail des tâches planifiées : registre, invariant d'instance, nommage, raison de chaque règle.
module: noyau
---

# Annexe du contrat — taches

> **À lire avant de créer, modifier ou suspendre une tâche, ou d'en instancier ou retirer une instance.** Annexe du contrat (`../VAULT-CONTRACT.md`).
> Elle précise, elle n'ajoute aucune règle : toute règle qu'on peut enfreindre
> sans avoir rien chargé est aussi au noyau, et en cas de contradiction le
> noyau fait foi — l'annexe est alors à corriger. La correspondance avec l'ancien
> contrat est suivie dans `registre.md`, document de travail non normatif.

## 12. Tâches planifiées

Une tâche planifiée est déclarée **dans le coffre**, jamais seulement chez
celui qui l'exécute. Le fichier `IA/tâches/<nom>.md` est la source de vérité ;
le timer systemd, le planificateur du harness ou le cron de la machine n'en
sont que des **instances** — jetables, reconstructibles.

Le motif est le même qu'au §11 pour les index : ce qui n'existe qu'à un seul
endroit se perd sans que rien ne le signale. Sans registre, changer de harness
ou de machine efface silencieusement des tâches dont plus personne ne connaît
l'existence. Avec registre, la perte se répare : on relit le registre et on
ré-instancie.

Trois règles en découlent :

- **Le registre déclare une intention, jamais un état.** Ni identifiant
  d'instance, ni nom de machine, ni date du dernier déclenchement : ces
  informations vieillissent mal, et le dépôt se publie (§13.5). L'état se lit
  chez l'exécutant, au moment où on le demande. `exécutant` n'y déroge pas :
  il dit quelle **classe** d'exécutant a le droit de déclencher la tâche, pas
  où elle tourne en ce moment — une règle, pas un constat.
- **Une tâche = au plus une instance vivante, tous exécutants confondus.**
  C'est l'invariant du registre. Sans lui, une tâche créée par le
  planificateur du harness puis instanciée en timer local se déclenche deux
  fois — et la réconciliation, qui ne regarderait qu'un seul exécutant,
  fabriquerait elle-même le doublon en croyant réparer un manque. Le champ
  `exécutant` du §5 tranche d'avance : il dit qui, et donc qui pas.
- **Une instance porte le nom de sa tâche, préfixé `obsia-`.** C'est la seule
  clé qui permette de rapprocher registre et exécutant quel que soit ce
  dernier ; le préfixe distingue au passage ce qui vient du coffre de ce que
  l'utilisateur a planifié par ailleurs.
- **L'instruction d'une tâche est auto-suffisante.** Au déclenchement il n'y a
  plus de conversation : le corps du fichier est tout ce qui sera reçu.

Créer, modifier ou suspendre une tâche touche `IA/tâches/` : **patch Git revu**
(§2). Instancier ou retirer une instance chez l'exécutant est une action à
effet externe : une ligne horodatée au carnet (§9).

`IA/system/taches-index.md` en est l'index généré, toujours présent en
contexte : c'est par lui qu'un harness neuf apprend qu'une tâche existe.
**Savoir n'est pas instancier** — l'index informe, il ne déclenche rien ; c'est
ce qui permet de constater qu'une tâche déclarée ne tourne nulle part.

La procédure — lister, créer, instancier, réconcilier — vit dans le skill
`cron` (`IA/skills/cron/cron.md`). Ce contrat ne nomme aucun exécutant : il dit
*quoi* planifier, le harness fournit *avec quoi*.
