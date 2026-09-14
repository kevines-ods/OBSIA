# Portabilité entre harness — l'exigence fondatrice

## Statut
🟢 Établie — énoncée par l'utilisateur le 2026-09-05, en ouverture de séance.

---

## La règle

> « OBSIA doit me permettre de changer de harness quand je veux sans aucune
> casse de mes discussions, de mes workflows et de mes tâches planifiées. »

Ce n'est pas une préférence de confort : c'est le critère qui tranche les
décisions de conception. Devant un choix, la question à poser est **« qu'est-ce
qui survit si le harness change demain ? »**

## Ce que ça implique, concrètement

| Ce qui doit survivre | Où ça vit | État |
| --- | --- | --- |
| les workflows | `IA/skills/` | acquis dès l'origine |
| les tâches planifiées | `IA/tâches/` | acquis le 2026-09-05 |
| ce qui a été appris | `mémoire/` | acquis — substitut assumé des conversations |
| la conversation brute | nulle part | **hors périmètre, arbitré par l'utilisateur** |

Sur ce dernier point, l'utilisateur a tranché après avoir parcouru sa mémoire :
les notes structurées se relisent mieux qu'une transcription. Ne pas rouvrir le
sujet sans qu'il le demande.

## Le test à appliquer avant d'écrire quoi que ce soit

Trois questions, dans cet ordre :

1. **Est-ce que ça vit dans le dépôt ?** Ce qu'un agent installe hors du dépôt
   doit au minimum y être *déclaré* — voir [[un-etat-non-declare-est-perdu]].
2. **Est-ce que ça nomme un harness ?** Si oui, c'est une erreur : le coffre
   décrit *quoi* faire, le harness fournit *avec quoi* (§3 du contrat). Une
   commande propre à un outil vit dans une configuration hors dépôt.
3. **Est-ce que le nouveau harness saura que ça existe ?** Un fichier que rien
   n'annonce en contexte n'est jamais ouvert. D'où les index générés du §11.

## Piège rencontré

Rendre une chose portable ne suffit pas : il faut aussi empêcher qu'elle soit
**faite deux fois**. Un harness doté de son propre planificateur crée sa tâche
de son côté ; sans invariant, on se retrouve avec deux déclenchements et aucune
erreur pour le signaler. D'où la règle « une tâche = au plus une instance
vivante », au §12 du contrat.

La portabilité crée des doublons potentiels partout où deux outils savent faire
la même chose. Y penser à chaque fois qu'un harness offre nativement ce que le
coffre décrit.
