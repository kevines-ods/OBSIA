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

## Infrastructure

Déduite des skills du coffre, **non confirmée** par l'utilisateur à ce jour :
un hôte **Proxmox** portant au moins une **VM Debian**, laquelle fait tourner
des conteneurs **Docker** derrière **Traefik**, avec des sauvegardes à
vérifier.

À confirmer ou corriger lors d'une prochaine session — et à ne jamais préciser
davantage ici : adresses IP, noms d'hôtes internes et identifiants n'entrent
pas dans le coffre (`VAULT-CONTRACT.md` §4).

---

## Ce qui n'entre jamais dans cette note

Adresse de courriel, mots de passe, jetons, clés, adresses IP privées, noms
d'hôtes internes. Le dépôt est public.
