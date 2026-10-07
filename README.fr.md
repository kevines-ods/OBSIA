# OBSIA

[English](README.md) | **Français**

OBSIA donne à ton assistant IA une équipe d'agents spécialisés — un pour
ranger tes notes, un pour administrer tes serveurs, un pour construire des
applications, un pour relire — et une mémoire qui dure d'une conversation à
l'autre.

Tout est écrit en simples fichiers texte (Markdown) : pas de base de données,
pas de format fermé. Tu peux tout lire et tout modifier avec n'importe quel
éditeur, ou avec Obsidian si tu l'utilises.

OBSIA s'installe dans un dossier de notes, ton **coffre**. Ta mémoire (tes
notes, tes projets, ce que les agents apprennent) y reste, à côté de l'outil,
et ne part jamais avec lui.

## Comment ça marche

OBSIA repose sur trois sortes de fichiers :

- un **agent** est un interlocuteur spécialisé : son rôle, ce qu'il sait
  faire, ce qu'il a le droit de toucher ;
- un **skill** est une compétence, une procédure écrite pas à pas
  (diagnostiquer une machine, ranger une note, préparer une livraison…) ;
- une **tâche** est une action à lancer toute seule à heure fixe (par exemple
  ranger tes notes chaque matin).

OBSIA ne fait rien tout seul : il faut un outil d'IA qui lit ces fichiers et
agit, ce qu'on appelle un **harness** (Claude Code, OpenCode, Codex, Goose…).
OBSIA dit *quoi* faire, le harness fournit *avec quoi*. Tu peux changer de
harness sans rien perdre.

L'IA ne lit pas tout d'un coup : elle voit d'abord la liste des agents et des
skills, puis n'ouvre un skill que lorsqu'elle en a besoin. Elle reste ainsi
rapide, même avec beaucoup de compétences.

## Démarrage

Le guide pas à pas est dans `DEMARRAGE.md`. En bref :

```bash
mkdir -p ~/"Mon coffre" && cd ~/"Mon coffre"   # ou ton coffre existant
git clone https://github.com/kevines-ods/OBSIA
cd OBSIA
python3 scripts/installer.py --sonder     # regarde ta machine, n'écrit rien
python3 scripts/installer.py              # te pose les questions, montre ce qui sera fait
python3 scripts/installer.py --appliquer  # installe
```

Il te faut seulement `git` et Python 3 : rien d'autre à installer.

Ensuite, lance ton harness **depuis le dossier du coffre** (`~/Mon coffre`),
pas depuis `OBSIA/`. L'installeur y a posé un fichier `AGENTS.md` que la
plupart des harness lisent tout seuls. Pour le brancher, suis la fiche de ton
harness dans `IA/system/adaptateurs-harness/`.

Si ton harness ne lit pas `AGENTS.md`, tu obtiens le même texte avec
`python3 scripts/generer_prompt.py -o prompt-systeme.md --mcp` (depuis
`OBSIA/`), à lui donner comme instructions de départ. `--mcp` y ajoute un
modèle de configuration des outils branchés (MCP) que tes agents utilisent :
sans lui, ces outils ne seront pas disponibles.

## Structure

```
OBSIA/                       l'outil (ta mémoire est à côté, pas ici)
├── IA/
│   ├── agents/              les agents
│   ├── skills/              les compétences
│   ├── MCP/                 les outils branchés (GitHub, navigateur, messagerie…)
│   ├── tâches/              les actions planifiées
│   └── system/              les règles (VAULT-CONTRACT.md), les index,
│                            le catalogue des modules à installer,
│                            les fiches pour brancher chaque harness
├── brouillon/               brouillons libres
├── scripts/                 installer, vérifier, publier (Python, sans dépendance)
├── HISTORIQUE.md            ce qui a été essayé puis abandonné
├── LICENSE                  AGPL-3.0-or-later
└── README.md
```

