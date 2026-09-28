---
schema: 1
kind: skill
name: nextcloud-aio
description: Administrer une instance Nextcloud All-in-One — commandes occ et base de données par Docker, comptes, partages par l'API OCS, suivi d'un auto-upload, doublons, corbeille, données sur NFS et démarrage sûr. À charger dès qu'une demande touche Nextcloud, ses fichiers, ses comptes ou l'application mobile qui y envoie des photos.
module: administration-homelab
type: outil
read_only: false
---

# Skill — Nextcloud AIO

Nextcloud All-in-One tourne en conteneurs Docker gérés par son propre
conteneur maître. On n'y entre pas comme dans une installation classique.

## Accès

```bash
docker exec -u www-data nextcloud-aio-nextcloud php occ <commande>
docker exec nextcloud-aio-database psql -U nextcloud -d nextcloud_database
```

Depuis un hyperviseur, préfixer par `pct exec <id> --` si AIO vit dans un LXC.
Le panneau d'administration AIO écoute sur le port 8080 de l'hôte Docker ; sa
**phrase de passe est un secret** — ni dans une note, ni dans la conversation.

## Comptes et partages

- `occ user:auth-tokens:add <uid> --name=<nom> -n` crée un mot de passe
  d'application **sans** le mot de passe de connexion.
- **`occ` ne sait pas créer un partage** : passer par l'API OCS, et par le
  **domaine réel** — un `Host: localhost` échoue en TLS (erreur 35, SNI non servi
  par le proxy AIO) :
  ```bash
  curl -sk --resolve <domaine>:443:127.0.0.1 -u "<uid>:<jeton>" \
    -H "OCS-APIRequest: true" https://<domaine>/ocs/v2.php/apps/files_sharing/api/v1/shares …
  ```
- Renommer ou déplacer un **partage reçu** ne déplace aucun octet : seul
  `oc_share.file_target` change.
- Sur disque, la racine d'un compte ne contient que **ses** dossiers : les
  partages reçus sont virtuels.
- Un fichier supprimé par le **destinataire** d'un partage part dans la
  corbeille du **propriétaire** : `occ trashbin:cleanup <propriétaire>`.
- Un quota ne limite que le compte **propriétaire** des fichiers : un
  destinataire qui écrit dans un partage remplit l'espace de l'autre.

## Fichiers

- Rescan **ciblé** : `occ files:scan --path="<uid>/files/<dossier>"` — jamais un
  scan complet de dizaines de milliers de fichiers sans raison.
- Sur des données importées (Takeout, anciennes photos), la date de
  modification est celle d'origine : trouver ce qui est **arrivé** récemment
  avec `find -newerct` (ctime), pas `-newermt`.
- L'espace libéré dans Nextcloud **ne se retrouve pas tout de suite** dans les
  sauvegardes : les anciens snapshots référencent encore les fichiers jusqu'à
  leur expiration.

### Suivre ce qu'un client dépose, en direct

```sql
SELECT to_char(to_timestamp(a.timestamp),'HH24:MI:SS') AS t, a.affecteduser AS compte, f.path
FROM oc_activity a JOIN oc_filecache f ON f.fileid = a.object_id
WHERE a.app='files' AND a.subject='created_self'
  AND a.timestamp > extract(epoch from now()) - 21600 ORDER BY a.timestamp DESC;
```

La base est en **UTC** : corriger le décalage avant de corréler avec les dates
vues sur le NAS. `affecteduser` est le compte qui **envoie**.

### Doublons d'auto-upload (application Android)

L'application refuse deux règles sur le même dossier, mais **accepte une règle
sur un dossier parent et une autre sur l'un de ses sous-dossiers** : le
sous-dossier est alors envoyé deux fois. Règle d'or : **aucune source de règle
ne doit être contenue dans la source d'une autre.** Preuve : le même fichier,
à la même seconde, dans deux destinations de `oc_activity`.

Autres pièges du même écran : « utiliser des sous-dossiers » recrée
l'arborescence locale ; « stocker dans des sous-dossiers selon la date » mêle
plusieurs conventions dans un dossier si on ne l'uniformise pas.

Avant d'accuser le serveur d'une suppression, **vérifier `oc_activity`** : un
client mobile resté configuré sur un compte inactif peut en effacer les données.

### Purger des doublons

1. Comparer `nom|taille` avec la référence (`find … -printf "%f|%s\n" | sort -u`
   puis `comm`), puis confirmer par somme de contrôle.
2. Déplacer d'abord les fichiers **uniques**, puis supprimer avec un garde-fou
   qui refuse tout fichier non vérifié. La vérification trouve ce qu'on n'attend
   pas (des pièces d'identité absentes de la copie de référence, par exemple).
3. Rescan ciblé.

## Données sur NFS et démarrage

- Le dossier de données (`/mnt/ncdata`) **ne doit jamais être vide au
  démarrage** : AIO part en boucle de redémarrage (`Permission denied`, dossier
  vu `65534:65534 755` au lieu de `33:0 750`). Protéger par un hook `pre-start`
  qui refuse de démarrer sur un montage absent ou vide (`administration-proxmox`).
- **Deux instances Nextcloud ne partagent jamais le même dossier de données** :
  deux bases qui indexent les mêmes fichiers divergent et se contredisent.
  Arrêter l'une ne suffit pas si elle peut redémarrer : la détacher du dossier.

## Rationalisations

| Ce qu'on se dit | La réalité |
| --- | --- |
| « un scan complet, pour être sûr » | des heures sur un NAS limité par son disque, pour un seul dossier à rafraîchir |
| « l'app n'autorise qu'une règle par dossier, donc pas de doublon possible » | parent + enfant envoie deux fois |
| « c'est le serveur qui a supprimé ces fichiers » | `oc_activity` dit qui a agi — souvent un client |
| « j'ai supprimé 40 Go, la sauvegarde va maigrir » | pas avant l'expiration des anciens snapshots |

## Contraintes

`read_only: false`. Voir `../system/VAULT-CONTRACT.md`. Toute suppression suit
la politique de l'agent : liste, somme de contrôle, « oui » explicite.
