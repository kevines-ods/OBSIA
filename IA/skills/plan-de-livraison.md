---
schema: 1
kind: skill
name: plan-de-livraison
description: Découper le cadrage en phases indépendamment livrables par tranches verticales — chacune traversant toutes les couches de bout en bout, démontrable seule, avec ses critères d'acceptation et ses dépendances — puis écrire `docs/PLAN.md`. À charger en dernière porte avant de construire, jamais sur un cadrage non validé. Aucun nom de fichier ni de fonction n'entre dans le plan.
module: construction
type: outil
read_only: false
---

# Skill — Plan de livraison

> **Adaptation.** Reprend `/planifie` de `naiersaidane/claude-mastery` (MIT),
> traduit et aligné sur les conventions du coffre. Les blocs `Interfaces` et
> `Focus de revue` sont repris de `obra/superpowers` (MIT),
> `skills/writing-plans`.

Un projet découpé en couches — « d'abord la base, puis l'API, puis
l'interface » — n'a rien de fini avant la toute fin, et découvre ses erreurs
au moment où elles coûtent le plus cher. Un projet découpé en **tranches
verticales** livre quelque chose de vérifiable dès la première.

En **voie rapide** du `batisseur` — un petit outil —, il n'y a rien à découper :
une fiche courte remplace `docs/PLAN.md`, et ce skill n'est pas chargé.

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
  Ce qu'une tranche **consomme** et ce qu'elle **produit** se décrit donc par sa
  **forme** — les champs d'un objet, ce qu'une route reçoit et ce qu'elle rend,
  l'unité d'un montant — jamais par le symbole qui l'implémentera.
- Chaque tranche nomme son **focus de revue** : les trois à cinq classes
  d'entrée d'échec qu'elle doit traiter et qu'aucun critère ne couvre. Toujours
  les mêmes, et c'est pour ça qu'elles s'oublient — l'entrée **vide**, l'entrée
  **extrême** (très grande, très longue, un seul élément), la **mauvaise entrée**
  (refus, erreur, coupure), le **même geste deux fois** (double envoi, rejeu),
  et **l'ordre** (les étapes interverties, ou en parallèle). Une classe retenue
  devient un critère, ou un point de revue écrit ; sinon elle n'existe pour
  personne.
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

### Interfaces
- **Consomme** : ce que la tranche précédente doit avoir livré, en clair.
- **Produit** : ce que les tranches suivantes peuvent tenir pour acquis.

### Focus de revue
- La classe d'entrée d'échec, et comment on la provoque.

### Bloquée par
Aucune — démarrable immédiatement.
```

Les deux derniers blocs sont ce qui empêche la dérive entre tranches.
**`Interfaces`** : sans lui, deux tranches nomment différemment la même idée —
et la divergence ne se voit qu'au moment où les deux morceaux refusent de
s'emboîter. Écrit, il se réfute à la relecture du plan, pour le prix d'une
ligne ; une tranche qui produit autre chose que ce que la suivante consomme est
une erreur de **plan**, à corriger avant de construire. **`Focus de revue`** ne
remplace pas les critères : il nomme ce qu'un critère heureux ne démontre pas,
et il se relit au moment de la revue de tranche (`construction-dune-tranche`
§6), pas au moment du découpage.

## Après l'écriture

Les critères d'acceptation d'une tranche disent si on a construit **la bonne
chose** ; ils ne disent pas si c'est **assez bon**. Cette seconde question est
la même pour toutes les tranches, et se décide une fois — dans le
`CONSTRAINTS.md` de `plancher-qualite`. Une tranche est finie quand les deux
sont satisfaites.

On construit **une tranche à la fois**, et on ne commence pas la suivante
avant que les critères d'acceptation de la précédente passent. Une tranche
finie se livre par `livraison-git` ; on ne les empile pas pour livrer en bloc.
