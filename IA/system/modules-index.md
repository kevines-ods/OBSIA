# modules-index.md — Index des modules installables

| Module | Essentiel | Retenu ici | Déclarations | Sondes | Requiert | Description |
|---|---|---|---|---|---|---|
| [noyau](modules/noyau.md) | oui | oui | 7 | — | — | Le socle — contrat, méthode, mémoire, recherche, création de skills, clôture de session. Toujours installé. |
| [coffre-obsidian](modules/coffre-obsidian.md) | non | oui | 5 | `parent:.obsidian`, `parent:-SAVOIRS`, `parent:-EN-VRAC` | noyau | Travailler dans un coffre Obsidian parent — remplir et classer les notes brutes, cartographier les connaissances, tenir le registre des tags. |
| [construction](modules/construction.md) | non | oui | 15 | `commande:git` | noyau | Construire des applications, sites et outils — l'agent batisseur et ses portes, de l'inventaire de l'existant à la mise en ligne. |
| [conteneurs](modules/conteneurs.md) | non | oui | 2 | `commande:docker`, `commande:podman` | noyau, linux-poste | Conteneurs et reverse proxy — état, journaux, volumes, réseaux, compose, labels de routage, certificats TLS. |
| [controle-des-sauvegardes](modules/controle-des-sauvegardes.md) | non | oui | 1 | — | noyau | Vérifier que les sauvegardes existent, sont récentes, respectent la règle 3-2-1, et se restaurent réellement. |
| [deploiement](modules/deploiement.md) | non | oui | 1 | — | noyau, construction, conteneurs, controle-des-sauvegardes | Empaqueter une application et la mettre en ligne derrière un reverse proxy — image, compose, labels de routage, secrets hors dépôt, retour arrière écrit d'avance. |
| [diagrammes](modules/diagrammes.md) | non | oui | 1 | `commande:docker`, `commande:podman`, `commande:npx`, `commande:mmdc` | noyau | Rendu de diagrammes Mermaid en SVG — flux, séquences, états, classes, entités. |
| [documents](modules/documents.md) | non | oui | 2 | — | noyau | Documents bureautiques et PDF — lire, produire, convertir, extraire, remplir des formulaires, appliquer l'OCR. |
| [linux-poste](modules/linux-poste.md) | non | oui | 2 | `commande:systemctl`, `commande:journalctl` | noyau | Diagnostiquer et corriger un système Linux — services, journaux, charge, disque, mémoire, réseau. |
| [modeles-locaux](modules/modeles-locaux.md) | non | oui | 2 | `commande:llama-server`, `commande:llama-swap`, `commande:ollama` | noyau | Délégation de tâches simples à un modèle local servi par une API compatible OpenAI, sans lui transmettre le contexte du coffre. |
| [navigateur](modules/navigateur.md) | non | oui | 2 | `commande:chromium`, `commande:google-chrome`, `commande:google-chrome-stable` | noyau, construction | Vérifier une interface dans un vrai navigateur — DOM rendu, erreurs de console, requêtes réseau, capture d'écran, arbre d'accessibilité. |
| [planification](modules/planification.md) | non | oui | 3 | `commande:systemctl` | noyau | Tâches planifiées — registre `IA/tâches/`, instanciation en timers, réconciliation après un changement de machine ou de harness. |
| [recherche-web](modules/recherche-web.md) | non | oui | 1 | — | noyau | Recherche web par un méta-moteur auto-hébergé — SearXNG, sans compte ni traçage. |
| [revue](modules/revue.md) | non | oui | 3 | — | noyau | Relecture adverse en lecture seule absolue — chercher ce qui cloche dans un diff, et cross-examiner une décision avant qu'elle tienne. |
| [virtualisation](modules/virtualisation.md) | non | oui | 1 | `commande:pvesh`, `fichier:/etc/pve` | noyau, linux-poste | Inspecter un hôte Proxmox — VM, conteneurs LXC, stockage, cluster, répartition des ressources. Lecture seule non négociable. |

> `Retenu ici` se lit dans `obsia.local.yml`, non versionné. Sans profil,
> tout est retenu — c'est l'état du dépôt de distribution, et celui sous
> lequel la CI vérifie le coffre (cf. `VAULT-CONTRACT.md` §13).

> Retenir un module écarté, ou en écarter un autre :
> `python3 scripts/installer.py --appliquer`. L'installeur sonde la
> machine, propose, et n'écrit qu'avec `--appliquer`.

> Fichier **généré** par `scripts/regenerate_index.py` depuis les
> frontmatters, qui font foi. Ne pas éditer à la main (§11).
