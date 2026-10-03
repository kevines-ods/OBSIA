---
schema: 1
kind: skill
name: cloture-de-session
description: Tenir le carnet d'un chantier et clore une séance — reprendre un chantier interrompu au démarrage, écrire l'étape en cours avant d'agir, mettre à jour le résumé du projet, distiller le durable vers profil/préférences/expériences, archiver les carnets d'un projet clos. À charger au démarrage pour reprendre après une coupure, et en fin de séance ou quand un lot de travail est livré.
module: noyau
type: core
read_only: false
---

# Skill — Clôture de session

Une session laisse deux traces de nature différente : ce qui s'est **passé**
(le carnet, propre au chantier) et ce qui a été **appris** (durable,
transversal). Sans distillation explicite, la seconde reste enfouie dans la
première et se re-découvre à chaque fois.

## Procédure

### 1. Établir ce qui a été touché

```bash
git status --short
git log --oneline origin/main..HEAD
```

Ne pas se fier à sa mémoire de la conversation : lire le diff.

### 2. Mettre à jour le carnet et le résumé

**D'abord, où.** Le §6 et le §7.3.1 donnent deux domiciles, selon ce que
décrit le projet :

| La séance portait sur… | Carnet et résumé dans… |
| --- | --- |
| le coffre lui-même — un skill, un agent, une règle | `mémoire/projets/<projet>/` — versionné, entre dans la PR |
| un projet de l'utilisateur | `Mon coffre/-PROJETS/<projet>/` — preview à la création (§7.4) |
| rien de tout cela — dépannage, correction ponctuelle | le carnet du jour du projet de domaine (§6) : `obsia`, ou `-PROJETS/<domaine>/` |
| une tâche terminée qui laisse un état à tenir à jour | `Mon coffre/-PERSONNELS/<sujet>.md`, avec `auteur: <nom-agent>` |

Test : *est-ce que ça décrit le coffre ?* Si oui, `mémoire/projets/` ; si
non, rien n'entre dans le dépôt. Dans le doute, demander plutôt que de créer
un projet par défaut — une tâche terminée n'est pas un projet.

**Le carnet** — `carnets/AAAA-MM-JJ-<projet>-<sujet>.md`, un par chantier.
Il s'écrit **pendant** la séance (voir « En cours de route » plus bas) ; à
la clôture, on le relit, on complète, on règle `statut:`.

```markdown
---
agent: <nom-agent>
projet: <projet>
statut: en cours | en attente | clos
---

# <Sujet>

## Demande
## Plan
## Étape en cours        écrite AVANT d'agir
## Fait                  dont actions à effet externe, horodatées (§9)
## Worktrees et branches
## Questions en attente
```

Aucune valeur que le §9 interdit — IP, nom d'hôte interne, URL interne,
identifiant —, même dans le privé.

**Le résumé** — `<projet> — résumé.md`, à la racine du projet, **vivant** :
où en est le projet, ce qui a été décidé, ce qui reste. Une seule note,
corrigée sur place. Le §8 impose d'y distinguer évidence, interprétation et
synthèse.

**Clore un projet.** Le corps du résumé n'est pas réécrit : le bilan, c'est la
section `## État` posée par-dessus. On coiffe ainsi :

| Élément | Règle |
| --- | --- |
| `statut:` | `clos`, dans le frontmatter |
| bandeau | **juste sous le H1**, avant le `## État`. Sous-projet : `> Sous-projet de [[<projet> — résumé\|<projet>]], clos le <AAAA-MM-JJ>.` Projet racine : `> Clos le <AAAA-MM-JJ>.` — jamais de lien vers un parent qui n'existe pas |
| bilan | un `## État` **juste après le H1** : le résultat atteint, ce qui reste, ce qui rouvrirait. Posé par-dessus le corps, sans le réécrire |
| `description:` | réécrite pour dire l'issue (« … clos le <AAAA-MM-JJ> »), pas l'enquête |

Le carnet passe `statut: clos` et rejoint `archives/` ; sa section
`## Étape en cours` devient un avis de clôture, l'état de la séance restant
conservé en citation.

### 3. Distiller — l'étape qui se saute toujours

Relire la note qu'on vient d'écrire et se demander, ligne par ligne : **est-ce
que ça ne vaut que pour ce projet ?** Si non, ça remonte, selon le tableau du
§6 :

| Ce qu'on a appris | Destination |
| --- | --- |
| un fait stable sur l'utilisateur, son poste, son infrastructure | `mémoire/profil-utilisateur.md` |
| un goût, une règle qui vaudra ailleurs | `mémoire/préférences/<sujet>.md` |
| une leçon tirée d'un échec ou d'une réussite | `mémoire/<nom-agent>/expériences/<sujet>.md` |

