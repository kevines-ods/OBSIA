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

Emplacement attendu : `IA/system/VAULT-CONTRACT.md`, depuis la racine du dépôt.

---

## 1. Vocabulaire (à ne pas confondre)

| Terme | Nature | Emplacement | Rôle |
| --- | --- | --- | --- |
| **agent** | un interlocuteur | `IA/agents/` | possède un system prompt, mène une conversation, décide |
| **skill** | une compétence | `IA/skills/` | décrit *comment* faire une chose, ne décide pas |
| **MCP** | un outil | `IA/MCP/` | expose des actions structurées |
| **tâche** | une action planifiée | `IA/tâches/` | dit quoi déclencher, quand, pour quel agent ; ne décide pas |

Un agent **utilise** des skills. Un skill n'est jamais un agent. Une tâche
n'est ni l'un ni l'autre : elle *déclenche* un agent, qui charge ensuite les
skills dont il a besoin.

Piège historique à ne pas reproduire : **`obsidian-manager` est un SKILL** ; il a
longtemps été pris pour un agent qui n'a jamais existé en tant que fichier.
Toute formulation suggérant qu'un skill est un agent est une erreur à corriger,
pas une convention à suivre.

**Un agent n'est nommé que s'il a son fichier dans `IA/agents/`.** Lesquels
existent, c'est `agents-index.md` qui le dit — pas ce contrat, qui vieillirait
à chaque agent ajouté. Aucun autre nom n'apparaît nulle part : ni dans un
skill, ni dans un exemple, ni dans un diagramme, ni dans une note. Nommer un
agent avant qu'il existe le fait exister dans les têtes, et c'est ainsi qu'un
agent fantôme s'installe. La règle vaut aussi pour les noms cités en exemple :
prendre un nom de skill, jamais un nom d'agent imaginaire.
`scripts/verifier_coffre.py` la contrôle.

Le coffre n'a longtemps porté qu'un agent, et cette règle s'écrivait « un seul
agent peut être nommé ». La formulation confondait l'interdiction — les agents
fantômes — avec un plafond qui n'a jamais été l'intention.

Les tournures `agent 1`, `agent 2` restent employées ailleurs dans ce contrat :
ce ne sont pas des noms d'agents mais des **contre-exemples de nommage de
dossier**, et elles ne désignent personne.

---

## 2. Écriture dans le coffre

- Le coffre est en **lecture seule pour les agents** dont `read_only: true`.
- Un agent `read_only: false` peut écrire **directement, sans patch**, dans
  trois zones seulement :
  - `brouillon/` — sans restriction ;
  - `mémoire/`, **sauf le dossier d'un autre agent** : la mémoire partagée
    (`profil-utilisateur.md`, `préférences/`, `projets/`) est ouverte à tous
    les agents ; `mémoire/<nom-agent>/` n'appartient qu'à l'agent qui le
    porte. Le détail de qui écrit quoi et où vit au §6 ;
  - `IA/skills/` — uniquement s'il déclare le skill `createur-de-skill` dans
    son frontmatter.
- Tout le reste du coffre (`IA/agents/`, `IA/system/`, `IA/tâches/`, la
  structure du dépôt) reste protégé : toute modification durable y passe par un
  **patch Git** soumis à revue humaine. Les interventions hors du coffre
  relèvent du §3.
- Aucune suppression sans archivage préalable dans `.archive/`, y compris dans
  une zone en écriture directe. Ce dossier est **versionné** : ignoré par Git,
  il ne survivrait pas à un clone neuf et la règle ne promettrait rien. Rien
  n'y est lu ni indexé — les dossiers commençant par un point sont écartés
  partout.
- Toute action touchant plusieurs fichiers exige un **preview** affiché avant
  exécution, listant les chemins concernés — que l'écriture soit directe ou
  passe par patch.
- Les **fichiers générés** ne sont jamais édités à la main ni par un agent,
  même dans une zone en écriture directe : `sommaire.md`, `agents-index.md`,
  `skills-index.md`, `taches-index.md` et `IA/README.md` sont régénérés par les
  scripts du §11,
  qui donne la liste complète et la commande.
- Ces trois zones sont les seules **du dépôt**. Hors du dépôt, les écritures
  dans le coffre parent suivent le §7 : zones d'écriture (7.3), preview et
  registre consignés dans `_maintenance/` (7.4).

