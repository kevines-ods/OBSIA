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
│                            prompt-fondateur.md (intention d'origine)
├── mémoire/                 par agent → profil, préférences, expériences, projets
├── brouillon/               zone de travail libre
├── scripts/
│   ├── generer_prompt.py    prompt système depuis les frontmatters
│   ├── regenerate_index.py  les trois index et IA/README.md
│   ├── regenerate_sommaire.py  les sommaire.md de mémoire/
│   └── verifier_coffre.py   cohérence du coffre — utilisé en CI
├── HISTORIQUE.md            ce qui a été décidé puis écarté
├── LICENSE                  AGPL-3.0-or-later
├── README.md
└── .gitignore
```

Il n'y a pas de sous-dossier « coffre » : le dépôt lui-même en tient lieu. Pour
l'utiliser dans Obsidian, cloner `OBSIA/` **dans** un coffre Obsidian existant —
c'est ce coffre-là qu'on appelle ici le *coffre parent*.

Le coffre ne connaît aucune interface et n'en nomme aucune. Il décrit *quoi*
faire ; le harness de ton choix fournit *avec quoi*. Rien ici ne dépend d'un
programme particulier — c'est la condition pour qu'OBSIA reste libre de ses
mouvements.

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

Le passage du registre aux timers systemd est outillé :

```bash
python3 IA/skills/cron/scripts/appliquer_taches.py             # aperçu
python3 IA/skills/cron/scripts/appliquer_taches.py --appliquer  # exécute
```

Il compare le registre aux unités `obsia-*` présentes, affiche le tableau des
écarts, et n'écrit qu'avec `--appliquer`. C'est le seul script du dépôt qui
dépende d'un exécutant — il vit donc dans le skill qui s'en sert, pas dans
`scripts/`, qui reste utilisable sans rien installer.

`IA/system/taches-index.md`, généré comme les autres index, met le registre en
contexte permanent : un harness neuf sait que ces tâches existent. Il ne les
crée pas pour autant sur la machine — l'instanciation reste un geste explicite.

## Démarrage

```bash
git clone https://github.com/kevines-ods/OBSIA
cd OBSIA
python3 scripts/generer_prompt.py -o prompt-systeme.md --mcp
```

Le fichier `prompt-systeme.md` produit est à donner comme prompt système au
harness. L'option `--mcp` liste en plus les serveurs MCP que les agents
déclarent, avec un squelette de configuration à compléter.

Régénérer le prompt après toute modification d'un agent ou d'un skill.

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
révoquer le secret d'abord, nettoyer l'historique ensuite.

## Licence

**GNU AGPL-3.0-or-later** — texte complet dans [`LICENSE`](LICENSE).

Le copyleft est délibéré : un dérivé d'OBSIA reste libre, y compris s'il n'est
jamais distribué mais seulement exposé à travers un réseau (§13 de la licence).

Outils libres exclusivement. Vérifier la licence de tout skill importé d'une
autre source avant de l'intégrer : certains catalogues publient sous licence
restrictive, et une licence incompatible avec l'AGPL ne peut pas entrer ici.
