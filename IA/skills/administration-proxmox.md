---
schema: 1
kind: skill
name: administration-proxmox
description: Agir sur un hôte Proxmox — créer une VM ou un conteneur LXC, régler le démarrage automatique et son ordre, poser un hookscript, monter un partage NFS dans un conteneur, injecter une clé ou exécuter une commande dans un invité, épingler des vCPU. À charger après un constat de `proxmox`, dès qu'une commande `qm`, `pct` ou `pvesm` doit modifier l'état.
module: virtualisation
type: outil
read_only: false
---

# Skill — Administration Proxmox

Le pendant « écriture » de `proxmox`, qui reste en lecture seule. Chaque action
ici touche la couche dont dépendent toutes les VM : elle s'annonce, s'exécute
seule, se vérifie.

## Règles

1. **Constat d'abord** avec `proxmox` : VMID vérifié, état actuel relu
   (`qm config`, `pct config`), sauvegarde ou instantané récent confirmé
   (`sauvegardes`). Sinon, le dire avant d'agir.
2. **Annoncer** la commande exacte, ce qu'elle change, si elle interrompt un
   invité, et comment revenir en arrière. Attendre l'accord.
3. **Une action à la fois**, puis relire la configuration : `qm config <id>`,
   `pct config <id>`, `qm status <id>`. Une option passée en `[PENDING]` n'est
   pas appliquée — il faut un **arrêt puis un démarrage** (pas un `reboot`).
4. Avant d'éditer un fichier de l'hôte (`/etc/fstab`, `storage.cfg`,
   `lvm.conf`) : copie `*.backup.<date>` à côté.
5. **Identifier un disque par UUID**, jamais par `sdX` : la lettre change d'un
   démarrage à l'autre, et un disque passé en brut à une VM porte un autre nom
   vu de l'hôte et vu de l'invité (`dumpe2fs -h /dev/sdX1 | grep "Last mounted on"`).

## Créer une VM

Les options qui comptent, et qu'on regrette d'avoir oubliées :

```bash
qm create <id> --name <nom> --machine q35 --bios ovmf \
  --efidisk0 <stockage>:1,efitype=4m,pre-enrolled-keys=0 \
  --cpu host --cores <n> --memory <Mo> --balloon 0 \
  --scsihw virtio-scsi-single --scsi0 <stockage>:<Go>,discard=on,iothread=1,ssd=1 \
  --net0 virtio,bridge=vmbr0,firewall=1 --agent enabled=1 --onboot 1
```

- **UEFI réel** = `bios: ovmf` **et** `efidisk0:` visibles dans `qm config`.
  Sans eux, la VM est en BIOS legacy même si l'on croit avoir choisi l'UEFI.
  `pre-enrolled-keys=0` désactive Secure Boot (sinon les modules DKMS sont bloqués).
- **`cpu: host`** pour toute VM de calcul : le type par défaut `x86-64-v2`
  n'expose **pas** AVX2, et llama.cpp perd plusieurs fois sa vitesse.
- Après l'installation : retirer l'ISO (`qm set <id> --delete ide2`), vérifier
  que l'installateur n'a pas laissé la racine minuscule (Anaconda : `/` à
  15 Go sur un disque de 100) → `lvextend -l +100%FREE` puis `xfs_growfs /`.
- Installer par **noVNC** : sans `console=ttyS0` sur la ligne du noyau, rien ne
  s'affiche sur la console série.
- Après une reconstruction, l'empreinte SSH change :
  `ssh-keygen -R <adresse>` **sur le poste client**.

## Créer un conteneur LXC

```bash
pct create <id> <stockage>:vztmpl/<modèle> --hostname <nom> \
  --unprivileged 1 --features nesting=1 --cores <n> --memory <Mo> \
  --rootfs <stockage>:<Go> --net0 name=eth0,bridge=vmbr0,ip=<cidr>,gw=<passerelle> \
  --onboot 1
```

- `nesting=1` pour Docker dans le conteneur.
- Un LXC non privilégié **n'a pas `/dev/net/tun`** : Tailscale ou WireGuard y
  exigent `lxc.cgroup2.devices.allow: c 10:200 rwm` + `lxc.mount.entry` et un
  redémarrage. Souvent plus simple : un **routeur de sous-réseau** sur l'hôte.

## Démarrage automatique et ordre

```bash
qm set <id> -onboot 1          pct set <id> -onboot 1
qm set <id> -startup order=1,up=60
```

**Vérifier `onboot` sur tous les invités** après toute création : un invité
sans lui reste éteint après une coupure de courant, et rien ne le signale.

## Hookscripts

Un script appelé par Proxmox aux phases `pre-start`, `post-start`, `pre-stop`,
`post-stop` d'un invité.

```bash
# stockage « snippets » activé dans /etc/pve/storage.cfg (content … ,snippets)
install -m 755 mon-hook.sh /var/lib/vz/snippets/
qm set <id> -hookscript local:snippets/mon-hook.sh      # ou pct set
```

