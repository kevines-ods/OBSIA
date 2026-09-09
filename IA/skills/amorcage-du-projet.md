---
schema: 1
kind: skill
name: amorcage-du-projet
description: Poser le squelette d'un dépôt neuf avant la première tranche — licence choisie explicitement, .gitignore qui couvre les secrets, .env.example versionné, README disant quoi et comment lancer, commande de vérification écrite dès le premier jour, CI minimale qui la lance. À charger une seule fois par projet, entre le plan validé et la première tranche. Ne génère jamais un squelette de cadriciel qu'on n'a pas lu.
type: outil
read_only: false
---

# Skill — Amorçage du projet

Ce qui manque au premier commit se rattrape mal. Un secret poussé une fois
reste dans l'historique ; un dépôt public sans licence n'est réutilisable par
personne, pas même par son auteur six mois plus tard ; une commande de
vérification qu'on n'a jamais écrite n'existera jamais.

Cette étape se fait **une fois**, entre `docs/PLAN.md` validé et la première
tranche. Elle prend dix minutes.

## 1. La licence — demandée, jamais supposée

Poser la question une fois, avec ses conséquences :

| Licence | Ce qu'elle impose | Pour qui |
| --- | --- | --- |
| **AGPL-3.0** | qui héberge un service dérivé doit publier ses modifications | copyleft fort, cohérent avec un coffre sous AGPL |
| **GPL-3.0** | qui distribue un dérivé doit le publier ; l'hébergement échappe | logiciel installé plutôt que service |
| **MIT** | rien, ou presque | diffusion maximale, appropriation possible |

Un dépôt part **toujours** avec une licence, y compris privé : le rendre
public plus tard sans licence oblige à retrouver tous les contributeurs.

## 2. Les secrets — avant le premier commit, pas après

```bash
printf '%s\n' '.env' '*.local' > .gitignore   # puis compléter selon la stack
```

- `.env.example` est **versionné** : il liste les variables attendues, avec
  des valeurs factices. C'est la documentation des secrets.
- `.env` n'est **jamais** versionné, et n'est jamais ajouté « juste pour
  tester » : `git rm --cached` retire le fichier du prochain commit, pas de
  l'historique.
- Le §3 vaut ici comme partout : aucune clé, aucun jeton dans le dépôt.

## 3. Le README — trois sections, pas plus

Ce que c'est en deux phrases · comment le lancer · comment le vérifier. Un
README qui ne dit pas comment lancer le projet oblige à relire le code pour
répondre à la première question que tout le monde pose.

## 4. La commande de vérification — écrite maintenant

C'est le point qui se saute et qui coûte le plus cher. Écrire dans le README
**la** commande qu'un contributeur lance avant de proposer un changement :
formatage, analyse statique, tests. `livraison-git` ira la chercher là.

Si le projet n'a encore rien à vérifier, écrire la plus petite qui soit vraie
— démarrer et voir qu'il démarre. Une commande minuscule qui existe vaut mieux
qu'une suite de tests qui n'existera jamais.

## 5. Une CI qui lance exactement cette commande

Pas plus. Une CI qui fait autre chose que la vérification locale crée deux
vérités, et c'est celle qui échoue le vendredi soir qu'on découvre.

## 6. Premier commit

Le squelette et les quatre documents de cadrage, rien d'autre. Puis, si
l'utilisateur le demande, la publication du dépôt distant — c'est une action
à effet externe, il choisit public ou privé (`livraison-git`).

## Piège

Un générateur de cadriciel produit deux cents fichiers en trois secondes.
Aucun n'a été lu, et l'on ne saura pas lesquels comptent le jour où quelque
chose casse. Partir du plus petit squelette qui tourne et ajouter en
comprenant ; le générateur reste un choix légitime, mais alors on lit ce qu'il
a écrit avant de committer.
