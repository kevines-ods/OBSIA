---
schema: 1
kind: skill
name: sauvegardes
description: Vérifier que les sauvegardes existent, sont récentes, respectent la règle 3-2-1, et se restaurent réellement. À charger avant toute action risquant de détruire des données, et lors d'un contrôle périodique. Ne restaure jamais par-dessus l'original et ne supprime aucune sauvegarde.
module: controle-des-sauvegardes
type: core
read_only: true
---

# Skill — Sauvegardes

Contrôler l'état des sauvegardes de l'infrastructure.

> **Le principe directeur.** Une sauvegarde dont la restauration n'a jamais été
> testée n'est pas une sauvegarde, c'est une supposition. Ce skill s'intéresse
> autant à la restauration qu'à la copie.

## Règles

1. **Ne jamais restaurer par-dessus des données vivantes.** Toute restauration
   de test se fait vers un emplacement neuf, jamais vers l'original.
2. Ne jamais supprimer une sauvegarde ancienne, même expirée. Le signaler.
3. Une sauvegarde présente ≠ une sauvegarde valide. Vérifier la taille, la date,
   et l'intégrité quand l'outil le permet.
4. Ne jamais inscrire de mot de passe de dépôt ni de clé de chiffrement dans une
   note du coffre.

## La règle 3-2-1

Trois copies, sur deux supports différents, dont une hors site. À vérifier
explicitement, car c'est le point qui manque le plus souvent : un NAS qui
sauvegarde sur lui-même ne survit ni au vol, ni à l'incendie, ni au
chiffrement par rançongiciel.

| Copie | Emplacement typique |
| --- | --- |
| 1 — production | la VM elle-même |
| 2 — locale | autre pool du NAS, disque distinct |
| 3 — hors site | disque externe rotatif, ou stockage distant chiffré |

## Proxmox Backup

Lister les sauvegardes d'une VM :

```bash
pvesm list <stockage> | grep vzdump
ls -lh /var/lib/vz/dump/
```

Tâches planifiées et leur dernier résultat :

```bash
cat /etc/pve/jobs.cfg
grep -i vzdump /var/log/syslog | tail -20
```

Avec Proxmox Backup Server :

```bash
proxmox-backup-client snapshot list --repository <dépôt>
proxmox-backup-client status --repository <dépôt>
```

Vérification d'intégrité (à lancer périodiquement, c'est long) :

```bash
proxmox-backup-manager verify-job list
```

**Aucune tâche de vérification = rien ne relit jamais le datastore** : un
`verification.cfg` absent se signale comme une alerte, pas comme un détail.
L'historique des tâches exige `--all`, sinon la liste est vide :
`proxmox-backup-manager task list --all` (pas d'option `--type` : filtrer
`worker_type` à la main).

Pièges propres à PBS :

- **Datastore amovible démonté = `inactive`** dans `pvesm status` : c'est
  normal quand le disque est ailleurs. Ses tâches planifiées de vérification,
  d'élagage et de nettoyage sont **sautées** tant qu'il n'est pas monté — d'où
  `verify-new true` sur un tel datastore. La règle udev livrée par PBS ne gère
  que le branchement : le démontage reste à la charge du script de sauvegarde.
- La sauvegarde vzdump d'un conteneur **n'inclut pas ses points de montage**
  (NFS, bind) : un conteneur de 7 Go peut servir des centaines de Go qui ne sont
  sauvegardés nulle part par ce job.
- Un job **terminé en code 0 peut être cohérent mais partiel** s'il a tourné
  pendant un gros transfert : comparer le volume avec la sauvegarde suivante.
- Un jeton d'API PBS a **ses propres ACL** : accorder le rôle à l'utilisateur
  **et** au jeton (`user@realm` et `user@realm!jeton`). Dans un shell bash
  interactif, le `!` d'un identifiant de jeton est développé même entre
  guillemets doubles : `set +H`, ou guillemets simples.

## Restic

```bash
restic snapshots
restic stats latest
restic check                    # intégrité de la structure
restic check --read-data-subset 5%   # vérifie réellement des données
```

Test de restauration vers un emplacement neuf :

```bash
restic restore latest --target /tmp/test-restauration
```

- **`restic diff` ne mesure pas un volume** : il compte les blobs neufs après
  déduplication (« 58 Mio ajoutés » pour 27 Gio réels). Pour la taille, comparer
  les `restic ls -l` des deux snapshots, ou `restic stats --mode restore-size`.
- Dépôt monté **en lecture seule** → `--no-lock`, sinon restic échoue en voulant
  poser un verrou. Monter un disque btrfs en lecture seule : `mount -o ro` —
  l'option `noload` n'existe que pour ext4 et xfs.
- L'espace libéré à la source ne se retrouve qu'après `forget --prune` des
  snapshots qui référencent encore les fichiers.
- Sur des données importées, les dates de modification sont celles d'origine :
  ce qui est **arrivé** récemment se trouve avec `find -newerct`.

## Disque hors site rotatif

