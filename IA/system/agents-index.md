# agents-index.md — Index des agents

| Agent | Rôle | Skills | MCP | Lecture seule |
|---|---|---|---|---|
| [assistant](../agents/assistant.md) | Agent de base du coffre OBSIA — orchestre la mémoire, crée des skills, et prépare les patches soumis à revue. | createur-de-skill, cloture-de-session, obsidian-manager, recherche, mermaid, cron, pdf, bureautique, diagnostic-linux, remediation-linux, conteneurs-docker, traefik, proxmox, sauvegardes, traitement-des-notes, cartographie-du-coffre | git-hub, chrome-devtools, obsidian, coffre-parent, searxng | non |
| [batisseur](../agents/batisseur.md) | Agent de construction d'applications, de sites web et d'outils — n'écrit aucune ligne de code avant d'avoir franchi six portes, dans cet ordre et avec validation explicite à chacune : inventaire-de-lexistant, interrogation-du-besoin, cadrage-produit, choix-de-la-stack, systeme-de-design, plan-de-livraison ; puis amorcage-du-projet et plancher-qualite une fois, construction-dune-tranche avec tests-dabord pour chaque tranche verticale, verification-aux-sources avant tout code propre à une bibliothèque, test-navigateur pour montrer qu'une interface marche, livraison-git pour livrer, mise-en-ligne pour publier, et investigation-de-bug devant tout symptôme. | inventaire-de-lexistant, interrogation-du-besoin, cadrage-produit, choix-de-la-stack, systeme-de-design, plan-de-livraison, amorcage-du-projet, plancher-qualite, construction-dune-tranche, tests-dabord, verification-aux-sources, test-navigateur, investigation-de-bug, livraison-git, mise-en-ligne, sauvegardes, conteneurs-docker, traefik, diagnostic-linux, createur-de-skill, obsidian-manager, recherche, mermaid, cloture-de-session | git-hub, chrome-devtools, coffre-parent, searxng | non |
| [contradicteur](../agents/contradicteur.md) | Agent de relecture en lecture seule absolue — cherche ce qui cloche dans un diff sur cinq axes (justesse, lisibilité, architecture, sécurité, performance) et cross-examine une décision non triviale avant qu'elle tienne. Ne corrige jamais : il constate, nomme le scénario d'échec, et rend la main. Un relecteur qui peut réparer cesse de relever. | revue-de-code, relecture-adverse, obsidian-manager, recherche | — | oui |

> Règle (cf. `VAULT-CONTRACT.md` §6) : un agent = un fichier dans `IA/agents/`,
> nommé au `name` du frontmatter. Un skill n'est jamais un agent.

> Fichier **généré** par `scripts/regenerate_index.py` depuis les frontmatters,
> qui font foi. Ne pas éditer à la main (cf. `VAULT-CONTRACT.md` §11).
