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

Emplacement attendu : `obsia_vault/IA/system/VAULT-CONTRACT.md`

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

- Le coffre est en **lecture seule pour les agents**, à l'exception du dossier
  `brouillon/` (écriture autorisée) et du périmètre spécial du §3.
- Toute modification durable passe par un **patch Git** soumis à revue humaine.
- Aucune suppression sans archivage préalable dans `.archive/`.
- Toute action touchant plusieurs fichiers exige un **preview** affiché avant
  exécution, listant les chemins concernés.
- Les fichiers `sommaire.md` ne sont **jamais** édités à la main ni par un agent :
  ils sont régénérés par `scripts/regenerate_sommaire.py` (chemin relatif depuis
  `IA/system/` : `../../scripts/regenerate_sommaire.py`).

## 3. Périmètre spécial — accès au framework `build/`

L'agent **`assistant`** (agent de base de l'app) est le **seul** autorisé à lire
et modifier le framework `build/` (UI React + backend Rust/Tauri).

- Toute modification de `build/` passe par un **patch Git revu** — jamais de
  commit direct sur `main`.
- Toute modification backend Rust doit passer **`cargo check` + `cargo clippy` +
  `cargo test`** avant validation.
- **Jamais de secret** (clé API, token) dans le code : variables d'env ou config
  chiffrée uniquement.
- Ajouter une fonctionnalité = d'abord un **skill** documenté dans `IA/skills/`,
  puis l'implémentation.

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
| `false` | **Écriture hors coffre autorisée** ; dans le coffre, uniquement dans `brouillon/` — le reste passe par patch Git revu. |

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

- Le coffre est `obsia_vault/`, imbriqué dans un coffre Obsidian parent. Les
  rétroliens Obsidian se résolvent à l'échelle du coffre entier, **pas** de
  `obsia_vault/`.
- Conséquence : les noms de notes doivent être **uniques dans tout le coffre**.
- Les liens vers ce contrat s'écrivent en chemin relatif depuis `IA/agents/` ou
  `IA/skills/` : `../system/VAULT-CONTRACT.md`.
- **Structure de la mémoire** : `mémoire/<nom-agent>/<nom-projet>/AAAA-MM-JJ-titre.md`.
  Les dossiers portent le **nom de l'agent** et le **nom du projet** — jamais
  `agent 1`, `agent 2`, `projets 1`, `projets 2`, etc.

## 7. Périmètre de lecture

À trancher explicitement et à consigner ici (aujourd'hui : non tranché) :

- [ ] Les agents peuvent-ils lire le coffre parent (`0-PROJETS`, `1-CONCEPTS`,
      `2-RESSOURCES`) ou sont-ils confinés à `obsia_vault/` ?

Tant que cette case n'est pas cochée, le comportement par défaut est le plus
restrictif : **confinement à `obsia_vault/`** (exception : l'agent `assistant`
et le framework `build/`, cf. §3).
