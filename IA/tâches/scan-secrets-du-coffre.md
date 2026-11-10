---
schema: 1
kind: tâche
name: scan-secrets-du-coffre
description: Relire tout le coffre à la recherche de valeurs à forme de secret, et signaler — sans corriger, sans supprimer, sans jamais bloquer.
module: planification
mode: agent
quand: "0 8 * * 1"
fuseau: Europe/Paris
exécutant: local
agent: administrateur
actif: true
---

# Tâche — Scan intégral des secrets du coffre

## Intention

Le garde du commit ne voit que ce qu'un commit **ajoute** : une valeur déjà
présente, ou posée sans passer par le crochet, reste en place sans être revue.
Un passage qui relit tout le coffre referme ce trou — en **signalant**.

`exécutant: local` parce qu'elle a besoin du clone et de sa mémoire sous la main.

`mode: agent` parce que le verdict est une phrase : le scan ne sort jamais en
erreur, et un journal de commande ne se lit pas.

## Instruction

Place-toi à la racine du dépôt produit et exécute :

```bash
python3 scripts/garde_secrets.py --tout-le-coffre
```

La première ligne du rapport nomme le coffre relu. Si ce n'est pas le coffre
attendu, arrête-toi là et dis-le : ne relis rien d'autre.

Rapporte en clair, en deux points : le nombre de fichiers relus, puis chaque
signalement avec son fichier, sa ligne et son étiquette.

Ne recopie **aucune** valeur : le scan ne la montre pas, et une réponse ne la
reconstitue pas sous prétexte de l'expliquer (§4).

Ne corrige rien, ne supprime rien, ne modifie aucune note, ne déplace aucun
fichier : c'est un signalement. Une valeur déjà écrite se corrige par une
**rotation** décidée par la personne qui la détient — l'agent propose, la
personne agit.

Si le rapport dit « Rien à signaler », dis-le en une ligne et arrête-toi là.
