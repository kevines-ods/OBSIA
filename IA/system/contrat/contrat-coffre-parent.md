---
schema: 1
kind: contract
name: contrat-coffre-parent
description: Détail du coffre parent : désignation, dépôt de données, zones d'écriture et leur raison, aperçu, rétroliens, accès du harness, cycle d'0-EN-VRAC.
module: noyau
---

# Annexe du contrat — coffre-parent

> **À lire avant d'écrire dans le coffre parent hors d'0-EN-VRAC/.** Annexe du contrat (`../VAULT-CONTRACT.md`).
> Elle précise, elle n'ajoute aucune règle : toute règle qu'on peut enfreindre
> sans avoir rien chargé est aussi au noyau, et en cas de contradiction le
> noyau fait foi — l'annexe est alors à corriger. La correspondance avec l'ancien
> contrat est suivie dans `registre.md`, document de travail non normatif.

## 7. Le coffre parent — la base de connaissances

Le dépôt OBSIA est cloné **à la racine du coffre parent**, côte à côte avec
les dossiers de connaissance. Ce coffre parent est la base de connaissances
primordiale : il se lit, s'enrichit et s'administre — par l'utilisateur, et
par les agents qui y accèdent selon ce paragraphe. La mémoire — les dossiers
`0-…` et `_MAINTENANCE/` — y est versionnée dans un **dépôt de données** à part
(§7.1) ; `OBSIA/` a le sien, et les deux ne se couplent pas.

**Le coffre parent s'écrit `Mon coffre/` partout dans ce dépôt.** C'est une
**convention d'écriture**, pas une contrainte sur le disque : le nom réel du
dossier se lit dans `obsia.local.yml` (clé `coffre_parent`, §13), que
l'installeur remplit et qui n'est pas versionné. Le dépôt se publie et ne peut
pas connaître le nom que chacun donne à son coffre ; il lui en faut pourtant un
pour en parler, sans quoi chaque skill inventerait le sien. Voici donc comment
on le désigne :

| Ce qu'on veut dire | Comment l'écrire |
| --- | --- |
| un dossier du coffre parent | `Mon coffre/0-SAVOIRS/` — jamais `../0-SAVOIRS/` |
| le dépôt lui-même | `Mon coffre/OBSIA/`, ou son chemin interne (`IA/skills/…`) |
| un fichier du dépôt, depuis un autre fichier du dépôt | relatif au fichier qui cite — depuis cette annexe : `../VAULT-CONTRACT.md` |

La règle tient en une phrase : **`../` ne sert qu'à naviguer à l'intérieur du
dépôt**, jamais à désigner le coffre parent. Sans elle, le même `../` veut dire
deux choses selon la cible — relatif au fichier ici, relatif au répertoire de
travail là — et c'est ainsi qu'un skill finit par pointer à côté.

Une **commande** reste une exception assumée : lancée depuis la racine du
dépôt, elle atteint le coffre parent par `..` (`rg "motif" ../0-SAVOIRS`). C'est
du shell, pas une désignation — et c'est aussi la forme qui se moque du nom
réel du dossier, ce qui la rend préférable au chemin absolu partout où elle
suffit. Un chemin absolu, lui, contient une espace et
se cite : `"$HOME/Mon coffre/0-SAVOIRS"`.

**Le tiret initial a disparu.** Les dossiers du coffre parent commençaient
auparavant par `-`, qu'un shell lisait comme une option : `rg "motif" -SAVOIRS`
échouait, `ls -PROJETS` aussi. Le préfixe `0-` a supprimé le piège — un chemin
de premier niveau s'écrit désormais tel quel, sans `./` ni guillemets pour le
désamorcer.

La règle de désignation, elle, ne change pas : un chemin du coffre parent
s'écrit `Mon coffre/…`, jamais `../…`, et une commande lancée depuis la racine
du dépôt l'atteint par `..` (`rg "motif" ../0-SAVOIRS`). Un chemin absolu, qui
contient une espace, se cite : `"$HOME/Mon coffre/0-SAVOIRS"`.

### 7.1 La structure et le dépôt de données — fixes

La structure de premier niveau est **fixe**. Seul l'utilisateur crée, renomme
ou supprime un dossier de premier niveau. Les agents ne modifient jamais cette
structure : ils travaillent dans les dossiers existants, sans y créer de
sous-structure de premier niveau.

