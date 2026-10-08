# Codex

**Statut : vérifié sur documentation le 2026-09-30
(<https://learn.chatgpt.com/docs/agent-configuration/agents-md>,
<https://learn.chatgpt.com/docs/agent-configuration/subagents> et
<https://learn.chatgpt.com/docs/config-file/config-reference>) — jamais éprouvé
sur machine réelle.**

Agent d'OpenAI, en ligne de commande (`codex`) comme dans l'application. C'est
le premier harness de ce dossier pour qui `AGENTS.md` n'est pas une commodité
mais **le** moyen d'arriver avec le cerveau : Codex le lit d'emblée, et le
fichier que `python3 scripts/installer.py --appliquer` pose à la racine du
coffre est exactement là où il regarde.

Une limite chiffrée se paie comptant : Codex **coupe** ses instructions à
32 Kio par défaut, sans le dire. Le coffre mesuré le 2026-10-08 produit un
`AGENTS.md` de 26 628 octets, soit 81,3 % du plafond — la marge existe, elle
n'est pas confortable. Le §5 dit quoi mesurer, et quoi faire quand ça déborde.

---

## 1. Où vit la configuration

Tout vit sous le **répertoire d'accueil de Codex** — `~/.codex` par défaut,
déplaçable par la variable `CODEX_HOME` — donc **hors dépôt** par construction.

| Chemin | Portée |
| --- | --- |
| `~/.codex/config.toml` | global — serveurs MCP, agents, réglages |
| `.codex/config.toml` | projet — à la racine d'un projet |
| `~/.codex/AGENTS.override.md` | instructions globales, **prioritaires** sur `AGENTS.md` |
| `~/.codex/AGENTS.md` | instructions globales |
| `~/.codex/agents/<nom>.toml` | agents personnalisés, portée personnelle (§4) |
| `.codex/agents/<nom>.toml` | agents personnalisés, portée projet |

Un `.codex/` posé à la racine du coffre parent commence par un point :
Obsidian ne l'indexe pas, et la règle d'unicité des noms de notes (§6) n'est
pas touchée.

## 2. Le bloc MCP

La clé racine est une **table TOML**, `[mcp_servers.<nom>]` — et non
`mcpServers` : recopier le bloc de `commun.md` tel quel ne passe pas ici.

```toml
[mcp_servers.coffre-parent]
command = "npx"
args = [
  "-y",
  "@modelcontextprotocol/server-filesystem",
  "/chemin/absolu/vers/la/racine/du/coffre",
]
```

```toml
[mcp_servers.searxng]
url = "https://searxng.exemple.org/mcp"   # streamable HTTP
bearer_token_env_var = "SEARXNG_TOKEN"    # §3 : un nom, jamais un secret
```

| Clé | Rôle | Défaut |
| --- | --- | --- |
| `command`, `args`, `cwd` | stdio — la commande, ses arguments, son répertoire | — |
| `env`, `env_vars` | stdio — variables fixées, variables reprises de l'hôte | — |
| `url` | HTTP — l'adresse du serveur | — |
| `auth`, `bearer_token_env_var` | HTTP — authentification, jeton par variable | — |
| `http_headers`, `env_http_headers` | HTTP — en-têtes fixes ou pris dans l'environnement | — |
| `startup_timeout_sec` | délai de démarrage | 10 |
| `tool_timeout_sec` | délai par appel d'outil | 60 |
| `enabled`, `required` | charger ou non, échouer ou non si absent | `true`, `false` |
| `enabled_tools`, `disabled_tools` | liste blanche ou noire d'outils, **par serveur** | — |
| `default_tools_approval_mode` | approbation par serveur — valeurs acceptées : `auto`, `prompt`, `writes`, `approve` | — |
| `tools.<outil>.approval_mode` | même réglage, outil par outil | — |

Trois gestes documentés, qui évitent d'éditer le TOML à la main :

```bash
codex mcp add coffre-parent -- npx -y @modelcontextprotocol/server-filesystem /chemin
codex mcp list
codex mcp login searxng        # serveurs OAuth
```

En session interactive, `/mcp` liste ce qui est branché.

## 3. Secrets et variables

La documentation ne décrit **aucune interpolation `${VAR}`** dans
`config.toml` — on n'y écrit donc pas de secret (§4). Elle documente mieux :
des champs qui **nomment** la variable d'environnement sans jamais porter sa
valeur.

| Besoin | Champ |
| --- | --- |
| reprendre une variable de l'hôte (stdio) | `env_vars = ["GITHUB_TOKEN"]`, ou `{ name = "…", source = "…" }` |
| fixer une variable (stdio) | `env = { CLE = "valeur" }` — **pas pour un secret** |
| jeton d'un serveur HTTP | `bearer_token_env_var = "SEARXNG_TOKEN"` |
| en-tête HTTP pris dans l'environnement | `env_http_headers = { X-Api-Key = "API_KEY" }` |

## 4. Restreindre un serveur à un agent

**Documenté, et c'est la traduction directe du §10.2.** Un agent personnalisé
de Codex est un **fichier TOML** rangé dans `~/.codex/agents/` (ou
`.codex/agents/`). Codex le charge comme une **couche de configuration** : ce
que le fichier ne dit pas, il l'hérite de la session qui l'appelle — `model`,
`model_reasoning_effort`, `sandbox_mode`, `skills.config`, et `mcp_servers`.
Un serveur déclaré **dans le fichier de l'agent** n'existe donc que pour lui :

```toml
# ~/.codex/agents/relecteur.toml — trois champs obligatoires
name = "relecteur"
description = "Relit un texte sans rien pouvoir écrire."
developer_instructions = """
Lis, cite, discute. Tu n'écris aucun fichier.
"""

sandbox_mode = "read-only"          # read-only | workspace-write | danger-full-access
```

| Dans le coffre | Côté harness |
| --- | --- |
| un fichier de `IA/agents/` | un agent personnalisé par fichier TOML, déclaré à `~/.codex/agents/` |
| `read_only: true` (§5) | `sandbox_mode = "read-only"` |
| `mcp:` déclaré par l'agent (§10.2) | `[mcp_servers.<nom>]` **dans** le fichier de l'agent, et nulle part ailleurs |
| `model:`, effort de raisonnement | `model`, `model_reasoning_effort` |
| un skill de `IA/skills/` | déclaré par chemin dans `skills.config`, ou lu comme un fichier ordinaire |

Les trois champs `name`, `description` et `developer_instructions` sont
**obligatoires** ; un nom qui reprend celui d'un agent livré (`explorer`,
`worker`, `default`) l'emporte sur lui.

