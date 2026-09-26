# CLAUDE.md — OBSIA

Ce dépôt est le coffre OBSIA : agents, skills, tâches planifiées et mémoire y
vivent comme fichiers Markdown. Applique le contrat et l'index ci-dessous à chaque
demande, en plus de ton comportement habituel de Claude Code.

@IA/system/VAULT-CONTRACT.md

@IA/system/agents-index.md

@IA/system/skills-index.md

@IA/system/taches-index.md

@IA/system/modules-index.md

Pour un harness autre que Claude Code (aider, goose, opencode…), régénérer le
prompt système complet avec `python3 scripts/generer_prompt.py`.

Sur un clone neuf, `python3 scripts/installer.py --sonder` dit ce que la machine
porte et quels modules cela suggère ; `--appliquer` écrit le profil. Sans profil,
tout le catalogue est actif (§13).
