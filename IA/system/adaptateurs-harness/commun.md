# Commun — les trois besoins et le bloc MCP

## Les trois besoins

| # | Besoin | Où ça vit dans OBSIA |
| --- | --- | --- |
| 1 | charger le cerveau | `CLAUDE.md` (racine du dépôt) ou prompt généré par `scripts/generer_prompt.py` |
| 2 | atteindre le coffre parent | racine du coffre = parent du dépôt (`../`) — §7 du contrat |
| 3 | connaître les repères | `IA/system/tags-du-coffre-parent.md`, `_maintenance/` du coffre parent |

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

## Vérification après branchement

Une conversation de test doit pouvoir : lister la racine du coffre (`..`),
lire une note de `../SAVOIRS/`, et retrouver le registre des tags.
