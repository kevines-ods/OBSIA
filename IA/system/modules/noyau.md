---
schema: 1
kind: module
name: noyau
description: Le socle — contrat, méthode, mémoire, recherche, création de skills, clôture de session. Toujours installé.
essentiel: true
---

## Ce que ce module apporte

Les agents `assistant` et `visionnaire`, et les compétences sans lesquelles le coffre ne fonctionne
pas : décider où chercher, retrouver ce qui existe, écrire en mémoire, créer un
skill, clore une séance.

Aucune question ne porte sur lui : un coffre sans noyau n'est pas un coffre.

## Pourquoi ce découpage

`obsidian-manager` est ici et non dans `coffre-obsidian`, parce qu'il cherche
d'abord dans le dépôt lui-même — index, skills, mémoire. Le coffre parent n'est
qu'une extension de son périmètre, pas sa raison d'être.

`configuration-mcp` est ici aussi : dès qu'un module apporte un MCP, il faut
savoir le brancher. Le placer dans un module optionnel ferait dépendre le
branchement du hasard de l'installation.

`visionnaire` est ici et non dans un module optionnel : `assistant` et
`batisseur` le rappellent à chaque moment clé, et un rappel vers un agent
absent tomberait dans le vide. Il garde la finalité de tout projet, pas
seulement des projets de code.
