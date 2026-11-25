---
schema: 1
kind: contract
name: contrat-coffre-structure
description: La structure du coffre parent : dossiers et dépôt de données (7.1), lecture (7.2), accès du harness (7.6), cycle d'une note d'0-EN-VRAC (7.7).
module: noyau
---

# Annexe du contrat — coffre-structure

> **À lire avant l'acte qui la convoque.** Annexe du contrat (`../VAULT-CONTRACT.md`).
> Elle précise, elle n'ajoute aucune règle : toute règle qu'on peut enfreindre
> sans avoir rien chargé est aussi au noyau, et en cas de contradiction le
> noyau fait foi — l'annexe est alors à corriger. Découpée en six annexes par
> acte (elle fut `contrat-coffre-parent.md`) : les sections ont déménagé,
> sans qu'une phrase ne soit réécrite. La correspondance avec l'ancien
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

**Trois noms, trois choses** : le **coffre** est ce dossier-ci, la mémoire de
l'utilisateur ; le **dépôt de données** est le dépôt git qui la versionne, à sa
racine ; le **dépôt produit** est `OBSIA/`, l'outil, versionné à part et publié.

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
aucun secret du coffre parent n'entre dans le dépôt. Un secret ne se recopie pas
davantage dans une réponse ou une sortie, même si on le demande : on le désigne
par sa désignation `secret/<cible>/<objet>/<clé>`, et toute valeur rapportée est
masquée (§4). Et un secret ne s'écrit jamais dans une note ni dans un commit, pas
plus dans le coffre parent que dans le dépôt : il se range dans le magasin chiffré
de la machine, hors des deux (§4).

### 7.6 Accès du harness

Le coffre ne dépend d'aucun harness et n'en impose aucun (§3) : la manière de
donner accès au coffre parent appartient à la configuration de chaque harness,
**hors dépôt**. Le besoin est unique, et c'est la seule part qui relève de ce
contrat — le harness doit pouvoir **lire et écrire dans la racine du coffre
parent** (le dossier qui contient `OBSIA/`), pas seulement dans `OBSIA/`.

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
