# Cadrage — Outils du coffre

Cadrage produit validé section par section le 2026-10-09 (porte 3). Il fixe **ce
que** l'outil doit faire, pas **comment** : la technique se décide à la porte
suivante. Il ne nomme donc aucune technologie et n'entre dans aucun dossier du
coffre ; le code de ce produit vit dans le dépôt produit, à côté du moteur de
règles qu'il doit appeler.

## 1. Problème

Un modèle local chargé d'écrire dans le coffre dispose aujourd'hui d'un accès
direct au système de fichiers pour écrire : rien ne l'empêche de mal placer le
contenu. Les
règles qui disent *où* et *comment* écrire (le contrat et les procédures des
skills) sont dispersées et doivent être connues de mémoire, puis appliquées
correctement du premier coup — ce que le modèle ne fait pas.

Les échecs sont **mesurés** : carnet écrit au mauvais endroit, non daté ou au
frontmatter hors contrat ; dossiers **inventés** qui n'existent pas dans le
coffre ; inventaires de destinations **inventés** ; boucles sur un refus que le
modèle n'avait pas vu venir.

La cause est double : le modèle doit **retrouver** la règle, et il doit la
**respecter** lui-même. Tant qu'une règle vit dans la tête du modèle, sa bonne
application est facultative.

## 2. Utilisateur cible

Les **modèles locaux** exécutés dans le coffre, dans le seul cadre d'une
**session d'équipe** : un agent chef d'équipe et administrateur les encadre et
lit leurs comptes rendus. Ce chef d'équipe garde son propre accès aux fichiers ;
c'est au modèle local que l'**accès direct en écriture** est retiré, pas la
lecture.

Second public, indirect mais décisif : le **chef d'équipe** qui doit pouvoir
juger ce qui a été écrit **d'un coup d'œil**, sans reconstituer les gestes du
modèle.

## 3. Solution

Un **serveur d'outils qui applique le contrat à la place du modèle**. Le modèle
n'écrit plus un fichier ; il **demande** une écriture, et l'outil la calcule, la
vérifie, puis l'exécute ou la refuse. Trois gestes couverts :

- **écrire un carnet** — l'outil calcule le chemin, la date et le frontmatter
  selon les règles du coffre, sans que le modèle ait à les connaître ;
- **classer une note** — l'outil range selon les seules destinations autorisées
  à ce modèle ;
- **vérifier une écriture avant de la faire** — zone autorisée, nom unique,
  appartenance des tags au vocabulaire contrôlé.

À côté de ces gestes d'écriture, la **lecture n'est pas verrouillée** : le
modèle local garde des outils de lecture seule, notamment pour lire une note
avant de la compléter. Seule l'**écriture** passe par le chemin unique.

Trois principes portent la solution :

1. **L'outil applique la règle ; il ne demande pas au modèle de la respecter.**
   La garantie ne dépend plus de la discipline du modèle.
2. **L'outil sert la vérité légale du coffre** — les destinations **autorisées**
   pour ce modèle et ce qui s'y trouve déjà —, jamais l'arborescence brute. Le
   modèle n'a plus à deviner qu'une zone existante lui est interdite.
3. **Une porte d'entrée pure.** Avant qu'un seul octet ne touche le disque,
   l'outil juge un **texte candidat** : zone autorisée, nom unique, appartenance
   des tags au vocabulaire contrôlé, frontmatter conforme, absence de secret.
   Chaque contrôle **réutilise l'implémentation qui existe déjà**, nommée
   contrôle par contrôle — **jamais une seconde copie de la règle là où une
   fonction pure suffit** :
   - **zone autorisée** : les règles de mémoire et de dépôt imbriqué déjà
     portées par la convention des notes du coffre parent (`est_gele`,
     `est_depot_imbrique`, `notes_du_dossier`, `point_de_depart_ecarte`) ;
   - **nom unique** : l'unicité des noms du moteur de vérification
     (`verifier_unicite_des_noms`) ;
   - **appartenance des tags** au vocabulaire contrôlé : la **table du registre
     des tags** ;
   - **frontmatter conforme** : `extraire_frontmatter` ;
   - **absence de secret** : les aides **pures** de `garde_secrets`
     (`valeur_a_forme_de_secret`, `jeton_isole`, `est_empreinte`,
     `motifs_secrets`), **enveloppées sur le texte candidat**.
   Pour le frontmatter et l'appartenance des tags, la **convention des notes du
   coffre parent sera extraite dans le moteur partagé** — fonctions **pures sur
   texte** — et le skill **`traitement-des-notes`** l'appellera : **une seule
   copie**, des deux côtés. Rien n'est écrit tant que ce jugement n'est pas
   rendu.

