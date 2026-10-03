---
schema: 1
kind: contract
name: vault-contract
description: Règles communes à tous les agents et skills du coffre OBSIA — le noyau, toujours chargé. Source unique de vérité.
module: noyau
---

# Contrat du coffre — OBSIA

Ce fichier est la **source unique** des règles qui s'appliquent à tous les agents
et tous les skills. Un fichier agent ou skill ne redéfinit jamais ces règles :
il les référence. En cas de contradiction entre ce contrat et un autre fichier,
**ce contrat fait foi**.

Le contrat, c'est ce fichier — le **noyau**, toujours chargé — et ses annexes
(`IA/system/contrat/`). Toute règle qu'on peut enfreindre sans avoir rien
chargé est ici ; une annexe n'en porte que le pourquoi, les exemples et les
procédures, et n'ajoute aucune règle. En cas de contradiction, ce fichier fait
foi et l'annexe est à corriger. **Modifier une règle ici, c'est reporter la
modification dans son annexe dans la même PR.** La correspondance avec le
contrat d'avant le découpage : `IA/system/contrat/registre.md` (document de
travail, non normatif).

| Annexe | À lire avant de… |
| --- | --- |
| `contrat/contrat-frontmatter.md` | écrire ou modifier un agent, un skill, un MCP, une tâche, un module ou un fichier du contrat |
| `contrat/contrat-memoire.md` | créer, renommer ou déplacer un projet, un carnet ou une note durable ; changer la forme d'un skill |
| `contrat/contrat-coffre-parent.md` | écrire dans le coffre parent hors d'`-EN-VRAC/` |
| `contrat/contrat-verification.md` | toucher un script de vérification ou un fichier généré ; relâcher une attente de routage ; travailler sur un clone neuf |
| `contrat/contrat-taches.md` | créer, modifier ou suspendre une tâche ; en instancier ou retirer une instance |
| `contrat/contrat-distribution.md` | installer, publier, synchroniser ; toucher `installer.py` ou `publier.py` ; écrire un module ou une sonde ; écrire un skill qui charge le skill d'un autre module ; citer dans un fichier publié un chemin vers une zone non publiée |

---

## 1. Vocabulaire (à ne pas confondre)

| Terme | Nature | Emplacement | Rôle |
| --- | --- | --- | --- |
| **agent** | un interlocuteur | `IA/agents/` | possède un system prompt, mène une conversation, décide |
| **skill** | une compétence | `IA/skills/` | décrit *comment* faire une chose, ne décide pas |
| **MCP** | un outil | `IA/MCP/` | expose des actions structurées |
| **tâche** | une action planifiée | `IA/tâches/` | dit quoi déclencher, quand, pour quel agent ; ne décide pas |

Un agent **utilise** des skills. Un skill n'est jamais un agent. Une tâche
*déclenche* un agent, qui charge ensuite les skills dont il a besoin.
**`obsidian-manager` est un SKILL** : toute formulation suggérant qu'un skill
est un agent est une erreur à corriger.

**Un agent n'est nommé que s'il a son fichier dans `IA/agents/`**
(`agents-index.md` dit lesquels existent). Aucun autre nom n'apparaît nulle
part — skill, exemple, diagramme, note. Pour un exemple, prendre un nom de
skill, jamais un nom d'agent imaginaire. `scripts/verifier_coffre.py` le
contrôle.

## 2. Écriture dans le coffre

- Le coffre est en **lecture seule pour les agents** dont `read_only: true`.
- Un agent `read_only: false` écrit **directement, sans patch**, dans trois
  zones seulement : `brouillon/` ; `mémoire/` **sauf le dossier d'un autre
  agent** ; `IA/skills/` s'il déclare le skill `createur-de-skill`.
- Tout le reste du dépôt (`IA/agents/`, `IA/system/`, `IA/tâches/`, la
  structure) passe par un **patch Git** soumis à revue humaine.
- **Aucune suppression sans archivage préalable dans `.archive/`**, zones
  directes comprises. `.archive/` reste **versionné** (jamais ignoré par Git) ;
  rien n'y est lu ni indexé — les dossiers commençant par un point sont
  écartés partout.
- Toute action touchant plusieurs fichiers exige un **preview** affiché avant
  exécution, listant les chemins — écriture directe ou patch.
- Les **fichiers générés** ne s'éditent jamais à la main ni par un agent :
  `sommaire.md`, `agents-index.md`, `skills-index.md`, `taches-index.md`,
  `modules-index.md`, `IA/README.md`.
