---
schema: 1
kind: skill
name: cron
description: Gérer les tâches planifiées — registre `IA/tâches/`, instanciation chez l'exécutant, réconciliation après un changement de harness ou de machine. À charger dès qu'une action doit se répéter à heure fixe, et toujours avant d'en créer une. Ne couvre ni le cron système ni les tâches root.
type: outil
read_only: false
---

# Skill — Tâches planifiées

## Principe

Deux objets, à ne jamais confondre :

| | Où | Ce que c'est | Durée de vie |
| --- | --- | --- | --- |
| **la tâche** | `IA/tâches/<nom>.md` | l'intention : quoi, quand, pour quel agent | versionnée, suit le coffre |
| **l'instance** | timer systemd, planificateur du harness… | ce qui déclenche réellement | jetable, propre à une machine |

Le registre fait foi (§12 du contrat). Une instance perdue se recrée depuis le
registre ; une tâche qui n'existe que sous forme d'instance est perdue au
premier changement de harness ou de machine.

**Clé de rapprochement : `obsia-<name>`.** Toute instance porte ce nom, quel
que soit l'exécutant. C'est ce qui rend la réconciliation possible.

## Choisir l'exécutant — une fois, et une seule

**Une tâche = au plus une instance vivante, tous exécutants confondus.** C'est
l'invariant du registre (§12). Le champ `exécutant` le rend applicable : il
dit qui a le droit de déclencher, donc qui n'en a pas.

| Besoin | `exécutant` | Instance |
| --- | --- | --- |
| toucher des fichiers locaux, ou `mode: commande` | `local` | timer systemd utilisateur |
| machine allumée, harness lançable en ligne de commande | `local` | timer systemd qui appelle le harness |
| partir même machine éteinte, ou travail purement distant | `harness` | planificateur du harness, s'il en a un |

> ⚠️ **Le piège du double déclenchement.** Si le harness offre lui-même une
> fonction de planification et que tu t'en sers, ça ne dispense pas de
> déclarer la tâche au registre — et ça **interdit** d'instancier en plus un
> timer local. Deux instances, deux déclenchements. La tâche porte alors
> `exécutant: harness`, et l'étape 3 ne crée rien côté systemd.

Le coffre ne privilégie aucun exécutant : il exige seulement qu'on en désigne
un, et que l'instance porte le nom `obsia-<name>`.

## Procédure

### 1. Lister — toujours en premier

Le registre :

```bash
ls IA/tâches/
grep -H -E '^(name|quand|fuseau|mode|actif):' IA/tâches/*.md
```

Puis les instances réelles sur cette machine :

```bash
systemctl --user list-timers --all 'obsia-*'
```

Si le harness a son propre planificateur, lister aussi de son côté — c'est la
moitié de l'inventaire qu'on oublie. Ne jamais créer avant d'avoir regardé les
deux : un doublon déclenche deux fois, et rien ne le signale.

### 2. Créer la tâche — patch Git

`IA/tâches/<nom>.md`, frontmatter conforme au §5 :

```yaml
---
schema: 1
kind: tâche
name: nom-de-la-tache
description: Une ligne — quoi, et à quel rythme.
mode: agent
quand: "0 9 * * 1"
fuseau: Europe/Paris
exécutant: local
agent: assistant
actif: true
---
```

Les guillemets autour de `quand` sont obligatoires : `*/15 * * * *` non quoté
est une ancre YAML invalide.

Puis le corps : `## Intention`, et `## Instruction` (mode agent) ou
`## Commande` (mode commande).

`IA/tâches/` n'est pas une zone d'écriture directe : patch soumis à revue.

### 3. Instancier — **à l'endroit déclaré, et nulle part ailleurs**

Lire `exécutant` avant de faire quoi que ce soit. `local` → la section
systemd ci-dessous. `harness` → la section suivante, et **rien** côté systemd.

**Timer systemd utilisateur** (`exécutant: local`) — deux fichiers dans
`~/.config/systemd/user/`.

`obsia-<nom>.service` :

```ini
[Unit]
Description=OBSIA — <description lisible>

[Service]
Type=oneshot
WorkingDirectory=%h/chemin/vers/OBSIA
ExecStart=/chemin/vers/la/commande
```

`obsia-<nom>.timer` :

```ini
[Unit]
Description=OBSIA — déclenche <description lisible>

[Timer]
OnCalendar=Mon *-*-* 09:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable --now obsia-<nom>.timer
```

`Persistent=true` rattrape un déclenchement manqué si la machine était éteinte.
Sans lui, une tâche hebdomadaire saute une semaine entière.

Pour qu'un timer survive à une déconnexion de session :
`loginctl enable-linger $USER`.

**Planificateur du harness** (`exécutant: harness`) — mêmes règles : nom
`obsia-<name>`, horaire converti dans le fuseau attendu (souvent UTC), et le
corps `## Instruction` recopié **tel quel**, sans le reformuler.

Si le harness courant n'a pas de planificateur, ne pas basculer en local
d'autorité : la tâche a été déclarée `harness` pour une raison. Le signaler,
et laisser trancher — changer `exécutant` est un patch, pas une improvisation.

### 4. Vérifier — avant d'annoncer quoi que ce soit

```bash
systemctl --user status obsia-<nom>.timer
systemctl --user start obsia-<nom>.service   # déclenchement à blanc
journalctl --user -u obsia-<nom>.service -n 30
```

