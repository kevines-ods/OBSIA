---
schema: 1
kind: contract
name: contrat-memoire-structure
description: La structure de la mémoire, où écrire selon la nature de l'information, les projets et leurs PR, les chantiers dossiers.
module: noyau
---

# Annexe du contrat — memoire-structure

> **À lire avant l'acte qui la convoque.** Annexe du contrat (`../VAULT-CONTRACT.md`).
> Elle précise, elle n'ajoute aucune règle : toute règle qu'on peut enfreindre
> sans avoir rien chargé est aussi au noyau, et en cas de contradiction le
> noyau fait foi — l'annexe est alors à corriger. Découpée en trois annexes par
> acte (elle fut `contrat-memoire.md`) : les sections ont déménagé,
> sans qu'une phrase ne soit réécrite. La correspondance avec l'ancien
> contrat est suivie dans `registre.md`, document de travail non normatif.

## 6. Nommage, rétroliens et mémoire

- `OBSIA/` est la **racine du dépôt produit** : il n'y a pas de sous-dossier
  intermédiaire dans ce clone. Les chemins du produit (§3, §5) partent de cette
  racine. La **mémoire**, elle, vit **hors** de ce clone — dans le coffre parent,
  versionnée à part (§7.1) — et ses chemins partent de la racine du coffre.
- Le dépôt produit est destiné à être cloné **dans** un coffre Obsidian,
  appelé ici *coffre parent* : c'est là que vivent les notes, et c'est ce coffre
  qui porte le dépôt de données (§7.1). Les rétroliens Obsidian se résolvent à
  l'échelle de ce coffre parent, **pas** de `OBSIA/`.
- Conséquence : les noms de notes doivent être **uniques dans tout le coffre
  parent** (§6), pas seulement dans `OBSIA/`.
- Les liens vers ce contrat s'écrivent en chemin relatif, et la profondeur
  dépend de la forme du skill (§5) :

  ```
  depuis IA/agents/ ou IA/skills/          ../system/VAULT-CONTRACT.md
  depuis IA/skills/<nom>/ (forme dossier)  ../../system/VAULT-CONTRACT.md
  ```

  Passer un skill d'une forme à l'autre casse donc ses liens.
  `scripts/verifier_coffre.py` résout tout chemin relatif cité — entre accents
  graves comme en lien Markdown — depuis le fichier qui le cite, et refuse
  celui qui ne mène nulle part. Les chemins du coffre parent (§7) en sont
  exclus : ils désignent des dossiers hors du dépôt.
- **Structure de la mémoire.** La mémoire se partage sur un seul axe : **ce
  que la note décrit**. Ce qui décrit l'utilisateur, un projet ou un chantier
  est commun à tous les agents ; ce qu'un agent a appris de sa propre manière de
  travailler reste chez lui.

  ```
  0-PROJETS/<projet>/                    un projet du coffre
  ├── <projet> — résumé.md               état vivant, mis à jour sur place
  ├── <projet> — vision.md               finalité — visionnaire seul (§7.3)
  ├── carnets/AAAA-MM-JJ-<projet>-<sujet>.md  carnets du jour, hors chantier
  ├── documents/                         documents du projet entier
  ├── code/                              le dépôt git du projet, hors mémoire (§7.1)
  └── <chantier>/                        un chantier — son dossier à lui
      ├── <chantier> — résumé.md         l'état du chantier, mis à jour sur place
      ├── carnets/AAAA-MM-JJ-<chantier>-<sujet>.md
      ├── documents/                     cadrages, plans, schémas du chantier
      └── code/                          le dépôt git, quand il n'appartient qu'à lui

  0-MEMOIRES/                             une mémoire qui vit, une qui est gelée
  ├── préférences/<sujet>.md             goûts et règles transversaux, corrigés sur place
  ├── courrier/<AAAA-MM-JJ>-<agent>-<sujet>.md  messages traités, à plat, corrigés sur place
  ├── <nom-agent>/expériences/<sujet>.md leçons de l'agent, corrigées sur place
  └── <projet>/
      ├── <chantier>/                    chantier clos, gelé — plus jamais modifié
      │   └── (le résumé devenu bilan, ses carnets `statut: clos`, ses documents)
      └── carnets/                       carnets de séance sans chantier, clos, gelés
          └── AAAA-MM-JJ-<projet>-<sujet>.md

  0-PERSONNELS/
  └── profil-utilisateur.md              faits stables sur l'utilisateur et sa machine
  ```

  `0-MEMOIRES/` porte **une mémoire qui vit et une qui est gelée**. La mémoire
  vivante — `préférences/`, `courrier/` et `<nom-agent>/expériences/` — se
  corrige sur place, comme le profil. Seuls les **chantiers clos** y sont
  gelés : le dossier du chantier n'y entre qu'au moment de la clôture, tel quel,
  et ne se modifie plus ensuite. Un dossier `0-MEMOIRES/` par projet n'existe que
  s'il a des chantiers clos.

  Un nom de premier niveau sous `0-MEMOIRES/` est donc, et rien d'autre :
  `préférences`, `courrier`, le nom d'un agent, ou un projet gelé. **Un projet
  ne peut porter aucun de ces trois premiers noms** : la collision rendrait la
  mémoire vivante indistinguable d'un chantier gelé, et `verifier_coffre.py` la
  refuse. `courrier/` ne contient en outre **que des notes, à plat** — un
  sous-dossier y serait un chantier, donc une collision.

  L'espace d'un agent porte son nom — jamais `agent 1`, `agent 2` — et c'est le
  **même nom** que celui de son fichier `IA/agents/`. Les noms de projet sont
  explicites — jamais `projets 1`, `projets 2` — et disent le chantier, pas qui
  l'a mené : `construction-du-batisseur`, pas `agent-batisseur`, qui se lirait
  comme l'espace mémoire d'un agent — et le serait.

