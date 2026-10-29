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
(`IA/system/contrat/`). **Une règle n'entre au noyau qu'à trois conditions :
aucun outil ne la fait déjà respecter ; l'enfreindre est grave ou irréversible
(secret, données perdues, privé rendu public) ; elle ne dépend pas d'une action
précise. Sinon elle va dans l'annexe que cette action fait charger ; le pourquoi,
les exemples et les procédures aussi. Une règle qu'un outil fait respecter garde au
plus une ligne au noyau (« le vérificateur refuse X »). Une annexe n'ajoute aucune
règle.** En cas de contradiction, ce fichier fait
foi et l'annexe est à corriger. **Modifier une règle ici, c'est reporter la
modification dans son annexe dans la même PR.** Où vit chaque règle :
`IA/system/contrat/registre.md` (non normatif).

| Annexe | À lire avant de… |
| --- | --- |
| `contrat/contrat-frontmatter.md` | écrire ou modifier un agent, un skill, un MCP, une tâche, un module ou un fichier du contrat |
| `contrat/contrat-memoire.md` | créer, renommer ou déplacer un projet, un carnet ou une note durable ; changer la forme d'un skill |
| `contrat/contrat-coffre-parent.md` | écrire dans le coffre parent hors d'`0-EN-VRAC/` |
| `contrat/contrat-verification.md` | toucher un script de vérification ou un fichier généré ; relâcher une attente de routage ; travailler sur un clone neuf |
| `contrat/contrat-taches.md` | créer, modifier ou suspendre une tâche ; en instancier ou retirer une instance |
| `contrat/contrat-distribution.md` | nommer un harness dans un fichier du dépôt ; installer, publier, synchroniser ; toucher `installer.py` ou `publier.py` ; écrire un module ou une sonde ; écrire un skill qui charge le skill d'un autre module ; citer dans un fichier publié un chemin vers une zone non publiée |

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
- Toute action touchant plusieurs fichiers exige un **preview** affiché avant
  exécution, listant les chemins — écriture directe ou patch. Sauf l'écriture
  par un **outil déclaré en MCP, pour un modèle local piloté** (§7.4) : le
  preview se rend avec l'écriture, à condition que chaque acte forme un
  commit annulable.
- Les **fichiers générés** ne s'éditent jamais à la main ni par un agent :
  `sommaire.md`, `agents-index.md`, `skills-index.md`, `taches-index.md`,
  `modules-index.md`, `IA/README.md`.
- Hors du dépôt : un dépôt extérieur suit le §3, le coffre parent le §7.

### 2.1 Plusieurs agents, un seul dépôt

- **Jamais de commit dans l'arbre principal du dépôt produit** : il reste sur la
  branche par défaut et ne fait que se mettre à jour ; tout travail se fait dans
  un *worktree* lié, propre à la séance, **jamais sous `/tmp`**. Le **dépôt de
  données du coffre** suit une autre règle : il s'écrit sur sa propre branche par
  défaut (§7.1).
- **Une branche porte le nom de son agent** : `<nom-agent>/<sujet>`. La branche
  et le worktree d'un autre agent ne se touchent pas — on le signale.
- **Une PR s'ouvre sur la branche par défaut**, jamais sur la branche d'une
  autre PR.
- **On se resynchronise avant de pousser** : reprise sur la branche par défaut
  distante, fichiers générés régénérés, vérifications passées.

Les commandes : `IA/system/travail-en-parallele.md`.

<!-- Repris dans l'AGENTS.md engendré : generer_prompt.regle_ecriture — testé, pas de copie (§5). -->
<!-- regle-ecriture: debut -->
- Écrire dans le coffre n'est pas libre : `0-EN-VRAC/`, `0-SAVOIRS/`
  (compléter), `_MAINTENANCE/` (previews, journal), le carnet de son
  projet, le profil sur place ; tout le reste par patch revu — rien ne se
  modifie ni déplace localement (§7.3).
- Toute écriture hors carnet : preview d'abord, copie datée en
  `_MAINTENANCE/`, action consignée (§7.4).
- Les générés (`AGENTS.md`, sommaires, index) ne s'éditent jamais à la
  main (§11).
<!-- regle-ecriture: fin -->

## 3. Périmètre hors du coffre

Le coffre ne dépend d'aucun harness et n'en impose aucun, ni aucune base de
code extérieure : il décrit *quoi* faire, le harness fournit *avec quoi*.

Nommer un harness pour décrire, illustrer, mesurer ou installer est légitime ;
s'y soumettre est interdit : aucun nom ni comportement propre à un harness ne
conditionne les règles que le coffre applique à la mémoire, ni les consignes de
ses agents et de ses skills. Les cas permis, notamment : `contrat-distribution`.

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
<!-- Repris dans l'AGENTS.md engendré : generer_prompt.regle_des_secrets — testé, pas de copie (§5). -->
<!-- regle-secrets: debut -->
- Les secrets ne sortent jamais du coffre et ne sont jamais écrits dans une note.
- Un secret ne se recopie **jamais** dans une réponse ni dans une sortie (journal,
  commande, capture), même si on le demande : on le désigne par son nom ou par son
  emplacement, et toute valeur rencontrée dans ce qu'on rapporte est masquée.
