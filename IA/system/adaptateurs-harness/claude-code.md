# Claude Code

**Statut : vérifié sur documentation le 2026-09-14
(`https://code.claude.com/docs/en/mcp`) — jamais éprouvé sur machine réelle.**

Agent en ligne de commande calqué sur un répertoire de travail. C'est le seul
harness de ce dossier qui charge le cerveau **tout seul**, à condition d'être
lancé au bon endroit.

---

## 1. Où vit la configuration

Trois portées, qui ne se mélangent pas :

| Portée | Fichier | Partagée |
| --- | --- | --- |
| `local` (défaut) | `~/.claude.json`, sous `projects.<chemin>.mcpServers` | non |
| `project` | `.mcp.json` à la racine du projet | oui, par Git |
| `user` | `~/.claude.json` | non, mais vaut pour tous les projets |

Priorité : `local` > `project` > `user` > serveurs de greffon > connecteurs.
Le serveur est pris **en entier** à la source la plus prioritaire — les champs
ne fusionnent pas d'une portée à l'autre.

> **Pour OBSIA, écrire en portée `user` ou `local`, pas `project`.** Le dépôt
> ignore `.mcp.json` à dessein (cf. `.gitignore`) : une configuration remplie y
> porterait le chemin du coffre et des références de jetons. La portée
> `project` ne servirait donc qu'en local, sans le partage qui la justifie.

## 2. Le bloc MCP

Clé racine `mcpServers`. Types : `stdio`, `http`, `sse`, `ws`.

```json
{
  "mcpServers": {
    "coffre-parent": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "${OBSIA_COFFRE}"]
    },
    "git-hub": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": { "Authorization": "Bearer ${GITHUB_TOKEN}" }
    }
  }
}
```

En ligne de commande, sans éditer le fichier :

```bash
claude mcp add --transport http git-hub https://api.githubcopilot.com/mcp/ --header "Authorization: Bearer $GITHUB_TOKEN"
claude mcp add --transport stdio coffre-parent -- npx -y @modelcontextprotocol/server-filesystem "$HOME/Mon coffre"
```

Le `--` sépare la commande du serveur des arguments de `claude`.

## 3. Secrets et variables

`${VAR}` et `${VAR:-valeur par défaut}`, interpolés dans `command`, `args`,
`env`, `url` et `headers`. Une variable non définie et sans défaut laisse le
texte `${VAR}` tel quel, avec un avertissement — donc un serveur qui échoue
sans dire pourquoi si on ne lit pas l'avertissement.

`${CLAUDE_PROJECT_DIR}` désigne la racine du projet.

C'est ce qui permet de tenir le §4 sans effort : le jeton vit dans
l'environnement, le fichier ne porte qu'une référence.

## 4. Restreindre un serveur à un agent

**Pas de traduction directe.** Ce harness n'associe pas un serveur MCP à un
agent : ce qui est déclaré est disponible pour la session. Le §10.2 reste donc
une **consigne de prompt**, pas une règle du moteur — contrairement à d'autres
fiches de ce dossier, qui savent le rendre exécutoire.

Conséquence pratique : ne déclarer que les serveurs réellement utilisés par les
agents qu'on fait tourner ici, puisque rien ne les cloisonnera ensuite.

## 5. Charger le cerveau

Lancer la session depuis le dépôt (`cd .../OBSIA && claude`) : `CLAUDE.md` est
lu automatiquement, et importe le contrat et les index par `@IA/system/…`.

Contrepartie : le répertoire de travail est alors le dépôt, pas la racine du
coffre. Pour atteindre le coffre parent, ajouter sa racine comme répertoire
supplémentaire, ou déclarer `coffre-parent` (§7.6). Lancer depuis la racine du
coffre marche aussi, mais `CLAUDE.md` n'est plus chargé seul : il faut alors le
citer explicitement.

## 6. Vérifier

```bash
claude mcp list          # les serveurs configurés
claude mcp get coffre-parent
```

Puis, en session : `/mcp` pour l'état de connexion, et un **appel réel** —
demander la liste de la racine du coffre. Si `-SAVOIRS/` n'apparaît pas,
l'accès n'est pas donné.

Vérification du cerveau : demander à l'agent d'énoncer une règle qui n'existe
que dans `VAULT-CONTRACT.md`. S'il ne la connaît pas, `CLAUDE.md` n'a pas été lu.

> Le coffre ne dépend pas de Claude Code ; cette fiche n'est qu'un gabarit
> d'intégration.
