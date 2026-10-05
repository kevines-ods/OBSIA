# Registre du contrat — où vit chaque règle

Ce registre accompagne le découpage du contrat en un **noyau**
(`IA/system/VAULT-CONTRACT.md`, toujours chargé) et des **annexes**
(`IA/system/contrat/`, lues au besoin). Il est permanent : il dit, pour chaque
phrase normative du contrat d'avant le découpage (état du 2026-10-02, 9 776
mots), où elle vit désormais. Les numéros de section ne changent pas : une
citation « §N » reste juste.

**Principe.** Le noyau se suffit à lui-même. Toute règle qu'un agent peut
enfreindre sans avoir rien chargé y reste. Depuis l'allègement du 2026-10-04,
le noyau la garde **en une phrase, sans sa justification** : le pourquoi, les
exemples et les procédures vivent dans une annexe, qui n'ajoute aucune règle.
Si une annexe contredit le noyau, c'est elle qui est fausse.

**Non normatif.** Ce registre est un outil de traçabilité : il dit où vit chaque
règle, il n'en porte aucune. Seuls le noyau et ses annexes font foi ; une règle
dont la seule trace serait une ligne d'ici n'existerait pas.

**Numérotation.** Les numéros de la première colonne (« 7.4 », « 2.1 »…)
numérotent les lignes de ce registre, **pas** les sections du contrat : la
ligne 7.4 n'est pas le §7.4. Un renvoi « §N » vise toujours la section du
contrat.

**Légende.**
- **N** : la règle reste au noyau, mot pour mot ou à peine raccourcie, sans
  rien perdre de ce qu'elle exige.
- **A·x** : seule la justification ou la procédure part dans l'annexe `x`.
  La règle elle-même, si la ligne en porte une, reste au noyau.
- **A** seul : l'élément part entier dans l'annexe, et le noyau garde une ligne
  de renvoi qui dit *quand* la lire.

Annexes : `frontmatter`, `memoire`, `coffre-parent`, `verification`,
`taches`, `distribution`. Chacune s'appelle `contrat-<x>.md`.

## Préambule

| # | Règle | Dest. |
| --- | --- | --- |
| P1 | Le contrat est la source unique des règles ; un agent ou un skill le référence, il ne les redéfinit pas. | N |
| P2 | Le contrat, c'est le noyau et ses annexes. Une annexe précise et n'ajoute aucune règle. En cas de contradiction, le noyau fait foi et l'annexe est à corriger. | N (nouveau, B2) |

## §1 Vocabulaire

| # | Règle | Dest. |
| --- | --- | --- |
| 1.1 | Tableau agent / skill / MCP / tâche : nature, emplacement, rôle. | N |
| 1.2 | Un agent utilise des skills. Un skill n'est jamais un agent. Une tâche déclenche un agent. | N |
| 1.3 | `obsidian-manager` est un skill. Toute formulation qui suggère qu'un skill est un agent est une erreur. | N |
| 1.4 | Un agent n'est nommé que s'il a son fichier dans `IA/agents/`, nulle part ailleurs, pas même en exemple. Ce sont les noms de skills qui servent d'exemples. | N |
| 1.5 | Histoire de la règle « un seul agent », et `agent 1`/`agent 2` comme contre-exemples. | A·memoire |

## §2 Écriture dans le coffre

