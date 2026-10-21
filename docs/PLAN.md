# Plan — les outils du coffre pour les modèles locaux

> Cadrage source : docs/CADRAGE.md

Un outil **facultatif** que les modèles locaux appellent pour **écrire dans le
coffre sans en connaître les règles** : ils proposent un **geste** — un carnet,
une note à ranger, une note à compléter —, l'outil **vérifie** le texte candidat
**avant toute écriture**, puis **écrit et committe en un acte**.

Le plan le livre par **tranches verticales** : chacune traverse **toutes les
couches**, de la demande du modèle à l'écriture commitée, et **se démontre
seule**. On construit **une tranche à la fois** ; on ne commence pas la suivante
avant que les critères de la précédente passent.

Avant la première tranche, deux actes d'hygiène : **poser le plancher de qualité**
(chiffré — les critères d'une tranche disent si on a construit la bonne chose, le
plancher dit si c'est assez bon) et **poser le squelette du dépôt**. Aucun code
n'existe encore.

## Décisions structurantes

Elles ne changent pas en cours de route sans revenir au cadrage ; les précisions
techniques vivent dans `docs/STACK.md` et n'ont pas à revenir ici.

- **Forme de l'outil** : un serveur local, module du dépôt produit, sans
  dépendance hors bibliothèque standard ; il ne crée **aucun état hors du coffre**
  et se **retire** sans rien casser d'autre.
- **Rapport au moteur** : l'outil **appelle le moteur de règles**, il ne le
  duplique pas ; **aucun nom de harnais ni d'adaptateur** n'entre dans le moteur
  partagé.
- **Écrivain** : **un seul** ; toutes les écritures du dépôt de données partent
  d'une seule machine.
- **Forme de l'écriture** : sur la **branche par défaut du dépôt de données**, en
  **un acte = un commit** ne portant **que les fichiers de l'acte**, reconnaissable
  à une **marque dans son message**, et **annulable**.
- **Aperçu** : rendu **avec l'écriture** (annonce et trace, sous **condition
  d'annulabilité**) ; le modèle **ne fournit jamais de chemin** — il propose un
  sujet, l'outil le traduit.
- **Repli** : l'outil reste **facultatif** ; sans lui, le modèle **s'arrête et le
  dit**, jamais d'écriture directe.
- **Coffre de travail** : les phases **3 à 5** ne s'exercent que sur le **coffre de
  test** ; l'outil ne touche le **coffre réel** qu'à partir de la **phase 6**, une
  fois l'accès direct des modèles retiré et constaté.

---

## Phase 1 — Une seule copie de la convention des notes

**User stories** : aucune livrée seule ; prépare le contrôle du frontmatter et des
tags (US-3 et suivantes).

### Ce qu'on livre

La convention des notes du coffre parent — frontmatter, vocabulaire des tags,
règles de mémoire et de dépôt imbriqué — vit en **un seul exemplaire** dans le
moteur partagé, en **fonctions pures sur texte** ; le skill qui traite les notes
**l'appelle**. Les **doubles existants** sont **ramassés**, y compris **deux
lectures de frontmatter qui divergent** et des **règles de zone écrites en
double**.

### Critères d'acceptation

- [ ] il ne reste **qu'une définition** par règle partagée — aucun double ;
- [ ] la lecture de frontmatter retenue est celle qui rend **aussi la position du
      corps** — nécessaire pour réécrire et pour détecter un **second bloc** —
      **enrichie** de ce que l'autre faisait de mieux (le nettoyage des guillemets
      des listes) ;
- [ ] le comportement actuel du coffre est **figé par des caractérisations
      avant** l'extraction, et **inchangé après** : le skill produit le **même**
      résultat ;
- [ ] le moteur partagé et le skill restent **sans dépendance** hors bibliothèque
      standard.

### Bloquée par

Aucune — démarrable immédiatement.

## Phase 2 — La porte d'entrée pure et la carte légale

**User stories** : US-6, US-7, US-8, US-9, US-13, US-14, US-15.

### Ce qu'on livre

