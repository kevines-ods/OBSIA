---
schema: 1
kind: skill
name: investigation-de-bug
description: Investiguer un bogue en quatre phases validées — localiser et reproduire, trois hypothèses classées et falsifiables, instrumenter pour trancher, corriger au minimum — sans jamais proposer de correctif avant la phase 4. À charger dès que ça plante, qu'un message d'erreur tombe, qu'un résultat est faux, ou que ce qui marchait hier ne marche plus. Exige le symptôme ET l'attendu avant de démarrer.
type: outil
read_only: false
---

# Skill — Investigation de bug

> **Adaptation.** Reprend `/investigue` de `naiersaidane/claude-mastery`
> (MIT), traduit et aligné sur les conventions du coffre.

Changer trois choses au hasard en espérant que ça passe fait parfois
disparaître le symptôme. La cause, elle, reste — et revient sous une autre
forme, plus tard, ailleurs.

## Avant de commencer

Deux éléments sont nécessaires. Si l'un manque, le demander et attendre :

- **le symptôme** — le message d'erreur, la valeur obtenue, le comportement
  constaté ;
- **l'attendu** — ce qui aurait dû se passer.

Sans l'attendu, on ne cherche pas un bug : on lit du code au hasard.

Si le symptôme s'observe dans un navigateur, `test-navigateur` fournit les
observations de la phase 1 — console, DOM rendu, requête réelle — au lieu de
les supposer.

## Les quatre phases

Chacune se termine par un arrêt et une validation explicite. Aucun correctif
avant la phase 4, même évident, même « pendant qu'on y est ».

### Phase 1 — Localiser et reproduire

Explorer le code et désigner les deux ou trois zones les plus susceptibles
d'héberger la cause, une phrase de justification chacune. Puis décrire en
trois lignes le scénario minimal qui rejoue le bug à coup sûr.

Si la reproduction n'est pas fiable, le dire franchement et proposer un plan
pour y arriver — un bug non reproductible ne se corrige pas, il se maquille.

### Phase 2 — Trois hypothèses classées

Trois hypothèses sur la **cause**, pas sur le symptôme, de la plus probable à
la moins probable. Chacune tient en une phrase et s'accompagne d'une
prédiction falsifiable :

> « Si cette hypothèse est vraie, on observera *telle chose précise* ; si on
> observe l'inverse, elle est éliminée. »

Une hypothèse qu'aucune observation ne peut réfuter n'est pas une hypothèse.

### Phase 3 — Instrumenter pour trancher

Ajouter des traces ciblées pour tester l'hypothèse la plus probable. Les
préfixer d'une étiquette unique — `[DEBUG-a4f2]`, quatre caractères tirés au
hasard — pour pouvoir toutes les retirer d'un coup ensuite. Dire précisément
ce qu'il faut observer.

**Règle des trois échecs :** si les trois hypothèses tombent, s'arrêter. Ce
n'est plus un bug local, c'est une question de conception — on change d'angle
et on remonte au plan, pas au débogueur.

### Phase 4 — Correctif minimal

Une fois l'hypothèse confirmée : la modification la plus courte qui traite la
cause. Aucun refactor opportuniste, aucune optimisation de passage — ils
brouillent le diff et la revue ne distingue plus le correctif du reste.

Retirer les traces de la phase 3. Le message de commit explique la **cause**,
pas le symptôme.

Le correctif ne tient que verrouillé par un test : `tests-dabord` — un test
qui reproduit le bogue, qui échoue avant la correction, et qui reste dans la
suite. Corriger sans lui, c'est signer pour corriger une seconde fois.

## Après

Un bug dont la cause était un piège d'intégration, un défaut de conception ou
une surprise d'une bibliothèque donne une leçon réutilisable : la consigner
dans `mémoire/batisseur/expériences/`. Un bug de frappe, non.
