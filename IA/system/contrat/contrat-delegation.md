---
schema: 1
kind: contract
name: contrat-delegation
description: Détail du format du ticket et du compte rendu d'une délégation — à un sous-agent (proposer_sous_agent) ou à un membre d'équipe (bloc delegation).
module: noyau
---

# Annexe du contrat — délégation (ticket / compte rendu)

> **À lire avant de déléguer une tâche** — à un sous-agent (appeler
> `proposer_sous_agent`) ou à un membre d'équipe (émettre un bloc
> ```delegation```). Annexe du contrat (`../VAULT-CONTRACT.md`).
> Elle précise, elle n'ajoute aucune règle : toute règle qu'on peut enfreindre
> sans avoir rien chargé est aussi au noyau, et en cas de contradiction le
> noyau fait foi — l'annexe est alors à corriger.

## Le ticket (ce que l'appelant envoie)

Deux chemins, deux formes : l'outil `proposer_sous_agent` pour un sous-agent,
le bloc ```delegation``` pour un membre d'équipe. Ils ne partagent pas leurs
champs.

### Vers un sous-agent — l'outil `proposer_sous_agent`

Vocabulaire aligné sur l'outil réel (`IA/MCP/proposer-un-sous-agent.md` expose
`tache`, `chemins`, `version`). Les champs `skills`, `mcp` et `budget`
**n'existent pas dans l'outil** : seul le bloc ```delegation``` les porte (4b),
cette annexe ne les rend pas normatifs pour l'outil.

| champ | contenu | borne |
| --- | --- | --- |
| `tache` | tâche autosuffisante | obligatoire dans l'outil |
| `chemins` | fichiers ou dossiers du coffre à lire | sous la racine du coffre, hors coffre interdit |
| `version` | version d'agent proposée | catalogue `sous-agent` et lançable ; l'utilisateur peut la changer |
| `compte_rendu_attendu` | ligne que **le ticket porte lui-même** : statut + résumé borné + chemins produits + points non vérifiés | un sous-agent en lecture ne charge pas les annexes du contrat : le ticket porte cette ligne, pas seulement l'annexe |
| `skills` | skills à charger | *absent de l'outil — voir le bloc ```delegation```* |
| `mcp` | MCP à charger | *absent de l'outil — voir le bloc ```delegation```* |
| `budget` | plafond de contexte du ticket | *absent de l'outil — voir le bloc ```delegation```* |

Aujourd'hui, cette ligne voyage **dans `tache`** (le schéma de l'outil ne
déclare que `tache`, `chemins`, `version`) ; un champ dédié est prévu à l'étape 4,
comme `skills`/`mcp`.

Dans le bloc ```delegation```, `skills`, `mcp` et `budget` sont posés **par le
modèle appelant**, seul porteur possible de leurs valeurs ; ils sont
facultatifs, et ne peuvent que restreindre (tableau ci-dessous).

### Vers un membre d'équipe — le bloc ```delegation```

Le bloc est écrit **en entier par le modèle appelant**, dans sa réponse. Son
corps est **un objet JSON**, une clé par champ :

~~~
```delegation
{"agent": "<nom-d-agent>", "fournisseur": "<fournisseur>", "modele": "<modele>",
 "instruction": "<tâche autosuffisante>",
 "compte_rendu_attendu": "<ligne attendue>"}
```
~~~

Un corps qui n'est pas du JSON valide est retiré de la réponse sans
délégation, comme un bloc incomplet. Le bloc
ne porte ni `tache`, ni `chemins`, ni `version` : la version du membre est
résolue par l'interface, pas par le bloc.

| champ | contenu | borne |
| --- | --- | --- |
| `agent` | agent visé | doit avoir sa fiche dans `IA/agents/` ; sinon la délégation est refusée |
| `fournisseur` | fournisseur du tour délégué | obligatoire |
| `modele` | modèle du tour délégué | obligatoire |
| `instruction` | tâche autosuffisante | obligatoire |
| `compte_rendu_attendu` | ligne attendue : statut + résumé borné + chemins produits + points non vérifiés | **facultatif** (4b) ; l'interface l'ajoute à l'instruction reçue par le membre, le bloc publié la garde à part |
| `skills` | liste des skills à charger | **facultatif** (4b) ; restreint les skills de la fiche du membre, n'en ajoute jamais (aucun en commun : aucun skill, et le tour le dit) — **fournisseur direct seulement** : sur un pont ACP, la fiche entière, et le tour le dit ; absent : la fiche entière ; mal formé : la fiche entière, et le tour le dit |
| `mcp` | liste des MCP à charger | **facultatif** (4b) ; restreint les MCP de la version du membre, n'en ajoute jamais ; `[]` : aucun ; absent : tous ; mal formé : tous, et le tour le dit |
| `budget` | plafond de contexte du ticket | **facultatif** (4b) ; *indicatif, non appliqué* : aucun code ne le lit |

Un bloc auquel manque un champ obligatoire est retiré de la réponse sans
délégation, **en silence** : aucun tour, aucun statut, aucun avis. Sans `compte_rendu_attendu`, le bloc reste valide : l'attente peut
alors voyager dans `instruction`. Une clé hors de ce tableau (`chemins`, `version`…)
est ignorée sans refus : ce qu'elle porte n'arrive pas au membre.

## Le compte rendu (ce que le sous-agent rend)

| champ | contenu |
| --- | --- |
| `statut` | vocabulaire de `STATUTS_FINAUX` (OBSIA-UI, `sous_agents.py`) — seul vocabulaire de statut d'une délégation, aucun second n'est inventé ici ; **qui le pose** : `termine` par le sous-agent, les autres par l'interface, à la place du compte rendu |
| `resume` | résumé **borné, court** — à la lecture d'un compte rendu entre membres d'équipe, OBSIA-UI le borne (tête + queue, ~600 caractères avec l'enveloppe) ; ce chiffre est un détail d'implémentation d'OBSIA-UI, non normatif ici, et le compte rendu stocké/affiché reste entier |
| `produits` | chemins écrits (dans les zones autorisées, §7.3) |
| `non_verifies` | ce qui n'a pas été vérifié, dit tel quel |

Précisions sur `statut` : pour un tour d'équipe, seuls 4 statuts sont produits — `termine`, `erreur`, `arrete`, `interrompu` (`refusee`/`expiree` sont des états de carte, pas de tour ; `arretee` n'a aucun producteur aujourd'hui). Un cinquième état transitoire, `en_cours`, est publié pendant qu'un tour tourne : hors `STATUTS_FINAUX`, ce n'est pas un statut de compte rendu.

La règle du noyau tient et devient plus importante avec un résumé court :
**le compte rendu ne s'écrit jamais tel quel — l'appelant le vérifie contre la
source.**

## Frontière — ce qui reste côté OBSIA-UI

Le format ne dit rien de tout cela, qui vit côté interface (OBSIA-UI) :
l'ordre des tickets et le parallélisme (nombre de places), qui appelle qui
(l'appelant propose, l'interface valide, le sous-agent rend), le routeur
(étape B côté OBSIA) et la carte de validation côté interface.
