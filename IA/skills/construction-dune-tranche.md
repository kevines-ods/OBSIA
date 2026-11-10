---
schema: 1
kind: skill
name: construction-dune-tranche
description: Construire une tranche verticale du plan et une seule — relire les documents et le journal de la tranche, écrire de quoi vérifier ses critères d'acceptation avant de coder, traverser toutes les couches, refuser d'élargir le périmètre en cours de route, montrer que ça marche, faire relire le diff — conformité, puis qualité — avant de livrer. À charger à chaque tranche de `docs/PLAN.md`, jamais pour en mener deux de front. S'arrête après trois tentatives infructueuses au lieu de s'acharner.
module: construction
type: outil
read_only: false
---

# Skill — Construction d'une tranche

C'est ici que les outils dérivent. Pas au cadrage — au moment où, en
construisant une chose, on en construit trois. Chacune est bonne, l'ensemble
n'est pas ce qui était prévu, et personne ne sait dire quand ça a dérapé.

Une tranche, une branche, une pull request. Rien d'autre entre les deux.

> **Adaptation.** Le journal de tranche et la revue en deux verdicts sont repris
> de `obra/superpowers` (MIT), `skills/subagent-driven-development` ; la table
> des preuves, de `skills/verification-before-completion`.

## 1. Relire, ne pas se souvenir

`docs/PLAN.md` pour la tranche et ses critères, `docs/STACK.md` pour ce qui a
été tranché, `docs/DESIGN.md` s'il y a de l'interface. Trois minutes de
lecture évitent une tranche construite sur une décision qu'on croyait prise.

Énoncer à voix haute, avant de commencer : *« Cette tranche livre X. Elle est
finie quand Y et Z passent. »* Si l'énoncé est flou, la tranche est mal
découpée : retourner au plan.

### Le journal de la tranche

Ouvrir dans `docs/PLAN.md`, sous la phase, une ligne par pas **au moment où le
pas se termine** :

```
- 2026-11-02 · pas 2 · la route lit le fichier · a1b2c3..d4e5f6 · revue propre
```

La date, ce qui est fait, les commits, le verdict. Une tranche dépasse rarement
une séance : le journal est ce qui reste quand le contexte a été compacté, ou
qu'on reprend huit jours plus tard. **Le relire avant le plan**, et ne repartir
que de la dernière ligne — sans quoi on refait un pas déjà fait, ou on relit un
diff déjà relu.

## 2. Écrire de quoi vérifier — avant de construire

Un test, un script, ou à défaut une procédure manuelle en trois lignes dans la
description de la tranche. Sans elle, « c'est fini » est une opinion, et
personne ne peut la contredire.

Écrite après coup, la vérification épouse ce qui a été construit au lieu de
vérifier ce qui était demandé.

**Comment l'écrire : `tests-dabord`** — le test rouge avant le code, et la
règle qui va avec : on le voit échouer pour la bonne raison avant d'écrire la
moindre ligne.

## 3. Construire de bout en bout, le plus risqué d'abord

La tranche traverse toutes les couches. Commencer par celle dont on est le
moins sûr : c'est là qu'on veut découvrir le problème, tant qu'il ne reste
rien à jeter.

Dès qu'on écrit du code **propre à une bibliothèque** — une route, un appel
d'API, un motif de cadriciel : charger `verification-aux-sources`. La
documentation officielle avant la mémoire du modèle, qui produit du code
plausible et périmé sans le signaler.

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

| L'annonce | Ce qu'elle exige | Ce qui ne suffit pas |
| --- | --- | --- |
| « les critères passent » | la commande de vérification, et sa sortie entière | un vert d'il y a une heure, un test vert sur une autre branche |
| « c'est corrigé » | la reproduction qui échouait, rejouée | la confiance dans le diff |
| « tout est vert » | le garde `plancher-qualite` en 0, **après** la dernière retouche | la sortie d'avant la dernière retouche |
| « je n'ai touché qu'à ça » | le diff complet, relu | la phrase elle-même |

**Une preuve a une date.** La commande tourne dans le message qui annonce, pas
dans un souvenir — et quand la sortie est longue, la tronquer en disant où se
trouve le reste, pas la résumer.

Pour une interface : `test-navigateur`. Il ouvre la page, lit le DOM rendu et
la console, et produit la capture. Une interface décrite n'est pas une
interface vue.

## 6. Faire relire la tranche, avant de la livrer

Deux verdicts, dans cet ordre — le second ne se pose pas si le premier échoue :

| Le verdict | La question | Ce qui le rend négatif |
| --- | --- | --- |
| **Conformité** | le diff fait-il ce que disent les critères, et rien de plus ? | un critère absent, ou une ligne que les critères ne demandent pas |
| **Qualité** | est-ce au niveau du `plancher-qualite` ? | le garde refuse, ou le diff est illisible sans son auteur |

Celui qui a construit ne s'audite pas : sur une tranche fine, le plancher est une
**auto-revue sur liste**, diff entier relu ligne à ligne, critère par critère.
Quand le module `revue` est installé, `revue-de-code` le fait dans une
conversation neuve — elle ne connaît pas l'intention, donc elle juge ce qui est
écrit.

**Deux tours de correction, puis on remonte.** Un troisième tour qui trouve
encore quelque chose de sérieux ne dit pas que le code est mauvais : il dit que
la tranche est trop grosse ou mal découpée. Retour au plan, pas de rapiéçage.

Les trois phrases qui sautent cette étape :

- « la PR servira de revue » — le relecteur humain arrive une fois la dépense
  faite, et il relit mal ce qu'on lui présente comme fini ;
- « je me relirai quand tout sera vert » — à ce moment-là, on ne se souvient
  plus du pourquoi, et on relit ce qu'on voulait faire, pas ce qu'on a écrit ;
- « c'est un petit diff » — le risque ne suit pas le nombre de lignes.

## 7. Cocher, puis livrer

Cocher les critères d'acceptation dans `docs/PLAN.md`, committer ce
changement avec la tranche. Si la tranche change l'installation, la
configuration ou une décision, charger `documentation-du-projet` : le README
ou l'ADR se met à jour **dans la même PR**, pas à la séance suivante. Puis
charger `livraison-git`.

Avant de livrer, le garde de `plancher-qualite` doit sortir en 0 : il refuse
les cinq gestes par lesquels une tranche passe au vert sans être meilleure. Ne pas commencer la
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

Un service **déjà en ligne** qui casse n'est pas une tranche : `conteneurs-docker`
ou `traefik`, selon la couche.

**En fin de séance** — pas seulement en fin de tranche : `cloture-de-session`.
