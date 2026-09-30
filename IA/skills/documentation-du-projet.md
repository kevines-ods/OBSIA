---
schema: 1
kind: skill
name: documentation-du-projet
description: Remettre et tenir à niveau la documentation d'un projet existant — README qui dit quoi et comment lancer, guide de contribution, décisions d'architecture (ADR) numérotées, journal des changements — vérifiée en suivant soi-même les instructions écrites. À charger quand la documentation est absente, périmée ou contredit le code, et à la fin de chaque tranche qui change l'installation, la configuration ou une décision.
module: construction
type: outil
read_only: false
---

# Skill — Documentation du projet

Une documentation qui ment est pire qu'une documentation absente : on la
suit, et on se trompe. Ce skill ne cherche pas à tout documenter ; il garde
vrai ce que quelqu'un d'autre lira pour **installer, contribuer, ou
comprendre une décision**.

## Les quatre documents, et seulement eux

| Document | Il répond à | Se met à jour quand |
| --- | --- | --- |
| `README.md` | quoi, pour qui, comment l'installer et le lancer | l'installation ou la configuration change |
| `CONTRIBUTING.md` | comment proposer une modification, quelles vérifications passer | la chaîne de vérification change |
| `docs/adr/NNNN-titre.md` | pourquoi tel choix a été fait, et ce qu'il a écarté | une décision d'architecture est prise |
| `CHANGELOG.md` | ce qui a changé pour l'utilisateur, par version | une version est livrée |

Pas de document de plus sans raison : chacun est une chose à tenir à jour.
`docs/CADRAGE.md`, `docs/STACK.md` et `docs/PLAN.md` restent ceux du bâtisseur ; on ne
les duplique pas dans le README, on y renvoie.

## Procédure

### 1. Éprouver l'existant

Suivre le README **à la lettre**, dans un environnement propre (conteneur,
répertoire vide), sans rien combler de mémoire. Chaque étape qui échoue ou
qui manque est un constat. C'est la seule vérification qui compte : une
documentation relue n'est pas une documentation testée.

### 2. Corriger ce qui ment, avant d'ajouter

Ordre de priorité :

1. ce qui est **faux** — une commande qui échoue, une variable renommée ;
2. ce qui **manque** pour lancer le projet ;
3. le reste.

### 3. Écrire une ADR par décision

Format court, une décision par fichier, numéroté et jamais réécrit :

```markdown
# 0004 — PostgreSQL plutôt que SQLite

- Statut : acceptée (AAAA-MM-JJ)
- Contexte : deux utilisateurs écrivent en même temps.
- Décision : PostgreSQL.
- Conséquences : un service de plus à sauvegarder ; migrations obligatoires.
- Écartées : SQLite (verrou d'écriture global).
```

Une décision qui change ne s'édite pas : une nouvelle ADR la remplace, et
l'ancienne passe au statut `remplacée par 0007`. C'est ce qui garde
l'historique du raisonnement.

### 4. Vérifier les commandes citées

Chaque bloc de commande du README a été exécuté pendant la séance. Si le
projet a une CI, y ajouter un test de fumée qui lance la commande de
démarrage documentée : la documentation cesse alors de pouvoir mentir sans
que la CI rougisse.

### 5. Livrer avec la tranche

La documentation d'un changement part **dans la même PR** que le changement.
Une documentation promise « pour plus tard » ne s'écrit pas.

## Rationalisations

| Ce qu'on se dit | La réalité |
| --- | --- |
| « le README est à jour, je l'ai relu » | relu n'est pas suivi ; la commande qui a changé de nom ne se voit qu'en la lançant |
| « le code est sa propre documentation » | le code dit comment, jamais pourquoi ni ce qui a été écarté |
| « je documenterai à la fin » | à la fin, les raisons du choix sont oubliées et il ne reste que le résultat |
| « je modifie l'ancienne ADR, c'est plus simple » | on perd la trace de ce qu'on croyait, et pourquoi on a changé d'avis |
| « un document de plus ne coûte rien » | chaque document est une promesse de mise à jour ; celui qu'on ne tient pas finit par mentir |

## Ce que ce skill ne fait pas

Il n'écrit que dans le dépôt du projet. Le travail sur le dépôt suit le §3 de
`../system/VAULT-CONTRACT.md`.
