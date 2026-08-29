---
schema: 1
kind: skill
name: diagnostic-linux
description: Constater l'état d'un système Linux — services, journaux, charge, disque, mémoire, réseau. Ne corrige rien.
type: core
read_only: true
---

# Skill — Diagnostic Linux

Établir un constat sur une machine Linux : ce qui tourne, ce qui a échoué, ce
qui sature.

> **Ce skill ne répare rien.** Il n'exécute que des commandes de lecture. Toute
> action corrective relève de `remediation-linux`, chargé séparément et
> explicitement. Si un diagnostic conclut à une action, l'énoncer — ne pas la
> faire.

## Règles

1. **Ne jamais exécuter une commande qui modifie l'état.** Pas de `restart`, pas
   de `kill`, pas de `prune`, pas d'écriture, pas d'installation.
2. Établir le constat **avant** de proposer quoi que ce soit. Un symptôme n'est
   pas une cause.
3. Citer les commandes exécutées et leur sortie. Ne jamais résumer un journal
   sans donner de quoi le retrouver.
4. Distinguer explicitement ce qui est **observé** de ce qui est **supposé**.
5. Ne jamais recopier dans une note du coffre une adresse IP interne, un nom
   d'hôte, une clé ou un identifiant. Voir la section « Secrets ».

## Méthode

Procéder du général au particulier. S'arrêter dès que la cause est identifiée —
inutile de dérouler toute la séquence.

### 1. Vue d'ensemble

```bash
uptime                          # charge moyenne, durée de fonctionnement
systemctl --failed              # unités en échec — souvent la réponse directe
df -h                           # remplissage des systèmes de fichiers
free -h                         # mémoire et swap
```

Une charge moyenne supérieure au nombre de cœurs indique une saturation.
Vérifier le nombre de cœurs : `nproc`.

### 2. Journaux

```bash
journalctl -p err -b --no-pager           # erreurs depuis le démarrage
journalctl -p warning -b --no-pager -n 50
journalctl -u <service> -n 50 --no-pager
journalctl --since "1 hour ago" -p err
```

Journaux du démarrage précédent (utile après un plantage) :

```bash
journalctl -b -1 -p err --no-pager
```

### 3. Services

```bash
systemctl status <service>
systemctl list-units --type=service --state=running
systemctl list-timers --all
```

### 4. Disque

```bash
df -h                           # espace
df -i                           # inodes — un disque plein d'inodes affiche 0 % utilisé
du -xh --max-depth=1 / 2>/dev/null | sort -h | tail -20
lsblk -f
```

État de santé physique :

```bash
sudo smartctl -H /dev/sdX
sudo smartctl -A /dev/sdX | grep -iE "reallocated|pending|uncorrect"
```

### 5. Mémoire

```bash
free -h
ps aux --sort=-%mem | head -10
dmesg -T | grep -i "out of memory"      # traces de l'OOM killer
```

### 6. Réseau

```bash
ip -br addr
ip route
ss -tulpn                       # ports en écoute et processus associés
resolvectl status               # résolution DNS
```

### 7. Processeur et entrées-sorties

```bash
top -b -n 1 | head -20
iostat -x 1 3                   # paquet sysstat
```

## Interprétation

| Symptôme | Piste à creuser |
| --- | --- |
| Charge élevée, processeur au repos | Attente d'entrées-sorties → `iostat`, santé disque |
| Service qui redémarre en boucle | `journalctl -u <service>` — l'erreur est dans les dernières lignes avant chaque relance |
| Disque à 100 % mais `du` ne trouve rien | Fichier supprimé encore ouvert → `lsof +L1` |
| Mémoire saturée sans processus coupable | Cache et tampons — normal. Regarder la colonne `available`, pas `free` |
| Espace libre mais écriture impossible | Inodes épuisés → `df -i` |
| Lenteur générale inexpliquée | Vérifier le thermal throttling et les journaux du noyau |

## Secrets

Ce skill s'exécute souvent sur des machines distantes. **Rien de ce qui suit ne
doit être écrit dans une note du coffre** : adresses IP privées, noms d'hôtes
internes, chemins de clés SSH, mots de passe, jetons, contenu de fichiers
`.env`.

Si une sortie de commande contient ce genre d'information, la remplacer par un
marqueur dans le compte rendu — le coffre est versionné sur GitHub.

L'inventaire des machines vit dans un fichier **hors dépôt**, listé au
`.gitignore`. Ce skill le lit, ne le recopie jamais.

## Format du compte rendu

1. **Constat** — ce qui a été observé, avec les commandes.
2. **Cause probable** — clairement identifiée comme hypothèse.
3. **Action recommandée** — énoncée, non exécutée. Préciser si elle nécessite
   `remediation-linux` et si elle est réversible.

## Contraintes

`read_only: true` — aucune écriture, aucune modification d'état, y compris via
patch. Voir `../system/VAULT-CONTRACT.md`.
