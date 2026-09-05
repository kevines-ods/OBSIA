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

## Choisir l'exécutant

| Situation | Exécutant |
| --- | --- |
| `mode: commande` — une commande shell, aucun modèle requis | timer systemd utilisateur |
| `mode: agent`, machine allumée, harness lançable en ligne de commande | timer systemd qui appelle le harness |
| `mode: agent`, machine éteinte à l'heure dite, ou harness distant | planificateur du harness, s'il en a un |

Le coffre ne privilégie aucun exécutant. Le seul choix qu'il impose est le nom
de l'instance.

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

Si le harness a son propre planificateur, lister aussi de son côté. Ne jamais
créer avant d'avoir regardé les deux : un doublon déclenche deux fois.

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
agent: assistant
actif: true
---
```

Les guillemets autour de `quand` sont obligatoires : `*/15 * * * *` non quoté
est une ancre YAML invalide.

Puis le corps : `## Intention`, et `## Instruction` (mode agent) ou
`## Commande` (mode commande).

`IA/tâches/` n'est pas une zone d'écriture directe : patch soumis à revue.

### 3. Instancier

**Timer systemd utilisateur** — deux fichiers dans `~/.config/systemd/user/`.

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

**Planificateur du harness** — mêmes règles : nom `obsia-<name>`, horaire
converti dans le fuseau attendu (souvent UTC), et le corps `## Instruction`
recopié **tel quel**, sans le reformuler.

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

C'est la raison d'être du registre. Comparer les deux listes de l'étape 1 :

| Écart | Lecture | Geste |
| --- | --- | --- |
| tâche `actif: true`, aucune instance | c'est le cas normal après migration | instancier (étape 3) |
| tâche `actif: false`, instance présente | suspension jamais appliquée | désactiver l'instance |
| instance `obsia-*` sans tâche au registre | tâche créée hors registre, ou renommée | retrouver l'intention, la déclarer, puis renommer l'instance |
| horaire divergent | le registre a raison | corriger l'instance |
| instance sans préfixe `obsia-` | ne vient pas du coffre | ne pas y toucher |

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
- Ne pas redemander confirmation quand la demande a déjà été formulée.
- Confirmer en langage normal : nom de la tâche et horaire lisible, pas
  d'identifiant interne.