- **Où écrire, selon la nature de l'information** :

  | Ce qu'on a appris | Destination | Commun ? |
  | --- | --- | --- |
  | un fait stable sur l'utilisateur, son poste, son infrastructure | `0-PERSONNELS/profil-utilisateur.md`, **mis à jour sur place** | oui |
  | un goût ou une règle qui vaudra pour d'autres projets | `0-MEMOIRES/préférences/<sujet>.md` | oui |
  | l'état d'un projet | `0-PROJETS/<projet>/<projet> — résumé.md`, **mis à jour sur place** | oui |
  | l'état d'un chantier | `0-PROJETS/<projet>/<chantier>/<chantier> — résumé.md`, **mis à jour sur place** | oui |
  | une demande, un plan, une étape, une action sur un chantier | `0-PROJETS/<projet>/<chantier>/carnets/AAAA-MM-JJ-<chantier>-<sujet>.md` | oui |
  | une séance sans chantier qui laisse un suspens | `0-PROJETS/<projet>/carnets/AAAA-MM-JJ-<projet>-<sujet>.md` | oui |
  | une séance sans chantier bouclée — ses actions | `_MAINTENANCE/journal-des-seances.md`, une ligne par action | oui |
  | une leçon tirée d'un échec ou d'une manœuvre qui a marché | `0-MEMOIRES/<nom-agent>/expériences/<sujet>.md` | non — chez l'agent |
  | un savoir détaché de tout chantier | `0-SAVOIRS/` | oui |

  Les notes de `0-PROJETS/`, `0-PERSONNELS/`, `0-MEMOIRES/préférences/` et
  `0-SAVOIRS/` ne sont **pas datées** : une préférence qui change se corrige,
  elle ne s'empile pas ; `expériences/` non plus. Seuls les carnets et les
  **messages du courrier** portent une date, parce qu'ils racontent une
  chronologie.

  Dans le doute, écrire dans le carnet : un carnet peut être distillé
  plus tard vers `0-MEMOIRES/préférences/` ou `0-MEMOIRES/<agent>/expériences/`,
  l'inverse fait perdre le contexte.

- **Tout projet vit dans `0-PROJETS/`** — celui du coffre comme celui de
  l'utilisateur. Le test qui les sépare est le §7.3.1 : *est-ce que ça décrit le
  produit ?* Si oui, la note va dans `OBSIA/` ; sinon, dans le coffre parent.
  Le dépôt produit se publie (`scripts/publier.py` en dérive un miroir
  public) ; le coffre parent, jamais.

- **Un projet passe par une PR, la demande comprise.** La **demande** — ce qui
  était voulu, ce qui a été fait, ce qui reste — s'écrit dans la description de
  la pull request, avec le résumé de séance. Le carnet, lui, vit dans le dépôt
  de données du coffre (§7.1) : il ne monte plus dans la PR, puisque le dépôt de
  l'outil ne porte pas de mémoire. C'est ce qui fait de la relecture une garde
  sur l'intention, pas seulement sur le diff — par l'utilisateur, le
  `visionnaire` (cap) et le `contradicteur` (relecture) pour un changement qui
  touche la base.

- **Un chantier est un dossier à lui.** Sous son projet :
  `0-PROJETS/<projet>/<chantier>/`, avec ses `carnets/`, ses `documents/` et son
  `<chantier> — résumé.md` — mis à jour sur place, comme le résumé du projet.
  Le `carnets/` du projet ne garde que les carnets du jour, ceux d'une séance
  hors chantier. Un seul niveau : un dossier de chantier n'en contient pas
  d'autre. Le nom du dossier dit le chantier, pas l'agent
  (`souverainete-des-donnees`, pas `batisseur`) : il devient le nom du carnet et
  le dossier de `0-MEMOIRES/` à la clôture.

