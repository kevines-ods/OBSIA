---
schema: 1
kind: tâche
name: maj-obsia-cachyos
description: Rafraîchir le clone OBSIA du poste secondaire depuis GitHub, à sens unique et sans jamais écrire dans l'arbre de travail.
module: planification
mode: commande
quand: "0 * * * *"
fuseau: Europe/Paris
exécutant: local
actif: true
---

# Tâche — Mise à jour d'OBSIA sur le poste secondaire

## Intention

`OBSIA/` est exclu de Syncthing — un `.git` synchronisé se corrompt — donc tout
le reste du coffre circule seul entre les machines, et le dépôt non : il ne
bouge que par git. Sur le poste secondaire, personne ne pousse et rien ne tire :
sans cette tâche, le clone ne se rafraîchit jamais, et l'écart avec le serveur
principal grandit à chaque poussée — un jour de retard au départ, puis des
semaines.

Toutes les heures, parce que la tâche est sans effet quand il n'y a rien à
faire : elle se présente, constate que le commit local est déjà le commit
distant, et s'arrête sans avoir rien écrit.

`exécutant: local` parce qu'elle a besoin du clone sous la main et du dépôt
privé joignable : un planificateur distant n'aurait rien à rafraîchir.

## Portée

**À instancier sur le poste secondaire seulement.** Le registre ne porte pas la
machine d'une tâche — `exécutant` dit *le type* d'exécutant, jamais l'hôte — et
cette tâche-ci n'a de sens que là. La contrainte est donc tenue par le script :
`scripts/maj_obsia.py` lit le nom du poste attendu dans une configuration locale
hors dépôt (`~/.config/obsia/maj_obsia.conf`) et sort sans rien faire partout
ailleurs — y compris si la tâche venait à être instanciée ailleurs par mégarde,
ou si la configuration manque. Le nom réel du poste n'est pas dans le dépôt : il
reste dans l'inventaire (`Homelab — vue d'ensemble`), où le script se contente
de renvoyer.

Sur le serveur principal, le clone est celui sur lequel on travaille, et il est
normal qu'il soit modifié en cours de séance : rien ne doit l'avancer
automatiquement.

## Commande

```bash
python3 scripts/maj_obsia.py
```

Le script ne pousse pas, ne rebase pas, ne force pas, ne revient jamais en
arrière et ne régénère rien — les fichiers générés sont suivis par git et
arrivent avec le commit. Il rend un code de sortie par verdict, pour que le
journal de systemd dise ce qui s'est passé sans qu'on ait à le deviner : arbre
sale (2), divergence (3), contrôle rouge (4), réseau injoignable (5).

Pour voir le verdict sans rien écrire :

```bash
python3 scripts/maj_obsia.py --verifier
```

Le script ne sait pas tout seul quel poste il doit servir : le nom est lu dans
`~/.config/obsia/maj_obsia.conf`, hors dépôt (voir la Portée). À poser sur le
poste avant d'instancier la tâche :

```bash
python3 scripts/maj_obsia.py --config > ~/.config/obsia/maj_obsia.conf
# puis renseigner `machine_cible`
```

Sans ce fichier, le script sort en 0 sans rien faire — la tâche est alors
silencieusement sans effet, comme si elle était instanciée sur un autre poste.
