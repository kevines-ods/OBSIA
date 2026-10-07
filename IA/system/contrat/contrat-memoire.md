---
schema: 1
kind: contract
name: contrat-memoire
description: Détail de la mémoire et des carnets : arborescence, pourquoi chaque règle, transition, liens vers le contrat.
module: noyau
---

# Annexe du contrat — memoire

> **À lire avant de créer, renommer ou déplacer un projet, un carnet ou une note durable, ou de changer la forme d'un skill (le lien vers le contrat change de profondeur).** Annexe du contrat (`../VAULT-CONTRACT.md`).
> Elle précise, elle n'ajoute aucune règle : toute règle qu'on peut enfreindre
> sans avoir rien chargé est aussi au noyau, et en cas de contradiction le
> noyau fait foi — l'annexe est alors à corriger. La correspondance avec l'ancien
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

  0-MEMOIRES/                             deux mémoires : l'une vit, l'autre est gelée
  ├── préférences/<sujet>.md             goûts et règles transversaux, corrigés sur place
  ├── <nom-agent>/expériences/<sujet>.md leçons de l'agent, corrigées sur place
  └── <projet>/<chantier>/               chantier clos, gelé — plus jamais modifié
      └── (le résumé devenu bilan, ses carnets `statut: clos`, ses documents)

  0-PERSONNELS/
  └── profil-utilisateur.md              faits stables sur l'utilisateur et sa machine
  ```

  `0-MEMOIRES/` porte **deux mémoires, et une seule est gelée**. La mémoire des
  agents — `préférences/` et `<nom-agent>/expériences/` — y **vit** : elle se
  corrige sur place, comme le profil. Seuls les **chantiers clos** y sont
  gelés : le dossier du chantier n'y entre qu'au moment de la clôture, tel quel,
  et ne se modifie plus ensuite. Un dossier `0-MEMOIRES/` par projet n'existe que
  s'il a des chantiers clos.

  Un nom de premier niveau sous `0-MEMOIRES/` est donc, et rien d'autre :
  `préférences`, le nom d'un agent, ou un projet gelé. **Un projet ne peut
  porter ni `préférences` ni le nom d'un agent** : la collision rendrait la
  mémoire des agents indistinguable d'un chantier gelé, et `verifier_coffre.py`
  la refuse.

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
  | une séance sans chantier | `0-PROJETS/<projet>/carnets/AAAA-MM-JJ-<projet>-<sujet>.md` | oui |
  | une leçon tirée d'un échec ou d'une manœuvre qui a marché | `0-MEMOIRES/<nom-agent>/expériences/<sujet>.md` | non — chez l'agent |
  | un savoir détaché de tout chantier | `0-SAVOIRS/` | oui |

  Les notes de `0-PROJETS/`, `0-PERSONNELS/`, `0-MEMOIRES/préférences/` et
  `0-SAVOIRS/` ne sont **pas datées** : une préférence qui change se corrige,
  elle ne s'empile pas ; `expériences/` non plus. Seuls les carnets portent une
  date, parce qu'ils racontent une chronologie.

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

- **Le carnet.** Un carnet par chantier, nommé
  `AAAA-MM-JJ-<chantier>-<sujet>.md` : `<chantier>` est le nom du dossier qui
  porte le `carnets/` — le chantier, ou le projet pour une séance sans
  chantier — et c'est ce nom, le même que celui du frontmatter `projet:`, qui
  doit rester unique dans tout le coffre parent (§6, §7.5) : deux chantiers
  homonymes sous deux projets feraient deux carnets homonymes. Frontmatter
  `agent:`, `projet:` et `statut: en cours | en attente | clos`. Il vit dans le
  `carnets/` du **dossier de son chantier** —
  `0-PROJETS/<projet>/<chantier>/carnets/` ; une séance sans chantier écrit dans
  le `carnets/` du projet. Il porte la demande, le plan,
  l'**étape en cours écrite avant d'agir**, les actions horodatées — effets
  externes compris (§9) —, les worktrees et branches ouverts, les questions
  en attente. Un carnet écrit après coup ne sert pas à reprendre : entre la
  dernière ligne et la coupure, il y a un trou que rien ne comble. Un
  chantier qui touche plusieurs projets écrit dans le carnet du projet
  `obsia`.

- **Un chantier est un dossier à lui.** Sous son projet :
  `0-PROJETS/<projet>/<chantier>/`, avec ses `carnets/`, ses `documents/` et son
  `<chantier> — résumé.md` — mis à jour sur place, comme le résumé du projet.
  Le `carnets/` du projet ne garde que les carnets du jour, ceux d'une séance
  hors chantier. Un seul niveau : un dossier de chantier n'en contient pas
  d'autre. Le nom du dossier dit le chantier, pas l'agent
  (`souverainete-des-donnees`, pas `batisseur`) : il devient le nom du carnet et
  le dossier de `0-MEMOIRES/` à la clôture.

- **Une séance sans chantier** — dépannage ponctuel, correction sur un
  système, question qui finit en action — écrit dans le **carnet du jour**
  du projet de domaine qui la porte : `0-PROJETS/obsia/` si elle touche le
  coffre, sinon le projet de domaine tenu pour ce sujet
  (`0-PROJETS/<domaine>/`). Elle ne crée pas
  de chantier pour avoir un carnet. Un agent `read_only: true` n'écrit
  aucun carnet : c'est l'agent qui reprend son travail qui consigne ses
  constats et les appels qu'il a menés.

- **Reprise.** Au démarrage, un agent cherche — dans l'arbre principal **et
  dans chaque worktree lié**, où vit le carnet d'un chantier en cours
  (§2.1) — les carnets `statut: en cours`
  qui portent son nom d'agent — jamais un nom de harness, qui change. Il rapproche ce que le carnet déclare de l'état réel
  — `git status`, `git worktree list`, fichiers cités — avant de proposer de
  reprendre ; s'il en trouve plusieurs, il les liste et l'utilisateur
  choisit. La procédure vit dans `cloture-de-session`.

- **Le carnet se commite à chaque étape**, dans le dépôt de données du coffre
  (§7.1) : un worktree se perd (dossier temporaire vidé, `git worktree prune`),
  un commit non. Seul ce qui est commité survit à la coupure.

- **Transition.** Tant que la bascule dure — chantier `souverainete-des-donnees`,
  au plus tard le 2026-12-31 (§11) — les carnets, les projets et les notes
  personnelles se cherchent à **tout emplacement qui existe**, dans cet ordre :
  `0-PROJETS/`, l'ancien nom du coffre `-PROJETS/`, puis l'ancien
  `mémoire/projets/` du dépôt ; le profil sous `0-PERSONNELS/`, `-PERSONNELS/`,
  puis `mémoire/` ; les préférences et les expériences sous `0-MEMOIRES/`
  (`préférences/`, `<nom-agent>/expériences/`), puis `0-PERSONNELS/`,
  `-PERSONNELS/`, puis `mémoire/`. Des projets
  gardent l'ancienne forme — notes datées à plat dans le dossier du projet,
  vision ou résumé à plat à côté. Leur absence de `carnets/` ne veut pas dire
  absence d'historique : lire aussi ces notes avant de conclure.

  `IA/system/session-log/` — des notes de séance, donc de la **mémoire** — suit
  `mémoire/` : il quitte le dépôt à la bascule, pour
  `0-MEMOIRES/obsia/session-log/`, gelé. Passé le jour dit, ni lui ni `mémoire/`
  ne doivent rester dans le dépôt (§11, `verifier_coffre.py`).

- **Clôture.** À la clôture d'un chantier, son **dossier entier** quitte
  `0-PROJETS/<projet>/<chantier>/` pour `0-MEMOIRES/<projet>/<chantier>/`, tel
  quel : le `— résumé` devient un bilan avec une section « État » (pour pouvoir
  le rouvrir), les carnets passent `statut: clos`, les documents suivent. Ce qui
  est durable a été distillé **avant** vers `0-MEMOIRES/préférences/` (une
  règle qui vaut ailleurs) ou `0-MEMOIRES/<agent>/expériences/` (une manière
  de travailler de l'agent). Le dossier gelé ne se modifie plus.

  **Rouvrir** un chantier clos le ramène dans `0-PROJETS/`, `statut: en cours`,
  **sans copie laissée** dans `0-MEMOIRES/`.

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

## Pourquoi — repris des sections restées au noyau

### §1 — d'où vient la règle des agents nommés

Le coffre n'a longtemps porté qu'un agent, et cette règle s'écrivait « un seul
agent peut être nommé ». La formulation confondait l'interdiction — les agents
fantômes — avec un plafond qui n'a jamais été l'intention.

Les tournures `agent 1`, `agent 2` restent employées ailleurs dans ce contrat :
ce ne sont pas des noms d'agents mais des **contre-exemples de nommage de
dossier**, et elles ne désignent personne.

### §9 — pourquoi l'horodatage, pourquoi `normal` ne dispense pas

L'horodatage
n'est pas décoratif : une séance qui touche plusieurs chantiers écrit dans
plusieurs carnets, et c'est lui qui rend l'ordre réel des actions
reconstituable.

`permission: normal` dit qu'un outil ne sort pas de la machine ; il ne
dispense pas d'en consigner l'usage. Un serveur « local » qui crée et
modifie des notes du coffre parent produit des effets aussi durables qu'un
serveur distant. Le dépôt de données rattrape désormais ce qui est commité
(§7.1), mais pas ce qu'aucune étape n'a pris le temps d'écrire. Ce que la
permission gradue, c'est la prudence avant d'appeler —
pas la trace après.
