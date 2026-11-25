---
schema: 1
kind: skill
name: diagnostic-de-session
description: Autopsier une séance qui a mal tourné — un skill qui n'a pas tiré, du travail refait en boucle, des frais partis sans qu'on voie où — en lisant les journaux du harness et en rendant chaque constat appuyé sur un emplacement cité. À charger à la demande, quand l'utilisateur veut savoir pourquoi une séance a dérapé ; ne corrige rien, ne remplace pas compilation-des-leçons.
module: noyau
type: outil
read_only: true
---

# Skill — Diagnostic de séance

> **Adaptation.** Reprend `diagnosing-superpowers` de `obra/superpowers`
> (MIT), condensé et traduit ; le harness spécifique y devient « le harness »,
> et la procédure de correction des skills (elle existe là) renvoie ici à
> `compilation-des-leçons`.

Une séance dérare : elle refait trois fois le même travail, ignore son plan,
tire un skill qui ne concernait rien, ou part en frais sans qu'on voie où.
La mémoire de ce qui s'est passé existe — ce sont les journaux de session du
harness. Ce skill dit comment la lire, et ce qu'un constat doit porter pour
compter.

**Principe.** Pas d'emplacement cité, pas de constat — et un nombre vient du
journal ou d'une commande rejouée, jamais de mémoire.

## 1. Cadrer la plainte

« C'était trop long », « ça a dérapé » : ce sont des plaintes, pas des
énoncés. Une question à la fois, jusqu'à pouvoir écrire : quelle séance (ou
quelles), la plage de tours si elle est connue, ce que l'utilisateur attendait,
ce qui s'est passé, et **l'observable** qui compte — le temps, un geste précis
répété, une action qui n'aurait pas dû avoir lieu. L'énoncé cadreur, rédigé,
attend l'accord avant de continuer : une autopsie menée sur le mauvais
problême dépense le budget du journal pour rien.

## 2. Localiser les journaux

Les journaux de session vivent **hors du dépôt**, à un emplacement propre à
chaque harness — les chercher, ne pas les deviner, et dire quel candidat on
écarte. Vérifier que c'est la bonne séance : en citer le premier message et
l'heure.

- **Lecture seule absolue** sur ces fichiers : jamais modifiés, déplacés ni
  supprimés, même « pour ranger ».
- Une ligne de journal peut être énorme — lire par plages, pas d'un bloc.
- Distinction qui protège le constat : les prompts système, les rappels de
  hooks et les sorties d'outils **ne sont pas les mots de l'utilisateur** ;
  dans le journal d'un sous-agent, « l'utilisateur » est l'agent appelant.

## 3. Lire par dimension

Lire soi-même la région du problème signalé, puis élargir selon les
questions posées, une dimension à la fois :

| Dimension | Ce qu'on cherche |
| --- | --- |
| chronologie des skills | lesquels ont tiré, lesquels étaient attendus et muets, et à quel tour |
| adhésion au plan | où la séance s'est écartée de son plan écrit, et si l'écart était annoncé |
| travail répété | le même geste refait, la même lecture relue, le même fichier réécrit |
| coûts | temps, taille des contextes, tours — comptés depuis le journal, jamais estimés |

Chaque constat passe le même filtre : **un emplacement (chemin et ligne) ou
une sortie citée**, et rien d'autre dans la colonne des faits.

## 4. Le rapport

Rendu dans la conversation, dans cet ordre : l'énoncé du problème (celui
validé en 1), les constats avec leurs citations, et ce que les citations
prouvent — sans enjambée au-delà. Ce qu'un constat ne prouve pas se dit
autant que ce qu'il prouve.

Le rapport ne **corrige** rien : aucun changement de skill, d'agent ni de
configuration ne se déduit de l'autopsie. Si une leçon en sort, elle suit
`compilation-des-lecons` ; ce qui reste vit au carnet du chantier concerné,
s'il existe, à ses règles à lui.

## Ce que le rapport ne montre jamais

Les valeurs à forme de secret lues dans un journal restent **hors du
rapport** : on cite l'emplacement, la valeur est masquée (§4 du
`../system/VAULT-CONTRACT.md`). Un journal de session est un fourre-tout des
sorties d'outils — il contient ce que la séance a lu, secrets compris.

## Rationalisations

| Ce qu'on se dit | La réalité |
| --- | --- |
| « le problème est évident, pas besoin de cadrer » | l'énoncé décide de ce qu'on lira ; une autopsie hors sujet ne se recadre pas |
| « je me souviens de ce qu'il a fait » | sans citation, ce n'est pas un constat, c'est un souvenir — et les deux se contredisent souvent |
| « trop long, c'est déjà la réponse » | long est une mesure ; elle se compte depuis le journal, ou elle n'existe pas |
| « j'ai vu, je corrige le skill tout de suite » | ce skill ne corrige rien ; la leçon passe par `compilation-des-lecons` |
| « tant qu'à lire, je balaie toute la séance » | une ligne peut peser un méga-octet ; on lit la région du problème, le reste à la demande |
