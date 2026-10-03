---
schema: 1
kind: contract
name: contrat-coffre-parent
description: Détail du coffre parent : désignation, piège du tiret, zones d'écriture et leur raison, aperçu, rétroliens, accès du harness, cycle d'-EN-VRAC.
module: noyau
---

# Annexe du contrat — coffre-parent

> **À lire avant d'écrire dans le coffre parent hors d'-EN-VRAC/.** Annexe du contrat (`../VAULT-CONTRACT.md`).
> Elle précise, elle n'ajoute aucune règle : toute règle qu'on peut enfreindre
> sans avoir rien chargé est aussi au noyau, et en cas de contradiction le
> noyau fait foi — l'annexe est alors à corriger. La correspondance avec l'ancien
> contrat est suivie dans `registre.md`, document de travail non normatif.

## 7. Le coffre parent — la base de connaissances

Le dépôt OBSIA est cloné **à la racine du coffre parent**, côte à côte avec
les dossiers de connaissance. Ce coffre parent est la base de connaissances
primordiale : il se lit, s'enrichit et s'administre — par l'utilisateur, et
par les agents qui y accèdent selon ce paragraphe. Seul `OBSIA/` est
versionné ; les autres dossiers ne le sont pas.

**Le coffre parent s'écrit `Mon coffre/` partout dans ce dépôt.** C'est une
**convention d'écriture**, pas une contrainte sur le disque : le nom réel du
dossier se lit dans `obsia.local.yml` (clé `coffre_parent`, §13), que
l'installeur remplit et qui n'est pas versionné. Le dépôt se publie et ne peut
pas connaître le nom que chacun donne à son coffre ; il lui en faut pourtant un
pour en parler, sans quoi chaque skill inventerait le sien. Voici donc comment
on le désigne :

| Ce qu'on veut dire | Comment l'écrire |
| --- | --- |
| un dossier du coffre parent | `Mon coffre/-SAVOIRS/` — jamais `../-SAVOIRS/` |
| le dépôt lui-même | `Mon coffre/OBSIA/`, ou son chemin interne (`IA/skills/…`) |
| un fichier du dépôt, depuis un autre fichier du dépôt | relatif au fichier qui cite — depuis cette annexe : `../VAULT-CONTRACT.md` |

La règle tient en une phrase : **`../` ne sert qu'à naviguer à l'intérieur du
dépôt**, jamais à désigner le coffre parent. Sans elle, le même `../` veut dire
deux choses selon la cible — relatif au fichier ici, relatif au répertoire de
travail là — et c'est ainsi qu'un skill finit par pointer à côté.

Une **commande** reste une exception assumée : lancée depuis la racine du
dépôt, elle atteint le coffre parent par `..` (`rg "motif" ../-SAVOIRS`). C'est
du shell, pas une désignation — et c'est aussi la forme qui se moque du nom
réel du dossier, ce qui la rend préférable au chemin absolu partout où elle
suffit. Un chemin absolu, lui, contient une espace et
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

Les dossiers de premier niveau s'écrivent **en majuscules**, tels qu'ils sont
sur le disque : `_MAINTENANCE/`, `-PROJETS/`… Linux distingue la casse, et un
agent qui cherche `_maintenance/` conclut à tort que le dossier manque.

| Dossier | Rôle |
| --- | --- |
| `Mon coffre/` | la racine — le coffre Obsidian lui-même, ouvert à ce niveau |
| `OBSIA/` | le dépôt, versionné — agents, skills, tâches, mémoire d'OBSIA |
| `_MAINTENANCE/` | journaux, astuces de débogage, previews consignés, registre des notes traitées |
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
`_MAINTENANCE/`, `-PROJETS/`, `-DOCUMENTS/`, `-PERSONNELS/`, `-SAVOIRS/` et
`-EN-VRAC/`. Ces dossiers se désignent par leur nom complet depuis la racine
(`Mon coffre/-SAVOIRS/`) ; dans une commande lancée depuis la racine du dépôt,
ils s'atteignent par `..`.

Le coffre parent n'est **pas** un « dépôt extérieur » au sens du §3 : ce
paragraphe vise des bases de code, pas des notes.

Lire n'est pas recopier : le coffre parent est privé, le dépôt se publie
(§13.5). Rien du coffre parent ne migre dans `OBSIA/` au fil des réponses, et
aucun secret du coffre parent n'entre dans le dépôt.

### 7.3 Écriture — zones autorisées

Le coffre parent n'étant pas versionné, il n'y a **pas de patch Git**
possible. Les écritures autorisées d'un agent `read_only: false` y sont
directes, limitées et tracées (7.4) :

- `-EN-VRAC/` — remplir une note, poser tags et rétroliens, préparer le
  classement ;
- `-SAVOIRS/` — compléter une note que l'utilisateur y a déposée (tags,
  rétroliens, corps manquant), sans en changer le sens ni la déplacer ;
- `_MAINTENANCE/` — consigner previews, actions et registre des notes
  traitées ;
- le **classement** : déplacer une note d'`-EN-VRAC/` vers sa destination
  (`-PROJETS/`, `-DOCUMENTS/`, `-PERSONNELS/`, `-SAVOIRS/`) une fois traitée ;