OBSIA se place **directement dans ton coffre**, à côté de tes dossiers de
notes, et pas dans un sous-dossier. Si tu utilises Obsidian, ouvre-le sur le
coffre entier, pas sur `OBSIA/` seul : c'est ce qui permet aux liens entre
notes de fonctionner partout.

Ta mémoire (résumés de projets, carnets de travail, savoirs, profil) vit dans
les dossiers `0-…` du coffre, avec son propre historique Git. `OBSIA/` n'en
contient aucune : tu peux mettre l'outil à jour ou le réinstaller sans jamais
toucher à tes notes.

## Ton coffre — ta mémoire

OBSIA est l'outil ; le coffre qui l'entoure porte ta mémoire. Il est organisé
en quelques dossiers fixes :

| Dossier | Ce qu'il contient |
| --- | --- |
| `0-EN-VRAC/` | ce que tu déposes en vrac ; les agents le complètent puis le rangent |
| `0-SAVOIRS/` | tes connaissances : fiches, notes de référence |
| `0-PROJETS/` | tes projets en cours, avec leurs résumés et carnets de travail |
| `0-MEMOIRES/` | ce que les agents ont appris, et les projets terminés |
| `0-DOCUMENTS/` | tes documents |
| `0-PERSONNELS/` | ce qui te concerne : ton profil, tes préférences |
| `_MAINTENANCE/` | la trace de ce que les agents ont fait |

Toi seul crées ou renommes ces dossiers. Les agents lisent tout le coffre,
mais n'écrivent qu'à des endroits précis, et ils te montrent ce qu'ils vont
modifier avant de le faire.

Le coffre a **son propre historique Git**, séparé de celui d'OBSIA : chaque
modification d'un agent y est enregistrée, et tu peux toujours revenir en
arrière. Tu peux l'envoyer vers le serveur de ton choix pour le sauvegarder.

Pour que les agents atteignent tes notes, ton harness doit être lancé
**depuis la racine du coffre**, et pas depuis `OBSIA/`. Les fiches de
`IA/system/adaptateurs-harness/` expliquent comment brancher chaque harness
(Claude Code, OpenCode, AionUi…).

## Tâches automatiques

Une tâche est une action que les agents lancent tout seuls à heure fixe :
ranger tes notes chaque matin, vérifier le coffre chaque lundi… Chacune est
décrite dans un fichier de `IA/tâches/` : quand la lancer, pour quel agent, et
quoi lui demander.

Les tâches ne s'activent **pas** toutes seules à l'installation : c'est toi qui
décides lesquelles tournent sur ta machine. Pour les activer (timers systemd) :

```bash
mkdir -p ~/.config/obsia
python3 IA/skills/cron/scripts/appliquer_taches.py --config > ~/.config/obsia/appliquer.conf
$EDITOR ~/.config/obsia/appliquer.conf                          # indiquer la commande qui lance ton harness
python3 IA/skills/cron/scripts/appliquer_taches.py              # montre ce qui va changer, n'écrit rien
python3 IA/skills/cron/scripts/appliquer_taches.py --appliquer  # active
```

Si tu changes de machine ou de harness, rien n'est perdu : on relance ces
commandes et les tâches sont recréées depuis leurs fichiers. Le détail (format
d'une tâche, règles, cas particuliers) est dans le skill `cron`.

---

# Pour aller plus loin

## Choisir ce que tu installes

OBSIA est un **catalogue** : tu ne gardes que ce qui te sert. Inutile de
charger les compétences Docker si tu n'as pas de conteneurs : elles
prendraient de la place et se proposeraient au mauvais moment.

Les compétences sont regroupées en **modules** (`IA/system/modules/`), par
exemple « conteneurs », « documents » ou « construction ». À l'installation :

1. l'installeur **regarde ta machine** (Docker est-il là ? Proxmox ?
   CachyOS ?) et en déduit une réponse par défaut ;
2. il te **pose une question par module**, et c'est ta réponse qui décide ;
3. il retient tes choix dans un fichier `obsia.local.yml`, propre à ta
   machine et jamais partagé.

