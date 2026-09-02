---
name: git-hub
description: Push/pull, PR, issues et review sur GitHub.
type: tool
transport: http
permission: elevated
---

# MCP — Git Hub

Serveur MCP officiel de GitHub :
[github/github-mcp-server](https://github.com/github/github-mcp-server).
Deux formes existent ; retenir la première sauf besoin précis :

- **Distant (recommandé)** — aucune installation. URL `https://api.githubcopilot.com/mcp/`,
  authentifié par en-tête `Authorization: Bearer <PAT>` (ou OAuth selon le
  harness).
- **Local (Docker)** — `docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN
  ghcr.io/github/github-mcp-server`, pour un usage hors-ligne ou auto-hébergé.

Gabarit de config prêt à copier : `IA/MCP/mcp.example.json`.

## Outils exposés (extrait)

Le serveur couvre dépôts, issues, PR, actions et sécurité du code. Les plus
utilisés côté coffre :

- `get_file_contents` / `create_or_update_file` — lire/écrire un fichier
  distant.
- `create_pull_request`, `get_pull_request`, `list_pull_requests` — cycle de
  PR.
- `list_issues`, `create_issue` — suivi.
- `get_commit`, `list_commits` — historique.

Liste complète et à jour : voir le dépôt officiel ci-dessus (elle évolue).

## Permissions

- **Élevées** : écriture sur un dépôt distant.
- Utiliser un PAT **fine-grained**, scopé au(x) dépôt(s) concerné(s) — jamais
  un token classic à portée globale.
- Utiliser un dépôt **spécial** pour les patches, pas le coffre personnel.

## Sécurité

- Le PAT ne va **jamais** dans le coffre : variable d'environnement ou secret
  du harness uniquement — voir `mcp.example.json`, qui référence
  `${GITHUB_TOKEN}` plutôt qu'une valeur en clair.
- Les patches de l'agent sont toujours en PR → **revue humaine obligatoire**.
