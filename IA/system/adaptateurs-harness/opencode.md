# OpenCode

**Statut : gabarit v2 — enrichi le 2026-09-13 depuis la documentation en ligne
du projet. Toujours pas éprouvé sur machine réelle : ce qui suit est vérifié
sur documentation, pas à l'usage.**

Agent en ligne de commande configuré par un fichier `opencode.json`, doublé
d'un **mode serveur** : les sessions vivent côté serveur et se reprennent
depuis un autre appareil. C'est ce mode qui intéresse un coffre atteint depuis
plusieurs machines.

Cette fiche reste un **gabarit d'intégration**, pas une recommandation : le
coffre ne choisit aucun harness (`../VAULT-CONTRACT.md` §3). La comparaison qui
a mené à s'y intéresser, et ce qu'elle a écarté, vivent dans
`mémoire/assistant/choix-du-harness/2026-09-13-opencode-retenu-et-les-ecartes.md`.

---

## 1. Où lancer — la racine du coffre, pas le dépôt

Lancer depuis la **racine du coffre parent** (le dossier qui contient
`OBSIA/`), jamais depuis le dépôt seul. C'est la première des trois voies du
§7.6, et elle rend le serveur MCP `coffre-parent` inutile : un composant de
moins à surveiller.

Conséquence : `CLAUDE.md` n'est plus à la racine du répertoire de travail, donc
il n'est plus chargé tout seul. Le §2 ci-dessous le rattrape explicitement.

## 2. Charger le cerveau — `opencode.json`

Ce fichier vit à la racine du coffre parent : **hors dépôt, non versionné**,
comme l'exige la règle d'or de `README.md` et le §7.6 du contrat.

```json
{
  "$schema": "https://opencode.ai/config.json",
  "instructions": [
    "OBSIA/CLAUDE.md",
    "OBSIA/IA/system/VAULT-CONTRACT.md",
    "OBSIA/IA/system/agents-index.md",
    "OBSIA/IA/system/skills-index.md",
    "OBSIA/IA/system/taches-index.md"
  ]
}
```

Les quatre fichiers de `IA/system/` sont listés à la main **exprès**.
`CLAUDE.md` les importe avec la syntaxe `@IA/system/…`, qui appartient à un
autre harness ; rien ne dit qu'elle soit résolue ici. Les énumérer coûte cinq
lignes et supprime le doute. Si la syntaxe d'import s'avère prise en charge,
ces lignes deviennent redondantes sans rien casser.

Deux points de la documentation, à connaître :

- le fichier de règles attendu par défaut s'appelle `AGENTS.md` ; `CLAUDE.md`
  n'est lu qu'**en repli**, s'il n'y a pas d'`AGENTS.md`. Ne pas créer
  d'`AGENTS.md` à la racine du coffre sans y reprendre ce qui précède, sinon
  le repli ne joue plus ;
- les entrées de `instructions` acceptent les motifs (`*.md`) et les URL.

Autre voie, si l'on préfère un seul bloc : `python3 scripts/generer_prompt.py`
depuis la racine du dépôt, et donner le fichier produit comme instruction de
démarrage.

## 3. Les agents — la carte, et ce qui ne se recopie pas

Un agent se déclare soit en JSON dans `opencode.json`, soit en Markdown à
frontmatter. **Les deux formats de frontmatter ne coïncident pas** : celui du
coffre porte `schema`, `kind`, `name`, `read_only`, `skills`, `mcp` (§5) ;
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

## 8. Vérifier après branchement

Comme pour tout harness (`commun.md`) : lister la racine du coffre, lire une
note de `Mon coffre/SAVOIRS/`, retrouver le registre des tags. Si `SAVOIRS/`
n'apparaît pas, le harness n'a pas été lancé à la bonne racine.

Deux vérifications de plus, propres à cette fiche :

- demander à l'agent d'énoncer une règle qui n'existe **que** dans
  `VAULT-CONTRACT.md` — s'il ne la connaît pas, `instructions` n'a pas été lu ;
- ouvrir une session, la reprendre depuis un autre appareil, vérifier que
  l'historique est là. C'est la promesse du mode serveur, et elle se constate.

> Le coffre ne dépend pas d'OpenCode ; cette fiche n'est qu'un gabarit
> d'intégration.