- 🚨 **Ordre des arguments : `<script> <vmid> <phase>`** — le VMID **en
  premier**, à l'inverse de ce que dit la documentation courante. Un script qui
  suppose `phase vmid` est **totalement inerte et silencieux** : sortie 0,
  aucune trace. Écrire le script pour qu'il détecte l'ordre (le seul argument
  numérique est le VMID).
- **Tester en réel**, pas seulement relire : `bash /var/lib/vz/snippets/<script> <id> post-start`.
- Un hook **`pre-start` qui sort en erreur empêche le démarrage** de l'invité :
  utile pour refuser de démarrer un service sur des données absentes, piégeux
  si c'est involontaire.
- Un hook `post-start` est **synchrone** : l'invité suivant de l'ordre de
  démarrage attend sa fin. Bon endroit pour attendre qu'un NAS exporte son NFS
  avant de démarrer le conteneur qui en dépend.

## Partage NFS dans un conteneur

- Sur l'hôte, dans `/etc/fstab` : `<nas>:/export/x /mnt/x nfs _netdev,nofail 0 0`.
  Avec `defaults`, le montage échoue au démarrage si le NAS — souvent une VM du
  même hôte — n'est pas encore prêt.
- Dans le conteneur : `pct set <id> -mp0 /mnt/x,mp=/mnt/x`.
- Un point de montage **`mp0` est résolu au démarrage du conteneur** : monter
  la source après coup ne la rend pas visible, il faut redémarrer le conteneur.
- 🚨 **`pct shutdown` peut ne jamais rendre la main** : systemd *dans* le
  conteneur reprend l'unité `.mount` du NFS et tente de démonter un système de
  fichiers qu'il ne possède pas. Masquer l'unité **dans le conteneur** :
  ```bash
  pct exec <id> -- systemctl mask "$(systemd-escape -p --suffix=mount /mnt/x)"
  ```
  En urgence seulement : `pct stop` (brutal).
- Les fichiers d'un point de montage **ne sont pas dans la sauvegarde vzdump**
  du conteneur : ils se sauvegardent à part.

## Agir dans un invité sans SSH

- **LXC** : `pct push <id> <fichier> <chemin> --perms 600`, puis
  `pct exec <id> -- bash -c "…"`, ou `pct enter <id>`.
- **VM** : agent QEMU —
  ```bash
  pvesh create /nodes/<nœud>/qemu/<id>/agent/exec --command /bin/bash --command -c --command "<commande>"
  pvesh get /nodes/<nœud>/qemu/<id>/agent/exec-status --pid <pid>
  ```
  L'agent **ré-encode en base64** l'`input-data` : lui passer du brut.
- Sur une VM Fedora avec **SELinux en `Enforcing`**, l'agent tourne en
  `virt_qemu_ga_t` et **ne peut pas lire `/home`**, même en root : passer par SSH.
- Injecter une clé SSH ainsi, sans mot de passe ni redémarrage : l'ajouter à
  `/root/.ssh/authorized_keys`, puis compter les clés avec
  `ssh-keygen -lf <fichier> | wc -l` (un fichier sans saut de ligne final
  trompe `wc -l`).
- La **console du nœud** et celle de l'**invité** sont distinctes dans l'UI et
  l'application mobile : vérifier où l'on tape avant de coller une clé.

## Épingler des vCPU

Des vCPU non épinglées peuvent tomber sur deux threads d'un même cœur physique :
un calcul intensif s'effondre alors quand on augmente le nombre de threads.

```bash
lscpu -e                       # correspondance CPU logique → cœur physique
qm set <id> -affinity 0,1,2,3,4,5     # des CPU logiques de cœurs distincts
```

`affinity` passe en `[PENDING]` : arrêt puis démarrage de la VM.

## Stockage LVM-thin

Agrandir le pool quand le groupe de volumes a de la place, et régler
l'auto-extension (`/etc/lvm/lvm.conf`, section `activation`) :

```bash
lvextend -L +30G pve/data
# thin_pool_autoextend_threshold = 80   thin_pool_autoextend_percent = 10
lvs -o lv_name,seg_monitor pve/data        # doit répondre « monitored »
```

L'auto-extension ne vaut que l'espace libre du groupe : ce n'est pas un filet
infini. Un pool thin plein **corrompt** les volumes qu'il contient.

## Rationalisations

| Ce qu'on se dit | La réalité |
| --- | --- |
| « le hook est posé, il marchera au prochain démarrage » | s'il suppose le mauvais ordre d'arguments, il ne fera rien, sans un mot ; seul le test réel le montre |
| « je le démarrerai à la main s'il le faut » | après une coupure, personne n'est là ; un invité sans `onboot` reste éteint |
| « `qm set` a répondu, c'est appliqué » | une option en `[PENDING]` attend un arrêt complet |
| « c'est `sdb`, je l'ai vu hier » | la lettre a pu changer au démarrage ; l'UUID, non |
| « un `pct shutdown` finit toujours par rendre la main » | pas avec un NFS monté dans le conteneur |

## Contraintes

`read_only: false`. Voir `../system/VAULT-CONTRACT.md`. Aucune adresse, aucun
nom d'hôte ni identifiant d'invité n'entre dans le dépôt : ils vivent dans
l'inventaire du coffre parent.
