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
(`IA/system/contrat/`). **Une règle qu'on peut enfreindre sans avoir rien chargé
vit ici ; le pourquoi, les exemples et les procédures vont dans une annexe ou un
skill, qui n'ajoutent aucune règle.** En cas de contradiction, ce fichier fait
foi et l'annexe est à corriger. **Modifier une règle ici, c'est reporter la
modification dans son annexe dans la même PR.** Correspondance avec le contrat
d'avant le découpage : `IA/system/contrat/registre.md` (non normatif).

| Annexe | À lire avant de… |
| --- | --- |
| `contrat/contrat-frontmatter.md` | écrire ou modifier un agent, un skill, un MCP, une tâche, un module ou un fichier du contrat |
| `contrat/contrat-memoire.md` | créer, renommer ou déplacer un projet, un carnet ou une note durable ; changer la forme d'un skill |
| `contrat/contrat-coffre-parent.md` | écrire dans le coffre parent hors d'`0-EN-VRAC/` |
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
(`agents-index.md` dit lesquels existent) ; aucun autre nom n'apparaît nulle
part — skill, exemple, diagramme, note. Pour un exemple, prendre un nom de
skill, jamais un nom d'agent imaginaire. `scripts/verifier_coffre.py` le contrôle.

## 2. Écriture dans le coffre

- Le coffre est en **lecture seule** pour les agents dont `read_only: true` :
  **aucune écriture nulle part, même pas par patch**.
- Un agent `read_only: false` écrit **directement, sans patch** dans le coffre
  parent, aux zones que le §7.3 autorise, et dans `IA/skills/` s'il déclare le
  skill `createur-de-skill`. Dans le dépôt produit, `brouillon/` reste la
  seule zone d'écriture libre ; la mémoire n'y a plus d'emplacement.
- Tout le reste du dépôt (`IA/agents/`, `IA/system/`, `IA/tâches/`, la
  structure) passe par un **patch Git** soumis à revue humaine.
- **La mémoire ne s'archive plus dans un dossier** : l'historique Git du dépôt de
  données (§7.1) en tient lieu. `.archive/` reste **versionné** pour le reste du
  dépôt produit ; rien n'y est lu ni indexé — les dossiers en `.` sont écartés.
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
- Ajouter une fonctionnalité = d'abord un **skill** dans `IA/skills/`, puis le code.

## 4. Exécution de code

- Toute exécution de code se fait en **sandbox**, sans exception.
- Aucun accès réseau implicite : il doit être demandé explicitement.
- Les secrets ne sortent jamais du coffre et ne sont jamais écrits dans une note.
- Un secret ne se recopie **jamais** dans une réponse ni dans une sortie (journal,
  commande, capture), même si on le demande : on le désigne par son nom ou par son
  emplacement, et toute valeur rencontrée dans ce qu'on rapporte est masquée.

## 5. Frontmatter — format obligatoire

Tout agent, skill, MCP, tâche, module et fichier du contrat commence par un
frontmatter YAML valide. Champs communs : `schema` (`1`), `kind`, `name`,
`description` (une ligne), `read_only`, `module` (le module du §13 ; un fichier
sans module est refusé). **Exceptions** : un MCP n'a ni `read_only` ni `skills` ;
une tâche n'a pas de `read_only` ; un fichier du contrat (`kind: contract`) non plus.

- `read_only: true` : écriture interdite, la règle est au §2.
- `name` = le nom du fichier, en minuscules avec tirets, **sans espaces**
  (accents permis). Un skill vit en `IA/skills/<nom>.md` ou
  `IA/skills/<nom>/<nom>.md` — **jamais `SKILL.md`** ; seul `references/`
  contient des notes. On cite le contrat **en chemin relatif**, dont la
  profondeur dépend de sa forme (`contrat-memoire`).
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
- La mémoire vit **dans le coffre parent**, jamais dans `OBSIA/` : elle
  appartient à son propriétaire et se versionne dans le dépôt de données du
  coffre (§7.1). Elle se partage sur un seul axe, **ce que la note décrit** :
  ce qui décrit l'utilisateur, un projet ou un chantier est commun à tous les
  agents ; ce qu'un agent a appris de sa propre manière de travailler reste chez
  lui. L'arborescence, l'ordre des anciens emplacements et le tableau « où
  écrire » sont dans `contrat-memoire`.
- **Tout projet vit dans `0-PROJETS/`** : le projet du coffre comme celui de
  l'utilisateur. Le test qui les sépare est le §7.3.1.
