# /IA/ — Définition des agents, skills, outils et tâches

Toutes les définitions d'agents, de compétences (skills), d'outils
structurés (MCP) et de tâches planifiées vivent ici. C'est la partie
déclarative du coffre.

Les règles de format sont au §5 de `system/VAULT-CONTRACT.md`, qui fait foi
et n'est pas reformulé ici.

## Agents — `IA/agents/`

- **assistant** — Agent de base du coffre OBSIA — orchestre la mémoire, crée des skills, et prépare les patches soumis à revue.
- **batisseur** — Agent de construction d'applications, de sites web et d'outils — n'écrit aucune ligne de code avant d'avoir franchi six portes, dans cet ordre et avec validation explicite à chacune : inventaire-de-lexistant, interrogation-du-besoin, cadrage-produit, choix-de-la-stack, systeme-de-design, plan-de-livraison ; puis construit une tranche verticale à la fois, charge investigation-de-bug devant tout symptôme, livraison-git pour livrer, et va jusqu'à la mise en ligne derrière Traefik.

## Skills — `IA/skills/`

- **bureautique** (`outil`) — Créer, lire et modifier des documents Word, Excel, PowerPoint et OpenDocument, et convertir entre formats. À charger dès qu'un fichier .docx, .xlsx, .pptx, .odt, .ods ou .odp est en entrée ou en sortie. Pas pour les PDF — voir `pdf`.
- **cadrage-produit** (`outil`) — Figer le besoin dans un document versionné en huit sections (Problème, Utilisateur cible, Solution, User stories numérotées, Critères de succès, Hors périmètre, Décisions produit, Notes) et créer le dépôt du projet s'il n'existe pas encore. À charger une fois l'accord obtenu par interrogation-du-besoin, jamais avant. Produit `docs/CADRAGE.md` dans le dépôt du projet, validé section par section.
- **cartographie-du-coffre** (`outil`) — Dresser la carte des connaissances du coffre parent — concepts de SAVOIRS, notes orphelines, doublons, tags hors vocabulaire, liens manquants. À charger pour faire le point sur la santé du coffre ou avant une réorganisation. Lit et propose, n'écrit rien.
- **choix-de-la-stack** (`outil`) — Choisir langage, cadriciel, base de données et hébergement en confrontant deux ou trois candidats à des critères écrits d'avance — licence libre, coût d'entretien, adéquation à l'infrastructure existante, capacité réelle à la reprendre en main — et consigner la décision dans `docs/STACK.md`. À charger après le cadrage et avant tout code ou design. Ne se rejoue pas à chaque tranche : la décision est prise une fois.
- **cloture-de-session** (`core`) — Clore une session de travail — écrire la note de projet, en distiller ce qui est durable vers profil/préférences/expériences, proposer le log du §9. À charger quand une session se termine ou qu'un lot de travail est livré. Pas pour écrire une note isolée en cours de route.
- **conteneurs-docker** (`outil`) — Diagnostiquer et gérer des conteneurs Docker — état, journaux, volumes, réseaux, compose. À charger devant un conteneur qui redémarre, sature ou refuse de démarrer, et avant toute modification d'un compose.yml. Si le symptôme est une erreur HTTP renvoyée par le reverse proxy, commencer par `traefik`.
- **createur-de-skill** (`core`) — Concevoir un nouveau skill OBSIA ou en réviser un — périmètre, dosage, découpage, frontmatter. À charger avant d'écrire ou de modifier un fichier de `IA/skills/`, y compris pour n'en changer que la description. Ne sert pas à exécuter un skill existant.
- **cron** (`outil`) — Gérer les tâches planifiées — registre `IA/tâches/`, instanciation outillée chez l'exécutant, réconciliation après un changement de harness ou de machine. À charger dès qu'une action doit se répéter à heure fixe, et toujours avant d'en créer une. Ne couvre ni le cron système ni les tâches root.
- **diagnostic-linux** (`core`) — Constater l'état d'un système Linux — services en échec, journaux, charge, disque, mémoire, réseau. À charger en premier devant tout symptôme machine, avant d'envisager la moindre correction. N'exécute que des commandes de lecture : pour agir, charger `remediation-linux`.
- **interrogation-du-besoin** (`outil`) — Interroger l'utilisateur jusqu'à une compréhension partagée — une seule question par message, en descendant l'arbre de décision, chaque question accompagnée d'une recommandation justifiée et de ce que coûte l'autre choix. À charger après l'inventaire et avant tout document de cadrage, dès qu'un projet est encore une intention. Ne produit aucun fichier : la sortie est un accord énoncé et confirmé.
- **inventaire-de-lexistant** (`outil`) — Inventorier ce qui existe déjà avant de construire — tentatives précédentes, dépôts, outils installés, notes du coffre — et en sortir trois listes : ce qu'on reprend, ce qu'on ne refait pas, ce qui est non négociable. À charger en toute première étape d'un projet de construction, avant même de poser une question sur le besoin. Lit et rapporte : n'écrit ni ne modifie rien.
- **investigation-de-bug** (`outil`) — Investiguer un symptôme en quatre phases validées — localiser et reproduire, trois hypothèses classées et falsifiables, instrumenter pour trancher, corriger au minimum — sans jamais proposer de correctif avant la phase 4. À charger dès qu'un comportement observé diffère du comportement attendu, y compris en pleine construction. Exige le symptôme ET l'attendu avant de démarrer.
- **livraison-git** (`outil`) — Livrer une tranche terminée — branche préfixée depuis la branche par défaut à jour, vérifications du projet passées, commit nommant le pourquoi, poussée et pull request soumise à revue humaine. À charger à la fin de chaque tranche verticale, jamais pour empiler plusieurs tranches. Refuse de committer sur la branche par défaut et refuse d'ajouter un fichier de secrets.
- **mermaid** (`outil`) — Générer des diagrammes Mermaid en SVG — flux, séquences, états, classes, entités. À charger quand une structure, un enchaînement ou une machine à états se lit mieux en image qu'en texte. Inutile pour une simple liste ou un tableau, que le Markdown rend déjà.
- **obsidian-manager** (`core`) — Interroger le dépôt OBSIA et le coffre parent `Mon coffre/` — recherche plein texte, rétroliens, résumé d'une note, état des index. À charger dès qu'il faut retrouver quelque chose, ou vérifier ce qui existe déjà avant d'écrire une note nouvelle. Lit et rapporte seulement : n'écrit, ne déplace ni ne supprime rien.
- **pdf** (`outil`) — Extraire texte et tableaux, fusionner, découper, pivoter, chiffrer, remplir des formulaires, appliquer l'OCR sur des PDF. À charger dès qu'un fichier .pdf est en entrée ou en sortie. Pas pour Word, Excel ou PowerPoint — voir `bureautique`.
- **plan-de-livraison** (`outil`) — Découper le cadrage en phases indépendamment livrables par tranches verticales — chacune traversant toutes les couches de bout en bout, démontrable seule, avec ses critères d'acceptation et ses dépendances — puis écrire `docs/PLAN.md`. À charger en dernière porte avant de construire, jamais sur un cadrage non validé. Aucun nom de fichier ni de fonction n'entre dans le plan.
- **proxmox** (`outil`) — Inspecter un hôte Proxmox — VM, conteneurs LXC, stockage, cluster, répartition des ressources. À charger quand le symptôme dépasse une seule machine, ou pour identifier une VM par son VMID avant d'en parler. Lecture seule non négociable : aucune commande `qm`, `pct` ou `pvesm` modifiant l'état.
- **remediation-linux** (`outil`) — Corriger un système Linux — redémarrer un service, libérer de l'espace, restaurer une configuration, revenir en arrière. À charger seulement après un constat écrit par `diagnostic-linux`, jamais seul. Chaque action est annoncée, puis vérifiée avant la suivante.
- **sauvegardes** (`core`) — Vérifier que les sauvegardes existent, sont récentes, respectent la règle 3-2-1, et se restaurent réellement. À charger avant toute action risquant de détruire des données, et lors d'un contrôle périodique. Ne restaure jamais par-dessus l'original et ne supprime aucune sauvegarde.
- **systeme-de-design** (`outil`) — Proposer un système visuel cohérent et assumé — direction, typographie, palette, densité, mouvement — avec ce qui est conventionnel et ce qui est pris comme risque, puis produire `docs/DESIGN.md` et un aperçu HTML que l'utilisateur ouvre et regarde. À charger après le choix de la stack, pour tout projet ayant une interface visible. Inutile pour un outil sans interface.
- **traefik** (`outil`) — Diagnostiquer Traefik — 404 et 502, labels, réseaux partagés, certificats TLS, service injoignable derrière le proxy. À charger dès qu'un service répond en direct mais pas par son nom de domaine. Si le conteneur lui-même est arrêté ou tué, commencer par `conteneurs-docker`.
- **traitement-des-notes** (`outil`) — Traiter les notes brutes du coffre parent — remplir, tagger (vocabulaire contrôlé), rétrolier, prévisualiser dans _maintenance/, classer depuis EN-VRAC et mettre à jour notes_remplies.md. À charger pour toute note brute ou toute note déposée dans SAVOIRS à compléter.

