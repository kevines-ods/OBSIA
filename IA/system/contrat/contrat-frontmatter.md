---
schema: 1
kind: contract
name: contrat-frontmatter
description: Détail du frontmatter : champs par type d'objet, sémantique de read_only, formes d'un skill, champs des MCP et des tâches.
module: noyau
---

# Annexe du contrat — frontmatter

> **À lire avant d'écrire ou de modifier un agent, un skill, un MCP, une tâche, un module ou un fichier du contrat.** Annexe du contrat (`../VAULT-CONTRACT.md`).
> Elle précise, elle n'ajoute aucune règle : toute règle qu'on peut enfreindre
> sans avoir rien chargé est aussi au noyau, et en cas de contradiction le
> noyau fait foi — l'annexe est alors à corriger. La correspondance avec l'ancien
> contrat est suivie dans `registre.md`, document de travail non normatif.

## 5. Frontmatter — format obligatoire

Tout fichier agent ou skill commence par un frontmatter YAML valide.

**Champs communs**

| Champ | Type | Obligatoire | Notes |
| --- | --- | --- | --- |
| `schema` | entier | oui | version du format. Actuellement `1`. |
| `kind` | `agent` \| `skill` \| `mcp` \| `tâche` \| `contract` | oui | permet de valider le type sans se fier au dossier |
| `name` | texte | oui | minuscules, tirets, **sans espaces**. Identique au nom du fichier. |
| `description` | texte | oui | une ligne. Réutilisée par le générateur de sommaires. |
| `read_only` | booléen | oui | cf. sémantique ci-dessous |
| `module` | texte | oui | le module du §13 auquel ce fichier appartient. Un fichier sans module est inclassable à l'installation. |

**Sémantique de `read_only`**

| Valeur | Signification |
| --- | --- |
| `true` | **Lecture seule absolue** : aucune écriture nulle part (ni coffre, ni hors coffre, même via patch). |
| `false` | **Écriture directe** dans `brouillon/`, dans la mémoire du coffre parent sous `0-PERSONNELS/` ou `0-SAVOIRS/` sauf le dossier d'un autre agent, et `IA/skills/` si `createur-de-skill` est déclaré (détail au §2), ainsi que dans les zones du coffre parent que le §7 ouvre (§7.3) ; écriture hors coffre autorisée (§3) ; le reste du dépôt passe par patch Git revu. |

**Champs propres aux agents**

| Champ | Type | Notes |
| --- | --- | --- |
| `skills` | liste | une entrée par ligne, tirets YAML |
| `mcp` | liste | idem |

**Champs propres aux skills**

| Champ | Type | Notes |
| --- | --- | --- |
| `type` | `core` \| `outil` | `core` = indispensable au fonctionnement du coffre |

**Emplacement d'un agent ou d'un skill**

Un agent vit dans `IA/agents/<nom>.md`. Un skill prend deux formes — plate
(`IA/skills/<nom>.md`) ou dossier (`IA/skills/<nom>/<nom>.md`, flanqué de
`references/`, `scripts/` et `assets/`). Dans les deux cas, le point d'entrée
porte **le nom du skill**, jamais `SKILL.md` : le `name` vaut le nom du
fichier, et le §6 impose l'unicité des noms de notes dans le coffre parent —
une douzaine de `SKILL.md` la violerait. Seul `references/` contient des
notes ; `scripts/` et `assets/` sont écartés du balayage des noms.

Quand passer d'une forme à l'autre, ce que chaque sous-dossier accueille et
comment citer une référence depuis le corps : `createur-de-skill`
(`IA/skills/createur-de-skill.md`).

**Une information vit à un seul endroit.** Écrite deux fois — dans ce contrat
et dans un skill, dans un corps et dans sa référence — elle diverge, et rien ne
le signale. C'est cette règle qui décide de ce qui entre ici : une **règle**
qu'un agent peut violer sans avoir rien chargé, jamais une **procédure** qui ne
s'applique qu'en faisant la chose.