- Hors du dépôt : un dépôt extérieur suit le §3, le coffre parent le §7.

### 2.1 Plusieurs agents, un seul dépôt

- **Jamais de commit dans l'arbre principal** : il reste sur la branche par
  défaut et ne fait que se mettre à jour ; tout travail se fait dans un
  *worktree* lié, propre à la séance, **jamais sous `/tmp`**.
- **Une branche porte le nom de son agent** : `<nom-agent>/<sujet>`. La branche
  et le worktree d'un autre agent ne se touchent pas — on le signale.
- **Une PR s'ouvre sur la branche par défaut**, jamais sur la branche d'une
  autre PR.
- **On se resynchronise avant de pousser** : reprise sur la branche par défaut
  distante, fichiers générés régénérés, vérifications passées.

Les commandes : `IA/system/travail-en-parallele.md`.

## 3. Périmètre hors du coffre

Le coffre ne dépend d'aucun harness et n'en nomme aucun, ni aucune base de
code extérieure : il décrit *quoi* faire, le harness fournit *avec quoi*.
Quand un agent `read_only: false` intervient sur un dépôt extérieur :

- Toute modification passe par un **patch Git revu** — jamais de commit direct
  sur la branche par défaut.
- Les vérifications du projet visé passent **avant** de proposer le patch.
- **Jamais de secret** dans le code : variables d'environnement ou
  configuration hors dépôt uniquement.
- Ajouter une fonctionnalité = d'abord un **skill** documenté dans
  `IA/skills/`, puis l'implémentation.

## 4. Exécution de code

- Toute exécution de code se fait en **sandbox**, sans exception.
- Aucun accès réseau implicite : il doit être demandé explicitement.
- Les secrets ne sortent jamais du coffre et ne sont jamais écrits dans une note.

## 5. Frontmatter — format obligatoire

Tout agent, skill, MCP, tâche, module et fichier du contrat commence par un
frontmatter YAML valide. Champs communs : `schema` (`1`), `kind`, `name`,
`description` (une ligne), `read_only`, `module` (le module du §13 ; un fichier
sans module est refusé). **Exceptions** : un MCP n'a ni `read_only` ni
`skills` ; une tâche n'a pas de `read_only` ; un fichier du contrat
(`kind: contract`) n'a pas de `read_only`.

- `read_only: true` = **aucune écriture nulle part**, même via patch.
- `name` = le nom du fichier, en minuscules avec tirets, **sans espaces**
  (accents permis). Un skill vit en `IA/skills/<nom>.md` ou
  `IA/skills/<nom>/<nom>.md` — **jamais `SKILL.md`** ; seul `references/`
  contient des notes. Un agent ou un skill cite le contrat **en chemin
  relatif**, dont la profondeur dépend de sa forme :

  ```
  depuis IA/agents/ ou IA/skills/          ../system/VAULT-CONTRACT.md
  depuis IA/skills/<nom>/ (forme dossier)  ../../system/VAULT-CONTRACT.md
  ```
- Les listes YAML s'écrivent **une entrée par ligne** (jamais `skills: a, b`) ;
  les clés prennent l'underscore (`read_only`) ; un champ du frontmatter n'est
  **pas répété** dans le corps.
- MCP : `permission: elevated` **dès qu'un système externe est touché**
  (réseau, dépôt distant, navigateur). Un MCP n'est utilisable que **déclaré
  par un agent**.
- Tâche : `quand` **entre guillemets** (cron à 5 champs), `fuseau` obligatoire,
  `exécutant` (`local` | `harness`) dit qui a le droit de la déclencher,
  le champ `agent:` quand le mode est `agent`, et une section `## Instruction` ou `## Commande`
  obligatoire.

**Une information vit à un seul endroit.** Une **règle** qu'un agent peut
violer sans avoir rien chargé vit dans ce contrat ; une **procédure** qui ne
s'applique qu'en faisant la chose vit dans un skill.

## 6. Nommage, rétroliens et mémoire

- Les noms de notes sont **uniques dans tout le coffre parent**, pas seulement
  dans `OBSIA/`. Le nom d'une note dit son sujet (pas `notes.md`). Un dossier
  d'agent porte le nom de l'agent, un projet le nom du chantier — jamais
  `agent 1` ni `projets 1`.
