---
schema: 1
kind: skill
name: cloture-de-session
description: Clore une séance de travail — consigner ce qui a été décidé dans la note de projet, en distiller ce qui est durable vers profil/préférences/expériences, proposer le log du §9. À charger en fin de séance, quand une session se termine ou qu'un lot de travail est livré. Pas pour écrire une note isolée en cours de route.
type: core
read_only: false
---

# Skill — Clôture de session

Une session laisse deux traces de nature différente : ce qui s'est **passé**
(chronologie, propre au projet) et ce qui a été **appris** (durable,
transversal). Sans distillation explicite, la seconde reste enfouie dans la
première et se re-découvre à chaque fois.

## Procédure

### 1. Établir ce qui a été touché

```bash
git status --short
git log --oneline origin/main..HEAD
```

Ne pas se fier à sa mémoire de la conversation : lire le diff.

### 2. Écrire ou compléter la note de projet

`mémoire/<agent>/<projet>/AAAA-MM-JJ-titre.md`, structurée pour que le
générateur de sommaires en tire quelque chose d'utile :

```markdown
# AAAA-MM-JJ — Titre

Une ou deux phrases de chapeau. C'est ce qui remontera dans le sommaire.

## Statut
🟢 / 🟡 / 🔴 — état en une ligne.

## Décisions
## Évidence
## Interprétation
## Questions ouvertes
## Synthèse IA
## URLs sources
```

Le §8 du contrat impose de distinguer évidence, interprétation et synthèse. Le
chapeau et `## Statut` sont ce que le sommaire extrait : les bâcler rend le
sommaire inutile.

### 3. Distiller — l'étape qui se saute toujours

Relire la note qu'on vient d'écrire et se demander, ligne par ligne : **est-ce
que ça ne vaut que pour ce projet ?** Si non, ça remonte, selon le tableau du
§6 :

| Ce qu'on a appris | Destination |
| --- | --- |
| un fait stable sur l'utilisateur, son poste, son infrastructure | `profil-utilisateur.md` |
| un goût, une règle qui vaudra ailleurs | `préférences/<sujet>.md` |
| une leçon tirée d'un échec ou d'une réussite | `expériences/<sujet>.md` |

**Lire d'abord la note durable existante.** Un fait qui change se corrige sur
place ; il ne s'écrit pas une seconde fois à côté. C'est la règle du §10.3.

Ce qui ne remonte jamais : un détail d'exécution, une supposition non vérifiée,
un secret, ou une leçon qu'on n'a pas réellement éprouvée.

### 4. Compiler la leçon — sinon elle ne servira jamais

Une leçon rangée dans `expériences/` ne change rien tant que le skill que
l'agent lit pour agir ne la porte pas. Pour chaque leçon écrite à l'étape 3,
une question : **quel skill aurait évité ça ?**

| Réponse | Ce qu'on fait |
| --- | --- |
| aucun skill n'est en cause | rien — la leçon reste une note, c'est une réponse valable |
| un skill existant | le modifier via `createur-de-skill` |
| le geste n'a pas de skill | le noter comme skill à créer, sans le créer dans la foulée |

Ce qui passe dans le skill est **la règle**, pas le récit : le skill dit quoi
faire, la note garde le symptôme, la cause et comment on l'a su. Recopier la
note dans le skill l'alourdit et fait diverger les deux à la première
correction.

Dans les deux derniers cas, ajouter une ligne à
`IA/system/impact-des-skills.md` — dossier `IA/system/`, donc **patch soumis à
revue** comme le log de session (§2).

**Une seule leçon compilée par clôture.** Deux skills modifiés dans le même
patch, et plus rien ne dit lequel a aidé.

### 5. Surveiller la taille

Une note de projet dépassant **~6 000 caractères** mérite d'être découpée ou
résumée. Repère mesuré le 2026-09-03 : la note moyenne du coffre fait 3 200
caractères, et une seule note de 15 900 en représentait alors 29 % à elle
seule. Une note qui enfle est le vrai risque de surcharge — pas l'absence de
couche d'index.

```bash
find mémoire -name '*.md' ! -name sommaire.md -exec wc -m {} \; | sort -rn | head -5
```

### 6. Proposer le log de session

`IA/system/session-log/AAAA-MM-JJ.md` — décisions, fichiers modifiés, questions
ouvertes. Ce dossier vit sous `IA/system/` : **patch soumis à revue**, jamais
d'écriture directe (§9).

Le log raconte la séance ; la note de projet documente le sujet. Les deux ne
disent pas la même chose et ne se remplacent pas.

### 7. Régénérer et vérifier

```bash
python3 scripts/regenerate_sommaire.py
python3 scripts/regenerate_index.py
python3 scripts/verifier_coffre.py
```

## Contraintes

Les zones d'écriture directe et celles qui passent par patch sont définies au
§2 de `../system/VAULT-CONTRACT.md`. La distillation écrit dans
`mémoire/<agent>/` — zone directe ; le log de session, non.
