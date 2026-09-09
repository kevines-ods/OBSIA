---
schema: 1
kind: skill
name: construction-dune-tranche
description: Construire une tranche verticale du plan et une seule — relire les documents, écrire de quoi vérifier ses critères d'acceptation avant de coder, traverser toutes les couches, refuser d'élargir le périmètre en cours de route, montrer que ça marche, puis livrer. À charger à chaque tranche de `docs/PLAN.md`, jamais pour en mener deux de front. S'arrête après trois tentatives infructueuses au lieu de s'acharner.
type: outil
read_only: false
---

# Skill — Construction d'une tranche

C'est ici que les outils dérivent. Pas au cadrage — au moment où, en
construisant une chose, on en construit trois. Chacune est bonne, l'ensemble
n'est pas ce qui était prévu, et personne ne sait dire quand ça a dérapé.

Une tranche, une branche, une pull request. Rien d'autre entre les deux.

## 1. Relire, ne pas se souvenir

`docs/PLAN.md` pour la tranche et ses critères, `docs/STACK.md` pour ce qui a
été tranché, `docs/DESIGN.md` s'il y a de l'interface. Trois minutes de
lecture évitent une tranche construite sur une décision qu'on croyait prise.

Énoncer à voix haute, avant de commencer : *« Cette tranche livre X. Elle est
finie quand Y et Z passent. »* Si l'énoncé est flou, la tranche est mal
découpée : retourner au plan.

## 2. Écrire de quoi vérifier — avant de construire

Un test, un script, ou à défaut une procédure manuelle en trois lignes dans la
description de la tranche. Sans elle, « c'est fini » est une opinion, et
personne ne peut la contredire.

Écrite après coup, la vérification épouse ce qui a été construit au lieu de
vérifier ce qui était demandé.

## 3. Construire de bout en bout, le plus risqué d'abord

La tranche traverse toutes les couches. Commencer par celle dont on est le
moins sûr : c'est là qu'on veut découvrir le problème, tant qu'il ne reste
rien à jeter.

## 4. Ne jamais élargir la tranche en cours

**La règle du skill.** Tout ce qu'on découvre en chemin devient une **nouvelle
tranche dans `docs/PLAN.md`** — jamais un ajout à celle-ci.

Trois formes de dérive, à reconnaître au moment où on les commet :

| La phrase qu'on se dit | Ce que c'est vraiment |
| --- | --- |
| « pendant que j'y suis… » | une seconde tranche non planifiée, non validée |
| « je nettoie vite fait ce fichier » | un refactor qui noie le diff et rend la revue impossible |
| « je le rends générique, ça servira » | une abstraction construite sur un seul cas, donc fausse |

Noter la découverte dans le plan prend trente secondes et laisse la décision
à l'utilisateur. C'est tout l'objet du protocole.

## 5. Montrer que ça marche

Avant de dire que c'est fait : exécuter la vérification de l'étape 2, et
**montrer le résultat** — la sortie réelle pour un outil en ligne de commande,
une capture d'écran via le navigateur pour une interface. « Ça devrait
marcher » n'est pas une démonstration, et c'est la phrase qui précède la
plupart des retours en arrière.

## 6. Cocher, puis livrer

Cocher les critères d'acceptation dans `docs/PLAN.md`, committer ce
changement avec la tranche, puis charger `livraison-git`. Ne pas commencer la
tranche suivante avant que celle-ci soit livrée : deux tranches ouvertes en
même temps se contaminent et la revue ne sait plus quoi regarder.

## Quand ça bloque

**Trois tentatives, puis on s'arrête.** Une quatrième tentative sur la même
piste n'est plus du travail, c'est de l'acharnement, et elle laisse du code
qu'on ne saura pas expliquer.

- Le symptôme est un comportement inattendu → `investigation-de-bug`, et ses
  quatre phases.
- Le blocage vient d'un choix technique qui ne tient pas → retour à la porte 4
  et à `choix-de-la-stack`. Contourner une stack qui résiste, c'est construire
  la dette au lieu du produit.
- Le blocage vient du plan → le dire, et redécouper.

Dans les trois cas, on remonte. On ne force pas.
