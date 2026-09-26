# OBSIA

Système d'orchestration d'agents IA reposant sur un coffre Obsidian.

Les agents, leurs compétences et leur mémoire sont des fichiers Markdown. Pas de
base de données, pas de format propriétaire : le coffre se lit et s'édite à la
main, dans Obsidian ou dans n'importe quel éditeur de texte.

## Principe

Un **agent** est un fichier qui décrit un interlocuteur : son rôle, les skills
qu'il mobilise, les serveurs MCP dont il dépend.

Un **skill** est un fichier qui décrit une manière de faire : une procédure, des
commandes, des pièges à éviter.

Une **tâche** est un fichier qui décrit une action planifiée : quand la
déclencher, pour quel agent, avec quelle instruction.

Un **harness** — Claude Code, OpenCode, Aider, Goose, ou l'interface de ton
choix — lit ces fichiers et exécute. Le coffre décrit *quoi* faire ; le harness
fournit *avec quoi*.

Le chargement est paresseux : le prompt système ne contient que l'index des
agents, des skills et des tâches planifiées. Le contenu d'un skill n'est lu que
lorsqu'il devient nécessaire.

## Structure

```
OBSIA/                       le coffre — la racine du dépôt EST le coffre
├── IA/
│   ├── agents/              définition des agents
│   ├── skills/              compétences réutilisables
│   ├── MCP/                 outils structurés
│   ├── tâches/              registre des tâches planifiées
│   └── system/              VAULT-CONTRACT.md (les règles), index,
│                            modules/ (le catalogue installable),
│                            prompt-fondateur.md (intention d'origine),
│                            adaptateurs-harness/ (gabarits d'intégration)
├── mémoire/                 commun → profil, préférences, projets ;
│                            par agent → expériences
├── brouillon/               zone de travail libre
├── scripts/
│   ├── installer.py         sonde la machine, retient les modules utiles
│   ├── publier.py           dérive le miroir public de ce dépôt
│   ├── generer_prompt.py    prompt système depuis les frontmatters
│   ├── regenerate_index.py  les quatre index et IA/README.md
│   ├── regenerate_sommaire.py  les sommaire.md de mémoire/
│   └── verifier_coffre.py   cohérence du coffre — utilisé en CI
├── HISTORIQUE.md            ce qui a été décidé puis écarté
├── LICENSE                  AGPL-3.0-or-later
├── README.md
└── .gitignore
```

Il n'y a pas de sous-dossier « coffre » : le dépôt lui-même en tient lieu. Pour
l'utiliser, cloner `OBSIA/` **à la racine** de votre coffre Obsidian, côte à
côte avec vos dossiers de connaissance, et ouvrir Obsidian sur ce coffre entier
(et non sur `OBSIA/` seul) : c'est la condition pour que les rétroliens se
résolvent à l'échelle du coffre (§7).

Le coffre ne connaît aucune interface et n'en nomme aucune. Il décrit *quoi*
faire ; le harness de ton choix fournit *avec quoi*. Rien ici ne dépend d'un
programme particulier — c'est la condition pour qu'OBSIA reste libre de ses
mouvements.

## Le coffre parent — votre base de connaissances

OBSIA est le cœur ; le coffre qui l'entoure est votre base de connaissances.
Il s'appelle `Mon coffre/`, et le dépôt se clone à sa racine, à côté de
`_maintenance/`, `-PROJETS/`, `-DOCUMENTS/`, `-PERSONNELS/`, `-SAVOIRS/` et
`-EN-VRAC/`. Seul `OBSIA/` est versionné.

La structure de premier niveau est fixe (seul vous la modifiez). Les agents
lisent tout le coffre parent, remplissent les notes d'`-EN-VRAC/` (corps, tags,
rétroliens) puis les classent, complètent les notes déposées dans `-SAVOIRS/`,
et consignent previews et actions dans `_maintenance/`. `-EN-VRAC/` est un
**tampon** : une session de rangement le vide entièrement. Les règles complètes
sont au §7 de `IA/system/VAULT-CONTRACT.md`.

