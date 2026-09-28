---
schema: 1
kind: skill
name: surveillance-et-alertes
description: Mettre en place et dépanner la surveillance d'une infrastructure — sondes de disponibilité Uptime Kuma, moniteurs push, vérificateurs de fraîcheur des sauvegardes, alerte SMART, notification Telegram, témoin externe qui détecte une panne totale. À charger quand une alerte manque, arrive à tort, ou qu'une tâche importante tourne sans que personne ne sache si elle a réussi.
module: administration-homelab
type: outil
read_only: false
---

# Skill — Surveillance et alertes

Savoir, sans aller regarder, que ce qui doit tourner a tourné et que ce qui
doit répondre répond. Une alerte qui ne part jamais est aussi fausse qu'une
alerte qui part tous les matins.

## Choisir le bon dispositif

| Question | Dispositif |
| --- | --- |
| le service **répond-il** ? | sonde de disponibilité (HTTP, TCP, DNS, ping) |
| une tâche lancée par systemd **a-t-elle échoué** ? | hook `ExecStopPost` sur le service |
| une tâche qui **n'est pas** un service systemd (ordonnanceur de l'hyperviseur, tâche d'une interface de NAS) **a-t-elle produit son résultat** ? | **vérificateur de fraîcheur** : contrôler le résultat (snapshot récent, journal sans erreur), pas l'exécution |
| une tâche **n'est plus venue** depuis trop longtemps ? | moniteur *push* : la tâche envoie une pulsation, l'absence alerte |
| **tout** est tombé, supervision comprise ? | **témoin externe** hors de l'infrastructure |

Deux règles de décision, qui évitent les deux pannes les plus courantes :

- **Moniteur d'absence ou compte rendu de fin ?** Se demander : *la ressource
  est-elle censée être là au moment du contrôle ?* Oui → un moniteur *push*
  d'absence a du sens (il rappelle, par exemple, qu'un disque n'a pas tourné).
  Non (disque branché quelques heures par semaine, poste souvent éteint) → le
  moniteur est un **faux positif programmé** : envoyer plutôt un **compte rendu
  à chaque exécution réelle**.
- **Un moniteur *push* n'envoie jamais de « succès »** : il n'alerte qu'au
  changement d'état. Pour garder une trace datée des réussites, le script
  envoie son propre message.