Les deux premières destinations sont **communes à tous les agents** : on y
corrige sur place, sans patch. Seul `expériences/` appartient à l'agent.

**Lire d'abord la note durable existante.** Un fait qui change se corrige sur
place ; il ne s'écrit pas une seconde fois à côté. C'est la règle du §10.3.

Ce qui ne remonte jamais : un détail d'exécution, une supposition non vérifiée,
un secret, ou une leçon qu'on n'a pas réellement éprouvée.

### 4. Compiler la leçon — sinon elle ne servira jamais

Une leçon rangée dans `expériences/` ne change rien tant que le skill que
l'agent lit pour agir ne la porte pas. Pour chaque leçon écrite à l'étape 3,
une question : **quel skill aurait évité ça ?**

| Réponse | Ce qu'on fait |
| --- | --- |
| aucun skill n'est en cause | rien — la leçon reste une note, c'est une réponse valable |
| un skill existant | le modifier via `createur-de-skill` |
| le geste n'a pas de skill | le noter comme skill à créer, sans le créer dans la foulée |

Ce qui passe dans le skill est **la règle**, pas le récit : le skill dit quoi
faire, la note garde le symptôme, la cause et comment on l'a su. Recopier la
note dans le skill l'alourdit et fait diverger les deux à la première
correction.

Dans les deux derniers cas, ajouter une ligne à
`IA/system/impact-des-skills.md` — dossier `IA/system/`, donc **patch soumis à
revue** (§2).

**Une seule leçon compilée par clôture.** Deux skills modifiés dans le même
patch, et plus rien ne dit lequel a aidé.

### 5. Surveiller la taille

Un résumé ou un carnet dépassant **~6 000 caractères** mérite d'être découpée ou
résumée. Repère mesuré le 2026-09-03 : la note moyenne du coffre fait 3 200
caractères, et une seule note de 15 900 en représentait alors 29 % à elle
seule. Une note qui enfle est le vrai risque de surcharge — pas l'absence de
couche d'index.

```bash
find mémoire -name '*.md' ! -name sommaire.md -exec wc -m {} \; | sort -rn | head -5
```

### 6. Pas de log de session

Le carnet **est** la trace (§9). `IA/system/session-log/` est archivé : on
n'y écrit plus. Pour un projet du coffre, carnet et résumé entrent dans la
pull request du travail, et se relisent avec le diff.

### 7. Régénérer et vérifier

```bash
python3 scripts/regenerate_sommaire.py
python3 scripts/regenerate_index.py
python3 scripts/verifier_coffre.py
```

## Contraintes

Les zones d'écriture directe et celles qui passent par patch sont définies au
§2 de `../system/VAULT-CONTRACT.md`. La distillation écrit dans `mémoire/`
— zone directe, sauf le dossier d'un autre agent.

## En cours de route — tenir le carnet

Ce skill se charge aussi **au démarrage** et **avant chaque étape**, pas
seulement à la fin : un carnet écrit après coup ne sert pas à reprendre.

- **Au démarrage** (§10, étape 0) : chercher ses carnets en cours.

  ```bash
  principal=$(git worktree list --porcelain | sed -n '1s/^worktree //p')
  git worktree list --porcelain | sed -n 's/^worktree //p' \
    | while IFS= read -r arbre; do
        grep -rl --include='*.md' -e '^statut: en cours' "$arbre/mémoire/projets"
      done | xargs -r -d '\n' grep -l '^agent: <nom-agent>'
  grep -rl --include='*.md' -e '^statut: en cours' "$principal/../-PROJETS" \
    | xargs -r -d '\n' grep -l '^agent: <nom-agent>'
  ```

  Le coffre parent s'atteint depuis l'**arbre principal**, jamais depuis
  `..` : un worktree vit ailleurs. Si `"$principal/../-PROJETS"` n'existe
  pas, le dire — une recherche vide n'est pas « aucun carnet ».
  Le carnet d'un chantier du coffre vit dans le **worktree** du chantier
  (§2.1) : chercher dans l'arbre principal seul ne le trouve pas. Et un
  worktree peut disparaître — un dossier temporaire vidé au redémarrage — :
  **commiter le carnet à chaque étape**, c'est ce qui le fait survivre.

  Pour chacun, rapprocher le carnet de l'état réel — `git status`,
  `git worktree list`, existence des fichiers et worktrees cités. Dire à
  l'utilisateur ce qui concorde et ce qui diffère. S'il y en a plusieurs, les
  lister : **l'utilisateur choisit**, l'agent ne reprend pas d'office.
- **Avant chaque étape** : écrire `## Étape en cours` — ce qu'on va faire,
  sur quels fichiers. Puis agir.
- **Après une action à effet externe** : une ligne horodatée sous `## Fait`.
