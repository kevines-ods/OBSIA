---
schema: 1
kind: skill
name: delegation-locale
description: Déléguer une tâche simple à un modèle local qui ne voit rien du coffre — résumer, reformuler, traduire, extraire en JSON, proposer des tags, trier, faire un premier jet — puis relire son résultat avant d'écrire. À charger avant tout appel du MCP `modele-local`, ou quand l'utilisateur demande de confier un travail au modèle local. Ne délègue ni raisonnement, ni décision, ni écriture.
module: modeles-locaux
type: outil
read_only: false
---

# Skill — Délégation à un modèle local

L'agent principal garde le contexte, les décisions et l'écriture. Le modèle
local exécute une consigne fermée sur un contenu fourni, et rend du texte —
rien d'autre. Il n'a ni fichier, ni outil, ni mémoire de la conversation :
tout ce qu'il sait tient dans l'appel.

L'outil est l'appel `deleguer` du MCP `modele-local` : lire sa fiche
(`../../MCP/modele-local.md`) avant le premier appel, comme le veut le §10.

## Déléguer ou non — le test

Déléguer seulement si **les quatre** sont vrais :

1. la tâche s'énonce en une consigne fermée, vérifiable d'un coup d'œil ;
2. elle ne demande aucun savoir hors de ce qu'on transmet ;
3. une erreur se voit à la relecture et ne coûte qu'un nouvel essai ;
4. vérifier le résultat coûte nettement moins que faire soi-même.

Le quatrième critère élimine le cas le plus tentant : une note courte déjà
lue. Pour contrôler son résumé contre la source, il faut la relire en
entier ; l'écrire soi-même ne coûte alors presque rien de plus, et l'appel
n'ajoute que son attente. La délégation paie sur un **lot** vérifiable par
échantillon ou par contrôle mécanique (JSON valide, valeur présente dans la
source), pas sur une pièce unique.

| Oui | Non |
| --- | --- |
| résumer un lot de notes, contrôlé par échantillon | résumer une note courte déjà lue |
| — | décider où classer une note (§7) |
| proposer des tags **dans une liste fournie** | inventer des tags hors du registre |
| reformuler, corriger l'orthographe, traduire | juger si une affirmation est vraie |
| extraire dates, liens, noms en JSON | raisonner sur plusieurs étapes |
| trier ou regrouper une liste selon un critère donné | écrire du code non trivial |
| premier jet d'un corps de note depuis un plan | relecture adverse, revue de code |

Dans le doute, ne pas déléguer : une délégation ratée coûte l'appel **et** la
relecture.

## Rédiger la consigne

Le modèle ne connaît rien du coffre ; la consigne dit tout.

- **Une seule tâche** par appel. Deux tâches = deux appels.
- **La forme de sortie, exactement** : nombre de puces, longueur, clés JSON.
  Avec `format: json`, nommer les clés attendues.
- **Les listes fermées en entier** : tags autorisés, catégories possibles.
  Jamais « les tags du coffre » — il ne les a pas.
- **Le strict nécessaire en contenu** : un extrait plutôt qu'une note entière.
  Sur un nœud CPU, chaque token transmis se paie en secondes de lecture.
- **Laisser `reflexion` à `false`** : sur une tâche fermée, le raisonnement
  multiplie le temps sans améliorer la sortie, et peut épuiser `max_tokens`
  avant la moindre réponse.

```text
consigne : Extrais les URL citées dans la note. Réponds en JSON :
           {"urls": ["..."]}. Aucune URL absente du texte.
contenu  : <corps de la note, sans le frontmatter>
```

## Relire avant d'écrire

Le résultat est un **brouillon de l'agent principal**, jamais une écriture en
soi. Avant de s'en servir :

- **Contrôler contre la source** : chaque fait, lien ou valeur extraite doit
  figurer dans le contenu transmis. Un petit modèle omet plus qu'il n'invente,
  mais il invente aussi.
- **Lire le pied de réponse** : `réponse tronquée`, `réponse vide`, `JSON
  invalide` ou `IMPOSSIBLE:` disent que l'appel a échoué — on corrige la
  consigne ou on fait soi-même, sans réessayer à l'aveugle.
- **Écrire soi-même**, selon les zones et le preview du §7 — le modèle local
  n'écrit rien.

## Confidentialité

Le contenu transmis quitte le processus de l'agent. Le serveur configuré doit
rester **sous le contrôle de l'utilisateur** — sur la machine ou sur son
réseau privé. Si son adresse désigne un service tiers, ne rien transmettre de
`-PERSONNELS/` ni aucun secret, et le signaler à l'utilisateur.

## Tracer

Chaque appel laisse une ligne dans le log de session (§9) : la nature de la
tâche et le résultat retenu ou écarté — jamais l'adresse du serveur.

## Brancher le serveur

Le serveur est `IA/skills/delegation-locale/scripts/mcp_modele_local.py` (bibliothèque standard seule),
lancé en stdio par le harness. Son adresse et son modèle passent par les
variables d'environnement décrites dans son en-tête, posées dans la
configuration du harness — la procédure générale est celle de
`configuration-mcp`.