- **Un projet du coffre passe par une PR, la demande comprise** : la description
  de la PR porte la **demande** et le **résumé de séance**, jamais un chemin du
  coffre parent ni un nom de personne ou de client. Le carnet, le résumé et la
  vision vivent dans le dépôt de données (§7.1) et ne voyagent pas dans la PR :
  ce qui a été décidé s'y relit avec le diff. Un changement qui touche la base se
  fait relire par l'utilisateur, le `visionnaire` (cap) et le `contradicteur`
  (relecture).
- **Le carnet** : un par chantier, nommé avec le chantier, frontmatter `agent:`,
  `projet:`, `statut: en cours | en attente | clos`. Il vit dans le `carnets/`
  du dossier du chantier — ou du projet pour une séance sans chantier — et se
  tient **au fil de l'eau** : la demande, le plan, l'**étape en cours écrite
  avant d'agir**, les actions horodatées (§9), les worktrees et branches, les
  questions en attente. Un chantier transverse écrit dans le carnet du projet
  `obsia`, sauf ce qui décrit un projet de l'utilisateur. **Seuls les carnets
  portent une date** ; dans le doute, écrire dans le carnet.
- **Un chantier est un dossier à lui** sous son projet : ses `carnets/`, ses
  `documents/` et son ` — résumé`, un seul niveau — jamais de chantier imbriqué.
- **Une séance sans chantier** écrit dans le carnet du jour du projet de domaine
  qui la porte, sans créer de chantier. Un agent `read_only: true` n'écrit aucun
  carnet : l'agent qui reprend son travail consigne ses constats et ses appels.
- **Reprise** : au démarrage, chercher — dans l'arbre principal **et dans chaque
  worktree lié** — ses carnets `statut: en cours` (par nom d'agent, jamais de
  harness), les rapprocher de l'état réel (`git status`, `git worktree list`,
  fichiers cités) avant de proposer de reprendre ; s'il y en a plusieurs,
  l'utilisateur choisit. Procédure : `cloture-de-session`.
- **Le carnet se commite à chaque étape** : seul ce qui est commité survit à la
  coupure.
- **Clôture** : le dossier entier du chantier quitte `0-PROJETS/` pour
  `0-MEMOIRES/<projet>/<chantier>/` — le ` — résumé` devient un bilan avec une
  section « État », les carnets passent `statut: clos`, les documents suivent. Le
  durable a été distillé **avant** vers `0-SAVOIRS/`,
  `0-MEMOIRES/préférences/` ou `0-MEMOIRES/<nom-agent>/expériences/`. Le dossier
  gelé ne se modifie plus jamais.
- **`0-MEMOIRES/` porte deux mémoires, et une seule est gelée** : la mémoire des
  agents — `préférences/` et `<nom-agent>/expériences/` — y reste **vivante** et
  se corrige **sur place**, comme le profil ; un chantier clos, lui, n'y est
  **jamais** retouché. Un nom de premier niveau sous `0-MEMOIRES/` est donc, et
  rien d'autre : `préférences`, le nom d'un agent, ou un projet gelé. **Un projet
  ne peut porter ni `préférences` ni le nom d'un agent** — la collision rendrait
  deux mémoires indistinguables — et le contrôle (§11) le refuse.
- **Rouvrir** un chantier clos le ramène dans `0-PROJETS/`, `statut: en cours`,
  **sans copie laissée** dans `0-MEMOIRES/`.
- **Un domaine dormant n'est pas clos** : sans chantier actif, son dossier reste
  dans `0-PROJETS/` et **sa vision reste** — on n'archive pas un domaine vivant
  (§7.3).
- **Clause de transition** : pendant la bascule, la mémoire se cherche à tout
  emplacement qui existe, dans l'ordre détaillé par `contrat-memoire`, et la
  tolérance se retire au plus tard le 2026-12-31 (chantier
  `souverainete-des-donnees`).
- **Rien de ce qui décrit l'utilisateur ne vit chez un agent** : le profil
  (`0-PERSONNELS/`) et les préférences (`0-MEMOIRES/préférences/`, un dossier
  commun, jamais sous le nom d'un agent) sont partagés, et tout agent
  `read_only: false` les corrige **directement, sur place**. Un agent
  `read_only: true` n'écrit pas d'expériences ; il lit la mémoire commune.

## 7. Le coffre parent — la base de connaissances

`OBSIA/` est cloné à la racine du **coffre parent**, côte à côte avec les
dossiers de connaissance. La mémoire ne vit **pas** dans ce clone : elle
appartient au **dépôt de données du coffre**, versionné à part (§7.1). Le coffre
parent s'écrit **`Mon coffre/`** dans ce dépôt (nom réel : `coffre_parent` dans
`obsia.local.yml`). **`../` ne sert qu'à naviguer à l'intérieur du dépôt**,
jamais à désigner le coffre parent.

