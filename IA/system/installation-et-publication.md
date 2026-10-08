# installation-et-publication.md — ce que font `installer.py` et `publier.py`

Le détail d'exécution des deux scripts du §13 de `VAULT-CONTRACT.md`. Le
contrat garde les **règles** — ce qu'un agent peut violer sans avoir rien
chargé ; ce fichier garde la **procédure** et ses raisons, qui ne servent
qu'au moment d'installer ou de publier (§5 : une information vit à un seul
endroit). À lire avant de lancer l'un des deux scripts autrement qu'en
lecture (`--sonder`, aperçu sans `--appliquer`).

Les garde-fous décrits ici sont appliqués **par le code** : un agent qui ne
les aurait pas lus ne les contourne pas pour autant.

## Installation — `installer.py` (§13.4)

**`--installer` ne touche jamais à la source.** Le coffre d'où l'on copie est lu,
rien de plus : c'est ce qui sépare une copie d'une installation en place. Le
profil — celui qu'on écrit comme celui qu'on supprime, sous `--tout` par
exemple — est toujours celui du coffre **effectif**, donc de la cible. Sans
cette règle, `--tout --installer CIBLE` effaçait le profil de la source : elle
perdait son mode, un `--rejouer` y échouait ensuite, et rien ne l'avait annoncé.

**Le dossier personnel n'est jamais un coffre.** Si le dossier qui contiendrait
`OBSIA/` (en place, ou la cible en copie) est le dossier personnel,
`--appliquer` refuse avant toute écriture, code 1 : ni `AGENTS.md`, ni profil,
ni mémoire. Sans ce refus, `AGENTS.md` y serait lu par tout harness lancé depuis
le dossier personnel, et un second passage, les dossiers de mémoire devenus
marqueurs, y ferait un `git init`. L'aperçu l'annonce.

**`AGENTS.md`** — l'installation écrit également, à côté de leur coffre effectif,
le fichier que les harness lisent d'eux-mêmes : `<dossier parent>/AGENTS.md`.
Autrement dit, la cible d'installation désigne le dossier `OBSIA/` : `AGENTS.md`
atterrit un cran au-dessus, à la racine du coffre que l'agent ouvre. Les deux
modes l'écrivent, chacun pour le coffre effectif — celui des deux qui reçoit
l'installation. Son contenu est celui de `scripts/generer_prompt.py` : index,
méthode, profil retenu. Il s'ouvre sur les **deux racines**, nommées : le coffre
(parent du dépôt, là où vit la mémoire) et le dépôt `OBSIA/` (agents, skills,
contrat). Un en-tête qui donnait le dépôt pour la racine du coffre a fait écrire
un `0-SAVOIRS/` dans le dépôt de code, sous Goose et DeepSeek Harness.

Les deux racines y sont désignées **sans aucun chemin** : le coffre est « le
dossier qui contient le sous-dossier `OBSIA/` », et le dépôt « son sous-dossier
`OBSIA/` ». Le texte engendré ne porte **aucun chemin absolu**, parce que
l'`AGENTS.md` est synchronisé entre des postes où le coffre n'a ni le même chemin
ni le même nom : un chemin de machine y serait faux partout ailleurs. Deux postes
engendrent donc le même fichier, à l'octet près.

Le repère n'est pas « le dossier qui contient ce fichier » : le texte se pose
aussi **ailleurs** qu'à la racine du coffre — une copie annexée par un harness qui
n'a pas de fichier à lire (`.pi/APPEND_SYSTEM.md`, espace de travail d'OpenClaw).
Là, « ce fichier » désignerait le dossier d'accueil de la copie. Le sous-dossier
`OBSIA/` est le repère qui tient partout.

