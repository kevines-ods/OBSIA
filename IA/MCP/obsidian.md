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

`normal` : le serveur ne sort pas de la machine — il parle à Obsidian sur
`127.0.0.1`. C'est tout ce que ce niveau dit, et il gradue la **prudence avant
l'appel**, rien d'autre.

Deux choses qu'il ne dispense pas :

- **Consigner l'usage.** Tout appel de MCP laisse une ligne dans le log de
  session (§9), quel que soit son `permission`. Ce serveur crée et modifie des
  notes du coffre parent, qui n'a pas d'historique Git : la trace du §9 et le
  preview du §7.4 sont tout ce qui reste pour savoir ce qui s'est passé.
- **Respecter les zones.** Écrire *par* Obsidian ne change rien aux droits :
  zones du §7.3 pour le coffre parent, §2 pour le dépôt. Le serveur, lui,
  accepterait n'importe quelle écriture.

## Sécurité

- La clé API ne va **jamais** dans le coffre : variable d'environnement
  (`OBSIDIAN_API_KEY`), cf. `IA/MCP/mcp.example.json`.
- Le plugin Local REST API n'écoute que sur `127.0.0.1` par défaut : ne pas
  l'exposer sur le réseau.
- Les écritures restent soumises au contrat : lecture seule selon
  `read_only`, zones autorisées, preview consigné (§7.4), usage consigné (§9).
- `mcp-obsidian` est un serveur tiers : c'est lui qui porte la clé API et qui
  atteint le coffre. Le choisir revient à lui accorder cet accès.
