---
schema: 1
kind: skill
name: tests-dabord
description: Écrire le test avant le code — le voir échouer pour la bonne raison, écrire le minimum qui le fait passer, puis nettoyer sans toucher au test. À charger avant d'implémenter une logique, de corriger un bogue ou de changer un comportement, et pour choisir quoi tester quand tout tester est hors de portée. Un test écrit après le code teste ce que le code fait, pas ce qu'il devait faire.
type: outil
read_only: false
---

# Skill — Les tests d'abord

> **Adaptation.** Reprend `test-driven-development` de
> `addyosmani/agent-skills` (MIT), condensé et traduit.

`construction-dune-tranche` demande d'écrire de quoi vérifier **avant** de
construire. Ce skill dit comment.

La raison tient en une phrase : un test écrit après le code se calque sur ce
que le code fait. Il passe toujours — y compris quand le code est faux — parce
qu'il a été écrit en le regardant.

## Le cycle — rouge, vert, propre

```
ROUGE ──────────→ VERT ──────────→ PROPRE
écrire le test    le minimum qui    nettoyer le code,
et le VOIR         le fait passer    jamais le test
échouer
```

### Rouge — voir l'échec, et pour la bonne raison

Un test qui n'a jamais échoué ne prouve rien : il peut passer parce qu'il ne
teste rien. **Le lancer, lire le message d'échec**, et vérifier qu'il échoue
pour la raison attendue — pas sur une faute de frappe, un import manquant ou
une fonction absente.

C'est l'étape qu'on saute, et c'est celle qui porte toute la valeur du cycle.

### Vert — le minimum

Le plus petit code qui fait passer le test. Pas l'implémentation générale
qu'on a déjà en tête : celle-là viendra quand un second test l'exigera. Écrire
plus que nécessaire, c'est écrire du code qu'aucun test ne décrit.

### Propre — sans toucher au test

Renommer, extraire, simplifier, **le test inchangé**. Si le nettoyage oblige à
modifier le test, ce n'est plus un nettoyage : c'est un changement de
comportement, et il repart au rouge.

## Devant un bogue

L'ordre ne change pas, et il est plus important encore :

1. Un test qui **reproduit** le bogue, et qui échoue.
2. La correction.
3. Le test passe — et il reste dans la suite.

Ce test est la garantie que le bogue ne revient pas. Corriger sans lui, c'est
signer pour le corriger une seconde fois.

`investigation-de-bug` s'occupe de **trouver** la cause ; ce skill s'occupe de
la **verrouiller**. Les deux se suivent : la phase 4 de l'investigation est le
« vert » de ce cycle.

## Quoi tester quand on ne peut pas tout tester

Tout tester n'est pas l'objectif, et une couverture de 100 % ne dit rien de la
qualité des tests. Par ordre de rendement :

| Priorité | Quoi | Pourquoi |
| --- | --- | --- |
| 1 | les règles métier — calculs, décisions, validations | c'est là que le faux coûte cher, et c'est invisible à l'œil |
| 2 | les cas limites : zéro, vide, négatif, un seul élément, dépassement | c'est là que les bogues vivent |
| 3 | les chemins d'erreur | le chemin heureux, on le teste à la main sans y penser |
| 4 | ce qu'un bogue a déjà cassé | un bogue revenu est un test manquant |

Ce qui ne mérite pas de test unitaire : un accesseur trivial, une constante,
du code que la bibliothèque tierce garantit déjà.

## Ce qu'un bon test a

- **Un nom qui dit le comportement attendu**, pas la fonction appelée :
  `repartit_le_reste_sur_les_premieres_parts`, pas `test_repartir`.
- **Une seule raison d'échouer.** Trois assertions sans lien = trois tests.
- **Aucune dépendance à l'ordre d'exécution** ni à un test précédent.
- **Un échec lisible** : le message doit dire ce qui était attendu et ce qui
  est arrivé, sans ouvrir le code.
- **Du concret plutôt que du calcul** : `assert somme == 3`, pas
  `assert somme == 1 + 2` — qui rejouerait l'erreur du code.

## Rationalisations

| Ce qu'on se dit | La réalité |
| --- | --- |
| « j'écrirai les tests après » | non. Et écrits après, ils testent l'implémentation, pas le comportement |
| « c'est trop simple pour être testé » | le code simple se complique. Le test documente ce qui était attendu |
| « je l'ai testé à la main » | un essai manuel ne survit pas à la séance. Demain, un changement le casse sans bruit |
| « les tests me ralentissent » | ils ralentissent maintenant et accélèrent chaque fois qu'on retouche le code |
| « ce n'est qu'un prototype » | les prototypes deviennent la production, avec leur dette de tests |
| « je relance la suite pour être sûr » | après une exécution propre, la relancer sans avoir rien changé n'apporte rien |

## Contraintes

La commande qui lance la suite est celle du projet, écrite dans son README par
`amorcage-du-projet` — la lire, ne pas l'inventer. Un test n'est jamais ignoré
ni supprimé pour passer au vert : `plancher-qualite` le refuse, et son garde le
voit dans le diff.