**Ce qui n'a pas de fichier doit recevoir la racine par l'appelant.** Pour un
harness qui lit un répertoire de travail (Pi à la racine du coffre, OpenClaw dont
`agents.defaults.workspace` pointe la racine), rien à faire : le repère se résout
sur place. Pour un harness qui **colle** le prompt dans une fenêtre (LibreChat,
DeepSeek Harness), la racine n'est plus dans le texte : elle s'écrit **une ligne,
en tête des instructions du preset**, avant le texte engendré —
`Coffre (la mémoire) : /chemin/vers/le/coffre` — ou l'agent passe par le serveur
`coffre-parent` (`IA/MCP/coffre-parent.md`), monté sur la racine et qui la nomme
lui-même dans la configuration du harness. Cette ligne vit hors du texte
engendré, donc hors de la portée de sa relecture : c'est là qu'un chemin a sa
place. Et aucun drapeau nouveau : `generer_prompt.py` n'a pas d'option pour
inscrire un chemin, et il ne doit pas en avoir.

Ce fichier est précédé d'un marqueur « généré — ne pas éditer »,
et un `AGENTS.md` qui ne porte pas ce marqueur n'est **jamais** écrasé :
avertissement, fichier intact, code de retour inchangé. Ce fichier vit **hors du
dépôt** : il n'est ni versionné, ni concerné par `publier.py`, qui n'exporte que
l'arbre suivi.

**Les dossiers de l'instance** — dans le dépôt, `brouillon/` et l'archive
`IA/system/session-log/` ; dans le coffre parent, la mémoire `0-MEMOIRES/`
(mémoire des agents et chantiers clos) et `0-PERSONNELS/`
(profil-utilisateur) (§6, §7.1) — sont **créés s'ils manquent**
dans la cible, avec le README ou le gabarit de la source, mais **jamais vidés** :
c'est là que vit le travail de qui installe, et réinstaller ne doit rien lui
emporter. Si l'un d'eux porte déjà un contenu, il est laissé tel quel, et
l'aperçu le dit (« conservé »). Leur contenu n'est pas copié depuis la source non
plus : la mémoire et les journaux de l'auteur ne partent pas chez le copié.
`0-MEMOIRES/préférences/` est posé même vide — l'agent qui écrit sa première
préférence le trouve déjà là —, et `<nom-agent>/expériences/` naît à la première
leçon. Le coffre parent reste un dépôt
Git **distinct** (§7.1) : l'installateur y pose la liste blanche `.gitignore`
(§7.1) et l'initialise s'il n'est pas encore un dépôt, avec le nom du distant
déclaré dans `obsia.local.yml` — mais il ne pousse **jamais** de lui-même :
c'est le `post-commit` qui s'en charge (voir la section suivante).

**Fichiers exclus d'Obsidian** — l'installation ajoute le motif
`/^0-PROJETS\/[^\/]+\/code\//` au réglage « Fichiers exclus » d'Obsidian
(`.obsidian/app.json`, clé `userIgnoreFilters`), pour tenir le code d'un projet
hors de la recherche et du graphe du coffre (§7.3). Pour le retirer, ouvrir
Obsidian → Réglages → Fichiers et liens → Fichiers exclus, et supprimer la
ligne ; une réinstallation le repose. Le motif est écrit de façon idempotente,
et l'ancienne forme `0-PROJETS/*/code` est retirée au passage si elle traîne.
Rien n'est écrit si le coffre parent n'a pas de `0-PROJETS/`, ou si
`userIgnoreFilters` n'est pas une liste : on ne touche pas au réglage d'un
autre usage.

**Ce que la documentation officielle ne dit pas** : la syntaxe du motif — donc
si l'ancre `^` correspond bien au chemin qu'Obsidian compare. La promesse de
l'aide (masqué de la recherche, du graphe et des mentions non liées ; moins
visible dans le sélecteur rapide et les suggestions) reste à confirmer une
fois, à la main, sur un coffre réel :

1. poser un fichier sous `0-PROJETS/<projet>/code/` ;
2. chercher son nom dans Obsidian.

