---
schema: 1
kind: skill
name: cron
description: Planifier des tâches récurrentes — créer, lister, modifier, supprimer un déclenchement horaire.
type: outil
read_only: false
---

# Skill — Tâches planifiées

> **Réécriture, pas traduction.** La version AionUi appelait
> `"$AIONUI_HELPER_BIN" config cron current ...`, un binaire propre à cette
> application qui n'existe pas dans OBSIA. Toute la couche d'exécution a donc été
> refaite sur **systemd user timers**, natif sur CachyOS et fonctionnant sans
> droits root. Les règles de conduite (une tâche par contexte, interroger avant
> de créer, message auto-suffisant) sont conservées : elles étaient bonnes.

## Règles

1. **Toujours lister l'existant avant de créer ou modifier.** Ne jamais créer en
   aveugle.
2. Ne pas redemander confirmation quand l'utilisateur a déjà formulé la demande.
3. Une tâche planifiée est une **action multi-fichiers différée** : le preview du
   contrat s'applique avant création (voir `../system/VAULT-CONTRACT.md`).
4. Ne jamais inscrire de secret dans un fichier d'unité systemd — ils sont
   lisibles en clair.
5. Si la commande échoue, rapporter l'erreur telle quelle. **Ne jamais affirmer
   qu'une tâche est créée sans l'avoir vérifiée.**
6. Confirmer en langage normal : nom de la tâche et horaire lisible. Ne pas
   afficher d'identifiants internes.

## Procédure

### Lister

```bash
systemctl --user list-timers --all
```

### Créer

Deux fichiers dans `~/.config/systemd/user/`.

`obsia-<nom>.service` :

```ini
[Unit]
Description=OBSIA — <description lisible>

[Service]
Type=oneshot
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

Activer :

```bash
systemctl --user daemon-reload
systemctl --user enable --now obsia-<nom>.timer
```

`Persistent=true` rattrape un déclenchement manqué si la machine était éteinte.

### Vérifier

```bash
systemctl --user status obsia-<nom>.timer
journalctl --user -u obsia-<nom>.service -n 30
```

### Modifier

Éditer le fichier `.timer`, puis `systemctl --user daemon-reload` et
`systemctl --user restart obsia-<nom>.timer`.

### Supprimer

```bash
systemctl --user disable --now obsia-<nom>.timer
```

Puis **archiver** les deux fichiers dans `.archive/` avant suppression, comme
l'exige le contrat.

## Syntaxe `OnCalendar`

| Besoin | Expression |
| --- | --- |
| tous les jours à 10h | `*-*-* 10:00:00` |
| chaque lundi à 9h | `Mon *-*-* 09:00:00` |
| toutes les heures | `hourly` |
| le 1er de chaque mois | `*-*-01 00:00:00` |

Vérifier une expression avant de l'utiliser :

```bash
systemd-analyze calendar "Mon *-*-* 09:00:00"
```

## Rédiger l'instruction déclenchée

Si la tâche envoie une instruction à un agent, cette instruction doit être
**complète et auto-suffisante** : au moment du déclenchement, il n'y a plus de
conversation, plus de contexte. Ne pas se contenter de reformuler la demande.

| L'utilisateur dit | Mauvais message | Bon message |
| --- | --- | --- |
| « rappelle-moi de boire de l'eau » | Rappelle-moi de boire de l'eau | Envoie un rappel amical de boire de l'eau. |
| « résume l'actu IA le lundi » | Résume l'actu IA | Cherche l'actualité IA de la semaine écoulée et produis un résumé en puces. |
| « régénère les sommaires le soir » | Régénère les sommaires | Exécute `scripts/regenerate_sommaire.py`, puis rapporte les fichiers modifiés. |

## Note sur l'agent assistant

Le fichier `IA/agents/assistant.md` déclare `cron` dans ses skills.
Cette dépendance pointe désormais vers **cette** version, pas vers celle
d'AionUi. Aucune modification du fichier agent n'est nécessaire, le nom est
identique.