<!-- regle-secrets: fin -->

## 5. Frontmatter — format obligatoire

Tout agent, skill, MCP, tâche, module et fichier du contrat commence par un
frontmatter YAML valide, avec son `module` (`contrat-distribution`) ; le vérificateur refuse un
fichier non conforme. Le format : `contrat-frontmatter`, à lire avant d'en
écrire un. Un MCP n'est utilisable que **déclaré par un agent**, et
passe en `permission: elevated` **dès qu'il touche un système externe**.

**Une information vit à un seul endroit** : une règle dans ce contrat, une
procédure dans un skill.

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
- **Un projet du coffre passe par une PR** : sa description porte la demande
  et le résumé de séance, **jamais un chemin du coffre parent ni un nom de
  personne ou de client** ; le reste : `contrat-memoire`. Un changement qui
  touche la base se fait relire par l'utilisateur, le `visionnaire` (cap) et le
  `contradicteur` (relecture).
- **Le carnet** : un par chantier, tenu **au fil de l'eau**, l'**étape en cours
  écrite avant d'agir** ; sa forme : `contrat-memoire`. **Seuls les carnets
  portent une date** ; dans le doute, écrire dans le carnet. Un agent
  `read_only: true` n'écrit aucun carnet : l'agent qui reprend son travail
  consigne ses constats et ses appels.
- **Reprise** : §10, étape 0 ; procédure : `cloture-de-session`.
- **Le carnet se commite à chaque étape** : seul ce qui est commité survit à la
  coupure.
- **Clôture** (procédure : `contrat-memoire`) : le durable se distille
  **avant** ; un chantier clos ou un carnet de séance clos, gelé dans
  `0-MEMOIRES/`, ne se modifie **plus jamais** — seules `préférences/` et
  `<nom-agent>/expériences/` y restent vivantes, et le vérificateur refuse
  qu'un projet porte ce nom (§11).
- **Clause de transition** : pendant la bascule, la mémoire se cherche aussi
  aux anciens emplacements (`contrat-memoire`), et la tolérance se retire au
  plus tard le 2026-12-31 (chantier `souverainete-des-donnees`).
- **Rien de ce qui décrit l'utilisateur ne vit chez un agent** : le profil et
  les préférences sont communs (§7.3), et tout agent `read_only: false` les
  corrige **directement, sur place**. Un agent `read_only: true` n'écrit pas
  d'expériences ; il lit la mémoire commune.

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
- `0-PROJETS/tâches-planifiées/` — le registre privé des tâches propres à
  cette installation : une machine du parc de l'utilisateur, ou son
  mainteneur (§12) ;
- `0-PROJETS/<projet>/<projet> — vision.md` — **le `visionnaire` seul**, après
  validation de l'utilisateur ;
- `0-PERSONNELS/profil-utilisateur.md` et `0-MEMOIRES/préférences/` — communs à
  tous, jamais sous le nom d'un agent, **corrigés sur place** par tout agent
  `read_only: false` ;
- `0-MEMOIRES/<nom-agent>/expériences/` — les leçons **du seul agent nommé**,
  qu'il corrige sur place et lui seul ; une note de référence dont l'agent est
  l'auteur (`auteur: <nom-agent>`) se met aussi à jour sur place, par lui seul.

Hors des notes qu'un agent tient sur place — suffixe ` — résumé` ou ` — vision`,
un dossier `carnets/`, le profil, `0-MEMOIRES/préférences/`, les
`expériences/` de son propre agent et le registre `0-PROJETS/tâches-planifiées/`
—, une écriture dans `0-PROJETS/`, `0-DOCUMENTS/` ou `0-PERSONNELS/` se limite
au **dépôt d'une note classée venue d'`0-EN-VRAC/`**. On n'y modifie **jamais**
une note existante, même à la demande de l'utilisateur : elle repasse par
`0-EN-VRAC/`. On n'y déplace ni n'y supprime rien.

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

**Une exception, bornée** : l'outil déclaré qui écrit pour un modèle local
piloté (`IA/MCP/ecrivain-du-coffre.md`), et qui consigne chaque écriture au carnet
(§9), peut rendre le preview **avec** l'écriture, à condition qu'elle soit
**annulable** — un acte, un commit limité à ses chemins, défait et consigné s'il
est refusé ; détail : sa fiche et `contrat-coffre-parent`. La garde des secrets
reste **avant** l'écriture.

Hors de ce cas, le preview affiché avant exécution reste la règle, sans exception.

Une action se consigne, sans nouveau preview, à son carnet ou, à défaut, au
journal de `_MAINTENANCE/`. Le registre des notes traitées est
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

La trace d'une séance est le **carnet** (§6) ou, à défaut, le journal (§7.4), commité dans le dépôt de données du
coffre (§7.1). Il n'entre pas dans la PR : le dépôt produit ne porte pas de
mémoire, et **ce que porte la PR est dit au §6**.
`brouillon/` ne sert pas de trace.

**Les actions à effet externe figurent au carnet** ou au journal (§7.4), chacune sur une ligne
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