Ne jamais affirmer qu'une tâche est créée sans l'avoir constaté. Si la commande
échoue, rapporter l'erreur telle quelle.

### 5. Modifier, suspendre, supprimer

| Geste | Registre | Instance |
| --- | --- | --- |
| changer l'horaire | patch sur `quand` | éditer le `.timer`, `daemon-reload`, `restart` |
| suspendre | `actif: false` | `systemctl --user disable --now obsia-<nom>.timer` |
| supprimer | archiver le fichier dans `.archive/` avant retrait | `disable --now`, puis archiver les deux unités |

Les deux vont toujours ensemble. Une instance désactivée mais restée `actif:
true` au registre sera ressuscitée à la prochaine réconciliation — et c'est le
comportement voulu : la suspension se déclare, elle ne s'improvise pas.

### 6. Réconcilier — après un changement de harness ou de machine

C'est la raison d'être du registre. Inventorier **tous** les exécutants avant
de conclure — systemd *et* le planificateur du harness. Une tâche jugée
« absente » parce qu'on n'a regardé qu'un seul côté, puis instanciée, devient
un doublon : c'est la réconciliation elle-même qui casse alors la règle.

| Écart | Lecture | Geste |
| --- | --- | --- |
| `actif: true`, aucune instance nulle part | cas normal après migration | instancier chez l'exécutant déclaré (étape 3) |
| `actif: true`, instance présente chez l'exécutant déclaré | rien à faire | ne pas toucher |
| **instance des deux côtés** | double déclenchement en cours | retirer celle qui n'est pas chez l'exécutant déclaré, puis vérifier qu'il n'en reste qu'une |
| instance présente, mais chez l'autre exécutant | déclaration et réalité ont divergé | soit déplacer l'instance, soit corriger `exécutant` par patch — jamais les deux à la fois |
| `actif: false`, instance présente | suspension jamais appliquée | désactiver l'instance |
| horaire divergent | le registre a raison | corriger l'instance |
| instance `obsia-*` sans tâche au registre | créée hors registre, ou renommée | retrouver l'intention, la déclarer, puis renommer l'instance |
| instance sans préfixe `obsia-` | ne vient pas du coffre | ne rien modifier, mais la **signaler une fois** : c'est peut-être une tâche à faire entrer au registre |

Afficher le tableau des écarts **avant** d'agir : c'est une action
multi-fichiers, le preview du §2 s'applique. Consigner ensuite les gestes
effectués dans le log de session (§9).

## Syntaxe de `quand`

Cron à 5 champs — `minute heure jour-du-mois mois jour-de-semaine` — parce que
c'est la seule notation que tous les exécutants comprennent ou savent traduire.

| Besoin | `quand` | `OnCalendar` systemd |
| --- | --- | --- |
| tous les jours à 10 h | `"0 10 * * *"` | `*-*-* 10:00:00` |
| chaque lundi à 9 h | `"0 9 * * 1"` | `Mon *-*-* 09:00:00` |
| toutes les heures | `"0 * * * *"` | `hourly` |
| le 1er de chaque mois | `"0 0 1 * *"` | `*-*-01 00:00:00` |
| en semaine à 18 h | `"0 18 * * 1-5"` | `Mon..Fri *-*-* 18:00:00` |

Vérifier l'expression systemd avant de l'utiliser :

```bash
systemd-analyze calendar "Mon *-*-* 09:00:00"
```

Deux pièges de conversion :

- **Le fuseau.** systemd suit l'horloge locale ; un planificateur distant
  raisonne le plus souvent en UTC. Convertir, et si le décalage franchit
  minuit, décaler aussi le jour de la semaine.
- **La fréquence minimale.** Beaucoup de planificateurs distants refusent en
  dessous de l'heure. Un besoin à la minute relève de systemd, pas d'eux.

## Rédiger l'instruction

Au déclenchement, il n'y a plus de conversation ni de contexte : ce que le
corps du fichier contient est tout ce que l'agent recevra.

| L'utilisateur dit | Mauvais message | Bon message |
| --- | --- | --- |
| « rappelle-moi de boire de l'eau » | Rappelle-moi de boire de l'eau | Envoie un rappel amical de boire de l'eau. |
| « résume l'actu IA le lundi » | Résume l'actu IA | Cherche l'actualité IA de la semaine écoulée et produis un résumé en puces. |
| « régénère les sommaires le soir » | Régénère les sommaires | Exécute `scripts/regenerate_sommaire.py` depuis la racine du coffre, puis rapporte les fichiers modifiés. |

Nommer les chemins, l'agent visé et le format de sortie attendu. Une
instruction qui suppose la conversation en cours ne se déclenchera jamais
correctement.

## Garde-fous

- Aucun secret dans une unité systemd ni dans un fichier de tâche : les deux
  se lisent en clair, et `IA/tâches/` est versionné dans un dépôt public.
- Une tâche déclenchée n'échappe à aucune règle du contrat : ce que l'agent
  n'a pas le droit de faire en conversation, il ne l'a pas davantage à 9 h le
  lundi.
- Avant de créer quoi que ce soit, se demander : est-ce que cette tâche
  tourne déjà quelque part ? Un doublon ne produit aucune erreur, il produit
  simplement deux fois l'effet — c'est la panne la plus discrète du lot.
- Ne pas redemander confirmation quand la demande a déjà été formulée.
- Confirmer en langage normal : nom de la tâche et horaire lisible, pas
  d'identifiant interne.