- `-PROJETS/<projet>/` — **le dossier d'un projet de l'utilisateur**, même
  forme que `mémoire/projets/` (§6) : `<projet> — résumé.md` (la note de
  suivi, créée et tenue par l'agent, **mise à jour sur place** : où en est le
  projet, ce qui a été décidé, ce qui reste à faire), `carnets/`,
  `documents/`, `archives/`, un seul niveau de sous-projet ;
- `-PROJETS/<projet>/code/` — **le dépôt git d'un projet construit ici** :
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
  fichier sous `-PROJETS/<projet>/code/`, puis chercher son nom dans Obsidian.
  L'unicité des noms de notes (§6) reste par conséquent
  **à surveiller** : l'exclusion allège l'index, elle ne garantit pas qu'un
  nom de note reste unique dans tout le coffre ;
- `-PERSONNELS/` — **une note de référence dont l'agent est l'auteur**, créée
  et tenue par lui, **mise à jour sur place**, et marquée `auteur: <nom-agent>`
  dans son frontmatter : l'inventaire d'une infrastructure, par exemple, qui
  décrit l'utilisateur et doit rester vivant — une machine ajoutée, une adresse
  changée. Seul l'agent nommé dans ce champ y écrit, et chaque mise à jour
  passe par le preview du 7.4 ;
- `-PROJETS/<projet>/<projet> — vision.md` — **la vision d'un projet de
  l'utilisateur** : finalité déclarée, finalités possibles validées ou
  rejetées, portes à garder ouvertes. Celle d'un projet du coffre — OBSIA
  compris — vit dans `mémoire/projets/<projet>/` et passe par PR, comme le reste de sa demande
  (§6). Seul l'agent `visionnaire` l'écrit, **sur place**, après validation
  de l'utilisateur. Un sous-projet n'a pas de vision : il relève de celle de
  son projet.

Une **note** de `-PROJETS/` que l'agent n'a pas écrite n'est pas à lui : elle reste protégée
comme le reste. Hors des dossiers de projet ci-dessus (note de suivi, vision, carnets,
`code/`) et des
notes de référence ci-dessus, une écriture dans `-PROJETS/`, `-DOCUMENTS/` ou `-PERSONNELS/` se limite au
**dépôt d'une note classée venue d'`-EN-VRAC/`**, et à rien d'autre. On n'y
modifie **jamais** une note existante, même à la demande de l'utilisateur :
une note à enrichir repasse d'abord par `-EN-VRAC/`, puis est classée. On n'y
déplace ni n'y supprime rien.

La note de suivi, la note de vision, les carnets et la note de référence sont les seules
exceptions, et elles tiennent à la même raison : **ce sont les seules notes de ces dossiers
dont l'agent est l'auteur.** Il les a créées, il les met à jour, personne
d'autre n'écrit dedans. La règle générale protège les notes de l'utilisateur
d'une réécriture silencieuse sans Git pour la rattraper ; elle ne protège de
rien quand l'agent corrige son propre texte. Ce qui rend la distinction
visible sans ouvrir la note, c'est le suffixe ` — résumé` ou ` — vision`, ou le
dossier `carnets/`, pour les premières et le champ `auteur:` pour la troisième : une note qui ne
porte rien de tout cela n'est pas à l'agent.

### 7.3.1 Où va la note d'un projet — le miroir est public

Deux endroits portent des notes de projet, et les confondre expose du privé :

| Le projet porte sur… | La note va dans… | Visibilité |
| --- | --- | --- |
| le coffre lui-même — un skill, un agent, une règle | `mémoire/projets/<projet>/` | dépôt privé, versionné, relu par PR — retiré du miroir public par `publier.py` |
| n'importe quoi d'autre — un projet de l'utilisateur | `-PROJETS/<projet>/` | privée — le coffre parent n'est pas versionné |

`mémoire/` vit dans le dépôt de travail, privé, dont le miroir public est
dérivé (§13.5). Ce qui décrit le coffre y entre, **demande et contexte
compris**, même s'ils nomment une personne ou un besoin — mais jamais une
**valeur** que le §9 interdit (adresse IP, nom d'hôte interne, URL interne,
identifiant) ; en cas de doute, le §9 l'emporte : c'est la condition pour qu'ils
passent par PR (§6). Ce qui décrit la vie de l'utilisateur n'y entre pas —
un projet personnel pas davantage qu'un secret (§7.2) —, et `publier.py`,
qui vide `mémoire/`, est un filet, pas une raison d'y verser. Un chantier
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
dont la nature est manifestement personnelle, ou pour tenir une note de
référence dont on est l'auteur (§7.3 ci-dessus), et son contenu
ne migre jamais dans `OBSIA/`, qui est public (§7.2). Un secret — mot de passe,
jeton, clé — n'a sa place ni ici ni ailleurs (§4).

### 7.4 Preview et traçabilité — `_MAINTENANCE/`

Sans Git, **le preview tient lieu de trace**. Avant toute écriture dans le
coffre parent hors d'`-EN-VRAC/` — note créée, complétée, déplacée, création du
carnet d'un projet de l'utilisateur comprise —, et avant toute action qui
touche plusieurs fichiers, l'agent :

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

Le registre des notes traitées est le fichier
**`Mon coffre/_MAINTENANCE/notes_remplies.md`** — une note Markdown, pour
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
