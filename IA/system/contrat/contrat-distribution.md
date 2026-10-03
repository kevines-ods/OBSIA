---
schema: 1
kind: contract
name: contrat-distribution
description: Détail des modules, de l'installation et de la publication : modules, sondes, profil, deux modes, public et privé, contrôle de fuite.
module: noyau
---

# Annexe du contrat — distribution

> **À lire avant d'installer, de publier ou de synchroniser ; de toucher `installer.py` ou `publier.py` ; d'écrire un module ou une sonde ; d'écrire un skill qui charge le skill d'un autre module ; d'écrire dans un fichier publié un chemin vers une zone non publiée.** Annexe du contrat (`../VAULT-CONTRACT.md`).
> Elle précise, elle n'ajoute aucune règle : toute règle qu'on peut enfreindre
> sans avoir rien chargé est aussi au noyau, et en cas de contradiction le
> noyau fait foi — l'annexe est alors à corriger. La correspondance avec l'ancien
> contrat est suivie dans `registre.md`, document de travail non normatif.

## 13. Modules, installation et publication

Le coffre est un **catalogue**, pas une livraison. Tout y est déclaré ; rien
n'oblige à tout retenir. Un coffre installé sur une machine sans Docker
n'embarque pas les skills qui pilotent des conteneurs — non pour économiser des
octets, mais parce qu'un skill qui ne peut pas s'exécuter coûte plus cher que
son absence : il occupe le contexte, se propose au mauvais moment, et échoue
là où il aurait fallu qu'il se taise.

### 13.1 Un module

Un **module** regroupe ce qui n'a de sens qu'ensemble. Il vit dans
`IA/system/modules/<nom>.md` et porte le frontmatter suivant :

| Champ | Type | Obligatoire | Notes |
| --- | --- | --- | --- |
| `schema` | entier | oui | comme partout, actuellement `1` |
| `kind` | `module` | oui | |
| `name` | texte | oui | identique au nom du fichier, et **unique dans tout le coffre parent** comme n'importe quelle note (§6) — un module `sauvegardes` à côté d'un skill `sauvegardes` casse les rétroliens |
| `description` | texte | oui | une ligne |
| `essentiel` | booléen | oui | `true` = toujours installé, aucune question posée |
| `question` | texte | si non essentiel | ce que l'installeur demande. Un module non essentiel sans question ne pourrait jamais être choisi. |
| `sondes` | liste | non | ce que la machine peut constater seule (13.2) |
| `requiert` | liste | non | modules entraînés par celui-ci |

Le corps dit ce que le module apporte et **pourquoi le découpage tombe là** :
c'est la seule information qu'on ne retrouve pas en listant ses fichiers.

Réciproquement, **tout agent, skill, MCP et tâche déclare son `module`** (§5).
Un fichier sans module est inclassable : l'installeur ne saurait ni le retenir
ni l'écarter. `scripts/verifier_coffre.py` le refuse.

Un module reste **libre de ses dépendances mais pas de ses renvois** : si un
skill de `A` dit de charger un skill de `B`, `A` doit entraîner `B` **ou**
écrire, à l'endroit du renvoi, quoi faire quand `B` n'est pas installé — en
nommant le module. Sinon la consigne tombe dans le vide chez qui n'a installé
que `A`. Le repli écrit convient quand entraîner `B` imposerait un module
disproportionné : on ne force pas la relecture sur quiconque construit. Le
vérificateur l'avertit ; c'est un avertissement et non une erreur, pour la même
raison qu'au §11 — la détection repose sur le verbe employé.

### 13.2 Les sondes — ce que la machine dit d'elle-même

Une sonde est **déclarative**, et son vocabulaire tient en quatre formes :

| Forme | Vrai quand |
| --- | --- |
| `commande:<nom>` | le binaire est dans le `PATH` |
| `fichier:<chemin>` | le chemin existe (`~` développé) |
| `distribution:<id>` | `ID` ou `ID_LIKE` de `/etc/os-release` correspond |
| `parent:<nom>` | le dossier existe à côté du dépôt — donc dans le coffre parent |

Il n'y en a pas de cinquième, et surtout aucune qui exécuterait une commande
arbitraire : un catalogue dont les fichiers déclenchent du code devient un
vecteur d'exécution, et on installe justement un catalogue qu'on n'a pas encore
lu. Aucune sonde n'ouvre le réseau (§4).

