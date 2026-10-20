# Dépôt de données du coffre — gabarits

Ce dossier porte les gabarits que `scripts/installer.py` pose à la racine du
**coffre parent** pour y créer son **dépôt de données** (§7.1 du contrat). Le
dépôt produit ne suit pas la mémoire ; le dépôt de données ne suit qu'elle.

| Gabarit | Posé sous | Jamais écrasé ? |
| --- | --- | --- |
| `gitignore-coffre` | `<coffre>/.gitignore` | oui — une fois posé, il appartient au coffre |
| `pre-commit` | `<coffre>/.githooks/pre-commit` | non — réinstaller le rafraîchit |
| `post-commit` | `<coffre>/.githooks/post-commit` | non — réinstaller le rafraîchit |
| `post-rewrite` | `<coffre>/.githooks/post-rewrite` | non — réinstaller le rafraîchit |

Le jeton `@PRODUIT@` des crochets est remplacé à l'installation par le nom du
dossier du dépôt produit, tel qu'il est à la racine du coffre. Rien ici ne
pousse au premier plan : `post-commit` lance la poussée en arrière-plan,
`post-rewrite` la relance une fois à la fin d'une réécriture d'historique, et
`scripts/depot_de_donnees.py fraicheur` dit si la dernière poussée réussie a
moins de 48 heures — c'est ce que surveille un moniteur push.

Le verrou, la marque de suspension et les journaux vivent dans le dossier git
**commun** (`--git-common-dir`), pas dans le `.git` du worktree : deux worktrees
liés du même coffre partagent ainsi un seul verrou, donc une seule poussée.

## La poussée automatique, sérialisée

`post-commit` ne pousse pas lui-même : il lance `depot_de_donnees.py
apres-commit` en arrière-plan, qui applique une **poussée à la fois** :

1. **Verrou** — `apres-commit` prend un verrou exclusif non bloquant
   (`<coffre>/.git/obsia-poussee.verrou`, `flock`). Qui l'obtient pousse ; les
   autres sortent aussitôt : la poussée du premier porte la **pointe** de la
   branche, donc la leur y est comprise.
2. **Anti-rebond** — le détenteur attend `OBSIA_POUSSEE_REBOND` secondes
   (3 par défaut) avant de pousser, le temps qu'une salve retombe.
3. **Boucle jusqu'à stabilité** — après avoir poussé, il relit la pointe ; si
   elle a bougé pendant la poussée, il repart pour un tour (10 au plus). Un
   commit arrivé pendant la poussée n'est donc pas laissé de côté.

Une salve — un rebase qui rejoue N commits et rappelle le crochet à chaque
commit — se solde ainsi par une ou deux poussées **successives**, jamais par N
poussées concurrentes. C'est la concurrence qui avait produit, le 2026-10-14, un
`cannot lock ref` et un `unable to migrate objects` — objets frôlant la
corruption, distant vérifié sain depuis par clone neuf et `git fsck`.

Deux garde-fous complètent la boucle :

- **Reprise bornée d'un échec** — si la poussée du détenteur échoue (hoquet
  réseau, distant momentanément indisponible), elle est retentée deux fois de
  plus, avec la fenêtre d'anti-rebond entre les essais. Sans cette reprise, un
  échec du détenteur laissait **toute** la salve en local : les autres crochets
  avaient déjà rendu la main (verrou tenu) et personne ne repoussait avant le
  commit suivant.
- **Échec du plafond distingué du succès** — si les 10 tours sont atteints alors
  que la pointe bouge encore, tout n'est pas parti : la ligne
  `salve inachevée (plafond de 10 tours)` est journalisée et le script sort en
  code `2`, distinct du `0` (« tout est parti ») et du `1` (poussée refusée).
  `fraicheur` relit le journal : toute ligne **à partir** de la marque de
  poussée réussie — celle-ci comprise — est relayée : une salve arrêtée en
  chemin, et une poussée échouée. La marque est comprise parce que la ligne de
  plafond est écrite dans la même seconde que la poussée réussie qui l'a posée ;
  un « à jour » ne tait donc pas des commits restés en local, et le rappel ne
  dépend pas de la *dernière* ligne écrite (un échec peut suivre la ligne de
  plafond et la masquer).

**Ce que le verrou ne ferme pas** : un commit qui atterrirait dans la
micro-fenêtre entre la dernière relecture de la pointe et la libération du
verrou n'est pas poussé tout de suite ; il part au commit suivant, et `fraicheur`
le signale au bout de 48 heures. C'est le prix du « la dernière gagne » ; faire
attendre les autres poussées coûterait un processus par commit rejoué, pour rien.

**Le verrou reste tenu pendant une reprise.** Les essais supplémentaires d'une
poussée échouée se font verrou en main : sur un réseau en trou noir, un détenteur
peut retenir la salve le temps de ses trois tentatives (délai réseau compris,
soit plusieurs minutes), pendant lesquelles les autres crochets rendent `0` sans
pousser. Si les trois échouent, la salve repart au commit suivant. Tenir le
verrou est ici le prix de la sérialisation : le relâcher entre deux essais
rouvrirait la porte à des poussées concurrentes — exactement le mal que cette
sérialisation corrige.

## Les réécritures d'historique : suspension automatique

