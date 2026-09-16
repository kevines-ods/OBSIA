# Pi

**Statut : vérifié sur documentation le 2026-09-16 (dépôt du projet et
documentation d'usage — URLs en fin de fiche) — jamais éprouvé sur machine
réelle.**

Agent en ligne de commande installé par npm, licence MIT. Son parti pris tient
dans une phrase de sa propre documentation : *« It intentionally does not
include built-in MCP, sub-agents, permission popups, plan mode, to-dos, or
background bash. »* Le cœur reste petit ; tout le reste vit en **extensions**
TypeScript, installées depuis un chemin, npm ou git.

C'est la première fiche de ce dossier dont la section « bloc MCP » n'a pas de
réponse à donner. Elle dit ce qui remplace chaque serveur déclaré par les
agents, et surtout où le remplacement s'arrête.

Cette fiche reste un **gabarit d'intégration**, pas une recommandation : le
coffre ne choisit aucun harness (`../VAULT-CONTRACT.md` §3). Ce qui a mené à
s'y intéresser vit dans
`mémoire/projets/choix-du-harness/2026-09-16-pi-en-second-harness.md`.

---

## 1. Où vit la configuration

Installation, sur une base Arch où `npm` vient de `pacman` :

```bash
npm install -g --ignore-scripts @earendil-works/pi-coding-agent
```

`--ignore-scripts` est la forme donnée par la documentation elle-même : rien
dans ce paquet n'a besoin de scripts de cycle de vie à l'installation. Un
installateur `curl … | sh` existe aussi ; la réserve habituelle s'applique —
on ne fait pas passer un script distant dans un interpréteur sans l'avoir lu.

Tout se configure par des fichiers rangés sous `$HOME`, donc **hors dépôt** par
construction : rien à ignorer dans `.gitignore`.

| Fichier ou dossier | Portée |
| --- | --- |
| `~/.pi/agent/settings.json` | global — tous les projets |
| `.pi/settings.json` | projet — écrase le global |
| `~/.pi/agent/AGENTS.md` | instructions globales |
| `.pi/SYSTEM.md`, `~/.pi/agent/SYSTEM.md` | **remplace** le prompt système |
| `.pi/APPEND_SYSTEM.md`, `~/.pi/agent/APPEND_SYSTEM.md` | **ajoute** au prompt système |
| `~/.pi/agent/sessions/` | sessions, rangées par répertoire de travail |
| `~/.pi/agent/skills/`, `.pi/skills/`, `.agents/skills/` | skills au standard Agent Skills |
| `~/.pi/agent/extensions/`, `.pi/extensions/` | extensions TypeScript |
| `~/.pi/agent/models.json` | fournisseurs et modèles personnalisés |
| `~/.pi/agent/trust.json` | décisions de confiance, par dossier |

Un `.pi/` posé à la racine du coffre parent commence par un point : Obsidian ne
l'indexe pas, et la règle d'unicité des noms de notes (§6) n'est pas touchée.

**La confiance du projet est un piège silencieux.** Pi demande à l'ouverture
s'il fait confiance à un dossier qui contient des ressources `.pi/`, et ne
charge celles-ci qu'après. Les modes non interactifs (`-p`, `--mode json`,
`--mode rpc`) **ne demandent rien** : sans décision enregistrée, ils appliquent
`defaultProjectTrust`, dont la valeur par défaut `ask` revient à **ignorer** les
ressources du projet. Une tâche planifiée qui compte sur `.pi/` et n'a pas
`--approve` tourne donc sans son cerveau, sans une seule erreur pour le dire.
`/trust` en interactif enregistre la décision une fois pour toutes.

## 2. Le bloc MCP — il n'y en a pas

Pi n'a **aucune** clé de configuration MCP : ni `mcpServers`, ni équivalent.
Il n'y a donc ni exemple stdio ni exemple HTTP à donner ici, et le skill
`configuration-mcp` (`../../skills/configuration-mcp.md`) doit s'arrêter à
cette section plutôt que d'inventer une clé — c'est exactement ce que la fiche
DSH obtient en étant vide.

Ce que deviennent les cinq serveurs déclarés dans `IA/MCP/` :

| Serveur déclaré | Sur ce harness |
| --- | --- |
| `coffre-parent` | **inutile** — lancer à la racine du coffre (§7.6, voie 1). Pi ne restreint aucun chemin : `read` et `bash` atteignent tout ce que l'utilisateur atteint. |
| `git-hub` | `git` en ligne de commande dans `bash`. Ce qui se perd : les opérations que l'outil structurait (revue de PR, commentaires) redeviennent du texte à composer. |
| `searxng` | l'instance s'interroge en HTTP depuis `bash`. À vérifier au branchement : c'est une hypothèse, pas un constat. |
| `obsidian` | une note est un fichier ; `read`, `write`, `edit` suffisent, et un rétrolien n'est que du texte (§7.5). |
| `chrome-devtools` | **aucun équivalent**. Le skill `test-navigateur` (`../../skills/test-navigateur.md`) reste inapplicable tel quel : c'est une frontière de périmètre, pas un oubli à rattraper. |

