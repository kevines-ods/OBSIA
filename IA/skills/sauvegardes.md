---
schema: 1
kind: skill
name: sauvegardes
description: Vérifier que les sauvegardes existent, sont récentes, respectent la règle 3-2-1, et se restaurent réellement. À charger avant toute action risquant de détruire des données, et lors d'un contrôle périodique. Ne restaure jamais par-dessus l'original et ne supprime aucune sauvegarde.
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

## Contraintes

`read_only: true`. Ce skill constate et alerte. Créer, modifier ou supprimer une
sauvegarde relève d'une action explicite hors de son périmètre. Voir
`../system/VAULT-CONTRACT.md`.