Le serveur **juge un texte candidat avant tout disque** — zone, unicité,
appartenance des tags, frontmatter, secrets — en appelant le moteur partagé ; il
refuse un corps qui ouvre un **second bloc de frontmatter** ou **répète une clé** ;
il **traduit seul** un sujet validé en chemin ; il rend, à la demande, **les zones
d'accueil autorisées** pour ce modèle et ce qui s'y trouve.

### Critères d'acceptation

- [ ] un texte conforme passe ; un texte fautif est **refusé sans qu'un octet
      touche le disque** — vérifiable ;
- [ ] un refus **nomme la règle**, **cite le contrôle** et dit **le geste
      suivant**, jamais un renvoi brut ;
- [ ] **aucun chemin** ne vient du modèle : un fragment de chemin, ou un chemin
      inventé, est refusé ;
- [ ] la carte légale ne montre que les zones **autorisées** pour ce modèle.

### Bloquée par

Phase 1.

## Phase 3 — Écrire un carnet, de bout en bout

**User stories** : US-1, US-10, US-11, US-12, US-17.

### Ce qu'on livre

Le modèle demande un carnet par son **sujet** ; l'outil calcule seul le **chemin,
la date et le frontmatter**, **rend l'aperçu** — texte exact, chemin, **copie
datée** — **avec l'écriture**, écrit, puis **committe l'acte** sur la branche par
défaut du dépôt de données, **marque** comprise.

La porte y gagne le contrôle de **mémoire gelée** : viser un chantier clos de la
mémoire du coffre est **refusé**. P2 n'en a ramassé que la règle dans le moteur —
c'est ici qu'elle entre dans la porte.

**Coffre de travail** : le **coffre de test** seulement — jamais le coffre réel
avant la phase 6.

### Critères d'acceptation

- [x] la porte **refuse toute zone hors de la matrice du §7.3**, même fournie par
      l'appelant : le §7.3 est une matrice **zone × auteur × nature d'écriture** ;
      P3 étend le port d'un champ **`auteur`** (agent déclaré) et encode la
      matrice dans le **moteur partagé** comme exécution du contrat — les noms du
      §7.1/§7.3 sont des noms du **contrat**, pas d'un harnais ni d'un coffre
      particulier. La matrice : `0-EN-VRAC/` + son classement ;
      `0-PROJETS/<projet>/` carnets · documents · résumé ; ` — vision` **réservé
      au visionnaire** ; `0-SAVOIRS/` compléter sans changer le sens ;
      `0-DOCUMENTS/` et `0-PERSONNELS/` **dépôt d'une note classée seulement** ;
      `profil-utilisateur` ; `préférences` ; `0-MEMOIRES/<agent>/expériences/` au
      **seul agent nommé**. `_MAINTENANCE/` est **ouvert à tous** : c'est la
      maintenance du coffre — aperçus et actions du §7.4, registre
      `notes_remplies.md` ; **tout autre dossier est refusé**, et une mémoire
      **gelée** aussi. P2 jugeait la **forme** d'une zone sans trancher
      l'appartenance ; P3 tranche l'appartenance dans la porte
      (`serveur/carte_legale.py`, `serveur/porte_entree.py`) — **tenu**, PR #149
      fusionnée ;
- [x] une écriture visant une **mémoire gelée** du coffre est **refusée** par la
      porte, la règle venant du moteur partagé — **tenu**, PR #149 fusionnée ;
- [x] un carnet demandé par sujet produit un chemin, une date et un frontmatter
      **conformes**, sans que le modèle les ait connus — **tenu**, PR #151
      fusionnée ;
- [x] l'aperçu **exact** est rendu **avec** l'écriture et **conservé** en copie
      datée — **tenu**, PR #151 fusionnée ;
- [x] l'acte forme **un seul commit**, ne portant **que ses fichiers**, et reste
      **annulable** — **tenu**, PR #151 fusionnée ;
- [x] un refus du crochet fait **défaire l'écriture** et le **dit** — **tenu**,
      PR #151 fusionnée ;
- [x] la **trace** de la demande — chemin, aperçu, refus — se lit **d'un coup
      d'œil** — **tenu**, PR #151 fusionnée ;
- [x] la **marque d'auteur** du commit distingue l'outil d'un agent chef d'équipe
      — **tenu**, PR #151 fusionnée.

### Bloquée par

Phase 2.