## 5. Charger le cerveau

Codex construit sa chaîne d'instructions **une fois par exécution**, dans cet
ordre de priorité :

1. **global** — dans le répertoire d'accueil, `AGENTS.override.md` s'il existe,
   sinon `AGENTS.md`. **Un seul** fichier non vide est retenu à ce niveau ;
2. **projet** — en partant de la racine du projet (le plus souvent la racine
   Git) et en **descendant** jusqu'au répertoire de travail. Dans chaque
   dossier : `AGENTS.override.md`, puis `AGENTS.md`, puis les noms de repli
   (`project_doc_fallback_filenames`). **Au plus un fichier par dossier** ;
3. **fusion** — les fichiers sont concaténés de la racine vers le répertoire de
   travail ; les plus proches passent en dernier, donc l'emportent.

**Sans racine Git, Codex ne regarde que le répertoire de travail.** C'est
exactement le cas du coffre : la racine du coffre parent n'est pas un dépôt.
Attention au chemin, donc : `scripts/installer.py --appliquer` n'écrit pas
l'`AGENTS.md` dans le dossier d'où on le lance, mais **un cran au-dessus de la
cible d'installation**, `cible.parent/AGENTS.md` — un chemin fixé par
l'emplacement du script ou par `--racine`, **jamais par le répertoire courant**
(`installer.py:330`). Et `--racine` désigne le dossier `OBSIA/`, **pas la
racine du coffre** (§13.4) : lui donner la racine du coffre enverrait
l'`AGENTS.md` un cran plus haut encore, là où Codex ne le lit pas. La règle se
lit donc ainsi : **lancer Codex depuis la racine du coffre**, et savoir qu'**il
ne lit rien** tant que l'installeur n'y est pas passé.

### ⚠️ Le plafond de 32 Kio

`project_doc_max_bytes` vaut **32768 octets** par défaut. Codex ignore les
fichiers vides et, dit la page, **« stops adding files »** dès que le total
atteint cette limite. Aucune page ne documente d'avertissement à ce
moment-là — l'agent ne le voit pas, et nous non plus. Notre lecture de « stops
adding files » : le surplus n'est pas coupé au milieu d'un fichier, il est
laissé de côté. Un `AGENTS.md` amputé reste un `AGENTS.md` valide — il décrit
simplement un coffre plus petit qu'il ne l'est.

Projection au 2026-10-08, mesurée sur la racine d'un coffre :

```bash
COFFRE=/chemin/vers/le/coffre          # la racine du coffre, quel que soit son nom
cd "$COFFRE/OBSIA"
python3 scripts/generer_prompt.py --sans-profil -o /tmp/agents-corps.md
wc -c /tmp/agents-corps.md     # 26 523 : le corps, plus le saut de ligne final
                               #   que la commande ajoute — l'installeur, lui,
                               #   n'en ajoute pas
wc -c "$COFFRE/AGENTS.md"      # 26 137 : le fichier écrit au profil courant
```