Le modèle ne fournit **jamais un fragment de chemin** : il propose un **sujet**,
que l'outil valide puis traduit en chemin selon les règles du coffre. Un corps
qui ouvre un **second bloc de frontmatter** ou **répète une clé** déjà posée est
refusé avant toute écriture.

L'outil est **branchable** sur les différents harnais qui accueillent les
modèles locaux, sans que la règle soit réécrite pour chacun. Il ne réinvente
aucune règle : il **appelle** le moteur de vérification du coffre, qui existe
déjà et fait foi.

## 4. User stories

- **US-1** — En tant que modèle local, je demande l'écriture d'un **carnet** ; le
  chemin, la date et le frontmatter sont calculés pour moi et l'écriture est
  conforme au coffre sans que j'aie à les connaître.
- **US-2** — Je demande l'écriture d'une **note rangée** dans une destination
  autorisée ; l'outil choisit ou valide le rangement et écrit.
- **US-3** — Je demande de **compléter ou tagger une note brute** en attente ; le
  remplissage et les tags appliqués respectent le vocabulaire contrôlé.
- **US-4** — Je demande de **compléter une note déjà classée** sans en changer le
  sens ; l'outil accepte l'ajout et refuse toute réécriture qui altérerait le
  sens.
- **US-5** — Je demande de **classer** une note en attente vers sa destination
  légale ; l'outil effectue le déplacement lié au classement et rien d'autre.
- **US-6** — Avant d'écrire, je demande **la carte légale** : les destinations
  autorisées pour moi et ce qui s'y trouve déjà, afin de ne pas inventer ni
  viser une zone interdite.
- **US-7** — Je demande une écriture **interdite** (modifier une note déjà
  rangée dans un espace protégé, renommer librement, écrire hors des
  destinations autorisées, poser une suppression) ; l'outil **refuse en
  expliquant** : il donne le motif et cite la règle du contrat concernée, sans
  faire le geste à ma place.
- **US-8** — Je propose un nom qui **existe déjà** ; l'outil refuse et me renvoie
  vers un nom conforme, plutôt que d'écraser ou de créer un doublon.
- **US-9** — Mon contenu **ressemble à un secret** ; l'outil refuse de l'écrire,
  sans le recopier ni le révéler.
- **US-10** — Avant toute écriture, l'outil me **rend l'aperçu** : le texte exact
  et le chemin qui seront posés, et il en conserve une copie datée ; personne
  n'a eu à approuver, l'aperçu est une annonce et une trace.
- **US-11** — À chaque écriture réussie, l'action est **consignée dans
  l'historique du dépôt de données**, de sorte qu'elle soit contrôlable et
  réversible.
- **US-12** — Le chef d'équipe lit le **compte rendu** de chaque demande (chemin,
  trace, refus) **d'un coup d'œil**, sans reconstituer les gestes du modèle.
- **US-13** — Je propose un **sujet**, jamais un fragment de chemin ; l'outil le
  valide et calcule la destination. Un sujet qui ne produit pas un nom unique
  dans une zone autorisée est refusé et corrigé.
- **US-14** — Mon corps de note ouvre un **second bloc de frontmatter** ou
  **répète une clé** déjà posée ; l'outil refuse sans avoir écrit.
- **US-15** — Un refus du moteur m'est **traduit en geste** : la voie correcte est
  nommée, avec la règle du contrat qui la fonde — je ne repars pas sur un renvoi
  brut ni une boucle.
- **US-16** — Quand je **classe** une note, la mise à jour du **registre des notes
  traitées** part dans le **même commit** que le classement : registre et
  rangement ne divergent pas.
- **US-17** — Mon écriture porte une **marque d'auteur** distincte de celle d'un
  agent chef d'équipe, lisible dans l'historique du dépôt de données.

## 5. Critères de succès

1. **Aucun dossier inventé** : toute destination produite par l'outil appartient
   au coffre et à une zone autorisée à ce modèle.
2. **Aucun carnet hors zone, non daté ou au frontmatter hors contrat** : la
   conformité ne dépend plus du modèle.
3. **Aucune écriture sans contrôle préalable** : zone, unicité du nom,
   appartenance des tags au vocabulaire, absence de secret sont vérifiés avant
   que le disque soit touché.
4. **Tout refus est guidé** : il porte un motif et **cite la règle concernée** du
   contrat, jamais un renvoi hors sujet.
5. **Chaque écriture laisse une trace** dans l'historique du dépôt de données,
   identifiable et réversible.
6. **Le compte rendu est lisible d'un coup d'œil** par le chef d'équipe.
7. **Un outil indisponible ne se contourne pas** : sans lui, le modèle **s'arrête
   et le dit** ; il ne retombe jamais sur une écriture directe du coffre.
8. **Aucun chemin ne vient du modèle** : tout chemin écrit est calculé par
   l'outil à partir d'un **sujet** ; un fragment de chemin est refusé.
