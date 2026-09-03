# agents-index.md — Index des agents

| Agent | Rôle | Skills | MCP | Lecture seule |
|---|---|---|---|---|
| [assistant](../agents/assistant.md) | Agent de base du coffre OBSIA — orchestre la mémoire, crée des skills, et prépare les patches soumis à revue. | createur-de-skill, obsidian-manager, mermaid, cron, pdf, bureautique, diagnostic-linux, remediation-linux, conteneurs-docker, traefik, proxmox, sauvegardes | git-hub | non |

> Règle (cf. `VAULT-CONTRACT.md` §6) : un agent = un fichier dans `IA/agents/`,
> nommé au `name` du frontmatter. Un skill n'est jamais un agent.

> Les colonnes Skills et MCP reproduisent les listes du frontmatter de l'agent,
> qui fait foi.
