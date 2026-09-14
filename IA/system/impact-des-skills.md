# impact-des-skills.md — Ce qu'une leçon a réellement changé

Une leçon écrite dans `mémoire/<nom-agent>/expériences/` ne change rien par
elle-même. Tant qu'elle n'est pas **compilée** dans le skill que l'agent lit
pour agir, elle reste une note que personne ne rouvre au bon moment.

Ce registre est le chaînon manquant : il dit, pour chaque leçon, quel skill
elle a modifié, ce qui a été vérifié, et si le changement tient toujours.
Sans lui, deux pannes silencieuses — une leçon vraie qui ne sert jamais, et
une modification de skill dont plus personne ne sait pourquoi elle est là.

## Les deux couches, et pourquoi elles ne se rétractent pas ensemble

| Couche | Où | Ce qu'elle porte | Peut-on l'annuler ? |
| --- | --- | --- | --- |
| la leçon | `mémoire/<nom-agent>/expériences/` | le récit : le symptôme, la cause, comment on l'a su | **non**, jamais |
| le skill | `IA/skills/` | la règle compilée : quoi faire, sans le récit | **oui**, par `git revert` |

L'asymétrie est le cœur du dispositif. Une leçon reste vraie même quand la
façon de l'appliquer était mauvaise : annuler la modification d'un skill
n'autorise pas à effacer la note qui l'a motivée — sinon on réapprend la même
chose au prochain échec, et le registre perd sa raison d'être.

Corollaire : le skill porte **la règle**, la note garde **l'histoire**. Une
leçon recopiée telle quelle dans un skill l'alourdit sans le rendre plus
actionnable, et les deux divergent à la première correction.

## Le tableau

Sept colonnes. `Revue` est la date à laquelle on confirme le changement ou on
l'annule : une modification que rien n'a confirmée depuis n'est pas acquise.

| Date | Leçon | Skill touché | Ce qui a changé | Vérifié par | Statut | Revue |
|---|---|---|---|---|---|---|
| 2026-09-13 | `rendu-mermaid-en-conteneur` | `mermaid` | le prérequis n'est plus « la commande est installée » (`-h`) mais « elle arrive au bout » : rendu jetable à lancer, et configuration Puppeteer `-p` si la machine n'a pas de session graphique | rendu rejoué en conteneur : échec sans les options (`zygote_host_impl_linux.cc`, « Running as root without --no-sandbox »), SVG produit avec | confirmé | — |

## Statuts

| Statut | Ce qu'il veut dire |
| --- | --- |
| `proposé` | la modification est écrite mais pas fusionnée |
| `appliqué` | fusionnée, en attente de confirmation par un cas réel |
| `confirmé` | un cas réel a montré que le skill modifié fait mieux |
| `annulé` | `git revert` — la ligne reste, avec la raison en clair |

Une ligne ne se supprime jamais. Un changement annulé qu'on efface est un
changement qu'on refera.

## Qui lit la colonne « Revue »

Une date de revue que personne ne relit ne vaut rien : sans lecteur, tout
resterait indéfiniment `appliqué`. C'est la tâche
`IA/tâches/revue-mensuelle-des-lecons.md` qui la lit, le 1er de chaque mois.
Elle statue sur les échues **avant** de compiler quoi que ce soit de nouveau —
confirmer, annuler, ou repousser une seule fois avec la raison écrite.

Tant que cette tâche n'est pas instanciée chez un exécutant (`actif: false`
aujourd'hui), la colonne reste déclarative : c'est à qui ouvre ce fichier de
trancher.

## Ce que ce registre ne prouve pas

Il trace, il ne mesure pas. Il n'existe ici ni jeu de validation tenu à
l'écart, ni exécution répétée qui dirait si un skill modifié fait mieux :
la confirmation est humaine, au cas par cas, et c'est ce que dit la colonne
`Revue`.

Le seul contrôle automatique porte sur le **déclenchement** — la description
suffit-elle à charger le bon skill — et vit dans
`IA/system/routage-attendu.md`. Le corps d'un skill, lui, n'est vérifié par
personne : ne pas confondre « le vérificateur est vert » et « la modification
était bonne ».

## Origine

Ce dispositif reprend la partie transposable de WikiSkill (Google Research,
arXiv:2608.27454) : la séparation entre une base de connaissances qui ne se
rétracte jamais et des skills qui, eux, s'annulent. Ce qui n'est **pas**
repris, faute de jeu d'évaluation : la validation automatique d'une
modification de skill et son annulation automatique en cas de régression.