## 3. Périmètre hors du coffre

Ce coffre ne dépend d'aucun harness et n'en connaît aucun : il décrit *quoi*
faire, le harness fournit *avec quoi*. Aucune base de code extérieure n'est
nommée ici, et aucun agent n'en a le monopole.

Quand un agent dont le frontmatter porte `read_only: false` intervient sur un
dépôt extérieur (interface, outillage, infrastructure), les règles suivantes
s'appliquent — elles ne dépendent ni du langage ni du projet :

- Toute modification passe par un **patch Git revu** — jamais de commit direct
  sur la branche par défaut.
- Les vérifications du projet visé (compilation, analyse statique, tests)
  passent **avant** de proposer le patch.
- **Jamais de secret** (clé API, jeton) dans le code : variables
  d'environnement ou configuration hors dépôt uniquement.
- Ajouter une fonctionnalité = d'abord un **skill** documenté dans
  `IA/skills/`, puis l'implémentation.

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
| `kind` | `agent` \| `skill` \| `mcp` \| `tâche` \| `contract` | oui | permet de valider le type sans se fier au dossier |
| `name` | texte | oui | minuscules, tirets, **sans espaces**. Identique au nom du fichier. |
| `description` | texte | oui | une ligne. Réutilisée par le générateur de sommaires. |
| `read_only` | booléen | oui | cf. sémantique ci-dessous |

**Sémantique de `read_only`**

| Valeur | Signification |
| --- | --- |
| `true` | **Lecture seule absolue** : aucune écriture nulle part (ni coffre, ni hors coffre, même via patch). |
| `false` | **Écriture directe** dans `brouillon/`, `mémoire/` sauf le dossier d'un autre agent, et `IA/skills/` si `createur-de-skill` est déclaré (détail au §2), ainsi que dans les zones du coffre parent que le §7 ouvre (7.3) ; écriture hors coffre autorisée (§3) ; le reste du coffre passe par patch Git revu. |

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
  ├── projets/<nom-projet>/AAAA-MM-JJ-titre.md   avancement daté d'un chantier
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
  | une décision ou un avancement sur un chantier **du coffre** | `mémoire/projets/<nom-projet>/AAAA-MM-JJ-titre.md` | oui |
  | une leçon tirée d'un échec ou d'une manœuvre qui a marché | `mémoire/<nom-agent>/expériences/<sujet>.md` | non — chez l'agent |

  Les deux premières ne sont **pas datées** : une préférence qui change se
  corrige, elle ne s'empile pas. `expériences/` ne l'est pas non plus. Seules
  les notes de projet portent une date, parce qu'elles racontent une
  chronologie.

  Dans le doute, écrire dans le projet : une note de projet peut être distillée
  plus tard vers `préférences/` ou `expériences/`, l'inverse fait perdre le
  contexte.

- **`mémoire/projets/` ne porte que les chantiers du coffre.** Le dépôt est
  public (§4) : un projet de l'utilisateur n'y a pas sa place, et sa note de
  suivi vit dans `Mon coffre/-PROJETS/` — privé, non versionné. Le partage
  exact est au §7.3.1.

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

## 7. Le coffre parent — la base de connaissances

Le dépôt OBSIA est cloné **à la racine du coffre parent**, côte à côte avec
les dossiers de connaissance. Ce coffre parent est la base de connaissances
primordiale : il se lit, s'enrichit et s'administre — par l'utilisateur, et
par les agents qui y accèdent selon ce paragraphe. Seul `OBSIA/` est
versionné ; les autres dossiers ne le sont pas.

**Le coffre parent s'appelle `Mon coffre/`.** C'est son nom, et c'est ainsi
qu'on le désigne partout dans la documentation :

| Ce qu'on veut dire | Comment l'écrire |
| --- | --- |
| un dossier du coffre parent | `Mon coffre/-SAVOIRS/` — jamais `../-SAVOIRS/` |
| le dépôt lui-même | `Mon coffre/OBSIA/`, ou son chemin interne (`IA/skills/…`) |
| un fichier du dépôt, depuis un autre fichier du dépôt | relatif : `../system/VAULT-CONTRACT.md` |

