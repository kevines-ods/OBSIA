---
schema: 1
kind: mcp
name: searxng
description: Recherche web via une instance SearXNG auto-hébergée, et lecture du texte d'une page (hors instance) — méta-moteur qui interroge plusieurs moteurs sans tracer l'appelant. À charger pour le dernier étage de la cascade du skill `recherche`, quand le coffre et les sites de confiance n'ont pas la réponse.
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

## Quand le client MCP échoue ou décale une réponse — contournement

Constaté le 2026-10-05, cause établie le 2026-10-07 avec `mcp-searxng` 2.5.1 :
le serveur se connecte et annonce ses outils, l'instance répond, et pourtant les
appels d'outil échouent — parfois en quelques millisecondes — sur
« No result in tool call response », ou rendent le résultat d'une **autre**
requête. Ni l'instance ni le serveur ne manquent quoi que ce soit : tout dépend
du **client MCP du harness**, qui peut ou non corréler une réponse à sa requête.
Un client qui les corrèle ne voit jamais le défaut ; un autre, sur la même
instance, peut donc travailler normalement.

Le serveur émet, aussitôt la requête reçue, des **notifications de
journalisation** (`notifications/message`), et ne produit sa réponse qu'une à
trois secondes plus tard. Un client qui prend la **première trame reçue** pour
sa réponse tombe sur une notification, n'y trouve pas de champ `result`, et rend
la main ; la réponse suivante, lue à l'appel d'après, **décale** le flux d'un
cran. C'est le cas dangereux : l'appel paraît réussir, et rend le résultat d'un
autre.

Quatre signes distinguent ce défaut d'une panne réelle :

- les échecs durent **0 à quelques millisecondes**, là où une recherche réelle
  prend une à trois secondes ;
- un appel qui « réussit » peut renvoyer les résultats d'une **autre** requête ;
- `initialize` et `tools/list` passent — ce sont les seuls appels qui ne
  déclenchent aucune notification ;
- l'instance interrogée directement par son API JSON répond normalement.

La correction appartient au harness, pas au coffre. En attendant, l'agent **peut
interroger l'instance** directement, **en lecture seule** — recherche comme
lecture d'URL, car `web_url_read` souffre du **même** défaut : c'est le serveur
qui journalise, quel que soit l'outil. Ces appels sortent en réseau : comme
toute exécution de code, ils relèvent du §4 — l'accès **se demande
explicitement** et s'exécute en sandbox, jamais implicitement. Poser d'abord
`SEARXNG_URL` — le nom du gabarit et du serveur — avec l'URL de la note
d'inventaire du coffre parent.

Pour constater le défaut soi-même, lancer ensuite le serveur à la main et lui
parler en JSON-RPC sur l'entrée standard : la réponse n'arrive **qu'après** les
trames de journalisation. `head -20` laisse à la réponse le temps d'arriver, et
stderr reste visible — le serveur y écrit ses erreurs.

```sh
# remplacer la commande entre chevrons par celle du gabarit
{ printf '%s\n' \
    '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"sonde","version":"1"}}}' \
    '{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}' \
    '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"searxng_web_search","arguments":{"query":"test"}}}' \
  ; sleep 6 ; } | <commande de lancement du serveur> | head -20
```

Un client qui apparie les trames par leur identifiant — ou qui ignore les
notifications — n'est pas concerné : c'est au harness de le faire.

Les deux appels directs — recherche, puis lecture de page — se font alors ainsi :

```sh
# rechercher
curl -sS --max-time 30 --get "${SEARXNG_URL:?SEARXNG_URL non posée}/search" \
  --data-urlencode "q=<requête>" --data-urlencode "format=json" | python3 -c 'import json,sys
for r in json.load(sys.stdin)["results"][:5]: print(r["title"], r["url"], sep="\n  ")'

# lire une page — équivalent de `web_url_read`
curl -sSL --max-time 30 --max-redirs 3 "<url>" | python3 -c 'import sys,html,re
t=sys.stdin.read()
t=re.sub(r"(?is)<(script|style|nav|footer|header)[^>]*>.*?</\1>"," ",t)
t=re.sub(r"(?s)<[^>]+>"," ",t)
print(re.sub(r"[ \t]+"," ",html.unescape(t)).strip())'
```

Ce `curl` rend le texte d'une page **HTML statique** : il n'exécute pas de
JavaScript, ne voit rien des pages construites côté navigateur, et perd titres,
tableaux et liens. Quand la mise en forme compte, ou que la page se construit
côté navigateur, préférer `chrome-devtools`, nommé plus haut, qui la lit comme
un navigateur.

`--max-redirs 3` borne les redirections, mais ne les rend pas sûres pour autant :
une page publique peut rediriger vers une adresse privée. Ne pas lire une URL
dont la cible n'est pas publique.

Une erreur de décodage JSON signale une réponse HTML : le format JSON n'est
pas activé sur l'instance (voir « Ce que l'instance doit permettre »).

Les règles de cette fiche s'appliquent à l'identique : même étage de la cascade,
même prudence sur le contenu de la requête, même ligne au carnet.

## Permissions

`permission: elevated`. L'outil sort de la machine : chaque requête part vers
l'instance SearXNG, qui interroge elle-même des moteurs tiers. C'est ce
caractère qui justifie le niveau.

**La lecture d'URL par `curl` sort hors de l'instance.** Contrairement à la
recherche, elle ne passe pas par SearXNG : c'est le poste qui contacte le site,
lequel voit donc son adresse et l'URL demandée — quand une recherche n'expose
aux moteurs que l'instance. Le dire dans la trace, et l'éviter pour une adresse
qu'on ne veut pas révéler au site.

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

- **L'URL de l'instance n'entre jamais dans `OBSIA/`.** Le privé fait foi et le
  public en dérive (§13) : une adresse interne écrite ici finirait publiée. Elle
  vit dans la configuration du harness et dans la note d'inventaire du coffre
  parent (voir « Où vit l'URL »). `mcp.example.json` ne porte qu'une URL fictive.
- **Une instance auto-hébergée n'est pas pour autant privée** : SearXNG
  interroge des moteurs externes, qui voient la requête. Ne pas y mettre de
  contenu du coffre parent — ni un extrait de note, ni un nom de projet.
- **Consigner l'usage** : tout appel de ce serveur laisse une ligne au carnet
  (§9) — quoi, où, résultat. On y écrit la nature de la recherche,
  pas une URL interne.
- **Vérifier ce qu'on rapporte** : un résultat de moteur n'est pas une source.
  Citer l'URL réellement consultée, et distinguer l'évidence de
  l'interprétation (§8).