### 7.1 La structure et le dépôt de données — fixes

Seul l'utilisateur crée, renomme, déplace ou supprime un dossier de premier
niveau ; les noms s'écrivent en majuscules, tels qu'ils sont sur le disque, et
commencent par `0-` (ou `_` pour l'entretien) : `_MAINTENANCE/`, `0-PROJETS/`,
`0-MEMOIRES/`, `0-DOCUMENTS/`, `0-PERSONNELS/`, `0-SAVOIRS/`, `0-EN-VRAC/`,
`OBSIA/`. **Trois noms, trois choses** : le **coffre** est ce dossier-ci, la
mémoire de l'utilisateur ; le **dépôt de données** est le dépôt git qui la
versionne, à sa racine ; le **dépôt produit** est `OBSIA/`, l'outil, versionné à
part et publié. Rôles et gabarit `.gitignore` : `contrat-coffre-parent`.

- **Un seul dépôt de données**, à la racine du coffre parent, versionne la mémoire
  et rien d'autre : `OBSIA/` compris reste dehors, sans gitlink ni couplage.
- **Un seul écrivain Git** : la machine qui porte les agents.
- **`**/.git` est exclu de Syncthing.**
- **Les secrets ne sont pas des données de mémoire** : rien de ce que le §9
  interdit n'entre dans le dépôt de données.

### 7.2 Lecture

Un agent `read_only: false` lit tout le coffre parent. **Lire n'est pas
recopier** : rien du coffre parent ne migre dans `OBSIA/`, aucun secret n'y
entre.

### 7.3 Écriture — zones autorisées

Écritures directes, limitées et tracées (§7.4) :

- `0-EN-VRAC/` — remplir, tagger, relier, préparer le classement ;
- `0-SAVOIRS/` — compléter une note déposée par l'utilisateur, sans en changer
  le sens ni la déplacer ;
- `_MAINTENANCE/` — previews, actions, registre ;
- le **classement** d'une note d'`0-EN-VRAC/` vers sa destination ;
- `0-PROJETS/<projet>/` — le projet et ses chantiers : ` — résumé`, `carnets/`,
  `documents/`, et `code/` où le §3 s'applique intégralement ;
- `0-PROJETS/<projet>/<projet> — vision.md` — **le `visionnaire` seul**, après
  validation de l'utilisateur ;
- `0-PERSONNELS/profil-utilisateur.md` et `0-MEMOIRES/préférences/` — communs à
  tous, **corrigés sur place** par tout agent `read_only: false` ;
- `0-MEMOIRES/<nom-agent>/expériences/` — les leçons **du seul agent nommé**,
  qu'il corrige sur place et lui seul ; une note de référence dont l'agent est
  l'auteur (`auteur: <nom-agent>`) se met aussi à jour sur place, par lui seul.

**Dans `0-MEMOIRES/`, seule la moitié gelée est intouchable** : un dossier de
chantier clos y entre tel quel à la clôture et n'en bouge plus.

Hors des notes qu'un agent tient sur place — suffixe ` — résumé` ou ` — vision`,
un dossier `carnets/`, le profil, `0-MEMOIRES/préférences/` et les
`expériences/` de son propre agent —, une écriture dans `0-PROJETS/`,
`0-DOCUMENTS/` ou `0-PERSONNELS/` se limite au **dépôt d'une note classée venue
d'`0-EN-VRAC/`**. On n'y modifie **jamais** une note existante, même à la demande
de l'utilisateur : elle repasse par `0-EN-VRAC/`. On n'y déplace ni n'y supprime
rien.

### 7.3.1 Où va la note d'un projet

Le test, avant d'écrire : *est-ce que ça décrit le produit ?* Si oui, la note vit
dans le dépôt produit (`IA/system/`, `IA/skills/`, `IA/MCP/`, `IA/tâches/`) et
entre dans la PR, règles et tests ensemble (§3). Sinon elle vit dans le coffre
parent, sous `0-…`, **jamais dans `OBSIA/`** — dans le doute, le coffre parent.
Le §9 l'emporte sur tout. On lit `0-PERSONNELS/` librement ; on n'y écrit que
pour classer une note manifestement personnelle ou tenir sa note de référence, et
son contenu ne migre jamais dans `OBSIA/`.

### 7.4 Preview et traçabilité — `_MAINTENANCE/`

Avant toute écriture dans le coffre parent hors d'`0-EN-VRAC/` — un carnet de
projet compris — : afficher le preview (forme du preview : §2), en **conserver
une copie datée dans `_MAINTENANCE/`**, exécuter, puis consigner l'action.

**Une correction du profil, d'une préférence ou d'une expérience n'appelle pas de
preview** : elle se fait directement, sur place (§6).

Une action menée dans un chantier se consigne au carnet ; `_MAINTENANCE/` ne
reçoit que celles faites hors chantier. Un carnet dont l'agent est l'auteur se
met à jour sur place sans nouveau preview. Le registre des notes traitées est
`Mon coffre/_MAINTENANCE/notes_remplies.md` : une note qui y figure n'est pas à
revérifier, et il se met à jour après chaque traitement.

### 7.5 Rétroliens et tags — ce qui ne se viole pas

- **Les tags suivent un vocabulaire contrôlé** :
  `IA/system/tags-du-coffre-parent.md` fait foi ; jamais un tag hors liste ;
  un tag nouveau se propose par patch sur ce registre.
- **Un lien ne relie que si sa cible existe.**
- **Unicité des noms de notes (§6)** : le vérifier avant de créer une note ou un
  lien.

La procédure (format, frontmatter d'une note) : skill `traitement-des-notes`.

### 7.6 Accès du harness

Le harness doit pouvoir lire et écrire à la racine du coffre parent. Lire la
fiche `IA/MCP/coffre-parent.md` avant d'appeler un de ses outils : elle porte
les limites que le serveur ne porte pas.

### 7.7 Cycle d'une note d'`0-EN-VRAC/`

`0-EN-VRAC/` est un tampon : une session de rangement le traite **en entier**,
et ce qui y reste est ce qui n'a pas pu être tranché — le dire. Une note
d'`0-EN-VRAC/` n'est **jamais une cible de rétrolien stable**.

## 8. Sources et citations

Une note durable distingue **évidence** (avec son URL source),
**interprétation** et **synthèse produite par un agent**. Les URLs sont
regroupées en fin de fichier.

## 9. Trace des séances — le carnet

La trace d'une séance est le **carnet** (§6), commité dans le dépôt de données du
coffre (§7.1). Il n'entre pas dans la PR : le dépôt produit ne porte pas de
mémoire, et **ce que porte la PR est dit au §6**. Il n'y a pas d'autre journal.
`brouillon/` ne sert pas de trace.

**Les actions à effet externe figurent au carnet**, chacune sur une ligne
horodatée — quoi, où, résultat : **tout appel de MCP, quel que soit son
`permission`**, et toute correction appliquée à un système.

Deux limites : le carnet **n'est pas un journal d'audit infalsifiable** — ce qui
le rend contradictoire, c'est l'historique du dépôt de données et, pour le
produit, la relecture de la PR ; et l'on consigne la **nature** de l'action, pas
nécessairement sa cible — **jamais d'adresse IP privée, de nom d'hôte interne,
d'URL interne ni d'identifiant**, même dans le privé. La liste locale des noms
interdits est `~/.config/obsia/noms-interdits`, hors dépôt.

## 10. Méthode d'exécution

Ce contrat lu, l'ordre à suivre pour toute demande — un harness peut le
citer ou l'injecter, il ne le redéfinit jamais :

0. Au démarrage, cherche tes carnets `statut: en cours` — dans l'arbre principal
   **et dans chaque worktree lié** — rapproche-les de l'état réel (§6) et propose
   de reprendre. Pendant la bascule, cherche aussi aux anciens emplacements
   (§6). Un agent `read_only: true` n'a pas de carnet : il saute cette étape.
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

**Un échec se dit.** Un skill déclaré ou une fiche introuvable, un outil
refusé, un code de retour ou un résultat vide qu'on n'attendait pas : dis-le
dans ta réponse, avec ce que tu as fait à la place. Ne présente jamais un
résultat partiel comme complet, et ne remplace pas en silence un skill par ta
propre méthode.

**Une tâche ne s'étire pas.** Après trois essais sans résultat nouveau, ou dès
qu'un geste de l'utilisateur (commande `sudo`, réglage, clic) irait plus vite
que de continuer, arrête-toi : dis où tu en es, ce qui reste, et demande « je
continue, ou tu le fais ? ». Si personne ne peut répondre (tâche planifiée,
sous-agent), écris où tu en es au carnet et rends le compte à qui t'a
déclenché. Préfère la voie simple qui marche à la voie automatisée qui se
débogue, sans sauter une porte déjà prévue, et rends compte par étapes
courtes plutôt qu'en un seul long tour.

## 11. Fichiers générés et vérification

- **Les index sont versionnés, donc canoniques.** `IA/README.md` et les quatre
  `IA/system/*-index.md` décrivent le catalogue **entier** : ils ne dépendent
  pas de la machine et ne se réduisent **jamais** au profil (§13). Le profil ne
  réduit que ce qui n'est pas versionné — le prompt système et `AGENTS.md`.
- Si un index et un frontmatter se contredisent, **le frontmatter a raison** :
  on corrige la source, puis on régénère — jamais l'inverse.
- **Un échec de routage veut dire « corriger la description ».** Une attente
  ne se relâche que lorsqu'elle demande l'impossible à une mesure lexicale, et
  cela s'écrit dans `IA/system/routage-attendu.md` avec sa raison.
- **Les exemptions vivent dans le script, jamais dans le frontmatter d'un
  skill.**
- **Le sommaire du coffre parent** (`sommaire.md`) est généré par
  `scripts/regenerate_sommaire.py` et s'écrit **dans le coffre parent** (dépôt
  de données, §7.1), jamais dans `OBSIA/` : il ne se calcule que là où un
  sommaire a un sens (`0-PROJETS/`, `0-MEMOIRES/`, et l'ancien `mémoire/` s'il
  existe).
- **Deux mémoires ne se confondent pas dans `0-MEMOIRES/`** : `verifier_coffre.py`
  refuse la collision (§6).
- Le détail des fichiers, des deux contrôles, du crochet de pré-commit et la
  séquence de commandes avant un commit : `contrat-verification`.

## 12. Tâches planifiées

Une tâche se déclare **dans le coffre** (`IA/tâches/<nom>.md`, qui fait foi) ;
le timer, le cron ou le planificateur du harness n'en est qu'une **instance**.

- Le registre déclare une **intention, jamais un état**.
- **Au plus une instance vivante par tâche**, tous exécutants confondus ; le
  champ `exécutant` dit qui, et donc qui pas.
- Une instance porte le nom de sa tâche, préfixé **`obsia-`**.
- L'instruction d'une tâche est **auto-suffisante** : au déclenchement, il n'y
  a plus de conversation.
- Créer, modifier ou **suspendre** une tâche passe par **patch Git revu**.
  **Instancier ou retirer une instance** est une action à effet externe : une
  ligne horodatée au carnet (§9).
- `IA/system/taches-index.md`, toujours en contexte : **savoir n'est pas
  instancier**.

## 13. Modules, installation et publication

- **Tout agent, skill, MCP et tâche déclare son `module`** (§5).
- Un module est libre de ses dépendances, **pas de ses renvois** : un renvoi vers
  le module B s'accompagne d'une entrée `requiert` **ou** d'une consigne, au lieu
  du renvoi, pour le cas où B n'est pas installé — en nommant le module B.
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
  le privé. **Les deux dépôts sont gardés** — le privé est l'atelier où une
  fonctionnalité s'essaie, le public la distribution — et, la mémoire ayant
  quitté l'outil, ils ne diffèrent plus que par les fonctionnalités encore à
  l'essai, **jamais par des données** : la mémoire n'est ni dans l'un ni dans
  l'autre (§7.1).
- **Un fichier publié ne cite pas un chemin qui ne sera pas publié**
  (`brouillon/`, `.archive/`) : nommer la note suffit. Le coffre parent n'est
  jamais publié : aucun de ses chemins n'apparaît dans un fichier publié — pour
  la description d'une PR, §6.
- **Contrôle de fuite** : une valeur à forme reconnaissable (clé privée,
  jeton, IP privée, courriel, nom d'hôte à domaine) refuse la publication ;
  `--forcer` ne franchit **jamais** une clé privée ni un jeton connu. Un nom de
  la liste locale **avertit sans bloquer**, et l'agent qui reçoit
  l'avertissement le rapporte à l'utilisateur. Liste absente = aucun nom
  contrôlé : « aucune trouvaille » ne dit alors rien des noms nus.
