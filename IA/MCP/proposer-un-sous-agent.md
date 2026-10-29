---
schema: 1
kind: mcp
name: proposer-un-sous-agent
description: Proposer à l'utilisateur de confier une tâche — de lecture par défaut — à un sous-agent à contexte minimal — tâche, chemins à lire, version proposée — qui ne part qu'après sa validation dans OBSIA-UI et dont le compte rendu revient en réponse. À charger avant d'appeler `proposer_sous_agent`.
module: sous-agents
type: tool
transport: http
permission: elevated
---

# MCP — Proposer un sous-agent

Un outil servi par l'interface OBSIA-UI, pas par le coffre : l'interface lance
les agents, elle seule peut montrer la proposition et attendre une réponse. Le
coffre déclare l'outil ; l'interface le sert ; l'agent le consomme.

Gabarit de config : `IA/MCP/mcp.example.json`, entrée `proposer-un-sous-agent`,
où l'adresse est fictive et le jeton se lit dans l'environnement.

## L'outil exposé

`proposer_sous_agent` — un seul outil :

| Argument | Rôle |
| --- | --- |
| `tache` | ce que le sous-agent doit faire, auto-suffisant (obligatoire) |
| `chemins` | les fichiers ou dossiers du coffre à lire |
| `version` | la version d'agent proposée ; l'utilisateur peut la changer |

La réponse est le **compte rendu** du sous-agent — ou « refusé par
l'utilisateur », « arrêté par l'utilisateur », « délai dépassé ». L'appel reste
en attente tant que l'utilisateur n'a pas tranché.

## Permissions

`permission: elevated`. L'outil lance un agent, qui appelle un modèle et peut
faire sortir du poste le contenu qu'il lit. **Rien ne part sans validation** :
l'interface montre la tâche, les chemins, la version, ses MCP et son droit
d'écrire, et attend un clic.

Le sous-agent est **en lecture seule par défaut** : ses outils d'écriture sont
coupés au lancement. Une version peut l'autoriser à écrire ; il charge alors le
contrat, et ses écritures suivent le §7 comme celles de tout agent.

## Règles d'usage

- **Une tâche bornée, de lecture par défaut** : lire, chercher, résumer un lot
  de fichiers. Le sous-agent ne voit pas la conversation : la tâche dit tout.
  L'écriture n'est possible que si la version choisie l'autorise.
- **L'interface borne** : chemins sous la racine du coffre seulement, délai
  réglable au-delà duquel l'appel répond « délai dépassé ».
- **Le compte rendu ne s'écrit jamais tel quel** : l'agent appelant le
  contrôle contre la source, puis écrit lui-même selon le §7.
- **Un seul sous-agent à la fois** : une seconde proposition attend.
- **Consigner l'usage** : c'est l'**agent appelant** qui écrit, après la
  réponse, une ligne par appel au carnet — du chantier ou du jour, à défaut le
  journal de `_MAINTENANCE/` — (§9), refus compris ; le serveur n'écrit rien.
- **Qui le déclare** : les agents `read_only: false` qui travaillent depuis
  l'interface (`assistant`, `batisseur`). Un agent en lecture seule ne pourrait
  pas consigner l'appel.

## Sécurité

- Le jeton de l'interface vit dans l'environnement (`OBSIA_UI_TOKEN`), jamais
  dans le dépôt ni dans une note (§4).
- L'adresse est celle de l'interface sur la machine de l'utilisateur : une
  valeur de machine, hors dépôt (§13).