La règle tient en une phrase : **`../` ne sert qu'à naviguer à l'intérieur du
dépôt**, jamais à désigner le coffre parent. Sans elle, le même `../` veut dire
deux choses selon la cible — relatif au fichier ici, relatif au répertoire de
travail là — et c'est ainsi qu'un skill finit par pointer à côté.

Une **commande** reste une exception assumée : lancée depuis la racine du
dépôt, elle atteint le coffre parent par `..` (`rg "motif" ../-SAVOIRS`). C'est
du shell, pas une désignation. Un chemin absolu, lui, contient une espace et
se cite : `"$HOME/Mon coffre/-SAVOIRS"`.

**Le tiret initial est un piège d'exécution, pas une coquetterie.** Les
dossiers du coffre parent commencent par `-`, et un argument qui commence par
`-` est lu comme une **option** par la quasi-totalité des commandes Unix :
`rg "motif" -SAVOIRS` échoue, `ls -PROJETS` aussi. D'où trois formes à
respecter, sans exception :

| Cas | Ce qui casse | Ce qui marche |
| --- | --- | --- |
| commande depuis la racine du dépôt | `rg "x" -SAVOIRS` | `rg "x" ../-SAVOIRS` |
| chemin absolu | — | `"$HOME/Mon coffre/-SAVOIRS"` |
| valeur d'option | `--dossier -SAVOIRS` | `--dossier=-SAVOIRS` |

Le préfixe `../` ou `./` suffit à désamorcer le tiret, parce que l'argument ne
commence alors plus par lui. Un chemin nu ne s'écrit jamais dans une commande.

### 7.1 La structure — fixe

La structure de premier niveau est **fixe**. Seul l'utilisateur crée, renomme
ou supprime un dossier de premier niveau. Les agents ne modifient jamais cette
structure : ils travaillent dans les dossiers existants, sans y créer de
sous-structure de premier niveau.

| Dossier | Rôle |
| --- | --- |
| `Mon coffre/` | la racine — le coffre Obsidian lui-même, ouvert à ce niveau |
| `OBSIA/` | le dépôt, versionné — agents, skills, tâches, mémoire d'OBSIA |
| `_maintenance/` | journaux, astuces de débogage, previews consignés, registre des notes traitées |
| `-PROJETS/` | les projets en cours ou à venir — notes, et le dépôt git du projet quand il en a un (7.3) |
| `-DOCUMENTS/` | revues, articles web, transcriptions YouTube |
| `-PERSONNELS/` | contexte personnel : configuration matérielle/logicielle, préférences, CV… |
| `-SAVOIRS/` | les connaissances accumulées — un fichier Markdown = un concept |
| `-EN-VRAC/` | zone de dépôt : notes brutes, parfois un simple titre à traiter |

Déplacer un dossier de premier niveau (ex. `OBSIA/` dans `-PROJETS/`) est une
décision de l'utilisateur, pas des agents.

### 7.2 Lecture

Les agents `read_only: false` peuvent **lire tout le coffre parent** dès que
le harness donne accès à sa racine (7.6) : la recherche couvre
`_maintenance/`, `-PROJETS/`, `-DOCUMENTS/`, `-PERSONNELS/`, `-SAVOIRS/` et
`-EN-VRAC/`. Ces dossiers se désignent par leur nom complet depuis la racine
(`Mon coffre/-SAVOIRS/`) ; dans une commande lancée depuis la racine du dépôt,
ils s'atteignent par `..`.

Le coffre parent n'est **pas** un « dépôt extérieur » au sens du §3 : ce
paragraphe vise des bases de code, pas des notes.

Lire n'est pas recopier : le coffre parent est privé, le dépôt est public
(§4). Rien du coffre parent ne migre dans `OBSIA/` au fil des réponses, et
aucun secret du coffre parent n'entre dans le dépôt.

### 7.3 Écriture — zones autorisées

Le coffre parent n'étant pas versionné, il n'y a **pas de patch Git**
possible. Les écritures autorisées d'un agent `read_only: false` y sont
directes, limitées et tracées (7.4) :

- `-EN-VRAC/` — remplir une note, poser tags et rétroliens, préparer le
  classement ;
- `-SAVOIRS/` — compléter une note que l'utilisateur y a déposée (tags,
  rétroliens, corps manquant), sans en changer le sens ni la déplacer ;
- `_maintenance/` — consigner previews, actions et registre des notes
  traitées ;
