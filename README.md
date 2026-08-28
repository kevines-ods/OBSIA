# 🧠 OBSI — Obsidian Orchestrated System Intelligence

Monorepo du projet **OBSI** : un **système d'orchestration agentic** natif Linux
(Tauri/Rust, multi-fournisseur), dont la **mémoire** et la **création d'agents**
reposent entièrement sur un **coffre Obsidian** (Markdown + rétroliens).

> **On ne construit pas une "app" : on construit un SYSTÈME D'ORCHESTRATION.**
> L'UI (`build/`) n'est qu'un **terminal humain** sur le vrai système (le coffre).

## Structure du monorepo

```
Obsia/                          ← racine git unique
├── obsi_vault/                 ← 🟢 LE COFFRE VIVANT (cœur)
│   ├── IA/agents/              │   définition des agents (system prompt + skills/MCP)
│   ├── IA/skills/              │   compétences réutilisables
│   ├── IA/MCP/                 │   outils structurés
│   ├── IA/system/              │   contrat, index, fournisseurs LLM
│   ├── mémoire/                │   mémoire par agent → projets → entrées datées
│   ├── scripts/                │   (regenerate_sommaire.py — rétroliens)
│   ├── README.md  RUNTIME.md   │   porte d'entrée humaine + agent
│   └── .gitignore              │   secrets (obsi_vault propre)
└── build/                      ← 🔧 LE FRAMEWORK (terminal humain)
    ├── src/                    │   React + Vite (3 zones + sélecteur fournisseur)
    └── src-tauri/              │   Rust/Tauri (orchestrateur multi-fournisseur)
```

| Dossier | Rôle |
|---|---|
| `obsi_vault/` | **Cœur** — mémoire, agents, skills, MCP. Le système d'orchestration réel. |
| `build/` | **Framework** — l'application Tauri/Rust (UI). Terminal humain. |

## Démarrage (à faire UNE seule fois)

Si le monorepo n'est pas encore restructuré, exécute le script de mise en place :

```bash
bash setup.sh
```

Il :
1. Supprime le `.git` imbriqué de `obsi_vault/` (→ `Obsia/` devient la seule racine git)
2. Crée le dossier `build/`
3. Configure le remote push vers `https://github.com/kevines-ods/obsi.git`
4. Fait le premier commit baseline

## Flux de travail

- **Coffre (`obsi_vault/`)** : lecture seule pour l'agent, écritures via **patches Git** (revue humaine).
- **Framework (`build/`)** : code Tauri/Rust, patch Git + revue humaine.
- **Rule d'or** : le coffre est le SEUL endroit où "vivent" les agents. L'UI n'est qu'un terminal.

## Documentation

- **Coffre** : `obsi_vault/README.md` (conventions, démarrage, sécurité)
- **Runtime complet** : `obsi_vault/RUNTIME.md` (à ouvrir en premier pour tout reconstruire)
- **Contrat d'exploitation** : `obsi_vault/VAULT.md`
- **GitHub** : `https://github.com/kevines-ods/obsi`

---

*Monorepo : racine git unique `Obsia/` = coffre + framework.*