| # | Règle | Dest. |
| --- | --- | --- |
| 2.1 | Un agent `read_only: true` n'écrit nulle part. | N |
| 2.2 | Trois zones en écriture directe : `brouillon/` ; la mémoire du coffre parent (`0-PERSONNELS/`, `0-SAVOIRS/`, le résumé et les carnets de son chantier) sauf le dossier d'un autre agent ; `IA/skills/` si `createur-de-skill` est déclaré. | N |
| 2.3 | Tout le reste du dépôt passe par un patch Git revu. | N |
| 2.4 | Aucune suppression sans archivage : pour la mémoire, **l'historique Git du dépôt de données tient lieu d'archive** ; pour le reste du dépôt produit, un fichier retiré part dans `.archive/`, qui reste **versionné** (jamais ignoré par Git). Rien de `.archive/` n'est lu ni indexé ; les dossiers commençant par un point sont écartés partout. | N |
| 2.5 | Le pourquoi de `.archive/` versionné (sinon il ne survit pas à un clone neuf). | A·verification |
| 2.6 | Un aperçu listant les chemins, avant toute action qui touche plusieurs fichiers. | N |
| 2.7 | Les fichiers générés ne s'éditent jamais à la main. La liste : `sommaire.md`, `agents-index.md`, `skills-index.md`, `taches-index.md`, `modules-index.md`, `IA/README.md`. | N (liste complète gardée, M10) |
| 2.8 | Hors du dépôt : un dépôt extérieur suit le §3, le coffre parent le §7. | N |
| 2.9 | Plusieurs agents (§2.1) : jamais de commit dans l'arbre principal ; un worktree par séance ; branche `<nom-agent>/<sujet>` ; ne pas toucher la branche ni le worktree d'un autre agent ; se resynchroniser avant de pousser. | N |
| 2.9b | Jamais de worktree sous `/tmp` ; une PR s'ouvre sur la branche par défaut, jamais sur la branche d'une autre PR. | N (ajoutés en N2, déjà décidés dans `travail-en-parallele.md`) |
| 2.10 | Pourquoi l'arbre principal est une ressource commune, et le crochet de pré-commit. | A·verification ; renvoi à `travail-en-parallele.md` gardé au noyau |

## §3 Hors du coffre

| # | Règle | Dest. |
| --- | --- | --- |
| 3.1 | Le coffre ne nomme aucun harness ni aucune base de code extérieure. | N |
| 3.2 | Sur un dépôt extérieur : patch Git revu, jamais de commit sur la branche par défaut. | N |
| 3.3 | Les vérifications du projet passent avant de proposer le patch. | N |
| 3.4 | Jamais de secret dans le code : variables d'environnement ou configuration hors dépôt. | N |
| 3.5 | Ajouter une fonctionnalité, c'est d'abord un skill documenté dans `IA/skills/`, puis l'implémentation. | N (perte relevée en B1, rétablie) |

## §4 Exécution de code

| # | Règle | Dest. |
| --- | --- | --- |
| 4.1 | Toute exécution se fait en sandbox. | N |
| 4.2 | Aucun accès réseau implicite. | N |
| 4.3 | Les secrets ne sortent jamais du coffre et ne s'écrivent jamais dans une note. | N |

## §5 Frontmatter

| # | Règle | Dest. |
| --- | --- | --- |
| 5.1 | Tout agent, skill, MCP, tâche, module **et fichier du contrat** commence par un frontmatter valide. Les champs communs sont `schema`, `kind`, `name`, `description`, `read_only` et `module`. **Exceptions** : un MCP n'a ni `read_only` ni `skills` ; une tâche et un fichier du contrat n'ont pas de `read_only`. | N (exceptions gardées au noyau, A5) |
| 5.2 | Tableaux détaillés des champs par type (agents, skills, MCP, tâches), sémantique de `read_only`. | A·frontmatter |
| 5.3 | `read_only: true` : aucune écriture nulle part, même par patch. | N (déjà au 2.1) |
| 5.4 | `name` = nom du fichier, en minuscules avec tirets, sans espaces ; jamais `SKILL.md`. | N |
| 5.5 | Les listes YAML s'écrivent une entrée par ligne ; les clés prennent un underscore ; un champ du frontmatter ne se répète pas dans le corps. | N (A3) |
| 5.6 | **Une information vit à un seul endroit.** Une règle violable sans rien charger va au contrat ; une procédure va dans un skill. | N |
| 5.7 | MCP : `permission: elevated` dès qu'un système externe est touché. Un MCP n'est utilisable que s'il est déclaré par un agent. | N |
| 5.8 | Tâches : `quand` entre guillemets, `fuseau` obligatoire, `exécutant` dit qui a le droit de déclencher (`local` ou `harness`), une section `## Instruction` ou `## Commande` obligatoire. | N (A3) ; tableau détaillé A·frontmatter |
| 5.9 | Un skill a une forme plate (`<nom>.md`) ou dossier (`<nom>/<nom>.md`) ; seul `references/` contient des notes. | N (A3) ; quand passer d'une forme à l'autre : A·frontmatter |

