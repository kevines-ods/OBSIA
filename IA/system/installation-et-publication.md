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

**`AGENTS.md`** — l'installation écrit également, à côté de leur coffre effectif,
le fichier que les harness lisent d'eux-mêmes : `<dossier parent>/AGENTS.md`.
Autrement dit, la cible d'installation désigne le dossier `OBSIA/` : `AGENTS.md`
atterrit un cran au-dessus, à la racine du coffre que l'agent ouvre. Les deux
modes l'écrivent, chacun pour le coffre effectif — celui des deux qui reçoit
l'installation. Son contenu est celui de `scripts/generer_prompt.py` : index,
méthode, profil retenu. Il est précédé d'un marqueur « généré — ne pas éditer »,
et un `AGENTS.md` qui ne porte pas ce marqueur n'est **jamais** écrasé :
avertissement, fichier intact, code de retour inchangé. Ce fichier vit **hors du
dépôt** : il n'est ni versionné, ni concerné par `publier.py`, qui n'exporte que
l'arbre suivi.

**Les trois dossiers de l'instance** — `mémoire/`, `brouillon/` et
`IA/system/session-log/` — sont **créés s'ils manquent** dans la cible, avec le
README de la source, mais **jamais vidés** : c'est là que vit le travail de qui
installe, et réinstaller ne doit rien lui emporter. Si l'un d'eux porte déjà un
contenu, il est laissé tel quel, et l'aperçu le dit (« conservé »). Leur contenu
n'est pas copié depuis la source non plus : la mémoire et les journaux de
l'auteur ne partent pas chez le copié.

**Aucun lien symbolique de la cible n'est suivi**, ni en lecture ni en écriture.
Un `IA` déplacé ailleurs, une `mémoire/` partagée : l'installation écrirait
hors du coffre qu'elle croit remplir. La zone concernée est sautée avec un
avertissement, et le reste de l'installation se poursuit — jusqu'à la réduction
des déclarations, qui n'a pas lieu au travers d'un lien.

La régénération s'arrête là aussi, et la vérification avec elle. Les deux
générateurs écrivent sous `IA/` et `mémoire/` — les quatre index, les
`sommaire.md` — et le vérificateur lit à travers le même lien. Un lien, **où
qu'il soit** sous l'un de ces deux dossiers, suffit à tout arrêter : un
`IA/system` déplacé ailleurs, un `sommaire.md` de la mémoire partagé, pas
seulement un `IA` ou une `mémoire/` entier. `installer.py` avertit alors, ne
régénère pas, ne vérifie pas, et l'annonce à la fin : il ne peut pas laisser la
dernière ligne dire que les index et les sommaires sont à jour après avoir
refusé d'y toucher.

**`--tout` veut dire catalogue complet, dans les deux modes.** En place, le
profil disparaît : c'est lui qui décrit un coffre réduit, et rien ne l'est plus.
En copie, il disparaît aussi, **et la copie a lieu** — la cible reçoit les
fichiers de tous les modules, y compris ceux que le profil écartait. Un
`--tout --installer` qui annonçait le catalogue entier et laissait la cible
vide ne le disait nulle part ; l'aperçu écrit donc « aucun — catalogue
complet » plutôt que de promettre un profil qui ne sera pas posé.

## Publication — `publier.py` (§13.5)

### Les cinq refus de `synchroniser`

**`synchroniser` refuse cinq cibles**, avant d'exporter quoi que ce soit, code
1 et motif en clair : la cible est la source, la contient, ou lui est inférieure ;
elle porte la marque d'un coffre vivant (`.obsidian`, `-SAVOIRS`, `-PROJETS`) ;
sa `mémoire/` porte autre chose que ce que la distribution y laisse ; son
`origin` est celui de la source — c'est alors un clone du privé, pas du public ;
elle n'est ni un miroir d'OBSIA, ni un dépôt vierge. L'aperçu liste, une par
une, les entrées de la cible qui seront effacées. Et un lien symbolique de la
cible est **défait par `unlink()`**, jamais traversé : `rmtree` s'arrête sur un
lien, et laisserait la cible à moitié vidée.

Les cinq refus, dans l'ordre où ils tombent. La comparaison des `origin` porte
sur ce qui désigne le dépôt — hôte et chemin — et non sur l'URL écrite :
`git@hôte:propriétaire/dépôt.git` et `https://hôte/propriétaire/dépôt` sont le
même dépôt, et comparer les chaînes brutes laisserait cloner le privé en ssh
pour publier dessus. Ce que la distribution laisse dans `mémoire/` est exactement
trois fichiers : son `README.md`, le `profil-utilisateur.md` que l'installeur y
pose, et `sommaire.md`. Le sommaire y est parce que `publier.py` le régénère et
le dépose dans l'export : une cible déjà publiée le porte, et le refuser
interdirait de republier sur sa propre publication. Tout le reste — une note, un
sous-dossier — n'est pas le nôtre, et « publier » l'effacerait sans retour.

Le cinquième refus est le seul qui n'énumère pas ce qu'il faut éviter mais ce
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

Un **nom d'hôte nu** — un nom de machine sans domaine, le nom du dépôt privé —
n'a aucune forme qui le trahisse : seul l'utilisateur sait que c'en est un. Il
se déclare donc dans une **liste locale**, `~/.config/obsia/noms-interdits` (ou
le fichier que désigne `OBSIA_NOMS_INTERDITS`), un nom par ligne, `#` pour
commenter. Elle vit hors du dépôt, sans quoi elle publierait ce qu'elle
protège. Un nom s'y cherche entier et sans casse ; en dessous de quatre
caractères il est ignoré, parce que `ia` signalerait `IA/` dans chaque fichier —
et le rapport le dit. Un nom interdit **ne se force pas** : c'est l'utilisateur
qui l'a déclaré, pas une heuristique qui a pu se tromper. Le rapport dit aussi
quand la liste est absente : « aucune trouvaille » ne vaut alors rien pour les
noms nus. La même liste nourrit la garde de pré-commit
`.githooks/pre-commit.d/20-noms-interdits`, qui refuse la faute au moment où
elle s'écrit, sur les seules lignes ajoutées.

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

`--forcer` passe outre les trouvailles, sauf deux : une clé privée, qui ne se
révoque pas mais se remplace, et un jeton connu, qui se révoque — encore
faut-il le faire avant qu'il ait servi. Pour les autres catégories, il publie,
et **écrit la dérogation et ses catégories dans le message de commit** : une
publication forcée qui ne laisse aucune trace est indiscernable d'une
publication propre. S'en servir sans avoir lu la trouvaille, c'est se priver du
seul filet qui reste une fois l'historique public.