Pour que les agents atteignent le coffre parent, le harness doit avoir accès à
sa racine — pas seulement à `OBSIA/` : dossier de travail ouvert sur le coffre,
ou serveur MCP « fichiers » (fiche `IA/MCP/coffre-parent.md`, gabarit
`IA/MCP/mcp.example.json`). La configuration réelle vit hors dépôt.

Les **gabarits d'intégration par harness** — Claude Code, OpenCode, OpenClaw,
DeepSeek Harness, AionUi/ObsiaUi, LibreChat — vivent dans
`IA/system/adaptateurs-harness/`.

## Tâches planifiées

Une tâche récurrente est déclarée dans `IA/tâches/<nom>.md` : quand, pour quel
agent, et l'instruction exacte à lui envoyer. Ce fichier fait foi.

Le timer systemd, le planificateur du harness ou le cron de la machine ne sont
que des **instances** de cette déclaration : nommées `obsia-<nom>`, jetables,
recréables depuis le registre. Changer de harness ou de machine ne perd donc
plus rien — on relit le registre et on ré-instancie.

```yaml
---
schema: 1
kind: tâche
name: revue-hebdomadaire-du-coffre
description: Une ligne — quoi, et à quel rythme.
mode: agent              # agent | commande
quand: "0 9 * * 1"       # cron à 5 champs, entre guillemets
fuseau: Europe/Paris
exécutant: local         # local | harness — qui a le droit de déclencher
agent: assistant
actif: true
---
```

Le corps porte l'instruction — auto-suffisante, puisqu'au déclenchement il n'y
a plus de conversation. Règles au §12 de `VAULT-CONTRACT.md`, procédure dans le
skill `cron`.

Une tâche = **au plus une instance vivante**, tous exécutants confondus. C'est
à ça que sert `exécutant` : planifier la même chose côté harness *et* côté
machine la déclencherait deux fois, sans qu'aucune erreur ne le signale.

Le passage du registre aux timers systemd est outillé. La séquence complète,
une fois par machine :

```bash
mkdir -p ~/.config/obsia
python3 IA/skills/cron/scripts/appliquer_taches.py --config > ~/.config/obsia/appliquer.conf
$EDITOR ~/.config/obsia/appliquer.conf                          # renseigner commande_agent
python3 IA/skills/cron/scripts/appliquer_taches.py              # aperçu, n'écrit rien
python3 IA/skills/cron/scripts/appliquer_taches.py --appliquer  # exécute
```

`--config` **n'écrit rien** : il affiche un gabarit, à rediriger soi-même. Ce
fichier n'est pas versionné, et c'est délibéré — il nomme le harness qui lance
un agent, ce que le coffre ne fait jamais (§3 de `VAULT-CONTRACT.md`). Tant que
`commande_agent` est vide, une tâche `mode: agent` est **refusée** plutôt
qu'instanciée inerte. Une tâche `mode: commande` n'a besoin d'aucune de ces
deux premières lignes.

Le script compare ensuite le registre aux unités `obsia-*` présentes, affiche
le tableau des écarts, et n'écrit qu'avec `--appliquer`. C'est le seul script
du dépôt qui dépende d'un exécutant — il vit donc dans le skill qui s'en sert,
pas dans `scripts/`, qui reste utilisable sans rien installer.

`IA/system/taches-index.md`, généré comme les autres index, met le registre en
contexte permanent : un harness neuf sait que ces tâches existent. Il ne les
crée pas pour autant sur la machine — l'instanciation reste un geste explicite.

## Démarrage

```bash
git clone https://github.com/kevines-ods/OBSIA
cd OBSIA
python3 scripts/installer.py --sonder     # ce que la machine porte, n'écrit rien
python3 scripts/installer.py --appliquer  # retient les modules utiles
python3 scripts/generer_prompt.py -o prompt-systeme.md --mcp
```

Le fichier `prompt-systeme.md` produit est à donner comme prompt système au
harness. L'option `--mcp` liste en plus les serveurs MCP que les agents
déclarent, avec un squelette de configuration à compléter.

Régénérer le prompt après toute modification d'un agent ou d'un skill.

## Installation modulaire