S'il n'apparaît ni dans la recherche, ni dans le graphe, ni dans les
suggestions de liens, le motif agit. Sinon, ajuster le motif dans les Fichiers
exclus. `installer.py` affiche cette recette après avoir posé le motif.

**Aucun lien symbolique de la cible n'est suivi**, ni en lecture ni en écriture.
Un `IA` déplacé ailleurs, une mémoire partagée : l'installation écrirait hors du
coffre qu'elle croit remplir. La zone concernée est sautée avec un
avertissement, et le reste de l'installation se poursuit — jusqu'à la réduction
des déclarations, qui n'a pas lieu au travers d'un lien.

La régénération s'arrête là aussi, et la vérification avec elle. Les deux
générateurs écrivent sous `IA/` — les quatre index — et dans le coffre parent —
les `sommaire.md` —, et le vérificateur lit à travers le même lien. Un lien, **où
qu'il soit** sous l'un de ces deux emplacements, suffit à tout arrêter : un
`IA/system` déplacé ailleurs, un `sommaire.md` de la mémoire partagé, pas
seulement un `IA` ou un dossier de mémoire entier. `installer.py` avertit alors,
ne régénère pas, ne vérifie pas, et l'annonce à la fin : il ne peut pas laisser
la dernière ligne dire que les index et les sommaires sont à jour après avoir
refusé d'y toucher.

**`--tout` veut dire catalogue complet, dans les deux modes.** En place, le
profil disparaît : c'est lui qui décrit un coffre réduit, et rien ne l'est plus.
Les index versionnés, eux, étaient déjà au catalogue complet et ne changent pas ;
c'est l'`AGENTS.md` qui repasse du profil réduit au catalogue entier.
En copie, il disparaît aussi, **et la copie a lieu** — la cible reçoit les
fichiers de tous les modules, y compris ceux que le profil écartait. Un
`--tout --installer` qui annonçait le catalogue entier et laissait la cible
vide ne le disait nulle part ; l'aperçu écrit donc « aucun — catalogue
complet » plutôt que de promettre un profil qui ne sera pas posé.

### Un modèle local — choisir un profil minimal

Le contexte qu'un harness charge avant la première question est le noyau du
contrat plus l'`AGENTS.md` engendré. L'`AGENTS.md` ne liste que les agents et
les skills des modules retenus : le profil est donc le levier, sans rien
réécrire. Mesures du 2026-10-02 :

| Profil | `AGENTS.md` | Avec le noyau (≈ 3 600 mots) |
| --- | --- | --- |
| catalogue complet | ≈ 3 800 mots | ≈ 7 400 mots, ≈ 10 000 tokens |
| `noyau` seul | ≈ 800 mots | ≈ 4 400 mots, ≈ 6 000 tokens |
| noyau, coffre Obsidian, documents, modèles locaux | ≈ 1 100 mots | ≈ 4 700 mots, ≈ 6 500 tokens |

**Cible retenue : un modèle d'au moins 16 000 tokens de contexte**, qui garde
alors plus de 9 000 tokens pour travailler avec un profil minimal. En dessous
(8 000), le noyau seul ne laisse pas assez de place : ce n'est pas une
configuration visée. Sur une machine à modèle local, ne retenir que les modules
dont on se sert, puis `python3 scripts/installer.py --appliquer` pour
régénérer l'`AGENTS.md`.

## Publication — `publier.py` (§13.5)

### Les quatre refus de `synchroniser`

**`synchroniser` refuse quatre cibles**, avant d'exporter quoi que ce soit, code
1 et motif en clair : la cible est la source, la contient, ou lui est inférieure ;
elle porte la marque d'un coffre vivant (`0-PROJETS`, `0-MEMOIRES`, `0-SAVOIRS`,
`0-PERSONNELS`, leurs anciens noms à tiret, `_MAINTENANCE` ou `.obsidian`) ; son
`origin` est celui de la source — c'est alors un clone du privé, pas du public ; elle n'est ni un
miroir d'OBSIA, ni un dépôt vierge. L'aperçu liste, une par une, les entrées de
la cible qui seront effacées. Et un lien symbolique de la cible est **défait par
`unlink()`**, jamais traversé : `rmtree` s'arrête sur un lien, et laisserait la
cible à moitié vidée.