Les dossiers de premier niveau s'écrivent **en majuscules**, tels qu'ils sont
sur le disque : `_MAINTENANCE/`, `0-PROJETS/`… Linux distingue la casse, et un
agent qui cherche `_maintenance/` conclut à tort que le dossier manque.

| Dossier | Rôle |
| --- | --- |
| `Mon coffre/` | la racine — le coffre Obsidian lui-même, ouvert à ce niveau, et la racine du dépôt de données |
| `OBSIA/` | le dépôt produit, versionné à part — agents, skills, tâches, scripts ; **hors** du dépôt de données |
| `_MAINTENANCE/` | journaux, astuces de débogage, previews consignés, registre des notes traitées |
| `0-PROJETS/` | les projets — notes, et le dépôt git du projet quand il en a un (7.3) |
| `0-MEMOIRES/` | la mémoire des agents — `préférences/` et `<nom-agent>/expériences/`, **vivantes** — et les chantiers clos, **gelés** (7.3) |
| `0-DOCUMENTS/` | revues, articles web, transcriptions YouTube |
| `0-PERSONNELS/` | contexte personnel : profil, configuration matérielle/logicielle, CV… |
| `0-SAVOIRS/` | les connaissances accumulées — un fichier Markdown = un concept |
| `0-EN-VRAC/` | zone de dépôt : notes brutes, parfois un simple titre à traiter |

**Un seul dépôt de données** versionne la mémoire, à la racine du coffre
parent. Son `.gitignore` est une **liste blanche** : `/*` ignore tout, puis
`!/0-*/`, `!/_MAINTENANCE/` et `!/.gitignore` ré-autorisent la mémoire, et
`0-PROJETS/**/code/` laisse hors dépôt le dépôt git d'un projet construit ici.
`OBSIA/`, `AGENTS.md`, `CLAUDE.md`, `opencode.json`, `.obsidian/`, `.claude/`,
`.aionrs/` sont donc ignorés — le dépôt produit et celui des données restent
séparés, sans gitlink.

- **Un seul écrivain Git** : la machine qui porte les agents commit à chaque
  étape, en local. La poussée vers le **distant nu du NAS** (`coffre.git`) part
  en arrière-plan et ne bloque jamais le travail.
- **`**/.git` est exclu de Syncthing** : un dépôt Git vivant ne se synchronise
  pas comme des fichiers.
- **Aucun secret dans le dépôt de données** (§4, §9), pas plus que dans le
  dépôt produit. Cette règle a un garde dans le crochet d'avant-commit du dépôt
  de données : il refuse toute valeur à forme de secret que le commit **ajoute**.
  Il reprend les motifs de **secret** de `publier.BLOQUANTS` — une seule source,
  pas de copie — et refuse en plus un fichier dont **tout le contenu** est un
  jeton sans espace à forte entropie : le mot de passe collé seul, qu'aucun motif
  nommé ne voit. La valeur d'un « secret affecté » doit avoir forme de secret :
  ne se refusent pas un gabarit jugé **en tête** (`yourpassword`,
  `change-root-password`), un chemin jugé **en tête** (`/`, `~/`, `./`, `../`) ni
  une prose **non guillemetée** ; une phrase **entre guillemets** en est un, sauf
  ligne de commande recopiée — admise seulement si elle porte **à la fois** une
  espace et un marqueur shell (`;`, `|`, accent grave, `$(`) ; la ponctuation
  ordinaire n'exempte rien. Cette règle de forme ne vaut que pour ce motif-là.
  Les motifs qui gardent la frontière *publique* (courriel, adresse IP privée,
  nom d'hôte interne) ne s'appliquent pas ici : le coffre privé les porte
  légitimement.
  Mécanique et limites : `IA/system/depot-de-donnees/README.md`.

Déplacer un dossier de premier niveau (ex. `OBSIA/` dans `0-PROJETS/`) est une
décision de l'utilisateur, pas des agents.

### 7.2 Lecture

Les agents `read_only: false` peuvent **lire tout le coffre parent** dès que
le harness donne accès à sa racine (7.6) : la recherche couvre
`_MAINTENANCE/`, `0-PROJETS/`, `0-MEMOIRES/`, `0-DOCUMENTS/`, `0-PERSONNELS/`,
`0-SAVOIRS/` et `0-EN-VRAC/`. Ces dossiers se désignent par leur nom complet
depuis la racine
(`Mon coffre/0-SAVOIRS/`) ; dans une commande lancée depuis la racine du dépôt,
ils s'atteignent par `..`.

Le coffre parent n'est **pas** un « dépôt extérieur » au sens du §3 : ce
paragraphe vise des bases de code, pas des notes.

Lire n'est pas recopier : le coffre parent est privé, le dépôt se publie
(§13.5). Rien du coffre parent ne migre dans `OBSIA/` au fil des réponses, et
aucun secret du coffre parent n'entre dans le dépôt.

### 7.3 Écriture — zones autorisées

La mémoire se versionne (§7.1), mais elle ne se **patche** pas : elle est écrite
en direct, dans des zones limitées et tracées (7.4). Un patch est un détour fait
pour une revue ; la mémoire se relit dans l'historique du dépôt de données. Les
écritures autorisées d'un agent `read_only: false` sont donc directes :

- `0-EN-VRAC/` — remplir une note, poser tags et rétroliens, préparer le
  classement ;
- `0-SAVOIRS/` — compléter une note que l'utilisateur y a déposée (tags,
  rétroliens, corps manquant), sans en changer le sens ni la déplacer ;