## Phase 4 — Ranger et compléter une note

**User stories** : US-2, US-3, US-4, US-5, US-16.

### Ce qu'on livre

Le modèle demande de **ranger** une note en attente vers sa destination légale, ou
de **compléter** une note — brute (remplir, tagger) ou **déjà rangée, sans en
changer le sens** ; le **registre des notes traitées** est mis à jour **dans le
même commit** que le rangement.

**Coffre de travail** : le **coffre de test** seulement — jamais le coffre réel
avant la phase 6.

### Critères d'acceptation

- [x] ranger **déplace** la note vers une zone autorisée et **ne fait rien
      d'autre**, sans écraser une note existante — **tenu**, PR #153
      fusionnée ;
- [x] compléter **ne réécrit pas le sens** : une note déjà rangée se complète
      **sur place** — **tenu**, PR #153 fusionnée ;
- [x] le registre des notes traitées et le rangement voyagent **dans le même
      commit** — **tenu**, PR #153 fusionnée ;
- [x] chaque geste reste **annulable** comme à la Phase 3 — **tenu**, PR #153
      fusionnée.

### Bloquée par

Phase 3.

## Phase 5 — La sûreté sous concurrence et sous panne

**User stories** : aucune nouvelle ; porte la **condition d'annulabilité** de
l'aperçu rendu avec l'écriture, et les critères de succès **5** et **10**.

### Ce qu'on livre

Les écritures passent **en série** sous un **verrou** ; un **commit concurrent**
est pris juste avant le commit par la **revérification de la position de tête et
de l'empreinte du fichier lu** — refus, ou relecture et recalcul ; une **écriture
directe non commitée** qui a contourné la porte est vue ; un **commit étranger**
qui a emporté les fichiers de l'acte est détecté et consigné ; après une **mort du
processus**, la reprise **constate et lève un verrou périmé**, et le **reste d'acte
laissé par l'écrivain mort reste tel quel** — jamais défait ni achevé au hasard — que
l'**acte suivant remonte à l'agent**, à charge pour lui de le consigner à son carnet.

Elle corrige aussi une omission du plan, exigée par la note `— vision` : la
**tenue au fil de l'eau d'un carnet existant** — une étape s'ajoute à un carnet
en cours **sans le réécrire**. La complétion, jusqu'ici bornée aux notes brutes et
à `0-SAVOIRS/`, s'ouvre au carnet ; elle est livrée ici parce qu'elle touche le
même geste que la sûreté d'écriture.

**Coffre de travail** : le **coffre de test** seulement — jamais le coffre réel
avant la phase 6.

### Critères d'acceptation

- [x] deux écritures concurrentes **ne se mélangent pas** : chacune forme son
      commit — **tenu**, PR #155 fusionnée ;
- [x] un commit concurrent provoque **refus ou recalcul**, jamais un écrasement
      silencieux — **tenu**, PR #155 fusionnée ;
- [x] un **commit étranger** est détecté et consigné, jamais attribué à l'acte —
      **tenu**, PR #155 fusionnée ;
- [x] un **verrou périmé** est constaté et levé à la reprise ; un reste d'acte laissé
      par un écrivain **mort** est **laissé tel quel**, jamais défait ni achevé au
      hasard, et l'**acte suivant le remonte à l'agent**, qui le consigne au carnet —
      distinct du commit refusé d'un écrivain **vivant**, qui défait son écriture
      comme le veut le §7.4 — **tenu**, PR #155 fusionnée ;
- [x] un **second écrivain** est détecté et signalé, jamais écrasé —
      **tenu**, PR #155 fusionnée ;
- [x] la complétion **tient un carnet existant au fil de l'eau** : une étape s'y
      ajoute, **sans réécrire** le carnet — **tenu**, PR #155 fusionnée.

### Bloquée par

Phase 4.

## Phase 6 — Brancher sur les harnais, retirer l'accès direct

**User stories** : aucune nouvelle ; elle rend effectives US-1 à US-17 en retirant
le chemin direct, et porte le critère de succès **7**.

### Ce qu'on livre

