---
schema: 1
kind: skill
name: relecture-adverse
description: Soumettre une décision non triviale à une relecture qui cherche à la faire tomber, avant qu'elle tienne — énoncer la thèse, isoler l'objet sans son raisonnement, la réfuter, trier les objections, s'arrêter. À charger avant une décision d'architecture, une opération irréversible, ou du travail dans du code mal connu. Sans contexte neuf, la relecture est dégradée et doit être annoncée comme telle.
type: outil
read_only: true
---

# Skill — Relecture adverse

> **Adaptation.** Reprend `doubt-driven-development` d'`addyosmani/agent-skills`
> (MIT), condensé et traduit. Sa limite — une relecture sans contexte neuf
> n'en est pas une — est reprise telle quelle, parce que c'est la partie qu'on
> est tenté d'oublier.

Une réponse assurée n'est pas une réponse juste. Une longue conversation
accumule un contexte qui transforme des hypothèses en faits sans que personne
ne le remarque : ce qu'on a supposé au dixième message est devenu, au
cinquantième, ce qu'on sait.

Ce n'est pas une revue de fin de parcours — c'est une **posture en cours de
route**, appliquée tant que se corriger coûte encore peu.

## Ce qui mérite ce traitement

Une décision est **non triviale** dès qu'une de ces conditions tient :

- elle introduit ou modifie une logique conditionnelle ;
- elle traverse une frontière — module, service, machine ;
- elle affirme une propriété que rien ne vérifie mécaniquement : c'est sûr,
  c'est idempotent, l'ordre est garanti, ça passe à l'échelle ;
- sa justesse dépend d'un contexte que le prochain lecteur n'aura pas ;
- elle est **irréversible** : mise en production, migration de données,
  interface publique, suppression.

**Ce qui ne le mérite pas** : un renommage, un déplacement de fichier, une
lecture, une instruction claire de l'utilisateur, un changement d'une ligne
dont la justesse est évidente. Qui doute de chaque frappe ne livre rien.

## Le cycle

```
THÈSE ──→ ISOLER ──→ RÉFUTER ──→ TRIER ──→ ARRÊTER
ce qui    l'objet     chercher     que      et le dire
tient     sans le     ce qui le    reste-
en 3      raisonnement fait        t-il ?
lignes    qui y mène  tomber
```

### 1. Énoncer la thèse

Deux ou trois lignes, pas plus :

```
THÈSE : la couche de cache est sûre si deux requêtes arrivent en même temps.
CE QUE ÇA COÛTE SI C'EST FAUX : des données mélangées entre deux
                                utilisateurs, invisible en test.
```

Si la thèse ne s'écrit pas en trois lignes, il n'y a pas de décision — il y a
une impression. L'énoncer d'abord, la contester ensuite.

### 2. Isoler l'objet — sans le raisonnement

Le relecteur a besoin de **l'objet** et de **ce qu'il doit respecter**, pas du
chemin qui y a mené :

- du code : le diff ou la fonction, pas le fichier entier ;
- une décision : la proposition en cinq phrases, plus les contraintes qu'elle
  doit satisfaire.

**Retirer son raisonnement.** Transmettre ses conclusions revient à demander
la validation de ses conclusions. Si l'objet est trop gros pour être tenu en
tête d'une lecture, il se découpe d'abord.

### 3. Réfuter — le cadrage décide de la réponse

La consigne est **adverse**, et elle s'énonce :

> *Cherche ce qui est faux dans cet objet. Ne dis pas ce qui est bien. Pour
> chaque problème : le scénario concret qui le déclenche, et ce qu'il produit.*

« Est-ce que ça te paraît correct ? » obtient un oui. C'est le cadrage qui
produit la réponse, pas la qualité du relecteur.

### 4. Trier les objections

Chacune se range dans une des trois cases, et une seule :

| Case | Ce qu'on en fait |
| --- | --- |
| **vraie** — le scénario tient | corriger avant que la décision tienne |
| **fausse** — le scénario ne peut pas se produire, et on sait pourquoi | l'écrire : cette raison manquait à l'objet, c'est donc un défaut de clarté |
| **hors sujet** — vraie mais sans rapport avec la thèse | noter ailleurs, ne pas élargir |

Une objection fausse n'est jamais gratuite : si un relecteur a pu la former,
l'objet ne disait pas assez.

### 5. Arrêter

Trois conditions d'arrêt, la première atteinte suffit :

- il ne reste que des objections mineures ;
- **trois cycles** sont passés — au-delà, ce n'est plus du doute, c'est du
  sur-place ;
- l'utilisateur tranche.

## La limite — à annoncer, jamais à masquer

Tout ce skill repose sur **un contexte neuf**. Appliqué dans la conversation
où la décision a été prise, il ne réfute rien : il relit ses propres
conclusions avec ses propres hypothèses, et conclut qu'elles tiennent.

Quand le contexte neuf n'est pas possible :

1. **le dire** et proposer que la relecture ait lieu dans une session neuve ;
2. si c'est impossible et que l'utilisateur veut avancer : réécrire thèse et
   contraintes comme un énoncé autonome, dérouler les cinq étapes, et
   **annoncer le résultat comme dégradé**.

Une relecture dégradée présentée comme une garantie est pire que pas de
relecture : elle fait baisser la garde.

## Rationalisations

| Ce qu'on se dit | La réalité |
| --- | --- |
| « j'ai déjà vérifié en écrivant » | vérifié avec les hypothèses qui ont produit le code. C'est le contexte, pas la vigilance, qui manque |
| « ça va me faire perdre du temps » | moins que déboguer en production une propriété qu'on avait affirmée |
| « le relecteur n'a pas trouvé de problème » | avec quelle consigne ? « Ça te paraît bon ? » obtient toujours un oui |
| « cette objection est absurde » | peut-être. Alors écrire pourquoi — et cette raison manquait à l'objet |
| « on a fait trois tours, continuons » | trois tours sans convergence veut dire que le problème est ailleurs : dans la conception, pas dans le détail |

## Contraintes

`read_only: true` : ce skill lit, questionne et rapporte. Il ne corrige rien
et n'exécute aucune commande modifiant l'état du système — s'il conclut à une
action, il l'énonce sans la faire (§10 de `../system/VAULT-CONTRACT.md`).