Il ne lance aucun programme et n'accède pas au réseau pour regarder ta
machine : il vérifie seulement si certains programmes ou fichiers sont
présents.

```bash
python3 scripts/installer.py --sonder             # ce qui a été détecté
python3 scripts/installer.py                      # les questions, et ce qui sera fait
python3 scripts/installer.py --appliquer          # applique tes choix
python3 scripts/installer.py --tout --appliquer   # revient au catalogue complet
```

Changer d'avis plus tard : relance l'installeur, il repose les questions. Le
détail (mode copie, sondes, ce qui est réduit ou non) est dans
`IA/system/installation-et-publication.md`.

## Pour contribuer : vérifier avant un commit

Avant de committer :

```bash
python3 -m unittest discover -s tests
python3 scripts/regenerate_sommaire.py
python3 scripts/regenerate_index.py
python3 scripts/verifier_coffre.py
```

La première commande lance la suite de `tests/` — les scripts, l'installeur, la
publication, la ligne de commande. Elle ne demande aucune dépendance non plus :
c'est `unittest` de la bibliothèque standard, jamais `pytest`.

`verifier_coffre.py` refuse un frontmatter invalide, un `name` qui ne
correspond pas au nom du fichier, une liste écrite en chaîne, une description
repliée sur plusieurs lignes, un agent déclarant un skill ou un MCP
inexistant, une tâche sans instruction ou au `quand` non quoté, un nom de note
en double, ou un fichier généré périmé. Il n'écrit rien et sort en code 1. Il
avertit sans refuser dès que l'`AGENTS.md` écrit approche le plafond total de
consignes de Codex (28 Kio), et refuse au-delà de 32 Kio : le fichier global et
ceux du projet comptent ensemble, et au-delà le surplus est laissé de côté.

Les mêmes contrôles tournent en intégration continue à chaque poussée. Aucune
dépendance : bibliothèque standard de Python uniquement.

Pour les lancer automatiquement avant chaque commit, une fois par clone — c'est
`installer.py --appliquer` qui l'arme (§11) :

```bash
git config core.hooksPath .githooks
```

## Format

Un skill est un fichier `IA/skills/<nom>.md`. Quand il grossit — au-delà de
500 lignes environ — il devient un dossier `IA/skills/<nom>/` dont le point
d'entrée s'appelle `<nom>.md`, et non `SKILL.md`, aux côtés de `references/`,
`scripts/` et `assets/`. Règle au §5 de `VAULT-CONTRACT.md`, détail dans
`IA/system/contrat/contrat-frontmatter.md`.

Tout fichier agent ou skill commence par un frontmatter YAML strict.

```yaml
---
schema: 1
kind: skill              # agent | skill | mcp | tâche | module | contract
name: nom-du-skill       # minuscules, tirets, identique au nom du fichier
description: Une ligne — quoi et quand.
type: core               # skills uniquement : core | outil
read_only: true
module: noyau            # obligatoire : le module du catalogue (IA/system/modules/)
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
module: noyau
---
```

Les listes s'écrivent avec des tirets, une entrée par ligne. `skills: a, b`
vaut une chaîne de caractères, pas une liste.

Ce frontmatter est la frontière entre l'outil et tout programme qui le lit.
`schema` permet de le faire évoluer sans casser les consommateurs existants.

## Règles

Elles vivent dans `IA/system/VAULT-CONTRACT.md` — le noyau, toujours chargé —
et ses annexes `IA/system/contrat/` ; le noyau fait foi. En
résumé :

- Les agents écrivent directement dans ta mémoire, mais seulement aux
  endroits prévus, et en te montrant d'abord ce qu'ils vont faire. Toute
  modification de l'outil lui-même (agents, règles) passe par une proposition
  Git que tu relis.