Le coffre est un **catalogue**, pas une livraison. Tout y est déclaré ; rien
n'oblige à tout retenir. Un poste sans Docker n'a que faire des skills qui
pilotent des conteneurs : ils occuperaient le contexte, se proposeraient au
mauvais moment, et échoueraient là où il aurait fallu qu'ils se taisent.

Un **module** (`IA/system/modules/<nom>.md`) regroupe ce qui n'a de sens
qu'ensemble, et chaque agent, skill, MCP et tâche déclare le sien. L'index
généré `IA/system/modules-index.md` les liste tous — y compris ceux qu'on n'a
pas retenus, parce qu'un catalogue dont on ignore les entrées absentes n'est
plus un catalogue.

```bash
python3 scripts/installer.py --sonder              # détection, verdict des sondes
python3 scripts/installer.py                       # aperçu, n'écrit rien
python3 scripts/installer.py --appliquer           # écrit le profil, en place
python3 scripts/installer.py --installer ~/coffre/OBSIA --appliquer
python3 scripts/installer.py --tout --appliquer    # revient au catalogue complet
```

L'installeur **sonde puis demande** : il constate que `docker` est installé, il
ne sait pas si vous voulez gérer des conteneurs. La sonde propose un défaut, la
question tranche. Quatre formes de sonde seulement — `commande:`, `fichier:`,
`distribution:`, `parent:` — et aucune qui exécute une commande arbitraire ou
ouvre le réseau.

Deux modes :

- **en place** — rien n'est déplacé ni supprimé, seuls les fichiers générés
  sont réduits au profil. `git checkout -- IA` remet tout ;
- **copie** (`--installer CIBLE`) — seuls les fichiers retenus atterrissent
  dans la cible, et les déclarations d'agents y sont réduites pour rester
  cohérentes.

Le profil vit dans `obsia.local.yml`, à la racine, **non versionné** : il
décrit cette machine, pas le coffre. Sans profil, tout le catalogue est actif —
c'est l'état du dépôt de distribution et celui sous lequel la CI vérifie. Règles
complètes au §13 de `IA/system/VAULT-CONTRACT.md`.

## Vérifier le coffre

Avant de committer :

```bash
python3 scripts/regenerate_sommaire.py
python3 scripts/regenerate_index.py
python3 scripts/verifier_coffre.py
```

`verifier_coffre.py` refuse un frontmatter invalide, un `name` qui ne
correspond pas au nom du fichier, une liste écrite en chaîne, une description
repliée sur plusieurs lignes, un agent déclarant un skill ou un MCP
inexistant, une tâche sans instruction ou au `quand` non quoté, un nom de note
en double, ou un fichier généré périmé. Il n'écrit rien et sort en code 1.

Les mêmes contrôles tournent en intégration continue à chaque poussée. Aucune
dépendance : bibliothèque standard de Python uniquement.

Pour les lancer automatiquement avant chaque commit, une fois par clone :

```bash
git config core.hooksPath .githooks
```

## Format

Un skill est un fichier `IA/skills/<nom>.md`. Quand il grossit — au-delà de
500 lignes environ — il devient un dossier `IA/skills/<nom>/` dont le point
d'entrée s'appelle `<nom>.md`, et non `SKILL.md`, aux côtés de `references/`,
`scripts/` et `assets/`. Détail dans `VAULT-CONTRACT.md` §5.

Tout fichier agent ou skill commence par un frontmatter YAML strict.

```yaml
---
schema: 1
kind: skill              # agent | skill | mcp | tâche | contract
name: nom-du-skill       # minuscules, tirets, identique au nom du fichier
description: Une ligne — quoi et quand.
type: core               # skills uniquement : core | outil
read_only: true
---
```

Pour un agent :

```yaml
---
schema: 1
kind: agent
name: nom-de-lagent
description: Une ligne.
skills:
  - premier-skill
  - second-skill
mcp:
  - nom-du-serveur
read_only: false
---
```

Les listes s'écrivent avec des tirets, une entrée par ligne. `skills: a, b`
vaut une chaîne de caractères, pas une liste.

