---
schema: 1
kind: skill
name: createur-de-skill
description: Concevoir un nouveau skill OBSIA ou en réviser un — périmètre, dosage, découpage, frontmatter — et rédiger une fiche MCP de `IA/MCP/`. À charger avant d'écrire ou de modifier un fichier de `IA/skills/` ou de `IA/MCP/`, y compris pour n'en changer que la description. Ne sert pas à exécuter un skill existant.
type: core
read_only: false
---

# Skill — Créateur de skill

Guide de conception des skills du coffre. À charger quand on crée un skill ou
qu'on en révise un.

> **Adaptation.** Version condensée du `skill-creator` d'origine (357 lignes),
> traduite et alignée sur les conventions OBSIA. Le principe « la concision est
> la règle » s'applique d'abord à ce fichier lui-même.

## Ce qu'est un skill

Un skill est un paquet autonome qui apporte une compétence procédurale : un
savoir-faire qu'un modèle ne peut pas deviner. Ce n'est pas un agent : il ne
décide pas, il explique comment faire.

## Principe 1 — La fenêtre de contexte est un bien commun

Elle est partagée entre le system prompt, l'historique, les métadonnées de tous
les autres skills, et la demande réelle de l'utilisateur.

**Partir du principe que le modèle est déjà compétent.** N'ajouter que ce qu'il
ne peut pas savoir : les spécificités de ton coffre, tes conventions, tes
chemins. Pour chaque paragraphe, se demander s'il justifie son coût en tokens.

Un exemple concis vaut mieux qu'une explication longue.

## Principe 2 — Doser la liberté laissée à l'agent

| Situation | Forme à donner |
| --- | --- |
| Plusieurs approches valables, ça dépend du contexte | instructions en texte |
| Un motif préféré existe, des variantes acceptables | pseudo-code, script paramétré |
| Opération fragile, l'ordre compte, erreurs coûteuses | script précis, peu de paramètres |

L'image : un chemin en terrain ouvert n'a pas besoin de barrières ; une
passerelle au-dessus du vide, si.

## Principe 3 — Divulgation progressive

Trois niveaux de chargement :

1. **Frontmatter** (`name` + `description`) — toujours en contexte. C'est le seul
   élément qui détermine si le skill se déclenche. Il doit dire clairement
   *quoi* et *quand*.
2. **Corps du fichier** — chargé seulement si le skill se déclenche. Viser moins
   de 500 lignes.
3. **Ressources annexes** — chargées à la demande, ou exécutées sans jamais être
   lues. Pas de limite de taille.

Quand le corps approche des 500 lignes, découper. Et toujours **référencer
explicitement** les fichiers extraits depuis le corps, en disant quand les lire :
un fichier qu'on ne sait pas exister n'est jamais consulté.

## Structure d'un skill

Par défaut, un skill est **un seul fichier** : `IA/skills/<nom>.md`. C'est la
forme de tous les skills du coffre aujourd'hui — le plus gros fait 187 lignes.

Quand le corps approche des 500 lignes, ou qu'une information devient
consultative plutôt que procédurale, passer à la **forme dossier** :

```
IA/skills/<nom>/
├── <nom>.md          point d'entrée — porte le nom du dossier, PAS `SKILL.md`
├── scripts/          code exécutable — déterministe, non chargé en contexte
├── references/       documentation à charger au besoin
└── assets/           fichiers réutilisés dans la sortie (gabarits, polices)
```

- **`scripts/`** : quand le même code est réécrit sans arrêt, ou quand il faut
  un résultat fiable et reproductible.
- **`references/`** : schémas, doc d'API, procédures détaillées. Une information
  vit soit dans le corps, soit dans une référence — **jamais les deux**, sinon
  les deux divergent. Chaque fichier extrait est **cité depuis le corps**, en
  disant quand le lire ; `scripts/verifier_coffre.py` avertit sinon.
- **`assets/`** : ce qui finit dans le résultat produit, pas dans le contexte.

> Le nom `SKILL.md`, courant ailleurs, est écarté ici : le §5 du contrat exige
> que le fichier porte le `name`, et le §6 l'unicité des noms de notes dans le
> coffre parent. Douze fichiers `SKILL.md` rendraient les rétroliens Obsidian
> ambigus.

## Ce qu'un skill ne doit PAS contenir

