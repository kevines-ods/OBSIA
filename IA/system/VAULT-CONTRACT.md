---
schema: 1
kind: contract
name: vault-contract
description: Règles communes à tous les agents et skills du coffre OBSIA. Source unique de vérité.
---

# Contrat du coffre — OBSIA

Ce fichier est la **source unique** des règles qui s'appliquent à tous les agents
et tous les skills. Un fichier agent ou skill ne redéfinit jamais ces règles :
il les référence. En cas de contradiction entre ce contrat et un autre fichier,
**ce contrat fait foi**.

Emplacement attendu : `IA/system/VAULT-CONTRACT.md`, depuis la racine du dépôt.

---

## 1. Vocabulaire (à ne pas confondre)

| Terme | Nature | Emplacement | Rôle |
| --- | --- | --- | --- |
| **agent** | un interlocuteur | `IA/agents/` | possède un system prompt, mène une conversation, décide |
| **skill** | une compétence | `IA/skills/` | décrit *comment* faire une chose, ne décide pas |
| **MCP** | un outil | `IA/MCP/` | expose des actions structurées |

Un agent **utilise** des skills. Un skill n'est jamais un agent.

Piège historique à ne pas reproduire : **`obsidian-manager` est un SKILL** ; il a
longtemps été confondu avec un agent « bibliothécaire » qui n'existait pas en
tant que fichier. Toute formulation suggérant qu'un skill est un agent est une
erreur à corriger, pas une convention à suivre.

---

## 2. Écriture dans le coffre

- Le coffre est en **lecture seule pour les agents** dont `read_only: true`.
- Un agent `read_only: false` peut écrire **directement, sans patch**, dans
  trois zones seulement :
  - `brouillon/` — sans restriction ;
  - `mémoire/<son-propre-nom-d'agent>/` — jamais dans le dossier mémoire d'un
    autre agent ;
  - `IA/skills/` — uniquement s'il déclare le skill `createur-de-skill` dans
    son frontmatter.
- Tout le reste du coffre (`IA/agents/`, `IA/system/`, la structure du dépôt)
  reste protégé : toute modification durable y passe par un **patch Git**
  soumis à revue humaine. Les interventions hors du coffre relèvent du §3.
- Aucune suppression sans archivage préalable dans `.archive/`, y compris dans
  une zone en écriture directe.
- Toute action touchant plusieurs fichiers exige un **preview** affiché avant
  exécution, listant les chemins concernés — que l'écriture soit directe ou
  passe par patch.
- Les fichiers `sommaire.md` ne sont **jamais** édités à la main ni par un agent,
  même dans une zone en écriture directe : ils sont régénérés par
  `scripts/regenerate_sommaire.py` (chemin relatif depuis `IA/system/` :
  `../../scripts/regenerate_sommaire.py`).

## 3. Périmètre hors du coffre

Ce coffre ne dépend d'aucun harness et n'en connaît aucun : il décrit *quoi*
faire, le harness fournit *avec quoi*. Aucune base de code extérieure n'est
nommée ici, et aucun agent n'en a le monopole.

Quand un agent dont le frontmatter porte `read_only: false` intervient sur un
dépôt extérieur (interface, outillage, infrastructure), les règles suivantes
s'appliquent — elles ne dépendent ni du langage ni du projet :

- Toute modification passe par un **patch Git revu** — jamais de commit direct
  sur la branche par défaut.
- Les vérifications du projet visé (compilation, analyse statique, tests)
  passent **avant** de proposer le patch.
- **Jamais de secret** (clé API, jeton) dans le code : variables
  d'environnement ou configuration hors dépôt uniquement.
- Ajouter une fonctionnalité = d'abord un **skill** documenté dans
  `IA/skills/`, puis l'implémentation.

## 4. Exécution de code

- Toute exécution de code se fait en **sandbox**, sans exception.
- Aucun accès réseau implicite : il doit être demandé explicitement.
- Les secrets ne sortent jamais du coffre et ne sont jamais écrits dans une note.

## 5. Frontmatter — format obligatoire

Tout fichier agent ou skill commence par un frontmatter YAML valide.

**Champs communs**

| Champ | Type | Obligatoire | Notes |
| --- | --- | --- | --- |
| `schema` | entier | oui | version du format. Actuellement `1`. |
| `kind` | `agent` \| `skill` \| `contract` | oui | permet de valider le type sans se fier au dossier |
| `name` | texte | oui | minuscules, tirets, **sans espaces**. Identique au nom du fichier. |
| `description` | texte | oui | une ligne. Réutilisée par le générateur de sommaires. |
| `read_only` | booléen | oui | cf. sémantique ci-dessous |

**Sémantique de `read_only`**

| Valeur | Signification |
| --- | --- |
| `true` | **Lecture seule absolue** : aucune écriture nulle part (ni coffre, ni hors coffre, même via patch). |
| `false` | **Écriture directe** dans `brouillon/`, `mémoire/<nom-agent>/`, et `IA/skills/` si `createur-de-skill` est déclaré (détail au §2) ; écriture hors coffre autorisée (§3) ; le reste du coffre passe par patch Git revu. |

