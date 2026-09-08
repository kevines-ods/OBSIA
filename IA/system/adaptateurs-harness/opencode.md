# OpenCode

**Statut : gabarit v1 — à valider sur machine réelle.**

Agent CLI configurable (fichier `opencode.json`). Pas de mécanisme
`CLAUDE.md` : on fournit le contexte via le prompt généré.

1. Depuis la racine du dépôt OBSIA, générer le prompt :
   `python3 scripts/generer_prompt.py -o prompt-systeme.md`.
2. Ouvrir le coffre : lancer OpenCode à la racine du coffre (parent d'OBSIA),
   ou déclarer le bloc MCP `coffre-parent` (commun.md) dans `opencode.json`.
3. Fournir `prompt-systeme.md` comme instruction de démarrage, puis vérifier
   l'accès à `../SAVOIRS/`.
