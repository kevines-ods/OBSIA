---
schema: 1
kind: skill
name: recherche
description: Choisir où chercher avant de chercher — le coffre d'abord (ses index puis ses notes), ensuite les sites de confiance listés ici, en dernier recours le web général. À charger dès qu'une question demande une information, avant toute recherche. Ne cherche pas lui-même — il dit où chercher, `obsidian-manager` exécute.
type: core
read_only: true
---

# Skill — Recherche

Décider **où** chercher avant de chercher. Ce skill ne cherche pas : il fixe
l'ordre des sources et le routage selon la question. L'exécution revient à
`obsidian-manager` pour le coffre, et aux MCP déclarés pour l'extérieur.

**Ceci est un skill, pas un agent.**

La règle d'ensemble — accès au coffre parent, zones d'écriture,
confidentialité — est au §7 de `../system/VAULT-CONTRACT.md`, qui fait foi et
n'est pas reformulé ici.

## La cascade — trois étages, toujours dans cet ordre

1. **Le coffre** — `Mon coffre/`. On cherche ici d'abord, parce que c'est la
   réponse la plus fiable, la plus rapide, et la seule qui soit la vôtre. Les
   **index** d'abord (voir plus bas) : ils disent quoi ouvrir **sans ouvrir**.
   Les notes ensuite, et seulement celles que l'index désigne.
2. **Les sites de confiance** — la liste plus bas. Chacun porte son cas
   d'usage : on va droit à l'URL connue, sans passer par un moteur.
3. **Le web général** — en dernier recours. C'est l'étage le plus large et le
   plus bruité ; c'est pourquoi il vient en dernier.

On s'arrête au premier étage qui répond. On descend quand le niveau au-dessus
n'a **rien** donné — jamais parce qu'il « pourrait » mieux répondre.

## Routage selon la question

L'ordre ci-dessus n'est pas mécanique : le premier étage se choisit d'après la
nature de la question.

| Type de question | Commencer par | Pourquoi |
| --- | --- | --- |
| « comment j'ai fait », « qu'avais-je décidé », un fait sur la machine ou l'utilisateur | le coffre — `SAVOIRS/`, `PERSONNELS/` | la réponse est personnelle ; aucun site ne la détient |
| syntaxe, option, version d'un logiciel, API | le site de confiance correspondant, **pas** le coffre | le coffre ne suit pas les versions ; la documentation officielle, si |
| actualité, comparatif, « qu'est-ce qui se fait » | le web général | ni le coffre ni les sites de confiance ne sont à jour |
| une question déjà traitée | le coffre, par la note de projet correspondante | ne pas refaire un travail déjà fait |

Une question qui n'entre dans aucune ligne se traite par la cascade, dans
l'ordre.

## Les index du coffre parent

Un index par dossier du coffre parent, produits par
`IA/skills/traitement-des-notes/scripts/indexer_coffre_parent.py` et écrits dans
`Mon coffre/_maintenance/` :

| Index | Couvre |
| --- | --- |
| `index-savoirs.md` | les connaissances — `Mon coffre/SAVOIRS/` |
| `index-personnels.md` | le contexte personnel — `Mon coffre/PERSONNELS/` |
| `index-projets.md` | les projets — `Mon coffre/PROJETS/` |
| `index-documents.md` | revues, articles, transcriptions — `Mon coffre/DOCUMENTS/` |
| `index-en-vrac.md` | le tampon — `Mon coffre/EN-VRAC/`, vide en fin de session (§7.7) |
| `index-maintenance.md` | journaux, previews, registre — `Mon coffre/_maintenance/` |

Chaque ligne porte le fichier, sa `description` — ou, à défaut, son premier
titre — son type et ses tags. Un index se lit **avant** les notes ; il suffit à
décider quoi ouvrir.

Les index vieillissent. Ce skill ne les régénère pas : il le **constate**.

```bash
python3 IA/skills/traitement-des-notes/scripts/indexer_coffre_parent.py --verifier
```

Cette commande n'écrit rien et sort en erreur si un index est périmé ou absent.
La régénération relève d'une action assumée — jamais d'un effet de bord de la
recherche (§10).

## Les sites de confiance

Une liste courte, tenue à la main. Chaque entrée dit **ce qu'on y trouve** et
**quand y aller**. On y va par URL connue, sans moteur. Un site n'entre ici que
s'il a servi et que sa fiabilité est établie ; un site dont plus aucune question
ne relève en sort.

| Site | Ce qu'on y trouve | Quand y aller |
| --- | --- | --- |
| Documentation officielle du logiciel visé | syntaxe, options, notes de version | toute question de syntaxe ou de version, **avant** le coffre |
| Dépôt et suivi d'issues du projet | code réel, bogues connus, discussions de conception | chercher si le problème est connu, ou lire l'implémentation |
| Wiki et forum communautaires du projet | retours d'usage, contournements | quand la documentation officielle est muette |
| Serveur de questions-réponses généraliste | réponses concrètes, votées | problème de configuration courant, pas une question de version |
| SearXNG auto-hébergé (MCP `searxng`) | recherche multi-moteurs, sans traçage | dernier recours de la cascade |

Maintenir cette liste est un geste de l'utilisateur : un agent peut proposer un
ajout par patch, jamais l'imposer.

## Contraintes

Ce skill est `read_only: true` : il ne cherche rien lui-même, n'écrit nulle part,
ne régénère aucun index. Il dit où chercher ; `obsidian-manager` exécute la
recherche dans le coffre.

Deux règles du contrat s'appliquent à tout ce qu'on remonte par cette cascade :

- ce qui vient du coffre parent ne se recopie **pas** dans `OBSIA/` : le dépôt
  est public, le coffre parent ne l'est pas (§7.2) ;
- les chemins des fichiers utilisés se citent dans la réponse (§10, point 4).

> Les autres contraintes (preview, archivage, sandbox, secrets) sont définies
> dans `../system/VAULT-CONTRACT.md`.