**Ce qu'une extension peut rendre.** La documentation liste « MCP server
integration » parmi ce que les extensions savent faire, et des paquets tiers
existent sur npm — un adaptateur MCP, un système de permissions. **Aucun n'est
officiel, aucun n'est audité ici**, et une extension s'exécute avec les droits
de l'utilisateur. La leçon de l'autre harness écarté vaut pour toute place de
marché : le nombre de paquets n'est pas une garantie. Statut de cette voie :
**non vérifiée**.

## 3. Secrets et variables

La documentation ne décrit **aucune syntaxe d'interpolation** dans
`settings.json` : on n'y écrit donc pas de secret (§4). Trois voies
documentées, par ordre de préférence :

1. **variable d'environnement** — `export ANTHROPIC_API_KEY=…` dans le profil
   du shell, hors dépôt ;
2. **`/login`** — authentification par abonnement, le jeton est géré par le
   harness ;
3. `--api-key` sur la ligne de commande — **à éviter** : la clé entre dans
   l'historique du shell et s'affiche dans la liste des processus.

Trois réglages de sobriété réseau, utiles à connaître : `PI_SKIP_VERSION_CHECK=1`
coupe la vérification de version, `PI_TELEMETRY=0` (ou `enableInstallTelemetry`
à `false`) coupe le ping d'installation, `--offline` / `PI_OFFLINE=1` coupe
toute opération réseau au démarrage.

## 4. Restreindre un serveur à un agent

**Impossible sous cette forme**, et pour deux raisons cumulées : il n'y a pas
de MCP à restreindre, et pas de notion d'agent à qui le restreindre. La
documentation l'énonce sans détour : *« Pi does not include a built-in
permission system for restricting filesystem, process, network, or credential
access. By default, it runs with the permissions of the user and process that
launched it. »*

Ce qui subsiste n'est pas rien : l'**allowlist d'outils au lancement**. La
documentation en donne elle-même l'usage sous le nom « Read-only mode ».

| Dans le coffre | Côté harness |
| --- | --- |
| un fichier de `IA/agents/` | aucun objet natif : un alias de shell qui passe le fichier en argument `@` |
| `read_only: true` (§5) | `pi --tools read,grep,find,ls` |
| `mcp:` déclaré par l'agent (§10.2) | sans objet |
| un skill de `IA/skills/` | rien à déclarer : le fichier s'ouvre quand la demande l'appelle |

```bash
# ~/.bashrc — hors dépôt, jamais versionné
alias obsia-relecture='pi --tools read,grep,find,ls @"$HOME/Mon coffre/OBSIA/IA/agents/contradicteur.md"'
```

⚠️ **La restriction vit dans la ligne de commande, pas dans le fichier.**
Lancer `pi` tout court sur le même fichier donne un interlocuteur qui se croit
en lecture seule et ne l'est pas — le prompt le dit, rien ne le tient. D'où
l'alias : ce qui se tape à la main s'oublie un soir de fatigue. C'est le point
exact où ce harness rend *moins* qu'un harness à permissions par agent.

**Ne pas recopier les skills du coffre dans `.pi/skills/`.** Le format attendu
là-bas est `SKILL.md`, que le §5 du contrat interdit comme point d'entrée
précisément parce qu'une douzaine de fichiers homonymes casserait l'unicité des
noms de notes. Les skills se chargent ici comme partout ailleurs : l'agent
ouvre le fichier quand la demande l'appelle.

## 5. Charger le cerveau

Pi charge `AGENTS.md` (ou `CLAUDE.md` à défaut) depuis `~/.pi/agent/`, depuis
les **dossiers parents en remontant** du répertoire de travail, et depuis le
répertoire courant. En remontant — jamais en descendant. D'où le piège :
lancé à la racine du coffre, il ne verra **pas** `OBSIA/CLAUDE.md`, qui est en
dessous.

Deux voies, selon le répertoire de lancement.

**Voie A — lancer à la racine du coffre.** C'est la voie 1 du §7.6, celle qui
rend le serveur `coffre-parent` inutile. Le cerveau se pose explicitement :

```bash
cd "$HOME/Mon coffre/OBSIA"
mkdir -p ../.pi
python3 scripts/generer_prompt.py -o ../.pi/APPEND_SYSTEM.md
cd ..
pi
```

Deux précisions qui décident du résultat :

- `APPEND_SYSTEM.md` **ajoute** au prompt par défaut ; `SYSTEM.md` le
  **remplace**, et remplacer supprime au passage ce que le harness dit à son
  modèle sur ses propres outils. Préférer la première forme, sauf raison
  explicite ;
