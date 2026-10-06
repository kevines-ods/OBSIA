---
schema: 1
kind: mcp
name: searxng
description: Recherche web via une instance SearXNG auto-hébergée — méta-moteur qui interroge plusieurs moteurs sans tracer l'appelant. À charger pour le dernier étage de la cascade du skill `recherche`, quand le coffre et les sites de confiance n'ont pas la réponse.
module: recherche-web
type: tool
transport: stdio
permission: elevated
---

# MCP — SearXNG

Un serveur MCP branché sur une instance **SearXNG auto-hébergée**. SearXNG est
un méta-moteur : il interroge plusieurs moteurs, agrège les résultats, et ne
trace pas l'appelant. Le serveur expose la recherche à l'agent ; il ne stocke
rien.

Implémentation de référence : `ihor-sokoliuk/mcp-searxng`. D'autres serveurs
MCP SearXNG existent ; le nom du paquet et la commande de lancement dépendent de
celui que vous retenez, et l'entrée du gabarit est à ajuster en conséquence.

Gabarit de config prêt à copier : `IA/MCP/mcp.example.json`, entrée `searxng`,
où l'URL fictive est à remplacer par celle de votre instance.

## Ce que l'instance doit permettre

- **Le format JSON doit être activé** dans `settings.yml` de l'instance
  (`search.formats: [html, json]`). Il ne l'est pas par défaut : sans lui,
  l'API refuse les requêtes du serveur MCP.
- Pour une instance privée, le limiteur peut être coupé (`server.limiter:
  false`) : il n'exige alors ni valkey ni `limiter.toml`.
- Au démarrage, les moteurs du réseau Tor (`ahmia`, `torch`) échouent à se
  charger sans proxy Tor : c'est attendu, pas une panne.

Vérifié le 2026-09-28 avec `mcp-searxng` : quatre outils exposés —
`searxng_web_search`, `searxng_search_suggestions`, `searxng_instance_info` et
`web_url_read`, qui lit une page trouvée. Ce dernier sort lui aussi de la
machine : même prudence, même trace.

## Ce que cet outil sert à faire

Il porte le **dernier étage** de la cascade décrite par le skill `recherche` :
le web général. On ne l'appelle qu'après avoir épuisé le coffre parent et les
sites de confiance — c'est l'étage le plus bruité, et celui dont les résultats
demandent le plus de vérification.

C'est aussi une alternative à `chrome-devtools` quand il ne faut que **lire**
des résultats, sans piloter un navigateur.

## Quand le serveur répond vide — contournement

Constaté le 2026-10-05 : le serveur se connecte et annonce ses quatre outils,
l'instance répond, mais **certains harness rejettent chaque réponse** en
quelques millisecondes (« No result in tool call response ») — c'est le client
qui ne lit pas la réponse, pas l'instance qui manque. Un autre harness, sur la
même machine, obtient des résultats. Avant de conclure à une panne : tester la
connexion du serveur et une requête directe à l'instance.

En attendant que le harness soit corrigé, l'agent peut interroger l'instance
directement par son API JSON, **en lecture seule**. Poser d'abord
`SEARXNG_URL` — le nom du gabarit et du serveur — avec l'URL de la note
d'inventaire du coffre parent :

```sh
curl -sS --get "${SEARXNG_URL:?SEARXNG_URL non posée}/search" --data-urlencode "q=<requête>" \
  --data-urlencode "format=json" | python3 -c 'import json,sys
for r in json.load(sys.stdin)["results"][:5]: print(r["title"], r["url"], sep="\n  ")'
```

Une erreur de décodage JSON signale une réponse HTML : le format JSON n'est
pas activé sur l'instance (voir « Ce que l'instance doit permettre »).

Les règles de cette fiche s'appliquent à l'identique : même étage de la cascade,
même prudence sur le contenu de la requête, même ligne au carnet.

## Permissions

`permission: elevated`. L'outil sort de la machine : chaque requête part vers
l'instance SearXNG, qui interroge elle-même des moteurs tiers. C'est ce
caractère qui justifie le niveau.

## Où vit l'URL

Le harness lit sa configuration **au démarrage**, avant qu'un agent existe : le
coffre ne peut donc pas *fournir* l'URL — il la **conserve**. Deux endroits,
deux rôles, le motif du §12 (un registre décrit, une instance agit) :

| Où | Rôle | Ce qu'on y met |
| --- | --- | --- |
| la configuration du harness, hors dépôt | **l'instance** — ce que le serveur utilise pour démarrer | l'URL réelle |
| une note d'inventaire du coffre parent | **le registre** — ce qui existe, et où vit la configuration | l'URL, la machine, le chemin de la configuration |

L'URL est une **adresse interne**, pas un secret : une note du coffre parent la
porte sans difficulté. Un jeton, lui, n'entrerait pas dans une note (§4).

Les deux copies peuvent diverger — un port changé d'un seul côté ne se signale
nulle part. Après toute modification de l'instance, mettre à jour la note.
(Partager une valeur unique par lien symbolique est une autre voie, non traitée
ici.)

## Sécurité

- **L'URL de l'instance n'entre jamais dans `OBSIA/`.** Le dépôt est public, et
  une adresse interne n'y a pas sa place (§9). Elle vit dans la configuration du
  harness et dans la note d'inventaire du coffre parent (voir « Où vit l'URL »).
  `mcp.example.json` ne porte qu'une URL fictive.
- **Une instance auto-hébergée n'est pas pour autant privée** : SearXNG
  interroge des moteurs externes, qui voient la requête. Ne pas y mettre de
  contenu du coffre parent — ni un extrait de note, ni un nom de projet.
- **Consigner l'usage** : tout appel de ce serveur laisse une ligne au carnet
  (§9) — quoi, où, résultat. On y écrit la nature de la recherche,
  pas une URL interne.
- **Vérifier ce qu'on rapporte** : un résultat de moteur n'est pas une source.
  Citer l'URL réellement consultée, et distinguer l'évidence de
  l'interprétation (§8).
