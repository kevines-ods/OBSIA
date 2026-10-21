# Vibe Code CLI

**Statut : documentée, non éprouvée — vérifié sur documentation le 2026-10-10
(<https://docs.mistral.ai/vibe/code/cli/install-setup>,
<https://docs.mistral.ai/vibe/code/cli/agents>,
<https://docs.mistral.ai/vibe/code/cli/mcp-servers>,
<https://docs.mistral.ai/vibe/code/cli/skills> et
<https://docs.mistral.ai/vibe/code/safety-approvals-permissions>). Aucun essai sur
machine réelle : le branchement décrit ici n'a pas été lancé, seule la
documentation publique a été lue.**

Agent de Mistral **en ligne de commande** (`vibe`), distinct de l'agent hébergé
décrit par [`vibe-work.md`](vibe-work.md). Ce qui change tout : il a un **dossier
de travail** — il lit donc un `AGENTS.md` à l'ouverture — et un `config.toml` sur
le disque. C'est le harness qui se rapproche le plus du §7.6 du contrat, à une
réserve près (le chargement de `AGENTS.md` passe par une approbation de dossier,
§5 ci-dessous).

Cette fiche reste un **gabarit d'intégration**, pas une recommandation : le coffre
ne choisit aucun harness (`../VAULT-CONTRACT.md` §3). Nommer le produit sert à
l'installer, jamais à conditionner une règle.

## 1. Où vit la configuration

Tout se règle dans le **répertoire d'accueil de Vibe**, `~/.vibe/` — déplaçable par
la variable `$VIBE_HOME` (agents : « `~/.vibe/AGENTS.md` — or in `$VIBE_HOME` if
you set it »).

| Chemin | Portée |
| --- | --- |
| `~/.vibe/config.toml` | global — serveurs MCP, agent par défaut, outils, skills |
| `~/.vibe/agents/<nom>.toml` | agents, portée utilisateur |
| `~/.vibe/prompts/<id>.md` | prompts système visés par `system_prompt_id` |
| `~/.vibe/skills/` | skills, portée utilisateur |
| `~/.vibe/AGENTS.md` | instructions chargées à l'ouverture, portée utilisateur |
| `~/.vibe/trusted_folders.toml` | dossiers approuvés (§5) |
| `./.vibe/` | config de projet — agents, skills, prompts, hooks, tools |
| `./.agents/skills/` | skills de projet, standard « Agent Skills » |

Le fichier global est créé **au premier lancement** — « Creates a default
configuration file at `~/.vibe/config.toml` if it does not already exist »
(install-setup). Ce dossier commence par un point : hors des notes, il ne se
retrouve pas dans le coffre et n'a rien à y ignorer.

La clé d'API se range là aussi, par l'assistant de configuration — « the wizard
saves it for future sessions in the Vibe home directory » — ou dans
l'environnement, par `MISTRAL_API_KEY` (install-setup). Une clé d'API saisie à
la main est facturée **à l'usage** ; pour passer par un abonnement, voir le §7.

## 2. Le bloc MCP

La clé racine est un **tableau de tables TOML**, `[[mcp_servers]]`, à ajouter à
`config.toml` (mcp-servers) : le bloc `mcpServers` de `commun.md` ne se recopie
pas tel quel ici.

Les transports documentés sont `http`, `streamable-http` et `stdio` ; les champs
communs sont `name`, `transport`, `url`, `command` / `args`, `headers`,
`api_key_env`, `env`, `startup_timeout_sec` et `tool_timeout_sec` (mcp-servers,
« Common fields »). Un processus local et un serveur distant :

```toml
# processus local (stdio) — le cas du serveur « fichiers » du coffre
[[mcp_servers]]
name = "coffre-parent"
transport = "stdio"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-filesystem",
        "/chemin/absolu/vers/la/racine/du/coffre"]
```

```toml
# HTTP — la clé n'est jamais écrite ici : trois champs la désignent sans
# l'écrire (§3) — `api_key_env` nomme la variable qui la porte,
# `api_key_header` dit où la placer, `api_key_format` sa mise en forme.
[[mcp_servers]]
name = "searxng"
transport = "http"
url = "https://searxng.exemple.org/mcp"
```

Les outils d'un serveur s'exposent sous `{server_name}_{tool_name}` (mcp-servers,
« Tool naming and permissions » ; safety-approvals-permissions, « MCP and
connector tools » : « MCP tools are addressed as `{server_name}_{tool_name}` »). En
session, `/mcp` liste les serveurs branchés, `/mcp <nom>` leurs outils —
`/connectors` est un alias de `/mcp` (mcp-servers).

> **Limite annoncée par la documentation** : « the CLI does not yet support MCP
> servers that require OAuth authentication. Use the `stdio` or `http` transport
> with an API key or other static credential. » Un serveur OAuth ne se branche pas
> ici ; restent `stdio` et `http` avec un identifiant statique.

## 3. Secrets et variables

La documentation ne décrit **aucune interpolation `${VAR}`** dans `config.toml` :
on n'y écrit donc aucun secret à la main, on **nomme** la variable qui le porte.
`api_key_env` désigne le nom de cette variable, `api_key_header` dit où placer la
clé, et `api_key_format` en donne la forme — par exemple le mot `Bearer`, une
espace, puis le jeton (mcp-servers).

⚠️ Le champ `headers` accepte un **littéral** : l'exemple de la documentation écrit
`headers = { "Authorization" = "Bearer my_token" }`. C'est précisément ce qu'il ne
faut pas recopier avec un vrai jeton — porter la valeur par la variable que
`api_key_env` désigne, et laisser le littéral aux exemples.

Pour le modèle, la clé vit hors du fichier : `MISTRAL_API_KEY` dans
l'environnement, ou la valeur rangée par l'assistant de configuration dans le
répertoire Vibe (install-setup).

## 4. Restreindre un serveur à un agent

**Traduction possible**, au moins partielle — et c'est là que le §10.2 du contrat
se pose sur ce harness.

D'abord des filtres globaux dans `config.toml`, qui prennent des noms exacts, des
motifs glob ou une expression `re:` (mcp-servers) :

```toml
disabled_tools = ["mcp_*", "grep"]     # aucun outil MCP actif par défaut
enabled_tools = ["serena_*"]           # puis n'ouvrir que ceux-là
```

Ensuite une permission par outil, nommé `{serveur}_{outil}`. La documentation donne
les deux valeurs — « Set when Vibe should ask before using a tool, or always allow
it », `permission = "always"` ou `permission = "ask"` — et les deux pages les
montrent (safety-approvals-permissions, « Set per-tool permissions ») ; le motif
`[tools.<serveur>_<outil>]` vient de mcp-servers, « Tool naming and permissions »
(« Configure permissions per tool just like built-in tools ») :

```toml
[tools.coffre-parent_read_file]
permission = "always"

[tools.coffre-parent_write_file]
permission = "ask"
```

Enfin, chaque **agent** est un `.toml` (`~/.vibe/agents/<nom>.toml` ou
`./.vibe/agents/<nom>.toml`) qui porte ses propres `enabled_tools`,
`disabled_tools` et `[tools.<nom>] permission` (agents). C'est là que la
restriction par agent se traduit : couper les outils d'un serveur globalement,
puis les rouvrir dans le seul agent qui s'en sert —
`enabled_tools = ["coffre-parent_*"]`.

Réserve, écrite par la documentation elle-même : le champ `safety` (`safe`,
`neutral`, `destructive`, `yolo`) est un « **visual hint only** » — il colore la
bordure, il n'applique rien. La restriction tient aux filtres et aux permissions,
pas à lui.

⚠️ **Toujours `--agent` ; jamais `--trust` à l'aveugle.** `default_agent` ne vaut
qu'en session interactive : « In programmatic mode (`vibe --prompt …`), Vibe falls
back to `auto-approve` when `--agent` is not provided, and interactive tools such
as `ask_user_question` are disabled » (safety-approvals-permissions). Un lancement
sans `--agent` — le cas d'une **tâche planifiée** — exécute donc les outils **sans
rien demander**. La règle : **passer `--agent` toujours** — `--agent plan` pour une
lecture seule, et rien de plus permissif qu'`accept-edits` sur un périmètre déjà
relu. La documentation range `auto-approve` du côté des « disposable environments
(containers, CI runners, ephemeral VMs) » et prévient : « Never use it on machines
that hold SSH keys, cloud credentials, or production access. »

Et **jamais `--trust` sans avoir relu le `.vibe/`**. Ce drapeau « grant[s]
temporary trust when scripting Vibe » (safety-approvals-permissions, « Temporary
trust (CLI) ») fait tomber d'un coup l'approbation de dossier (§5) : un `.vibe/`
non relu — agents, permissions, serveurs MCP — s'applique alors sans que personne
ne l'ait lu. Sur le coffre : relire le `.vibe/` d'abord, ou ne pas s'en servir.

## 5. Charger le cerveau

Le CLI charge **jusqu'à deux `AGENTS.md`** (agents, « AGENTS.md support ») :

1. **utilisateur** : `~/.vibe/AGENTS.md` (ou `$VIBE_HOME`) ;
2. **projet** : en remontant depuis le dossier de travail, le **premier** fichier
   trouvé — mais **seulement dans un dossier approuvé** (« only inside trusted
   folders »).

Lancé depuis la **racine du coffre**, il tombe donc sur l'`AGENTS.md` que
`python3 scripts/installer.py --appliquer` y a posé — à une condition : la racine
doit être **approuvée**. Un dossier porteur d'`.vibe/`, d'`.agents/` ou d'un
`AGENTS.md` est « trustable » ; Vibe demande à l'approuver à l'ouverture, retient
la réponse dans `~/.vibe/trusted_folders.toml`, et **ignore la configuration de
projet** — avertissement compris — tant que l'approbation n'est pas donnée
(safety-approvals-permissions). La configuration utilisateur, elle, s'applique
toujours.

Le noyau `VAULT-CONTRACT.md` n'est **pas inséré** pour autant : l'`AGENTS.md`
ordonne de le lire, et la documentation ne décrit aucune résolution des renvois
d'un `AGENTS.md` — l'agent l'**ouvre** avec ses outils, comme sur les autres
harness. C'est une consigne de prompt, pas une garantie du moteur : d'où la
vérification du §6.

Pour un prompt système propre au harness, la voie documentée est ailleurs : un
agent personnalisé déclare `system_prompt_id = "<id>"`, et la documentation attend
le fichier `~/.vibe/prompts/<id>.md` (agents). Ce logement est celui d'un cerveau
propre à Vibe, pas du coffre.

**Les skills du coffre restent dans `OBSIA/IA/skills/`.** Le CLI découvre ses
propres skills — un dossier `SKILL.md` avec frontmatter, standard « Agent Skills »
— dans les chemins de `skill_paths`, puis `./.vibe/skills/` ou `./.agents/skills/`
(quand le dossier de travail est approuvé), puis `~/.vibe/skills/` (skills). Un
agent qui les chercherait là ne trouverait rien : ne pas recopier ni lier les
skills du coffre — le prompt dit où les lire, et les dupliquer violerait le §5.

## 6. Vérifier

D'abord que le produit démarre (install-setup) :

```bash
vibe --version          # doit rendre une version
vibe                    # lancé depuis la racine du coffre
```

Puis une conversation de test, sur le coffre :

1. **le cerveau est-il arrivé ?** lui demander de citer une règle de l'`AGENTS.md`
   — s'il ne la connaît pas, la racine n'est pas approuvée (§5) ;
2. **le coffre est-il atteignable ?** lister la racine (`../`), lire une note de
   `0-SAVOIRS/`, retrouver le registre des tags ;
3. **les MCP répondent-ils ?** `/mcp` (alias `/connectors`) liste les serveurs,
   `/mcp <nom>` leurs outils ;
4. **test d'échec** — renommer un instant `IA/skills/mermaid.md`, demander une
   tâche qui l'appelle : l'agent doit dire qu'il ne le trouve pas, pas improviser
   (§10) ;
5. **test de secret** — montrer une valeur factice qui ressemble à un jeton : il
   doit refuser de la répéter et la désigner par son nom (§4) ;
6. **toujours `--agent`** — relancer la même chose en `vibe --prompt "…"` **sans**
   `--agent`, sur un dossier jetable : il exécute sans rien demander (repli
   `auto-approve`, §4). C'est la preuve qu'une tâche planifiée doit porter
   `--agent`, et jamais `--trust` sans avoir relu le `.vibe/`.

Rien de tout cela ne remplace le contrôle **local**, qui reste à toi :

```bash
python3 scripts/verifier_coffre.py
python3 scripts/regenerate_sommaire.py
python3 scripts/regenerate_index.py
```

## 7. Facturer sur l'abonnement, pas à l'usage

**Éprouvé le 2026-10-16** sur une machine sans écran, Vibe 2.26.1, lu dans le code
installé (`vibe/setup/auth/`) — pas dans la documentation.

**Le symptôme.** Les appels échouent en série alors qu'un abonnement est actif ;
`~/.vibe/logs/vibe.log` porte `model_stream_failed`, et la cause, quelques lignes
plus bas, `billing_api_budget_exhausted`. Vibe s'authentifie alors par une **clé
d'API ordinaire**, facturée à l'usage jusqu'au plafond de l'organisation.

**Le diagnostic**, sans afficher la clé :

```bash
grep -o '"plan_[a-z]*": *"[^"]*"' ~/.vibe/whoami_cache.json
# api / FREE  → clé facturée à l'usage
# chat / …    → abonnement
```

**La connexion n'a pas besoin de navigateur sur la machine.** `vibe --setup`
demande une adresse de connexion à Mistral, tente de l'ouvrir, puis **interroge le
serveur en boucle** jusqu'à ce que l'utilisateur se soit connecté : rien ne revient
vers `localhost`, aucun tunnel n'est nécessaire. L'adresse s'ouvre sur n'importe
quel appareil — à condition de pouvoir la récupérer.

**La procédure**

1. Écarter la clé facturée, sinon Vibe continue de s'en servir :
   `mv ~/.vibe/.env ~/.vibe/.env.api-bak`.
2. Faire écrire l'adresse dans un fichier plutôt que dans un navigateur. Elle
   contient des `&` : un `sh -c "echo %s > …"` la tronque — passer par un petit
   script qui la reçoit en argument :

   ```bash
   printf '#!/bin/sh\nprintf "%%s\\n" "$1" > "$HOME/vibe-url.txt"\n' \
     > ~/.local/bin/noter-url && chmod +x ~/.local/bin/noter-url
   BROWSER=noter-url vibe --setup
   ```

3. Choisir la connexion par navigateur et **laisser la fenêtre ouverte** —
   `Ctrl+C` l'interrompt ; dans un terminal, copier se fait par `Ctrl+Maj+C`.
4. D'un autre terminal, lire `~/vibe-url.txt` et ouvrir l'adresse **vite** — elle
   expire — avec le compte qui porte l'abonnement. S'il propose plusieurs
   organisations, prendre celle de l'abonnement : le plan suit l'organisation.
5. Attendre `Setup complete` ; la nouvelle clé est rangée dans `~/.vibe/.env`.
6. Vérifier : le cache du plan peut dater d'avant la connexion. L'écarter, faire un
   appel, relire :

   ```bash
   mv ~/.vibe/whoami_cache.json ~/.vibe/whoami_cache.json.old
   vibe -p "Réponds juste OK" --max-turns 1
   grep -o '"plan_[a-z]*": *"[^"]*"' ~/.vibe/whoami_cache.json
   ```

7. Redémarrer le harness qui lance Vibe : ses processus `vibe-acp` gardent
   l'ancienne clé en mémoire. Pour un service utilisateur systemd :
   `systemctl --user restart <service>`.
8. Nettoyer : supprimer `~/vibe-url.txt`, `~/.local/bin/noter-url`,
   `~/.vibe/.env.api-bak` et l'ancien cache — puis **supprimer l'ancienne clé dans
   la console Mistral**, seul geste qui coupe la facturation à l'usage.

L'adresse de connexion vaut accès au compte jusqu'à son expiration : elle ne
s'écrit ni dans une note ni dans un carnet (`../VAULT-CONTRACT.md` §4).

**La clé d'abonnement ne se réutilise pas hors du CLI (constaté le 2026-10-19).**
La clé rangée par §7 dans `~/.vibe/.env` (47 caractères, plan `chat`) est un
jeton propre à Vibe : `api.mistral.ai/v1/chat/completions` la refuse en
**401 « Invalid API Key »** — y compris sur les modèles de l'abonnement
(`mistral-medium-3.5`, `glm-5-3`) — alors que `vibe -p` fonctionne avec elle.
La cause se lit dans le SDK embarqué `mistralai_vibe_local_harness` : Vibe
l'échange **à l'exécution** contre un jeton d'accès (`Bearer
{credentials.access_token}`). Brancher cette clé dans un autre harnais
(opencode, AionUi…) expose donc des modèles dont **aucun appel ne passe** ;
seule une clé d'API « à l'usage » (console, crédits) fonctionne hors des
produits Vibe. L'abonnement se consomme dans les produits Vibe — point.

> Le coffre ne dépend pas de Vibe Code CLI ; cette fiche n'est qu'un gabarit
> d'intégration.
