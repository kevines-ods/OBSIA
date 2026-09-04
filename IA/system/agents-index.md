# agents-index.md — Index des agents

| Agent | Rôle | Skills | MCP | Lecture seule |
|---|---|---|---|---|
| [assistant](../agents/assistant.md) | Agent de base du coffre OBSIA — orchestre la mémoire, crée des skills, et prépare les patches soumis à revue. | createur-de-skill, cloture-de-session, obsidian-manager, mermaid, cron, pdf, bureautique, diagnostic-linux, remediation-linux, conteneurs-docker, traefik, proxmox, sauvegardes | git-hub, chrome-devtools | non |

> Règle (cf. `VAULT-CONTRACT.md` §6) : un agent = un fichier dans `IA/agents/`,
> nommé au `name` du frontmatter. Un skill n'est jamais un agent.

> Fichier **généré** par `scripts/regenerate_index.py` depuis les frontmatters,
> qui font foi. Ne pas éditer à la main (cf. `VAULT-CONTRACT.md` §11).