- le **classement** : déplacer une note d'`-EN-VRAC/` vers sa destination
  (`-PROJETS/`, `-DOCUMENTS/`, `-PERSONNELS/`, `-SAVOIRS/`) une fois traitée ;
- `-PROJETS/<nom-du-projet> — résumé.md` — **la note de suivi d'un projet**,
  créée et tenue par l'agent, **mise à jour sur place** : où en est le projet,
  ce qui a été décidé, ce qui reste à faire. Une note vivante par projet, pas
  une pile de notes datées — un état qui change se corrige, comme au §6. Elle
  vit **à côté** du dépôt, jamais dedans : le dossier du dépôt est exclu de
  l'index d'Obsidian, une note posée à l'intérieur serait invisible à la
  recherche et aux rétroliens ;
- `-PROJETS/<nom-du-projet>/` — **le dépôt git d'un projet construit ici** :
  l'agent y crée le dossier, y écrit le code et ses documents, y commite.
  C'est un dépôt à part entière, versionné pour lui-même, et la seule zone du
  coffre parent où du code vit. Le §3 s'y applique intégralement : patch revu,
  vérifications du projet passées avant de proposer, aucun secret dans le
  dépôt. Ce dossier est **exclu de l'index d'Obsidian** — sans quoi le
  Markdown du dépôt et de ses dépendances entre dans la recherche du coffre et
  fait tomber l'unicité des noms de notes (§6) dès le deuxième projet.

Une **note** de `-PROJETS/` n'est pas un dépôt de projet : elle reste protégée
comme le reste. Hors des dépôts de projet et de la note de suivi ci-dessus,
une écriture dans `-PROJETS/`, `-DOCUMENTS/` ou `-PERSONNELS/` se limite au
**dépôt d'une note classée venue d'`-EN-VRAC/`**, et à rien d'autre. On n'y
modifie **jamais** une note existante, même à la demande de l'utilisateur :
une note à enrichir repasse d'abord par `-EN-VRAC/`, puis est classée. On n'y
déplace ni n'y supprime rien.

La note de suivi est l'unique exception, et elle tient à une raison précise :
**c'est la seule note de `-PROJETS/` dont l'agent est l'auteur.** Il l'a
créée, il la met à jour, personne d'autre n'écrit dedans. La règle générale
protège les notes de l'utilisateur d'une réécriture silencieuse sans Git pour
la rattraper ; elle ne protège de rien quand l'agent corrige son propre texte.
Le suffixe ` — résumé` est ce qui rend la distinction visible sans l'ouvrir :
une note qui ne le porte pas n'est pas à l'agent.

### 7.3.1 Où va la note d'un projet — le dépôt est public

Deux endroits portent des notes de projet, et les confondre expose du privé :

| Le projet porte sur… | La note va dans… | Visibilité |
| --- | --- | --- |
| le coffre lui-même — un skill, un agent, une règle | `mémoire/projets/<nom-projet>/AAAA-MM-JJ-titre.md` | **publique** — le dépôt est public (§4) |
| n'importe quoi d'autre — un projet de l'utilisateur | `-PROJETS/<nom-du-projet> — résumé.md` | privée — le coffre parent n'est pas versionné |

`mémoire/` vit dans le dépôt, et le dépôt est public : **rien de privé n'y
entre**, un projet personnel pas davantage qu'un secret (§7.2). Un chantier
sur le coffre y a sa place parce qu'il *est* le dépôt ; un projet de
l'utilisateur, non.

Le test, avant d'écrire : *est-ce que ça décrit le coffre ?* Si non, ça va dans
`-PROJETS/`. Dans le doute, `-PROJETS/` : un contenu privé qui atterrit dans
un dépôt public ne se rattrape pas — l'historique Git le garde même effacé.

`-PERSONNELS/` porte du contenu **personnel mais non critique** : configuration
matérielle, préférences, CV. Il **participe au graphe de liens** comme les
autres dossiers — ces notes doivent être reliées au reste, sinon elles ne
servent à rien. Un agent le lit donc librement pour établir des rétroliens et
pour répondre.

Deux limites tiennent quand même : on n'y **écrit** que pour y classer une note
dont la nature est manifestement personnelle (§7.3 ci-dessus), et son contenu
ne migre jamais dans `OBSIA/`, qui est public (§7.2). Un secret — mot de passe,
jeton, clé — n'a sa place ni ici ni ailleurs (§4).