**Une sonde ne décide jamais seule.** Elle constate que `docker` est installé ;
elle ne sait pas si l'utilisateur veut gérer des conteneurs. Elle propose une
réponse par défaut, la question tranche. Un module sans sonde n'est pas un
module mal fait : il est simplement indécidable depuis la machine, et c'est
honnête de le dire plutôt que de deviner.

### 13.3 Le profil — `obsia.local.yml`

Le profil dit quels modules sont retenus **sur cette machine**. Il vit à la
racine du dépôt, **n'est pas versionné**, et n'est pas une des trois zones
d'écriture du §2 : ce n'est pas un agent qui l'écrit, c'est l'installeur.

**Absence de profil = catalogue complet.** C'est l'état du dépôt de
distribution, et l'état sous lequel la CI vérifie le coffre — sans quoi la CI
ne contrôlerait qu'une installation particulière, et les modules écartés
pourriraient sans que rien ne le signale.

Le profil ne décrit qu'une **sélection**. Il ne contredit donc jamais un
frontmatter, et la règle du §11 — le frontmatter a raison — tient sans
exception : le frontmatter dit ce qui existe, le profil dit ce qu'on en retient.

Il ne filtre **que ce qui n'est pas versionné** : le prompt système et l'`AGENTS.md`
engendré. Les index (`IA/README.md`, les quatre `IA/system/*-index.md`) sont
versionnés, donc canoniques : ils montrent le catalogue entier, sur toutes les
machines (§11). Une colonne « retenu ici » y serait un mensonge d'avance — elle
dirait « oui » partout sur une machine au catalogue complet, et ferait diverger
deux clones du même dépôt.

### 13.4 Deux modes d'installation

`scripts/installer.py` sonde, montre, demande, puis écrit — et seulement avec
`--appliquer` : l'aperçu du §2 n'est pas décoratif.

| Mode | Ce qui se passe | Quand le choisir |
| --- | --- | --- |
| **en place** | rien n'est déplacé ni supprimé ; seuls les fichiers **non versionnés** sont réduits au profil — le prompt système et `AGENTS.md`. Les index versionnés (`IA/README.md`, les quatre `*-index.md`) restent au catalogue complet | on utilise le clone tel quel, et on veut pouvoir changer d'avis d'une commande |
| **copie** | seuls les fichiers retenus atterrissent dans le coffre cible, et les déclarations d'agents y sont réduites pour rester cohérentes | on veut un coffre réellement minimal, versionné pour lui-même |

La différence n'est pas cosmétique. **En place, les frontmatters ne sont jamais
réécrits** : les fichiers écartés sont toujours là, un agent qui les déclare ne
déclare rien d'absent. **En copie, ils le sont** : les fichiers écartés manquent
réellement, un agent qui les déclarerait ferait échouer le vérificateur de la
cible. Une tâche visant un agent absent est retirée pour la même raison.

Trois règles protègent le travail de qui installe, et tiennent dans les deux
modes : l'installation **ne vide jamais** `mémoire/`, `brouillon/` ni
`IA/system/session-log/` de la cible ; elle **n'écrase jamais** un
`AGENTS.md` qui ne porte pas son marqueur « généré » ; elle **ne suit aucun
lien symbolique** de la cible. `--installer` ne touche jamais à la source, et
`--tout` veut dire catalogue complet dans les deux modes.

Le détail — `AGENTS.md`, dossiers de l'instance, liens, `--tout` — vit dans
`IA/system/installation-et-publication.md`, **à lire avant de lancer
`installer.py` avec `--appliquer`**.

Revenir au catalogue complet : `python3 scripts/installer.py --tout --appliquer`
— le profil disparaît, et l'`AGENTS.md` repasse au catalogue entier. Un
`git checkout` ne suffit plus : les index, eux, étaient déjà canoniques.

### 13.5 Public et privé

Le dépôt de travail est **privé** : il porte la mémoire, les carnets, les anciens logs de session et
le profil de son propriétaire. Le dépôt **public** est la distribution : le même
coffre, moins ce qui décrit une personne ou une machine.

**Le privé fait foi.** Il n'y a pas deux sources de vérité : `scripts/publier.py`
dérive la seconde de la première, et refuse de publier ce qu'il ne sait pas
relire. Il exporte l'arbre suivi par Git à `HEAD` — jamais le répertoire de
travail, parce que ce qui n'est pas suivi n'a pas été relu —, vide `mémoire/`,
`IA/system/session-log/`, `brouillon/` et `.archive/` de tout sauf leurs
`README.md`, régénère, vérifie, passe un contrôle de fuite sur l'export final, et
n'écrit dans la cible qu'avec `--appliquer`. Il ne pousse jamais.

