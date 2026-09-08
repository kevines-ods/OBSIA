# DeepSeek Harness (DSH)

**Statut : gabarit v1 — formats à confirmer avec ta version (l'écosystème DSH
évolue vite).**

Harness « tout est plugin », compatible MCP et skills.

1. Depuis la racine du dépôt OBSIA, générer le contexte :
   `python3 scripts/generer_prompt.py -o prompt-systeme.md`.
2. Déclarer le bloc MCP `coffre-parent` (commun.md) dans la configuration MCP
   du harness (l'emplacement exact dépend de la version — menu/plugin MCP).
3. Charger `prompt-systeme.md` comme base de la session (via patch/profile ou
   instruction de démarrage, selon la version).
4. Vérifier l'accès au coffre : demander la liste de `../SAVOIRS/`.

> À compléter avec la configuration réelle (format d'un plugin MCP DSH) quand
> tu y auras accès.
