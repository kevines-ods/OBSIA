---
schema: 1
kind: skill
name: createur-de-skill
description: Concevoir un nouveau skill OBSIA ou en réviser un — périmètre, dosage, découpage, frontmatter. À charger avant d'écrire ou de modifier un fichier de `IA/skills/`, y compris pour n'en changer que la description. Ne sert pas à exécuter un skill existant.
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

```
nom-du-skill/
├── SKILL.md          (obligatoire)
├── scripts/          code exécutable — déterministe, non chargé en contexte
├── references/       documentation à charger au besoin
└── assets/           fichiers réutilisés dans la sortie (gabarits, polices)
```

- **`scripts/`** : quand le même code est réécrit sans arrêt, ou quand il faut
  un résultat fiable et reproductible.
- **`references/`** : schémas, doc d'API, procédures détaillées. Une information
  vit soit dans SKILL.md, soit dans une référence — **jamais les deux**, sinon
  les deux divergent.
- **`assets/`** : ce qui finit dans le résultat produit, pas dans le contexte.

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

## Procédure de création

1. Écrire d'abord le `description` du frontmatter. S'il est difficile à écrire,
   c'est que le périmètre du skill n'est pas clair : le retravailler avant tout
   le reste.
2. Écrire le corps minimal : la procédure, rien de plus.
3. Extraire dans `references/` tout ce qui est consultatif plutôt que procédural.
4. Relire en supprimant : chaque phrase que le modèle connaît déjà est du poids
   mort.
5. Vérifier qu'aucune règle du contrat n'a été recopiée par inadvertance.
