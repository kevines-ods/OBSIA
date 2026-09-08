---
schema: 1
kind: mcp
name: obsidian
description: Accéder au coffre ouvert dans Obsidian via son API REST locale — recherche, lecture, création et mise à jour de notes, rétroliens, tags. À charger quand une action porte sur une note du coffre parent, ou quand un rétrolien doit être garanti indexé par Obsidian.
type: tool
transport: stdio
permission: normal
---

# MCP — Obsidian (API REST locale)

Serveur qui relaie vers l'API REST locale du plugin Obsidian **Local REST API**
(Obsidian ouvert sur le coffre, plugin actif, écoute locale par défaut sur
`127.0.0.1:27123`). Écrire *par* Obsidian garantit que la note est indexée :
un rétrolien posé est immédiatement visible dans le graphe.

Gabarit de config prêt à copier : `IA/MCP/mcp.example.json`, entrée `obsidian`.

## Prérequis

- Obsidian ouvert sur le coffre parent, avec le plugin **Local REST API** actif ;
- une clé API du plugin, fournie au harness par variable d'environnement
  (`OBSIDIAN_API_KEY`) — jamais écrite dans le dépôt.

## Ce que le serveur expose (selon le serveur MCP utilisé)

- recherche plein texte et par tags dans le coffre ;
- lecture d'une note (contenu, frontmatter, liens) ;
- création et mise à jour d'une note ;
- lecture des rétroliens d'une note.

La liste exacte des outils dépend du serveur MCP retenu (ex. `mcp-obsidian`) ;
vérifier sa documentation.

## Permissions

- `normal` : le serveur ne touche que le coffre local. Les écritures restent
  régies par le contrat — zones du §7.3 pour le coffre parent, §2 pour le
  dépôt — et se consignent au §9 quand elles touchent le coffre parent.

## Sécurité

- La clé API ne va **jamais** dans le coffre : variable d'environnement
  (`OBSIDIAN_API_KEY`), cf. `IA/MCP/mcp.example.json`.
- Le plugin Local REST API n'écoute que sur `127.0.0.1` par défaut : ne pas
  l'exposer sur le réseau.
- Les écritures restent soumises au contrat : lecture seule selon
  `read_only`, zones autorisées, preview consigné (§7.4).
