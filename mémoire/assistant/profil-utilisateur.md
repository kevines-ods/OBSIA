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

Le dépôt `OBSIA/` est cloné dans un coffre Obsidian personnel, non versionné,
qui contient au moins `0-PROJETS`, `1-CONCEPTS`, `2-RESSOURCES` et
`0-EN VRAC`. Ce dernier est la zone de dépôt de l'utilisateur : c'est le seul
endroit du coffre parent où un agent écrit.

La règle complète est au §7 de `IA/system/VAULT-CONTRACT.md`, qui fait foi —
elle n'est pas recopiée ici.

## Infrastructure

**Confirmée par l'utilisateur le 2026-09-03.** Un hôte **Proxmox** portant au
moins une **VM Debian**, laquelle fait tourner des conteneurs **Docker**
derrière **Traefik**, avec des sauvegardes à vérifier.

Conséquences pratiques :

- le poste est sous Arch, les machines administrées sous Debian : ne pas
  confondre `pacman` et `apt` selon la cible ;
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
