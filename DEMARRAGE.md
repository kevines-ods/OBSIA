# Démarrage rapide

[English](GETTING-STARTED.md) | **Français**

De zéro à un premier échange avec un agent d'OBSIA, en cinq étapes. Le détail
de chaque règle vit dans `IA/system/VAULT-CONTRACT.md` (le noyau) et ses
annexes `IA/system/contrat/` ; ce guide ne dit que
l'ordre des gestes.

**Prérequis** : `git` et Python 3 — bibliothèque standard seule, rien à
installer. Obsidian est conseillé, pas obligatoire.

## 1. Cloner dans votre coffre

OBSIA se clone **à la racine** de votre coffre Obsidian, à côté de vos
notes — pas ailleurs, et pas dans un sous-dossier :

```bash
cd "/chemin/de/votre coffre"   # à remplacer par le vôtre
git clone https://github.com/kevines-ods/OBSIA
```

Vous obtenez `<coffre>/OBSIA/` — ce guide écrit `Mon coffre/` pour la racine
de votre coffre, quel que soit son nom réel. Ouvrez ensuite Obsidian sur **le coffre
entier**, pas sur `OBSIA/` seul : les rétroliens se résolvent à cette échelle.

Pas encore de coffre ? Un dossier vide fait l'affaire ; les dossiers de
connaissance (`-SAVOIRS/`, `-EN-VRAC/`…) se créent quand vous en avez besoin
(§7.1 du contrat).

## 2. Voir ce que la machine porte

```bash
cd OBSIA
python3 scripts/installer.py --sonder
```

Rien n'est écrit. L'installeur constate ce qui est installé (`docker`,
`systemctl`, Proxmox…) et en déduit les modules qu'il proposera.

## 3. Installer

```bash
python3 scripts/installer.py              # aperçu et questions, n'écrit rien
python3 scripts/installer.py --appliquer  # exécute
```

L'installeur demande, module par module, ce que vous voulez garder. À la fin :

- `OBSIA/obsia.local.yml` — votre profil, non versionné ;
- les index versionnés d'`IA/system/` et `IA/README.md` — inchangés, au
  catalogue complet : ils ne dépendent pas de la machine ;
- **`Mon coffre/AGENTS.md`** — le cerveau d'OBSIA, à la racine du coffre, là
  où les harness le cherchent. Ne l'éditez pas : il se régénère.

Changer d'avis : relancer la même commande. Tout reprendre :
`python3 scripts/installer.py --tout --appliquer` — qui supprime le profil :
sans profil, tout le catalogue est actif.

## 4. Lancer un harness depuis la racine du coffre

**Toujours depuis `Mon coffre/`**, jamais depuis `OBSIA/` : c'est là qu'est
`AGENTS.md`, et c'est de là que l'agent atteint vos notes.

```bash
cd ..                          # depuis OBSIA/, remonter à la racine du coffre
```

| Harness | Ce qu'il lit tout seul | À savoir |
| --- | --- | --- |
| Claude Code | `CLAUDE.md` s'il en trouve un, dans le dossier ou **au-dessus** ; sinon `AGENTS.md` | l'un **ou** l'autre, jamais les deux. Pour qu'il charge le contrat entier, créer `Mon coffre/CLAUDE.md` contenant la ligne `@OBSIA/CLAUDE.md` : il lira ce fichier **à la place** d'`AGENTS.md` |
| OpenCode | `AGENTS.md` | ajouter le contrat en `instructions` — voir sa fiche |
| Codex | `AGENTS.md` | plafond de 32 Kio : un coffre complet en occupe les trois quarts |
| Goose | `AGENTS.md` | l'extension `developer` doit rester active |
| DeepSeek Harness | `AGENTS.md` et `CLAUDE.md`, de `~/.dsh/` puis de chaque dossier jusqu'au dossier de travail | les lignes `@` de `CLAUDE.md` arrivent brutes, sans effet |
| AionUi (moteur Aion CLI) | `AGENTS.md`, pas `CLAUDE.md` | la règle de l'assistant doit faire lire le contrat — voir sa fiche |

Chaque harness a sa fiche dans `IA/system/adaptateurs-harness/` : elle dit
où écrire la configuration — serveurs MCP, secrets, restriction par agent.
Cette configuration, elle, vit **hors du dépôt** : aucune clé n'entre jamais
dans `OBSIA/`.

## 5. Vérifier que le cerveau est chargé

Demandez à l'agent :

> Quels agents connais-tu, et où vivent les notes de connaissance ?

Il doit citer les agents de `IA/system/agents-index.md` et le dossier
`-SAVOIRS/`. S'il répond de façon générique, ses instructions n'ont pas été
lues : vérifiez qu'`AGENTS.md` existe à la racine du coffre et que le harness a
été lancé de là. Avec Claude Code, cherchez aussi un `CLAUDE.md` au-dessus du
coffre (jusqu'à votre dossier personnel) : il passerait avant `AGENTS.md`.

## Ensuite

Les scripts du dépôt se lancent **depuis `OBSIA/`** (`cd OBSIA`) ; seul le
harness se lance depuis la racine.

- **Après avoir ajouté ou modifié un skill** : relancer l'installeur pour
  régénérer `AGENTS.md` — `python3 scripts/installer.py --rejouer --appliquer`
  reprend votre profil sans reposer les questions.
- **Avant de proposer une modification du dépôt** :
  `python3 scripts/verifier_coffre.py`. Seul `OBSIA/` est un dépôt Git ; vos
  notes ne le sont pas.
- **Aller plus loin** : `README.md` pour l'architecture, le contrat pour les
  règles, `IA/system/agents-index.md` pour savoir à quel agent parler.
