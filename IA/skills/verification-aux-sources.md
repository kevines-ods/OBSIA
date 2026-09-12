---
schema: 1
kind: skill
name: verification-aux-sources
description: Vérifier dans la documentation officielle toute décision propre à un cadriciel ou une bibliothèque, version lue dans le fichier de dépendances, et citer la source dans la réponse. À charger avant d'écrire du code propre à une bibliothèque, et devant tout motif qu'on s'apprête à reproduire ailleurs. Dit ce qui fait autorité et ce qui n'en fait pas ; `recherche` dit où chercher.
type: outil
read_only: false
---

# Skill — Vérification aux sources

> **Adaptation.** Reprend `source-driven-development` de
> `addyosmani/agent-skills` (MIT), condensé, traduit, et raccordé au skill
> `recherche` plutôt qu'à un moteur nommé.

Les données d'entraînement vieillissent. Une API se déprécie, une bonne
pratique change, une option disparaît — et le code produit de mémoire reste
**plausible**. C'est ce qui le rend dangereux : il compile, il se lit bien, et
il est faux.

Ce skill existe pour le mode d'échec qu'un utilisateur qui code peu ne peut
pas attraper seul.

## Le partage avec `recherche`

`recherche` dit **où** chercher — la cascade coffre, sites de confiance, web.
Ce skill dit **ce qui fait autorité** pour une question de code, et **ce qu'on
écrit dans la réponse**. Les deux se chargent ensemble ; ils ne se remplacent
pas.

## La procédure

```
RELEVER ──→ VÉRIFIER ──→ ÉCRIRE ──→ CITER
la pile     la page      selon ce    montrer la
et ses      exacte de    qui est     source, avec
versions    la doc       documenté   sa version
```

### 1. Relever la pile et ses versions

Dans le fichier de dépendances du projet, jamais de mémoire :

| Fichier | Ce qu'il donne |
| --- | --- |
| `package.json`, et le verrou à côté | Node et l'écosystème JavaScript |
| `pyproject.toml`, `requirements.txt` | Python |
| `go.mod`, `Cargo.toml`, `composer.json`, `Gemfile` | Go, Rust, PHP, Ruby |

Le **verrou** (`package-lock.json`, `uv.lock`, `Cargo.lock`) donne la version
réellement installée ; le fichier de déclaration ne donne qu'une fourchette.
C'est le verrou qui fait foi.

Annoncer ce qu'on a trouvé, explicitement, avant de chercher. Si la version
est absente ou ambiguë, **demander** : c'est elle qui décide quel motif est
correct.

### 2. Vérifier sur la page exacte

Pas la page d'accueil, pas la documentation entière : la page de la
fonctionnalité qu'on implémente, pour la version relevée.

**Hiérarchie d'autorité**, dans cet ordre :

| | Source | Pourquoi elle fait autorité |
| --- | --- | --- |
| 1 | documentation officielle du projet | c'est l'auteur du code qui l'écrit |
| 2 | journal des versions, billet officiel | dit ce qui a changé, et quand |
| 3 | référence de standard — MDN, spécification | pour ce qui n'appartient à aucun cadriciel |
| 4 | tableau de compatibilité | pour savoir si c'est utilisable chez la cible |
| 5 | **le code source du projet**, à la version installée | quand la documentation est muette ou en retard |

**Ne font pas autorité**, et ne se citent jamais comme source première : une
réponse de forum, un billet de blog même très lu, un tutoriel, une
documentation résumée par une IA — y compris par celle qui écrit.

Le cinquième rang mérite d'être connu : sur un projet libre, lire la fonction
appelée dans le dépôt à la version installée est souvent **plus fiable** que
sa documentation, qui décrit parfois la version suivante.

### 3. Écrire selon ce qui est documenté

Si la documentation contredit ce qu'on allait écrire, c'est la documentation
qui gagne. Si elle propose plusieurs voies, choisir celle qu'elle recommande —
et dire laquelle, avec la raison.

### 4. Citer

Dans la réponse, pas dans un commentaire du code :

```
Vérifié : <bibliothèque> <version exacte>
Source  : <URL de la page consultée>
Ce qu'elle dit : <une phrase>
```

Le §8 du contrat impose déjà de séparer **évidence**, **interprétation** et
**synthèse produite par un agent**. Une citation est une évidence ; « ça
devrait marcher comme ça » est une synthèse. Les confondre est l'erreur que ce
skill prévient.

## Quand ne pas charger ce skill

- La justesse ne dépend d'aucune version : une boucle, un renommage, un
  déplacement de fichier.
- La logique est la sienne, pas celle d'une bibliothèque.
- L'utilisateur a demandé de la vitesse en connaissance de cause.

Vérifier chaque ligne ne livre rien. Ce skill vise ce qui est **propre à une
bibliothèque**.

## Quand la vérification échoue

Trois cas, trois conduites — et aucune n'est « écrire quand même » :

| Situation | Conduite |
| --- | --- |
| la page n'existe pas pour cette version | le dire, et lire le code source à la version installée (rang 5) |
| la documentation est ambiguë | énoncer les deux lectures et demander, plutôt que de parier |
| aucun accès réseau | le dire, écrire en signalant **explicitement** que le motif n'est pas vérifié, et le marquer à reprendre |

Du code non vérifié annoncé comme tel est utilisable. Du code non vérifié
présenté comme vérifié est un piège posé pour plus tard.

## Rationalisations

| Ce qu'on se dit | La réalité |
| --- | --- |
| « je connais bien cette bibliothèque » | on connaît la version sur laquelle on s'est entraîné. Le projet en utilise une autre |
| « c'est le motif standard » | il l'était. Les bonnes pratiques changent plus vite que les données d'entraînement |
| « la doc dit sûrement la même chose » | alors la lire coûte trente secondes, et on n'a plus à dire « sûrement » |
| « ce billet de blog l'explique mieux » | mieux, peut-être. À jour, rien ne le garantit |
| « on verra si ça casse » | ça cassera chez l'utilisateur, et la cause sera invisible dans le code |

## Contraintes

Atteindre la documentation demande un accès réseau, qui **se demande
explicitement** (§4). Le MCP employé pour chercher se consigne dans le log de
session, comme tout appel de MCP (§9).

> Les autres règles sont au §4 et au §8 de `../system/VAULT-CONTRACT.md`.
