---
schema: 1
kind: mcp
name: ecrivain-du-coffre
description: Écrire dans le coffre parent — un carnet de chantier, une note rangée, une note complétée — pour un harnais pilotant un modèle local : le geste passe la porte (§7.3) avant que le socle ne l'écrive, un acte et un commit à la fois, avec son aperçu daté. C'est la fiche qui nomme l'écrivain comme écrivant *pour un harnais pilotant un modèle local*, condition d'entrée de l'exception bornée du §7.4. À charger avec le skill `delegation-locale` quand un travail confié à un harnais pilotant un modèle local doit écrire, et avec `livraison-git` pour soumettre le commit à revue.
module: coffre-obsidian
type: tool
transport: stdio
permission: elevated
---

# MCP — Écrivain du coffre

Un serveur MCP qui fait **écrire le coffre parent par un harnais pilotant un
modèle local**. Le modèle ne voit ni le dépôt, ni un shell, ni le disque : il
propose un **geste** — poser un carnet, ranger une note, la compléter, ou lire
l'inventaire des notes — et le socle d'écriture le juge, l'écrit, le commite,
ou le refuse.

Le modèle dit **quoi** écrire, jamais **où** : le chemin, le nom, la date et le
frontmatter sont calculés par l'écrivain. Un geste = un acte = un commit qui
porte exactement ses fichiers.

