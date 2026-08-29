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
│   ├── assistant-de-bureau.md
│   ├── bibliothécaire.md
│   └── développeur.md
├── skills/              ← un fichier .md = une compétence
│   ├── obsidian-manager.md
│   ├── web-research.md
│   ├── officecli.md
│   ├── troubleshooting.md
│   ├── cron.md
│   └── skill-créator.md
└── MCP/                 ← un fichier .md = un outil structuré
    ├── chrome-devtools.md
    └── git-hub.md
```

**Format d'un agent** (frontmatter + body) :
```markdown
---
schema: 1
kind: agent
name: assistant-de-bureau
description: Assiste au quotidien — documents, mail, calendrier, navigation web.
skills: [officecli, cron]      ← skills activées par défaut
mcp: [chrome-devtools]          ← outils structurés activés
read_only: false
---
# Assistant de bureau
...
```

**Format d'un skill** : frontmatter (`name`, `description`) + règles d'usage +
exemples.

**Format d'un MCP** : description, outils exposés, permissions, sécurité.
