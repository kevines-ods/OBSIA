---
schema: 1
kind: skill
name: extrapolation-des-finalites
description: Fixer avec l'utilisateur la finalité d'un projet et où il pourrait aller — une question par message, trois à cinq avenirs possibles validés ou rejetés un par un, portes à garder ouvertes — puis écrire la note `— vision` du projet, qui reste même après la clôture d'un chantier. À charger au premier appel du visionnaire sur un projet, ou quand la finalité change. Ne juge aucun changement : c'est `controle-de-cap`.
module: noyau
type: outil
read_only: false
---

# Skill — Extrapolation des finalités

Une finalité floue ne départage rien : « faire un bon outil » valide tous les
changements. Ce skill produit une finalité assez précise pour qu'un changement
puisse s'en éloigner — et la liste des avenirs qu'on refuse de rendre
impossibles.

## Procédure

1. **Relire avant de demander.** Note `— résumé` du projet, `docs/CADRAGE.md`
   s'il existe, note `— vision` existante. Ne pas poser une question dont la
   réponse est déjà écrite.
2. **La finalité déclarée.** Interroger l'utilisateur, **une question par
   message**, jusqu'à pouvoir écrire en deux phrases : pour qui, quel
   changement dans sa vie quand le projet est réussi. Reformuler ; la porte est
   franchie quand l'utilisateur ne corrige plus.
3. **Extrapoler.** Proposer trois à cinq finalités possibles — ce que le
   projet pourrait devenir s'il réussit : plus d'utilisateurs, un autre
   support, une ouverture publique, une automatisation, un abandon partiel.
   Chacune en une phrase, avec ce qui la rend plausible.
4. **Faire trancher, une par une.** Pour chacune : validée, rejetée, ou
   « pas encore ». Garder la raison d'un rejet — c'est elle qui évite de la
   reproposer.
5. **Dériver les portes à garder ouvertes.** Pour chaque finalité validée, ce
   qui ne doit jamais devenir impossible (« les données restent exportables »,
   « rien ne suppose un seul utilisateur »). Une porte se formule comme une
   contrainte vérifiable, pas comme une fonctionnalité à construire.
6. **Écrire la note**, après preview (§7.4 du contrat).

## La note — `<projet> — vision.md`

Elle vit à la racine du dossier du projet, dans le coffre parent :
`Mon coffre/0-PROJETS/<projet>/` (§7.1), pour un projet du coffre comme pour un
projet de l'utilisateur. La vision **ne s'archive pas** : à la clôture d'un
chantier, seul le dossier du chantier passe dans `0-MEMOIRES/`, la vision reste
dans `0-PROJETS/` (§6). Un chantier n'en a pas.

```markdown
---
auteur: visionnaire
projet: "[[<projet> — résumé]]"
révisée: AAAA-MM-JJ
---

# <projet> — vision

## Finalité déclarée
Deux phrases : pour qui, quel changement.

## Finalités possibles
| Finalité | Statut | Raison |
| --- | --- | --- |
| … | validée / rejetée / pas encore | … |

## Portes à garder ouvertes
- contrainte vérifiable — finalité qu'elle protège

## Signaux d'abandon
Ce qui montrerait qu'une finalité n'est plus visée.

## Révisions
- AAAA-MM-JJ — ce qui a changé, et pourquoi
```

Le rétrolien vers `— résumé` n'est posé que si la note existe (§7.5). Une
révision corrige la note sur place et ajoute une ligne à `## Révisions` ;
elle ne crée jamais une seconde note.

## Rationalisations

| Ce qu'on se dit | La réalité |
| --- | --- |
| « la finalité est évidente, je l'écris directement » | une finalité que l'utilisateur n'a pas reformulée avec toi est la tienne, et tous les verdicts suivants jugeront ton projet, pas le sien |
| « je pose toutes les questions d'un coup, ça ira plus vite » | il répondra aux deux premières et survolera les autres ; la finalité sortira à moitié fixée |
| « je mets toutes les finalités en validées, on ne sait jamais » | chaque porte ouverte contraint chaque décision ; dix portes, et plus aucun choix n'est permis |
| « cette finalité possible mérite qu'on la construise dès maintenant » | c'est le projet qui grossit sans que personne ne l'ait décidé |
| « l'utilisateur a changé d'avis, je réécris la note » | sans la ligne de révision, on ne saura plus pourquoi une ancienne décision avait été prise |
