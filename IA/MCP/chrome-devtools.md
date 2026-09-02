---
name: chrome-devtools
description: Navigation, capture et automatisation web via Chrome DevTools.
type: tool
transport: stdio
permission: elevated
---

# MCP — Chrome DevTools

Serveur MCP officiel :
[ChromeDevTools/chrome-devtools-mcp](https://github.com/ChromeDevTools/chrome-devtools-mcp),
paquet npm `chrome-devtools-mcp`. Lancement via `npx`, aucune installation
préalable requise.

Gabarit de config prêt à copier : `IA/MCP/mcp.example.json`.

## Outils exposés (26 outils, 6 catégories)

- **Navigation** — `navigate_page`, ouverture/fermeture d'onglets, historique.
- **Debugging** — `take_screenshot`, `list_console_messages`, inspection DOM.
- **Réseau** — capture des requêtes/réponses.
- **Automatisation d'entrée** — clic, saisie, défilement.
- **Performance** — profilage, traces.
- **Émulation** — device/throttling.

Liste complète et à jour : `docs/tool-reference.md` du dépôt officiel.

## Permissions

- **Élevées** : accès à la navigation web et au réseau, exécution dans un
  vrai navigateur.
- Lancer avec `--headless=true --isolated=true` par défaut ; ne désactiver
  l'isolation que pour un besoin explicite et temporaire.

## Sécurité

- Ne naviguer que vers des URLs autorisées (listes blanches optionnelles).
- Le profil lancé par `--isolated=true` est jetable — ne jamais le pointer
  vers un profil Chrome personnel contenant des sessions authentifiées.
- Loguer chaque navigation dans `.audit/`.