Les quatre refus, dans l'ordre où ils tombent. La comparaison des `origin` porte
sur ce qui désigne le dépôt — hôte et chemin — et non sur l'URL écrite :
`git@hôte:propriétaire/dépôt.git` et `https://hôte/propriétaire/dépôt` sont le
même dépôt, et comparer les chaînes brutes laisserait cloner le privé en ssh
pour publier dessus. Le test « coffre vivant » a remplacé le contrôle qui portait
sur `mémoire/` : la mémoire n'est plus dans ce dépôt, elle a son propre dépôt
dans le coffre parent (§7.1) — mais tant que l'ancien `mémoire/` y traîne, la
distribution le vide comme le reste du privé.

Le quatrième refus est le seul qui n'énumère pas ce qu'il faut éviter mais ce
qu'il faut avoir : la cible doit être vierge ou porter
`IA/system/VAULT-CONTRACT.md`. **Vierge veut dire un dépôt qui n'a rien que son
`.git/`** — pas un dossier vide, qui n'est pas un dépôt : `publier.py` refuse
d'écrire dans une cible dont il ne peut pas dire ce qu'elle contenait. Un
`.gitignore` de reste, et ce n'est déjà plus un dépôt vierge. Le contrat, lui,
est la marque d'un miroir d'OBSIA, et la seule qui dise à la fois « c'est bien
notre publication » et « ce n'est pas le coffre vivant » ; un `README.md` ne dit
ni l'un ni l'autre, n'importe quel dépôt en a un. Sans ce refus, un dépôt à
personne — sans marque de coffre, sans `origin` comparable — était vidé sans que
rien ne l'ait vu venir.

### Le contrôle de fuite

Le contrôle de fuite vise des **valeurs**, jamais les mots qui les nomment :
le contrat parle de jetons et de mots de passe à longueur de page, et il doit
pouvoir continuer. Il bloque sur une adresse de courriel, une adresse IP privée,
un bloc de clé privée, un préfixe de jeton connu, ou un secret affecté à une
variable — `password` comme `mdp`, `mot de passe`, `jeton` ou `clé`, la valeur
pouvant porter des symboles, et des espaces dès qu'elle est entre guillemets.
Le mot-clé se reconnaît aussi dans un identifiant composé, d'un seul tenant :
`db_password`, `password_hash`, `mdp_hash` — une empreinte bcrypt ne se casse pas
moins qu'un mot de passe, elle se casse hors ligne. Un seul morceau après le
mot-clé, en revanche : `bearer_token_env_var` porte le **nom** d'une variable
d'environnement, et reste dehors. S'y ajoutent une clé secrète AWS nue, qui n'a
pas de préfixe reconnaissable puisque c'est justement pourquoi elle se recopie
telle quelle, et un nom d'hôte interne — `.lan`, `.local`, `.internal`,
`.home.arpa`, `.ts.net`.

Le contrôle ne regarde pas que des valeurs : il refuse aussi l'écriture d'un
**chemin de la machine** — la racine du coffre parent et celle du dépôt, que le
§13 interdit dans un fichier publié. Ces deux motifs ne s'écrivent pas dans la
table des motifs : ils se construisent à la publication depuis la racine passée
à `publier.py`, le dépôt publié et le dossier qui le contient. Ils ne portent
donc que sur la machine qui publie, et disparaissent quand aucune racine n'est
donnée — c'est ce qui permet de tester le contrôle sans dépendre du poste. Le
dépôt dont il s'agit est le **clone principal**, retrouvé par `git` : lancé
depuis un worktree, `publier.py` ne prendrait sinon pour coffre le dossier qui
range les worktrees, et signalerait la documentation qui décrit ce rangement.

