# AionUi / ObsiaUi (interface)

**Statut : vérifié sur documentation le 2026-09-14
(`https://github.com/iOfficeAI/AionUi/wiki/MCP-Configuration-Guide`) — jamais
éprouvé sur machine réelle.**

Interface de bureau qui **pilote d'autres agents en ligne de commande**. Elle
n'est donc pas un harness de plus à côté des autres : elle se place au-dessus.
Conséquence directe pour le branchement — les MCP se configurent **une fois
ici**, et l'interface les synchronise vers les agents qu'elle pilote, au lieu
d'un `mcp.json` par agent.

---

## 1. Où vit la configuration

Pas de fichier à éditer : la configuration se fait **par l'interface**,
`Réglages → Tools Settings → MCP Management`. Le stockage est du JSON encodé en
base64 dans le répertoire de configuration de l'utilisateur, sous la clé
`mcp.config` — lisible par le programme, pas fait pour être écrit à la main.

> **Ce que ça change pour le skill `configuration-mcp`.** C'est la seule fiche
> du dossier où l'agent **n'écrit pas de fichier**. Il prépare le JSON, et
> l'utilisateur le colle dans la boîte de dialogue. Le dire plutôt que chercher
> un fichier à écraser.

## 2. Le bloc MCP

Schéma `mcpServers` standard — celui de `commun.md` se colle tel quel.

```json
{
  "mcpServers": {
    "coffre-parent": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/chemin/absolu/vers/Mon coffre"],
      "env": { "LOG_LEVEL": "info" }
    },
    "git-hub": {
      "type": "streamable_http",
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": { "Authorization": "Bearer TOKEN" }
    }
  }
}
```

Types distants : `sse`, `http`, `streamable_http` (avec un souligné, à la
différence de LibreChat qui écrit `streamable-http`).

L'interface sait aussi **importer en un clic** la configuration MCP d'un agent
déjà installé qu'elle détecte. Voie la plus sûre quand un agent est déjà
branché : importer plutôt que ressaisir.

## 3. Secrets et variables

Aucune syntaxe d'interpolation documentée : l'exemple officiel écrit le jeton
en clair. **C'est incompatible avec le §4 du contrat.**

Conduite à tenir : ne pas déclarer ici les serveurs qui demandent un jeton
(`git-hub`, `obsidian`, `searxng` s'il est authentifié). Les laisser à l'agent
en ligne de commande, dont la fiche porte une vraie interpolation, et ne
confier à l'interface que `coffre-parent`, qui n'a besoin que d'un chemin.

Si l'interpolation existe malgré le silence de la documentation, cette section
se corrige — par patch, avec la source.

## 4. Restreindre un serveur à un agent

L'inverse du §10.2 : le modèle de l'interface est la **synchronisation vers
tous** les agents compatibles, pas le cloisonnement. Un serveur activé ici est
poussé vers ce qu'elle pilote.

Donc : ce qu'on déclare ici doit être ce que **tous** les agents pilotés ont le
droit d'avoir. Le reste se déclare agent par agent, dans leurs fiches
respectives.

Supprimer un service le retire de la gestion centrale et nettoie les
configurations synchronisées — mais un outil installé indépendamment peut
demander un nettoyage à part.

## 5. Charger le cerveau

L'interface ne charge pas de cerveau : chaque agent qu'elle pilote suit **sa
propre fiche** (`claude-code.md`, `opencode.md`, `openclaw.md`…). Le coffre ne
change pas.

Un agent en ligne de commande conforme ACP s'ajoute par
`Réglages → Agent Management → Custom Agents`.

## 6. Vérifier

Activer le serveur dans `MCP Management`, puis ouvrir une conversation avec un
agent piloté et faire un **appel réel** : lister la racine du coffre, y voir
`OBSIA/` et les dossiers en `-`.

Deux vérifications propres à cette fiche, parce que la synchronisation est le
mécanisme central :

- vérifier que le serveur apparaît bien **chez l'agent piloté**, pas seulement
  dans l'interface — c'est la synchronisation qu'on teste, pas la saisie ;
- après suppression d'un service, vérifier qu'il a bien disparu côté agent.

> Rappel §3 : OBSIA ne nomme aucune interface dans ses règles ; cette fiche est
> un gabarit d'intégration.