- `_MAINTENANCE/` — consigner previews, actions et registre des notes
  traitées ;
- le **classement** : déplacer une note d'`0-EN-VRAC/` vers sa destination
  (`0-PROJETS/`, `0-DOCUMENTS/`, `0-PERSONNELS/`, `0-SAVOIRS/`) une fois traitée ;
- `0-PROJETS/<projet>/` — **le dossier d'un projet**, même
  forme que `0-PROJETS/` (§6) : `<projet> — résumé.md` (la note de
  suivi, créée et tenue par l'agent, **mise à jour sur place** : où en est le
  projet, ce qui a été décidé, ce qui reste à faire), `carnets/` du jour,
  `documents/`, et **un dossier par chantier** — `<chantier>/`, portant ses
  `carnets/`, ses `documents/` et son `<chantier> — résumé.md` ; un seul
  niveau. **Plus aucun `archives/`** : un
  chantier clos part, dossier entier, dans `0-MEMOIRES/` (§6) ;
- `0-PROJETS/<projet>/code/` — **le dépôt git d'un projet construit ici** :
  l'agent y écrit le code et ses documents, y commite. C'est un dépôt à part
  entière, versionné pour lui-même, et la seule zone du coffre parent où du
  code vit. Le §3 s'y applique intégralement : patch revu, vérifications du
  projet passées avant de proposer, aucun secret dans le dépôt. Ce dossier
  doit être **exclu** dans le réglage « Fichiers exclus » d'Obsidian, pour que
  le Markdown du dépôt et de ses dépendances ne vienne pas encombrer la
  recherche et le graphe du coffre. L'exclusion est posée par
  `scripts/installer.py`, pour qu'elle suive le coffre d'une machine à
  l'autre ; le retrait est décrit dans `installation-et-publication.md` ;

  Ce que dit la documentation officielle : un fichier exclu est **masqué de
  la recherche, de la vue graphe et des mentions non liées**, et **moins
  visible** dans le sélecteur rapide et les suggestions de liens
  (help.obsidian.md, « Settings » → *Excluded files*). Elle **ne dit pas**
  qu'un fichier exclu cesse de compter pour la résolution des liens, et la
  syntaxe du motif n'y est pas documentée : on s'en tient donc à la forme
  `/<chemin>/`, constatée par l'usage, **sans savoir si l'ancre `^` correspond
  au chemin qu'Obsidian compare**. La recette qui tranche est écrite dans
  `installation-et-publication.md` et affichée par `installer.py` : poser un
  fichier sous `0-PROJETS/<projet>/code/`, puis chercher son nom dans Obsidian.
  L'unicité des noms de notes (§6) reste par conséquent
  **à surveiller** : l'exclusion allège l'index, elle ne garantit pas l'unicité ;