9. **La consignation ne diverge pas du geste** : le registre des notes traitées
   et un classement voyagent dans le **même commit**.
10. **Aucune écriture n'en double une autre** : les écritures passent **en série**,
    et un second écrivain est **détecté et signalé**, jamais écrasé.

## 6. Hors périmètre

- **Aucune suppression** : les outils n'exposent pas de geste destructeur.
- **Aucun écrasement** : une écriture ne remplace jamais un contenu existant ;
  elle complète ou refuse.
- **Aucun geste réservé au chef d'équipe** : modifier une note déjà rangée dans
  un espace protégé, renommer, ou tout ce qui sort des destinations autorisées
  reste de son ressort — l'outil le refuse et le dit.
- **Aucune règle nouvelle** : l'outil applique le contrat, il ne l'étend ni ne
  l'assouplit.
- **Aucun secret écrit** : le contenu qui en est un est refusé, jamais recopié.
- **Aucun verrouillage de la lecture** : seule l'écriture passe par les outils ;
  la lecture reste ouverte au modèle local, y compris pour lire une note avant
  de la compléter.
- **Aucun jugement de qualité ni de rédaction** : l'outil contrôle la conformité,
  pas le fond.
- **Aucune décision technique** : langage, cadriciel, emplacement d'exécution et
  forme de la traçabilité sont renvoyés à la porte suivante.

## 7. Décisions produit

**§7.1 — Le niveau de garantie : seul l'écriture est verrouillée.** Les
nouveaux outils sont le **seul** chemin d'**écriture** des modèles locaux ;
l'accès direct en écriture leur est retiré. La **lecture reste ouverte** : le
modèle local garde des outils de lecture seule et lit librement, notamment pour
lire une note avant de la compléter. Le chef d'équipe **garde** son propre
accès. C'est le seul réglage où un carnet mal placé ou un dossier inventé
deviennent impossibles.

**§7.2 — Le périmètre : créer et modifier, sans destruction.** L'outil couvre la
création **et** la modification d'une note existante, dans les limites des zones
d'écriture : compléter ou tagger une note en attente ; compléter une note déjà
classée **sans en changer le sens** ; tenir carnets et résumé de chantier ;
déplacer **uniquement pour classer** depuis la zone d'attente. Il **refuse** de
modifier une note déjà rangée dans un espace protégé et **refuse tout renommage
libre**. L'aperçu tient, l'absence de suppression tient.

**§7.3 — Ce que le modèle voit : la carte légale.** L'outil sert les seules
destinations **autorisées** pour ce modèle et ce qui s'y trouve déjà. « Existe »
n'est pas « permis », et une arborescence brute ne le dit pas : c'est
exactement ce qui produit les dossiers inventés. Le modèle n'invente plus, il
choisit dans une liste fermée.

**§7.4 — Quand l'outil refuse : refus guidé.** Un refus porte le motif **et** la
voie correcte prévue par le contrat, **citée par la règle concernée** selon le
cas. Le refus est **traduit en geste** pour le modèle : la prochaine action est
nommée, jamais un renvoi brut. L'outil **nomme** la voie correcte ; il **ne fait
jamais** le geste à la place du modèle. Un refus sec ferait boucler un modèle
faible sur le même appel.

**§7.5 — Quand l'outil écrit : un seul appel.** L'aperçu est une **annonce et une
trace**, pas une approbation : l'outil renvoie le texte exact et le chemin,
conserve la copie datée, puis consigne l'action — en un seul appel. Un second
appel de confirmation n'ajoute aucune garantie externe (c'est le même modèle qui
proposerait puis confirmerait) et nourrit la boucle. Les vrais garde-fous
restent : contrôles mécaniques avant écriture, jamais d'écrasement, aucune
suppression. **Un commit du dépôt de données par écriture** : l'historique du
dépôt rend chaque écriture contrôlable et réversible. Cette lecture de l'aperçu
est **couverte par le §7.4 du contrat du coffre**, patché pour ce cas (aperçu
rendu avec l'écriture, annonce et trace, sous **condition d'annulabilité**) ;
elle sera portée à la fiche de l'outil, pour relecture.

**§7.6 — Le contexte d'usage.** Le modèle local ne travaille qu'en **session
d'équipe**, sous un chef d'équipe/administrateur qui voit ses comptes rendus. Le
compte rendu de l'outil (chemin, trace, refus) doit se lire **d'un coup d'œil**.

**§7.7 — Un seul écrivain du dépôt de données.** Les écritures du dépôt de
données ne partent que d'**une seule machine**, celle qui héberge les agents et
qui versionne la mémoire : le serveur d'outils y vit, ou délègue l'écriture à ce
qui y tourne. Le point précis — **où tourne l'outil** — se tranche à la porte
suivante ; il n'est pas décidé ici.

