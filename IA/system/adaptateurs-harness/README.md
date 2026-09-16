# Adaptateurs harness — gabarits d'intégration

> **Statut : gabarits, non normatifs.** Les règles du coffre vivent dans
> `../VAULT-CONTRACT.md`, qui fait foi. Ce dossier recueille des **exemples
> d'intégration** : comment brancher un harness donné sur OBSIA et sur le
> coffre parent. Les noms de harness n'apparaissent qu'ici, dans les gabarits,
> jamais dans les règles — parce qu'un gabarit sert justement à brancher un
> outil précis.

## Pourquoi ce dossier

Le coffre décrit *quoi* faire, le harness fournit *avec quoi*. Ce qui est
portable (agents, skills, tâches, mémoire, registre des tags) vit dans OBSIA.
Ce qui ne l'est pas — la manière dont un harness précis accède au coffre — se
reconfigure à chaque changement de harness. Ces gabarits réduisent cette
friction à quelques minutes, sans faire dépendre OBSIA d'aucun harness.

## Les trois besoins communs (détail : `commun.md`)

1. **charger le cerveau** — prompt système / `CLAUDE.md` / index ;
2. **atteindre le coffre parent** — la racine du coffre (parent du dépôt),
   pas seulement `OBSIA/` ;
3. **connaître les repères** — racine du coffre, `_maintenance/`, registre des
   tags.

## Règle d'or

La **configuration réelle** (chemins, clés) vit **hors du dépôt**. Ces
gabarits ne contiennent que des chemins fictifs, à remplacer localement — un
gabarit rempli ne se re-versionne pas.

## Passer du gabarit au branchement réel

Ces fiches disent *où* la configuration vit pour chaque harness. Les traduire
en serveurs qui répondent vraiment est la procédure du skill
`configuration-mcp` (`../../skills/configuration-mcp.md`) : il ne configure que
les MCP qu'un agent déclare, garde les secrets en variables d'environnement, et
vérifie chaque serveur par un appel réel plutôt que par l'absence d'erreur au
démarrage.

## Fiches

Toutes suivent la **forme commune en six sections** définie par `commun.md` :
c'est elle que le skill `configuration-mcp` lit pour savoir où écrire.

| Fiche | Harness | Clé du bloc MCP | Secrets en `${VAR}` | Statut |
| --- | --- | --- | --- | --- |
| `claude-code.md` | Claude Code | `mcpServers` | oui, avec valeur par défaut | vérifié 2026-09-14 |
| `opencode.md` | OpenCode | `mcp` | oui | vérifié 2026-09-13 |
| `librechat.md` | LibreChat | `mcpServers` (YAML) | oui | vérifié 2026-09-14 |
| `openclaw.md` | OpenClaw | `mcp.servers` | **à confirmer** | vérifié 2026-09-14 |
| `aionui-obsiaui.md` | AionUi / ObsiaUi | `mcpServers`, saisi dans l'interface | **non** — jeton en clair | vérifié 2026-09-14 |
| `deepseek-harness.md` | DeepSeek Harness (DSH) | inconnue | inconnue | **non vérifié** |
| `pi.md` | Pi | **aucune** — pas de MCP intégré | sans objet — variables d'environnement | vérifié 2026-09-16 |

Trois choses que ce tableau rend visibles d'un coup d'œil, et qui décident du
branchement :

- **`mcpServers` n'est pas une norme.** Deux harness sur sept attendent une
  autre clé, et un n'en a aucune. Recopier le bloc de `commun.md` sans lire la
  fiche échoue en silence.
- **Deux fiches ne peuvent pas porter un jeton.** Sur AionUi la documentation
  écrit le secret en clair, ce que le §4 interdit ; sur OpenClaw
  l'interpolation n'est pas documentée. Les serveurs authentifiés s'y déclarent
  autrement, ou pas du tout.
- **Une fiche est vide, et le dit.** DSH n'a pas de configuration publiée :
  l'agent s'arrête au lieu d'écrire au hasard. Pi produit le même arrêt pour la
  raison inverse — sa configuration est documentée, mais elle n'a pas de MCP à
  remplir, et sa fiche le dit à la place de la clé.

Un statut « vérifié » signifie **vérifié sur documentation**, avec sa date et
sa source dans la fiche. Aucune n'a été éprouvée sur machine réelle ; c'est
écrit en tête de chacune, et ça ne se déduit pas d'un branchement qui a l'air
de marcher.
