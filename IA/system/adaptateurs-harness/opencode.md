# OpenCode

**Statut : vérifié sur documentation — les règles
(<https://opencode.ai/docs/rules/>) le 2026-09-30 ; le serveur
(<https://opencode.ai/docs/server/>), les agents
(<https://opencode.ai/docs/agents/>) et les serveurs MCP
(<https://opencode.ai/docs/mcp-servers/>) le 2026-09-13. Éprouvé sur machine réelle
(Debian 13) le 2026-10-06.**

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

## 2. Charger le cerveau — `opencode.json`

Ce fichier vit à la racine du coffre parent : **hors dépôt, non versionné**,
comme l'exige la règle d'or de `README.md` et le §7.6 du contrat.

```json
{
  "$schema": "https://opencode.ai/config.json",
  "instructions": ["OBSIA/IA/system/VAULT-CONTRACT.md"]
}
```

Pour le créer sans éditeur, depuis la racine du coffre (le dossier qui contient
`OBSIA/`) — un fichier déjà présent n'est pas écrasé :

```bash
if [ ! -d OBSIA ]; then
  echo "OBSIA/ absent : ce n'est pas la racine du coffre, rien n'est écrit"
elif [ -e opencode.json ]; then
  echo "opencode.json existe déjà, rien n'est écrit"
else
  cat > opencode.json <<'EOF'
{
  "$schema": "https://opencode.ai/config.json",
  "instructions": ["OBSIA/IA/system/VAULT-CONTRACT.md"]
}
EOF
fi
```

**Les skills restent dans `OBSIA/IA/skills/`.** OpenCode a son propre dossier
de skills (`SKILL.md`) : un agent qui y cherche d'abord ne trouve rien, et
peut proposer de lui-même des liens symboliques ou une « installation
complète » des skills, agents et MCP. Refuser : le prompt d'`AGENTS.md` dit où
lire un skill, et lier ou recopier dupliquerait le catalogue (§5, une
information vit à un seul endroit). Constaté lors du premier essai sur machine
réelle, le 2026-10-06.

**Une seule entrée, et c'est le noyau.** Les entrées de `instructions`
*s'ajoutent* à `AGENTS.md` — la documentation le dit en toutes lettres : « All
instruction files are combined with your `AGENTS.md` files ». Or l'`AGENTS.md`
du §1 porte déjà l'index des agents, celui des skills, celui des tâches et la
méthode : les quatre fichiers `IA/system/` qu'on listait ici y sont donc en
double. Le noyau, lui, n'y est pas : la méthode se contente d'ordonner « Lis en
entier le noyau `IA/system/VAULT-CONTRACT.md` avant toute action ». Le nommer ici
le met dans le contexte **d'emblée**, au lieu de laisser l'agent aller le
chercher — et c'est la seule pièce du cerveau qui manquait à `AGENTS.md`.

Le noyau est nommé **lui-même**, et non par la syntaxe `@IA/system/…` de
`CLAUDE.md` : OpenCode **ne résout pas** les références de fichier d'un
`AGENTS.md` — la documentation le dit, et propose de charger explicitement ce
qu'on veut voir arriver. Nommer le fichier garantit qu'il est inséré **entier**.
Les annexes de `IA/system/contrat/`, elles, ne s'insèrent pas : elles se lisent à
la demande, avant l'acte que le tableau du préambule du noyau assigne à chacune.

Deux points de la documentation, à connaître :

- le fichier de règles attendu par défaut s'appelle `AGENTS.md` ; `CLAUDE.md`
  n'est lu qu'**en repli**, s'il n'y a pas d'`AGENTS.md`. Cet `AGENTS.md`, on
  ne le rédige pas à la main : `python3 scripts/installer.py --appliquer` le
  pose à côté de `OBSIA/`, et il contient le prompt système complet — index,
  méthode, profil retenu — précédé d'un marqueur « généré — ne pas éditer ». Un
  `AGENTS.md` sans ce marqueur n'est jamais écrasé. Complété, il vaut mieux
  qu'incomplet : c'est ce que le coffre produit, et rien n'oblige à en écrire
  un second ;
- les entrées de `instructions` acceptent les motifs (`*.md`) et les URL.

Sans `AGENTS.md` — avant la première installation — la ligne n'est pas perdue :
le contrat reste lu, et c'est l'essentiel. Pour obtenir le prompt complet sans
installer : `python3 scripts/generer_prompt.py` depuis la racine du dépôt, et
donner le fichier produit comme instruction de démarrage.

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
  `VAULT-CONTRACT.md` — s'il ne la connaît pas, `instructions` n'a pas été lu ;
- ouvrir une session, la reprendre depuis un autre appareil, vérifier que
  l'historique est là. C'est la promesse du mode serveur, et elle se constate.

> Le coffre ne dépend pas d'OpenCode ; cette fiche n'est qu'un gabarit
> d'intégration.