## §6 Nommage et mémoire

| # | Règle | Dest. |
| --- | --- | --- |
| 6.1 | Les noms de notes sont uniques dans tout le coffre parent. | N |
| 6.2 | Liens vers le contrat en chemin relatif, profondeur selon la forme du skill. | N (au §5, revue N2) ; le vérificateur : A·memoire |
| 6.3 | Arborescence de la mémoire du coffre parent (`0-PROJETS/`, `0-MEMOIRES/` — préférences et `<nom-agent>/expériences/`, **vivantes**, et chantiers clos **gelés** —, `0-PERSONNELS/` : profil ; projets avec résumé, vision, carnets du jour, documents ; **un dossier par chantier** portant ses `carnets/`, ses `documents/` et son résumé, un seul niveau ; plus de dossier `archives/`). | A·memoire (l'arbre est dans l'annexe ; le noyau garde, en une phrase, l'axe de partage de la mémoire) |
| 6.4 | Tableau « où écrire selon la nature de l'information ». | A·memoire (le noyau renvoie à l'annexe) |
| 6.5 | Profil, préférences et expériences ne se datent pas ; seuls les carnets portent une date. Dans le doute, on écrit dans le carnet. | N |
| 6.6 | `0-PROJETS/` porte **tout** projet — du coffre comme de l'utilisateur ; `code/` y est exclu du dépôt de mémoire. | N |
| 6.7 | Un projet du coffre passe par une PR, demande comprise : la description porte la demande et le résumé de séance, jamais la mémoire ni un chemin du coffre parent ; relecture à trois. | N |
| 6.8 | Le carnet : son nom, son frontmatter (`agent`, `projet`, `statut`), son contenu, l'étape écrite **avant** d'agir, son dossier — celui du chantier, ou celui du projet pour une séance sans chantier —, un chantier transverse dans `obsia` sauf la part personnelle. | N |
| 6.9 | Une séance sans chantier écrit dans le carnet du jour du projet de domaine. Un agent en lecture seule n'écrit aucun carnet. | N |
| 6.10 | Reprise : chercher dans l'arbre principal et dans chaque worktree lié, par nom d'agent, rapprocher le carnet de l'état réel, laisser l'utilisateur choisir ; pendant la bascule, aux anciens emplacements aussi. | N |
| 6.11 | Le carnet se commite à chaque étape. | N |
| 6.12 | Transition : l'ancienne forme ne veut pas dire « sans historique », et pendant la bascule carnets, projets et notes personnelles se cherchent à tout emplacement qui existe, dans l'ordre — `0-PROJETS/`, l'ancien nom `-PROJETS/`, l'ancien `mémoire/projets/` du dépôt ; le profil sous `0-PERSONNELS/`, `-PERSONNELS/`, `mémoire/` ; les préférences et les expériences sous `0-MEMOIRES/`, puis `0-PERSONNELS/`, `-PERSONNELS/`, `mémoire/`. | A·memoire (l'ordre détaillé ; le noyau garde la clause datée — chantier `souverainete-des-donnees`, au plus tard le 2026-12-31 — et le renvoi) |
| 6.13 | Clôture : le résumé devient un bilan avec une section « État », le dossier entier du chantier gèle dans `0-MEMOIRES/`, le durable remonte avant. | N |
| 6.14 | Rien de ce qui décrit l'utilisateur ne vit chez un agent ; tout agent `read_only: false` corrige sur place le profil (`0-PERSONNELS/`) et les préférences (`0-MEMOIRES/préférences/`, dossier commun, jamais sous le nom d'un agent). | N |
| 6.15 | Pourquoi un projet ne vit pas chez un agent ; agent en lecture seule sans espace mémoire (`0-MEMOIRES/<nom-agent>/`). | A·memoire (règle gardée au 6.9) |
| 6.16 | Le nom d'une note dit son sujet. | N |
| 6.17 | Noms de projets explicites ; jamais `agent 1` ni `projets 1`. Un projet ne peut porter ni `préférences` ni le nom d'un agent : la collision rendrait la mémoire des agents indistinguable d'un chantier gelé, et le contrôle refuse. | N (revue N2) |

