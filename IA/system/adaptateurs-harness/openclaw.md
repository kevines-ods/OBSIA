# OpenClaw

**Statut : vérifié sur documentation le 2026-09-14
(`https://docs.openclaw.ai/tools/mcp`, `https://docs.openclaw.ai/start/openclaw`)
— jamais éprouvé sur machine réelle.**

> « OpenClaw 2.0 » est un **alias de release** ; le paquet, lui, est versionné
> par date. Ne pas confondre l'alias et le numéro de paquet.

Assistant personnel autonome, pas un agent calqué sur un répertoire de travail :
il lit ses instructions et sa mémoire dans un **espace de travail** à lui. C'est
la différence qui structure toute l'intégration.

---

## 1. Où vit la configuration

`~/.openclaw/openclaw.json`.

L'espace de travail par défaut est `~/.openclaw/workspace`, où le harness crée
`AGENTS.md`, `SOUL.md`, `IDENTITY.md` et `USER.md`. Clés utiles :
`agents.defaults.workspace`, `agents.entries.<nom>.default`.

## 2. Le bloc MCP

Clé `mcp.servers` — **pas** `mcpServers`. Le bloc universel de `commun.md` est
donc à transposer, pas à recopier.

```json
{
  "mcp": {
    "servers": {
      "coffre-parent": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/chemin/absolu/vers/Mon coffre"],
        "toolFilter": { "include": ["read_*", "write_*", "search", "list_*"] }
      },
      "git-hub": {
        "url": "https://api.githubcopilot.com/mcp/",
        "transport": "streamable-http",
        "headers": { "Authorization": "Bearer ${GITHUB_TOKEN}" }
      }
    }
  }
}
```

Le transport se lit à la forme : `command` + `args` (+ `env`) pour stdio ;
`url` + `transport` (`streamable-http` ou `sse`) + `headers` pour HTTP.

En **node hébergé**, le même bloc vit sous `nodeHost.mcp.servers`.

Le fichier se pilote aussi sans l'éditer :

```bash
openclaw mcp add <nom>
openclaw mcp list
openclaw mcp show <nom>
openclaw mcp reload
```

## 3. Secrets et variables

La documentation des serveurs **ne documente pas** de syntaxe
d'interpolation, alors qu'un exemple officiel de node hébergé écrit
`${INTERNAL_MCP_TOKEN}` dans un en-tête. L'un des deux a tort, et on ne sait
pas lequel.

**Donc : vérifier avant d'écrire un jeton sous forme `${VAR}` ici.** Si
l'interpolation n'a pas lieu, l'en-tête partira littéralement et
l'authentification échouera — panne silencieuse côté configuration, visible
seulement au premier appel. Le §6 ci-dessous la rattrape. En attendant, un
serveur HTTP authentifié est le seul cas à ne pas brancher à l'aveugle.

## 4. Restreindre un serveur à un agent

`toolFilter.include` accepte des motifs à joker (`read_*`) et **restreint les
outils exposés** d'un serveur. C'est la traduction la plus fine du §10.2 de
tout ce dossier : on n'ouvre pas seulement les serveurs qu'un agent déclare, on
peut n'ouvrir que les outils dont il a besoin.

Cas d'usage direct : `coffre-parent` peut écrire partout alors que le §7.3
n'ouvre qu'une poignée de zones. `toolFilter` ne connaît pas ces zones — il
filtre par nom d'outil, pas par chemin — mais retirer les outils de
suppression et de déplacement réduit réellement ce qui est atteignable.

La documentation est explicite : « connecter un serveur ne contourne pas votre
politique ». Le filtre s'ajoute à la politique d'outils, il ne la remplace pas.

## 5. Charger le cerveau

Le harness lit ses instructions dans son espace de travail, pas dans le dépôt.
Deux voies :

- pointer `agents.defaults.workspace` sur un dossier qui contient le cerveau
  généré (`python3 scripts/generer_prompt.py -o prompt-systeme.md`) ;
- ou reprendre le contenu dans `SOUL.md` / `AGENTS.md` de l'espace de travail.

⚠️ **Ne pas dupliquer les skills OBSIA dans les skills du harness.** Le coffre
reste la source de vérité (§5) ; deux exemplaires divergent à la première
correction, et rien ne le signale (§11).

La documentation conseille de faire de l'espace de travail un dépôt git privé.
Bonne idée en soi — mais il porte alors `USER.md` et la mémoire de l'assistant :
**privé au sens strict**, jamais poussé à côté d'OBSIA qui est public (§7.2).

## 6. Vérifier

```bash
openclaw mcp doctor <nom> --probe    # connecte et liste les outils annoncés
openclaw mcp status --verbose
```

`doctor --probe` est exactement ce que le §6 du skill `configuration-mcp`
demande : il **connecte** et énumère, au lieu de constater l'absence d'erreur.
C'est le seul harness du dossier à fournir cette commande.

Puis un appel réel : lister la racine du coffre, y voir `OBSIA/` et les
dossiers en `-`.

> Le coffre ne dépend pas d'OpenClaw ; cette fiche n'est qu'un gabarit
> d'intégration.