### 7.4 Preview et traçabilité — `_maintenance/`

Sans Git, **le preview tient lieu de trace**. Avant toute action qui touche
plusieurs fichiers, déplace une note ou écrit hors d'`-EN-VRAC/`, l'agent :

1. affiche le preview — fichiers concernés, contenu final, destination ;
2. en **conserve une copie datée dans `_maintenance/`** ;
3. exécute, puis consigne l'action (quoi, où, résultat) dans `_maintenance/`,
   comme au §9.

Le registre des notes traitées est le fichier
**`Mon coffre/_maintenance/notes_remplies.md`** — une note Markdown, pour
qu'Obsidian l'indexe et la rende consultable comme le reste. Il liste les
notes déjà remplies, surtout celles de `-SAVOIRS/` que l'utilisateur dépose
brutes. Une note qui y figure n'est pas à revérifier ; le registre est mis à
jour après chaque traitement.

### 7.5 Rétroliens et tags — ce qui ne se viole pas

Un rétrolien Obsidian est **du texte** : `[[Nom de la note]]`, qu'Obsidian
résout à la lecture. Aucune API ni aucun greffon n'est requis. Le **comment**
— format du lien, frontmatter d'une note, procédure de traitement — vit dans le
skill `traitement-des-notes`
(`IA/skills/traitement-des-notes/traitement-des-notes.md`). Trois règles
restent ici, parce qu'on peut les violer sans avoir chargé quoi que ce soit :

- **Les tags suivent un vocabulaire contrôlé.** Le registre
  `IA/system/tags-du-coffre-parent.md` fait foi ; on ne pose **jamais** un tag
  hors liste, et un tag nouveau se propose par patch sur ce registre. Des tags
  générés librement par une IA, sans cohérence, surchargent les recherches.
- **Un lien ne relie que si sa cible existe.** `[[Nom]]` vers une note absente
  n'affiche qu'une « note non créée » et ne relie rien.
- **Les noms de notes sont uniques dans tout le coffre parent** (§6) : avant de
  créer une note ou un lien, vérifier qu'aucun nom identique n'existe ailleurs.

Ces liens se résolvent à l'échelle du coffre parent, jamais de `OBSIA/` seul,
ce qui suppose le coffre ouvert dans Obsidian **à sa racine** — c'est au
harness d'y répondre (7.6).

### 7.6 Accès du harness

Le coffre ne nomme aucun harness (§3) : la manière de donner accès au coffre
parent appartient à la configuration de chaque harness, **hors dépôt**. Le
besoin est unique, et c'est la seule part qui relève de ce contrat — le harness
doit pouvoir **lire et écrire dans la racine du coffre parent** (le dossier qui
contient `OBSIA/`), pas seulement dans `OBSIA/`.

Les voies possibles, le serveur MCP « fichiers » et les gabarits par harness
vivent dans `IA/system/adaptateurs-harness/README.md`. Une limite ne s'y dilue
pas pour autant : un serveur de fichiers braqué sur la racine du coffre peut
écrire **partout**, alors que le §7.3 n'en ouvre qu'une poignée. C'est la fiche
`IA/MCP/coffre-parent.md` qui porte cette limite, pas le serveur — d'où
l'obligation de la lire avant d'appeler un de ses outils (§10.2).

### 7.7 Cycle d'une note d'`-EN-VRAC/`

`-EN-VRAC/` est un **dossier tampon**, pas une destination : il ne stocke rien
durablement. Une session de rangement le traite **en entier**, et il est vide
quand elle se termine : c'est le critère d'achèvement, et ce qui y reste est ce
qui n'a pas pu être tranché — le dire. Conséquence pratique : une note
d'`-EN-VRAC/` n'est jamais une cible de rétrolien stable, puisqu'elle aura
changé de dossier avant qu'on la relise.

La procédure — lire, vérifier qu'un doublon n'existe pas, remplir, tagger,
prévisualiser, classer, consigner au registre — vit dans le skill
`traitement-des-notes`
(`IA/skills/traitement-des-notes/traitement-des-notes.md`). Elle n'est pas
reprise ici : ce qui s'écrit à deux endroits diverge, et c'est la destination
qui décide — une **règle** violable sans avoir rien chargé reste dans ce
contrat, une **procédure** qui ne s'applique qu'en faisant la chose part dans
le skill.