- La mémoire se partage sur un seul axe, **ce que la note décrit** :

  ```
  mémoire/
  ├── profil-utilisateur.md              faits stables sur l'utilisateur et sa machine
  ├── préférences/<sujet>.md             goûts et règles de conduite transversaux
  ├── projets/<projet>/                  un projet du coffre
  │   ├── <projet> — résumé.md           état vivant, mis à jour sur place
  │   ├── <projet> — vision.md           finalité — visionnaire seul (§7.3)
  │   ├── carnets/AAAA-MM-JJ-<projet>-<sujet>.md  un carnet par chantier
  │   ├── documents/                     cadrages, schémas, plans hors dépôt de code
  │   ├── <sous-projet>/                 un seul niveau, même structure, sans vision
  │   └── archives/                      carnets clos
  └── <nom-agent>/
      └── expériences/<sujet>.md         leçons réutilisables, tirées d'un cas réel
  ```

  | Ce qu'on a appris | Destination | Commun ? |
  | --- | --- | --- |
  | un fait stable sur l'utilisateur, son poste, son infrastructure | `mémoire/profil-utilisateur.md`, **mis à jour sur place** | oui |
  | un goût ou une règle qui vaudra pour d'autres projets | `mémoire/préférences/<sujet>.md` | oui |
  | l'état d'un projet **du coffre** | `mémoire/projets/<projet>/<projet> — résumé.md`, **mis à jour sur place** | oui |
  | une demande, un plan, une étape, une action sur un chantier du coffre | `mémoire/projets/<projet>/carnets/AAAA-MM-JJ-<projet>-<sujet>.md` | oui |
  | une leçon tirée d'un échec ou d'une manœuvre qui a marché | `mémoire/<nom-agent>/expériences/<sujet>.md` | non — chez l'agent |

  Seuls les carnets portent une date. Dans le doute, écrire dans le carnet.
- **`mémoire/projets/` ne porte que les chantiers du coffre** ; un projet de
  l'utilisateur vit dans `Mon coffre/-PROJETS/` (§7.3.1).
- **Un projet du coffre passe par une PR, demande comprise** : sa note d'état,
  sa vision et ses carnets entrent par la même PR que la modification, relue
  par l'utilisateur, le `visionnaire` (cap) et le `contradicteur` (relecture)
  pour un changement qui touche la base.
- **Le carnet** : un par chantier, frontmatter `agent:`, `projet:`,
  `statut: en cours | en attente | clos`. Il porte la demande, le plan,
  l'**étape en cours écrite avant d'agir**, les actions horodatées (§9), les
  worktrees et branches, les questions en attente. Un chantier transverse
  écrit dans le carnet du projet `obsia`, sauf ce qui décrit un projet de
  l'utilisateur (carnet de ce projet dans `-PROJETS/`).
- **Une séance sans chantier** écrit dans le **carnet du jour** du projet de
  domaine qui la porte (`obsia`, ou `-PROJETS/<domaine>/`), sans créer de
  chantier. Un agent `read_only: true` n'écrit aucun carnet : l'agent qui
  reprend son travail consigne ses constats et ses appels.
- **Reprise** : au démarrage, chercher — dans l'arbre principal **et dans
  chaque worktree lié** — ses carnets `statut: en cours` (par nom d'agent,
  jamais de harness), les rapprocher de l'état réel (`git status`,
  `git worktree list`, fichiers cités) avant de proposer de reprendre ; s'il y
  en a plusieurs, l'utilisateur choisit. Procédure : `cloture-de-session`.
- **Le carnet se commite à chaque étape** : seul ce qui est commité survit à
  la coupure.
- **Clôture** : le `— résumé` devient un bilan avec une section « État » ; les
  carnets passent `statut: clos` et rejoignent `archives/` ; le durable remonte
  vers `préférences/` ou `expériences/`.
- **Rien de ce qui décrit l'utilisateur ne vit chez un agent** : profil et
  préférences sont communs, et tout agent `read_only: false` les corrige
  **directement, sur place**. Un agent `read_only: true` n'a pas d'espace
  mémoire ; il lit la mémoire commune.

## 7. Le coffre parent — la base de connaissances

Le dépôt est cloné à la racine du **coffre parent**, côte à côte avec les
dossiers de connaissance ; seul `OBSIA/` est versionné. Le coffre parent
s'écrit **`Mon coffre/`** dans ce dépôt (nom réel : `coffre_parent` dans
`obsia.local.yml`). **`../` ne sert qu'à naviguer à l'intérieur du dépôt**,
jamais à désigner le coffre parent.

