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

Un **harness** — Claude Code, OpenCode, Aider, Goose, ou l'interface de ton
choix — lit ces fichiers et exécute. Le coffre décrit *quoi* faire ; le harness
fournit *avec quoi*.

Le chargement est paresseux : le prompt système ne contient que l'index des
agents et des skills. Le contenu d'un skill n'est lu que lorsqu'il devient
nécessaire.

## Structure

```
OBSIA/
├── obsia_vault/
│   ├── IA/
│   │   ├── agents/          définition des agents
│   │   ├── skills/          compétences réutilisables
│   │   ├── MCP/             outils structurés
│   │   └── system/          VAULT-CONTRACT.md — les règles
│   ├── mémoire/             par agent → projet → entrées datées
│   └── scripts/
│       ├── generer_prompt.py
│       └── regenerate_sommaire.py
├── .gitignore
└── README.md
```

L'interface graphique vit dans un dépôt séparé : elle consomme ce coffre, elle
n'en fait pas partie.

## Démarrage

```bash
git clone https://github.com/kevines-ods/OBSIA
cd OBSIA
python3 obsia_vault/scripts/generer_prompt.py \
        --racine obsia_vault -o prompt-systeme.md --mcp
```

Le fichier `prompt-systeme.md` produit est à donner comme prompt système au
harness. L'option `--mcp` liste en plus les serveurs MCP que les agents
déclarent, avec un squelette de configuration à compléter.

Régénérer le prompt après toute modification d'un agent ou d'un skill.

## Format

Tout fichier agent ou skill commence par un frontmatter YAML strict.

```yaml
---
schema: 1
kind: skill              # agent | skill | contract
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

Elles vivent dans `obsia_vault/IA/system/VAULT-CONTRACT.md`, qui fait foi. En
résumé :

- Le coffre est en lecture seule pour les agents. Les modifications passent par
  des patches Git soumis à revue.
- Aucune suppression sans archivage préalable.
- Aperçu obligatoire avant toute action touchant plusieurs fichiers.
- Les `sommaire.md` sont régénérés par script, jamais édités à la main.
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

Outils libres exclusivement. Vérifier la licence de tout skill importé d'une
autre source avant de l'intégrer : certains catalogues publient sous licence
restrictive.