**Avant tout usage sur un coffre réel**, l'écrivain est **déclaré comme MCP** dans
`IA/MCP/` — une fiche qui dit qu'il écrit *pour un harnais pilotant un modèle
local* : c'est la **condition d'entrée** de l'exception bornée du §7.4, et sans
elle le chemin d'écriture outillé n'a pas à exister.

Le serveur est déclaré et **joignable depuis chaque harnais visé** ; un harnais
**déporté** l'appelle **par une clé dédiée en commande forcée** ; l'**écriture
directe du modèle local est retirée partout** et **constatée harnais par
harnais**.

### Critères d'acceptation

- [x] l'écrivain est **déclaré comme MCP** dans `IA/MCP/`, fiche disant qu'il écrit
      *pour un harnais pilotant un modèle local* — **condition d'entrée** du §7.4,
      posée **avant** tout usage sur le coffre réel — **tenu**, PR #166 fusionnée ;
- [x] pour **chaque harnais**, un **constat écrit** que le modèle local n'a **plus
      aucun outil d'écriture** — ni celui **fourni par défaut**, ni un **accès
      fichiers au coffre** — **tenu** pour `opencode`, PR #167 fusionnée (`codex`
      hors périmètre : non installé) ;
- [x] l'appel déporté passe par une **clé dédiée à ce seul appel**, en **commande
      forcée**, **jamais une clé de connexion** ; hors de cet appel, la clé ne
      permet **rien** — **tenu**, PR #169 fusionnée ;
- [x] la **permission** du harnais est vérifiée, fiche à l'appui — **tenu**,
      PR #169 fusionnée ;
- [x] sans l'outil, **aucune écriture n'a lieu** (disque + `git`) et **toute
      annonce d'écriture du modèle est démentie par un constat indépendant** —
      critère **reformulé** (décision utilisateur du 2026-10-11) : la **parole**
      du petit modèle n'est pas fiable — six annonces de succès sur onze tirages
      libres, jamais une écriture — et aucune consigne ne l'en empêche (liste
      factuelle de ses capacités : 1 mensonge sur 3 ; règle de sincérité seule :
      3 sur 3 ; outils visibles mais refusés : 2 sur 3). Le §8 du contrat sépare
      l'**évidence** de la **synthèse produite par un agent**, et le §7.4 prend
      l'acte — un commit — pour trace : **la parole du modèle ne prouve rien**.
      `scripts/constat_acte.py` ne conclut donc que sur l'**état du coffre** —
      `git rev-parse`, `git status`, relevé **avant/après** ; le repérage lexical
      des annonces ne fait que **nommer** la phrase confrontée, jamais décider,
      et quand la preuve manque (coffre hors de `git`, relevé avant absent,
      journal tronqué) il rend `À CONTRÔLER` plutôt qu'une accusation — **tenu**,
      PR #171 ; **corrigé et reprouvé** par la PR corrective #177 ;
- [x] le serveur reste **retirable** sans rien casser d'autre — **tenu**,
      PR #168 fusionnée.

### Bloquée par

Phase 5.

## Phase 7 — La mesure finale

**User stories** : la vérification de **toutes**, sur le cas réel.

### Ce qu'on livre

La **batterie de neuf énoncés** qui a mesuré les échecs de placement est
**rejouée** sur un **gabarit de coffre de test reconstruit pour l'occasion**.

### Critères d'acceptation

- [ ] chaque énoncé échoue ou réussit de façon **lisible** : un placement refusé
      est **expliqué et guidé**, un placement admis est **conforme** — zone, nom,
      date, frontmatter, tags, **aucun secret** ;
- [ ] **aucun** énoncé ne laisse derrière lui un dossier inventé, une note mal
      placée, un carnet sans date ou un frontmatter fautif ;
- [ ] la batterie se **rejoue sans intervention manuelle** et son résultat est
      **écrit**.

### Bloquée par

Phase 6.

---

## Ce que ce plan ne fait pas

- Il ne touche **pas** aux modèles locaux (entraînement, réglage) : hors périmètre
  du cadrage.
- Il ne remplace **pas** l'écriture par l'agent : l'outil reste **facultatif**.
- Il ne livre **aucune interface** : rien de visuel.
- Il n'**étend ni n'assouplit** aucune règle du contrat : l'outil applique, il ne
  décide pas.
