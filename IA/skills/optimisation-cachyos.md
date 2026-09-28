---
schema: 1
kind: skill
name: optimisation-cachyos
description: Diagnostiquer et optimiser un poste CachyOS (base Arch) — noyau et ordonnanceur (BORE, sched-ext), mémoire et zram, disques et btrfs, réseau, services, jeu, nettoyage des caches et des instantanés snapper. À charger pour optimiser, nettoyer ou accélérer une machine CachyOS, ou quand l'espace disque ne revient pas après une suppression.
module: poste-cachyos
type: outil
read_only: false
---

# Skill — Optimisation CachyOS

CachyOS est une Arch optimisée : noyaux `linux-cachyos*` (EEVDF, BORE,
compilés LTO/AutoFDO/PGO), dépôts par niveau de CPU (`x86-64-v3`, `v4`,
`znver4`), `pacman` forké, ordonnanceurs en espace utilisateur (sched-ext).
Beaucoup de réglages sont déjà bons par défaut : **mesurer avant de changer**.

## Règles

1. **Diagnostic d'abord, en lecture seule** (section suivante), puis nommer le
   goulot — processeur, mémoire, disque ou réseau — avant de proposer.
2. **`sudo` demande souvent un mot de passe** : l'agent n'exécute alors aucune
   commande root. Il écrit un script lisible dans `/tmp` et le fait lancer
   (`sudo bash /tmp/…`). Toute modification s'annonce, un changement à la fois.
3. **Shell `fish`** fréquent : ni heredoc, ni `$?`, ni boucle bash. Écrire le
   script dans `/tmp` et l'exécuter avec `bash` ; à distance,
   `ssh <poste> bash -s < /tmp/script.sh`.
4. Sauvegarder avant de modifier : `/etc/sysctl.d/`, `/etc/default/grub` ou
   l'entrée systemd-boot, `/etc/scx_loader.toml`.
5. Mise à jour : **`pacman -Syu` complète, jamais partielle**. Ne jamais
   mélanger avec des paquets d'Arch standard sans précaution : le `pacman` de
   CachyOS gère la détection d'architecture.

## Diagnostic

```bash
/lib64/ld-linux-x86-64.so.2 --help | grep "(supported, searched)"   # niveau x86-64 supporté
grep -m1 "model name" /proc/cpuinfo ; uname -r
sysctl kernel.sched_bore 2>/dev/null ; cat /sys/kernel/sched_ext/root/ops 2>/dev/null
free -h ; swapon --show ; zramctl ; sysctl vm.swappiness vm.vfs_cache_pressure
lsblk -f ; findmnt -t btrfs,ext4,xfs ; cat /sys/block/*/queue/scheduler
uptime ; ps aux --sort=-%cpu | head ; ps aux --sort=-%mem | head
sensors 2>/dev/null ; systemctl --failed
sysctl net.ipv4.tcp_congestion_control ; resolvectl status
grep -E '^\[cachyos' /etc/pacman.conf          # dépôts optimisés actifs
```

Vérifier que le dépôt activé (`cachyos-v3`, `cachyos-v4`, `cachyos-znver4`)
correspond au niveau du processeur : un mauvais dépôt donne des plantages ou
des performances dégradées. Le `pacman` de CachyOS note l'origine de chaque
paquet (`INSTALLED_FROM`) : ne pas le remplacer par celui d'Arch.

## Noyau et ordonnanceur

| Usage | Noyau | Ordonnanceur |
| --- | --- | --- |
| jeu, bureau interactif | `linux-cachyos-bore` | BORE |
| usage général, développement | `linux-cachyos` | EEVDF |
| serveur, compilation | `linux-cachyos-server` | EEVDF, pas de préemption |
| stabilité maximale | `linux-cachyos-lts` | BORE |
| temps réel, audio professionnel | `linux-cachyos-rt-bore` | BORE + RT |
| console portable (Steam Deck) | `linux-cachyos-deckify` | BORE |

- Préférer l'outil officiel **`cachyos-kernel-manager`** (graphique et CLI) à un `makepkg` manuel pour installer ou compiler un noyau.
- Changer de noyau : installer aussi ses `-headers` (et le module NVIDIA
  correspondant le cas échéant), garder l'ancien dans le chargeur d'amorçage.
- **sched-ext** : `scx-scheds` + `scx_loader`. `scx_bpfland` (mode Gaming ou
  Auto), `scx_lavd` (latence, bureau). Configuration persistante dans
  `/etc/scx_loader.toml`. Le noyau `-bmq` **ne supporte pas** sched-ext.
