# skills-index.md — Index des skills

| Skill | Type | Description — quoi, quand, quand pas | Utilisé par |
|---|---|---|---|
| [bureautique](../skills/bureautique.md) | outil | Créer, lire et modifier des documents Word, Excel, PowerPoint et OpenDocument, et convertir entre formats. À charger dès qu'un fichier .docx, .xlsx, .pptx, .odt, .ods ou .odp est en entrée ou en sortie. Pas pour les PDF — voir `pdf`. | assistant |
| [cloture-de-session](../skills/cloture-de-session.md) | core | Clore une session de travail — écrire la note de projet, en distiller ce qui est durable vers profil/préférences/expériences, proposer le log du §9. À charger quand une session se termine ou qu'un lot de travail est livré. Pas pour écrire une note isolée en cours de route. | assistant |
| [conteneurs-docker](../skills/conteneurs-docker.md) | outil | Diagnostiquer et gérer des conteneurs Docker — état, journaux, volumes, réseaux, compose. À charger devant un conteneur qui redémarre, sature ou refuse de démarrer, et avant toute modification d'un compose.yml. Si le symptôme est une erreur HTTP renvoyée par le reverse proxy, commencer par `traefik`. | assistant |
| [createur-de-skill](../skills/createur-de-skill.md) | core | Concevoir un nouveau skill OBSIA ou en réviser un — périmètre, dosage, découpage, frontmatter. À charger avant d'écrire ou de modifier un fichier de `IA/skills/`, y compris pour n'en changer que la description. Ne sert pas à exécuter un skill existant. | assistant |
| [cron](../skills/cron/cron.md) | outil | Gérer les tâches planifiées — registre `IA/tâches/`, instanciation chez l'exécutant via `scripts/appliquer_taches.py`, réconciliation après un changement de harness ou de machine. À charger dès qu'une action doit se répéter à heure fixe, et toujours avant d'en créer une. Ne couvre ni le cron système ni les tâches root. | assistant |
| [diagnostic-linux](../skills/diagnostic-linux.md) | core | Constater l'état d'un système Linux — services en échec, journaux, charge, disque, mémoire, réseau. À charger en premier devant tout symptôme machine, avant d'envisager la moindre correction. N'exécute que des commandes de lecture : pour agir, charger `remediation-linux`. | assistant |
| [mermaid](../skills/mermaid.md) | outil | Générer des diagrammes Mermaid en SVG — flux, séquences, états, classes, entités. À charger quand une structure, un enchaînement ou une machine à états se lit mieux en image qu'en texte. Inutile pour une simple liste ou un tableau, que le Markdown rend déjà. | assistant |
| [obsidian-manager](../skills/obsidian-manager.md) | core | Interroger le coffre — recherche plein texte, rétroliens, résumé d'une note, état des index. À charger dès qu'il faut retrouver quelque chose dans le coffre, ou vérifier ce qui existe déjà avant d'écrire une note nouvelle. Lit et rapporte seulement : n'écrit, ne déplace ni ne supprime rien. | assistant |
| [pdf](../skills/pdf.md) | outil | Extraire texte et tableaux, fusionner, découper, pivoter, chiffrer, remplir des formulaires, appliquer l'OCR sur des PDF. À charger dès qu'un fichier .pdf est en entrée ou en sortie. Pas pour Word, Excel ou PowerPoint — voir `bureautique`. | assistant |
| [proxmox](../skills/proxmox.md) | outil | Inspecter un hôte Proxmox — VM, conteneurs LXC, stockage, cluster, répartition des ressources. À charger quand le symptôme dépasse une seule machine, ou pour identifier une VM par son VMID avant d'en parler. Lecture seule non négociable : aucune commande `qm`, `pct` ou `pvesm` modifiant l'état. | assistant |
| [remediation-linux](../skills/remediation-linux.md) | outil | Corriger un système Linux — redémarrer un service, libérer de l'espace, restaurer une configuration, revenir en arrière. À charger seulement après un constat écrit par `diagnostic-linux`, jamais seul. Chaque action est annoncée, puis vérifiée avant la suivante. | assistant |
| [sauvegardes](../skills/sauvegardes.md) | core | Vérifier que les sauvegardes existent, sont récentes, respectent la règle 3-2-1, et se restaurent réellement. À charger avant toute action risquant de détruire des données, et lors d'un contrôle périodique. Ne restaure jamais par-dessus l'original et ne supprime aucune sauvegarde. | assistant |
| [traefik](../skills/traefik.md) | outil | Diagnostiquer Traefik — 404 et 502, labels, réseaux partagés, certificats TLS, service injoignable derrière le proxy. À charger dès qu'un service répond en direct mais pas par son nom de domaine. Si le conteneur lui-même est arrêté ou tué, commencer par `conteneurs-docker`. | assistant |

> `core` = indispensable au fonctionnement du coffre ; `outil` = compétence
> ponctuelle. (cf. `VAULT-CONTRACT.md` §5)

> Fichier **généré** par `scripts/regenerate_index.py`. La colonne description
> reproduit mot pour mot le champ `description` du frontmatter, qui fait foi :
> c'est le seul élément toujours présent en contexte, il doit suffire à décider
> d'ouvrir le skill sans le lire. Ne pas éditer à la main (§11).
