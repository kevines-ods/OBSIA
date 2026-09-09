---
schema: 1
kind: skill
name: interrogation-du-besoin
description: Interroger l'utilisateur jusqu'à une compréhension partagée — une seule question par message, en descendant l'arbre de décision, chaque question accompagnée d'une recommandation justifiée et de ce que coûte l'autre choix. À charger après l'inventaire et avant tout document de cadrage, dès qu'un projet est encore une intention. Ne produit aucun fichier : la sortie est un accord énoncé et confirmé.
type: outil
read_only: true
---

# Skill — Interrogation du besoin

> **Adaptation.** Reprend `/interroge` de `naiersaidane/claude-mastery` (MIT),
> traduit dans les conventions du coffre et complété par les règles d'arrêt.

L'erreur classique n'est pas de mal répondre, c'est de commencer à répondre
trop tôt. Ce skill n'a qu'une fonction : retarder la construction jusqu'à ce
que l'utilisateur et l'agent décrivent le même projet.

## Les quatre règles

1. **Une seule question par message.** Attendre la réponse. Trois questions
   empilées reçoivent une réponse à la dernière et un silence sur les deux
   autres.
2. **Chaque question porte une recommandation.** « A ou B ? » fait travailler
   l'utilisateur à la place de l'agent. « Je ferais A, parce que *raison* ;
   B coûterait *coût*. Tu en penses quoi ? » lui donne prise.
3. **Chercher avant de demander.** Si la réponse est dans le code, dans le
   coffre ou dans l'inventaire qui vient d'être fait, la trouver. Redemander
   ce qui a déjà été dit use la patience et la confiance.
4. **Descendre, ne pas balayer.** Chaque réponse ouvre la question suivante.
   Une liste de questions préparée à l'avance ignore ce qu'on vient
   d'apprendre.

## L'ordre de descente

```
le problème vécu   →  qui s'en sert, dans quel contexte
                   →  ce qui doit exister pour que ce soit utile
                   →  ce qu'on refuse explicitement
                   →  à quoi on saura que c'est fini
```

Les questions transverses — cas limites, états vides, erreurs — se posent
quand elles surgissent, pas dans une passe dédiée à la fin.

## Quand s'arrêter

Reformuler le projet en cinq lignes, sans hésiter et sans « je suppose ».
Si l'utilisateur ne corrige rien, la porte 2 est franchie. S'il corrige,
la correction est la question suivante.

Compter les questions : **en dessous de huit, on n'a pas creusé**. Au delà de
la vingtaine sans convergence, le projet est trop gros — le dire, et proposer
d'en cadrer une partie.

## Ce qu'on ne demande pas ici

- Une technologie, un langage, un hébergeur : c'est `choix-de-la-stack`.
- Une couleur, une police : c'est `systeme-de-design`.
- Un découpage en étapes : c'est `plan-de-livraison`.

Poser ces questions maintenant fait choisir la solution avant le problème —
exactement ce que le protocole cherche à empêcher.

## Piège

La question fermée déguisée : *« Tu veux bien qu'on parte sur une petite
application web ? »* n'est pas une question, c'est une décision qu'on fait
signer. Si l'agent connaît déjà la réponse qu'il veut, il ne pose pas de
question — il propose et argumente.
