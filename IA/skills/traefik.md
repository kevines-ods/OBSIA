---
schema: 1
kind: skill
name: traefik
description: Diagnostiquer Traefik — 404 et 502, labels, réseaux partagés, certificats TLS, service injoignable derrière le proxy. À charger dès qu'un service répond en direct mais pas par son nom de domaine. Si le conteneur lui-même est arrêté ou tué, commencer par `conteneurs-docker`.
type: outil
read_only: false
---

# Skill — Traefik

Reverse proxy de la VM Debian. Composant qui casse silencieusement : quand
Traefik échoue, il renvoie une erreur HTTP propre sans rien écrire d'évident
dans les journaux.

## Règles

1. **Diagnostiquer par la couche, du bas vers le haut.** Le service répond-il en
   direct ? Partage-t-il un réseau avec Traefik ? Ses labels sont-ils lus ? Le
   certificat est-il valide ? Dans cet ordre.
2. Ne jamais publier le tableau de bord Traefik sans authentification.
3. Ne jamais recopier dans le coffre : jeton d'API DNS, contenu de `acme.json`,
   noms de domaines internes.
4. `acme.json` doit être en `chmod 600`, sinon Traefik refuse de démarrer.

## Lire l'erreur

| Réponse | Signification | Où chercher |
| --- | --- | --- |
| **404** | Aucune règle ne correspond | Labels du conteneur, ou réseau non partagé |
| **502** | Règle trouvée, service injoignable | Le conteneur est arrêté, ou mauvais port |
| **503** | Aucun serveur sain disponible | Test de santé en échec |
| **Certificat invalide** | Let's Encrypt a échoué | Journaux ACME, DNS, limite de débit |
| **Délai dépassé** | Le service ne répond pas | Le conteneur tourne mais est bloqué |

Le 404 et le 502 se confondent souvent. Le 404 signifie que Traefik ne connaît
pas la route ; le 502 qu'il la connaît mais n'atteint pas la cible.

## Diagnostic par couche

### 1. Le service répond-il directement ?

```bash
docker exec <conteneur> wget -qO- http://localhost:<port>
```

S'il ne répond pas ici, le problème n'est pas Traefik.

### 2. Traefik voit-il le conteneur ?

```bash
docker logs traefik --tail 100 | grep -i "<nom-du-service>"
docker network inspect <réseau-traefik> | jq '.[0].Containers'
```

> **Cause numéro un des 404.** Traefik et le service doivent partager un réseau
> Docker. Un service sur son propre réseau isolé est invisible pour Traefik,
> sans aucun message d'erreur.

### 3. Les labels sont-ils corrects ?

```bash
docker inspect <conteneur> | jq '.[0].Config.Labels'
```

Structure minimale attendue :

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.monservice.rule=Host(`service.exemple.fr`)"
  - "traefik.http.routers.monservice.entrypoints=websecure"
  - "traefik.http.routers.monservice.tls.certresolver=letsencrypt"
  - "traefik.http.services.monservice.loadbalancer.server.port=8080"
```

Pièges fréquents :

- `traefik.enable=true` oublié alors que `exposedByDefault=false`
- Le nom du routeur (`monservice`) doit être identique partout
- `loadbalancer.server.port` est le port **interne** au conteneur, jamais le
  port publié sur l'hôte
- Les accents graves autour du domaine dans `Host(...)` sont obligatoires

### 4. Les certificats

```bash
docker logs traefik 2>&1 | grep -i acme
docker exec traefik ls -l /acme.json
```

Vérifier le certificat servi :

```bash
echo | openssl s_client -connect service.exemple.fr:443 2>/dev/null \
  | openssl x509 -noout -dates -issuer
```

> Let's Encrypt limite à **5 échecs par heure** et 50 certificats par domaine et
> par semaine. En cas d'échec répété, utiliser le serveur de test
> (`caServer: https://acme-staging-v02.api.letsencrypt.org/directory`) le temps
> de corriger, sinon le domaine est bloqué plusieurs heures.

Pour un domaine interne non exposé, le défi HTTP est impossible : il faut le
défi DNS, avec un jeton d'API du registrar. Ce jeton va dans un fichier `.env`
**hors dépôt**.

## Tableau de bord

```yaml
api:
  dashboard: true
  insecure: false          # jamais true en exposition
```

Accessible via un routeur protégé par authentification basique. `insecure: true`
ouvre le port 8080 sans mot de passe : acceptable seulement en local, jamais
au-delà.

## Configuration

```bash
docker exec traefik traefik version
docker logs traefik --tail 200 | grep -iE "error|warn"
```

Traefik ne recharge pas sa configuration statique à chaud : toute modification
de `traefik.yml` exige un redémarrage du conteneur. La configuration dynamique
(labels, fichiers) est relue automatiquement.

## Interaction avec le reste de l'infrastructure

- **Nextcloud** exige des en-têtes spécifiques et une valeur `overwriteprotocol`
  cohérente dans `config.php`, sinon les liens générés sont en HTTP derrière un
  proxy HTTPS.
- **Ollama** n'a pas d'authentification propre. L'exposer via Traefik sans une
  couche d'authentification, c'est offrir son GPU au premier venu.
- **Home Assistant** demande `use_x_forwarded_for` et `trusted_proxies` dans sa
  configuration, sinon il refuse les connexions passant par le proxy.

## Contraintes

`read_only: false`. Voir `../system/VAULT-CONTRACT.md`.