Un rebase rejoue ses commits un à un et rappelle `post-commit` à chaque rejeu.
Pousser chacun de ces états intermédiaires serait au mieux inutile, au pire
nuisible : le nom de branche lu pendant un rebase vaut `HEAD` (la branche
réellement réécrite n'est lisible que dans l'état du rebase), et l'historique en
cours de réécriture n'avance plus côté distant.

**La poussée se suspend donc d'elle-même** : dès qu'un `rebase-merge` ou
`rebase-apply` est présent dans le dossier git du worktree, `apres-commit` ne
pousse pas. C'est le crochet `post-rewrite` — tiré une fois, à la fin — qui
pousse la **pointe finale**, au seul moment où la branche est réattachée et
stable. **Il n'y a rien à poser à la main pendant un rebase.**

Deux interrupteurs explicites restent disponibles, pour les réécritures que le
script ne détecte pas (`filter-branch`, réécriture menée hors de ce dépôt) :

- `OBSIA_POUSSEE=0` dans l'environnement — p. ex. `OBSIA_POUSSEE=0 git filter-branch …` ;
- la marque `<coffre>/.git/obsia-poussee.suspendue` (un simple fichier).

Valeurs reconnues pour `OBSIA_POUSSEE` : `0`, `non`, `false`, `off`. La
suspension explicite est respectée aussi par `post-rewrite` : suspendre pour tout
un rebase suspend la poussée de fin de rebase comprise.

**Rien ne disparaît sans trace.** Chaque épisode laisse une ligne datée dans
`<coffre>/.git/obsia-poussee.suspendue.log` — `suspendue` à la première mise en
suspension, `reprise` dès la première poussée qui repart (une seule ligne par
épisode, pas une par commit rejoué). `fraicheur` la relaie : il affiche
« Poussée suspendue depuis … (raison) ». Une marque restée en place ne se
découvre donc plus 48 heures plus tard sans qu'on sache pourquoi.

**Limite connue** : la détection ne couvre que `rebase-merge` et `rebase-apply`.
Une réécriture plus exotique (`filter-branch`, `git commit-tree` en boucle) doit
être suspendue à la main par l'un des deux interrupteurs ci-dessus.

## Ce que le crochet d'avant-commit refuse

`pre-commit` appelle `depot_de_donnees.py avant-commit`, qui applique trois refus
dans cet ordre :

1. le commit ne vient pas de la machine déclarée **écrivain** du coffre (§7.1) ;
2. une valeur à forme de secret **entre** dans la mémoire — `garde_secrets.py` ;
3. un carnet du coffre ne respecte pas le §6 — `verifier_coffre.py`.

Le garde de secrets (`scripts/garde_secrets.py`) reprend les motifs de **secret**
de `publier.BLOQUANTS` — une seule source, jamais recopiés — et y joint un cas
que ces motifs ne voyaient pas : un fichier dont **tout le contenu** est un jeton
sans espace, à forte entropie. C'est le mot de passe collé seul dans une note, qui
est entré en clair le 2026-10-04 puis a été recopié par un index régénéré.

- **Ce qu'il ne reprend pas** : les motifs de publication — courriel, adresse IP
  privée, nom d'hôte interne. Le coffre privé les porte légitimement ; les
  refuser fermerait la mémoire au nom de la publication.
- **Faux positifs maîtrisés** : ce n'est que pour « secret affecté » — la règle
  de forme ne vaut pas pour les trois autres motifs, qui portent déjà la forme de
  leur secret — que la valeur doit *avoir forme de secret*. Ne se refusent pas :
  un gabarit jugé **en tête** (`yourpassword`, `change-root-password`,
  `mot-de-passe` — une valeur qui contient « change » plus loin reste un secret),
  un chemin jugé **en tête** (`/`, `~/`, `./`, `../` — un `/` au milieu ne fait
  pas un chemin), et une prose **non guillemetée**. Une phrase **entre
  guillemets**, elle, est un secret, comme le dit le commentaire du motif
  importé ; sauf si c'est une ligne de commande recopiée, que le coffre porte
  légitimement — encore faut-il, pour l'admettre, **à la fois** une espace et un
  marqueur shell (`;`, `|`, accent grave, `$(`). La ponctuation ordinaire (`&`,
  `$` seul, parenthèses, accolades, chevrons) vit dans la prose et n'exempte
  rien : une valeur citée qui n'a pas d'espace, ou dont le seul signe est un
  `&`, reste un secret. Enfin une empreinte n'est pas un secret : hexadécimal
  d'une longueur de condensat réelle
  (7-12, 40, 64), ou hexadécimal quelconque à côté d'un mot qui dit « sha » ou
  « commit ».
- **Limite connue** : un secret collé *au milieu d'une prose* n'est vu que s'il
  porte un nom. Sans qu'on écrive « mot de passe » à côté, seul un fichier qui
  n'est *que* le jeton est refusé — le jeton se juge sur le **fichier entier**,
  jamais mot à mot : juger chaque mot du corpus refuserait des chemins, des liens
  et des noms de fichiers, c'est-à-dire la mémoire elle-même.
- **Fichiers non-UTF-8** : tout se lit en octets ; un binaire est écarté à son
  octet nul, le reste est décodé avec `replace`. Un fichier Latin-1 garde ainsi
  son secret lisible, sans faire tomber le crochet.
- **Réarmement** : réinstaller (`installer.py`) rafraîchit le crochet ; le garde,
  lui, vit dans le dépôt produit et suit ses mises à jour.
