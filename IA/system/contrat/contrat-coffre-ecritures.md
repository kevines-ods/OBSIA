---
schema: 1
kind: contract
name: contrat-coffre-ecritures
description: Les écritures directes dans le coffre parent : zones autorisées et leurs raisons (7.3), où va une note (7.3.1), rétroliens et tags (7.5).
module: noyau
---

# Annexe du contrat — coffre-ecritures

> **À lire avant l'acte qui la convoque.** Annexe du contrat (`../VAULT-CONTRACT.md`).
> Elle précise, elle n'ajoute aucune règle : toute règle qu'on peut enfreindre
> sans avoir rien chargé est aussi au noyau, et en cas de contradiction le
> noyau fait foi — l'annexe est alors à corriger. Découpée en six annexes par
> acte (elle fut `contrat-coffre-parent.md`) : les sections ont déménagé,
> sans qu'une phrase ne soit réécrite. La correspondance avec l'ancien
> contrat est suivie dans `registre.md`, document de travail non normatif.

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
- `0-PROJETS/tâches-planifiées/` — **le registre privé des tâches planifiées**
  propres à cette installation — une machine précise du parc de l'utilisateur,
  ou son mainteneur (§12 du contrat, `contrat-taches`) : un fichier par tâche,
  créé ou corrigé sur place, jamais publié ;
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
`code/`), du registre `0-PROJETS/tâches-planifiées/` et des
notes de référence ci-dessus, une écriture dans `0-PROJETS/`, `0-DOCUMENTS/` ou `0-PERSONNELS/` se limite au
**dépôt d'une note classée venue d'`0-EN-VRAC/`**, et à rien d'autre. On n'y
modifie **jamais** une note existante, même à la demande de l'utilisateur :
une note à enrichir repasse d'abord par `0-EN-VRAC/`, puis est classée. On n'y
déplace ni n'y supprime rien.

La note de suivi, la note de vision, les carnets, le profil, les préférences,
les `expériences/` de l'agent, le registre des tâches planifiées et la note de
référence sont les seules exceptions, et elles tiennent à la même raison : **ce sont les seules notes de
ces dossiers dont l'agent est l'auteur ou le correcteur attitré.** Il les a
créées, il les met à jour, personne d'autre n'écrit dedans. La règle générale
protège les notes de l'utilisateur d'une réécriture silencieuse ; elle ne
protège de rien quand l'agent corrige son propre texte, ou un fait sur son
utilisateur. Ce qui rend la distinction visible sans ouvrir la note, c'est le
suffixe ` — résumé` ou ` — vision`, le dossier `carnets/`, un chemin sous
`0-PERSONNELS/`, le champ `auteur:`, ou un fichier à plat sous
`0-PROJETS/tâches-planifiées/` : une note qui ne porte rien de tout cela
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