**Champs propres aux MCP**

Un fichier de `IA/MCP/` décrit un outil, pas un interlocuteur : il n'a ni
`read_only` (il n'écrit rien par lui-même, c'est l'agent qui l'appelle) ni
`skills`. Le détail de son frontmatter — `type`, `transport`, et les valeurs
admises — vit dans `createur-de-skill` (`IA/skills/createur-de-skill.md`), avec
le reste de ce qu'on écrit en rédigeant une fiche. Deux règles restent ici :

- `permission: elevated` **dès qu'un système externe est touché** : réseau,
  dépôt distant, navigateur. `normal` gradue la prudence *avant* l'appel ; il
  ne dispense jamais de consigner l'usage *après* (§9).
- **Un MCP n'est utilisable que déclaré par un agent** (§10.2). Un fichier de
  `IA/MCP/` que personne ne déclare est du code mort : le vérificateur le
  signale.
- **Une fiche MCP porte son `module`** (§13), comme tout ce qui se déclare :
  sans lui, l'installeur ne saurait ni la retenir ni l'écarter.

**Fichiers du contrat** (`kind: contract` : ce fichier et ses annexes de
`IA/system/contrat/`) : `schema`, `kind`, `name`, `description` et `module`,
sans `read_only`.

**Champs propres aux tâches**

Un fichier de `IA/tâches/` décrit une action planifiée. Il n'a pas de
`read_only` : une tâche n'écrit rien par elle-même — c'est l'agent ou la
commande qu'elle déclenche qui agit, sous ses propres règles.

| Champ | Type | Obligatoire | Notes |
| --- | --- | --- | --- |
| `schema` | entier | oui | comme partout, actuellement `1` |
| `kind` | `tâche` | oui | |
| `name` | texte | oui | identique au nom du fichier |
| `description` | texte | oui | une ligne |
| `module` | texte | oui | comme partout — le module du §13 |
| `mode` | `agent` \| `commande` | oui | `agent` : une instruction part vers un agent, il faut donc un harness. `commande` : une commande shell, qui tourne sans modèle. |
| `quand` | texte **entre guillemets** | oui | cron à 5 champs — `"0 9 * * 1"`. Les guillemets ne sont pas décoratifs : `*/15 * * * *` non quoté est une ancre YAML invalide, et tout lecteur YAML réel refuse le fichier. |
| `fuseau` | texte | oui | `Europe/Paris`, `UTC`… Un cron sans fuseau est ambigu, et les planificateurs distants raisonnent en UTC. |
| `exécutant` | `local` \| `harness` | oui | **qui a le droit de la déclencher** — `local` : la machine (timer systemd, cron) ; `harness` : le planificateur du harness, quand il en a un. Ce n'est pas un état mais une contrainte : une tâche qui touche des fichiers locaux ne peut pas être `harness`, une tâche qui doit partir machine éteinte ne peut pas être `local`. |
| `agent` | texte | si `mode: agent` | nom d'un agent existant (§1) |
| `actif` | booléen | oui | `false` = déclarée mais non instanciée |

Le corps du fichier porte ce que le frontmatter ne peut pas contenir : une
section `## Instruction` en `mode: agent`, `## Commande` en `mode: commande`.
Elle est obligatoire et contrôlée — une tâche sans elle ne déclenche rien.

**Règles de syntaxe**

- Les listes s'écrivent en YAML, une entrée par ligne précédée d'un tiret.
  Jamais `skills: a, b` — ça vaut une chaîne de caractères, pas une liste.
- Les clés utilisent l'underscore (`read_only`), pas le tiret.
- Les noms (fichier, `name`) sont en minuscules avec tirets, **sans espaces**.
  Les accents sont autorisés (`sauvegardes-chiffrées`, `diagnostic-réseau`).
- Un champ déclaré dans le frontmatter n'est **pas** répété dans le corps du
  fichier : le frontmatter est la vérité machine.
