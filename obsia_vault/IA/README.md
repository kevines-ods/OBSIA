# /IA/ — Définition des agents, skills et outils

Toutes les définitions d'agents, de compétences (skills) et d'outils structurés
(MCP) vivent ici. C'est la "configuration déclarative" du système.

```
IA/
├── README.md
├── system/              ← contrat + index + fournisseurs (lecture seule)
│   ├── VAULT-CONTRACT.md
│   ├── agents-index.md
│   ├── skills-index.md
│   └── providers.md
├── agents/              ← un fichier .md = un agent
│   └── assistant.md
├── skills/              ← un fichier .md = une compétence
│   ├── bureautique.md
│   ├── conteneurs-docker.md
│   ├── createur-de-skill.md
│   ├── cron.md
│   ├── diagnostic-linux.md
│   ├── mermaid.md
│   ├── obsidian-manager.md
│   ├── pdf.md
│   ├── proxmox.md
│   ├── remediation-linux.md
│   ├── sauvegardes.md
│   └── traefik.md
└── MCP/                 ← un fichier .md = un outil structuré
    ├── chrome-devtools.md
    └── git-hub.md
```

**Format d'un agent** (frontmatter + body) :
```markdown
---
schema: 1
kind: agent
name: assistant
description: Agent de base du coffre OBSIA — orchestre la mémoire, crée des skills, et prépare les patches soumis à revue.
skills:
  - createur-de-skill      ← une compétence par ligne (tirets YAML)
  - obsidian-manager
mcp:
  - git-hub                ← outils structurés activés
read_only: false           ← true = lecture seule absolue
---
# Assistant
...
```

**Format d'un skill** : frontmatter (`name`, `description`) + règles d'usage +
exemples.

**Format d'un MCP** : description, outils exposés, permissions, sécurité.