**Champs propres aux agents**

| Champ | Type | Notes |
| --- | --- | --- |
| `skills` | liste | une entrée par ligne, tirets YAML |
| `mcp` | liste | idem |

**Champs propres aux skills**

| Champ | Type | Notes |
| --- | --- | --- |
| `type` | `core` \| `outil` | `core` = indispensable au fonctionnement du coffre |

**Règles de syntaxe**

- Les listes s'écrivent en YAML, une entrée par ligne précédée d'un tiret.
  Jamais `skills: a, b` — ça vaut une chaîne de caractères, pas une liste.
- Les clés utilisent l'underscore (`read_only`), pas le tiret.
- Les noms (fichier, `name`) sont en minuscules avec tirets, **sans espaces**.
  Les accents sont autorisés (`bibliothécaire`, `développeur`).
- Un champ déclaré dans le frontmatter n'est **pas** répété dans le corps du
  fichier : le frontmatter est la vérité machine.

## 6. Nommage, rétroliens et mémoire

- Le coffre est la **racine du dépôt** (`OBSIA/`) : il n'y a pas de sous-dossier
  intermédiaire. Tous les chemins de ce contrat partent de cette racine.
- Le dépôt est destiné à être cloné **dans** un coffre Obsidian préexistant,
  appelé ici *coffre parent* (non versionné). Les rétroliens Obsidian se
  résolvent à l'échelle de ce coffre parent, **pas** de `OBSIA/`.
- Conséquence : les noms de notes doivent être **uniques dans tout le coffre
  parent**, pas seulement dans `OBSIA/`.
- Les liens vers ce contrat s'écrivent en chemin relatif depuis `IA/agents/` ou
  `IA/skills/` : `../system/VAULT-CONTRACT.md`.
- **Structure de la mémoire** : `mémoire/<nom-agent>/<nom-projet>/AAAA-MM-JJ-titre.md`.
  Les dossiers portent le **nom de l'agent** et le **nom du projet** — jamais
  `agent 1`, `agent 2`, `projets 1`, `projets 2`, etc.

## 7. Périmètre de lecture

À trancher explicitement et à consigner ici (aujourd'hui : non tranché) :

- [ ] Les agents peuvent-ils lire le coffre parent (`0-PROJETS`, `1-CONCEPTS`,
      `2-RESSOURCES`) ou sont-ils confinés à `OBSIA/` ?

Tant que cette case n'est pas cochée, le comportement par défaut est le plus
restrictif : **confinement à `OBSIA/`** (les interventions hors du coffre
relèvent du §3).

## 8. Sources et citations

Une note durable distingue explicitement trois natures d'information :
**évidence** (avec son URL source), **interprétation** et **synthèse produite
par un agent**. Les URLs sont regroupées en fin de fichier.

## 9. Log des sessions

À la fin de chaque session de travail, une note est **proposée en patch** dans
`IA/system/session-log/AAAA-MM-JJ.md` : décisions prises, fichiers modifiés,
questions restées ouvertes. Ce dossier vit sous `IA/system/`, donc son
écriture suit la règle générale du §2 (patch Git revu) — ce n'est pas une des
trois zones en écriture directe.

## 10. Méthode d'exécution

Ce contrat lu, l'ordre à suivre pour toute demande — un harness peut le
citer ou l'injecter, il ne le redéfinit jamais (cf. préambule) :

1. Choisis l'agent pertinent pour la demande, via `IA/system/agents-index.md`
   ou l'index fourni par le harness. S'il n'y en a qu'un, c'est lui par
   défaut. Lis `IA/agents/<nom>.md` pour son rôle et ses règles propres.
2. Identifie, PARMI les skills et les MCP déclarés par cet agent, ce qui est
   nécessaire à la demande — et seulement ça.
   - Skill : lis `IA/skills/<nom>.md`, applique la procédure décrite.
   - MCP : lis `IA/MCP/<nom>.md` avant d'appeler un de ses outils — il donne
     les permissions et les règles de sécurité propres à cet outil (marqué
     `permission: elevated` quand il touche un système externe : réseau,
     dépôt distant).
3. Mémoire — dès qu'une décision est prise ou qu'une information mérite
   d'être retrouvée plus tard : écris une entrée dans
   `mémoire/<nom-agent>/<nom-projet>/AAAA-MM-JJ-titre.md`. Le nom de projet
   est explicite (jamais « projet 1 ») ; crée le dossier s'il n'existe pas.
   Vérifie au §2 si l'écriture est directe ou passe par patch. Ne touche
   JAMAIS `sommaire.md` à la main : il se régénère via
   `scripts/regenerate_sommaire.py`.
4. Cite les chemins des fichiers utilisés dans ta réponse.

Ne charge pas de fichier « pour voir ». Si aucun skill ne correspond, réponds
directement en le signalant. Un skill `read_only: true` n'exécute aucune
commande modifiant l'état du système : s'il conclut à une action, énonce-la
sans la faire.