**Piège du tiret** : les dossiers du coffre parent commencent par `-`, qu'une
commande lit comme une option. Un chemin nu ne s'écrit jamais dans une
commande : `../-SAVOIRS`, `./-PROJETS` ou un chemin absolu entre guillemets.

### 7.1 La structure — fixe

Seul l'utilisateur crée, renomme, déplace ou supprime un dossier de premier
niveau. Ces dossiers s'écrivent tels qu'ils sont sur le disque, en majuscules :
`_MAINTENANCE/` (entretien, previews, registre), `-PROJETS/` (projets de
l'utilisateur), `-DOCUMENTS/` (revues, articles, transcriptions),
`-PERSONNELS/` (contexte personnel), `-SAVOIRS/` (un fichier = un concept),
`-EN-VRAC/` (notes brutes à traiter), `OBSIA/` (le dépôt).

### 7.2 Lecture

Un agent `read_only: false` lit tout le coffre parent. **Lire n'est pas
recopier** : rien du coffre parent ne migre dans `OBSIA/`, aucun secret n'y
entre.

### 7.3 Écriture — zones autorisées

Écritures directes, limitées et tracées (7.4) :

- `-EN-VRAC/` — remplir, tagger, relier, préparer le classement ;
- `-SAVOIRS/` — compléter une note déposée par l'utilisateur, sans en changer
  le sens ni la déplacer ;
- `_MAINTENANCE/` — previews, actions, registre ;
- le **classement** d'une note d'`-EN-VRAC/` vers sa destination ;
- `-PROJETS/<projet>/` — résumé (` — résumé`), `carnets/`, `documents/`,
  `archives/`, un niveau de sous-projet ; `code/`, le dépôt git d'un projet
  construit ici, où le §3 s'applique intégralement ;
- `-PROJETS/<projet>/<projet> — vision.md` — **le `visionnaire` seul**, après
  validation de l'utilisateur ;
- `-PERSONNELS/` — une note de référence dont l'agent est l'auteur
  (`auteur: <nom-agent>`), mise à jour sur place par lui seul.

Hors de ces notes dont l'agent est l'auteur (suffixe ` — résumé` ou
` — vision`, dossier `carnets/`, champ `auteur:`), une écriture dans
`-PROJETS/`, `-DOCUMENTS/` ou `-PERSONNELS/` se limite au **dépôt d'une note
classée venue d'`-EN-VRAC/`**. On n'y modifie **jamais** une note existante,
même à la demande de l'utilisateur : elle repasse par `-EN-VRAC/`. On n'y
déplace ni n'y supprime rien.

### 7.3.1 Où va la note d'un projet

Le test, avant d'écrire : *est-ce que ça décrit le coffre ?* Si oui,
`mémoire/projets/` (privé, versionné, relu par PR, retiré du miroir public) ;
sinon `-PROJETS/`. **Dans le doute, `-PROJETS/`.** Jamais une valeur interdite
par le §9 dans `mémoire/`, même pour décrire le coffre : le §9 l'emporte.
`-PERSONNELS/` se lit librement ; on n'y écrit que pour y classer une note
manifestement personnelle ou tenir sa note de référence, et son contenu ne
migre jamais dans `OBSIA/`.

### 7.4 Preview et traçabilité — `_MAINTENANCE/`

Avant toute écriture dans le coffre parent hors d'`-EN-VRAC/` — y compris la
création du carnet d'un projet de l'utilisateur — et avant toute action qui
touche plusieurs fichiers : 1. afficher le preview ; 2. en **conserver une
copie datée dans `_MAINTENANCE/`** ; 3. exécuter, puis consigner l'action.

Une action menée dans un chantier se consigne au carnet ; `_MAINTENANCE/` ne
reçoit que celles faites hors chantier. Un carnet dont l'agent est l'auteur se
met ensuite à jour sur place sans nouveau preview. Le registre des notes
traitées est `Mon coffre/_MAINTENANCE/notes_remplies.md` : une note qui y
figure n'est pas à revérifier, et il se met à jour après chaque traitement.

### 7.5 Rétroliens et tags — ce qui ne se viole pas

- **Les tags suivent un vocabulaire contrôlé** :
  `IA/system/tags-du-coffre-parent.md` fait foi ; jamais un tag hors liste ;
  un tag nouveau se propose par patch sur ce registre.
- **Un lien ne relie que si sa cible existe.**
- **Les noms de notes sont uniques dans tout le coffre parent** : vérifier
  avant de créer une note ou un lien.

La procédure (format, frontmatter d'une note) : skill `traitement-des-notes`.

### 7.6 Accès du harness

Le harness doit pouvoir lire et écrire à la racine du coffre parent. Lire la
fiche `IA/MCP/coffre-parent.md` avant d'appeler un de ses outils : elle porte
les limites que le serveur ne porte pas.

### 7.7 Cycle d'une note d'`-EN-VRAC/`

`-EN-VRAC/` est un tampon : une session de rangement le traite **en entier**,
et ce qui y reste est ce qui n'a pas pu être tranché — le dire. Une note
d'`-EN-VRAC/` n'est **jamais une cible de rétrolien stable**.

## 8. Sources et citations

Une note durable distingue **évidence** (avec son URL source),
**interprétation** et **synthèse produite par un agent**. Les URLs sont
regroupées en fin de fichier.

## 9. Trace des séances — le carnet

La trace d'une séance est le **carnet** — du chantier, ou du jour hors
chantier (§6) —, écrit au fil de l'eau. Pour un projet du coffre, il est
versionné et entre dans la PR du travail, où il se relit avec le diff. Il n'y
a pas d'autre journal.
`IA/system/session-log/` est **archivé** : on n'y écrit plus, et ses notes ne
se réécrivent pas.

**Les actions à effet externe figurent au carnet**, chacune sur une ligne
horodatée — quoi, où, résultat : **tout appel de MCP, quel que soit son
`permission`**, et toute correction appliquée à un système.

Deux limites :

- Le carnet est écrit par l'agent qui agit : ce n'est **pas un journal d'audit
  infalsifiable**. Ce qui le rend contradictoire, c'est la relecture de la PR ;
  le carnet d'un projet de l'utilisateur, hors Git, n'a que le preview du §7.4.
- On consigne la **nature** de l'action, pas nécessairement sa cible :
  **jamais d'adresse IP privée, de nom d'hôte interne, d'URL interne ni
  d'identifiant**. Une trace qu'on ne pourrait pas publier ne s'écrit pas
  davantage dans le privé. La liste locale des noms interdits est
  `~/.config/obsia/noms-interdits`, hors dépôt.

`brouillon/` reste la zone du provisoire ; il ne sert pas de trace.

## 10. Méthode d'exécution

Ce contrat lu, l'ordre à suivre pour toute demande — un harness peut le
citer ou l'injecter, il ne le redéfinit jamais :

0. Au démarrage, cherche tes carnets `statut: en cours` — dans l'arbre
   principal **et dans chaque worktree lié** — et propose de reprendre, après
   les avoir rapprochés de l'état réel (§6). Un agent `read_only: true` n'a
   pas de carnet : il saute cette étape.
1. Choisis l'agent pertinent pour la demande, via `IA/system/agents-index.md`
   ou l'index fourni par le harness. S'il n'y en a qu'un, c'est lui par
   défaut. Lis `IA/agents/<nom>.md` pour son rôle et ses règles propres.
2. Identifie, PARMI les skills et les MCP déclarés par cet agent, ce qui est
   nécessaire à la demande — et seulement ça.
   - Skill : lis `IA/skills/<nom>.md`, applique la procédure décrite.
   - MCP : lis `IA/MCP/<nom>.md` avant d'appeler un de ses outils — il donne
     les permissions et les règles de sécurité propres à cet outil.
   - Annexe : lis-la avant l'acte que sa ligne nomme (tableau du préambule).
3. Mémoire — dès qu'une décision est prise ou qu'une information mérite
   d'être retrouvée plus tard : écris-la à l'emplacement que le §6 assigne à
   sa nature. L'étape en cours s'écrit au carnet **avant** d'agir. Crée le
   dossier s'il n'existe pas. Vérifie au §2 si l'écriture est directe ou passe
   par patch.

   Avant d'écrire une note durable, **lis celle qui existe déjà** sur le même
   sujet : un fait qui change se corrige sur place, il ne se réécrit pas à
   côté. Ne touche JAMAIS un fichier généré à la main.
4. Cite les chemins des fichiers utilisés dans ta réponse.

Ne charge pas de fichier « pour voir ». Si aucun skill ne correspond, réponds
directement en le signalant. Un skill `read_only: true` n'exécute aucune
commande modifiant l'état du système : s'il conclut à une action, énonce-la
sans la faire.

## 11. Fichiers générés et vérification

- **Les index sont versionnés, donc canoniques.** `IA/README.md` et les quatre
  `IA/system/*-index.md` décrivent le catalogue **entier** : ils ne dépendent
  pas de la machine et ne se réduisent **jamais** au profil (§13). Sinon la CI,
  qui n'a pas de profil, verrait un index périmé, et une machine réduite ne
  pourrait plus rien committer sans mentir sur son contenu. Le profil ne réduit
  que ce qui n'est pas versionné — le prompt système et `AGENTS.md`.
- Si un index et un frontmatter se contredisent, **le frontmatter a raison** :
  on corrige la source, puis on régénère — jamais l'inverse.
- **Un échec de routage veut dire « corriger la description ».** Une attente
  ne se relâche que lorsqu'elle demande l'impossible à une mesure lexicale, et
  cela s'écrit dans `IA/system/routage-attendu.md` avec sa raison.
- **Les exemptions vivent dans le script, jamais dans le frontmatter d'un
  skill.**
- Le crochet de pré-commit s'active **une fois par clone** :
  `git config core.hooksPath .githooks`.
- Avant un commit :

  ```bash
  python3 scripts/regenerate_sommaire.py
  python3 scripts/regenerate_index.py
  python3 scripts/verifier_coffre.py
  python3 scripts/evaluer_routage.py
  ```

## 12. Tâches planifiées

Une tâche se déclare **dans le coffre** (`IA/tâches/<nom>.md`, qui fait foi) ;
le timer, le cron ou le planificateur du harness n'en est qu'une **instance**.

- Le registre déclare une **intention, jamais un état** (ni identifiant
  d'instance, ni nom de machine, ni date de dernier déclenchement).
- **Au plus une instance vivante par tâche**, tous exécutants confondus ; le
  champ `exécutant` dit qui, et donc qui pas.
- Une instance porte le nom de sa tâche, préfixé **`obsia-`**.
- L'instruction d'une tâche est **auto-suffisante** : au déclenchement, il n'y
  a plus de conversation.
- Créer, modifier ou **suspendre** une tâche passe par **patch Git revu**.
  **Instancier ou retirer une instance** est une action à effet externe : une
  ligne horodatée au carnet (§9).
- `IA/system/taches-index.md`, toujours en contexte, informe : **savoir n'est
  pas instancier**.

## 13. Modules, installation et publication

- **Tout agent, skill, MCP et tâche déclare son `module`** (§5).
- Un module est libre de ses dépendances, **pas de ses renvois** : si un skill
  du module A dit de charger un skill du module B, A entraîne B (`requiert`)
  **ou** écrit, à l'endroit du renvoi, quoi faire quand B n'est pas installé,
  en nommant le module B.
- Une **sonde** est déclarative et tient en quatre formes (`commande:`,
  `fichier:`, `distribution:`, `parent:`) : **aucune n'exécute de commande
  arbitraire, aucune n'ouvre le réseau**, et une sonde ne décide jamais seule.
- Le profil `obsia.local.yml` dit quels modules sont retenus sur la machine ;
  il n'est pas versionné et seul l'installeur l'écrit. **Pas de profil =
  catalogue complet**, et c'est sous cet état que la CI vérifie le coffre.
- `scripts/installer.py` et `scripts/publier.py` n'écrivent qu'avec
  `--appliquer`. Lire `IA/system/installation-et-publication.md` **avant** de
  les lancer avec `--appliquer`.
- **Le privé fait foi** : le dépôt public en est dérivé par `publier.py`, à
  sens unique ; une correction faite sur le public se reporte à la main dans
  le privé.
- **Un fichier publié ne cite pas un chemin qui ne sera pas publié**
  (`mémoire/`, `brouillon/`, `.archive/`, `IA/system/session-log/`), sauf les
  `README.md` de ces zones et `mémoire/profil-utilisateur.md` : nommer la note
  suffit.
- **Contrôle de fuite** : une valeur à forme reconnaissable (clé privée,
  jeton, IP privée, courriel, nom d'hôte à domaine) refuse la publication ;
  `--forcer` ne franchit **jamais** une clé privée ni un jeton connu. Un nom de
  la liste locale **avertit sans bloquer**, et l'agent qui reçoit
  l'avertissement le rapporte à l'utilisateur. Liste absente = aucun nom
  contrôlé : « aucune trouvaille » ne dit alors rien des noms nus.