**§7.8 — Traçabilité de l'auteur.** Une écriture produite par le modèle local
(carnet ou note) porte une **marque distincte** de celle d'un agent chef
d'équipe, pour qu'on sache **qui a écrit quoi** sans confondre les deux. La
forme exacte se décide au cadrage technique ; **si elle touche le frontmatter
défini par le contrat — le champ `agent:`, qui sert à la reprise d'un chantier —
c'est un correctif de contrat probable, à signaler et à traiter comme tel, pas à
improviser.**

## 8. Notes

- **Rapport au moteur existant** : l'outil **appelle** le moteur de vérification
  du coffre ; il ne le réécrit ni ne le duplique. C'est la raison du choix du
  dépôt d'accueil.
- **Dépendance au retrait de l'accès direct en écriture** : toute la garantie
  repose sur le fait que les modèles locaux n'ont plus d'autre chemin
  **d'écriture**. Sans ce retrait, l'outil redevient facultatif, donc
  contournable. La lecture, elle, reste ouverte. Le plan le **constate harnais
  par harnais** : le modèle local n'a **plus aucun outil d'écriture** — ni celui
  **fourni par défaut**, ni un **MCP de fichiers du coffre** — c'est un
  **critère vérifiable**, pas une intention.
- **Risque — outil indisponible** : sans accès direct en écriture ni outil, le
  modèle n'a aucun chemin d'écriture ; il **s'arrête et le dit**, jamais de repli
  (il garde la lecture). À vérifier au plan.
- **À trancher à la porte suivante** : où tourne l'outil (l'unique écrivain du
  dépôt de données, §7.7) ; la forme exacte de la traçabilité de l'auteur
  (§7.8), et le correctif de contrat qu'elle entraînerait le cas échéant.
- **Règles du contrat mobilisées** : écriture et absence de suppression,
  secrets, frontmatter, nommage et unicité, zones d'écriture, aperçu, vocabulaire
  des tags, cycle de la zone d'attente, portée hors coffre.
- **Le coffre est synchronisé entre les machines**, hors son historique de
  version (le dossier `.git`) : la **fenêtre entre l'écriture et son commit est
  donc visible des autres machines**. L'outil la **réduit** — il écrit puis
  committe dans le **même verrou, sans attente**. Un **commit concurrent** venu
  d'ailleurs ne se devine pas au `git status` : l'outil **relève `HEAD` et
  l'empreinte du fichier qu'il a lu**, les **revérifie juste avant le commit**,
  et **refuse** — ou **relit et recalcule** — si l'un des deux a bougé.
- **Contre la course entre écrivains** : les écritures passent **en série** sous
  un verrou ; un commit ne porte **que les fichiers de l'acte**, jamais l'ensemble
  de ce qui traîne dans le dépôt. Avant de committer, l'outil **lit `git status`**,
  ce qui révèle une **écriture directe non commitée** ayant **contourné** la
  porte ; le **commit concurrent**, lui, se prend à la **revérification de `HEAD`
  et de l'empreinte du fichier lu**. Deux écrivains sont **détectés et signalés**,
  jamais arbitrés en silence.
- **Mort du processus — reprise nette.** Si le serveur meurt entre l'écriture et
  son commit, la **reprise défait (ou achève) tout reste d'acte non commité** et
  le **signale** : jamais un fichier orphelin laissé derrière. Autant que
  possible, le serveur **ne se suspend pas à la session** — sa durée de vie ne
  décide pas de celle de l'écriture en cours.
- **Résidu de concurrence — le commit étranger** : un `git commit -a` ou un
  `git add -A` lancé par **n'importe qui** dans le dépôt de données pendant la
  fenêtre emporte les fichiers de l'acte dans un **commit étranger**. L'outil le
  **détecte** — les fichiers de l'acte n'apparaissent pas dans son propre commit —
  et le **consigne** ; en **remise en état**, c'est le **chef d'équipe** qui
  **défait ce commit étranger**. Pour tarir la cause, il est **recommandé** — à
  **proposer**, pas à appliquer ici — que **tout agent committe le dépôt de
  données par chemins** (`git commit -- <chemins>`, jamais `-a`), et que le
  **contrat** et le skill **`cloture-de-session`** le portent.
- **Si le commit est refusé** (crochet du dépôt) : l'outil **défait sa propre
  écriture** et le **dit** — il ne laisse pas derrière lui un fichier non
  consigné.
- **Conditions de cap (contrôle du Visionnaire, 2026-10-09)** : l'outil reste
  **facultatif** — le coffre s'installe, se lit et se modifie sans lui, et
  l'outil ne crée **aucun état hors du coffre** ; il entre comme **module
  retirable** ; **aucun nom de harness ni d'adaptateur** n'entre dans le moteur
  de règles partagé ; le compte rendu « pour le chef » **ne devient pas** un
  format d'équipe déclaré dans la base.