## MCP — `IA/MCP/`

- **chrome-devtools** (`stdio`, permission `elevated`) — Navigation, capture et automatisation web via Chrome DevTools.
- **coffre-parent** (`stdio`, permission `elevated`) — Lire et écrire dans les fichiers du coffre parent `Mon coffre/` via un serveur MCP « fichiers » monté sur sa racine. À charger quand le harness n'ouvre pas déjà la racine du coffre comme dossier de travail. Le serveur peut écrire partout ; les zones autorisées restent celles du §7.3.
- **git-hub** (`http`, permission `elevated`) — Push/pull, PR, issues et review sur GitHub.
- **obsidian** (`stdio`, permission `normal`) — Lire, chercher et modifier les notes du coffre `Mon coffre/` via l'API REST locale du plugin Obsidian. À charger quand une écriture doit être indexée par Obsidian sur-le-champ — un rétrolien visible dans le graphe sans rouvrir l'application. Expose `delete_file`, que le contrat interdit d'appeler.

Gabarit de configuration à compléter côté harness : `MCP/mcp.example.json`.

## Tâches planifiées — `IA/tâches/`

Le registre fait foi ; timers et planificateurs n'en sont que des
instances reconstructibles (§12). Procédure dans le skill `cron`.

- **revue-des-notes-du-coffre** (`0 10 * * 1`, Europe/Paris, mode `agent`, exécutant `local`) — Traiter les notes brutes du coffre parent — remplir et classer celles d'EN-VRAC, compléter celles déposées dans SAVOIRS, et signaler les tags hors vocabulaire contrôlé. À charger via le skill traitement-des-notes.
- **revue-hebdomadaire-du-coffre** (`0 9 * * 1`, Europe/Paris, mode `agent`, exécutant `local`) — Régénérer index et sommaires, vérifier la cohérence du coffre, et réconcilier le registre des tâches avec ce qui tourne réellement.

## `IA/system/`

- `VAULT-CONTRACT.md` — les règles. Fait foi.
- `agents-index.md`, `skills-index.md`, `taches-index.md` — index
  générés (§11).
- `providers.md` — repère pour choisir un modèle. Aucune clé n'y vit.
- `prompt-fondateur.md` — intention d'origine, non normative.
- `session-log/` — une note par session de travail (§9).

Le registre des tâches planifiées vit à côté, dans `IA/tâches/` (§12) ;
`system/taches-index.md` en est l'index généré.

> Fichier **généré** par `scripts/regenerate_index.py` depuis les
> frontmatters, qui font foi. Ne pas éditer à la main (§11).
