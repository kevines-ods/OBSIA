---
schema: 1
kind: skill
name: tests-de-caracterisation
description: Figer ce qu'un vieux code fait aujourd'hui — son comportement actuel, bizarreries comprises — par des caractérisations enregistrées avant de le modifier, pour qu'une régression se voie au lieu de se découvrir en production. À charger avant de toucher un code hérité, peu ou pas couvert, avant un refactoring, une montée de version ou une migration. Pour du code neuf, c'est `tests-dabord`.
module: construction
type: outil
read_only: false
---

# Skill — Tests de caractérisation

`tests-dabord` teste ce que le code **doit** faire. Sur un code existant, on
ne le sait souvent pas — mais on sait ce qu'il **fait**, et c'est ce que les
utilisateurs attendent de lui aujourd'hui. Un test de caractérisation écrit
ce comportement tel quel, pour qu'un changement involontaire casse un test au
lieu de casser un usage.

## Procédure

### 1. Choisir la zone à figer

Uniquement celle qu'on s'apprête à modifier, et ses appelants directs. Figer
tout le projet avant d'y toucher n'est pas de la prudence, c'est un chantier
de plus. Les zones fragiles relevées par `reprise-dun-projet` passent en
premier.

### 2. Observer avant d'affirmer

Écrire le test avec une valeur attendue **volontairement fausse**, le lancer,
et lire ce que le code renvoie vraiment :

```python
def test_calcul_remise_client_fidele():
    assert calcul_remise(panier_exemple, client_fidele) == "???"  # lire l'échec
```

L'échec donne la valeur réelle ; on la recopie. C'est l'inverse de
`tests-dabord`, et c'est voulu : on documente, on ne spécifie pas.

### 3. Couvrir les bords, pas seulement le chemin heureux

Pour chaque fonction figée : une entrée normale, une vide ou nulle, une
limite (zéro, maximum, chaîne très longue), une invalide. C'est aux bords que
les réécritures changent le comportement sans le vouloir.

Quand la sortie est volumineuse (HTML, JSON, rapport), un test d'**instantané**
(*snapshot*) enregistré dans le dépôt vaut mieux que vingt assertions.

### 4. Garder les bizarreries — et les signaler

Un comportement qui ressemble à un bogue se fige **tel quel**, avec un
commentaire :

```python
# CARACTÉRISATION — arrondi à l'inférieur, probablement involontaire.
# Signalé à l'utilisateur le AAAA-MM-JJ ; ne pas corriger dans ce lot.
```

Le corriger en même temps mélange deux changements : si un utilisateur
dépendait de ce comportement, on ne saura plus lequel des deux l'a cassé. La
correction vient après, dans sa propre tranche, avec son propre test.

### 5. Vérifier que les tests mordent

Casser volontairement une ligne du code figé : au moins un test doit passer
au rouge. Sinon il ne protège rien — il faut le resserrer avant de
s'appuyer dessus. Remettre la ligne.

### 6. Commiter les tests seuls

Un commit « tests de caractérisation de <zone> », **sans aucune modification
du code**. C'est la ligne de base contre laquelle tout le reste se compare.

## Rationalisations

| Ce qu'on se dit | La réalité |
| --- | --- |
| « je sais ce que fait cette fonction » | la valeur que tu aurais écrite de tête est fausse une fois sur trois ; l'échec du test te dit la vraie |
| « ce comportement est un bogue, je teste la version corrigée » | tu viens de livrer un changement de comportement sans le savoir ni le dire |
| « un test sur le chemin normal suffit » | la réécriture changera le cas vide ou la limite, et aucun test ne le verra |
| « je commiterai les tests avec le refactoring » | si le refactoring fait passer un test au rouge, tu ne sauras pas si c'est le test ou le code qui a tort |
| « le test passe, donc il protège » | tant qu'il n'a pas échoué une fois sur une vraie cassure, rien ne le prouve |

## Ce que ce skill ne fait pas

Il ne modifie pas le code testé. Le travail sur le dépôt suit le §3 de
`../system/VAULT-CONTRACT.md`.
