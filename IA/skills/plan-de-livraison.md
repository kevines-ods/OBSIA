---
schema: 1
kind: skill
name: plan-de-livraison
description: Découper le cadrage en phases indépendamment livrables par tranches verticales — chacune traversant toutes les couches de bout en bout, démontrable seule, avec ses critères d'acceptation et ses dépendances — puis écrire `docs/PLAN.md`. À charger en dernière porte avant de construire, jamais sur un cadrage non validé. Aucun nom de fichier ni de fonction n'entre dans le plan.
type: outil
read_only: false
---

# Skill — Plan de livraison

> **Adaptation.** Reprend `/planifie` de `naiersaidane/claude-mastery` (MIT),
> traduit et aligné sur les conventions du coffre.

Un projet découpé en couches — « d'abord la base, puis l'API, puis
l'interface » — n'a rien de fini avant la toute fin, et découvre ses erreurs
au moment où elles coûtent le plus cher. Un projet découpé en **tranches
verticales** livre quelque chose de vérifiable dès la première.

## Procédure

### 1. Relire le cadrage et la stack

`docs/CADRAGE.md` et `docs/STACK.md`. Si `docs/PLAN.md` existe déjà, le lire :
repérer les user stories non couvertes et les incohérences avec un cadrage
qui a bougé, proposer des phases additionnelles, **ne pas réécrire** ce qui
est déjà validé.

### 2. Fixer les décisions structurantes

Avant de découper, nommer ce qui ne devra plus bouger en cours de route :
forme des URL, forme du schéma de données, noms des objets métier, mode
d'authentification, frontières avec les services tiers. Elles vont en tête du
plan ; chaque phase s'y réfère au lieu de les redécider.

### 3. Découper en tranches verticales

- Chaque tranche traverse **toutes** les couches, sur un chemin étroit mais
  complet.
- Une tranche terminée est **démontrable seule** — sinon ce n'est pas une
  tranche.
- Beaucoup de tranches fines valent mieux que peu de tranches épaisses.
- Aucun nom de fichier ni de fonction : ils changeront, et le plan mentira.
- La première tranche traverse le chemin le plus **risqué**, pas le plus
  facile : c'est là qu'on veut se tromper tôt.

### 4. Faire valider le découpage avant de l'écrire

Présenter la liste numérotée — titre, bloquée par, user stories couvertes —
et poser trois questions : la granularité est-elle juste ? les dépendances
sont-elles bonnes ? faut-il fusionner ou refendre ? Itérer jusqu'à validation.

### 5. Écrire `docs/PLAN.md`

```markdown
# Plan — <nom du projet>

> Cadrage source : docs/CADRAGE.md

## Décisions structurantes
- **URL** : …
- **Schéma** : …
- **Objets métier** : …

---

## Phase 1 — <titre>
**User stories** : US-…

### Ce qu'on livre
Le comportement de bout en bout, pas l'implémentation couche par couche.

### Critères d'acceptation
- [ ] …

### Bloquée par
Aucune — démarrable immédiatement.
```

## Après l'écriture

On construit **une tranche à la fois**, et on ne commence pas la suivante
avant que les critères d'acceptation de la précédente passent. Une tranche
finie se livre par `livraison-git` ; on ne les empile pas pour livrer en bloc.