## 8. Sources et citations

Une note durable distingue explicitement trois natures d'information :
**évidence** (avec son URL source), **interprétation** et **synthèse produite
par un agent**. Les URLs sont regroupées en fin de fichier.

## 9. Log des sessions

À la fin de chaque session de travail, une note est **proposée en patch** dans
`IA/system/session-log/AAAA-MM-JJ.md` : décisions prises, fichiers modifiés,
questions restées ouvertes. Ce dossier vit sous `IA/system/`, donc son
écriture suit la règle générale du §2 (patch Git revu) — ce n'est pas une des
trois zones en écriture directe.

**Les actions à effet externe y figurent aussi** : **tout appel de MCP, quel
que soit son `permission`**, et toute correction appliquée à un système. Une
ligne suffit — quoi, où, résultat.

`permission: normal` dit qu'un outil ne sort pas de la machine ; il ne dispense
pas d'en consigner l'usage. Un serveur « local » qui crée et modifie des notes
du coffre parent produit des effets aussi durables qu'un serveur distant, et
le coffre parent n'a pas d'historique Git pour les rattraper. Ce que la
permission gradue, c'est la prudence avant d'appeler — pas la trace après. Il n'existe **pas** de journal séparé : un fichier
d'audit que personne ne relit ne sert à rien, alors que cette note passe par
une revue.

Deux limites, à connaître plutôt qu'à découvrir :

- La note s'écrit **en fin de session**. Une session interrompue ne laisse
  rien. C'est un journal de travail, pas un journal d'audit infalsifiable —
  le coffre n'en fournit pas, et n'a pas vocation à en fournir.
- Le dépôt est **public** (§4). On consigne la **nature** de l'action, pas
  nécessairement sa cible : jamais d'adresse IP privée, de nom d'hôte interne,
  d'URL interne ni d'identifiant. Une trace qui ne peut pas être publiée n'a
  pas sa place dans ce dépôt — et c'est une raison de ne pas créer de journal
  dédié, qui inviterait précisément à l'y mettre.

Pour une trace vivante pendant la session, `brouillon/` est la zone du
provisoire ; le skill `cloture-de-session` la consolide ici à la fermeture.

## 10. Méthode d'exécution

Ce contrat lu, l'ordre à suivre pour toute demande — un harness peut le
citer ou l'injecter, il ne le redéfinit jamais (cf. préambule) :

1. Choisis l'agent pertinent pour la demande, via `IA/system/agents-index.md`
   ou l'index fourni par le harness. S'il n'y en a qu'un, c'est lui par
   défaut. Lis `IA/agents/<nom>.md` pour son rôle et ses règles propres.
2. Identifie, PARMI les skills et les MCP déclarés par cet agent, ce qui est
   nécessaire à la demande — et seulement ça.
   - Skill : lis `IA/skills/<nom>.md`, applique la procédure décrite.
   - MCP : lis `IA/MCP/<nom>.md` avant d'appeler un de ses outils — il donne
     les permissions et les règles de sécurité propres à cet outil (marqué
     `permission: elevated` quand il touche un système externe : réseau,
     dépôt distant).
3. Mémoire — dès qu'une décision est prise ou qu'une information mérite
   d'être retrouvée plus tard : écris-la à l'emplacement que le §6 assigne à
   sa nature — `mémoire/profil-utilisateur.md`, `mémoire/préférences/`,
   `mémoire/projets/<nom-projet>/`, ou ton propre `expériences/`. Crée le
   dossier s'il n'existe pas. Vérifie au §2 si l'écriture est directe ou passe
   par patch.

   Avant d'écrire une note durable, **lis celle qui existe déjà** sur le même
   sujet : un fait qui change se corrige sur place, il ne se réécrit pas à
   côté. Ne touche JAMAIS un fichier généré à la main — voir §11.
4. Cite les chemins des fichiers utilisés dans ta réponse.

Ne charge pas de fichier « pour voir ». Si aucun skill ne correspond, réponds
directement en le signalant. Un skill `read_only: true` n'exécute aucune
commande modifiant l'état du système : s'il conclut à une action, énonce-la
sans la faire.

