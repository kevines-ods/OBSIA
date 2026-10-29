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
celui qui l'exécute. Deux emplacements, selon ce que la tâche fait :

| La tâche… | Vit dans | Écriture |
| --- | --- | --- |
| est générique — elle vaudrait pour toute installation d'OBSIA | `IA/tâches/<nom>.md` (dépôt produit) | patch Git revu |
| est **propre à cette installation** — elle sert, nomme un rôle d'une machine précise du parc de l'utilisateur, ou n'a de sens que pour le mainteneur de ce coffre (une publication depuis son dépôt privé, par exemple) — rien qui vaudrait pour toute installation d'OBSIA | `Mon coffre/0-PROJETS/tâches-planifiées/<nom>.md` (coffre parent) | écriture directe tracée (§7.4) |

Le fichier retrouvé, où qu'il soit, est la source de vérité pour cette tâche ;
le timer systemd, le planificateur du harness ou le cron de la machine n'en
sont que des **instances** — jetables, reconstructibles. Le registre du coffre
ne se publie pas (`publier.py` n'atteint pas le coffre parent, §13.5) : il fait
foi pour ses propres tâches sans jamais apparaître dans le miroir public.
`IA/system/taches-index.md`, généré et versionné, ne liste donc que
`IA/tâches/` ; une ligne y signale qu'un registre privé existe, sans nommer ses
tâches.

Le motif est le même qu'au §11 pour les index : ce qui n'existe qu'à un seul
endroit se perd sans que rien ne le signale. Sans registre, changer de harness
ou de machine efface silencieusement des tâches dont plus personne ne connaît
l'existence. Avec registre, la perte se répare : on relit le registre et on
ré-instancie.

Cinq règles en découlent :

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
- **Un même nom ne se déclare pas aux deux emplacements.** Les deux registres
  comptent ensemble pour l'invariant ci-dessus : un nom présent à la fois dans
  `IA/tâches/` et dans le registre du coffre est un doublon de déclaration,
  même sans instance — le skill `cron` le signale en listant les deux côtés
  avant d'agir.
- **Une instance porte le nom de sa tâche, préfixé `obsia-`.** C'est la seule
  clé qui permette de rapprocher registre et exécutant quel que soit ce
  dernier ; le préfixe distingue au passage ce qui vient du coffre de ce que
  l'utilisateur a planifié par ailleurs.
- **L'instruction d'une tâche est auto-suffisante.** Au déclenchement il n'y a
  plus de conversation : le corps du fichier est tout ce qui sera reçu.

Créer, modifier ou suspendre une tâche du dépôt touche `IA/tâches/` : **patch
Git revu** (§2) ; une tâche propre à cette installation touche le registre
privé du coffre :
**écriture directe tracée** (§7.4 de `contrat-coffre-parent`). Instancier ou
retirer une instance chez l'exécutant est une action à effet externe : une
ligne horodatée au carnet (§9).

`IA/system/taches-index.md` en est l'index généré, toujours présent en
contexte : c'est par lui qu'un harness neuf apprend qu'une tâche existe.
**Savoir n'est pas instancier** — l'index informe, il ne déclenche rien ; c'est
ce qui permet de constater qu'une tâche déclarée ne tourne nulle part.

La procédure — lister, créer, instancier, réconcilier — vit dans le skill
`cron` (`IA/skills/cron/cron.md`). Ce contrat ne nomme aucun exécutant : il dit
*quoi* planifier, le harness fournit *avec quoi*.
