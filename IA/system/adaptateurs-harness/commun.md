# Commun — les trois besoins, le bloc MCP, et la forme d'une fiche

## Les trois besoins

| # | Besoin | Où ça vit dans OBSIA |
| --- | --- | --- |
| 1 | charger le cerveau | `CLAUDE.md` (racine du dépôt) ou prompt généré par `scripts/generer_prompt.py` |
| 2 | atteindre le coffre parent | racine du coffre = parent du dépôt (`../`) — §7 du contrat |
| 3 | connaître les repères | `IA/system/tags-du-coffre-parent.md`, `_maintenance/` du coffre parent |

## La forme d'une fiche — six sections, dans cet ordre

Le skill `configuration-mcp` (`../../skills/configuration-mcp.md`) **lit ces
fiches** pour savoir où écrire et sous quelle forme. Il ne devine pas : une
fiche qui n'a pas ces sections le laisse sans réponse, et il s'arrête.

| § | Titre | Ce qu'il doit donner |
| --- | --- | --- |
| 1 | Où vit la configuration | le **chemin exact** du fichier, et ses portées s'il y en a plusieurs |
| 2 | Le bloc MCP | la clé racine, et un exemple **stdio** et un exemple **HTTP** |
| 3 | Secrets et variables | la syntaxe d'interpolation, ou son absence |
| 4 | Restreindre un serveur à un agent | la traduction du §10.2, ou le constat qu'elle est impossible |
| 5 | Charger le cerveau | quel fichier est lu, et s'il l'est automatiquement |
| 6 | Vérifier | la commande ou le geste qui **prouve** que ça répond |

Chaque fiche ouvre sur un **statut** qui dit d'où vient l'information :

```
Statut : vérifié sur documentation le AAAA-MM-JJ (URL) — jamais éprouvé sur machine.
Statut : non vérifié — la documentation publique ne donne pas <ce qui manque>.
```

Un statut n'est pas décoratif. Il dit à l'agent s'il peut écrire une
configuration ou s'il doit demander — cf. la leçon
`nommage-verifie-a-la-source`, dans la mémoire du dépôt privé : un format
déduit d'une description est une hypothèse, et rien ne l'en distingue une fois
écrit.

## Bloc MCP universel — accès fichiers au coffre

La voie la plus portable pour donner accès au coffre parent : un serveur MCP
« fichiers » monté sur la **racine du coffre** (le dossier qui contient
`OBSIA/`). Bloc à recopier dans la configuration MCP du harness, le chemin
étant remplacé par le chemin réel (jamais versionné) :

```json
{
  "mcpServers": {
    "coffre-parent": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/chemin/absolu/vers/la/racine/du/coffre"
      ]
    }
  }
}
```

Toutes les fiches du dossier supposent ce bloc déclaré — ou l'équivalent :
ouvrir la racine du coffre comme dossier de travail.

`mcpServers` est la clé la plus répandue, pas une norme : plusieurs harness
attendent autre chose (`mcp.servers`, `mcpServers:` en YAML…). La section 2 de
chaque fiche tranche pour son harness.

## Vérification après branchement

Une conversation de test doit pouvoir : lister la racine du coffre (`..`),
lire une note de `Mon coffre/-SAVOIRS/`, et retrouver le registre des tags.

⚠️ Les dossiers du coffre commencent par `-`, donc par un caractère que les
commandes lisent comme le début d'une **option** : écrire `../-SAVOIRS`, jamais
`-SAVOIRS` nu (§7 du contrat).