Un disque externe qui tourne entre plusieurs machines ne peut être branché
**qu'à un seul endroit à la fois**. Si chaque machine déclenche sa sauvegarde
au branchement (udev + service avec `ConditionPathExists=` sur l'UUID), celle
qui n'a pas le disque **saute en silence** : aucune erreur, aucun journal,
aucune notification.

- **Avant de conclure « la sauvegarde a échoué », vérifier où est le disque**
  (`ls -l /dev/disk/by-uuid/<uuid>` sur chaque machine).
- Lire la **dernière ligne du journal** avant de le débrancher : c'est le
  script qui démonte, pas l'utilisateur.
- Ce silence voulu se compense par un compte rendu à chaque exécution réelle
  (`surveillance-et-alertes`).

## SnapRAID

**SnapRAID n'est pas une sauvegarde** : il protège d'une panne de disque, pas
d'une suppression. Un fichier effacé reste restaurable depuis la parité
(`snapraid fix -d <fichier>`) **seulement jusqu'au `sync` suivant** — souvent
la nuit même. À savoir **avant** de lancer un `sync` « pour nettoyer ».

- **Trouver la vraie configuration** : le greffon d'OpenMediaVault écrit
  `/etc/snapraid/array<n>.conf`, pas `/etc/snapraid.conf`. Toutes les commandes
  prennent `-c <conf>`. Un job qui ne trouve aucun fichier `.content` s'arrête
  en `WARN: No Content files found!` **sans rien synchroniser** — y compris
  quand le tableau n'a jamais été initialisé.
- Sous OpenMediaVault, les seuils (`delthreshold`, `updthreshold`) se lisent
  dans la **base OMV**, pas dans `/etc/snapraid-diff.conf` : ils se règlent
  dans l'interface.
- **`scrub` sans option ne fait rien sur des blocs récents** (`Nothing to do`) :
  le filtre par défaut ignore ce qui a moins de 10 jours. Toujours
  `snapraid -c <conf> scrub -p 10 -o 0` ; une passe vaut environ 10 %.
- **`Missing file` + `Unexpected file errors` pendant un `scrub` = index
  périmé**, pas un disque défaillant : des fichiers supprimés depuis le dernier
  `sync`. Remède : `sync`, qui ne supprime rien — mais referme la fenêtre de
  récupération ci-dessus.
- `You have N files with a zero sub-second timestamp` : une part de l'array
  reste impossible à certifier. Remède `snapraid touch` puis `sync`, qui
  re-hache tout — **plusieurs heures**, à programmer.
- Le `scrub` n'écrit sa progression que sur un terminal : suivre
  `/proc/<pid>/io` ou le journal de fin de passe, et détacher les longues
  séries (`setsid nohup`).
- Le rapport par courriel du greffon part **dans le vide** sans SMTP configuré
  (`statusreport sent to ''`) : surveiller la fraîcheur du journal à la place.

## Nextcloud

Trois choses distinctes à sauvegarder, et il faut les trois :

1. Le répertoire `data/` (les fichiers)
2. La base de données
3. Le fichier `config/config.php`

```bash
# base de données (adapter au SGBD utilisé)
mysqldump --single-transaction nextcloud > nextcloud.sql
# ou
pg_dump nextcloud > nextcloud.sql
```

> Passer Nextcloud en mode maintenance avant la sauvegarde de la base, sinon la
> cohérence entre fichiers et base n'est pas garantie :
> `occ maintenance:mode --on` puis `--off`.

## Conteneurs Docker

Ce qui compte, ce sont les **volumes**, pas les images — celles-ci se
retéléchargent.

```bash
docker volume ls
docker run --rm -v <volume>:/data -v $(pwd):/sauvegarde alpine \
  tar czf /sauvegarde/<volume>.tar.gz -C /data .
```

Les fichiers `docker-compose.yml` doivent être versionnés séparément. Sans eux,
les volumes ne servent à rien.

## Contrôle périodique

À chaque passage, répondre à ces questions :

- [ ] La dernière sauvegarde de chaque VM date de moins de 24 h ?
- [ ] Sa taille est cohérente avec la précédente ? (une chute brutale = alerte)
- [ ] Le dernier job s'est terminé sans erreur ?
- [ ] Une copie existe hors du NAS ?
- [ ] Une restauration de test a eu lieu il y a moins de trois mois ?
- [ ] L'espace restant permet encore au moins deux cycles ?

La cinquième case est celle qu'on ne coche jamais. C'est celle qui compte.

## Signaux d'alerte

| Observation | Ce que ça signifie |
| --- | --- |
| Taille en chute brutale | Un point de montage manquant → la sauvegarde est vide |
| Taille en hausse constante | Rétention mal configurée → saturation prochaine |
| Job « réussi » sans fichier produit | Vérifier le chemin de destination |
| Toutes les sauvegardes sur le même pool | La règle 3-2-1 n'est pas respectée |
| Dépôt accessible en écriture depuis la production | Un rançongiciel les chiffrera aussi |
| Datastore amovible `inactive` | Normal si le disque est ailleurs — vérifier où avant d'alerter |
| Job SnapRAID « terminé » sans `sync` dans le journal | Mauvaise configuration ou tableau non initialisé |

## Contraintes

`read_only: true`. Ce skill constate et alerte. Créer, modifier ou supprimer une
sauvegarde relève d'une action explicite hors de son périmètre ; un remède cité
ici (`snapraid sync`, `touch`) s'énonce et s'exécute par `remediation-linux`.
Voir `../system/VAULT-CONTRACT.md`.
