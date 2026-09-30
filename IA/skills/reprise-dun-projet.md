---
schema: 1
kind: skill
name: reprise-dun-projet
description: Reprendre une application ou un projet existant qu'on n'a pas écrit soi-même, et comprendre comment il marche — cartographier le code, ses points d'entrée, ses dépendances et l'état de ses tests, repérer les zones fragiles, puis reconstituer `docs/CADRAGE.md` et `docs/STACK.md` à partir de ce que le code fait réellement. À charger avant de modifier, d'étoffer ou de faire évoluer un projet déjà écrit, juste après l'inventaire de l'existant. Ne modifie aucune ligne de code.
module: construction
type: outil
read_only: false
---

# Skill — Reprise d'un projet

Un projet existant a déjà pris ses décisions — souvent sans les écrire. Le
modifier sans les connaître, c'est défaire en trois lignes un choix qui avait
une raison. Ce skill transforme un code qu'on ne connaît pas en documents
qu'on peut relire et valider, **avant** d'y toucher.

Il remplace, pour un projet existant, les portes 3 et 4 du bâtisseur : on ne
cadre pas un besoin et on ne choisit pas une stack, on **constate** ceux qui
sont déjà là.

## Procédure

### 1. Faire tourner le projet tel quel

Avant de lire, lancer. Installer, démarrer, exécuter la suite de tests —
**dans un environnement isolé** (conteneur jetable, machine de test), jamais
sur la machine de l'agent : une installation exécute le code des dépendances
(`postinstall`, `setup.py`), que personne n'a encore audité (§4) :

```bash
git -C <dépôt> status && git -C <dépôt> log --oneline -15
# puis la commande d'installation et de test que le README ou la CI indique
```

Noter ce qui échoue **avant** toute modification. Un test déjà rouge qu'on
découvre après son premier commit devient « la faute du changement » — et on
passe une heure à chercher une régression qui n'existe pas.

Si le projet ne démarre pas du tout, c'est le premier constat, et il passe
avant le reste : charger `investigation-de-bug`.

### 2. Cartographier en cinq questions

| Question | Où regarder |
| --- | --- |
| Par où entre-t-on ? | `main`, routes, commandes CLI, points d'entrée déclarés dans le fichier de dépendances |
| Quelles couches, et qui appelle qui ? | arborescence, imports ; un diagramme `mermaid` si plus de quatre modules |
| Sur quoi repose-t-il ? | fichier de dépendances et leurs **versions** ; services externes, base de données |
| Qu'est-ce qui est testé ? | dossier de tests, couverture si l'outil existe ; sinon, lister ce qui ne l'est pas |
| Comment est-il livré ? | CI, Dockerfile, compose, scripts de déploiement |

On lit les points d'entrée et on suit un parcours utilisateur de bout en bout.
On ne lit pas tout le code : une carte n'est pas un inventaire ligne à ligne.

### 3. Repérer les zones fragiles

Trois signaux suffisent à les trouver :

- **le churn** — les fichiers les plus modifiés sont ceux où les bogues vivent :
  `git -C <dépôt> log --format= --name-only | sort | uniq -c | sort -rn | head -15` ;
- **l'absence de test** sur un chemin critique (paiement, écriture de données,
  authentification) ;
- **les aveux dans le code** — `TODO`, `FIXME`, `HACK`, un `try` qui avale tout.

Une zone fragile n'est pas à réparer maintenant : elle est à **connaître**.
Elle décidera plus tard s'il faut des `tests-de-caracterisation` avant d'y
entrer.

### 4. Reconstituer les documents

Dans le dépôt du projet, écrire ce que le code **fait**, pas ce qu'on
voudrait qu'il fasse :

- `docs/CADRAGE.md` — mêmes sections que `cadrage-produit`, remplies par
  constat. Ce qu'on ne peut pas déduire du code se marque `à confirmer` et se
  demande à l'utilisateur ;
- `docs/STACK.md` — la stack réelle, versions comprises, et pour chaque choix
  « raison connue » ou « raison inconnue ». Aucune recommandation de
  changement ici : c'est le rôle de `dette-technique` ou `montee-de-version`.

Si ces documents existent déjà, les **comparer** au code : un écart entre le
cadrage écrit et le comportement réel est un constat à rapporter, pas à
corriger en silence d'un côté ou de l'autre.

### 5. Restituer et faire valider

Présenter la carte, les zones fragiles et les deux documents. La porte n'est
franchie que lorsque l'utilisateur a confirmé que le cadrage reconstitué
décrit bien son projet — y compris les points `à confirmer`.

## Rationalisations

| Ce qu'on se dit | La réalité |
| --- | --- |
| « le changement est petit, pas besoin de tout comprendre » | le petit changement touche le module que trois autres appellent, et on ne le saura qu'en production |
| « les tests passaient sûrement avant moi » | sans les avoir lancés, le premier test rouge sera mis sur le compte de ton commit |
| « je documenterai une fois que j'aurai compris » | ce qu'on a compris sans l'écrire est perdu à la séance suivante, et l'utilisateur n'a rien pu corriger |
| « ce choix de stack est bizarre, je le change au passage » | il avait peut-être une raison ; un constat va dans `docs/STACK.md`, pas dans le diff |
| « je lis tout le code pour être sûr » | une carte se fait par les points d'entrée ; lire tout, c'est ne rien retenir |

## Ce que ce skill ne fait pas

Il n'écrit que dans `docs/` du dépôt du projet, et ne modifie aucune ligne de
code. Le travail sur le dépôt suit le §3 de `../system/VAULT-CONTRACT.md`.
