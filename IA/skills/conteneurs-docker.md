---
schema: 1
kind: skill
name: conteneurs-docker
description: Diagnostiquer et gérer des conteneurs Docker — état, journaux, volumes, réseaux, compose.
type: outil
read_only: false
---

# Skill — Conteneurs Docker

Inspection et gestion des conteneurs de la VM Debian.

## Règles

1. **Les volumes sont les données. Les conteneurs sont jetables.** Cette
   distinction gouverne tout le reste : détruire un conteneur est anodin,
   toucher à un volume ne l'est jamais.
2. **`docker system prune` est interdit sans accord explicite.** Avec `-a
   --volumes`, il supprime des données. Toujours préférer une suppression ciblée.
3. Toute modification passe par le fichier `compose.yml`, jamais par une
   commande `docker run` improvisée — sinon l'état réel diverge du fichier
   versionné.
4. Ne jamais afficher le contenu d'un `.env` ni les variables d'environnement
   d'un conteneur dans une note du coffre : mots de passe et jetons y vivent.

## Constat

```bash
docker ps                                # conteneurs actifs
docker ps -a                             # y compris arrêtés — voir les codes de sortie
docker compose ps                        # dans le répertoire du projet
docker stats --no-stream                 # consommation instantanée
```

Codes de sortie utiles : `0` arrêt normal, `1` erreur applicative, `137` tué par
manque de mémoire (OOM), `143` arrêté proprement par SIGTERM.

> Un `137` répété signifie que le conteneur dépasse sa limite mémoire ou que
> l'hôte sature. C'est fréquent avec Ollama sur une VM sous-dimensionnée.

## Journaux

```bash
docker logs <conteneur> --tail 100
docker logs <conteneur> --since 1h
docker compose logs -f <service>
```

Un conteneur qui redémarre en boucle : lire les dernières lignes **avant**
chaque relance, c'est là qu'est l'erreur.

```bash
docker logs <conteneur> --tail 200 2>&1 | grep -iE "error|fatal|panic"
```

## Inspection

```bash
docker inspect <conteneur> | jq '.[0].State'
docker inspect <conteneur> | jq '.[0].Mounts'          # volumes montés
docker inspect <conteneur> | jq '.[0].NetworkSettings.Networks'
docker port <conteneur>
```

Entrer dans un conteneur pour investiguer :

```bash
docker exec -it <conteneur> sh
```

> Toute modification faite dans un conteneur disparaît à sa recréation. Utile
> pour comprendre, jamais pour corriger durablement — la correction va dans le
> `compose.yml` ou l'image.

## Volumes

```bash
docker volume ls
docker volume inspect <volume>
docker system df -v                      # taille réelle par volume et image
```

Trouver les volumes orphelins **sans les supprimer** :

```bash
docker volume ls -qf dangling=true
```

> Un volume « orphelin » peut simplement appartenir à un service arrêté
> temporairement. Vérifier avant, toujours.

## Réseaux

```bash
docker network ls
docker network inspect <réseau>
```

Deux conteneurs ne se voient que s'ils partagent un réseau. Ils s'adressent par
leur **nom de service**, pas par `localhost` : depuis Traefik, l'URL d'un
service est `http://nom-du-service:port`.

## Compose

```bash
docker compose config                    # valide et affiche la configuration résolue
docker compose up -d
docker compose down                      # arrête et supprime les conteneurs
docker compose down -v                   # ⚠ supprime AUSSI les volumes
docker compose pull && docker compose up -d
```

> `docker compose down -v` détruit les données. Ne jamais le proposer sans
> l'annoncer explicitement comme destructeur.

Valider avant d'appliquer :

```bash
docker compose config --quiet && echo "configuration valide"
```

## Cas propres à ton infrastructure

**Ollama** — modèles stockés dans un volume, plusieurs gigaoctets chacun.

```bash
docker exec ollama ollama list
docker exec ollama ollama ps             # modèles chargés en mémoire
```

Vérifier l'accès GPU si la VM en dispose :

```bash
docker exec ollama nvidia-smi
```

Sans GPU visible, l'inférence tourne sur processeur : très lente, mais
fonctionnelle. Ce n'est pas une panne.

**llama.cpp** — vérifier que le port du serveur est bien exposé et que le
fichier de modèle est monté en lecture seule.

**Traefik** — voir le skill dédié. Retenir ici que Traefik doit partager un
réseau avec chaque service qu'il expose, sinon il renvoie 404 sans erreur
explicite.

## Ménage sûr

Par ordre de risque, du plus anodin au plus dangereux :

```bash
docker container prune                   # conteneurs arrêtés — sûr
docker image prune                       # images sans tag — sûr
docker image prune -a                    # toutes les images inutilisées — retéléchargeables
docker volume prune                      # ⚠ DONNÉES — jamais sans accord explicite
docker system prune -a --volumes         # ⚠⚠ tout à la fois — à éviter
```

## Contraintes

`read_only: false`. Preview avant toute action destructive, archivage avant
écrasement. Voir `../system/VAULT-CONTRACT.md`.