- Retour arrière d'urgence : `systemctl disable --now scx_loader`, ou démarrer
  sur l'ancien noyau depuis le menu.

## Mémoire

- CachyOS configure **zram** : vérifier avant d'ajouter un swap.
- Réglages courants (`/etc/sysctl.d/99-performance.conf`) : `vm.swappiness=10`
  pour un bureau, `vm.vfs_cache_pressure=50`. Appliquer par
  `sysctl --system`, qui montre les erreurs.
- `echo 3 > /proc/sys/vm/drop_caches` ne sert qu'à un **test de performance à
  froid** ; ce n'est pas une optimisation.

## Disques, btrfs et snapper

- Ordonnanceur d'E/S : `none` ou `mq-deadline` pour NVMe/SSD, `bfq` pour un
  disque rotatif. Le régler **disque par disque**, par une règle udev
  persistante, après avoir lu la valeur actuelle — jamais par une boucle sur
  tous les périphériques.
- `fstrim.timer` actif par défaut : le vérifier.
- 🚨 **Sur btrfs avec snapper, un fichier supprimé ne libère rien** tant qu'un
  instantané le référence : `df` ne bouge pas alors que `du` montre le dossier
  vide. Lister (`snapper -c root list`), supprimer une plage
  (`snapper -c root delete <n1>-<n2>`), et limiter (`NUMBER_LIMIT=10`).
- `du -x` **ne traverse pas les subvolumes** : mesurer subvolume par subvolume.
- ⚠️ **Ne pas lancer `btrfs filesystem defragment -r`** sur un volume qui a des
  instantanés : la défragmentation casse le partage des extents et **duplique**
  les données, l'espace peut exploser.
- `chattr +C` (pas de copie à l'écriture) pour les images de VM ou les bases :
  ne s'applique qu'aux fichiers **créés ensuite** dans le dossier.

## Nettoyage

Par risque croissant, en **listant avant de supprimer** :

```bash
journalctl --disk-usage ; sudo journalctl --vacuum-size=500M
paccache -rk1                       # garde une version de chaque paquet (pacman-contrib)
pacman -Qdtq                        # orphelins : LISTER, puis sudo pacman -Rns <liste relue>
du -sh ~/.cache/* | sort -h | tail
```

- Un cache supprimé **se régénère** en quelques minutes si l'application tourne
  (navigateur, `paru`, `pip`) : seul un gros poste (modèles `huggingface`,
  Steam) vaut l'effort.
- `~/.cache/<gestionnaire AUR>` contient des **clones de compilation**, parfois
  appartenant à root : ce n'est pas un cache à vider à l'aveugle.
- **Jamais `rm … 2>/dev/null`** : une suppression qui échoue devient invisible
  et le compte rendu est faux.

## Réseau

```bash
sysctl net.ipv4.tcp_congestion_control net.core.default_qdisc
modinfo tcp_bbr 2>/dev/null | head -2
```

BBR + `fq` convient à un poste de jeu et de streaming. `ufw` est souvent
actif : ouvrir un port explicitement pour un test depuis le LAN.

## Jeu

- `gamemode` (`gamemoderun %command%`), `mangohud` pour mesurer en jeu,
  `proton-cachyos` dans Steam.
- Gouverneur CPU : lire l'actuel
  (`cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor | sort | uniq -c`)
  avant de passer en `performance` ; `gamemode` le fait déjà le temps d'une partie.

## Profils

| Profil | Noyau | Ordonnanceur | Swappiness |
| --- | --- | --- | --- |
| Jeu | `linux-cachyos-bore` | `scx_bpfland` Gaming | 10 |
| Productivité | `linux-cachyos` | EEVDF ou `scx_lavd` | 20 |
| Compilation | `linux-cachyos-server` | EEVDF | 1 à 10, `ccache` |

Après chaque changement : températures, `systemctl --failed`, et la même mesure
qu'avant, pour comparer.

## Rationalisations

| Ce qu'on se dit | La réalité |
| --- | --- |
| « j'ai supprimé 40 Go, `df` va suivre » | pas tant que snapper garde l'instantané |
| « une défragmentation compressera tout » | avec des instantanés, elle duplique au lieu de réduire |
| « je vide `~/.cache` entier, c'est sans risque » | la moitié revient en dix minutes, et un dossier de compilation AUR n'est pas un cache |
| « ce réglage est recommandé, je l'applique » | sans mesure avant et après, on ne saura pas s'il a servi — ni lequel a cassé |

## Contraintes

`read_only: false`. Voir `../system/VAULT-CONTRACT.md`. Correction générique
d'un système Linux : `remediation-linux`, après `diagnostic-linux`.
