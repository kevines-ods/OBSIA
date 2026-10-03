---
schema: 1
kind: mcp
name: chrome-devtools
description: Navigation, capture et automatisation web via Chrome DevTools.
module: navigateur
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

## Lancement

```bash
npx -y chrome-devtools-mcp@latest --headless --isolated \
  --no-usage-statistics --no-performance-crux
```

- **Chrome ou Chromium.** Le serveur cherche par défaut Google Chrome, canal
  stable. Sur une distribution qui ne fournit que Chromium, lui donner le
  binaire : `--executablePath=/usr/bin/chromium-browser` (nom Fedora ; lire
  `command -v chromium chromium-browser` ailleurs). Sans cette option, le
  serveur démarre mais échoue à la première navigation.
- **Prérequis** : Node.js et `npx` sur la machine qui lance le serveur — le
  premier lancement télécharge le paquet depuis le registre npm.
- **Confidentialité** : `--no-usage-statistics` coupe les statistiques
  d'usage envoyées à Google ; `--no-performance-crux` empêche d'envoyer les
  URL des traces de performance à l'API CrUX. Les deux sont actives par défaut.
- Avec l'option de routage par page (active par défaut), les outils liés à une
  page exigent son `pageId` : `list_pages` le donne.

Vérifié le 2026-09-28 (version 1.10.1, Chromium 154) : 30 outils exposés,
navigation vers une page locale, instantané du DOM et messages de console
relus.

## Permissions

- **Élevées** : accès à la navigation web et au réseau, exécution dans un
  vrai navigateur.
- Lancer avec `--headless=true --isolated=true` par défaut ; ne désactiver
  l'isolation que pour un besoin explicite et temporaire.

## Sécurité

- Ne naviguer que vers des URLs autorisées (listes blanches optionnelles).
- Le profil lancé par `--isolated=true` est jetable — ne jamais le pointer
  vers un profil Chrome personnel contenant des sessions authentifiées.
- Consigner les navigations au carnet — du chantier, ou du jour hors chantier — (`VAULT-CONTRACT.md` §9) —
  il n'y a pas de journal séparé. Y écrire la nature de la navigation, pas une
  URL interne : le dépôt est public.