Et une règle d'architecture : **la supervision hébergée sur la machine qu'elle
surveille se tait quand cette machine tombe.** Seul un témoin externe (service
de type *dead-man's switch*, pingé toutes les quelques minutes) voit une panne
totale.

## Écrire un vérificateur ou un script de compte rendu

1. **Trois modes, partout les mêmes** : sans argument = contrôle + pulsation +
   notification si nouveauté ; `dry` = diagnostic et message **exact** affichés,
   rien envoyé ; `test` = message d'essai réellement envoyé. Sans `test`, la
   chaîne de notification reste non prouvée jusqu'au premier vrai passage.
2. **Codes de sortie** : 0 sain, 1 anomalie (l'unité passe en échec et apparaît
   dans `systemctl --failed`), 2 mauvais argument.
3. **Construire le message une seule fois**, puis l'afficher (`dry`) ou
   l'envoyer : un `dry` qui s'arrête avant la fin valide un message plus court
   que le vrai.
4. **Icône** : ✅ seulement si le résultat est bon **et** récent ; une anomalie
   d'ancienneté porte ⚠️.
5. **Tâche en cours** (fin absente, bloc sans « terminé ») : pulsation `up` et
   sortie 0 — sinon on alerte sur une durée négative.
6. **Journal soumis à rotation** : lire le courant **et** `.1` (et `.gz`), garder
   le plus récent. La rotation doit alors utiliser `delaycompress` (et
   `copytruncate` si l'écrivain garde le fichier ouvert).
7. **`PATH` complet exporté** en tête de script : cron ne donne que
   `/usr/bin:/bin`, et un `smartctl` introuvable rend une variable vide qui
   déclenche une fausse alerte. Tester `-n "$var"` avant de comparer.
8. **Le script de notification sort toujours en 0** : une panne d'alerte ne doit
   jamais faire échouer la sauvegarde.

Banc de test hors production, avant tout déploiement : extraire le script du
déployeur (tester le code réellement installé), mettre un **faux `curl` en tête
de `PATH`**, rejouer succès, échec, absence et tâche en cours sur un **vrai
journal copié**, vérifier codes de sortie, pulsations et texte, puis relancer
pour tester le dédoublonnage.

## Hooks systemd

```ini
[Service]
ExecStopPost=/bin/sh -c 'if [ "$SERVICE_RESULT" = "success" ] && [ "$EXIT_STATUS" = "0" ]; then <script> up; else <script> down; fi'
```

- `$SERVICE_RESULT` et `$EXIT_STATUS` n'existent que dans les `ExecStop*` ;
  écrire `$EXIT_STATUS`, jamais `$$EXIT_STATUS`.
- Un service **sauté** par `ConditionPathExists=` n'exécute **aucune** directive
  `Exec*` : ni `ExecStopPost`, ni `OnFailure=`. Silence total — c'est le délai du
  moniteur *push* qui couvre ce cas.
- Un `ExecCondition=` qui sort en 1 rend le service « ignoré », pas « en échec »,
  et `ExecStopPost` ne s'exécute pas : si un message « rien à faire » est voulu,
  c'est la condition elle-même qui l'envoie.

## Uptime Kuma

- La base `kuma.db` (SQLite) **n'est relue qu'au démarrage** : pour toute
  écriture SQL — arrêter le conteneur, copier `kuma.db.backup.<date>`, écrire,
  redémarrer. `sqlite3` est souvent absent du conteneur hôte : passer par le
  module `sqlite3` de `python3`.
- **Une notification active mais liée à aucun moniteur ne sert à rien**, et
  l'interface l'accepte sans rien dire : vérifier la table `monitor_notification`.
- Ajouter un moniteur par SQL : **recopier une ligne existante**
  (`SELECT * FROM monitor WHERE id=<n>`) plutôt qu'inventer une dizaine de
  colonnes. Attendre 60 à 90 s avant de conclure : un moniteur qui naît `DOWN`
  envoie une vraie alerte.
- État d'un moniteur : `SELECT status,time,msg FROM heartbeat WHERE monitor_id=<id>`
  (`0` DOWN, `1` UP, `2` en attente, `3` maintenance).
- Un moniteur *push* neuf n'est évalué qu'à **création + intervalle** : sans
  pulsation, il n'est pas `DOWN` tout de suite.
- Retirer un moniteur : vérifier nom et type, **écrire un fichier de
  restauration** (l'`INSERT` reconstruit), puis purger toutes les tables qui
  portent `monitor_id` — **en citant les noms** : l'une d'elles s'appelle
  `group`, mot réservé (`DELETE FROM "%s" WHERE monitor_id=?`).
- En version 1.23, le type de notification et **son jeton** sont dans le JSON
  `notification.config` : n'en lire que les noms de champs.

## Santé des disques

- **Une seule source de vérité SMART.** Deux outils sur les mêmes disques font
  deux alertes pour une panne — et l'un des deux finit par ne plus rien collecter
  sans que personne ne le voie.
- Alerter aussi sur un disque **absent**, **illisible** ou dont l'état **n'est
  pas rapporté** — pas seulement sur « différent de `PASSED` ».
- Avant de conclure qu'un outil ne voit pas un disque, **vérifier où il est
  réellement installé** : un collecteur posé sur l'hôte et non dans le conteneur
  change tout le diagnostic.

## Secrets de notification

- Jeton de bot et identifiant de discussion dans un fichier `600 root`
  (`/etc/<outil>.env`), chargé par le script — jamais dans le script ni dans la
  conversation. Contrôle sans affichage : `sed -E 's/=.*/=<masque>/' <fichier>`.
- Copier un secret d'une machine à l'autre sans le voir :
  ```bash
  ssh source 'cat /etc/a.env' | ssh cible 'umask 077; cat > /etc/b.env'
  ```
  puis comparer les `sha256sum` des deux fichiers.
- Jamais de `status=down` poussé « pour voir » sans prévenir : c'est une vraie
  alerte chez l'utilisateur.
- Témoin externe Healthchecks.io : l'adresse à pinger est la **Ping URL**
  (`https://hc-ping.com/<uuid>`, onglet *Integrations*), pas l'adresse de badge
  qui finit en `.svg`.

## Rationalisations

| Ce qu'on se dit | La réalité |
| --- | --- |
| « la notification est configurée, donc les alertes partent » | une notification liée à aucun moniteur ne part jamais |
| « pas de message, donc tout va bien » | un service sauté par une condition ne dit rien ; une supervision tombée non plus |
| « le mode `dry` suffit comme test » | il n'atteint jamais `curl` : la chaîne d'envoi reste non prouvée |
| « je mets un moniteur d'absence, par sécurité » | sur une ressource souvent absente, il alertera à tort chaque semaine, et on apprendra à l'ignorer |
| « le script a marché à la main » | cron n'a pas le même `PATH` que le shell |

## Contraintes

`read_only: false`. Voir `../system/VAULT-CONTRACT.md`. Identifiants de
moniteurs, adresses et jetons vivent dans l'inventaire du coffre parent, jamais
dans le dépôt.