- Rien ne se perd : l'historique Git du coffre garde chaque version.
- Aperçu obligatoire avant toute action touchant plusieurs fichiers.
- Les fichiers générés — `sommaire.md` (dans le coffre parent), `agents-index.md`,
  `skills-index.md`, `taches-index.md`, `modules-index.md`, `IA/README.md` — sont régénérés par
  script, jamais édités à la main. Si un index contredit un frontmatter, le
  frontmatter a raison.
- Un agent et un skill sont deux choses distinctes. Un agent décide ; un skill
  décrit une manière de faire.

## Secrets

Tout ce qui entre ici se retrouve dans la distribution publique. Ne doivent jamais y entrer : clés, jetons, mots de passe,
adresses IP privées, noms d'hôtes internes.

Les inventaires réels (machines, instances LLM) vivent hors du dépôt. Seuls des
gabarits sont versionnés, comme `IA/MCP/mcp.example.json`.

Vérifie avant de pousser :

```bash
git diff --cached | grep -iE "password|token|api[_-]key|BEGIN.*PRIVATE KEY"
```

Un secret poussé puis effacé reste dans l'historique Git. Si cela arrive :
révoque le secret d'abord, nettoie l'historique ensuite.

## Public et privé

Le dépôt de travail est **privé** : il porte l'outil, ses logs de session et son
`brouillon/`. Ce dépôt-ci, public, en est la **distribution** : le même outil,
moins ce qui décrit une personne ou une machine.

La **mémoire** n'est ni dans l'un ni dans l'autre : elle a son propre dépôt, à la
racine du coffre, que tu peux sauvegarder où tu veux. Elle ne se publie pas.

Le privé fait foi, et `scripts/publier.py` en dérive le public. Le sens unique
n'est pas qu'une précaution : c'est ce qui crée la **fenêtre de validation**.
Le privé est l'atelier — une fonctionnalité y naît, s'y éprouve sur des séances
réelles, et ne franchit la frontière que le jour où on lance la commande. Rien
ne part tout seul.

À savoir avant de basculer un dépôt existant en privé : **cela ne dépublie pas
son passé**, qui reste chez qui l'a cloné. Le dépôt public, lui, part propre —
`publier.py` écrit dans un clone neuf, sans y verser l'historique du privé.

```bash
git clone https://github.com/mon-compte/OBSIA ~/OBSIA-public      # une fois
python3 scripts/publier.py --cible ~/OBSIA-public              # aperçu
python3 scripts/publier.py --cible ~/OBSIA-public --appliquer
python3 scripts/publier.py --cible ~/OBSIA-public --appliquer \
        --depot-public mon-compte/OBSIA --commit
```

`--depot-public` réécrit les `git clone https://github.com/…` de la
documentation : le README du privé annonce l'adresse du privé, qui donnerait un
404 à un lecteur du public sans lui dire pourquoi.

Il exporte l'arbre suivi par Git à `HEAD` — jamais le répertoire de travail,
parce que ce qui n'est pas suivi n'a pas été relu —, vide
`IA/system/session-log/`, `brouillon/` et `.archive/` de tout sauf leurs
`README.md` (pendant la bascule, l'ancien `mémoire/` aussi), passe un contrôle de
fuite, régénère les index, vérifie le coffre obtenu, puis écrit dans la cible. Il
ne pousse jamais.

Le contrôle de fuite vise des **valeurs**, pas les mots qui les nomment : une
adresse de courriel, une IP privée, un bloc de clé privée, un préfixe de jeton
connu, un secret affecté à une variable. Il bloque la publication ; `--forcer`
passe outre, et s'en servir sans avoir lu la trouvaille revient à se priver du
dernier filet.

## Licence

**GNU AGPL-3.0-or-later** — texte complet dans [`LICENSE`](LICENSE).

Le copyleft est délibéré : un dérivé d'OBSIA reste libre, y compris s'il n'est
jamais distribué mais seulement exposé à travers un réseau (§13 de la licence).

Outils libres exclusivement. Vérifie la licence de tout skill importé d'une
autre source avant de l'intégrer : certains catalogues publient sous licence
restrictive, et une licence incompatible avec l'AGPL ne peut pas entrer ici.