- ces fichiers sont des ressources `.pi/` : ils dépendent de la confiance du
  §1. `/trust` une fois en interactif, `--approve` dans tout lancement
  automatisé.

**Voie B — lancer depuis le dépôt.**

```bash
cd "$HOME/Mon coffre/OBSIA"
pi
```

`CLAUDE.md` est alors chargé tout seul, en repli d'`AGENTS.md`. Mais la
syntaxe `@IA/system/…` qu'il emploie pour importer le contrat et les trois
index n'est **pas documentée comme résolue** par ce harness : le cerveau
risque d'arriver amputé de l'essentiel, sans que rien ne le signale. La voie A
supprime ce doute pour le prix d'une commande.

Ce que le répertoire de lancement change, c'est ce qui est **chargé tout
seul** — pas ce qui est **atteignable**. Faute de restriction de chemin, le
coffre parent reste accessible dans les deux cas ; dans la voie B il s'atteint
par `..`, et les dossiers à tiret s'écrivent `../-SAVOIRS`, jamais `-SAVOIRS`
nu (§7).

Régénérer le prompt après toute modification d'un frontmatter : un cerveau
généré une fois décrit le coffre tel qu'il était (§11).

## 6. Vérifier

Les trois vérifications communes de `commun.md` d'abord : lister la racine du
coffre, lire une note de `Mon coffre/-SAVOIRS/`, retrouver le registre des
tags. ⚠️ écrire `./-SAVOIRS`, jamais `-SAVOIRS` nu.

Trois de plus, propres à cette fiche — chacune prouve une chose que la
précédente ne prouve pas :

```bash
pi -p "Énonce la règle du contrat OBSIA sur les fichiers générés, et dis d'où tu la tiens."
pi --tools read,grep,find,ls -p "Crée un fichier nommé essai.txt"
pi -p "Liste les dossiers de la racine du coffre" && pi -c
```

1. si la règle du §11 est inconnue, le cerveau n'a pas été chargé — relancer
   avec `--no-context-files` pour comparer les deux réponses lève le doute ;
2. l'agent doit **échouer faute d'outil**. S'il crée le fichier, l'allowlist
   n'a pas été appliquée — et c'est la seule chose qui tienne lieu de
   `read_only: true` ici ;
3. `-c` doit retrouver la session précédente. C'est la promesse des sessions
   sur disque, et elle se constate.

## 7. Tâches planifiées

Aucun planificateur documenté. Les tâches du registre restent donc
`exécutant: local` (§12) — timer systemd nommé `obsia-<nom-de-la-tâche>`,
appelant le harness en mode non interactif :

```bash
cd "$HOME/Mon coffre"
pi --approve --name "revue-hebdomadaire-du-coffre" -p "instruction de la tâche"
```

`--approve` n'est pas décoratif : sans lui, les ressources `.pi/` sont ignorées
en silence (§1). `--name` donne à la session un nom retrouvable dans
`~/.pi/agent/sessions/`, ce qui remplace le journal qu'un timer ne tient pas.

⚠️ **Le risque réel d'un poste à deux harness est ici.** L'invariant du §12 —
une tâche, au plus une instance vivante, tous exécutants confondus — ne se
défend pas tout seul. Deux harness qui savent tous deux lire `IA/tâches/`
peuvent instancier la même tâche chacun de son côté : elle se déclenche deux
fois, et aucune erreur ne le dit. Le registre déclare une intention ;
l'instanciation se décide **d'un seul côté**, et cela s'écrit avant de
brancher le second harness.

## 8. Ce que cette fiche ne dit pas

- **Rien n'a tourné.** Le statut en tête est « vérifié sur documentation », et
  cela ne se déduit pas d'un branchement qui a l'air de marcher.
- **Les extensions ne sont pas auditées.** Tout ce que ce harness ne fait pas
  nativement — MCP, sous-agents, permissions — passe par du code tiers exécuté
  avec les droits de l'utilisateur. Chaque ajout est un arbitrage de sécurité,
  pas une case à cocher.
- **Le projet bouge vite.** Le dépôt a déjà changé d'organisation et le paquet
  npm porte un nom différent du dépôt d'origine. Revérifier les chemins de
  configuration avant de s'appuyer sur cette fiche dans six mois.
- **La conteneurisation n'est pas reprise ici.** La documentation renvoie à
  trois motifs (micro-VM, Docker, bac à sable à politique) ; c'est la réponse
  du projet à l'absence de permissions, et elle mérite sa propre évaluation.

## URLs sources

1. https://github.com/badlogic/pi-mono
2. https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/README.md
3. https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/usage.md
4. https://pi.dev/docs/latest
5. https://www.npmjs.com/search?q=keywords%3Api-package

> Le coffre ne dépend pas de ce harness ; cette fiche n'est qu'un gabarit
> d'intégration.