- `0-PERSONNELS/profil-utilisateur.md` et `0-MEMOIRES/préférences/` —
  **communs**, corrigés **directement, sur place** par tout agent
  `read_only: false`, **sans preview** (7.4) : un fait sur l'utilisateur se
  corrige, il ne se prévisualise pas ;
- `0-MEMOIRES/<nom-agent>/expériences/` — les leçons d'un agent sur sa propre
  manière de travailler ; il est le seul à y écrire ;
- `0-PERSONNELS/` — **une note de référence dont l'agent est l'auteur**, créée
  et tenue par lui, **mise à jour sur place**, et marquée `auteur: <nom-agent>`
  dans son frontmatter : l'inventaire d'une infrastructure, par exemple, qui
  décrit l'utilisateur et doit rester vivant — une machine ajoutée, une adresse
  changée. Seul l'agent nommé dans ce champ y écrit, et chaque mise à jour
  passe par le preview du 7.4 ;
- `0-PROJETS/<projet>/<projet> — vision.md` — **la vision d'un projet** :
  finalité déclarée, finalités possibles validées ou rejetées, portes à garder
  ouvertes. Seul l'agent `visionnaire` l'écrit, **sur place**, après validation
  de l'utilisateur. Un chantier n'a pas de vision : il relève de celle de
  son projet. **Une vision ne s'archive pas** : un domaine dormant garde la
  sienne dans `0-PROJETS/` (§6).

Une **note** de `0-PROJETS/` que l'agent n'a pas écrite n'est pas à lui : elle reste protégée
comme le reste. Hors des dossiers de projet ci-dessus (note de suivi, vision, carnets,
`code/`) et des
notes de référence ci-dessus, une écriture dans `0-PROJETS/`, `0-DOCUMENTS/` ou `0-PERSONNELS/` se limite au
**dépôt d'une note classée venue d'`0-EN-VRAC/`**, et à rien d'autre. On n'y
modifie **jamais** une note existante, même à la demande de l'utilisateur :
une note à enrichir repasse d'abord par `0-EN-VRAC/`, puis est classée. On n'y
déplace ni n'y supprime rien.

La note de suivi, la note de vision, les carnets, le profil, les préférences,
les `expériences/` de l'agent et la note de référence sont les seules
exceptions, et elles tiennent à la même raison : **ce sont les seules notes de
ces dossiers dont l'agent est l'auteur ou le correcteur attitré.** Il les a
créées, il les met à jour, personne d'autre n'écrit dedans. La règle générale
protège les notes de l'utilisateur d'une réécriture silencieuse ; elle ne
protège de rien quand l'agent corrige son propre texte, ou un fait sur son
utilisateur. Ce qui rend la distinction visible sans ouvrir la note, c'est le
suffixe ` — résumé` ou ` — vision`, le dossier `carnets/`, un chemin sous
`0-PERSONNELS/`, ou le champ `auteur:` : une note qui ne porte rien de tout cela
n'est pas à l'agent.

**Dans `0-MEMOIRES/`, seule la moitié gelée fait exception à tout** : un dossier
de chantier clos n'y est modifié **jamais** — on y entre seulement par la
clôture (§6), et rouvrir un chantier repasse par `0-PROJETS/`. La mémoire des
agents y vit au contraire comme partout : `0-MEMOIRES/préférences/` et
`0-MEMOIRES/<nom-agent>/expériences/` se corrigent **sur place**. C'est la même
zone, pas la même règle — et c'est écrit pour que personne ne les confonde.

### 7.3.1 Où va la note — le seul partage est « est-ce que ça décrit le produit ? »

Deux endroits portent des notes, et un seul test les sépare.

| La note porte sur… | Elle va dans… | Visibilité |
| --- | --- | --- |
| le produit — un skill, un agent, une règle, une fiche MCP, une tâche | `OBSIA/`, sous `IA/` | dépôt produit, relu par PR, miroir public dérivé par `publier.py` (§13.5) |
| tout le reste — une personne, un savoir, un projet, un chantier | le coffre parent, sous `0-…` | privée — le coffre parent n'est jamais publié |

Le coffre parent et le dépôt produit ne se mélangent pas : une note qui décrit
le produit vit dans le produit, et **tout projet du coffre passe par une PR**,
décrite au §6 et au §9. Le reste — la vie de l'utilisateur, un savoir,
l'histoire d'un chantier — vit dans le coffre parent, que `publier.py` n'atteint
pas : il traite le dépôt produit, pas la mémoire. Un secret n'y entre pas
davantage (§7.2).

