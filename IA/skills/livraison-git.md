---
schema: 1
kind: skill
name: livraison-git
description: Livrer une tranche terminée — branche préfixée depuis la branche par défaut à jour, vérifications du projet passées, commit nommant le pourquoi, poussée et pull request soumise à revue humaine. À charger à la fin de chaque tranche verticale, jamais pour empiler plusieurs tranches. Refuse de committer sur la branche par défaut et refuse d'ajouter un fichier de secrets.
type: outil
read_only: false
---

# Skill — Livraison Git

> **Adaptation.** Fusionne `/branche` et `/livre` de
> `naiersaidane/claude-mastery` (MIT) en une seule procédure, alignée sur le
> §3 du contrat : toute modification d'un dépôt passe par un patch revu.

Une tranche finie qu'on ne livre pas n'existe pas. Trois tranches livrées
ensemble ne se revoient plus : la revue devient un survol.

## 1. Une branche, avant de toucher au code

```bash
git checkout main && git pull origin main
git checkout -b feat/<sujet-court>
```

Préfixes : `feat/` pour une fonctionnalité, `fix/` pour une correction. Si la
branche par défaut ne s'appelle pas `main`, utiliser son vrai nom — le lire
plutôt que le supposer.

**Jamais de commit direct sur la branche par défaut** (§3). Si le travail a
commencé dessus par inadvertance, créer la branche maintenant : les
modifications non commitées la suivent.

## 2. Les vérifications du projet, avant de proposer

Lancer ce qu'un contributeur lancerait localement : formatage, analyse
statique, tests. Le §3 l'exige, et une branche qui casse la CI coûte un
aller-retour et de la confiance.

Pour ce coffre-ci, les vérifications sont dans `scripts/verifier_coffre.py` ;
pour un autre dépôt, elles sont dans son fichier de contribution ou sa
configuration d'intégration continue. Les trouver, pas les inventer.

## 3. Commit

```bash
git status --short
git diff
git log --oneline -5        # pour reprendre le style des commits du dépôt
```

Ajouter les fichiers **nommément**, jamais `git add -A` : c'est ainsi qu'un
`.env` ou une clé finit poussé. Un fichier de secrets ne s'ajoute pas, même
temporairement — un secret poussé une fois reste dans l'historique (§4).

Le message dit **pourquoi**, pas quoi : le diff dit déjà quoi.

## 4. Pousser

```bash
git push -u origin HEAD
```

Si le dépôt n'a pas encore de distant — cas d'un projet créé à la porte 3 —
demander à l'utilisateur avant de créer le dépôt en ligne : publier est une
action à effet externe, et le choix public/privé lui appartient.

## 5. Pull request

Titre court. Corps en deux parties : **Ce que ça change** (une à trois puces)
et **Comment le vérifier** (les étapes exactes pour rejouer le comportement).
Renvoyer l'URL à l'utilisateur.

La PR est le moment de la revue humaine exigée par le §3. Ne pas la fusionner
soi-même.

## 6. Consigner

L'appel d'un MCP — la création de la PR en est un — se consigne dans le log de
session (§9), en une ligne : quoi, où, résultat. Sans adresse interne ni
identifiant : le dépôt est public.
