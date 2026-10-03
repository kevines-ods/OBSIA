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

- Le coffre est la **racine du dépôt** (`OBSIA/`) : il n'y a pas de sous-dossier
  intermédiaire. Tous les chemins de ce contrat partent de cette racine.
- Le dépôt est destiné à être cloné **dans** un coffre Obsidian préexistant,
  appelé ici *coffre parent* (non versionné). Les rétroliens Obsidian se
  résolvent à l'échelle de ce coffre parent, **pas** de `OBSIA/`.
- Conséquence : les noms de notes doivent être **uniques dans tout le coffre
  parent**, pas seulement dans `OBSIA/`.
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
  que la note décrit**. Ce qui décrit l'utilisateur ou un chantier est commun
  à tous les agents et vit à la racine ; ce qu'un agent a appris en
  travaillant reste chez lui.

  ```
  mémoire/
  ├── profil-utilisateur.md              faits stables sur l'utilisateur et sa machine
  ├── préférences/<sujet>.md             goûts et règles de conduite transversaux
  ├── projets/<projet>/                  un projet du coffre (cf. ci-dessous)
  │   ├── <projet> — résumé.md           état vivant, mis à jour sur place
  │   ├── <projet> — vision.md           finalité — visionnaire seul (§7.3)
  │   ├── carnets/AAAA-MM-JJ-<projet>-<sujet>.md  un carnet par chantier
  │   ├── documents/                     cadrages, schémas, plans hors dépôt de code
  │   ├── <sous-projet>/                 un seul niveau, même structure, sans vision
  │   └── archives/                      carnets clos
  └── <nom-agent>/
      └── expériences/<sujet>.md         leçons réutilisables, tirées d'un cas réel
  ```

  L'espace d'un agent porte son nom — jamais `agent 1`, `agent 2`. Les noms de
  projet sont explicites — jamais `projets 1`, `projets 2` — et disent le
  chantier, pas qui l'a mené : `construction-du-batisseur`, pas
  `agent-batisseur`, qu'on lirait comme l'espace mémoire d'un agent.

- **Où écrire, selon la nature de l'information** :

  | Ce qu'on a appris | Destination | Commun ? |
  | --- | --- | --- |
  | un fait stable sur l'utilisateur, son poste, son infrastructure | `mémoire/profil-utilisateur.md`, **mis à jour sur place** | oui |
  | un goût ou une règle qui vaudra pour d'autres projets | `mémoire/préférences/<sujet>.md` | oui |
  | l'état d'un projet **du coffre** | `mémoire/projets/<projet>/<projet> — résumé.md`, **mis à jour sur place** | oui |
  | une demande, un plan, une étape, une action sur un chantier du coffre | `mémoire/projets/<projet>/carnets/AAAA-MM-JJ-<projet>-<sujet>.md` | oui |
  | une leçon tirée d'un échec ou d'une manœuvre qui a marché | `mémoire/<nom-agent>/expériences/<sujet>.md` | non — chez l'agent |

  Les deux premières ne sont **pas datées** : une préférence qui change se
  corrige, elle ne s'empile pas. `expériences/` ne l'est pas non plus. Seuls
  les carnets portent une date, parce qu'ils racontent une chronologie.

  Dans le doute, écrire dans le carnet : un carnet peut être distillé
  plus tard vers `préférences/` ou `expériences/`, l'inverse fait perdre le
  contexte.

- **`mémoire/projets/` ne porte que les chantiers du coffre.** Le dépôt de
  travail est privé, mais il se publie : `scripts/publier.py` en dérive le
  miroir public en vidant `mémoire/` (§13.5). Un projet de l'utilisateur n'a
  donc rien à faire dans le dépôt ; il vit dans `Mon coffre/-PROJETS/` —
  privé, non versionné. Le partage exact est au §7.3.1.