## §7 Coffre parent

| # | Règle | Dest. |
| --- | --- | --- |
| 7.1 | Le coffre parent est **son propre dépôt Git** : versionné, un seul écrivain, un unique dépôt distant nu sur le NAS, `**/.git` hors de Syncthing ; `OBSIA/` en est exclu par un `.gitignore` en liste blanche. Le coffre s'écrit `Mon coffre/`, son nom réel se lit dans `obsia.local.yml`. | N (la règle, en une phrase) ; le gabarit `.gitignore` exact : A·coffre-parent |
| 7.2 | `../` ne sert qu'à l'intérieur du dépôt, jamais pour désigner le coffre parent. | N |
| 7.3 | Les dossiers de mémoire de premier niveau commencent par `0-` : un chemin n'est plus confondu avec une option, le piège du tiret a disparu. | N (une phrase, sans tableau) |
| 7.3.1 | Où va la note d'un projet : *est-ce que ça décrit le produit ?* Si oui, le dépôt produit (`IA/system/`, `IA/skills/`, `IA/MCP/`, `IA/tâches/`) et la PR ; sinon le coffre parent, sous `0-…`, jamais `OBSIA/` — **dans le doute, le coffre parent**. | N |
| 7.4 | Tableau des trois formes, exemples, chemin absolu entre guillemets. | A·coffre-parent |
| 7.5 | Structure de premier niveau fixe : le dépôt produit (`OBSIA/`) est exclu ; seul l'utilisateur crée, renomme ou supprime un dossier de mémoire de premier niveau. Les noms s'écrivent en majuscules, tels qu'ils sont sur le disque. | N |
| 7.6 | Tableau des dossiers et de leur rôle, `0-MEMOIRES/` compris (la mémoire des agents y vit, les chantiers clos y sont gelés). | A·coffre-parent (le noyau garde la règle des `0-` et des trois noms) |
| 7.7 | Un agent `read_only: false` lit tout le coffre parent. Lire n'est pas recopier : rien du coffre parent ne migre dans `OBSIA/`, aucun secret n'y entre. | N |
| 7.8 | Zones d'écriture : `0-EN-VRAC/`, compléter dans `0-SAVOIRS/`, `_MAINTENANCE/`, le classement, `0-PROJETS/<projet>/` (résumé, carnets, documents), `code/`, la note de référence `auteur:` de `0-PERSONNELS/`, `0-MEMOIRES/préférences/` et `0-MEMOIRES/<nom-agent>/expériences/` (corrigées sur place), la vision par le seul `visionnaire` ; un dossier de chantier clos de `0-MEMOIRES/` ne s'écrit jamais (gelé). | N (une liste) |
| 7.9 | On ne modifie jamais une note existante de `0-PROJETS/`, `0-DOCUMENTS/` ou `0-PERSONNELS/` dont l'agent n'est pas l'auteur, même à la demande de l'utilisateur ; on n'y déplace ni n'y supprime rien. | N |
| 7.10 | Pourquoi l'auteur peut corriger son propre texte ; les marques (` — résumé`, ` — vision`, `carnets/`, `auteur:`). | A·coffre-parent (les marques restent au noyau) |
| 7.11 | `code/` : §3 intégral ; exclusion Obsidian posée par l'installeur ; réserve sur l'effet du motif et sur l'unicité des noms. | A·coffre-parent (la phrase « §3 intégral » reste au noyau) |
| 7.12 | Jamais une valeur interdite par le §9 dans `OBSIA/` ; le §9 l'emporte sur tout. | N |
| 7.13 | `0-PERSONNELS/` : on y lit librement ; on n'y écrit que pour classer ou tenir sa note de référence ; son contenu ne migre jamais dans `OBSIA/`. | N |
| 7.14 | Aperçu, copie datée dans `_MAINTENANCE/`, exécution, puis consignation, avant toute écriture hors `0-EN-VRAC/` ou sur plusieurs fichiers. | N |
| 7.15 | Une action de chantier va au carnet, une action hors chantier dans `_MAINTENANCE/`. Un carnet dont on est l'auteur se met à jour sans nouvel aperçu. | N |
| 7.16 | Le registre `notes_remplies.md` : une note qui y figure n'est pas à revérifier, et il se met à jour après chaque traitement. | N |
| 7.17 | Tags du vocabulaire contrôlé (`IA/system/tags-du-coffre-parent.md`), jamais hors liste. Un lien ne relie que si sa cible existe. Les noms de notes sont uniques. | N |
| 7.18 | Accès du harness : il doit lire et écrire à la racine du coffre parent. Lire la fiche `IA/MCP/coffre-parent.md` avant d'appeler ses outils. | N |
| 7.19 | `0-EN-VRAC/` est un tampon, vidé à chaque rangement. Une note d'`0-EN-VRAC/` n'est jamais une cible de rétrolien stable. | N (M : rétabli) |
| 7.20 | Le pourquoi de chaque zone, le lien avec les skills `traitement-des-notes` et `adaptateurs-harness`. | A·coffre-parent |