Le chemin se reconnaît **écrit de toutes les façons**, parce que c'est écrit qui
le fait fuir, pas la façon : `file:///…` — une URL de fichier, la forme que
prend un chemin recopié d'un navigateur —, `//…`, et un chemin recomposé sous
un point de montage, `…/montage/<racine>`. Le motif ne regarde donc pas ce qui
précède. Deux exceptions, et deux seulement :

- le **chemin d'une URL http(s)** reste muet : `https://exemple.fr/<racine>`
  porte un chemin d'URL, pas une arborescence locale, et l'égalité serait une
  coïncidence. Le silence vaut par **occurrence**, pas par ligne : partout
  ailleurs sur la même ligne, le chemin est regardé — et c'est souvent là qu'il
  fuit, écrit en `file://` ;
- un **dossier de premier niveau** ne se pose pas comme motif. `/srv`, `/opt`,
  `/mnt` : une installation y tient avec le dépôt posé directement dedans, et le
  motif `/srv` se signalerait dans la moitié des textes qui parlent d'un serveur
  ou d'un montage. Un contrôle qui crie à tort est un contrôle qu'on force sans
  le lire — plutôt que de crier, il se taît. Le dépôt, lui, garde le sien : le
  nom du dépôt dans `/srv` désigne bien quelque chose.

C'est pour cette raison qu'aucun exemple de ce document n'écrit un chemin
complet et vraisemblable : une installation réelle à cet endroit serait bloquée
par le document qui explique la règle.

La même machine s'écrit aussi en `~` : quand la racine est sous le home de qui
publie, `~/…` est reconnu comme le chemin absolu. Un coffre qui *est* le home ne
fait pas de `~` tout court un motif, et `~/autre` n'est pas le coffre. Un chemin
**voisin** reste dehors : `…/coffre-notes`, `…-tests/OBSIA` ne sont pas la
machine, le motif exige que le chemin s'arrête, pas qu'il commence pareil.

Un **nom d'hôte nu** — un nom de machine sans domaine, le nom du dépôt privé —
n'a aucune forme qui le trahisse : seul l'utilisateur sait que c'en est un. Il
se déclare donc dans une **liste locale**, `~/.config/obsia/noms-interdits` (ou
le fichier que désigne `OBSIA_NOMS_INTERDITS`), un nom par ligne, `#` pour
commenter. Elle vit hors du dépôt, sans quoi elle publierait ce qu'elle
protège. Un nom s'y cherche entier et sans casse ; en dessous de quatre
caractères il est ignoré, parce que `ia` signalerait `IA/` dans chaque fichier —
et le rapport le dit. Un nom interdit **avertit, il ne refuse pas** : la liste
doit retenir des identités, mais elle frappe des mots — un mot banal peut s'y
trouver — et un avertissement n'a pas besoin de converger. Le contrôle le
signale donc ligne par ligne, sans bloquer, et `--forcer` n'a pas à le
franchir : il n'y a rien à forcer. Le rapport dit aussi quand la liste est
absente : « aucune trouvaille » ne vaut alors rien pour les noms nus — liste
absente, aucun nom contrôlé. La même liste nourrit la garde de pré-commit
`.githooks/pre-commit.d/20-noms-interdits`, qui avertit au moment où la faute
s'écrit, sur les seules lignes ajoutées, puis laisse le commit passer.

La phrase de passe **sans guillemets** est attrapée sous condition de position :
mot-clé fort (`password`, `secret`, `mdp`, `mot de passe`) en tête de ligne,
éventuellement après une puce, et une affectation qui court jusqu'au bout de la
ligne. C'est la seule forme qui distingue `secret: correct horse battery staple`
de la prose — « … pas un secret : une note du coffre parent la porte » a le même
mot-clé au milieu de la ligne. La limite est donc assumée : une valeur à espaces
qui ne commence pas la ligne passe sous le contrôle, et c'est le prix à payer
pour que la prose reste publiable.

