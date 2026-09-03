# Schéma — fonctionnement d'OBSIA

Produit par le skill `mermaid` (`IA/skills/mermaid.md`) lors d'un test du
workflow du coffre. Bloc Mermaid brut et non SVG, conformément à la section
« Intégration au coffre » du skill : dans une note du coffre, le bloc reste
lisible, modifiable et versionnable ; le SVG n'est généré que pour un usage
hors coffre.

```mermaid
graph TD
  U["Utilisateur"] --> A["agent : assistant<br/>IA/agents/assistant.md"]
  C["VAULT-CONTRACT.md<br/>règles du coffre"] -.lu en premier.-> A
  A -->|charge seulement<br/>ce qui est nécessaire| S["skills<br/>IA/skills/"]
  A -->|actions structurées| M["MCP<br/>IA/MCP/"]
  A -->|écrit| ME["mémoire/assistant/<br/>écriture directe"]
  A -->|écrit| B["brouillon/<br/>écriture directe"]
  A -->|patch Git revu| P["reste du coffre<br/>IA/system, IA/agents"]
  SC["scripts/*.py"] -->|régénèrent| G["sommaire.md<br/>agents-index.md<br/>skills-index.md"]
```

Rendu SVG vérifié hors coffre avec :

```bash
npx -y @mermaid-js/mermaid-cli -p pptr.json -i obsia.mmd -o obsia.svg
```

où `pptr.json` contient `{"args":["--no-sandbox","--disable-gpu","--disable-dev-shm-usage"]}`.
Sans ce fichier, le Chromium de Puppeteer refuse de démarrer en conteneur.
