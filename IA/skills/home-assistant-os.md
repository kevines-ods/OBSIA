---
schema: 1
kind: skill
name: home-assistant-os
description: Diagnostiquer et administrer Home Assistant OS — port de l'interface, observateur du Supervisor, accès SSH par l'add-on Terminal & SSH, clés posées par l'API Supervisor, mises à jour de Core. À charger quand Home Assistant ne répond pas, qu'il faut s'y connecter en SSH, ou avant toute mise à jour.
module: administration-homelab
type: outil
read_only: false
---

# Skill — Home Assistant OS

HAOS n'est ni un LXC ni une VM ordinaire : pas de `sshd`, souvent pas d'agent
QEMU, une console série réduite au `ha >` interactif. Ce qui passe pour une
panne ailleurs est souvent normal ici.

## Est-il vivant ?

1. **Le port de l'interface n'est pas forcément 8123** : il se change
   (`http.server_port`). Le lire dans `ha core info` (champ `port`) avant de
   conclure qu'un 8123 fermé est une panne.
2. **Sonde de vitalité : l'observateur du Supervisor sur `:4357`** —
   `curl -sS -m 5 http://<adresse>:4357/` → *Supervisor Connected / Supported /
   Healthy*. Il reste debout même si Core est arrêté : plus fiable que l'interface.
3. Après une mise à jour de Core, **l'interface reste fermée une à deux
   minutes** le temps du redémarrage.

## Accès SSH — l'add-on « Terminal & SSH »

- Installer l'add-on **ne le démarre pas** : « Démarrer », cocher « Démarrer au
  démarrage », vérifier que l'onglet **Réseau** expose `22/tcp`.
- `Connection refused` = add-on non démarré ou port non exposé ;
  `Permission denied` = clé refusée. Ce ne sont pas les mêmes pannes.
- Syntaxe : `ssh -p 22 root@<adresse>` — `ssh root@<adresse>:22` est invalide
  (*Could not resolve hostname*).

### Poser une clé

Les clés vivent dans **`/data/options.json`** de l'add-on ; `authorized_keys`
est **réécrit à chaque démarrage** depuis ce fichier, toute édition manuelle est
perdue. Méthode propre : l'API Supervisor, **depuis l'intérieur du conteneur de
l'add-on** (`$SUPERVISOR_TOKEN`, `curl` et `jq` y sont ; `python3` non) :

```bash
BASE=http://supervisor/addons/core_ssh          # pas de /api
HDR="Authorization: Bearer $SUPERVISOR_TOKEN"
curl -sS -H "$HDR" "$BASE/info" | jq -c '.data.options'                    # lecture
curl -sS -X POST -H "$HDR" -H 'Content-Type: application/json' \
     -d '{"options":{"authorized_keys":[…],"password":"","apks":[],"server":{"tcp_forwarding":true}}}' \
     "$BASE/options"                                                        # écriture
ha apps restart core_ssh                        # prise d'effet ; ~40 s avant que le port 22 réponde
```

- `GET /options` répond **405** : l'état se lit sur `/info`, seul le `POST` va
  sur `/options`. Le `POST` répond `{"result":"ok"}` sans renvoyer les options :
  relire `/info` pour vérifier.
- Envoyer toutes les options, pas seulement la clé : l'objet remplace l'ancien.
- Redémarrer l'add-on **coupe la session SSH en cours** : c'est attendu.
- Si la commande transite par un shell non-POSIX (`fish`) : écrire le script en
  local et le transférer en base64 plutôt qu'empiler trois niveaux de guillemets.

## CLI `ha`

- Depuis 2026.9, **`apps` remplace `addons`** (les deux répondent) :
  `ha apps start|stop|restart|info|logs|update`. Pas de sous-commande `options`.
- **`ha core update` est une tâche du Supervisor** : elle continue si le client
  SSH meurt, et n'écrit rien dans un journal redirigé. Suivre par
  `ha core info | grep '^version'` ou `ha jobs` (« Another job is running » = en cours).
- `ha core info` donne `version`, `version_latest`, `update_available`, `port`.

## Rationalisations

| Ce qu'on se dit | La réalité |
| --- | --- |
| « 8123 est fermé, Home Assistant est tombé » | le port a pu être changé ; l'observateur :4357 tranche |
| « je colle la clé dans `authorized_keys` » | elle disparaîtra au prochain démarrage de l'add-on |
| « l'add-on est installé, SSH doit marcher » | installé n'est pas démarré |
| « la mise à jour n'affiche rien, elle a échoué » | c'est une tâche du Supervisor ; interroger `ha jobs` |

## Contraintes

`read_only: false`. Voir `../system/VAULT-CONTRACT.md`. Le jeton du Supervisor
et les jetons longue durée sont des secrets : jamais affichés.
