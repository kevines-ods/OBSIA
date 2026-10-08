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

1. **charger le cerveau** — `AGENTS.md` / prompt système / `CLAUDE.md` / index ;
2. **atteindre le coffre parent** — la racine du coffre (parent du dépôt),
   pas seulement `OBSIA/` ;
3. **connaître les repères** — racine du coffre, `_MAINTENANCE/`, registre des
   tags.

## Atteindre le coffre parent — les trois voies

Le contrat (§7.6) pose le besoin et s'arrête là : le harness doit pouvoir
**lire et écrire dans la racine du coffre parent** — le dossier qui contient
`OBSIA/` —, pas seulement dans `OBSIA/`. Comment on le lui donne appartient à
ce dossier-ci. Trois voies, au choix du harness :

1. **ouvrir la racine du coffre comme dossier de travail** — la plus simple, et
   celle qui rend le serveur MCP inutile : un composant de moins à surveiller ;
2. **y ajouter les dossiers de connaissance** comme répertoires de travail
   supplémentaires, quand le harness sait en prendre plusieurs ;
3. **monter le serveur MCP « fichiers »** décrit par `../../MCP/coffre-parent.md`.
   Sa fiche donne ses permissions ; le gabarit de configuration vit dans
   `../../MCP/mcp.example.json`, entrée `coffre-parent`, à compléter du chemin
   réel.

La troisième voie porte un piège que les deux premières n'ont pas : **un
serveur de fichiers braqué sur la racine peut écrire partout**, alors que le
§7.3 du contrat n'ouvre qu'une poignée de zones. C'est la fiche du MCP qui
porte cette limite, pas le serveur — d'où l'obligation de la lire avant
d'appeler un de ses outils. Et comme tout MCP, celui-là n'est utilisable que
**déclaré par un agent**.

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
c'est elle que le skill `configuration-mcp` lit pour savoir où écrire — sauf
`opencode.md`, antérieure à cette forme, dont l'en-tête donne la correspondance
section par section.

| Fiche | Harness | Clé du bloc MCP | Secrets en `${VAR}` | Statut |
| --- | --- | --- | --- | --- |
| `claude-code.md` | Claude Code | `mcpServers` | oui, avec valeur par défaut | vérifié 2026-09-14 |
| `opencode.md` | OpenCode | `mcp` | oui | vérifié 2026-09-30 |
| `codex.md` | Codex | `mcp_servers` (TOML) | non — des **noms** (`env_vars`, `bearer_token_env_var`) | vérifié 2026-09-30 |
| `goose.md` | Goose | `extensions:` (YAML) | partielle — `client_id` ; préférer `env_keys` | vérifié 2026-09-30 |
| `librechat.md` | LibreChat | `mcpServers` (YAML) | oui | vérifié 2026-09-14 |
| `openclaw.md` | OpenClaw | `mcp.servers` | **à confirmer** | vérifié 2026-09-14 |
| `aionui-obsiaui.md` | AionUi / ObsiaUi | `mcpServers`, saisi dans l'interface | **non** — jeton en clair | vérifié 2026-09-14 |
| `deepseek-harness.md` | DeepSeek Harness (DSH) | **aucune** — une ligne de greffon par serveur | oui — `!!js process.env.X` | vérifié 2026-09-30, **sauf le §4** |
| `pi.md` | Pi | **aucune** — pas de MCP intégré | sans objet — variables d'environnement | vérifié 2026-09-16 |
| `vibe-work.md` | Vibe Work (Mistral, hébergé) | **aucune** — connecteurs posés par l'administrateur de l'espace | sans objet — OAuth côté plateforme (la doc cite aussi « aucun », « Bearer », « Basic ») | constat direct, 2026-10-07 |

Trois choses que ce tableau rend visibles d'un coup d'œil, et qui décident du
branchement :

- **`mcpServers` n'est pas une norme.** Trois harness sur dix l'utilisent ;
  quatre attendent une autre clé, deux n'en ont aucune, et DSH n'empile pas de
  clé du tout — une ligne de greffon par serveur. Recopier le bloc de
  `commun.md` sans lire la fiche échoue en silence.
- **Deux fiches ne peuvent pas porter un jeton.** Sur AionUi la documentation
  écrit le secret en clair, ce que le §4 interdit ; sur OpenClaw
  l'interpolation n'est pas documentée. Les serveurs authentifiés s'y déclarent
  autrement, ou pas du tout. Codex, Goose et DSH, eux, ont mieux qu'une
  interpolation : des champs ou une expression qui **nomment** la variable sans
  porter sa valeur (`env_vars`, `bearer_token_env_var`, `env_keys`,
  `!!js process.env.X`).
- **Deux fiches restent sans MCP, et le disent.** Pi n'a pas de MCP intégré ;
  Vibe Work, hébergé, n'expose aucun bloc configurable — l'utilisateur n'y
  pose pas de connecteur, l'administrateur de l'espace les fixe — et il ne
  peut pas non plus être lancé depuis la racine du coffre. Sa fiche décrit
  trois ponts vers le coffre parent (Google Drive, GitHub, prompt transposé)
  et dit ce qu'il ne faut pas lui demander : le pont GitHub ne porte que le
  dépôt `OBSIA/`, ni les notes du coffre ni l'`AGENTS.md`. L'agent s'arrête au
  lieu d'écrire au hasard. DSH n'était qu'un trou de documentation le
  2026-09-14 — sa fiche est remplie depuis le 2026-09-30, le §4 excepté.

Un statut dit **d'où vient l'information**, selon l'échelle de `commun.md` :
**vérifié sur documentation**, avec sa date et sa source dans la fiche ;
**constat direct**, écrit depuis le harness lui-même par le compte qui
l'utilise, ce que la documentation ne dit pas étant déclaré comme tel dans la
fiche ; **non vérifié**, quand la documentation publique ne donne pas ce qui
manque. Aucune n'a été éprouvée sur machine réelle ; c'est écrit en tête de
chacune, et ça ne se déduit pas d'un branchement qui a l'air de marcher.
