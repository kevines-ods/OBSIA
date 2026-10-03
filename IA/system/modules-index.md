# modules-index.md — Index des modules installables

| Module | Essentiel | Déclarations | Sondes | Requiert | Description |
|---|---|---|---|---|---|
| [noyau](modules/noyau.md) | oui | 10 | — | — | Le socle — contrat, méthode, mémoire, recherche, création de skills, clôture de session. Toujours installé. |
| [administration-homelab](modules/administration-homelab.md) | non | 4 | — | noyau, linux-poste, virtualisation, conteneurs, controle-des-sauvegardes | Administrer une infrastructure auto-hébergée — l'agent administrateur, la surveillance et les alertes, Nextcloud AIO et Home Assistant OS. |
| [coffre-obsidian](modules/coffre-obsidian.md) | non | 5 | `parent:.obsidian`, `parent:-SAVOIRS`, `parent:-EN-VRAC` | noyau | Travailler dans un coffre Obsidian parent — remplir et classer les notes brutes, cartographier les connaissances, tenir le registre des tags. |
| [construction](modules/construction.md) | non | 22 | `commande:git` | noyau, controle-des-sauvegardes | Construire des applications, sites et outils, ou faire évoluer un projet existant — l'agent batisseur, ses portes de création et son parcours de reprise, de refactoring et de dette technique. |
| [conteneurs](modules/conteneurs.md) | non | 2 | `commande:docker`, `commande:podman` | noyau, linux-poste | Conteneurs et reverse proxy — état, journaux, volumes, réseaux, compose, labels de routage, certificats TLS. |
| [controle-des-sauvegardes](modules/controle-des-sauvegardes.md) | non | 1 | — | noyau | Vérifier que les sauvegardes existent, sont récentes, respectent la règle 3-2-1, et se restaurent réellement. |
| [deploiement](modules/deploiement.md) | non | 1 | — | noyau, construction, conteneurs, controle-des-sauvegardes | Empaqueter une application et la mettre en ligne derrière un reverse proxy — image, compose, labels de routage, secrets hors dépôt, retour arrière écrit d'avance. |
| [diagrammes](modules/diagrammes.md) | non | 1 | `commande:docker`, `commande:podman`, `commande:npx`, `commande:mmdc` | noyau | Rendu de diagrammes Mermaid en SVG — flux, séquences, états, classes, entités. |
| [documents](modules/documents.md) | non | 2 | — | noyau | Documents bureautiques et PDF — lire, produire, convertir, extraire, remplir des formulaires, appliquer l'OCR. |
| [linux-poste](modules/linux-poste.md) | non | 2 | `commande:systemctl`, `commande:journalctl` | noyau | Diagnostiquer et corriger un système Linux — services, journaux, charge, disque, mémoire, réseau. |
| [messagerie](modules/messagerie.md) | non | 1 | — | noyau | Lire, chercher et envoyer des courriels depuis une boîte Gmail — documents produits joints, envoi toujours confirmé. |
| [modeles-locaux](modules/modeles-locaux.md) | non | 2 | `commande:llama-server`, `commande:llama-swap`, `commande:ollama` | noyau | Délégation de tâches simples à un modèle local servi par une API compatible OpenAI, sans lui transmettre le contexte du coffre. |
| [navigateur](modules/navigateur.md) | non | 2 | `commande:chromium`, `commande:google-chrome`, `commande:google-chrome-stable` | noyau, construction | Vérifier une interface dans un vrai navigateur — DOM rendu, erreurs de console, requêtes réseau, capture d'écran, arbre d'accessibilité. |
| [planification](modules/planification.md) | non | 4 | `commande:systemctl` | noyau | Tâches planifiées — registre `IA/tâches/`, instanciation en timers, réconciliation après un changement de machine ou de harness. |
| [poste-cachyos](modules/poste-cachyos.md) | non | 1 | `distribution:cachyos` | noyau, linux-poste | Optimiser un poste CachyOS — noyau et ordonnanceur, mémoire, btrfs et snapper, réseau, jeu, nettoyage. |
| [recherche-web](modules/recherche-web.md) | non | 1 | — | noyau | Recherche web par un méta-moteur auto-hébergé — SearXNG, sans compte ni traçage. |
| [revue](modules/revue.md) | non | 4 | — | noyau | Relecture adverse en lecture seule absolue — chercher ce qui cloche dans un diff, auditer la sécurité d'un projet entier, et cross-examiner une décision avant qu'elle tienne. |
| [services-nextcloud](modules/services-nextcloud.md) | non | 1 | — | noyau | Agenda, tâches, notes et contacts sur une instance Nextcloud auto-hébergée — consulter, planifier et noter sans dépendre d'un service tiers. |
| [virtualisation](modules/virtualisation.md) | non | 2 | `commande:pvesh`, `fichier:/etc/pve` | noyau, linux-poste | Inspecter un hôte Proxmox en lecture seule — VM, conteneurs LXC, stockage, ressources — puis y agir sous annonce — créer des machines, régler le démarrage, poser des hookscripts. |

> Ce fichier montre le **catalogue complet** : versionné, il ne dépend
> pas de la machine, et ne se réduit jamais au profil. Quels modules
> sont retenus *ici* se lit dans `obsia.local.yml`, s'il existe ; son
> absence vaut catalogue complet (cf. `VAULT-CONTRACT.md` §13 et
> `contrat/contrat-distribution.md`).

> Retenir un module écarté, ou en écarter un autre :
> `python3 scripts/installer.py --appliquer`. L'installeur sonde la
> machine, propose, et n'écrit qu'avec `--appliquer`.

> Fichier **généré** par `scripts/regenerate_index.py` depuis les
> frontmatters, qui font foi. Ne pas éditer à la main (§11).
