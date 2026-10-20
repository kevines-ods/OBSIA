# OpenCode

**Statut : vérifié sur documentation — les règles
(<https://opencode.ai/docs/rules/>) le 2026-09-30 ; le serveur
(<https://opencode.ai/docs/server/>), les agents
(<https://opencode.ai/docs/agents/>) et les serveurs MCP
(<https://opencode.ai/docs/mcp-servers/>) le 2026-09-13. Éprouvé sur machine réelle
(VM de test Debian 13) le 2026-10-06, puis sur le poste CachyOS le 2026-10-08
(opencode v2.0.24, campagne gpt-oss-20b) : la clé `instructions` est **ignorée**
— voir §2. Éprouvé de nouveau le 2026-10-10 (opencode v1.18.32, gpt-oss-20b
servi localement) : l'écriture directe se **retire**, l'écrivain du coffre la
remplace, et la lecture se **borne** par motif pour que le modèle ne puisse pas
recopier un secret — voir §9.**

Agent en ligne de commande configuré par un fichier `opencode.json`, doublé
d'un **mode serveur** : les sessions vivent côté serveur et se reprennent
depuis un autre appareil. C'est ce mode qui intéresse un coffre atteint depuis
plusieurs machines.

Cette fiche reste un **gabarit d'intégration**, pas une recommandation : le
coffre ne choisit aucun harness (`../VAULT-CONTRACT.md` §3). La comparaison qui
a mené à s'y intéresser, et ce qu'elle a écarté, vivent dans la note de projet
`choix-du-harness`, datée du 2026-09-13, dans la mémoire du dépôt privé.

> Les six sections attendues par `commun.md` se lisent ici ainsi : **1. où vit
> la configuration** → §2 ; **2. le bloc MCP** → §4 ; **3. secrets** → §4 ;
> **4. restreindre à un agent** → §3 et §4 ; **5. charger le cerveau** → §1
> et §2 ; **6. vérifier** → §8. Cette fiche est antérieure à la forme commune
> et garde son plan, plus riche.

---

## 1. Où lancer — la racine du coffre, pas le dépôt

Lancer depuis la **racine du coffre parent** (le dossier qui contient
`OBSIA/`), jamais depuis le dépôt seul. C'est la première des trois voies du
§7.6, et elle rend le serveur MCP `coffre-parent` inutile : un composant de
moins à surveiller.

C'est aussi de là que le cerveau arrive, tout seul. OpenCode **remonte** depuis
le dossier de travail et retient le **premier `AGENTS.md` rencontré** ; lancé de
la racine du coffre, il tombe sur celui que `python3 scripts/installer.py
--appliquer` y a posé. `CLAUDE.md` n'est lu qu'**en repli**, faute d'`AGENTS.md`
— c'est le fichier historique, pas le principal.

## 2. Charger le cerveau — par l'`AGENTS.md`, pas par `opencode.json`

Ce fichier vit à la racine du coffre parent : **hors dépôt, non versionné**,
comme l'exige la règle d'or de `README.md` et le §7.6 du contrat. Il sert aux
agents (§3), aux serveurs MCP (§4) et aux modèles (§5). **Pas** au noyau.

Un `opencode.json` minimal — les sections des §3 à §5 viennent s'y ajouter :

```json
{
  "$schema": "https://opencode.ai/config.json"
}
```

### ⚠️ La clé `instructions` est acceptée puis ignorée

Cette fiche présentait `instructions` comme la voie d'entrée du noyau
`VAULT-CONTRACT.md`, et `AGENTS.md` comme un simple complément. **C'est l'inverse
— et la clé ne sert à rien.** Mesuré le 2026-10-08 sur opencode v2.0.24, sur
machine réelle : la clé est **acceptée sans erreur**, mais le noyau n'apparaît
**jamais** dans le prompt système envoyé au modèle. Éprouvée sous **quatre
formes** — configuration globale et configuration de projet, chemin relatif et
chemin absolu —, chaque fois avec un fichier témoin de quelques octets : aucune
trace, pas même dans les journaux de démarrage du harnais, **qui ne surveillent
que les `AGENTS.md`**. Le déploiement croyait charger le contrat ; il ne le
charge pas.

**La voie qui marche est l'`AGENTS.md` du §1** — le seul fichier surveillé. Il
porte l'index des agents, celui des skills, celui des tâches, la méthode, le
profil retenu, et depuis le 2026-10-08 la **règle des secrets** du §4, reprise
mot pour mot en tête du prompt.

### Ce qui manque alors

Le noyau lui-même : l'`AGENTS.md` reprend la règle des secrets, mais **pas** les
autres règles du contrat — écriture, suppression, aperçu, frontmatter, annexes.
La méthode de l'`AGENTS.md` ordonne « Lis en entier le noyau
`IA/system/VAULT-CONTRACT.md` avant toute action » ; or OpenCode **ne résout pas**
les références de fichier d'un `AGENTS.md` (la documentation le dit) : le noyau
n'est donc **pas inséré**, il doit être **ouvert** par l'agent avec ses outils.
C'est une consigne de prompt, pas une garantie du moteur, et un modèle local peut
passer outre — d'où la vérification du §8.

**Les skills restent dans `OBSIA/IA/skills/`.** OpenCode a son propre dossier
de skills (`SKILL.md`) : un agent qui y cherche d'abord ne trouve rien, et
peut proposer de lui-même des liens symboliques ou une « installation
complète » des skills, agents et MCP. Refuser : le prompt d'`AGENTS.md` dit où
lire un skill, et lier ou recopier dupliquerait le catalogue (§5, une
information vit à un seul endroit). Constaté lors du premier essai sur machine
réelle, le 2026-10-06.

L'`AGENTS.md` ne se rédige pas à la main : `python3 scripts/installer.py
--appliquer` le pose à côté de `OBSIA/`, complet — index, méthode, profil retenu,
règle des secrets — précédé d'un marqueur « généré — ne pas éditer ». Un
`AGENTS.md` sans ce marqueur n'est jamais écrasé.

Sans `AGENTS.md` — avant la première installation — **rien du cerveau n'arrive** :
ni le noyau, ni l'index. Le geste de secours, dans cet ordre :

1. produire le prompt — `python3 scripts/generer_prompt.py` depuis la racine du
   dépôt (`-o <chemin>` pour écrire dans un fichier plutôt que sur la sortie) ;
2. le **coller dans la première consigne de session** ; ou, si l'on veut un
   fichier lu d'emblée, l'**écrire comme `AGENTS.md`** à côté de `OBSIA/`.

`instructions`, lui, ne fait pas ce travail : la clé est ignorée (voir plus haut).

## 3. Les agents — la carte, et ce qui ne se recopie pas

Un agent se déclare soit en JSON dans `opencode.json`, soit en Markdown à
frontmatter. **Les deux formats de frontmatter ne coïncident pas** : celui du
coffre porte `schema`, `kind`, `name`, `read_only`, `skills`, `mcp` (§5, annexe
`../contrat/contrat-frontmatter.md`) ;
celui du harness attend `description`, `mode`, `model`, `permission`. Un
fichier de `IA/agents/` ne se dépose donc pas tel quel dans le dossier
d'agents du harness.

La voie qui ne duplique rien : déclarer l'agent côté harness et **pointer** le
fichier du coffre comme prompt.

```json
{
  "agent": {
    "contradicteur": {
      "mode": "primary",
      "prompt": "{file:./OBSIA/IA/agents/contradicteur.md}",
      "permission": { "edit": "deny", "bash": "deny" }
    }
  }
}
```

Ce que la carte donne, et qui vaut d'être noté :

| Dans le coffre | Côté harness |
| --- | --- |
| un fichier de `IA/agents/` | une entrée `agent`, dont le `prompt` pointe le fichier |
| `read_only: true` (§5) | `permission: { edit: deny, bash: deny }` |
| l'écriture retirée au modèle local (§7.4) | `agent.<nom>.tools` à `false` — l'outil disparaît de la liste offerte (§9) |
| `mcp:` déclaré par l'agent (§10.2) | `tools` désactivés globalement, réactivés par agent |
| un skill de `IA/skills/` | rien à déclarer : l'agent ouvre le fichier quand la demande l'appelle |

`read_only: true` cesse ainsi d'être une consigne de prompt pour devenir une
règle du moteur. C'est le seul endroit où ce harness rend exécutoire une règle
que le contrat ne pouvait jusqu'ici qu'énoncer.

Réserve : le frontmatter du fichier d'agent part dans le prompt avec le reste
du corps. Sans gravité — il décrit ce que l'agent mobilise — mais ce n'est pas
gratuit en contexte.

## 4. MCP

Deux formes, `local` (stdio) et `remote` (HTTP), à remplir depuis
`IA/MCP/mcp.example.json` — les clés par variables d'environnement, jamais dans
le fichier (§4).

```json
{
  "mcp": {
    "git-hub": {
      "type": "remote",
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": { "Authorization": "Bearer ${GITHUB_TOKEN}" }
    }
  },
  "tools": { "git-hub*": false },
  "agent": {
    "assistant": { "tools": { "git-hub*": true } }
  }
}
```

Le couple `tools: false` global / `true` par agent est la traduction fidèle du
§10.2 : un MCP n'est utilisable que **déclaré par l'agent** qui s'en sert.

## 5. Modèles

Un serveur local et un service distant se déclarent côte à côte, et se
permutent en session. Quelle machine répond ne s'écrit **jamais** dans le
coffre (§7.6), seulement dans cette configuration, qui n'est pas versionnée.

⚠️ **La fenêtre déclarée se dimensionne sur la réservation de sortie.** OpenCode
réserve sa sortie sur la fenêtre **déclarée** du modèle — 8 192 jetons pour
gpt-oss-20b — et n'offre que le reste à l'entrée. Mesuré le 2026-10-08 sur
gpt-oss-20b : à 32 768 déclarés, le budget d'entrée tombait à ~24 576 jetons, sous
le pic de contexte mesuré de la campagne (25 456, à l'énoncé 07), et la session
partait en boucle de compaction ; à 65 536 déclarés, le budget est de ~57 000,
sans compactage. **Prévoir 65 536 déclarés au minimum** pour un modèle local comme
gpt-oss-20b qui porte le prompt OBSIA — et lire la fenêtre **servie**
(`/v1/models`), pas celle espérée.

## 6. Mode serveur et accès distant

```bash
opencode serve --hostname 127.0.0.1 --port 4096
opencode web
```

Les sessions sont conservées côté serveur : on en ouvre plusieurs, on les
reprend, on les liste. Un mot de passe se pose par variable d'environnement
(`OPENCODE_SERVER_PASSWORD`).

⚠️ **Ne pas publier ce service sur l'internet.** Le processus exécute du shell
sous l'utilisateur qui l'a lancé ; l'exposer revient à exposer la machine, et
le mot de passe n'est qu'un second verrou. Le faire passer par un réseau privé
(tailnet, VPN) est la seule voie à recommander ici. Cette réserve n'est pas
propre à ce harness : elle vaut pour tout agent joignable à distance.

## 7. Tâches planifiées

La documentation ne décrit **pas** de planificateur intégré. Les tâches du
registre restent donc `exécutant: local` (§12) — timers systemd, comme
aujourd'hui — et le piège du double déclenchement ne peut pas se produire.
À recontrôler si le projet en ajoute un : ce serait alors un arbitrage, pas
une évidence.

## 8. Vérifier

Comme pour tout harness (`commun.md`) : lister la racine du coffre, lire une
note de `Mon coffre/0-SAVOIRS/`, retrouver le registre des tags. Si `0-SAVOIRS/`
n'apparaît pas, le harness n'a pas été lancé à la bonne racine.

Deux vérifications de plus, propres à cette fiche :

- demander à l'agent d'énoncer une règle qui n'existe **que** dans
  `VAULT-CONTRACT.md` — s'il ne la connaît pas, **c'est normal** : le noyau n'est
  pas injecté (§2). La question utile n'est pas « la connaît-il ? » mais « va-t-il
  l'ouvrir ? » : le faire lire, puis vérifier qu'il cite la règle ;
- ouvrir une session, la reprendre depuis un autre appareil, vérifier que
  l'historique est là. C'est la promesse du mode serveur, et elle se constate.

## 9. Retirer l'écriture directe, brancher l'écrivain

**Éprouvé sur machine réelle le 2026-10-10** (opencode **v1.18.32**, `gpt-oss-20b`
servi localement, coffre de test sur un dossier de notes dédié, configuration
hors dépôt) : l'écriture directe se retire, et l'écrivain du coffre la remplace.
C'est la traduction du **§7.4** du contrat — le modèle ne touche pas le disque, il
passe par l'écrivain. *(Le constat du §2 — `instructions` ignorée — vient d'une
autre observation, sur le poste CachyOS en v2.0.24 ; tout ce qui suit vient de la
v1.18.32.)*

### Ce qu'on retire, et ce qu'on garde

Le harness déclare **douze** outils intégrés. On n'en retire que ceux qui
donnent prise sur le disque **en écriture**, ou qui ouvrent un sous-agent : lire
reste permis par le contrat (§7.2), et sans `read` le modèle ne pourrait plus
ouvrir `VAULT-CONTRACT.md` ni un skill (§2, §3, §8).

| Outil | Ce qu'il fait | Sort |
| --- | --- | --- |
| `bash` | shell | **retiré** |
| `edit` | modifier un fichier | **retiré** |
| `write` | écrire un fichier | **retiré** |
| `task` | lancer un sous-agent, qui **hérite** des outils | **retiré** |
| `webfetch` | aller chercher une page | **retiré** — sortie réseau qui, avec la lecture, pourrait emporter du coffre (§4, pas de réseau implicite) |
| `read` | lire un fichier | gardé (§7.2) |
| `glob`, `grep` | lister, chercher dans les fichiers | gardés — ils servent la lecture |
| `question` | poser une question | gardé |
| `todowrite` | écrire la liste des tâches | gardé — il n'écrit pas dans le coffre |
| `skill` | charger un skill du coffre | gardé |
| `invalid` | repli du harness (outil appelé qui n'existe pas) | gardé — ce n'est pas une écriture |

Tout se règle dans la carte `tools` de l'**agent** (`agent.<nom>.tools`), pas
globalement : le harness nomme son agent principal `build`, et c'est sur lui
qu'on éprouve le retrait.

```json
{
  "agent": {
    "build": {
      "tools": {
        "bash": false, "edit": false, "write": false,
        "task": false, "webfetch": false
      }
    }
  }
}
```

`opencode debug agent build` montre la carte effective : les outils retirés y
apparaissent à `false`, les gardés à `true`. Les outils MCP, eux, s'ajoutent par
dessus, préfixés du nom du serveur.

### `tools` et `permission` — deux étages

Le §3 règle `permission` (une entrée par outil : `allow`, `ask`, `deny`) pour
rendre exécutoire une règle du contrat — c'est ainsi que `read_only: true` devient
un refus du moteur. `tools` est un cran plus bas : ce n'est pas un refus, c'est le
**retrait** de l'outil de la liste offerte au modèle. Un outil refusé reste
visible : le modèle peut l'appeler et se voir répondre non. Un outil retiré n'est
plus là du tout — rien à appeler, rien qui tente.

Les deux se combinent sans se contredire : opencode traduit aussi une entrée
`tools: false` en refus de `permission` pour les outils qui ont une entrée de
permission (`bash`, `edit`, `task`, `webfetch`, ici) — ceinture et bretelles.
`write`, lui, n'a pas d'entrée de `permission` : son retrait tient à la seule
carte `tools`. Pour un agent que le contrat veut **en lecture seule**, le §3 garde
`permission: deny` ; pour retirer l'écriture à un agent qui doit **lire quand
même**, c'est `agent.<nom>.tools` qu'il faut — le modèle ne peut plus écrire, mais
il ouvre et cite encore le contrat et les skills.

### Brancher l'écrivain

L'écrivain du coffre est un serveur MCP **stdio** ; il prend le coffre par la
variable `OBSIA_COFFRE`, jamais par un argument — le modèle dit *quoi*, jamais
*où* :

```json
{
  "mcp": {
    "ecrivain-du-coffre": {
      "type": "local",
      "command": ["python3", "/chemin/vers/OBSIA/serveur/mcp_ecrivain.py"],
      "enabled": true,
      "environment": { "OBSIA_COFFRE": "/chemin/vers/le/coffre" }
    }
  }
}
```

Le chemin du coffre reste **hors dépôt**, comme le reste de cette configuration.
`opencode mcp list` doit montrer `ecrivain-du-coffre` **connected**.

**Quel coffre viser.** Le harnais de **livraison** vise le **coffre en service** ;
les profils **pilotes** — ceux qui éprouvent un modèle local — gardent un **clone de
test**, et le profil d'essai du **refus** vise un dossier qui n'est justement **pas**
un coffre. Cette séparation vient de la **condition (1)** du plan de phase 6
(2026-10-09) : la phase s'était menée sur un clone, **jamais** sur le coffre en
service. La phase close, le harnais de livraison a basculé le **2026-10-17** ; le
clone reste en place, terrain d'essai des profils pilotes.

Où ce bloc se lit **dépend de la version du harnais**, et cela ne se devine pas :

- **v1.18.32** — `OPENCODE_CONFIG` désigne un fichier dédié, à côté de la
  configuration personnelle : on éprouve un déploiement sans toucher à la
  configuration de tous les jours. C'est la forme éprouvée sur la machine du coffre ;
- **v2.0.24** — `OPENCODE_CONFIG`, `OPENCODE_CONFIG_DIR` et
  `OPENCODE_CONFIG_CONTENT` sont **acceptées puis ignorées** : les sous-commandes
  parlent au **service d'arrière-plan**, qui a résolu sa configuration à son
  démarrage. Vérifié le 2026-10-10 par trois sondes et un serveur témoin dans un
  dossier dédié — `opencode debug config` n'ajoute **aucune** source. Le seul levier
  **local à la machine** est alors la configuration **globale** ; le `opencode.json`
  de la racine du coffre, lui, est **synchronisé entre les machines** — y poser une
  clé privée et une adresse serait une faute, puisque l'autre machine y lirait un
  chemin qui n'existe pas.

  Les sources lues par la v2.0.24 : la configuration globale, le dossier de
  configuration (greffons), le `opencode.json` de la racine du coffre, et
  `<projet>/.opencode`.

  **Conséquence pratique : modifié sous un service déjà lancé, le fichier n'est pas
  relu — il faut redémarrer le service opencode avant de conclure.** Et `opencode mcp
  list` n'a rendu aucun serveur quand `opencode debug config` voyait ceux du projet :
  pour la résolution, c'est `debug config` qui fait foi.

### L'appel déporté — l'écrivain d'une autre machine

Un harnais qui ne tourne pas sur la machine du coffre ne peut pas y lancer
l'interpréteur : il passe par `ssh`, sur une **clé dédiée à ce seul appel**, posée en
**commande forcée** chez le compte qui exécute l'écrivain — voir
`IA/MCP/ecrivain-du-coffre.md`, « l'appel déporté ». La déclaration est celle du
serveur stdio ordinaire, la commande étant l'appel `ssh`, et **sans** `environment` :
le coffre visé est posé **côté serveur** par la commande forcée, le client ne le
nomme jamais.

```json
{
  "mcp": {
    "ecrivain-du-coffre": {
      "type": "local",
      "command": ["ssh", "-T",
        "-i", "/chemin/hors-depot/cle-dediee",
        "-o", "IdentitiesOnly=yes",
        "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=yes",
        "-o", "ConnectTimeout=10",
        "-o", "ServerAliveInterval=30",
        "-o", "ServerAliveCountMax=3",
        "<compte>@<adresse-du-poste>"],
      "enabled": true
    }
  },
  "tools": { "ecrivain-du-coffre*": false },
  "agent": { "assistant": { "tools": { "ecrivain-du-coffre*": true } } }
}
```

- `-T` : pas de terminal — le canal porte le protocole, rien d'autre ;
- `-i` **avec** `IdentitiesOnly=yes` : cette clé-là, et pas une autre du trousseau ;
- `BatchMode=yes` : jamais de question posée — un harnais n'y répond pas ;
- `ServerAliveInterval=30` avec `ServerAliveCountMax=3` : un canal muet se referme au
  bout de quatre-vingt-dix secondes au lieu de pendre — un harnais attend, il ne
  demande pas ;
- l'empreinte de la machine distante est **épinglée d'abord** dans `known_hosts`,
  après comparaison avec la clé d'hôte lue **sur la machine elle-même** : pas de
  confiance au premier contact ;
- `tools` **retire** l'écrivain de la liste offerte à tous, et `agent.assistant.tools`
  l'ouvre au **seul** agent que la fiche nomme : la `permission: elevated` de la fiche
  est la règle appliquée, pas une case à cocher.

**Ce point est prouvé** (2026-10-10) : la déclaration est posée chez l'appelant, dans
sa configuration **globale** — le seul levier restant sous v2.0.24, la configuration
dédiée étant inerte (voir ci-dessus). Le service **redémarré**, `opencode debug config`
lu **depuis la racine du coffre** (sinon la source de projet — les prompts des agents —
n'apparaît pas) montre le serveur `ecrivain-du-coffre` déclaré et actif, l'écrivain
**refusé à tous** (`ecrivain-du-coffre*` → `*` : `deny`) et **ouvert au seul
`assistant`** (`allow`), **sans perte pour cet agent** — son prompt reste résolu comme
avant (2 505 caractères). `opencode mcp list` le donne **connecté**. Le critère 4 est
donc tenu.

Éprouvé le 2026-10-10 depuis le poste secondaire : un acte réel a traversé la commande
forcée (commit dans le clone de test, et **rien** dans le coffre en service) ; une
commande demandée par le client est **ignorée** ; le transfert de port est refusé
(`administratively prohibited`) ; le pty est refusé ; la même clé est refusée sur un
autre compte et sur une autre machine.

### Les secrets — le filet, et la barrière

Retirer l'écriture **n'empêche pas** un secret d'entrer dans le coffre par un
autre chemin : ce que le modèle peut **lire**, l'écrivain peut le recopier dans
une note — et la note, une fois poussée, emporte le secret jusqu'au dépôt
distant. Le garde-fou de l'écrivain (le refus « absence de secret ») contrôle
donc aussi ce que le modèle y fait entrer : un jeton seul, un **bloc de base64
recopié sans son en-tête** et l'**en-tête d'une clé privée** (`-----BEGIN …
PRIVATE KEY …`, armure PGP comprise) y sont refusés. Deux formes **publiques**
font exception : un bloc fait d'**empreintes** (SHA-1 ou SHA-256, en entier — un
condensat abrégé n'exempte pas) et un bloc **encadré** par une armure publique
(clé PGP publique, certificat) — et l'exemption du cadre **tombe** dès qu'un
délimiteur s'y glisse, ce qui démasque une armure privée glissée dans un cadre
public. Mais ce garde-fou est un **filet**, pas une barrière :

- un mot de passe noyé dans une phrase, ou un secret trop court pour le seuil
  d'entropie, lui échappent — et lui échapperont toujours ;
- **limite assumée** : un corps de base64 **nu** posé entre deux **faux**
  délimiteurs publics passe, car rien ne le distingue du corps d'une **vraie** clé
  publique — du base64 entre deux lignes d'armure valides, des deux côtés. Aucune
  inspection ne peut trancher ; c'est l'**en-tête privé**, et non cette forme, qui
  tient le secret.

Un filet ne se règle pas au point de refuser la mémoire ordinaire : on l'écrit
tel qu'il est, et on met la vraie barrière en amont.

La vraie barrière est en amont, et elle est plus simple : **ce que le modèle ne
peut pas lire, il ne peut pas le recopier.** On borne donc la lecture, par
motif, dans la configuration (hors dépôt) :

```json
{
  "permission": {
    "read": {
      "*": "allow",
      "**/.ssh/**": "deny",
      "**/.gnupg/**": "deny",
      "**/.config/obsia/**": "deny",
      "*.env": "deny"
    }
  }
}
```

Trois points vérifiés le 2026-10-10 sur une configuration synthétique, avec
`opencode debug agent build` (v1.18.32) :

- la forme `{ "*": "allow", "<motif>": "deny" }` est la bonne, et le refus
  l'emporte sur un `allow` plus haut ;
- **l'ancre du motif dépend du projet.** Dans le projet, le motif se compare au
  chemin **relatif à la racine du projet**, pas au chemin absolu : un `.env` posé
  à la racine du clone ne se lit que comme `.env`, et `**/*.env` **ne l'attrape
  pas** — `"*.env"` **suffit** (il mord la racine comme les sous-dossiers ;
  `"**/*.env"` serait redondant). Hors du projet, l'ancre est le **chemin absolu
  privé de sa barre oblique de tête** (`home/<utilisateur>/.ssh/…`) quand aucune
  racine n'est ouverte, et le chemin **relatif à la racine du projet** — donc avec
  ses `..` — quand la session tourne depuis un clone. Devant cette ancre qui
  change, on écrit `**/` en tête (« `**/.ssh/**` », pas
  « `home/<utilisateur>/.ssh/**` ») : la seule forme juste des deux côtés,
  indépendante du compte et de la profondeur ;
- le refus tombe **avant** la lecture : un chemin interdit qui n'existe même pas
  est refusé de la même façon — ce n'est pas le contenu qui est filtré.

Rejeu du constat : sommé de lire un fichier sous `~/.ssh`, le modèle appelle
`read` et reçoit « permission refusée » — l'appel est visible dans la session, le
fichier n'est jamais ouvert. `opencode debug agent build --tool read` le montre
de la même façon, sans modèle.

⚠️ **`permission.glob` et `permission.grep` ne bornent pas un chemin.** Leur
motif se compare à l'**argument de requête** de l'outil (le motif global de
`glob`, l'expression de `grep`), pas à son dossier : impossible d'y interdire un
répertoire sans éteindre l'outil. Pour borner un **chemin**, c'est
`permission.external_directory` qui agit — tout ce qui est **hors de la racine
du projet** y passe, et vaut `ask` par défaut. Lancer la session **depuis le
clone** fait donc de `~/.ssh` un chemin externe, refusé à ce titre en plus du
motif de `read` : deux barrières plutôt qu'une.

### Ce que la session a montré

Sur un clone de données, modèle local, configuration ci-dessus (v1.18.32) :

- **outils vus par le modèle** : les quatre gestes de l'écrivain
  (`ecrivain-du-coffre_ecrire_un_carnet`, `…_completer_une_note`,
  `…_ranger_une_note`, `…_notes_du_coffre`) et, côté harness, `read`, `glob`,
  `grep`, `question`, `todowrite`, `skill` — **aucun** outil d'écriture ni de
  shell, ce que `opencode debug agent build` confirme ;
- **sommé d'écrire un fichier** (`ESSAI-T3c.md`) : **aucun fichier n'est apparu sur
  le disque**, et cette fois le modèle **s'est arrêté et l'a dit** — aucun outil
  ne le lui permettait. Une formulation antérieure l'avait vu **affirmer** un
  succès qu'il n'avait pas obtenu : d'où la prudence ci-dessous ;
- **un geste de l'écrivain** (`ecrire_un_carnet`) a **créé son commit dans le
  clone** : le dossier de notes gagne un carnet, et le clone reste propre — l'acte
  se commite lui-même.

⚠️ **La parole du modèle ne prouve rien.** Retirer les outils retire la capacité ;
ça n'empêche pas un petit modèle d'annoncer un succès qu'il n'a pas obtenu —
**six fois sur onze tirages libres** (constat du 2026-10-11). Et aucune consigne
ne l'en empêche de façon fiable : une liste **factuelle** de ses capacités le
laisse mentir 1 fois sur 3, une **règle de sincérité** seule 3 fois sur 3, des
outils d'écriture **visibles mais refusés** (`permission: deny`) 2 fois sur 3 —
il n'appelle même pas l'outil, il boucle puis annonce. La seule variante qui
tienne lui **nomme la réponse**, c'est-à-dire souffle ce qu'on veut entendre. Un
constat se lit donc sur le **disque** et dans le **journal de git**, jamais sur
ce que le modèle dit avoir fait.

Le **constat d'acte** fait ce constat sur pièces : `scripts/constat_acte.py` lit
le journal de la session, en tire les outils réellement appelés et le texte
produit, et le confronte à `git rev-parse`, `git status`, au **contenu** de chaque
fichier modifié et au disque — **relevé avant/après** à l'appui. Le verdict vient
de l'**état du coffre**, pas de la phrase : `ANNONCE NON TENUE` (sortie `1`) quand
le coffre n'a pas bougé, ni de tête, ni de nom, ni de contenu ; `ANNONCE TENUE`
quand il a bougé **depuis un relevé avant fiable** sous un geste qui peut écrire
(si l'annonce nomme un fichier, son existence sous le coffre le corrobore) ;
`RIEN ANNONCÉ` quand il n'y a rien à réfuter ; et `À CONTRÔLER` (sortie `3`) quand
la preuve manque — coffre hors de `git`, **relevé avant absent**, journal tronqué
—, plutôt qu'une accusation sur un doute : **sans relevé avant, un geste suspect
ne blanchit jamais**. Le repérage des annonces dans le texte est **lexical, donc
un indice** : il ne fait que **nommer** la phrase confrontée, ce qui **prouve**
c'est l'état du coffre. Éprouvé le 2026-10-11 sur les onze sessions réelles : six
`ANNONCE NON TENUE`, cinq `RIEN ANNONCÉ`. C'est le 5e critère de la phase 6,
**reformulé** le 2026-10-11 : « sans l'outil, aucune écriture n'a lieu, et toute
annonce d'écriture du modèle est démentie par un constat indépendant ».

## 10. Retirer l'écrivain — le serveur reste retirable

**Éprouvé le 2026-10-10** (opencode **v1.18.32**, même clone de test, configuration
hors dépôt chargée par `OPENCODE_CONFIG`) : l'écrivain se retire de la
configuration **sans rien casser** — le harness et le coffre restent sains. C'est
le **6e critère de la phase 6** : le serveur MCP n'est qu'un **maillon
déployable**, jamais une pièce du coffre.

### Comment le retirer

Deux gestes, tous deux dans la configuration hors dépôt (§9), et **chacun se lit
à sa façon** :

- **le retrait logique** — passer `enabled` à `false` sur
  `mcp.ecrivain-du-coffre` : la déclaration reste, le serveur n'est **plus
  lancé**. `opencode mcp list` montre alors `○ ecrivain-du-coffre **disabled**`
  (toujours `1 server(s)`) ; ses quatre gestes ne sont plus offerts ;
- **le retrait franc** — **supprimer** le bloc `mcp` (ou l'entrée
  `ecrivain-du-coffre`) : `opencode mcp list` affiche `▲ **No MCP servers
  configured**`, et le serveur n'existe plus du tout.

Aucun autre réglage n'est à toucher : ce qui borne la lecture (`permission.read`)
et ce qui retire l'écriture (`agent.build.tools`) vit ailleurs dans la même
configuration, et **ne dépend pas** de l'écrivain.

### Ce qui reste sain

Les **deux** gestes ont été rejoués sur la **vraie** configuration — sauvegardée,
puis **restaurée à l'identique** (`sha256` inchangé : `b4a715c9…`).

| Contrôle | Branché | `enabled:false` | Retrait franc |
| --- | --- | --- | --- |
| `opencode mcp list` | `✓ connected` · 1 server | `○ disabled` · 1 server | `▲ No MCP servers configured` |
| `opencode debug agent build` | **12** intégrés | **12** intégrés | **12** intégrés |
| gestes MCP offerts | **4** | **0** | **0** |
| clone de test | arbre propre | arbre propre, HEAD inchangé | arbre propre, HEAD inchangé, aucun commit |
| `verifier_coffre --coffre <clone>` | cohérent | cohérent | cohérent |

`opencode debug agent build` ne rend que la carte des **douze outils intégrés**
(`bash`, `edit`, `write`, `read`, `grep`, `glob`, `list`, `task`, `webfetch`,
`todowrite`, `skill`, `invalid`) : elle est **la même dans les trois états** — le
retrait ne touche pas le harness. Les gestes MCP se comptent à part, sur le
serveur (`tools/list` → `OUTILS`) : **4** (`ecrire_un_carnet`, `ranger_une_note`,
`completer_une_note`, `notes_du_coffre`) quand il est branché, **0** dès qu'il est
retiré — logiquement comme franchement.

Rien d'autre ne tombe avec lui : **aucun outil ne prend de chemin** vers le
serveur (§9) et son fichier reste dans le dépôt — le retrait est donc
**réversible** ; c'est ce qui le rend « retirable » plutôt qu'« attaché ». Un mot
sur le rebranchement : remettre le bloc ne suffit pas si l'on oublie
`OBSIA_COFFRE` — privé de cette variable, le serveur démarre mais **refuse toute
écriture** (il ne sait plus où écrire). On rebranche donc **avec** son
environnement, comme au §9.

### Le modèle privé de l'outil

Écrivain retiré, il ne reste **aucun** outil d'écriture : ni `bash`, ni `write`, ni
`edit`, ni `task`, ni les quatre gestes de l'écrivain. J'ai sommé le modèle local
d'écrire un fichier ; sur six formulations :

- **aucune** n'a rien écrit — aucun fichier sur le disque, aucun commit dans le
  clone, et les événements de session (`opencode run --format json`) ne montrent
  que `glob`, `read` et un appel de `skill` resté sans suite : **aucun** appel
  `bash`, `write` ou `edit` ;
- devant un **choix binaire** (« réponds `ok` si un outil a réellement écrit,
  sinon `impossible` »), le modèle a répondu **`impossible`** — il s'est arrêté et
  l'a dit ;
- sur les formulations libres, en revanche, il a **annoncé un succès qu'il n'avait
  pas obtenu** — la parole du modèle ne prouve rien, et le §8 du contrat le
  rappelle : une synthèse d'agent n'est pas une évidence.

⚠️ Le 5e critère — « sans l'outil, le modèle s'arrête et le dit » — ne se tient
**pas sur la parole** : un petit modèle annonce spontanément des succès qu'il
n'obtient pas. **Décision de l'utilisateur du 2026-10-10 (option B)** : le critère
**reste OUVERT** sous cette forme — tenu sur la **capacité** (« aucune écriture
directe » : elle est retirée, et ça, c'est vérifiable), pas sur la parole.
**Révisé le 2026-10-11** : il est **reformulé** — « sans l'outil, aucune écriture
n'a lieu, et toute annonce d'écriture du modèle est démentie par un constat
indépendant » — et **tenu** par le constat d'acte (§9 de cette fiche ; §8 du
contrat), qui conclut sur le **disque** et le **journal de git**, jamais sur la
phrase du modèle.

> Le coffre ne dépend pas d'OpenCode ; cette fiche n'est qu'un gabarit
> d'intégration.
