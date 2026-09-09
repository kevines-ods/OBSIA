---
schema: 1
kind: mcp
name: obsidian
description: Lire, chercher et modifier les notes du coffre `Mon coffre/` via l'API REST locale du plugin Obsidian. À charger quand une écriture doit être indexée par Obsidian sur-le-champ — un rétrolien visible dans le graphe sans rouvrir l'application. Expose `delete_file`, que le contrat interdit d'appeler.
type: tool
transport: stdio
permission: normal
---

# MCP — Obsidian (API REST locale)

Relaie vers l'API REST locale du plugin Obsidian **Local REST API**. Écrire
*par* Obsidian garantit que la note est indexée : un rétrolien posé est
immédiatement visible dans le graphe, sans attendre qu'Obsidian relise le
fichier.

## Le paquet — il y a deux homonymes, ne pas se tromper

**`mcp-obsidian` sur PyPI** (`uvx mcp-obsidian`) : c'est celui-ci. Son résumé
est explicite — *« MCP server to work with Obsidian via the remote REST
plugin »*.

Il existe un **autre `mcp-obsidian`, sur npm** (`npx -y mcp-obsidian`), qui n'a
rien à voir : il lit un dossier de Markdown, attend un chemin de coffre en
argument, ignore toute clé API et n'expose que `read_notes` et `search_notes` —
donc **aucune écriture**. Lancé avec la configuration ci-dessous, il sort
en `Usage: mcp-obsidian <vault-directory>`, code 1.

Le coffre a porté ce gabarit npm pendant plusieurs jours en croyant décrire le
serveur REST. Vérifié et corrigé le 2026-09-09.

## Prérequis

- **Obsidian ouvert** sur `Mon coffre/`, plugin communautaire
  **Local REST API** activé (`coddingtonbear/obsidian-local-rest-api`) ;
- une **clé API** générée par le plugin, fournie au harness par variable
  d'environnement — jamais écrite dans le dépôt ;
- **`uv`** installé, qui fournit `uvx` (le serveur est en Python, pas en
  Node). Sur CachyOS : `pacman -S uv`.

Trois variables, telles que le serveur les attend :

| Variable | Rôle |
| --- | --- |
| `OBSIDIAN_API_KEY` | la clé du plugin — obligatoire |
| `OBSIDIAN_HOST` | l'hôte, `127.0.0.1` |
| `OBSIDIAN_PORT` | le port ; **27124 par défaut** si absent |

Le plugin écoute en HTTPS sur **27124** et n'ouvre le HTTP (27123) que si on
l'active. Renseigner `OBSIDIAN_PORT` explicitement plutôt que de se fier au
défaut : c'est le réglage qui diffère le plus d'une installation à l'autre.

Gabarit prêt à copier : `IA/MCP/mcp.example.json`, entrée `obsidian`.

## Les outils exposés

| Outil | Ce qu'il fait |
| --- | --- |
| `list_files_in_vault` | liste la racine du coffre |
| `list_files_in_dir` | liste un dossier |
| `get_file_contents` | contenu d'une note |
| `search` | recherche plein texte |
| `patch_content` | insère du contenu relativement à un titre, un bloc ou un champ de frontmatter |
| `append_content` | ajoute à la fin d'une note, existante ou nouvelle |
| `delete_file` | **supprime** un fichier ou un dossier |

`patch_content` et `append_content` sont la raison d'être de ce serveur : ils
écrivent *par* Obsidian, donc l'index suit.

## `delete_file` ne s'appelle pas

Le §2 du contrat interdit toute suppression sans archivage préalable, et le
coffre parent n'a **pas** d'historique Git pour rattraper l'erreur. Ce serveur
expose pourtant la suppression, sans corbeille ni confirmation.

Règle : ne jamais appeler `delete_file`. Si une note doit disparaître, le dire
à l'utilisateur et le laisser faire depuis Obsidian, où la suppression passe
par la corbeille du coffre.

## Permissions

`normal` : le serveur ne sort pas de la machine — il parle au plugin sur
`127.0.0.1`. C'est tout ce que ce niveau dit, et il gradue la **prudence avant
l'appel**, rien d'autre.

Deux choses qu'il ne dispense pas :

- **Consigner l'usage.** Tout appel de MCP laisse une ligne dans le log de
  session (§9), quel que soit son `permission`. Ce serveur modifie des notes du
  coffre parent, qui n'a pas d'historique Git : la trace du §9 et le preview du
  §7.4 sont tout ce qui reste pour savoir ce qui s'est passé.
- **Respecter les zones.** Écrire *par* Obsidian ne change rien aux droits :
  zones du §7.3 pour le coffre parent, §2 pour le dépôt. Le serveur, lui,
  accepterait n'importe quelle écriture — et n'importe quelle suppression.

## Sécurité

- La clé API ne va **jamais** dans le dépôt : variable d'environnement
  uniquement, cf. `IA/MCP/mcp.example.json`.
- Le plugin n'écoute que sur `127.0.0.1` : ne pas l'exposer sur le réseau.
- C'est un serveur **tiers** : le lancer revient à lui confier la clé et
  l'accès en écriture au coffre. Épingler une version connue plutôt que de
  suivre aveuglément la dernière.