## 11. Fichiers générés et vérification

Certains fichiers du coffre **décrivent** d'autres fichiers. Ils sont produits
par script, jamais saisis : écrits à la main, ils divergent de leur source sans
que rien ne le signale.

| Fichier | Produit par | Source de vérité |
| --- | --- | --- |
| `mémoire/**/sommaire.md` | `scripts/regenerate_sommaire.py` | le contenu des notes |
| `IA/system/agents-index.md` | `scripts/regenerate_index.py` | le frontmatter des agents |
| `IA/system/skills-index.md` | `scripts/regenerate_index.py` | le frontmatter des skills |
| `IA/system/taches-index.md` | `scripts/regenerate_index.py` | le frontmatter des tâches |
| `IA/README.md` | `scripts/regenerate_index.py` | les frontmatters d'agents, skills, MCP et tâches |

Corollaire : si un index et un frontmatter se contredisent, **le frontmatter a
raison**. On corrige la source, puis on régénère — jamais l'inverse.

`scripts/verifier_coffre.py` refuse un coffre incohérent : frontmatter
invalide, `name` différent du nom de fichier, liste écrite en chaîne,
description repliée sur plusieurs lignes physiques, agent déclarant un skill ou
un MCP inexistant, tâche sans instruction ou au `quand` non quoté, chemin cité
ou lien Markdown qui ne mène nulle part, nom de note en double, fichier généré
périmé. Il n'écrit rien et sort en code 1.

Il **avertit** en plus, sans refuser, quand un skill dit de charger un skill
que l'agent qui le déclare ne possède pas : la consigne est alors
inapplicable pour cet agent, et la procédure s'arrête là sans que rien ne le
dise. Un avertissement et non une erreur, pour deux raisons — la détection
repose sur le verbe employé, donc sur une heuristique ; et l'absence peut être
**voulue**, une frontière de périmètre plutôt qu'un oubli. C'est alors au
skill qui renvoie de l'énoncer, et à l'exemption du vérificateur de porter la
raison.

`scripts/evaluer_routage.py` contrôle autre chose, que le précédent ne voit
pas : le **déclenchement**. La `description` d'un skill est le seul élément
toujours présent en contexte, donc la seule chose qui décide qu'un skill se
charge — et rien ne vérifiait qu'elle porte les mots que l'utilisateur
emploie. Le script lit le registre `IA/system/routage-attendu.md`, classe les
skills par proximité lexicale pour chaque demande, et sort en 1 si le skill
attendu n'atteint pas le rang exigé ou si deux descriptions se ressemblent
trop.

Deux choses à savoir, pour ne pas lui prêter plus qu'il ne fait :

- la mesure est **lexicale**, pas sémantique. Elle attrape les deux pannes
  réelles — un mot que l'utilisateur dit et qui manque à la description, une
  description trop large qui passe devant la bonne — et rien d'autre ;
- **un échec veut dire « corriger la description »**, pas « corriger le
  registre ». Une attente ne se relâche que lorsqu'elle demande l'impossible
  à une mesure lexicale, et cela s'écrit dans le registre avec sa raison.

Ses exemptions — les paires de skills qui se ressemblent légitimement — vivent
**dans le script**, jamais dans le frontmatter d'un skill : un skill qui se
déclare lui-même dispensé d'un contrôle annule le contrôle.

Le contrôle des chemins s'arrête à `IA/` et aux documents de la racine : là, un
chemin faux **agit** — une instruction de tâche part au déclenchement, un skill
dit d'ouvrir un fichier. `mémoire/` en est exempté : c'est un récit, où une
note ancienne cite légitimement un état révolu. `IA/system/session-log/` l'est
aussi, pour la même raison et bien qu'il vive sous `IA/` : un log dit ce qui a
été fait ce jour-là, aux chemins de ce jour-là. Le corriger après un
déplacement lui ferait annoncer la création d'un fichier à un endroit qui
n'existait pas encore — on falsifierait le récit pour faire taire le contrôle.

Trois précisions sur ce contrôle, parce qu'un contrôle qu'on croit plus large
qu'il n'est vaut moins que pas de contrôle du tout :

- il couvre les chemins **depuis la racine du dépôt** (`IA/…`, `scripts/…`) et
  les chemins **relatifs**, résolus depuis le fichier qui les cite — c'est
  cette seconde forme qui casse quand un skill change de forme (§6) ;