Ce qui **ne doit pas** se signaler fait partie du contrôle autant que ce qu'il
attrape : `obsia.local.yml`, `AGENTS.local.md` et `CLAUDE.local.md` sont des
fichiers, pas des machines, et les quarante caractères hexadécimaux d'une
empreinte de commit citée dans une note ne sont pas une clé. Chaque motif a son
témoin négatif dans les tests, faute de quoi il finirait par crier sur la prose
qu'il est censé laisser passer.

Le contrôle dit aussi ce qu'il **n'a pas pu relire** — un binaire, un fichier
qui n'est pas de l'UTF-8 —, en les comptant et en les nommant : « aucune
trouvaille » sur un fichier qu'on n'a pas ouvert ne dit rien de ce fichier. Un
`.svg` est du texte, et se relit comme tel. Et il passe **après la
régénération**, sur l'export final : les générateurs réécrivent les index et les
sommaires, et c'est cet arbre-là qui partira — contrôler avant reviendrait à
relire un état qui n'existe plus.

`--forcer` passe outre les trouvailles, sauf **quatre** : une clé privée, qui ne
se révoque pas mais se remplace ; un jeton connu, qui se révoque — encore
faut-il le faire avant qu'il ait servi ; et les deux **chemins de la machine**,
la racine du coffre parent et celle du dépôt, qui ne sont pas des valeurs : un
chemin ne se révoque pas, il se retire du fichier. Ces deux motifs ne sont pas
écrits dans la table des motifs — ils naissent de la racine passée à la
publication, le dépôt publié et le dossier qui le contient, et n'existent donc
que sur la machine qui publie : absents quand aucune racine n'est donnée, ils ne
font dépendre aucun test du poste. Pour les autres catégories, il publie,
et **écrit la dérogation et ses catégories dans le message de commit** : une
publication forcée qui ne laisse aucune trace est indiscernable d'une
publication propre. S'en servir sans avoir lu la trouvaille, c'est se priver du
seul filet qui reste une fois l'historique public. Ce filet-là vise les valeurs
à **forme reconnaissable** — un jeton, une clé, une adresse IP : pour un **nom**
de la liste locale, il n'en existe aucun. Un nom est signalé deux fois — par la
garde de pré-commit au moment de l'écriture, puis par `publier.py` au moment de
la publication — et c'est dans ce rapport local, et nulle part ailleurs, que
survit le détail `fichier:ligne` : le message de commit, lui, n'en porte que le
nombre.

Le même contrôle tourne sur **le titre et la description d'une pull request** —
à chaque ouverture, modification, poussée ou réouverture : une description se
corrige sans pousser de commit, et c'est le texte corrigé qui paraît —, par
`publier.py --controler-texte` : ils paraissent sur le dépôt public alors que
le contrôle d'arbre ne les verra jamais, puisque la pull request n'est pas dans
l'arbre. Le texte vient de l'entrée standard ; en vérification continue, GitHub
le fournit par des variables d'environnement, et jamais en l'écrivant dans le
script — une description de PR qu'on croit inoffensive suffirait, sinon, à y
faire passer une commande. Les motifs, les régimes et `--forcer` sont ceux de
l'arbre, à deux réserves près : la liste locale des noms interdits peut manquer
en CI, et le contrôle ne porte alors que sur les valeurs à forme
reconnaissable ; et les **chemins de la machine**, construits depuis la racine
publiée, n'y sont pas contrôlés du tout — un chemin absolu écrit dans une
description de PR passe donc ce mode sans être vu.
`--cible` n'est pas requis dans ce mode : il n'y a rien à copier, seulement un
texte à juger.