## §8 Sources

| # | Règle | Dest. |
| --- | --- | --- |
| 8.1 | Une note durable distingue évidence (avec URL), interprétation et synthèse, et regroupe ses URL en fin de fichier. | N |

## §9 Le carnet comme trace

| # | Règle | Dest. |
| --- | --- | --- |
| 9.1 | La trace d'une séance, c'est le carnet, écrit au fil de l'eau dans le dépôt du coffre parent (§7.1) ; la PR du produit ne porte que la demande et le résumé de séance, et se relit avec le diff. Il n'y a pas d'autre journal. | N |
| 9.2 | `IA/system/session-log/` est des notes de séance — donc de la **mémoire** : on n'y écrit plus, ses notes ne se réécrivent pas, et elles quittent le dépôt à la bascule. | Hors du noyau ; `A·memoire` (transition) — destination `0-MEMOIRES/obsia/session-log/`, gelé ; `verifier_coffre.py` refuse leur survie après le 2026-12-31 (§11). |
| 9.3 | **Tout appel de MCP, quel que soit son `permission`**, et toute correction appliquée à un système, s'inscrivent au carnet sur une ligne horodatée (quoi, où, résultat). | N (perte relevée en B1, rétablie mot pour mot) |
| 9.4 | Première limite : le carnet n'est pas un journal d'audit infalsifiable, et celui d'un projet de l'utilisateur n'a que l'aperçu du §7.4. | N |
| 9.4b | Seconde limite : on consigne la **nature** de l'action, pas nécessairement sa cible. Une trace qu'on ne pourrait pas publier ne s'écrit pas davantage dans le privé. | N (B1 de N0, rétablie) |
| 9.5 | Jamais d'adresse IP privée, de nom d'hôte interne, d'URL interne ni d'identifiant, même dans le privé. La liste locale des noms interdits est `~/.config/obsia/noms-interdits`. | N (A4 : emplacement de la liste gardé) |
| 9.6 | Pourquoi l'horodatage ; pourquoi `normal` ne dispense pas de consigner. | A·memoire |
| 9.7 | `brouillon/` ne sert pas de trace. | N |

