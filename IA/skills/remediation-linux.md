---
schema: 1
kind: skill
name: remediation-linux
description: Corriger un système Linux — redémarrer un service, libérer de l'espace, restaurer une configuration, revenir en arrière. À charger seulement après un constat écrit par `diagnostic-linux`, jamais seul. Chaque action est annoncée, puis vérifiée avant la suivante.
type: outil
read_only: false
---

# Skill — Remédiation Linux

Appliquer une correction sur un système Linux, après diagnostic.

> **Ce skill agit.** Il ne se charge jamais seul : il suppose qu'un diagnostic a
> déjà établi la cause. Corriger sans avoir constaté, c'est deviner en cassant
> des choses.

## Règles

1. **Charger `diagnostic-linux` d'abord.** Aucune correction sans constat écrit.
2. **Annoncer l'action avant de l'exécuter** : la commande exacte, ce qu'elle
   change, si elle est réversible, et comment revenir en arrière. Attendre
   l'accord.
3. **Une action à la fois.** Puis vérifier. Enchaîner trois corrections d'affilée
   rend impossible de savoir laquelle a résolu — ou aggravé — le problème.
4. **Sauvegarder tout fichier avant de le modifier**, avec la date :
   `sudo cp fichier fichier.bak-$(date +%F)`.
5. Ne jamais exécuter une commande dont l'effet n'est pas compris. Demander.
6. **Interdit sans accord explicite et circonstancié** : `rm -rf`, `dd`,
   `mkfs`, `> fichier`, `chown -R` / `chmod -R` hors du répertoire personnel,
   toute suppression de partition ou de volume.

## Avant toute correction

- [ ] Le diagnostic identifie une cause, pas seulement un symptôme ?
- [ ] L'action est-elle réversible ? Si non, une sauvegarde existe-t-elle ?
- [ ] Y a-t-il un moyen moins intrusif d'obtenir le même résultat ?
- [ ] Quels services vont être interrompus, et pour combien de temps ?

Si la machine héberge un service utilisé par quelqu'un d'autre au moment de
l'intervention, le dire avant d'agir.

## Services

```bash
sudo systemctl restart <service>
sudo systemctl status <service>          # vérifier immédiatement après
```

Redémarrage propre plutôt que brutal, quand le service le supporte :

```bash
sudo systemctl reload <service>          # relit la configuration sans couper
```

Valider une configuration **avant** de recharger, quand l'outil le permet :

```bash
sudo nginx -t
sudo sshd -t
sudo systemd-analyze verify <unité>.service
```

> Recharger une configuration invalide coupe le service. Tester d'abord évite
> de se retrouver sans SSH sur une machine distante — panne classique et
> particulièrement pénible sur un NAS.

## Espace disque

Par ordre de risque croissant.

Journaux systemd, sans danger :

```bash
journalctl --disk-usage
sudo journalctl --vacuum-time=30d
```

Cache du gestionnaire de paquets :

```bash
sudo pacman -Sc                          # Arch / CachyOS
sudo apt clean                           # Debian
```

Fichiers supprimés mais toujours ouverts (cas du disque plein invisible) :

```bash
sudo lsof +L1
```

La solution est de redémarrer le processus qui les détient, pas de supprimer
quoi que ce soit.

> Ne jamais lancer un `rm -rf` exploratoire pour faire de la place. Identifier
> précisément quoi supprimer avec `du`, l'annoncer, puis agir.

## Restaurer une configuration

```bash
sudo cp /etc/fichier.conf /etc/fichier.conf.bak-$(date +%F)
# modification
sudo systemctl reload <service> || sudo cp /etc/fichier.conf.bak-$(date +%F) /etc/fichier.conf
```

Sur Arch et CachyOS, les fichiers `.pacnew` signalent une configuration mise à
jour par un paquet et non fusionnée :

```bash
sudo find /etc -name "*.pacnew" -o -name "*.pacsave"
```

Les traiter un par un avec `diff`, jamais en écrasant en masse.

## Processus

```bash
sudo systemctl stop <service>            # préférer, si le processus est un service
kill <PID>                               # SIGTERM — laisse le processus se terminer
kill -9 <PID>                            # SIGKILL — dernier recours, risque de corruption
```

`kill -9` sur une base de données ou un service en écriture peut laisser des
données incohérentes. Toujours essayer `SIGTERM` et attendre.

## Paquets

```bash
sudo pacman -Syu                         # CachyOS : mise à jour complète, jamais partielle
sudo apt update && sudo apt upgrade      # Debian
```

> Sur Arch, une mise à jour partielle (`pacman -Sy paquet`) casse le système.
> C'est `-Syu` ou rien.

Sur les VM Debian du NAS, vérifier après mise à jour du noyau que les modules
nécessaires sont toujours présents avant de redémarrer.

## Après chaque correction

1. Vérifier que le problème a disparu — avec la même commande qui l'avait montré.
2. Vérifier que rien d'autre n'a cassé : `systemctl --failed`.
3. Consigner : symptôme, cause, action, résultat. C'est ce qui rend la panne
   suivante plus rapide à résoudre. Deux destinations, selon la portée :
   le **log de session** (`VAULT-CONTRACT.md` §9) pour la trace de l'action ;
   `mémoire/<agent>/expériences/` si la leçon resservira ailleurs (§6).
   Ni l'un ni l'autre ne reçoit d'adresse IP, de nom d'hôte interne ou
   d'identifiant — le dépôt est public.

## Ce qui n'est pas dans le périmètre

- La couche Proxmox (démarrage/arrêt de VM, stockage) → skill `proxmox`
- Les conteneurs → skill `conteneurs-docker`
- La restauration de sauvegarde → skill `sauvegardes`

## Contraintes

`read_only: false`. Preview obligatoire avant toute action multi-fichiers,
archivage avant écrasement. Voir `../system/VAULT-CONTRACT.md`.
