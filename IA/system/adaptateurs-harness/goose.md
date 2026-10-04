# Goose

**Statut : vérifié sur documentation le 2026-09-30
(<https://goose-docs.ai/docs/guides/context-engineering/using-goosehints>,
<https://goose-docs.ai/docs/getting-started/using-extensions>,
<https://goose-docs.ai/docs/guides/recipes/recipe-reference>,
<https://goose-docs.ai/docs/guides/environment-variables> et
<https://goose-docs.ai/docs/guides/goose-cli-commands>) — jamais éprouvé sur
machine réelle.**

Agent local (Block), en ligne de commande comme en application. Deux choses le
rendent confortable ici : il lit **`AGENTS.md` tout seul**, et il résout les
`@` **dans `AGENTS.md`** — là où OpenCode, lui, ne les résout pas. Une chose le
rend exigeant : **sans l'extension Developer, les fichiers de contexte ne sont
pas utilisés du tout** — or elle est **activée par défaut**. Le §5 le dit en
tête, avant le reste ; la vérification du §6 ne sert qu'à confirmer qu'elle
n'a pas été désactivée.

---

## 1. Où vit la configuration

| Chemin | Portée |
| --- | --- |
| `~/.config/goose/config.yaml` | global — extensions, fournisseurs, réglages |
| `~/.config/goose/.goosehints` | contexte global |
| `AGENTS.md`, `.goosehints` | contexte local, au fil de l'arborescence |
| `~/.config/goose/secrets.yaml` | secrets, **quand le trousseau système est désactivé** |
| fichier de recette (`*.yaml`) | un agent complet : instructions, extensions, paramètres ; rangé où vous voulez, ou dans un dossier de `$GOOSE_RECIPE_PATH` |

Tout vit sous `~/.config/goose/` ou dans le coffre : **aucun fichier de
configuration n'entre dans le dépôt.** Le dossier de recettes, lui, peut vivre
dans le coffre parent — c'est du contenu, pas de la configuration, et il ne
contient alors que des chemins fictifs (§ règle d'or de `README.md`).

### `~/.config/goose/config.yaml`

Le schéma minimal, celui que `goose configure` écrit puis relit :

```yaml
extensions:
  coffre-parent:
    name: coffre-parent
    type: stdio
    cmd: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/chemin/absolu/vers/la/racine/du/coffre"]
    enabled: true
    timeout: 300
```

## 2. Le bloc MCP

La clé racine s'appelle **`extensions:`** — un **dictionnaire YAML**, pas une
liste. Ni `mcpServers`, ni `mcp_servers` : recopier le bloc de `commun.md` tel
quel ne passe pas ici.

| Clé | Rôle | Défaut |
| --- | --- | --- |
| `name` | nom affiché | le nom de la clé |
| `type` | `stdio`, `streamable_http`, `builtin`, `platform` | `stdio` |
| `cmd`, `args` | stdio — la commande et ses arguments | — |
| `uri` | `streamable_http` — l'adresse du serveur | — |
| `enabled` | charger au démarrage ou non | `true` |
| `timeout` | secondes d'attente d'un appel d'outil | 300 |
| `description` | texte libre | — |
| `envs`, `env_keys` | variables fixées, variables nommées (§3) | — |
| `client_id`, `client_secret_key`, `scopes` | OAuth d'un serveur distant (§3) | — |

Quatre gestes documentés, du plus rapide au plus durable :

```bash
goose configure              # Add Extension, Remove, Toggle
goose mcp fetch              # installer une extension par son nom exact
goose info -v                # voir ce qui est activé, et avec quelles variables
```

En session, `--with-extension` et `--with-builtin` n'activent une extension que
**pour cette session** :

```bash
goose session --with-extension "coffre:npx -y @modelcontextprotocol/server-filesystem /chemin"
goose session --with-builtin developer
```

Deux points qui évitent des surprises :

- **le nom compte** : sans `nom:` explicite, une extension lancée par `npx`
  s'appelle `npx`, et ses outils sont préfixés `npx__` — deux serveurs lancés
  par le même lanceur se marchent dessus. D'où le `coffre:` ci-dessus ;
- **les racines MCP sont transmises** : les extensions qui les comprennent
  voient d'elles-mêmes le répertoire de travail de la session. Utile pour la
  troisième voie du §7.6, inutile pour les deux premières.

## 3. Secrets et variables

| Besoin | Champ | Remarque |
| --- | --- | --- |
| nommer une variable attendue | `env_keys: ["GITHUB_TOKEN"]` | **la voie conforme au §4** : goose lit la valeur dans l'environnement, puis dans son trousseau |
| fixer une valeur | `envs: { CLE: "valeur" }` | la valeur est **écrite dans le fichier** — jamais un secret |
| OAuth d'un serveur distant | `client_id`, `client_secret_key`, `scopes` | `client_secret_key` est un **nom**, résolu comme `env_keys` |
| interpolation | `$VAR` / `${VAR}` | documentée **pour `client_id`** — ne pas la supposer ailleurs |

`env_keys` accepte aussi bien des secrets que de la configuration ordinaire
(une URL, un chemin). La résolution se fait dans cet ordre : **variable
d'environnement d'abord**, trousseau ensuite. Un démarrage de recette **ne
redemande rien** : si la valeur manque, l'extension échoue à l'initialisation
et le dit.

Le trousseau est celui du système ; s'il est désactivé, goose retombe sur
`~/.config/goose/secrets.yaml` — encore un fichier hors dépôt.

## 4. Restreindre un serveur à un agent

**Documenté, et c'est la traduction directe du §10.2.** L'agent, chez goose,
s'appelle une **recette** : un fichier YAML qui déclare ses extensions. Quand
une recette fournit un bloc `extensions:` explicite, **seules ces extensions
sont disponibles** — les extensions de plateforme habituelles (`summon`, le
département de sous-agents) ne sont pas ajoutées d'office. Un serveur déclaré
là n'existe donc que pour cet agent :

```yaml
title: Relecteur
description: Relit un texte sans rien pouvoir écrire.
instructions: Lis, cite, discute. Tu n'écris aucun fichier.
extensions:
  - type: stdio
    name: coffre-parent
    cmd: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/chemin/absolu"]
    env_keys: ["COFFRE_CHEMIN"]
    timeout: 300
    available_tools: ["read_text_file", "list_directory"]
```

| Dans le coffre | Côté harness |
| --- | --- |
| un fichier de `IA/agents/` | une recette, un fichier YAML |
| `read_only: true` (§5) | pas d'équivalent direct : c'est `available_tools` qui retire l'écriture, outil par outil |
| `mcp:` déclaré par l'agent (§10.2) | le bloc `extensions:` **de la recette**, et nulle part ailleurs |
| un skill de `IA/skills/` | extension **Skills** (activée par défaut) ou fichier ordinaire |
| `requiert` / `peut_requerir` | `available_tools`, et le choix de l'extension elle-même |

`available_tools` est le seul verrou fin : il **liste** ce que l'agent a le
droit d'appeler. Un serveur de fichiers monté sans lui ouvre l'écriture partout
où le serveur regarde — c'est la mise en garde du `README.md`, et elle vaut
ici mot pour mot.

## 5. Charger le cerveau

**⚠️ D'abord ceci : goose n'utilise les fichiers de contexte que si l'extension
`developer` est active — et elle l'est par défaut.** Elle est donc nécessaire,
mais acquise : les trois vérifications du §6 ne servent qu'à s'assurer qu'elle
n'a pas été désactivée.

Ensuite, goose cherche **deux noms de fichier** de contexte :

- le défaut documenté par la page des hints est `["AGENTS.md", ".goosehints"]` ;
  la table des variables d'environnement les cite dans l'autre ordre — les deux
  fichiers étant fusionnés, l'ordre ne change rien ;
- `CONTEXT_FILE_NAMES` remplace cette liste. C'est ainsi qu'on branche une
  convention d'un autre harness sans renommer ses fichiers. Mais `AGENTS.md` est
  déjà dans la liste par défaut : **rien à faire** pour le coffre.

Où goose les cherche :

1. **globalement**, dans `~/.config/goose/` ;
2. **localement**, dans le répertoire courant — et, **dans un dépôt Git**, en
   remontant du répertoire de travail jusqu'à la racine du dépôt. Les fichiers
   imbriqués sont chargés à mesure que goose touche les fichiers concernés.

Les deux portées s'appliquent en même temps ; **le local l'emporte en cas de
contradiction**. La racine du coffre parent n'étant pas un dépôt, la remontée
s'arrête au répertoire de travail : c'est exactement là que
`python3 scripts/installer.py --appliquer` a posé `AGENTS.md`. Lancé de la
racine du coffre, goose l'a.

**Bonne nouvelle, et c'est l'inverse d'OpenCode** : goose **résout** la syntaxe
`@`. Un `@0-SAVOIRS/README.md` dans un fichier de contexte fait insérer le
fichier dans le contexte immédiat. Le `@` de `CLAUDE.md` fonctionne donc ici tel
quel — au point qu'on peut y renvoyer plutôt que de recopier.

## 6. Vérifier

Les trois vérifications communes de `commun.md` d'abord : lister la racine du
coffre, lire une note de `Mon coffre/0-SAVOIRS/`, retrouver le registre des tags.
⚠️ écrire `./0-SAVOIRS`, jamais `0-SAVOIRS` nu.

Puis trois gestes propres à cette fiche :

```bash
goose info -v                 # version, chemins, variables, extensions activées
goose configure               # Toggle Extensions : ce qui est branché
goose session                 # puis, en session : « cite la règle d'unicité des noms »
```

1. `goose info -v` doit **montrer `developer` et les extensions du coffre** ;
2. `goose configure` → Toggle Extensions dit la même chose, en interactif ;
3. en session, faire **citer une règle du contrat** — pas seulement répondre
   « oui, j'ai bien lu ». Si la règle sort de travers, le contexte n'est pas
   arrivé : vérifier `developer` avant toute autre chose, puis le nom du
   fichier (`AGENTS.md` ou `.goosehints`), puis la portée.

## 7. Ce que cette fiche ne dit pas

- **Rien n'a tourné.** Statut « vérifié sur documentation », comme les autres.
- **L'ordre des deux noms par défaut n'est pas tranché** : les deux pages
  officielles ne le donnent pas de la même façon. Sans effet tant que les deux
  fichiers sont fusionnés — mais à ne pas recopier comme une vérité.
- **`available_tools` ne remplace pas un `read_only`.** Le coffre demande un
  agent en lecture seule ; goose demande de retirer des outils un par un. C'est
  plus fin, et plus facile à rater.
- **Le trousseau du système n'est pas décrit ici** : ce qu'il protège dépend de
  la machine, pas de goose.

## URLs sources

1. <https://goose-docs.ai/docs/guides/context-engineering/using-goosehints>
2. <https://goose-docs.ai/docs/getting-started/using-extensions>
3. <https://goose-docs.ai/docs/guides/recipes/recipe-reference>
4. <https://goose-docs.ai/docs/guides/goose-cli-commands>

> Le coffre ne dépend pas de ce harness ; cette fiche n'est qu'un gabarit
> d'intégration.