## §10 Méthode d'exécution

| # | Règle | Dest. |
| --- | --- | --- |
| 10.0 | Étape 0 : la reprise (arbre principal et worktrees, agents en lecture seule dispensés). | N, mot pour mot (l'`AGENTS.md` la recopie) |
| 10.1–10.4 | Choisir l'agent ; ne charger que les skills et MCP déclarés et nécessaires ; lire la fiche d'un MCP avant de l'appeler ; écrire en mémoire selon le §6 ; **lire la note existante avant d'écrire** ; lire une annexe avant l'acte que sa ligne nomme ; citer les chemins. | N, sans raccourci (A : M10) |
| 10.5 | Ne pas charger un fichier « pour voir ». Un skill en lecture seule n'exécute aucune commande qui modifie l'état. | N |

## §11 Fichiers générés et vérification

| # | Règle | Dest. |
| --- | --- | --- |
| 11.1 | Si un index et un frontmatter se contredisent, le frontmatter a raison : on corrige la source, puis on régénère. | N (A4) |
| 11.2 | Tableau fichier → script → source ; les sommaires se génèrent dans le coffre parent, pas dans ce dépôt. | A·verification (liste des fichiers gardée au 2.7) |
| 11.3 | Un échec de routage se corrige dans la description. Une attente ne se relâche que lorsqu'elle demande l'impossible à une mesure lexicale, et cela s'écrit dans `IA/system/routage-attendu.md` avec sa raison. Les exemptions vivent dans le script, jamais dans un frontmatter. | N (A4) |
| 11.4 | Un contrôle qu'on croit plus large qu'il n'est vaut moins que pas de contrôle ; `brouillon/`, `.archive/` et `IA/system/session-log/` sont exemptés du contrôle des chemins — la mémoire est sortie du dépôt, ses chemins ne s'y citent plus. | A·verification |
| 11.5 | Avant un commit : `regenerate_sommaire`, `regenerate_index`, `verifier_coffre`, `evaluer_routage`. | A·verification (la séquence ; le crochet la lance, le noyau renvoie à l'annexe) |
| 11.6 | Le crochet de pré-commit s'active une fois par clone — `installer.py --appliquer` l'arme (`git config core.hooksPath .githooks`). | A·verification (le noyau renvoie à l'annexe) |
| 11.7 | CI, `--no-verify`, `evaluer_modele.py`, bibliothèque standard seule. | A·verification |

## §12 Tâches planifiées

| # | Règle | Dest. |
| --- | --- | --- |
| 12.1 | Une tâche se déclare dans `IA/tâches/`, qui fait foi ; un timer ou un cron n'en est qu'une instance. Créer, modifier ou **suspendre** une tâche passe par PR. **Instancier ou retirer une instance est une action à effet externe : une ligne horodatée au carnet.** | N (B2 de N0) |
| 12.2 | Au plus une instance vivante par tâche, tous exécutants confondus. Une instance s'appelle `obsia-<tâche>`. L'instruction se suffit à elle-même. Le registre déclare une intention, jamais un état. | N |
| 12.3 | `taches-index.md` est toujours en contexte ; savoir qu'une tâche existe n'est pas l'instancier. | N |
| 12.4 | Pourquoi, et la procédure (skill `cron`). | A·taches |

## §13 Modules, installation, publication

| # | Règle | Dest. |
| --- | --- | --- |
| 13.1 | Tout agent, skill, MCP et tâche déclare son `module`. | N (déjà au 5.1) |
| 13.2 | Frontmatter d'un module ; renvois entre modules ; les sondes, purement déclaratives, sans commande arbitraire ni réseau. | A·distribution |
| 13.3 | Profil `obsia.local.yml` non versionné, écrit par l'installeur ; pas de profil = catalogue complet. | N (revue N3) ; le pourquoi : A·distribution |
| 13.4 | `installer.py` et `publier.py` n'écrivent qu'avec `--appliquer`. Lire `installation-et-publication.md` avant de les lancer avec `--appliquer`. | N |
| 13.5 | Le privé fait foi ; la publication va à sens unique ; une correction faite sur le public se reporte à la main dans le privé. | N (A3) ; le pourquoi : A·distribution |
| 13.6 | Un fichier publié ne cite pas un chemin non publié (`brouillon/`, `.archive/`, et l'ancien `mémoire/` pendant la bascule), sauf leurs `README.md` et `profil-utilisateur.md`. | N (s'enfreint en écrivant un skill) |
| 13.7 | Contrôle de fuite : les valeurs à forme reconnaissable refusent la publication ; `--forcer` ne franchit jamais une clé privée ni un jeton ; les noms de la liste locale avertissent sans bloquer, et un agent rapporte l'avertissement. Liste absente = aucun nom contrôlé : « aucune trouvaille » ne dit alors rien des noms nus. | N (M7) ; motifs exacts A·distribution |

## Ce qui a été vérifié

- Chaque paragraphe normatif des §1 à §13 figure dans une ligne de ce
  registre. Les phrases purement explicatives, sans exigence, partent avec
  l'annexe de leur section.
- Les pertes relevées par la relecture adverse sont rétablies au noyau :
  3.5, 9.3, 9.4, 9.4b, 9.5, 10.1–10.4, 2.4, 2.7, 11.1, 7.19, 5.1 (`kind: contract`
  et exceptions). Après la relecture du registre : 5.5, 5.8, 5.9, 11.3, 11.6,
  12.1 (suspendre, instancier), 12.3, 13.5, 13.7 remontent ou sont complétés.
- **Allègement du 2026-10-04.** Le noyau est redescendu de 574 à **450 lignes**
  (ligne de base `main` : 442) en sortant du noyau ce qui n'y est pas une règle :
  l'arbre de la mémoire et le tableau « où écrire » (6.3, 6.4), l'ordre détaillé
  de la bascule (6.12), le rôle de chaque dossier et le gabarit `.gitignore`
  exact (7.6, 7.1), l'organisation du frontmatter d'un projet (7.3.1), la
  procédure de preview (7.4), la séquence de commandes et le crochet de
  pré-commit (11.5, 11.6). Chaque règle est restée au noyau **en une phrase**,
  sans sa justification ; les annexes les portaient déjà, seule leur
  destination a changé ci-dessus.
- **Dédoublonnage du 2026-10-04.** Après la relecture du noyau règle par règle
  par le `contradicteur`, chaque règle citée deux fois au noyau n'y garde plus
  qu'**une seule formulation**, l'autre devenue un renvoi : l'unicité des noms
  reste au §6 (7.5 renvoie) ; `read_only` au §2 (5.3 renvoie) ; la règle de la PR
  au §6, réunie en une phrase — la demande, le résumé, et « ni personne ni
  client » (9.3 renvoie) ; le commit du carnet au §6 (9.1 renvoie) ; le preview
  au §2 (7.4 renvoie) ; « aucun chemin du coffre parent » au §6 pour la PR et au
  §13 pour le fichier publié ; le contrôle de collision au §6 (11.6 renvoie).
  Les mentions de l'ancien `session-log/` quittent le noyau (9.2, 13.6) : le fait
  vit dans `IA/README.md` et le skill `cloture-de-session`. Le noyau passe de 450
  à **446 lignes**, 4 067 mots.
- **Estimation du noyau** : une centaine de lignes N, à une ou deux phrases
  chacune, soit **environ 2 800 à 3 300 mots**. C'est au-dessus de la
  cible de 2 000 mots de la v1 et autour du plafond de 3 000 mots de la v2.
  Le seuil est un constat, pas un ordre : si le noyau dépasse 3 000 mots
  sans perdre de règle, c'est le seuil qui cède, et le carnet le dit.