Ce frontmatter est la frontière entre le coffre et tout programme qui le lit.
`schema` permet de le faire évoluer sans casser les consommateurs existants.

## Règles

Elles vivent dans `IA/system/VAULT-CONTRACT.md`, qui fait foi. En
résumé :

- Le coffre est en lecture seule pour les agents. Les modifications passent par
  des patches Git soumis à revue.
- Aucune suppression sans archivage préalable.
- Aperçu obligatoire avant toute action touchant plusieurs fichiers.
- Les fichiers générés — `sommaire.md`, `agents-index.md`, `skills-index.md`,
  `taches-index.md`, `IA/README.md` — sont régénérés par script, jamais édités à la main. Si un
  index contredit un frontmatter, le frontmatter a raison.
- Un agent et un skill sont deux choses distinctes. Un agent décide ; un skill
  décrit une manière de faire.

## Secrets

Le dépôt est public. Ne doivent jamais y entrer : clés, jetons, mots de passe,
adresses IP privées, noms d'hôtes internes.

Les inventaires réels (machines, instances LLM) vivent hors du dépôt. Seuls des
gabarits `*.example.yml` sont versionnés.

Vérifier avant de pousser :

```bash
git diff --cached | grep -iE "password|token|api[_-]key|BEGIN.*PRIVATE KEY"
```

Un secret poussé puis effacé reste dans l'historique Git. Si cela arrive :
révoguer le secret d'abord, nettoyer l'historique ensuite.

## Public et privé

Le dépôt de travail est **privé** : il porte la mémoire, les logs de session et
le profil de son propriétaire. Ce dépôt-ci, public, en est la **distribution** :
le même coffre, moins ce qui décrit une personne ou une machine.

Le privé fait foi, et `scripts/publier.py` en dérive le public. Le sens unique
n'est pas qu'une précaution : c'est ce qui crée la **fenêtre de validation**.
Le privé est l'atelier — une fonctionnalité y naît, s'y éprouve sur des séances
réelles, et ne franchit la frontière que le jour où on lance la commande. Rien
ne part tout seul.

À savoir avant de basculer un dépôt existant en privé : **cela ne dépublie pas
son passé**, qui reste chez qui l'a cloné. Le dépôt public, lui, part propre —
`publier.py` écrit dans un clone neuf, sans y verser l'historique du privé.

```bash
python3 scripts/publier.py --cible ~/OBSIA-public              # aperçu
python3 scripts/publier.py --cible ~/OBSIA-public --appliquer
python3 scripts/publier.py --cible ~/OBSIA-public --appliquer \
        --depot-public mon-compte/OBSIA --commit
```

`--depot-public` réécrit les `git clone https://github.com/…` de la
documentation : le README du privé annonce l'adresse du privé, qui donnerait un
404 à un lecteur du public sans lui dire pourquoi.

Il exporte l'arbre suivi par Git à `HEAD` — jamais le répertoire de travail,
parce que ce qui n'est pas suivi n'a pas été relu —, vide `mémoire/`,
`IA/system/session-log/`, `brouillon/` et `.archive/` de tout sauf leurs
`README.md`, passe un contrôle de fuite, régénère les index, vérifie le coffre
obtenu, puis écrit dans la cible. Il ne pousse jamais.

Le contrôle de fuite vise des **valeurs**, pas les mots qui les nomment : une
adresse de courriel, une IP privée, un bloc de clé privée, un préfixe de jeton
connu, un secret affecté à une variable. Il bloque la publication ; `--forcer`
passe outre, et s'en servir sans avoir lu la trouvaille revient à se priver du
dernier filet.

## Licence

**GNU AGPL-3.0-or-later** — texte complet dans [`LICENSE`](LICENSE).

Le copyleft est délibéré : un dérivé d'OBSIA reste libre, y compris s'il n'est
jamais distribué mais seulement exposé à travers un réseau (§13 de la licence).

Outils libres exclusivement. Vérifier la licence de tout skill importé d'une
autre source avant de l'intégrer : certains catalogues publient sous licence
restrictive, et une licence incompatible avec l'AGPL ne peut pas entrer ici.