Le test, avant d'écrire : *est-ce que ça décrit le produit ?* Si oui, `OBSIA/`.
Sinon, le coffre parent, sous `0-…`. **Dans le doute, le coffre parent** : une
note qui atterrit dans le dépôt du produit se publie avec lui, et l'historique
Git la garde même effacée.

`0-PERSONNELS/` porte du contenu **personnel mais non critique** : configuration
matérielle, CV. Les préférences, elles, vivent dans `0-MEMOIRES/préférences/`,
avec la mémoire des agents. Le dossier **participe au graphe de liens** comme les
autres dossiers — ces notes doivent être reliées au reste, sinon elles ne
servent à rien. Un agent le lit donc librement pour établir des rétroliens et
pour répondre.

Deux limites tiennent quand même : on n'y **écrit** que pour y classer une note
dont la nature est manifestement personnelle, ou pour tenir une note de
référence dont on est l'auteur (§7.3 ci-dessus), et son contenu
ne migre jamais dans `OBSIA/`, qui est public (§7.2). Un secret — mot de passe,
jeton, clé — n'a sa place ni ici ni ailleurs (§4).

### 7.4 Preview et traçabilité — `_MAINTENANCE/`

La mémoire se versionne (§7.1), mais le preview reste la trace lisible au moment
de l'acte. Avant toute écriture dans le coffre parent hors d'`0-EN-VRAC/` — note
créée, complétée, déplacée, création du carnet d'un projet comprise —, et avant
toute action qui touche plusieurs fichiers, l'agent :

1. affiche le preview — fichiers concernés, contenu final, destination ;
2. en **conserve une copie datée dans `_MAINTENANCE/`** ;
3. exécute, puis consigne l'action (quoi, où, résultat) dans `_MAINTENANCE/`.

`_MAINTENANCE/` ne porte que l'**entretien du coffre parent** : previews,
actions consignées, registre, index. Le récit d'un chantier va dans son
carnet (§6), pas ici. Une action menée dans un chantier se consigne au
carnet ; `_MAINTENANCE/` ne reçoit que celles faites hors chantier. Un
carnet dont l'agent est l'auteur se met ensuite à jour sur place sans
nouveau preview : exiger un preview à chaque étape pousserait à tout écrire
en fin de séance, ce que le §6 interdit.

**La correction du profil et des préférences ne demande aucun preview** : elle
se fait directement, sur place (§6), et se relit dans le commit suivant du dépôt
de données. Le preview protège une note qu'on ne possède pas ; celle-ci est faite
pour être corrigée à mesure.

Le registre des notes traitées est le fichier
**`Mon coffre/_MAINTENANCE/notes_remplies.md`** — une note Markdown, pour
qu'Obsidian l'indexe et la rende consultable comme le reste. Il liste les
notes déjà remplies, surtout celles de `0-SAVOIRS/` que l'utilisateur dépose
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
- **Unicité des noms de notes (§6)** : avant de créer une note ou un lien,
  vérifier qu'aucun nom identique n'existe ailleurs.

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

### 7.7 Cycle d'une note d'`0-EN-VRAC/`

`0-EN-VRAC/` est un **dossier tampon**, pas une destination : il ne stocke rien
durablement. Une session de rangement le traite **en entier**, et il est vide
quand elle se termine : c'est le critère d'achèvement, et ce qui y reste est ce
qui n'a pas pu être tranché — le dire. Conséquence pratique : une note
d'`0-EN-VRAC/` n'est jamais une cible de rétrolien stable, puisqu'elle aura
changé de dossier avant qu'on la relise.

La procédure — lire, vérifier qu'un doublon n'existe pas, remplir, tagger,
prévisualiser, classer, consigner au registre — vit dans le skill
`traitement-des-notes`
(`IA/skills/traitement-des-notes/traitement-des-notes.md`). Elle n'est pas
reprise ici : ce qui s'écrit à deux endroits diverge, et c'est la destination
qui décide — une **règle** violable sans avoir rien chargé reste dans ce
contrat, une **procédure** qui ne s'applique qu'en faisant la chose part dans
le skill.
