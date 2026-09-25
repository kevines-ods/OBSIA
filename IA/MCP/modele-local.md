---
schema: 1
kind: mcp
name: modele-local
description: Confier une tâche simple à un modèle local servi par une API compatible OpenAI (llama-server, llama-swap, Ollama) — le modèle ne reçoit que la consigne et le contenu transmis, sans fichier ni outil. À charger avant d'appeler `deleguer`, avec le skill `delegation-locale`.
module: modeles-locaux
type: tool
transport: stdio
permission: elevated
---

# MCP — Modèle local

Un serveur MCP minimal qui relaie une consigne vers un modèle local et rend sa
réponse en texte. Code : `IA/skills/delegation-locale/scripts/mcp_modele_local.py`,
bibliothèque standard seule.

Gabarit de config prêt à copier : `IA/MCP/mcp.example.json`, entrée
`modele-local`, où le chemin, l'adresse et le nom du modèle sont fictifs.

## L'outil exposé

`deleguer` — un seul outil :

| Argument | Rôle |
| --- | --- |
| `consigne` | l'instruction, auto-suffisante (obligatoire) |
| `contenu` | la matière à traiter |
| `format` | `texte` ou `json` — `json` contraint la sortie à un objet valide |
| `max_tokens` | longueur maximale de la réponse (512 par défaut, plafond 4096) |
| `reflexion` | raisonnement du modèle, désactivé par défaut |

La réponse se termine par un pied qui donne la durée, les tokens, et les
alertes : réponse tronquée, vide, JSON invalide, tâche refusée.

## Permissions

`permission: elevated`. Le serveur fait un appel réseau, et l'adresse
configurée peut désigner une autre machine que celle de l'agent : le contenu
transmis sort alors du poste. Le serveur, lui, n'écrit rien et n'expose au
modèle ni fichier ni outil — c'est ce qui rend la délégation sûre pour le
coffre.

## Règles d'usage

- **Charger `delegation-locale` avant d'appeler** : il dit quoi déléguer,
  comment rédiger la consigne, et comment relire.
- **Le résultat ne s'écrit jamais tel quel** : l'agent le contrôle contre la
  source, puis écrit lui-même selon le §7.
- **Consigner l'usage** : une ligne par appel dans le log de session (§9).

## Sécurité

- L'adresse du serveur et le nom du modèle vivent dans la configuration du
  harness (`OBSIA_LOCAL_URL`, `OBSIA_LOCAL_MODEL`), jamais dans le dépôt : ce
  sont des valeurs de machine (§13.5).
- Pointer uniquement vers un serveur sous le contrôle de l'utilisateur. Une
  API tierce ferait sortir le contenu du coffre parent — `-PERSONNELS/`
  compris.
- Aucune clé n'est prévue : un serveur local ne devrait pas en demander. S'il
  en exige une, elle passe par une variable d'environnement, jamais en clair.

## Pièges connus

- **Modèle à raisonnement** : sans `reflexion: false`, un modèle qui pense
  avant de répondre peut épuiser `max_tokens` et rendre une réponse vide. Le
  serveur coupe le raisonnement par défaut (`enable_thinking`), ce qui suppose
  un gabarit de conversation qui le respecte (`--jinja` sur llama-server).
- **Passerelle multi-modèles** (llama-swap, Ollama) : `OBSIA_LOCAL_MODEL` est
  obligatoire, et appeler un modèle peut en décharger un autre de la mémoire —
  avec son cache.
- **Nœud CPU** : la lecture du contenu domine le temps d'appel. Transmettre
  un extrait plutôt qu'une note entière.
