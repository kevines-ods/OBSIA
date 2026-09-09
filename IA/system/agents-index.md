# agents-index.md — Index des agents

| Agent | Rôle | Skills | MCP | Lecture seule |
|---|---|---|---|---|
| [assistant](../agents/assistant.md) | Agent de base du coffre OBSIA — orchestre la mémoire, crée des skills, et prépare les patches soumis à revue. | createur-de-skill, cloture-de-session, obsidian-manager, mermaid, cron, pdf, bureautique, diagnostic-linux, remediation-linux, conteneurs-docker, traefik, proxmox, sauvegardes, traitement-des-notes, cartographie-du-coffre | git-hub, chrome-devtools, obsidian, coffre-parent | non |
| [batisseur](../agents/batisseur.md) | Agent de construction d'applications, de sites web et d'outils — n'écrit aucune ligne de code avant d'avoir franchi six portes, dans cet ordre et avec validation explicite à chacune : inventaire-de-lexistant, interrogation-du-besoin, cadrage-produit, choix-de-la-stack, systeme-de-design, plan-de-livraison ; puis construit une tranche verticale à la fois, charge investigation-de-bug devant tout symptôme, livraison-git pour livrer, et va jusqu'à la mise en ligne derrière Traefik. | inventaire-de-lexistant, interrogation-du-besoin, cadrage-produit, choix-de-la-stack, systeme-de-design, plan-de-livraison, investigation-de-bug, livraison-git, conteneurs-docker, traefik, diagnostic-linux, createur-de-skill, obsidian-manager, mermaid, cloture-de-session | git-hub, chrome-devtools, coffre-parent | non |

> Règle (cf. `VAULT-CONTRACT.md` §6) : un agent = un fichier dans `IA/agents/`,
> nommé au `name` du frontmatter. Un skill n'est jamais un agent.

> Fichier **généré** par `scripts/regenerate_index.py` depuis les frontmatters,
> qui font foi. Ne pas éditer à la main (cf. `VAULT-CONTRACT.md` §11).
