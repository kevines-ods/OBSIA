---
schema: 1
kind: skill
name: choix-de-la-stack
description: Choisir langage, cadriciel, base de données et hébergement en confrontant deux ou trois candidats à des critères écrits d'avance — licence libre, coût d'entretien, adéquation à l'infrastructure existante, capacité réelle à la reprendre en main — et consigner la décision dans `docs/STACK.md`. À charger après le cadrage et avant tout code ou design. Ne se rejoue pas à chaque tranche : la décision est prise une fois.
type: outil
read_only: false
---

# Skill — Choix de la stack

Une technologie ne se choisit pas parce qu'elle est bonne, mais parce qu'elle
est bonne **ici** : sur cette machine, dans cette infrastructure, entretenue
par cette personne, avec ces valeurs. Un choix pris pour d'autres raisons se
paie plus tard, en entretien.

## Procédure

### 1. Écrire les critères AVANT de regarder les candidats

Sinon les critères sont rédigés pour justifier le candidat qu'on préférait
déjà. Six critères, pondérés par l'utilisateur :

| Critère | La question à laquelle il répond |
| --- | --- |
| **Licence** | est-ce du logiciel libre ? sous quelle licence, compatible avec le projet ? |
| **Entretien** | qui met à jour, à quelle fréquence, et que se passe-t-il si personne ne le fait pendant six mois ? |
| **Reprise en main** | l'utilisateur peut-il lire et modifier ce code sans l'agent ? |
| **Infrastructure** | est-ce que ça tourne sur ce qui existe déjà, ou faut-il ajouter une brique ? |
| **Dépendances** | combien de paquets tiers, et lesquels sont maintenus par une seule personne ? |
| **Sortie de secours** | si ce choix déçoit, que coûte le changement ? |

Lire `mémoire/assistant/profil-utilisateur.md` avant de pondérer : poste,
infrastructure, valeurs et rapport au code y sont déjà écrits. Ne pas
redemander ce qui s'y trouve.

### 2. Deux ou trois candidats, pas plus

Un seul candidat n'est pas un choix, c'est une préférence déguisée. Cinq
candidats produisent un tableau que personne ne lit. Toujours inclure le
candidat **le plus ennuyeux** — celui que l'utilisateur connaît déjà, ou celui
qui demande le moins de pièces.

### 3. Le tableau de confrontation

Une ligne par critère, une colonne par candidat, une **phrase** par case — pas
une note sur cinq, qui donne l'illusion d'objectivité et cache le raisonnement.

### 4. Recommander, chiffrer le coût, laisser trancher

Annoncer le candidat recommandé, la raison principale en une phrase, et **ce
qu'on perd** en le choisissant. Un choix sans coût annoncé est un choix mal
compris.

### 5. Écrire `docs/STACK.md`

```markdown
# Stack — <nom du projet>

## Critères retenus et leur poids
## Candidats confrontés
## Décision
Ce qu'on retient, et la raison principale.

## Ce que ça coûte
Ce qu'on perd, et à quel signe on saura que le choix était mauvais.

## Ce qu'on a écarté, et pourquoi
Pour que personne ne rouvre le débat sans élément nouveau.
```

## Règles

- **Aucun secret dans le dépôt** : clés et jetons passent par variables
  d'environnement ou configuration hors dépôt (§3). Le noter ici, quand la
  question se pose, plutôt qu'au moment de déployer dans l'urgence.
- Une pile déjà en place dans l'infrastructure part avec un avantage réel,
  pas sentimental : elle est déjà supervisée, sauvegardée et comprise.
- « C'est ce que tout le monde utilise » n'est pas un critère. « C'est ce que
  j'utilise déjà et que je sais réparer » en est un.

## Après la décision

Une pile qui déçoit à l'usage donne une leçon réutilisable : la consigner dans
`mémoire/batisseur/expériences/`, pas dans la note du projet, qui ne sera plus
relue.
