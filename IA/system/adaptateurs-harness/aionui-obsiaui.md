# AionUi / ObsiaUi (interface)

**Statut : gabarit v1 — à valider sur machine réelle.**

L'interface (AionUi, ObsiaUi) pilote des agents CLI et peut exposer un plugin
local REST + MCP. Deux branchements :

1. **Côté agent** : chaque agent CLI qu'elle pilote suit sa propre fiche
   (`claude-code.md`, `opencode.md`, `deepseek-harness.md`…) — le coffre ne
   change pas.
2. **Côté interface** : déclarer le bloc MCP `coffre-parent` (commun.md) dans
   le serveur local REST/MCP de l'interface, pointant sur la racine du coffre,
   pour que l'interface et ses agents atteignent `SAVOIRS/`, `EN-VRAC/`, etc.

Rappel §3 : OBSIA ne nomme aucune interface dans ses règles ; cette fiche est
un gabarit d'intégration de l'interface vers le coffre.