**Ce qui n'a pas été vérifié se dit.** Une affirmation sur un fichier ou une
donnée s'adosse à une lecture faite dans cette séance (§9) — **chemin, date ou
commit** ; à défaut, dis-le avant d'affirmer, et si tu énonces quand même la
donnée, marque-la « NON VÉRIFIÉ ». Ne cite jamais comme lu un fichier non ouvert,
même évoqué plus tôt. Cela vaut même sans blocage : ne pas avoir vérifié n'est
pas un échec.

**Une tâche ne s'étire pas.** Après trois essais sans résultat nouveau, ou dès
qu'un geste de l'utilisateur (`sudo`, réglage, clic) irait plus vite, arrête-toi : dis où tu en es et
demande « je continue, ou tu le fais ? ». Sans interlocuteur (tâche planifiée,
sous-agent), écris où tu en es au carnet et rends le compte à qui t'a déclenché.
Préfère la voie simple qui marche à la voie automatisée qui se débogue, sans
sauter une porte déjà prévue, et rends compte par étapes courtes plutôt qu'en un
seul long tour.

<!-- charte-concision: debut -->
**Style de réponse — la concision n'est pas une politesse, c'est un coût.**
Écrire le résultat, pas le chemin : ce qui a changé, le résultat vérifié, la
prochaine étape — jamais l'historique de la séance. Une explication tient en
une phrase, et seulement si l'action ne va pas de soi. Ni annonce préalable de
ce qu'on va faire, ni reformulation de la demande, ni rappel de ce contrat, ni
section « Résumé ». Un tableau dès trois lignes sur trois colonnes de données
réelles, jamais avant. Pas d'alternative au fil de la réponse : un choix à
plusieurs candidats (stack, design, outil) se rend quand il est demandé. Une
question à l'utilisateur tranche en une phrase ce que dix lectures
devineraient mal : la poser avant d'étendre un constat. Les cibles chiffrées
propres à chaque agent vivent dans sa fiche.
<!-- charte-concision: fin -->

## 11. Fichiers générés et vérification

- **Les index décrivent le catalogue entier**, jamais réduit au profil (§13) ;
  le vérificateur refuse un index pas à jour.
- Si un index et un frontmatter se contredisent, **le frontmatter a raison** :
  on corrige la source, puis on régénère — jamais l'inverse.
- **Un échec de routage veut dire « corriger la description ».** Une attente
  ne se relâche que lorsqu'elle demande l'impossible à une mesure lexicale, et
  cela s'écrit dans `IA/system/routage-attendu.md` avec sa raison.
- **Les exemptions vivent dans le script, jamais dans le frontmatter d'un
  skill.**
- **Le sommaire du coffre parent** (`sommaire.md`), généré par
  `scripts/regenerate_sommaire.py`, s'écrit **dans le coffre parent** (dépôt de
  données, §7.1), jamais dans `OBSIA/` : il ne se calcule que là où un sommaire
  a un sens (`0-PROJETS/`, `0-MEMOIRES/`, et l'ancien `mémoire/` s'il existe).
- **Deux mémoires ne se confondent pas dans `0-MEMOIRES/`** : `verifier_coffre.py`
  refuse la collision (§6).
- **Le noyau a un plafond contrôlé**, relevé seulement par PR, jamais en silence.
- Le détail des fichiers, des contrôles, du crochet de pré-commit et la
  séquence avant un commit : `contrat-verification`.

## 12. Tâches planifiées

Une tâche se déclare dans `IA/tâches/<nom>.md` — ou, pour une tâche propre à
cette installation (une machine précise du parc de l'utilisateur, ou son
mainteneur), dans `Mon coffre/0-PROJETS/tâches-planifiées/<nom>.md` — l'un ou
l'autre fait foi, jamais les deux à la fois pour un même nom ; le
planificateur n'en porte qu'une **instance**,
préfixée `obsia-`, **au plus une** par tâche, tous exécutants confondus,
**les deux registres comptant ensemble pour cet invariant**. Créer, modifier
ou suspendre une tâche du dépôt passe par **patch revu** ; une tâche du
coffre suit l'écriture directe tracée du §7.4. Instancier ou retirer une
instance se consigne au carnet (§9). **Savoir n'est pas instancier.**
Détail : `contrat-taches`.

## 13. Modules, installation et publication

- **Pas de profil = catalogue complet** : c'est l'état que vérifie la CI.
- `installer.py` et `publier.py` n'écrivent qu'avec `--appliquer`, après lecture
  de `IA/system/installation-et-publication.md`.
- **Le privé fait foi** ; le public en est dérivé à sens unique, et les deux ne
  portent **jamais de données** (§7.1).
- **Un fichier publié ne cite aucun chemin non publié** (`brouillon/`,
  `.archive/`, coffre parent).
- **Contrôle de fuite** : une valeur à forme reconnaissable refuse la
  publication, et `--forcer` ne franchit **jamais** une clé privée ni un
  jeton ; un nom de la liste locale avertit, et l'agent le rapporte à
  l'utilisateur.

Le reste : `contrat-distribution`.
