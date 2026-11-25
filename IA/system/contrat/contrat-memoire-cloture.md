---
schema: 1
kind: contract
name: contrat-memoire-cloture
description: La clôture et le gel d'un chantier, le profil et les préférences communes, les expériences d'un agent read_only ; la forme d'une note durable et ses sources (§8).
module: noyau
---

# Annexe du contrat — memoire-cloture

> **À lire avant l'acte qui la convoque.** Annexe du contrat (`../VAULT-CONTRACT.md`).
> Elle précise, elle n'ajoute aucune règle : toute règle qu'on peut enfreindre
> sans avoir rien chargé est aussi au noyau, et en cas de contradiction le
> noyau fait foi — l'annexe est alors à corriger. Découpée en trois annexes par
> acte (elle fut `contrat-memoire.md`) : les sections ont déménagé,
> sans qu'une phrase ne soit réécrite. La correspondance avec l'ancien
> contrat est suivie dans `registre.md`, document de travail non normatif.

- **Clôture.** À la clôture d'un chantier, son **dossier entier** quitte
  `0-PROJETS/<projet>/<chantier>/` pour `0-MEMOIRES/<projet>/<chantier>/`, tel
  quel : le `— résumé` devient un bilan avec une section « État » (pour pouvoir
  le rouvrir), les carnets passent `statut: clos`, les documents suivent. Ce qui
  est durable a été distillé **avant** vers `0-SAVOIRS/` (un savoir détaché du
  chantier), `0-MEMOIRES/préférences/` (une
  règle qui vaut ailleurs) ou `0-MEMOIRES/<agent>/expériences/` (une manière
  de travailler de l'agent). Le dossier gelé ne se modifie plus.

  **Rouvrir** un chantier clos le ramène dans `0-PROJETS/`, `statut: en cours`,
  **sans copie laissée** dans `0-MEMOIRES/`.

  Un **carnet de séance sans chantier** clos suit la même logique en plus
  léger : pas de dossier, pas de bilan à coiffer — c'est déjà un fichier seul.
  Son déplacement vers `0-MEMOIRES/<projet>/carnets/` se fait au même instant
  que son passage `statut: clos`, pas en différé.

  **Un domaine dormant n'est pas clos** : sans chantier actif, son dossier reste
  dans `0-PROJETS/` et **sa vision reste** — on n'archive pas un domaine vivant.

- **Rien de ce qui décrit l'utilisateur ne vit chez un agent.**
  `0-PERSONNELS/profil-utilisateur.md` décrit la personne,
  `0-MEMOIRES/préférences/` décrit ses règles : ni l'un ni l'autre n'appartient à
  l'agent qui les a écrits — `préférences/` est un dossier **commun** de
  `0-MEMOIRES/`, jamais un dossier d'agent. Les ranger chez
  un agent obligeait les autres à passer par patch pour corriger un fait sur
  leur propre utilisateur — une exception dont la racine dispense. Tout agent
  `read_only: false` les corrige **directement, sur place** (§2), sans preview
  (§7.4).

  Un projet ne vit pas chez un agent non plus, et pour une raison qu'on ne
  voit qu'après coup : un chantier ouvert par un agent et repris par un autre
  aurait vu son histoire coupée en deux dossiers, sans que rien ne le signale.
  Ce qu'un agent apprend sur **sa propre manière de travailler** reste, lui,
  dans son `0-MEMOIRES/<nom-agent>/expériences/` : c'est la seule chose qui
  lui appartienne vraiment.

- **Un agent `read_only: true` n'a pas d'espace mémoire.** Le §5 lui interdit
  toute écriture, y compris par patch : il n'a donc pas de dossier sous
  `0-MEMOIRES/<nom-agent>/`, et rien à y régénérer. Il **lit** en revanche
  toute la mémoire commune — profil, préférences, projets — comme n'importe quel
  agent. Ses constats, eux, vivent le temps de la conversation, et c'est à
  l'agent qui reprend le travail d'en écrire la leçon. La contrepartie est
  réelle et s'assume : un constat non repris est un constat perdu.

- Une note durable n'est utile que si elle est **retrouvée** : son nom dit son
  sujet (`licences-et-logiciel-libre.md`, pas `notes.md`) et respecte la règle
  d'unicité ci-dessus.

## 8. Sources et citations

Une note durable distingue **évidence** (avec son URL source),
**interprétation** et **synthèse produite par un agent**. Les URLs sont
regroupées en fin de fichier.

