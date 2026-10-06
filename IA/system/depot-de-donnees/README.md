# Dépôt de données du coffre — gabarits

Ce dossier porte les gabarits que `scripts/installer.py` pose à la racine du
**coffre parent** pour y créer son **dépôt de données** (§7.1 du contrat). Le
dépôt produit ne suit pas la mémoire ; le dépôt de données ne suit qu'elle.

| Gabarit | Posé sous | Jamais écrasé ? |
| --- | --- | --- |
| `gitignore-coffre` | `<coffre>/.gitignore` | oui — une fois posé, il appartient au coffre |
| `pre-commit` | `<coffre>/.githooks/pre-commit` | non — réinstaller le rafraîchit |
| `post-commit` | `<coffre>/.githooks/post-commit` | non — réinstaller le rafraîchit |

Le jeton `@PRODUIT@` des crochets est remplacé à l'installation par le nom du
dossier du dépôt produit, tel qu'il est à la racine du coffre. Rien ici ne
pousse : `post-commit` lance la poussée en arrière-plan, et
`scripts/depot_de_donnees.py fraicheur` dit si la dernière poussée réussie a
moins de 48 heures — c'est ce que surveille un moniteur push.

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
