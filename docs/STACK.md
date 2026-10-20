# Stack — Outils du coffre

Décision prise **une fois**, à la porte 4, après le cadrage. Elle ne se rejoue pas
à chaque tranche.

## Critères retenus et leur poids

Écrits **avant** de regarder les candidats, pondérés selon le profil de
l'utilisateur (open source, rapport au code modeste, infrastructure existante).

| Critère | Poids | La question à laquelle il répond |
| --- | --- | --- |
| **Licence** | fort | est-ce du logiciel libre, sous une licence connue ? |
| **Infrastructure** | fort | est-ce que ça tourne sur ce qui existe déjà, sans ajouter une brique ? |
| **Dépendances** | fort | combien de paquets tiers, et tenus par qui ? |
| **Entretien** | moyen | qui met à jour, et que se passe-t-il si personne ne le fait pendant six mois ? |
| **Reprise en main** | moyen | l'utilisateur peut-il lire et modifier ce code sans l'agent ? |
| **Sortie de secours** | moyen | si ce choix déçoit, que coûte le changement ? |

Deux contraintes pèsent **plus qu'un critère** :

1. **Appeler le moteur de règles, ne pas le dupliquer** *(héritée du cadrage)*.
   L'outil vérifie une écriture en s'appuyant sur le moteur de vérification qui
   existe déjà ; le cadrage interdit de le réécrire. Ce moteur est en Python. La
   **convention des notes du coffre parent** — frontmatter et vocabulaire des
   tags — en fait partie : elle **sera extraite du script du skill
   `traitement-des-notes` vers le moteur partagé**, en **fonctions pures sur
   texte**, et **les deux l'appelleront** — **une seule copie**.
2. **Bibliothèque standard seule** *(choix, pour ne rien installer)*. Un serveur
   qui n'installe **rien** sur la machine des agents est plus simple à poser, à
   suivre et à reprendre : une seule chaîne d'outils, celle du moteur de règles,
   déjà comprise et testée. Le seul serveur MCP déjà présent dans le dépôt suit
   déjà cette voie — écrit à la main, en `stdio`, sans dépendance
   (`IA/MCP/modele-local.md`, `IA/skills/delegation-locale/`).

## Candidats confrontés

| Critère | **A. Python, bibliothèque standard seule** | **B. Python + SDK `mcp`** | **C. Node/TypeScript** |
| --- | --- | --- | --- |
| **Licence** | libre (Python, PSF) ; aucune dépendance tierce à suivre | libre (SDK sous MIT) | libre, mais deux licences de chaîne d'outils à suivre |
| **Infrastructure** | tourne là où le moteur, le coffre et l'agent sont déjà ; rien à installer | il faut installer le SDK (`pip`/`uv`) sur la machine | nouvelle brique : Node, absent aujourd'hui de la machine |
| **Dépendances** | **aucune** hors bibliothèque standard | une dépendance tierce, plus ses propres dépendances | Node, npm, le SDK et sa chaîne |
| **Entretien** | même chaîne d'outils que le dépôt, déjà comprise et testée | une version de SDK à suivre en plus | deuxième chaîne d'outils à suivre |
| **Reprise en main** | code lisible, sans magie ; même langage que le reste du dépôt | la logique du protocole sort du code vers le SDK | langage que l'utilisateur ne connaît pas |
| **Sortie de secours** | on retire le module, rien d'autre ne bouge | retirer le SDK n'affecte que l'outil | deux écosystèmes à défaire, pas un |

Deux points décisifs, hors tableau :

- **C (Node/TypeScript)** devrait **appeler le moteur Python** : soit par un
  sous-processus dont il faut parser la sortie (fragile), soit en
  **réimplémentant** les règles — ce que le cadrage **interdit**. Le SDK MCP y
  est le plus mûr, mais cela ne compense pas une duplication interdite.
- **B (avec le SDK)** règle le protocole clés en main, mais introduit un **paquet
  à installer** sur la machine des agents et une **seconde chaîne d'outils à
  suivre** — précisément ce qu'on cherche à ne pas ajouter.

## Décision

**Python 3, bibliothèque standard seule**, livré comme **module du dépôt
produit**, exécuté **sur la machine des agents** — celle qui porte le coffre, le
moteur de règles et le dépôt de données, donc **le seul écrivain** (cadrage
§7.1).

La raison principale, en une phrase : le moteur de règles qui fait autorité est
en Python et le cadrage interdit de le dupliquer, donc rester en Python et
s'appuyer sur la bibliothèque standard est le **seul** chemin qui appelle le
moteur **sans pont** et **sans rien installer** sur la machine qui l'exécute.

Précisions qui font partie de la décision :