Le corps de l'`AGENTS.md` engendré au catalogue entier pèse donc 26 522 octets ;
l'installeur y ajoute un marqueur de 106 octets, soit **26 628 octets, 81,3 % du
plafond**. C'est le pire cas — le catalogue entier, celui que la CI et
`verifier_coffre.py` mesurent — et aucun `obsia.local.yml` ne peut y masquer un
dépassement : un profil ne fait que raccourcir le catalogue. Les 26 137 octets
du `AGENTS.md` installé à la racine du coffre parent sont ce que Codex lit
réellement ici, soit **79,8 %**.

Le chiffre bouge pour **deux** raisons : le catalogue, qui grandit, et la règle
des secrets du §4, reprise mot pour mot en tête du prompt (331 octets) — elle se
lit dans le contrat, elle n'est pas écrite dans le générateur, donc elle grandit
si le contrat grandit, et un test la tient courte. Pour le reste, le texte
engendré ne porte aucun chemin absolu — les deux racines y sont désignées
sans chemin, par le sous-dossier `OBSIA/` (§7.1) — donc deux postes, même à des
chemins et sous des noms différents, obtiennent des `AGENTS.md` de taille
**identique** : c'est ce qu'exige un fichier synchronisé entre eux. La marge se
réduit à chaque agent, skill ou tâche ajouté : un profil (`obsia.local.yml`) ne
fait que raccourcir le prompt, mais sans profil c'est le catalogue entier qui part.

**Quand ça débordera, deux réponses, dans cet ordre :**

1. **relever le plafond** dans `~/.codex/config.toml` — une ligne, hors dépôt :

   ```toml
   project_doc_max_bytes = 65536
   ```

2. **réduire le prompt** — un profil qui ne retient que les modules utiles
   (`obsia.local.yml`, §13.3 du contrat et annexe
   `../contrat/contrat-distribution.md`) est la réponse propre quand le coffre
   grandit. Découper sur plusieurs `AGENTS.md` de sous-dossiers ne s'applique
   pas ici : sans racine Git, Codex ne lit que le répertoire courant.

Ce plafond ne concerne **que** le chargement automatique. Un fichier nommé
autrement et lu à la demande n'y est pas soumis.

## 6. Vérifier

Les vérifications communes de `commun.md` d'abord (dont celle du secret) : lister la racine du
coffre, lire une note de `Mon coffre/0-SAVOIRS/`, retrouver le registre des tags.
⚠️ écrire `./0-SAVOIRS`, jamais `0-SAVOIRS` nu.

Puis trois gestes propres à cette fiche, chacun prouvant une chose différente :

```bash
COFFRE=/chemin/vers/le/coffre          # la racine du coffre, quel que soit son nom
cd "$COFFRE"
codex --ask-for-approval never "Résume les instructions que tu as chargées."
codex mcp list
wc -c "$COFFRE/AGENTS.md"
```

1. Codex doit **citer les règles du coffre**. S'il répond à côté, l'`AGENTS.md`
   n'était pas dans le répertoire de travail — ou son début a été mangé par le
   plafond ;
2. `codex mcp list` doit montrer les serveurs déclarés. Pour le détail de ce
   qui a été réellement chargé, `/mcp` en session ;
3. le troisième n'est pas décoratif : **tant que ce nombre tient sous 32 768,
   la question de la troncature ne se pose pas.** Au-delà, elle se pose, et
   `wc -c` est le seul moyen de le savoir avant que la réponse ne devienne
   étrange.

Pour auditer les sources d'instructions réellement lues, la documentation
donne deux voies : `codex -c log_dir=./.codex-log` puis lecture de
`./.codex-log/codex-tui.log`, ou les fichiers `session-*.jsonl` quand le
journal de session est activé.

## 7. Ce que cette fiche ne dit pas

- **Rien n'a tourné.** Le statut en tête est « vérifié sur documentation », et
  cela ne se déduit pas d'un branchement qui a l'air de marcher.
- **La mesure de taille est datée.** 26 628 octets le 2026-10-08, catalogue entier
  (26 137 octets pour le fichier réellement lu, profil appliqué). Elle ne dépend
  ni du poste ni du chemin — le texte engendré n'en porte aucun — mais elle
  vieillira quand même : la refaire avant de conclure.
- **Le format des agents personnalisés est assumé comme mouvant** par la
  documentation elle-même (« the format may evolve »). Le §4 est exact
  aujourd'hui ; ce n'est pas une promesse de stabilité.
- **La garde d'entreprise n'est pas traitée.** `mcp_servers` sert aussi de
  liste blanche verrouillable par une politique d'organisation — un
  déploiement qui l'active change la lecture du §2.

## URLs sources

1. <https://learn.chatgpt.com/docs/agent-configuration/agents-md>
2. <https://learn.chatgpt.com/docs/agent-configuration/subagents>
3. <https://learn.chatgpt.com/docs/config-file/config-reference>
4. <https://learn.chatgpt.com/docs/extend/mcp>
5. <https://agents.md>

> Le coffre ne dépend pas de ce harness ; cette fiche n'est qu'un gabarit
> d'intégration.