Pas de `README.md`, pas de `GUIDE-INSTALLATION.md`, pas de `CHANGELOG.md`, pas
de notes sur la façon dont le skill a été fabriqué. Un skill contient ce qu'il
faut pour faire le travail, rien d'autre. Le reste est de l'encombrement.

## Conventions OBSIA

Tout skill du coffre respecte le frontmatter défini dans
`../system/VAULT-CONTRACT.md` :

```yaml
---
schema: 1
kind: skill
name: nom-du-skill
description: Une ligne qui dit quoi et quand.
type: core        # ou: outil
read_only: true   # ou: false
---
```

Rappels qui découlent du contrat :

- Les règles communes (sandbox, preview, archivage, écriture par patch) ne sont
  **pas recopiées** dans le skill. On y renvoie.
- Le nom du fichier est identique au champ `name`.
- Les noms doivent être uniques dans tout le coffre parent, pas seulement dans
  `OBSIA/` — les rétroliens Obsidian ignorent la frontière git.

## Frontmatter d'une fiche MCP

Une fiche de `IA/MCP/` décrit un **outil**, pas un interlocuteur : ni
`read_only` (elle n'écrit rien par elle-même, c'est l'agent qui l'appelle), ni
`skills`.

```yaml
---
schema: 1
kind: mcp
name: nom-du-serveur     # identique au nom du fichier
description: Une ligne qui dit quoi et quand.
type: tool               # seule valeur à ce jour
transport: stdio         # ou: http — comment le harness joint le serveur
permission: normal       # ou: elevated
---
```

Deux pièges, et ils se paient tous les deux plus tard :

- **`type: tool` n'est pas le `type` d'un skill.** Même clé, vocabulaire
  distinct : un skill porte `core` ou `outil`, une fiche MCP porte `tool`.
  Recopier le frontmatter d'un skill produit un fichier que le vérificateur
  refuse.
- **`permission` gradue la prudence *avant* l'appel, jamais la trace après.**
  Mettre `elevated` dès qu'un système externe est touché — réseau, dépôt
  distant, navigateur. `normal` ne dispense pas de consigner l'usage : c'est la
  règle du contrat, et elle vaut pour les deux valeurs.

Le corps de la fiche porte ce que le frontmatter ne peut pas dire : les outils
exposés, leurs permissions réelles, et les **limites propres à ce serveur**.
C'est là que ça compte — un serveur de fichiers peut techniquement écrire
partout, et c'est sa fiche, pas le serveur, qui dit où il a le droit d'écrire.

Une fiche que **personne ne déclare** est du code mort : un MCP n'est utilisable
que déclaré par un agent, et le vérificateur signale ceux qui ne le sont pas.

## La table des rationalisations

Un skill procédural finit par une table des **excuses que l'agent se donne
pour sauter l'étape**, et de ce qui les rend fausses :

```markdown
## Rationalisations

| Ce qu'on se dit | La réalité |
| --- | --- |
| « j'écrirai les tests après » | non. Et écrits après, ils testent l'implémentation, pas le comportement |
| « je relance la suite pour être sûr » | après une exécution propre, la relancer sans avoir rien changé n'apporte rien |
```

Ce n'est pas de la décoration. Une procédure dit quoi faire ; elle ne résiste
pas à la phrase qui la contourne — et c'est toujours la même poignée de
phrases. Les écrire, c'est les désarmer d'avance : l'agent qui se surprend à
les formuler reconnaît le raccourci au lieu de le prendre.

Deux règles pour qu'elle serve :

- **la colonne de gauche se cite au discours direct**, telle qu'on se la dit.
  Une excuse reformulée en langage technique ne se reconnaît plus ;
- **la colonne de droite donne la conséquence concrète**, pas un rappel de la
  règle. « Le `skip` restera » agit ; « c'est interdit » non.

Une table de cinq à sept lignes suffit. Au-delà, on y range des règles qui
appartiennent au corps du skill.

## Procédure de création

1. Écrire d'abord le `description` du frontmatter. S'il est difficile à écrire,
   c'est que le périmètre du skill n'est pas clair : le retravailler avant tout
   le reste.
2. Écrire le corps minimal : la procédure, rien de plus.
3. Extraire dans `references/` tout ce qui est consultatif plutôt que procédural.
4. Relire en supprimant : chaque phrase que le modèle connaît déjà est du poids
   mort.
5. Vérifier qu'aucune règle du contrat n'a été recopiée par inadvertance.
6. Écrire la table des rationalisations — les excuses, pas les règles.