Code : `serveur/mcp_ecrivain.py` (le point d'entrée MCP), `serveur/ecrivain.py`
(le geste « carnet »), `serveur/gestes_des_notes.py` (ranger, compléter),
`serveur/porte_entree.py` (la matrice §7.3 et les gardes),
`serveur/socle_ecriture.py` (verrou, préalable, marque du commit, retour en
arrière). Bibliothèque standard seule, aucun accès réseau.

## Pourquoi cette fiche existe

Le §7.4 exige, **avant d'écrire**, un aperçu daté dans `_MAINTENANCE/` — sauf
pour l'**outil déclaré qui écrit pour un modèle local piloté**. Cette fiche
**déclare** cet outil : elle le nomme, et elle est la **condition d'entrée** de
l'exception. Sans
elle, l'écrivain reste dans le droit commun — l'aperçu d'abord, l'écriture ensuite —
et n'a rien à faire sur un coffre réel.

L'exception ne dispense de rien d'autre. Ce qu'elle ouvre se paie des trois
garanties du §7.4, que le socle tient déjà :

- **un acte, un commit** portant exactement les fichiers de l'acte — jamais
  `git commit -a` ;
- **un seul écrivain à la fois** : verrou d'écriture, et second écrivain
  signalé ;
- **à tout refus, l'acte est défait** et consigné — rien n'est écrit à moitié.

## Permission — `elevated`

L'écrivain écrit **dans le coffre parent**, **hors du dépôt** : ses actes visent des
fichiers qui ne sont pas dans ce dépôt OBSIA, et aucun `git revert` d'OBSIA ne les
rattrape. C'est le critère du §5 lu à la lettre — le niveau suit la **cible**, pas la
distance ni la présence d'un réseau — et c'est le motif qui met déjà `coffre-parent`,
qui écrit dans le même espace, en `elevated`.

L'élévation ne change rien au jugement : les actes restent **versionnés** dans le
dépôt de données du coffre — un acte, un commit, qu'un `revert` du coffre défait — et
le socle garde ses trois garanties. Elle dit seulement que l'outil écrit **au-delà**
du dépôt qui le décrit.

## Ce qu'il expose

| Geste | Ce qu'il fait | Zone |
| --- | --- | --- |
| `ecrire_un_carnet` | poser un carnet de chantier à partir d'un sujet | `0-PROJETS/<chantier>/carnets/` |
| `ranger_une_note` | classer une note brute d'`0-EN-VRAC` dans sa zone | selon la matrice §7.3 |
| `completer_une_note` | tenir une note sur place, au fil de l'eau | zones tenues à la main |
| `notes_du_coffre` | lire l'inventaire (nom, dossier, état) sans rien écrire | — |

## Le serveur

Le point d'entrée MCP est `serveur/mcp_ecrivain.py` : un serveur **stdio**,
JSON-RPC 2.0 délimité par des fins de ligne, bibliothèque standard seule. Il
expose les quatre gestes du tableau ci-dessus — un outil par geste, rien de plus.

Le coffre visé vient de la variable d'environnement `OBSIA_COFFRE`, **jamais du
message** : aucun outil ne prend de chemin, si bien que le modèle ne *peut pas*
désigner où écrire. Si la variable manque ou est vide, ou si elle ne désigne pas
un dépôt de données, l'écrivain **refuse** — il ne se rabat sur aucun autre
coffre. Un refus est rendu **avec son motif**, et rien n'est écrit.

`IA/MCP/mcp.example.json` porte l'entrée correspondante, **à titre d'exemple** :
les chemins y sont des repères, pas des valeurs — la configuration réelle vit
hors du dépôt (§13).

L'agent **`assistant`** le déclare (`IA/agents/assistant.md`, liste `mcp`) :
c'est lui qui confie une écriture à un harnais pilotant un modèle local, et la
déclaration lève l'avertissement « déclaré par aucun agent » du vérificateur. Le
jour où un autre agent doit écrire par ce MCP, c'est sa liste qu'on touche, pas
cette fiche.

## Rien ne l'attache : le serveur reste retirable

Le serveur est un **maillon déployable**, jamais une pièce du coffre : sa
déclaration vit dans la configuration **hors dépôt** (§13), et le fichier du
serveur reste dans ce dépôt. Il est **retirable** sans rien casser, par deux
gestes :

- **retrait logique** — `enabled: false` : `opencode mcp list` le montre
  `disabled` (le serveur n'est plus lancé), la carte des douze outils intégrés que
  rend `opencode debug agent build` reste **la même** ;
- **retrait franc** — le bloc `mcp` supprimé : `opencode mcp list` affiche alors
  `No MCP servers configured`, et le harness tient toujours.

Le retrait est **réversible** : remettre l'entrée le rebranche (`connected`) —
**avec** `OBSIA_COFFRE`, sans quoi le serveur refuse toute écriture. Procédure,
sorties exactes et constat : `IA/system/adaptateurs-harness/opencode.md` §10.

Un point a été **tranché** (2026-10-11), et il se lit ici : privé de l'outil, le
modèle **s'arrête et le dit** n'était tenu que sur la **capacité** (aucune
écriture possible), **pas sur la parole** — le petit modèle annonce des succès
qu'il n'obtient pas. La consigne ne l'en empêche pas de façon fiable, et le §8
du contrat sépare l'**évidence** de la **synthèse produite par un agent**, quand
le §7.4 prend l'acte — un commit — pour trace : **la parole du modèle ne prouve
rien**. Exiger d'elle une
garantie serait se donner une preuve qui n'en est pas une. Le critère ne porte
donc plus sur ce que le modèle **dit**, mais sur ce qu'on **constate** — voir la
section suivante.

## Le constat d'acte — ce qui prouve, c'est le disque

Exiger de la parole du modèle qu'elle soit fiable serait se donner une preuve
qui n'en est pas une. Éprouvé le 2026-10-11 : privé de tout outil d'écriture, le
petit modèle annonce un succès qu'il n'obtient pas **six fois sur onze tirages
libres** — jamais une écriture. Et aucune consigne ne l'en empêche de façon
fiable : une liste **factuelle** de ses capacités le laisse mentir 1 fois sur 3,
une **règle de sincérité** seule 3 fois sur 3, des outils d'écriture **visibles
mais refusés** 2 fois sur 3. La seule variante qui tient lui **nomme la réponse**
— c'est le soufflage qu'on s'interdit.

Le critère porte donc sur ce qu'on **constate**, pas sur ce qu'il **dit**.
`scripts/constat_acte.py` lit le journal de la session et le confronte à l'état
réel, en gardant la distinction visible jusque dans le code :

- le **constat dur** — `git rev-parse`, `git status`, un **condensé du contenu**
  de chaque fichier modifié, le disque — est la **preuve** : si aucun octet n'a
  bougé, aucune écriture n'a eu lieu, quoi qu'en dise le modèle. Comparer les
  seuls **noms** ne suffirait pas : une réécriture du même fichier passerait pour
  « rien n'a bougé » ;
- le **repérage des annonces** dans le texte est **lexical, donc faillible** : il
  ne sert qu'à nommer la phrase à confronter au coffre, jamais à établir les
  faits — deux formulations ont échappé au premier jet, et c'est pourquoi elles
  sont en régression dans les tests.

Quatre verdicts, **rendus par l'état du coffre, jamais par la seule phrase** :
`ANNONCE NON TENUE` — le coffre n'a pas bougé (ni tête, ni noms, ni contenu) et
aucun geste n'a pu écrire (sortie `1`) ; `ANNONCE TENUE` — le coffre a bougé
**depuis un relevé avant fiable** sous un geste qui peut écrire, et si l'annonce
nomme un fichier son existence sous le coffre le corrobore ; `RIEN ANNONCÉ` —
rien à réfuter ; `À CONTRÔLER` (sortie `3`) — la preuve manque (coffre hors de
`git`, **relevé avant absent**, journal tronqué), plutôt qu'une accusation sur un
doute ; sans relevé avant, un geste suspect **ne blanchit jamais**. À lancer par
le chef d'équipe après une session confiée à un harnais pilotant un modèle
local.

Éprouvé sur les onze sessions réelles : six `ANNONCE NON TENUE`, cinq
`RIEN ANNONCÉ`. Le critère 5 de la phase 6 est tenu sur cette formulation.

## L'appel déporté — une clé dédiée, en commande forcée

Un harnais qui ne tourne pas sur la machine du coffre n'a pas d'autre porte que
`ssh`. On ne lui ouvre pas de session : on lui donne une **clé dédiée à ce seul
appel**, dont la ligne d'`authorized_keys` ne sait faire qu'une chose — lancer le
point d'entrée, sur le coffre visé, et rien d'autre.

```
restrict,no-pty,no-agent-forwarding,from="<adresse-de-l-appelant>",command="env OBSIA_COFFRE='<coffre-visé>' <interpréteur> <entrée-de-l-écrivain>" <clé-publique> <nom-de-la-clé>
```

- `command=` — seule cette commande tourne : **ce que le client demande est
  ignoré**. On y nomme l'entrée, et **jamais un shell** : ni `sh -c`, ni shell de
  connexion détourné, ni commande composée ;
- la valeur d'`OBSIA_COFFRE` est **entre guillemets simples** : un chemin peut
  contenir une espace, et sans eux la commande serait coupée en deux ;
- `restrict` couvre déjà `no-pty`, `no-agent-forwarding`, le transfert de port et
  l'X11 ; les options explicites restent écrites pour que l'intention se lise même
  sans connaître `sshd` ;
- **`from=` est obligatoire** : c'est lui qui **borne la clé** — volée, elle ne
  servira que depuis l'adresse de l'appelant ;
- la commande passe par `env` pour que l'affectation ne dépende pas de la syntaxe du
  shell. Point fort : `env` **écrase toute valeur héritée**, donc un réglage
  d'environnement ne peut pas détourner l'appel vers un autre coffre ;
- pour autant, la commande reste **lancée par le shell de connexion du compte** : ce
  shell doit rester présent et exécutable, sinon l'appel forcé cesse ;
- le coffre visé est posé **côté serveur** : le client ne le nomme jamais, et aucun
  message MCP ne le porte.

La clé se traite comme un laissez-passer :

- **sans phrase de passe**, parce qu'un harnais n'en saisit pas : c'est un choix
  assumé, et ce sont `from=`, `restrict` et `command=` qui le rendent tenable — c'est
  aussi pourquoi `from=` n'est pas facultatif ;
- la **privée** reste en `0600`, **hors dépôt**, **hors sauvegarde** et **hors
  synchronisation** : elle ne quitte pas l'appelant et ne se recopie nulle part ;
- **pour révoquer**, on retire la ligne d'`authorized_keys` : rien d'autre à faire,
  aucun état à nettoyer ailleurs.

Ce que la porte **ne** donne pas, et qui se revérifie à chaque déploiement :

- **aucune session** — ni shell, ni pty, ni transfert : la clé ne sert qu'à cet
  appel, et jamais à se connecter ;
- **aucun sous-système** — une demande `sftp` ou `scp` n'aboutit pas : la clé ne sait
  pas transporter de fichier ;
- **rien ailleurs** — la même clé est refusée sur un autre compte et sur une autre
  machine ;
- **rien d'autre au sein de l'appel** — une commande demandée par le client est
  ignorée, et c'est la réponse de l'écrivain qui revient ;
- **`AcceptEnv` / `PermitUserEnvironment`** côté serveur : si le client pouvait poser
  ses propres variables, il choisirait le coffre visé. `env` écrase toute valeur
  héritée, mais on le vérifie plutôt que de le supposer.

L'appel déporté ne change ni la permission ni la règle : la cible reste le coffre
parent, donc `elevated`. La règle à **appliquer** chez le harnais appelant est
celle-ci : l'écrivain y est **refusé à tous**
(`"tools": { "ecrivain-du-coffre*": false }`) et **ouvert au seul agent**
**`assistant`** — celui que cette fiche déclare auteur. C'est cette règle que
`opencode debug config` doit montrer, sans rien retirer à l'agent au passage.

**Ce point est prouvé** (2026-10-10) : la déclaration est posée chez l'appelant, dans
sa configuration **globale** — le seul levier restant quand la configuration dédiée est
ignorée (voir `IA/system/adaptateurs-harness/opencode.md`). Le service redémarré,
`opencode debug config` montre l'écrivain **refusé à tous** et **ouvert au seul
`assistant`**, **sans rien retirer à cet agent** (son prompt reste résolu), et
`opencode mcp list` le donne **connecté**. Le critère 4 est donc tenu.

Éprouvé le 2026-10-10 : un acte réel passé par la commande forcée (un commit dans le
clone de test, et **rien** dans le coffre en service) ; une commande du client
ignorée ; le transfert de port refusé ; le pty refusé ; la clé refusée ailleurs.

**La cible a changé le 2026-10-17** : la commande forcée sert désormais le **coffre en
service** — condition (1) du plan de phase 6 levée, la phase étant close. Le clone de
test n'est pas supprimé : il reste le terrain d'essai des profils pilotes. Les
garde-fous de la ligne (`restrict`, `no-pty`, `no-agent-forwarding`, filtre d'origine)
sont **inchangés** ; seule la valeur du coffre visé a bougé.

## Le harnais AionUi — une liste centrale, un défaut par agent

L'interface **AionUi** est un second harnais, **local** — rien à déporter,
contrairement à `## L'appel déporté`, plus haut. Elle ne se configure pas par un
fichier par agent : elle tient **une liste MCP unique**, puis **pousse** vers
chaque assistant ce que son **défaut MCP** autorise. Où vit la configuration,
comment elle se synchronise vers tous et quelle est la table des défauts sont
décrits dans `IA/system/adaptateurs-harness/aionui-obsiaui.md` (§1, §4 et §5). La
déclaration se fait par le réglage MCP de l'interface (`MCP Management`) ou par
son CLI de configuration, le binaire **`aioncore`** (`aioncore config mcp …`).

**Déclarer le serveur.** Une entrée `stdio` : l'interpréteur, le chemin absolu du
point d'entrée dans ce dépôt, et `OBSIA_COFFRE` pointé sur le **coffre parent en
service** — le vrai, jamais un clone de test. Le serveur est ensuite **activé**.
Comme celle d'opencode, cette configuration vit **hors du dépôt** : chez AionUi,
elle est tenue par l'interface, dans sa configuration **locale** — rien à éditer à
la main dans l'arbre suivi (§1 du doc d'adaptation, « Où vit la configuration »).

**Pourquoi l'écrivain échappe au §3 du doc d'adaptation.** Le §3 met en garde contre
les serveurs qui réclament un **jeton** — l'interface n'offre pas d'interpolation
documentée — et n'autorisait jusque-là que `coffre-parent`, seul serveur à ne
demander qu'un **chemin**. Cet interdit garde sa portée pour les serveurs
authentifiés (`git-hub`, `obsidian`, `searxng` s'il est protégé), laissés à
l'agent CLI ; l'écrivain y **échappe** pour la même raison que `coffre-parent` :
lui non plus ne porte aucun secret, seulement le chemin du coffre.

**Le restreindre au seul `assistant`.** Le défaut MCP d'un assistant prend deux
états (§5 du doc d'adaptation, ligne « MCP par défaut » ; le CLI les nomme `auto`
et `fixed`) : **automatique** — l'interface pousse **tous** les serveurs activés —
ou **liste fixe**, explicite. Le choix est **exclusif** : une liste fixe
**remplace** l'héritage automatique au lieu de s'y ajouter. La règle « refusé à
tous, ouvert au seul `assistant` » se traduit donc par des listes **fixes**, et
chacune doit **nommer tout ce qu'on veut** :

- les profils qui **tiennent le rôle `assistant`** — **`OBSIA`** (appelé
  directement, hors équipe) et **`obsi`** (contexte d'équipe) : pour chacun, la
  liste doit **nommer tout ce qui est déclaré au centre et voulu pour lui**,
  l'écrivain compris — ce qu'une liste fixe omet, elle le **retire**. Les deux ne
  sont **pas identiques** (chaque profil a la sienne), et les serveurs à **jeton**
  (`git-hub`, `obsidian`) n'y figurent pas : ils restent hors de l'interface (§3) ;
- **les autres agents OBSIA** (`Administrateur`, `Bâtisseur`, `Contradicteur`,
  `Visionnaire`) : des listes où l'écrivain n'apparaît **pas**. Un agent laissé en
  `auto` hérite de **tout** ce qui est activé au centre, écrivain compris — c'est
  le cas à corriger quand on en trouve un.

Le **piège de l'outil** (§5 du doc d'adaptation) vaut ici : mettre à jour un
assistant peut remettre son **modèle** par défaut en automatique. Prendre une
copie des défauts **avant**, relire **tous** les défauts après, comparer.

**Vérifier**, en deux temps :

1. la commande de test du CLI — `aioncore config mcp test-connection` — **prend un
   paramètre que son `--help` ne montre pas** : le corps est lu sur l'**entrée
   standard**, et c'est l'**objet du serveur** à éprouver — `name` et `transport`
   obligatoires. Elle éprouve **ce seul serveur**, pas tous. Un corps vide (`{}`)
   ou un objet sans `name` est refusé par le back-end (HTTP 400) : c'est ce refus,
   pris pour « aucun paramètre », qui avait fait écrire le contraire ici. Ne pas
   recopier le `transport` à la main, le lire dans la déclaration :

   ```sh
   aioncore config mcp servers list \
     | jq -c '.data[] | select(.name=="ecrivain-du-coffre") | {name, transport}' \
     | aioncore config mcp test-connection
   ```

   `jq` doit être installé — il ne sert qu'à lire la déclaration.

   La réponse est un objet à deux étages (`{success, data:{success, tools}}`) :
   `data.tools` doit annoncer les **quatre gestes** (`notes_du_coffre`,
   `ecrire_un_carnet`, `ranger_une_note`, `completer_une_note`) ;
2. un **appel réel** — `notes_du_coffre` — doit rendre l'inventaire du **vrai**
   coffre : c'est la preuve que l'`OBSIA_COFFRE` posé est le bon.

**Deux limites assumées, non résolues** :

- les assistants **intégrés** de l'interface et ses moteurs **générés**, restés
  en `auto`, héritent eux aussi d'un serveur activé au centre. C'est déjà le cas
  de `nextcloud`, ouvert au seul `assistant` selon les fiches : « tous » veut
  dire **tous les agents OBSIA**, pas tous les assistants de l'interface. Le
  fermer exigerait de les figer tous, au risque que l'interface les régénère ;
- un défaut MCP ne vaut que pour les **conversations neuves** : une conversation
  déjà ouverte garde l'instantané pris à son ouverture. L'écrivain n'apparaît
  donc, chez les profils du rôle `assistant`, qu'à la **prochaine** conversation.
