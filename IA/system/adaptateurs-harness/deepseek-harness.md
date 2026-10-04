# DeepSeek Harness (DSH)

**Statut : vérifié sur documentation le 2026-09-30
(<https://github.com/deepseek-ai/deepseek-harness>) — jamais éprouvé sur
machine. Le §1, le §2, le §3 et le §5 sont vérifiés ; le §4 reste
**NON VÉRIFIÉ**, et il le dit.**

Le harness de DeepSeek : Node et TypeScript, bâti sur le cadre de greffons
Cordis, où **tout est greffon** et où la configuration est un empilement de
fichiers YAML qu'on appelle des *patches*. Un *profil* assemble des paquets
installables et son propre patch — d'où une conséquence pratique : côté DSH, on
n'écrit jamais « le fichier de configuration », on écrit **une ligne dans le
patch du profil actif**.

Deux choses le rendent intéressant ici : il lit `AGENTS.md` **et** `CLAUDE.md`
tout seul, et son budget de contexte par défaut (64 Kio) est **le double de
celui de Codex** — voir le §5, où la comparaison est chiffrée sur ce coffre.

---

## 1. Où vit la configuration ✅

Tout part de `$DSH_HOME`, `~/.dsh` par défaut.

| Chemin | Rôle |
| --- | --- |
| `$DSH_HOME/profiles/<nom>/cordis.patch.yml` | **la couche qu'on édite** : patch propre au profil actif |
| `$DSH_HOME/profiles/<nom>/` | le profil : bundles installables + son patch |
| `$DSH_HOME/AGENTS.md` | instructions globales de l'utilisateur (§5) |
| `$DSH_HOME/.credentials.yaml` | identifiants gérés (§3) |
| `packages/bundle/base/cordis.patch.yml` | **le bundle `base`** : la liste des greffons actifs par défaut, dans le dépôt |

Un profil se crée et s'entretient en ligne de commande :

```bash
dsh --profile <nom> --from-default-profile web   # profil neuf, à partir d'un gabarit livré
dsh plugin                                       # profil adossé à base, et gestion des bundles
```

`base` monte la composition par défaut : agents, outils de fichiers, skills,
sous-agents, et les greffons dont parle cette fiche. Un patch de profil
**s'ajoute** à ce socle ; il ne le remplace pas.

**Hors dépôt** : `$DSH_HOME` est un dossier utilisateur (souvent à point,
`~/.dsh`), jamais versionné. Seule exception à surveiller : les `.env` de projet
que les identifiants prennent en repli (§3) — ceux-là ne doivent pas entrer dans
le dépôt.

**Non vérifié** : l'existence d'un `.dsh/` par projet, et l'ordre exact entre le
patch du foyer et les surcouches de ligne de commande.

## 2. Le bloc MCP ✅

Le chemin du fichier n'est **pas** dans la documentation du paquet
`packages/mcp/mcp-client` — il est dans celle du démarrage
(`packages/boot/app-boot`) : c'est **le patch du profil**, donc
`$DSH_HOME/profiles/<nom>/cordis.patch.yml`.

La forme est celle de tout greffon : un `id` local, un nom de paquet, un
`config`. **Une ligne par serveur**, pas de dictionnaire de serveurs.

```yaml
- id: mcp-coffre-parent
  name: '@deepseek-ai/dsh-mcp-client'
  config:
    serverName: coffre-parent
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/chemin/absolu/vers/la/racine/du/coffre"]
```

```yaml
- id: mcp-searxng
  name: '@deepseek-ai/dsh-mcp-client'
  config:
    serverName: searxng
    transport: streamable-http
    url: https://searxng.exemple.org/mcp
    headers:
      Authorization: !!js `Bearer ${process.env.SEARXNG_TOKEN}`   # §3
```

| Clé | Rôle | Défaut |
| --- | --- | --- |
| `serverName` | nom du serveur — `[A-Za-z0-9_-]{1,32}`, **unique par portée** | — |
| `transport` | `stdio` ou `streamable-http` | — |
| `command`, `args`, `env`, `cwd` | stdio | — |
| `url`, `headers` | streamable-http | — |
| `toolCallTimeoutMs` | délai par appel d'outil | 60 000 |
| `maxInstructionBytes` | taille des instructions du serveur | 32 768 |
| `failOnStartupError` | échouer le démarrage si le serveur ne répond pas | `false` |
| `reconnect` | reconnexion (activée, délai 500 ms, plafond 30 000 ms, 10 essais) | — |

Les outils exposés s'appellent `mcp__<serverName>__<outil>` — d'où l'unicité du
`serverName` dans une même portée. **Aucun serveur n'est activé par défaut** :
une portée vide ne donne aucun outil, et ce n'est pas une panne.

## 3. Secrets et variables ✅

Le YAML de Cordis accepte un **tag JavaScript**, `!!js` : l'expression est
évaluée à la lecture, pas recopiée dans le fichier.

```yaml
    headers:
      Authorization: !!js `Bearer ${process.env.SEARXNG_TOKEN}`
```

| Besoin | Moyen |
| --- | --- |
| passer un secret au serveur | `!!js process.env.X` — le fichier porte un **nom**, jamais une valeur (§4) |
| l'environnement ambiant | **filtré** : les noms qui contiennent `KEY`, `PASSWORD`, `SECRET` ou `TOKEN` — et tous les `DSH_*` — ne sont pas transmis |
| identifiants du harness | environnement hérité, puis `$DSH_HOME/.credentials.yaml`, puis `.env` de projet et d'utilisateur |

Deux conséquences à retenir :

- **le filtrage de l'environnement est un filet, pas un mur** : ce qui est
  déclaré explicitement dans `env` passe par-dessus le filtre. C'est le
  comportement voulu, et c'est aussi le chemin par lequel un secret peut
  atterrir dans un fichier — la prudence reste de mise ;
- `!!js` étant du JavaScript évalué, **le fichier de configuration est du code**.
  Un patch de profil ne se recopie pas d'un dépôt inconnu sans le lire : c'est
  une remarque de sûreté, pas de style.

## 4. Restreindre un serveur à un agent — ❌ NON VÉRIFIÉ

Plan de vérification, à reprendre :

- les greffons MCP se déclarent « dans la portée Cordis voulue », et un
  sous-agent est une composition à part (`packages/subagent/`) ; il est
  **probable** qu'une ligne de greffon posée dans la portée d'un sous-agent
  n'existe que pour lui ;
- ce que j'ai cherché sans le trouver : la documentation d'un sous-agent qui
  déclare **ses propres** greffons, et le nom exact de la portée à viser. Le
  sous-système, dans `packages/subagent/`, décrit la délégation, les backends et
  les outils des enfants — pas la restriction de leurs serveurs ;
- en l'état, on ne peut donc **pas** affirmer que le §10.2 se traduit ici.

Un sous-agent en lecture seule ne se déclare pas non plus par un mot-clé : rien
n'a été trouvé d'équivalent à un `read_only`, ce qui reste à vérifier au même
endroit.

## 5. Charger le cerveau ✅

Le greffon **`@deepseek-ai/dsh-agent-instructions`** s'en charge. Il est monté
par le bundle `base` — donc **actif par défaut**, sans rien écrire — avec un
`maxBytes` obligatoire que `base` fixe à **65 536 octets** :

```yaml
    - id: agent-instructions
      name: '@deepseek-ai/dsh-agent-instructions'
      config:
        maxBytes: 65536
```

### Ce qu'il lit, et dans quel ordre

1. **la ligne globale** : `$DSH_HOME/AGENTS.md` (`~/.dsh/AGENTS.md`), s'il
   existe ;
2. **la chaîne du projet** : du plus large au plus précis, de la racine du
   projet jusqu'au dossier de travail ;
3. dans chaque dossier, deux **candidats de base** — `AGENTS.md`, `CLAUDE.md` —
   puis deux **surcouches locales** — `AGENTS.local.md`, `CLAUDE.local.md`.

Trois détails qui comptent :

- deux fichiers frères dont le contenu est identique **après rognage des
  blancs** ne sont rendus qu'une fois. Un fichier distinct, même s'il ressemble,
  est rendu **en entier** à côté de l'autre ;
- **les imports `@chemin` ne sont pas interprétés.** Ni les `@`, ni les règles
  d'un `.claude/rules/` : la ligne arrive brute dans le contexte ;
- si le budget est dépassé, le greffon garde les fichiers **les plus précis**,
  écarte des fichiers entiers plutôt que de couper le plus précis, et **le dit**
  dans un avis visible nommant les chemins écartés ou tronqués. Un dépassement
  ne passe donc pas inaperçu — contrairement à Codex.

### La racine du projet, quand il n'y a pas de `.git`

Le greffon cherche, en remontant depuis le dossier de travail, le premier
dossier qui porte un marqueur de racine — `['.git']` par défaut. **Si aucun
marqueur n'est trouvé, la racine retenue est le dossier de travail lui-même**
(`findProjectRoot`, `src/files.ts`) : la chaîne se réduit alors à ce seul
dossier. Une erreur d'entrée/sortie pendant la remontée arrête la recherche au
lieu de choisir un ancêtre — le doute ne devient jamais une supposition.

### Ce que cela donne sur ce coffre

Vérifié le 2026-09-30 : **aucun `.git`** dans la racine du coffre parent, ni
dans `/srv`, ni dans `/` ; et **pas d'`AGENTS.md`** à la racine du coffre — donc
l'installeur n'y est pas encore passé.

| Où l'on lance | Racine retenue | Ce qui est lu |
| --- | --- | --- |
| la racine du coffre (`Mon coffre/`) | le dossier de travail | `AGENTS.md` **et** `CLAUDE.md` *(une fois `installer.py --appliquer` passé)* |
| `OBSIA/` (qui a un `.git`) | `OBSIA/` | `OBSIA/CLAUDE.md` — et **jamais** l'`AGENTS.md` du parent |

**Lancer depuis la racine du coffre, donc** — sinon le cerveau n'arrive pas.

### Ce que cela donnera — projection, `AGENTS.md` non installé

**Ce qui suit est une projection, pas une mesure** : aucun `AGENTS.md` n'existe
aujourd'hui à la racine du coffre. En l'état, DSH ne lirait que le `CLAUDE.md`
racine (282 octets), dont l'unique ligne utile `@OBSIA/CLAUDE.md` **n'est pas
interprétée** : le `CLAUDE.md` d'`OBSIA/` (747 octets) n'est pas chargé. **Pas
de cerveau, donc, tant que l'installeur n'est pas passé.**

Une fois `installer.py --appliquer` passé, les deux fichiers seront lus et le
second **ne disparaîtra pas** par déduplication. Projection :

- `AGENTS.md` produit par l'installeur : **24 939 octets** ;
- `CLAUDE.md` racine : **282 octets**, dont l'unique ligne utile sera toujours
  `@OBSIA/CLAUDE.md`, non interprétée — du bruit inoffensif à côté du cerveau
  porté par l'`AGENTS.md` ;
- total ≈ **25 221 octets**, soit **38 % du budget de 65 536**. Pas de
  troncature, et une marge confortable — à comparer aux 32 Kio de Codex, où le
  même coffre frôlera les trois quarts du plafond ;
- `$DSH_HOME/AGENTS.md` n'existe pas sur cette machine : rien à composer au-dessus.

## 6. Vérifier ✅ *(gestes documentés — rien n'a été lancé ici)*

`dsh` n'est pas installé sur cette machine (vérifié) ; `npx` et Node 24 sont là,
donc l'installation est possible — mais **tant qu'elle n'est pas faite, tout ce
qui suit reste à prouver**.

Les trois vérifications communes de `commun.md` d'abord : lister la racine du
coffre, lire une note de `Mon coffre/0-SAVOIRS/`, retrouver le registre des tags.
⚠️ écrire `./0-SAVOIRS`, jamais `0-SAVOIRS` nu.

Puis trois gestes propres à cette fiche :

```bash
dsh --profile <nom>          # lancer, puis lui demander de citer une règle du contrat
wc -c ../AGENTS.md           # une fois installé ; le budget de l'avis éventuel
```

1. lancé de la racine du coffre, DSH doit **citer les règles du coffre** — pas
   les paraphraser ;
2. **aucun avis « budget »** ne doit apparaître. S'il apparaît, il **nomme** le
   fichier écarté ou tronqué : c'est la meilleure trace dont on dispose, et
   elle ne coûte rien à lire ;
3. pour prouver que la chaîne du projet est bien celle qu'on croit, faire
   **lister les sources d'instructions** plutôt que les deviner. Rien n'a été
   trouvé de documenté pour cela : à établir au premier essai réel.

## 7. Ce que cette fiche ne dit pas

- **Rien n'a tourné.** Le §4 est explicitement non vérifié ; les autres
  sections le sont *sur documentation*, ce qui n'est pas la même chose.
- **Le dépôt bouge vite** : dernier envoi le 2026-09-29, un jour avant cette
  lecture. Les chemins de paquets cités ici peuvent changer ;
- **les chiffres de taille sont une projection** : `AGENTS.md` n'est pas
  installé ; les 24 939 octets viennent du prompt généré, pas d'un fichier lu.
  Le 2026-09-30, sans profil et sans `~/.dsh/AGENTS.md`, DSH ne lirait que le
  `CLAUDE.md` racine (282 octets) ;
- **le sous-agent n'est pas traité** : ni restriction de serveurs, ni lecture
  seule. C'est un manque, pas une absence de fonctionnalité.

## URLs sources

1. <https://github.com/deepseek-ai/deepseek-harness/tree/master/packages/context/agent-instructions>
2. <https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/mcp/mcp-client/README.md>
3. <https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/mcp.md>
4. <https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/config-catalog.md>
5. <https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/boot/app-boot/README.md>
6. <https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/bundle/base/cordis.patch.yml>
7. <https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/credentials.md>

> Le coffre ne dépend pas de ce harness ; cette fiche n'est qu'un gabarit
> d'intégration.
