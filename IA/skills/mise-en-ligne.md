---
schema: 1
kind: skill
name: mise-en-ligne
description: Empaqueter une application et la publier derrière le reverse proxy — image et compose, réseau partagé, labels de routage, secrets par variables d'environnement hors dépôt, sauvegarde des volumes vérifiée avant la première mise en ligne, retour arrière écrit d'avance, puis vérification réelle de l'URL. À charger pour publier une application neuve ou une nouvelle version. Pour réparer un service déjà en ligne, charger `conteneurs-docker` ou `traefik`.
type: outil
read_only: false
---

# Skill — Mise en ligne

Publier n'est pas démarrer un conteneur. Un conteneur `Up` peut ne répondre à
personne, répondre en clair, ou écraser des données qui n'avaient pas de
sauvegarde. Ce skill couvre l'écart entre « ça tourne chez moi » et « c'est
joignable, sauvegardé, et réversible ».

## Avant tout — la sauvegarde, si le service détient des données

Charger `sauvegardes` et **vérifier avant la première mise en ligne**, pas
après : la sauvegarde des volumes existe, elle est récente, et elle a été
restaurée au moins une fois ailleurs. Une sauvegarde jamais restaurée est une
hypothèse, pas une sauvegarde.

Un service sans données persistantes en est dispensé — le dire explicitement
plutôt que de sauter l'étape en silence.

## 1. Empaqueter

- Une image, construite depuis le dépôt, pas assemblée à la main sur l'hôte :
  ce qui n'est pas dans le dépôt ne se reconstruit pas.
- Un fichier compose **versionné**, qui déclare : l'image, les volumes
  **nommés** (pas des chemins d'hôte au hasard), le réseau partagé avec le
  proxy, et le port interne du service.
- Les secrets viennent d'un fichier d'environnement **hors dépôt**, référencé
  par le compose. Jamais une valeur en clair dans le fichier versionné (§3).

## 2. Router

Les labels de routage disent trois choses : le nom de domaine, le point
d'entrée, et le port interne à joindre. Les trois erreurs qui reviennent :

| Symptôme | Cause quasi certaine |
| --- | --- |
| 404 par le domaine, mais le service répond en direct | le conteneur n'est pas sur le réseau du proxy, ou la règle de domaine est mal écrite |
| 502 | le port déclaré dans les labels n'est pas celui que le service écoute |
| certificat absent ou invalide | le point d'entrée ou le résolveur de certificat n'est pas celui attendu |

## 3. Déployer — une action, puis sa vérification

Comme `remediation-linux` : on annonce, on exécute, **on vérifie**, puis
seulement on passe à la suivante. Dans cet ordre, parce que chaque étape
suppose la précédente :

```bash
docker compose up -d              # 1. démarrer
docker compose ps                 # 2. le conteneur est vivant, pas en redémarrage
docker compose logs --tail 50     # 3. il a fini de démarrer, sans erreur
curl -I http://localhost:<port>   # 4. il répond sur son port
curl -I https://<domaine>         # 5. il répond par son nom de domaine, en TLS
```

**L'étape 5 est la seule qui prouve quelque chose.** Un conteneur `Up` ne dit
rien de ce que voit un visiteur : c'est le code HTTP renvoyé par l'URL réelle
qui fait foi, lu et non supposé.

## 4. Le retour arrière — écrit avant de déployer

Avant la première commande, écrire la commande qui ramène à l'état d'avant :
version d'image précédente, ou arrêt et restauration du volume. La chercher
pendant que le service est cassé coûte le double.

## 5. Si ça rate

Ne pas deviner la couche — la déduire du symptôme :

- le conteneur est mort, redémarre en boucle, ou sature → `conteneurs-docker` ;
- le service répond en direct mais pas par son domaine → `traefik` ;
- le symptôme dépasse cette machine → c'est de l'infrastructure, et l'hôte de
  virtualisation reste en lecture seule.

## 6. Consigner

Une mise en ligne est une action à effet externe : une ligne dans le log de
session (§9) — quoi, où, résultat. Sans adresse interne, sans nom d'hôte, sans
identifiant : le dépôt est public.
