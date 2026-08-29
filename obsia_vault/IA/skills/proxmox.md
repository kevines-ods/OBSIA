---
schema: 1
kind: skill
name: proxmox
description: Inspecter un hôte Proxmox — VM, conteneurs LXC, stockage, cluster, ressources.
type: outil
read_only: true
---

# Skill — Proxmox

Constat sur l'hôte hyperviseur : machines virtuelles, conteneurs LXC, stockage,
répartition des ressources.

> **Couche la plus dangereuse de l'infrastructure.** Une commande malheureuse
> ici n'affecte pas un service, elle affecte toutes les VM à la fois. Ce skill
> est en lecture seule, et cette contrainte n'est pas négociable pour du
> diagnostic courant.

## Règles

1. Aucune commande modifiant l'état : ni `qm start/stop/destroy`, ni
   `pct`, ni `pvesm remove`, ni modification de configuration.
2. **Toujours identifier une VM par son VMID avant d'en parler.** Les noms se
   ressemblent, les identifiants non.
3. Avant de recommander une action sur une VM, vérifier qu'un instantané ou une
   sauvegarde récente existe. Sinon, le dire.
4. Ne jamais recopier dans le coffre : IP, noms d'hôtes internes, contenu de
   `/etc/pve/`, empreintes de clés.

## Inventaire

```bash
qm list                         # machines virtuelles
pct list                        # conteneurs LXC
pvesh get /nodes                # nœuds du cluster
pveversion -v                   # versions des composants
```

Configuration d'une VM précise :

```bash
qm config <VMID>
pct config <CTID>
```

## Ressources

```bash
pvesh get /nodes/<nœud>/status
qm status <VMID> --verbose
```

Sur-allocation — à vérifier systématiquement sur un NAS domestique :

```bash
# somme de la RAM allouée à toutes les VM
qm list | awk 'NR>1 {somme+=$4} END {print somme " Mo alloués"}'
free -h                         # RAM réellement disponible
```

La sur-allocation mémoire est courante et acceptable tant que les VM
n'utilisent pas tout simultanément. Elle devient un problème le jour où
l'hôte commence à swapper : tout ralentit d'un coup, sans coupable évident.

## Stockage

```bash
pvesm status                    # tous les stockages et leur remplissage
pvesm list <stockage>
```

Sur ZFS :

```bash
zpool status                    # état des pools et des disques
zpool list -o name,size,alloc,free,frag,cap,health
zfs list -o name,used,avail,refer
zfs list -t snapshot
```

> Un pool ZFS au-delà de **80 %** de remplissage se fragmente et ralentit
> nettement. Au-delà de 90 %, les performances s'effondrent. C'est un seuil à
> surveiller bien avant la saturation réelle.

Sur LVM-thin :

```bash
lvs -a
vgs
```

> Un pool thin qui atteint 100 % corrompt les volumes qu'il contient. Ce n'est
> pas un simple manque d'espace : les données sont perdues. Surveiller `Data%`.

## Instantanés

```bash
qm listsnapshot <VMID>
pct listsnapshot <CTID>
```

> Un instantané n'est pas une sauvegarde : il vit sur le même stockage. Si le
> disque meurt, les deux disparaissent. Et un instantané laissé en place des
> semaines grossit indéfiniment jusqu'à saturer le pool.

## Journaux

```bash
journalctl -u pvedaemon -n 50 --no-pager
journalctl -u pve-cluster -n 50 --no-pager
journalctl -u qemu-server@<VMID> --no-pager
cat /var/log/pve/tasks/index | tail -20      # historique des tâches
```

## Réseau

```bash
cat /etc/network/interfaces
ip -br link
brctl show 2>/dev/null || bridge link
```

## Points de vigilance sur ton infrastructure

| Point | Pourquoi |
| --- | --- |
| Dépôt d'entreprise non souscrit | Bandeau d'avertissement à chaque connexion. Basculer sur le dépôt `no-subscription` est normal en usage personnel |
| VM Nextcloud et VM Docker sur le même pool | Une saturation du pool les arrête toutes les deux |
| Ollama sans passage GPU | Vérifier `qm config <VMID>` pour `hostpci` — sinon inférence sur processeur, très lente |
| Home Assistant | Demande souvent un passage USB (clé Zigbee/Z-Wave) : `qm config` doit montrer une entrée `usb` |
| Instantanés anciens | Les lister à chaque contrôle, ils sont vite oubliés |

## Contraintes

`read_only: true`. Voir `../system/VAULT-CONTRACT.md`.