**`synchroniser` refuse cinq cibles** avant d'exporter quoi que ce soit —
jamais la source ni ce qui la contient, jamais un coffre vivant, jamais un
clone du privé, jamais une cible qui n'est ni vierge ni un miroir d'OBSIA. Le
détail des refus vit dans `IA/system/installation-et-publication.md`, **à lire
avant de lancer `publier.py` avec `--appliquer`**.

Le sens unique n'est pas qu'une précaution, c'est **ce qui crée la fenêtre de
validation**. Le privé est l'atelier : une fonctionnalité y naît, s'y éprouve
sur des séances réelles, et ne franchit la frontière que le jour où on lance
`publier.py`. Rien ne part tout seul — pas de poussée automatique, pas de
synchronisation de fond. Le public ne reçoit donc jamais qu'un état que
quelqu'un a jugé bon, et la durée du test est celle qu'on veut bien lui
laisser.

Un flux bidirectionnel aurait supprimé cette fenêtre en même temps que la
frontière : ce qui circule dans les deux sens finit par circuler tout seul.

La contrepartie s'assume : **une correction proposée sur le public se reporte
à la main dans le privé.** L'inverse — publier depuis le public et y rapatrier
le privé — aurait exposé la mémoire au premier oubli, et un contenu privé entré
dans un historique public ne se rattrape pas (§7.3.1).

**Rendre un dépôt privé ne dépublie pas son passé.** Le basculement cache les
poussées à venir, pas l'historique déjà servi : ce qui a été public le reste
chez qui l'a cloné. C'est une raison de plus de n'avoir jamais rien mis de
secret dans le coffre, et non un filet auquel se fier après coup. Le dépôt
public, lui, part propre par construction : `publier.py` écrit l'arbre exporté
dans un clone neuf, sans y verser l'historique du privé.

**Un fichier publié ne cite pas un chemin qui ne sera pas publié.** Les zones
vidées — `mémoire/`, `brouillon/`, `.archive/`, `IA/system/session-log/` — ne
se désignent pas par leur chemin depuis `IA/` ni depuis la racine : le lien
mènerait nulle part dans la distribution, et l'export échouerait loin de
l'endroit où la faute a été écrite. Ce n'est pas une interdiction d'y
**renvoyer** : nommer la note suffit, et c'est déjà ce que le §7.5 demande pour
les rétroliens — un lien par nom survit aux déplacements, un lien par chemin
casse. Deux exceptions, parce qu'elles survivent : les `README.md` de ces
zones, et `mémoire/profil-utilisateur.md`, que l'installeur et le publieur
réécrivent tous deux en gabarit vide. `scripts/verifier_coffre.py` contrôle la
règle dans le dépôt privé, où la faute s'écrit.

Le contrôle de fuite vise des **valeurs**, jamais les mots qui les nomment :
une adresse de courriel, une adresse IP privée, un bloc de clé privée, un
préfixe de jeton connu, un secret affecté à une variable, un nom d'hôte
interne — et tout nom de la **liste locale des noms interdits**, tenue hors du
dépôt, seul moyen d'attraper un nom de machine qui n'a pas de forme de
domaine. Il passe sur l'export final, après régénération, et dit ce qu'il n'a
pas pu relire. Deux régimes, deux traitements : les valeurs à **forme
reconnaissable** (clé privée, jeton, IP privée, courriel, nom d'hôte à
domaine) refusent la publication. `--forcer` en publie malgré tout, sauf deux
qu'il ne franchit **jamais** : une clé privée, qui ne se révoque pas mais se
remplace, et un jeton connu, qui se révoque — encore faut-il le faire avant
qu'il ait servi. Pour les autres catégories, il publie et écrit la dérogation
dans le message de commit. Un nom de la **liste locale** n'a pas de forme : la
liste retient des identités, mais frappe des mots, et un avertissement n'a pas
besoin de converger. Il est donc **signalé ligne par ligne en avertissement,
sans bloquer**, et `--forcer` ne sert pas contre lui — il n'y a rien à forcer.
Un agent qui reçoit cet avertissement le rapporte à l'utilisateur : il ne le
tait pas. Liste absente = aucun nom contrôlé ; « aucune trouvaille » ne dit
alors rien des noms nus. Les motifs exacts et leurs limites :
`IA/system/installation-et-publication.md`.
