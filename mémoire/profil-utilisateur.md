# Profil utilisateur

Faits durables sur la personne qui utilise ce coffre. Cette note évite de
redemander à chaque session ce qui a déjà été dit. Elle n'est pas datée : elle
est **mise à jour sur place** quand un fait change, pas dupliquée.

## Statut
🟢 Vivante — à compléter au fil des sessions.

---

## Poste de travail

- Distribution : **CachyOS** (base Arch). Les paquets s'installent avec
  `pacman`, l'AUR avec `paru`.
- Environnement de bureau : **KDE Plasma**.

Conséquence pratique : les commandes d'installation proposées visent Arch, pas
Debian ni Fedora. Un skill qui documente `apt` s'adresse à une machine
distante, pas au poste.

## Rapport au code

Bricole avec l'IA et les systèmes Linux ; **connaissances en codage modestes**,
de son propre aveu.

Ce que ça implique concrètement :

- expliquer ce qu'une commande fait avant de la proposer, pas seulement la
  donner ;
- nommer le risque quand il y en a un, plutôt que de supposer qu'il est
  évident ;
- ne pas conclure d'une question de suivi qu'une erreur a été commise.

## Valeurs

Orientation **open source et logiciel libre**, assumée et structurante : elle
gouverne le choix de la licence du coffre et le refus des outils propriétaires.
Détail dans [[licences-et-logiciel-libre]].

## Coffre Obsidian

Le dépôt `OBSIA/` est cloné **à la racine** du coffre Obsidian personnel, non
versionné. Sa structure de premier niveau est fixe (modifiable par
l'utilisateur seul) :

- `OBSIA/` — le dépôt, seul versionné : agents, skills, tâches, mémoire ;
- `_maintenance/` — journaux, astuces de débogage, previews consignés,
  registre des notes traitées (`notes_remplies`) ;
- `PROJETS/` — projets en cours ou à venir ;
- `DOCUMENTS/` — revues, articles web, transcriptions YouTube ;
- `PERSONNELS/` — contexte personnel, configuration matérielle/logicielle,
  préférences, CV ;
- `SAVOIRS/` — connaissances accumulées, un fichier = un concept ;
- `EN-VRAC/` — zone de dépôt : notes brutes que l'agent remplit, tagge,
  rétrolie, puis classe dans l'un des autres dossiers.

Les règles complètes (lecture, zones d'écriture, preview consigné dans
`_maintenance/`) sont au §7 de `IA/system/VAULT-CONTRACT.md`, qui fait foi —
elles ne sont pas recopiées ici.

## Infrastructure

**Confirmée par l'utilisateur le 2026-09-03, précisée le 2026-09-12.** Un
hôte **Proxmox** portant au moins deux VM, volontairement séparées :

- une **VM Debian**, qui fait tourner les conteneurs **Docker** personnels et
  divers, derrière **Traefik**, avec des sauvegardes à vérifier ;
- une **VM Fedora**, réservée à **tout ce qui est IA** — l'utilisateur préfère
  isoler cet usage plutôt que de le mélanger aux conteneurs personnels de la
  VM Debian.

Le poste de travail (CachyOS) a **Docker installé** : c'est là que se font les
premiers tests d'un service avant d'envisager son hébergement sur la VM
Fedora.

Conséquences pratiques :

- le poste est sous Arch (`pacman`/`paru`), la VM Debian sous `apt`, la VM
  Fedora sous `dnf` — ne pas confondre le gestionnaire de paquets selon la
  cible ;
- un service lié à l'IA vise la **VM Fedora** pour son hébergement final, pas
  la VM Debian : les deux ne se substituent pas l'une à l'autre ;
- une erreur HTTP sur un service hébergé se diagnostique par la couche —
  `traefik` d'abord si le service répond en direct, `conteneurs-docker` si le
  conteneur est mort, `proxmox` si le symptôme dépasse une machine ;
- `proxmox` est en lecture seule et le reste : une commande malheureuse à ce
  niveau affecte toutes les VM à la fois.

Ne jamais préciser davantage ici : adresses IP, noms d'hôtes internes et
identifiants n'entrent pas dans le coffre (`VAULT-CONTRACT.md` §4).

---

## Ce qui n'entre jamais dans cette note

Adresse de courriel, mots de passe, jetons, clés, adresses IP privées, noms
d'hôtes internes. Le dépôt est public.
