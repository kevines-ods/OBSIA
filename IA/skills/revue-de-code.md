---
schema: 1
kind: skill
name: revue-de-code
description: Relire un diff sur cinq axes — justesse, lisibilité, architecture, sécurité, performance — et rendre des constats classés par gravité, chacun accompagné du scénario d'échec concret qui le prouve. À charger avant de fusionner un changement, écrit par soi, par un agent ou par quelqu'un d'autre. Constate et rapporte sans rien modifier ; ne double pas ce que l'outillage du projet contrôle déjà.
type: outil
read_only: true
---

# Skill — Revue de code

> **Adaptation.** Condense `code-review-and-quality`, `security-and-hardening`
> et le persona de revue d'`addyosmani/agent-skills` (MIT) en une procédure.
> L'axe sécurité reprend l'essentiel de leur liste de menaces.

Une relecture sans méthode trouve ce qui saute aux yeux : le nommage et le
style. Ce sont les deux choses qu'un outil fait mieux, et pendant qu'on les
regarde, l'erreur de logique passe.

D'où cinq axes, **dans cet ordre** : le premier est celui qui coûte le plus
cher quand on le rate.

## L'ordre des axes

### 1. Justesse — est-ce que ça fait ce que ça prétend ?

C'est l'axe qui compte. Le seul qui produise un défaut invisible à la lecture
rapide.

- Le comportement correspond-il aux critères d'acceptation de la tranche ?
- Les cas limites : zéro, vide, un seul élément, négatif, valeur absente,
  dépassement, deux appels simultanés ?
- Les erreurs sont-elles traitées, ou avalées ? Un `catch` qui ne fait rien
  cache la panne au lieu de la gérer.
- La condition inversée, le `<=` qui devait être `<`, l'indice décalé d'un.

### 2. Lisibilité — le prochain lecteur comprendra-t-il ?

Le prochain lecteur, c'est souvent l'utilisateur dans six mois, sans le
contexte.

- Les noms disent-ils l'intention, ou la mécanique ?
- Faut-il un commentaire pour comprendre *ce que* fait le code ? C'est que le
  code devrait être réécrit — un commentaire explique *pourquoi*, pas *quoi*.
- Reste-t-il du code mort, une sortie de débogage, un bloc commenté ?

### 3. Architecture — est-ce à sa place ?

- La logique métier est-elle mêlée à l'affichage ou à l'accès aux données ?
- La même règle est-elle écrite à deux endroits ? Elles divergeront.
- L'abstraction introduite sert-elle **deux** cas réels, ou un seul imaginé ?
- Le changement dépasse-t-il la tranche annoncée ? C'est un constat de revue
  autant qu'un défaut de discipline.

### 4. Sécurité — y a-t-il une entrée qu'on n'a pas questionnée ?

Le tableau court, dans l'ordre de fréquence réelle :

| À chercher | Le signe |
| --- | --- |
| entrée non fiable employée telle quelle | valeur d'un formulaire, d'une URL, d'un en-tête, d'un fichier, concaténée dans une requête, une commande, un chemin, un gabarit |
| chemin construit depuis une entrée | `../` possible, donc lecture hors du dossier prévu |
| requête sortante vers une adresse fournie | le serveur devient un relais vers le réseau interne |
| autorisation absente | l'authentification dit *qui* ; elle ne dit pas *s'il a le droit sur cet objet-là* |
| secret dans le code, un journal, un message d'erreur | une clé, un jeton, un mot de passe qui sort |
| dépendance ajoutée | qui la maintient, depuis quand, combien de mainteneurs ? |
| donnée personnelle | est-elle nécessaire ? journalisée par accident ? |

Une entrée dont on ne peut pas dire d'où elle vient est une entrée non fiable.

### 5. Performance — seulement si une mesure le justifie

En dernier, et **sans supposition**. Ce qui se relève sans mesurer :

- une requête dans une boucle — le motif qui fait mille appels au lieu d'un ;
- une lecture complète là où une lecture partielle suffirait ;
- un travail refait à chaque appel alors que le résultat ne change pas.

Le reste demande un profil. « Ça pourrait être lent » n'est pas un constat.

## Rendre les constats

Classés par gravité, la plus forte d'abord :

| Gravité | Ce que ça veut dire |
| --- | --- |
| **bloquant** | ça produit un résultat faux, une faille, ou une perte de données |
| **à corriger** | ça marche, mais ça coûtera cher plus tard, et le coût est nommé |
| **à discuter** | un choix défendable des deux côtés — poser la question, pas le verdict |

Chaque constat porte **trois** choses : l'emplacement, ce qui cloche, et **le
scénario d'échec** — quelles entrées produisent quel résultat faux.

Un constat sans scénario est une opinion. « Cette fonction est fragile » ne
s'actionne pas ; « avec une liste vide, elle renvoie `None` et l'appelant fait
`len(None)` » se corrige en trois minutes.

Ce qui ne se rapporte **pas** : ce que le formateur range, ce que l'analyse
statique signale, ce que le plancher de qualité du projet contrôle déjà, et le
goût personnel. Les doubler noie les trois constats qui comptaient.

## Rationalisations

| Ce qu'on se dit | La réalité |
| --- | --- |
| « le diff est petit, un coup d'œil suffit » | les défauts de justesse tiennent en une ligne. C'est la taille du risque qui compte, pas celle du diff |
| « les tests passent, c'est donc bon » | les tests vérifient ce qu'on a pensé à vérifier. La revue cherche ce qu'on n'a pas pensé |
| « je dois bien trouver quelque chose » | une relecture qui doit rapporter un défaut en fabrique un. « Rien trouvé, voici ce que j'ai vérifié » est un résultat |
| « je corrige, c'est plus rapide que d'expliquer » | alors le défaut disparaît sans que personne n'apprenne qu'il existait — et il reviendra |
| « ce nom est mal choisi » | si c'est le seul constat, la revue n'a pas eu lieu. Commencer par la justesse |

## Contraintes

Ce skill est `read_only: true` : il lit un diff et rapporte. Il ne modifie
aucun fichier, n'exécute aucune commande qui change l'état du système, et ne
fusionne rien — la fusion passe par une revue humaine (§3 de
`../system/VAULT-CONTRACT.md`).

Lire le diff se fait en local :

```bash
git diff main...HEAD
git diff --stat main...HEAD
```