- il couvre les **scripts appelés dans un bloc de code** (`python3 …`) : c'est
  là que vivent les commandes qu'une tâche exécutera vraiment. Le reste d'un
  bloc de code n'est pas contrôlé — on y écrit des arborescences d'exemple ;
- il **écarte les chemins du coffre parent** (§7) : ils désignent des dossiers
  hors du dépôt, que le vérificateur ne peut pas voir.

Il tourne en intégration continue à chaque poussée
(`.github/workflows/verifier-coffre.yml`), et localement en crochet de
pré-commit — à activer une fois par clone :

```bash
git config core.hooksPath .githooks
```

Le crochet refuse alors un commit qui laisserait le coffre incohérent, et
rappelle la commande de régénération. `git commit --no-verify` le contourne
ponctuellement ; la CI, elle, ne se contourne pas.

À lancer aussi à la main, avant un commit :

```bash
python3 scripts/regenerate_sommaire.py
python3 scripts/regenerate_index.py
python3 scripts/verifier_coffre.py
python3 scripts/evaluer_routage.py
```

Pour savoir quel skill répondrait à une demande, sans rien vérifier :

```bash
python3 scripts/evaluer_routage.py --explique "ça plante quand je clique"
```

Ces scripts n'utilisent que la bibliothèque standard de Python, à dessein : le
coffre ne doit dépendre d'aucune installation pour être vérifiable.

---

## 12. Tâches planifiées

Une tâche planifiée est déclarée **dans le coffre**, jamais seulement chez
celui qui l'exécute. Le fichier `IA/tâches/<nom>.md` est la source de vérité ;
le timer systemd, le planificateur du harness ou le cron de la machine n'en
sont que des **instances** — jetables, reconstructibles.

Le motif est le même qu'au §11 pour les index : ce qui n'existe qu'à un seul
endroit se perd sans que rien ne le signale. Sans registre, changer de harness
ou de machine efface silencieusement des tâches dont plus personne ne connaît
l'existence. Avec registre, la perte se répare : on relit le registre et on
ré-instancie.

Trois règles en découlent :

- **Le registre déclare une intention, jamais un état.** Ni identifiant
  d'instance, ni nom de machine, ni date du dernier déclenchement : ces
  informations vieillissent mal, et le dépôt est public (§9). L'état se lit
  chez l'exécutant, au moment où on le demande. `exécutant` n'y déroge pas :
  il dit quelle **classe** d'exécutant a le droit de déclencher la tâche, pas
  où elle tourne en ce moment — une règle, pas un constat.
- **Une tâche = au plus une instance vivante, tous exécutants confondus.**
  C'est l'invariant du registre. Sans lui, une tâche créée par le
  planificateur du harness puis instanciée en timer local se déclenche deux
  fois — et la réconciliation, qui ne regarderait qu'un seul exécutant,
  fabriquerait elle-même le doublon en croyant réparer un manque. Le champ
  `exécutant` du §5 tranche d'avance : il dit qui, et donc qui pas.
- **Une instance porte le nom de sa tâche, préfixé `obsia-`.** C'est la seule
  clé qui permette de rapprocher registre et exécutant quel que soit ce
  dernier ; le préfixe distingue au passage ce qui vient du coffre de ce que
  l'utilisateur a planifié par ailleurs.
- **L'instruction d'une tâche est auto-suffisante.** Au déclenchement il n'y a
  plus de conversation : le corps du fichier est tout ce qui sera reçu.

Créer, modifier ou suspendre une tâche touche `IA/tâches/` : **patch Git revu**
(§2). Instancier ou retirer une instance chez l'exécutant est une action à
effet externe : une ligne dans le log de session (§9).

`IA/system/taches-index.md` en est l'index généré, toujours présent en
contexte : c'est par lui qu'un harness neuf apprend qu'une tâche existe.
**Savoir n'est pas instancier** — l'index informe, il ne déclenche rien ; c'est
ce qui permet de constater qu'une tâche déclarée ne tourne nulle part.

La procédure — lister, créer, instancier, réconcilier — vit dans le skill
`cron` (`IA/skills/cron/cron.md`). Ce contrat ne nomme aucun exécutant : il dit
*quoi* planifier, le harness fournit *avec quoi*.
