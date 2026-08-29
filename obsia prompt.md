je veux créer un système d'orchestration agentic natif linux, complétement modifiable à
travers le chat avec l'agent "assistant" : l'interface complète est modifiable, l'ajout
de fonctionnalités passe par des patches. Le système permet des chats avec un agent
spécifique mais aussi avec des équipes d'agents. Il repose en grande partie sur
l'application Obsidian pour la mémoire et la création d'agents.

## 1- STRUCTURE DE LA MÉMOIRE (dans le coffre obsia_vault/mémoire/)

```
mémoire/
└── <nom-agent>/              ← dossier au NOM de l'agent (jamais "agent 1")
    ├── sommaire.md           ← index de l'agent (généré)
    └── <nom-projet>/         ← dossier au NOM du projet (jamais "projets 1")
        ├── sommaire.md       ← index du projet (généré)
        └── AAAA-MM-JJ-titre.md
```

- Les fichiers `sommaire.md` énumèrent les sous-dossiers et les notes présentes
  avec eux dans le dossier parent, avec un court résumé.
- Ils sont **générés** par `obsia_vault/scripts/regenerate_sommaire.py`, jamais
  édités à la main (ni par un agent).
- Tout est tagué et lié par des rétroliens.

## 2- STRUCTURE DES AGENTS (obsia_vault/IA/agents/)

- **assistant.md** — l'agent de base de l'app : modifie l'UI (React), ajoute des
  fonctionnalités (backend Rust/Tauri), crée des skills. Seul agent autorisé sur
  le framework `build/` (patch Git revu + `cargo check`/`clippy`/`test`).
- Chaque fichier agent contient son system prompt + la liste des skills/MCP qu'il
  peut utiliser, dans son frontmatter YAML.
- Grâce aux rétroliens, le LLM mémorise son system prompt et va chercher
  SEULEMENT les skills/MCP dont il a réellement besoin, au moment où il en a besoin.

## 3- STRUCTURE DES SKILLS (obsia_vault/IA/skills/)

Les skills gèrent le RESTE du coffre. Un skill = une compétence réutilisable
("comment l'agent doit travailler"), ce n'est jamais un agent.

- **core** : `obsidian-manager` (gestion du coffre, lecture seule),
  `createur-de-skill` (création de skills).
- **outil** : `bureautique`, `conteneurs-docker`, `cron`, `diagnostic-linux`,
  `mermaid`, `pdf`, `proxmox`, `remediation-linux`, `sauvegardes`, `traefik`.

## 4- OBSIDIAN-MANAGER EST UN SKILL (pas un agent)

Piège historique : `obsidian-manager` a longtemps été confondu avec un agent
« bibliothécaire » qui n'a jamais existé en tant que fichier.

- `obsidian-manager` est un **SKILL** : il gère le coffre Obsidian (recherche,
  rétroliens, résumés, index) en **lecture seule**.
- L'agent qui l'utilise est **`assistant`** (déclaré dans son frontmatter).
- Il maintient les `sommaire.md` via `scripts/regenerate_sommaire.py` (jamais à
  la main). Toute formulation suggérant qu'un skill est un agent est une erreur
  à corriger, pas une convention à suivre (cf. `VAULT-CONTRACT.md` §1).

## 5- L'INTERFACE UTILISATEUR (Tauri/Rust, multi-fournisseur)

- Épurée : choisir un LLM. Un bouton "fournisseur" + menu déroulant.
- Trois zones redimensionnables : chat, contrôle (réflexions/écritures des
  agents), gestionnaire de fichier (le coffre). Les zones contrôle et
  gestionnaire se réduisent.
- L'UI n'est qu'un terminal humain sur le vrai système d'orchestration (le coffre).

## 6- FRONTIÈRE ABSOLUE (à toujours respecter)

- `obsia_vault/` = **LE COFFRE VIVANT** : mémoire, agents, skills, MCP, scripts,
  git. C'est le système d'orchestration réel.
- `build/` = **LE FRAMEWORK** : UI React + backend Rust/Tauri. Modifiable par
  l'agent `assistant` uniquement, via patch revu.
- Écriture dans le coffre : **lecture seule** sauf `brouillon/` — les
  modifications passent par des patchs Git revus (cf. `VAULT-CONTRACT.md`).