- **Un projet du coffre passe par une PR, demande comprise.** Sa note
  d'état, sa vision et ses carnets sont versionnés : la **demande**, le plan
  et le récit entrent par la même pull request que la modification, et se
  relisent avec elle — par l'utilisateur, le `visionnaire` (cap) et le
  `contradicteur` (relecture) pour un changement qui touche la base. C'est ce qui fait de la relecture une garde sur
  l'intention, pas seulement sur le diff.

- **Le carnet.** Un carnet par chantier, nommé
  `AAAA-MM-JJ-<projet>-<sujet>.md` — le nom du projet le rend unique dans le
  coffre parent (§7.5) —, frontmatter `agent:`, `projet:` et
  `statut: en cours | en attente | clos`. Il porte la demande, le plan,
  l'**étape en cours écrite avant d'agir**, les actions horodatées — effets
  externes compris (§9) —, les worktrees et branches ouverts, les questions
  en attente. Un carnet écrit après coup ne sert pas à reprendre : entre la
  dernière ligne et la coupure, il y a un trou que rien ne comble. Un
  chantier qui touche plusieurs projets écrit dans le carnet du projet
  `obsia` — sauf ce qui décrit un projet de l'utilisateur, qui va au carnet
  de ce projet dans `-PROJETS/` (§7.3.1).

- **Une séance sans chantier** — dépannage ponctuel, correction sur un
  système, question qui finit en action — écrit dans le **carnet du jour**
  du projet de domaine qui la porte : `obsia` si elle touche le coffre,
  sinon un projet de l'utilisateur tenu pour ce domaine
  (`-PROJETS/<domaine>/`). Elle ne crée pas
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

- **Le carnet se commite à chaque étape**, sur la branche du chantier : un
  worktree se perd (dossier temporaire vidé, `git worktree prune`), un commit
  non. Seul ce qui est commité survit à la coupure.

- **Transition.** Tant que la migration n'est pas faite, des projets gardent
  l'ancienne forme — notes datées à plat dans `mémoire/projets/<projet>/`,
  vision ou résumé à plat dans `-PROJETS/`. Leur absence de `carnets/` ne
  veut pas dire absence d'historique : lire aussi ces notes avant de conclure.

- **Clôture.** Un projet clos garde son `— résumé`, réécrit en bilan avec
  une section « état » (pour pouvoir le rouvrir) ; ses carnets passent
  `statut: clos` et rejoignent son `archives/`. Ce qui est durable remonte
  vers `préférences/` (une règle qui vaut ailleurs) ou vers
  `expériences/` (une manière de travailler de l'agent).

- **Rien de ce qui décrit l'utilisateur ne vit chez un agent.**
  `profil-utilisateur.md` décrit la personne, `préférences/` décrit ses règles :
  ni l'un ni l'autre n'appartient à l'agent qui les a écrits. Les ranger chez
  un agent obligeait les autres à passer par patch pour corriger un fait sur
  leur propre utilisateur — une exception dont la racine dispense. Tout agent
  `read_only: false` les corrige **directement, sur place** (§2).

  Un projet ne vit pas chez un agent non plus, et pour une raison qu'on ne
  voit qu'après coup : un chantier ouvert par un agent et repris par un autre
  aurait vu son histoire coupée en deux dossiers, sans que rien ne le signale.
  Ce qu'un agent apprend sur **sa propre manière de travailler** reste, lui,
  dans son `expériences/` : c'est la seule chose qui lui appartienne vraiment.

- **Un agent `read_only: true` n'a pas d'espace mémoire.** Le §5 lui interdit
  toute écriture, y compris par patch : il n'a donc pas de dossier sous
  `mémoire/`, et rien à y régénérer. Il **lit** en revanche toute la mémoire
  commune — profil, préférences, projets — comme n'importe quel agent. Ses
  constats, eux, vivent le temps de la conversation, et c'est à l'agent qui
  reprend le travail d'en écrire la leçon. La contrepartie est réelle et
  s'assume : un constat non repris est un constat perdu.

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
serveur distant, et le coffre parent n'a pas d'historique Git pour les
rattraper. Ce que la permission gradue, c'est la prudence avant d'appeler —
pas la trace après.