- **Transport : `stdio` uniquement.** Le serveur n'ouvre **aucun port**, ne sert
  **aucun service HTTP**, ne porte **aucun jeton** : le harnais qui tourne sur la
  machine des agents le lance en direct, comme le serveur déjà dans le dépôt. Un
  harnais **déporté** sur le poste GPU **lance le même serveur à distance par
  SSH** et parle à sa sortie standard. La garantie ne tient **pas à la
  discipline**, mais à la **clé** : l'appel déporté se fait avec une **clé SSH
  dédiée à ce seul appel**, en **commande forcée** — `command="…"`, `restrict`,
  `no-pty`, `no-agent-forwarding` — **jamais une clé de connexion**. Par cette
  clé, il n'existe **ni coquille, ni redirection d'agent, ni terminal** : le seul
  geste possible est cet appel.
- **Une écriture, une séquence.** Contrôler (porte d'entrée pure) → écrire →
  `git add -- <chemin>` → `git commit --only -- <chemin>` ; **jamais
  `git commit -a`**. Le **message du commit porte la marque** de l'acte (§7.4) :
  c'est à cette marque qu'un commit est reconnu. Un **verrou** met les écritures
  **en série** ; il vit **dans le dossier `.git/` du dépôt de données** — ignoré
  de git par construction, **jamais** dans `git status`, et **machine-local** (le
  dossier `.git` est exclu de la synchronisation du coffre) — sinon il se ferait
  passer lui-même pour une écriture en attente. Avant de committer, l'outil
  **lit `git status`** — une écriture directe non commitée se voit là — et
  **revérifie `HEAD` et l'empreinte du fichier qu'il a lu** — un commit concurrent
  se voit là ; si l'un a bougé, il **refuse**, ou **relit et recalcule**. Si le
  **crochet** du dépôt refuse le commit, l'outil **défait sa propre écriture** et
  le dit.
- **Un seul écrivain (§7.7).** Les écritures ne partent que d'**une seule
  machine** ; un second écrivain est **détecté et signalé**, jamais écrasé.
- **Le coffre est synchronisé entre machines** (seul `**/.git` en est exclu) : la
  fenêtre entre l'écriture et son commit est donc **visible des autres machines**.
  L'outil la **réduit** — écrire puis committer dans le **même verrou, sans
  attente** — et **détecte un commit concurrent** en **revérifiant `HEAD` et
  l'empreinte du fichier lu** juste avant de poser le sien ; au moindre mouvement,
  il **refuse** ou **relit et recalcule**. **Mort du processus** : à la reprise,
  tout **reste d'acte non commité** est **défait (ou achevé)** et **signalé** ;
  autant que possible, le **serveur ne se suspend pas à la session**.
- **Retrait de l'accès direct, constaté.** Le plan **constate harnais par
  harnais** que le modèle local n'a **plus aucun outil d'écriture** — ni celui
  **fourni par défaut**, ni un **MCP de fichiers du coffre**. C'est un **critère
  vérifiable**, pas une intention : sans ce retrait, l'outil redevient facultatif,
  donc contournable (cadrage §8).
- **Permission MCP à revérifier.** Le passage au seul `stdio` change ce que le
  harnais déclare : plus de serveur réseau à autoriser, mais la permission du
  serveur local et le droit de lancer la commande distante par SSH sont à
  **re-vérifier au plan**, fiche à l'appui.
- **Placement.** Le serveur ne crée **aucun état hors du coffre** ; il est
  **retirable** sans rien casser d'autre.
- **Hors du moteur.** Le serveur est l'adaptateur ; **aucun nom de harness ni
  d'adaptateur n'entre dans le moteur de règles partagé**.
- **Doubles à ramasser — dont un qui diverge.** Deux `extraire_frontmatter`
  coexistent : celui d'`appliquer_convention_parent.py` rend le frontmatter **et
  la position du corps** et type les valeurs (booléens, entiers) ; celui
  d'`indexer_coffre_parent.py` ne rend que des **chaînes**, nettoie les guillemets
  des listes et rend un dictionnaire vide à défaut de bloc. **Le premier
  survit** — la position du corps est nécessaire pour réécrire et pour détecter un
  **second bloc** — **enrichi du nettoyage des guillemets** du second.
  `notes_du_dossier` diverge de même entre les deux : l'application exclut les
  **dossiers hors mémoire** (`node_modules`, `code`) et les fichiers de dossier,
  l'indexeur non — **c'est la règle de l'application qui survit**, l'indexeur s'y
  aligne. `est_depot_imbrique` existe en double, **à l'identique**, dans
  `appliquer_convention_parent.py` et `regenerate_sommaire.py` : **une seule
  définition survit**, dans le moteur partagé. Ces écarts de comportement sont
  **figés par des tests de caractérisation avant** l'extraction (Phase 1 du
  plan).
  **État au 2026-10-09** : le moteur partagé est extrait, et la divergence de
  `notes_du_dossier` est **résorbée** — l'indexeur reprend la règle de
  l'applicateur (`est_note`) et n'y ajoute plus que ses propres index
  (PR #150 ; phase 1 du plan, `docs/PLAN.md`).

## Ce que ça coûte

- On écrit **à la main le peu de protocole nécessaire** en `stdio` — le serveur
  MCP existant en donne le modèle. Le transport réseau sort du champ : la surface
  délicate de Streamable HTTP (réponse unique ou flux d'événements, session) n'a
  plus à être écrite ni suivie.
- On **n'utilise pas** le SDK MCP, pourtant le plus confortable : on renonce à sa
  conformité suivie gratuitement.
- On suppose un **Python présent sur la machine cible** — déjà le cas.
- **Lancement à distance** : un harnais déporté lance le serveur `stdio` **par
  SSH**, sous une **clé dédiée en commande forcée** — le repli envisagé devient la
  règle ; c'est la **clé** qui borne l'appel, jamais la discipline de l'appelant.
- **Signe qu'on s'est trompé** : si le protocole écrit à la main devient un
  entretien à lui seul (ruptures de version du protocole MCP), ou si le serveur
  se met à porter de l'état ou une logique qui n'appartient pas au coffre.

## Ce qu'on a écarté, et pourquoi

- **SDK `mcp`** (officiel, **MIT**, transports **stdio, Streamable HTTP et SSE**,
  **Python 3.10+**, installation par `pip`/`uv`) : écarté **non pour sa qualité**
  mais pour ne pas installer **un paquet** sur la machine des agents ni suivre une
  **seconde chaîne d'outils**. À rouvrir si le confort du SDK pèse plus que cette
  simplicité — source : dépôt officiel `modelcontextprotocol/python-sdk` (licence
  et transports lus à la source).
- **Node/TypeScript** : écarté pour le pont obligé vers le moteur Python
  (sous-processus fragile, ou réimplémentation interdite) et pour une deuxième
  chaîne d'outils.
- **Go** : même rédhibitoire (pont vers le moteur Python, SDK MCP moins mûr) et
  langage non maîtrisé par l'utilisateur.

## Conditions de cap (contrôle du Visionnaire, 2026-10-09)

La décision les respecte ; le plan devra les tenir :

- l'outil reste **facultatif** : le coffre s'installe, se lit et se modifie sans
  lui, et l'outil ne crée **aucun état hors du coffre** ;
- il entre comme **module retirable** ;
- **aucun nom de harness ni d'adaptateur** dans le moteur de règles partagé ;
- le compte rendu « pour le chef » **ne devient pas** un format d'équipe déclaré
  dans la base.

## Après la décision

La relecture adverse a eu lieu (agent `contradicteur`, session neuve,
2026-10-09). Ses objections **retenues** sont intégrées : porte d'entrée pure et
sujet validé, au cadrage (§3, US-13/14) ; séquence d'écriture, verrou,
`git status` avant commit et refus du crochet qui défait l'écriture (ci-dessus) ;
registre des notes traitées dans le même commit (cadrage US-16) ; refus traduits
en geste (cadrage §7.4) ; marque d'auteur (`agent:`) comme correctif de contrat
probable (cadrage §7.8) ; permission MCP à revérifier (ci-dessus).

Une **seconde relecture** adverse a eu lieu (agent `contradicteur`, session
neuve, 2026-10-09) : verdict « **non mûr** », **deux points** à corriger, le
reste prêt. Ses **sept points** sont intégrés — (1) le retrait de l'accès direct
est borné par une **clé SSH dédiée en commande forcée**, constaté harnais par
harnais au plan, « n'expose rien » retiré ; (2) la détection d'un commit
concurrent passe par la **revérification de `HEAD` et de l'empreinte du fichier
lu** (le `git status` reste pour l'écriture non commitée) ; (3) à la **mort du
processus**, le reste d'acte non commité est défait ou achevé et signalé, et le
serveur **ne se suspend pas à la session** ; (4) la **porte d'entrée pure** nomme
**contrôle par contrôle** l'implémentation réutilisée, la convention des notes du
coffre parent étant **extraite dans le moteur partagé** et appelée par le skill
`traitement-des-notes` (une seule copie), les secrets passant par les aides pures
de `garde_secrets` ; (5) « deux principes » devient « **trois** » ; (6) le
**message du commit porte la marque** (§7.4) ; (7) le **verrou** vit hors du
suivi git **et hors du champ de `git status`**.
