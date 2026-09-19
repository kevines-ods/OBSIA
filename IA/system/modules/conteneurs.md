---
schema: 1
kind: module
name: conteneurs
description: Conteneurs et reverse proxy — état, journaux, volumes, réseaux, compose, labels de routage, certificats TLS.
essentiel: false
question: Héberges-tu des services en conteneurs, éventuellement derrière un reverse proxy ?
sondes:
  - commande:docker
  - commande:podman
requiert:
  - noyau
  - linux-poste
---

## Ce que ce module apporte

`conteneurs-docker` et `traefik`. Ils se renvoient l'un à l'autre selon la
couche où se situe le symptôme : le conteneur est mort, ou il répond mais pas
par son nom de domaine. Le renvoi n'a de sens que si les deux sont là.

## Pourquoi il dépend de `linux-poste`

Un conteneur qui ne démarre pas se diagnostique souvent une couche plus bas :
disque plein, service `docker` arrêté, port déjà pris. `conteneurs-docker`
renvoie à `diagnostic-linux` pour ces cas.
