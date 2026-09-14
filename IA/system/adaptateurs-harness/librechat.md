# LibreChat

**Statut : vérifié sur documentation le 2026-09-14
(`https://www.librechat.ai/docs/configuration/librechat_yaml/object_structure/mcp_servers`)
— jamais éprouvé sur machine réelle.**

Interface web auto-hébergée dont les conversations vivent dans une base **sur
le serveur**, pas dans le navigateur : une même session se reprend depuis un
poste fixe comme depuis un téléphone. C'est ce qui en fait un candidat sérieux
quand le coffre doit être atteint depuis plusieurs appareils.

---

## 1. Où vit la configuration

`librechat.yaml`, le fichier de configuration de l'instance — hors dépôt, non
versionné (règle d'or de `README.md`). Deux clés distinctes s'y côtoient :

| Clé | Rôle |
| --- | --- |
| `mcpServers` | la déclaration des serveurs, un par nom |
| `mcpSettings` | les règles globales de sécurité : domaines et adresses joignables |

`mcpSettings` mérite un regard avant de brancher `coffre-parent` : c'est là que
se décide ce qu'un serveur a le droit d'atteindre.

## 2. Le bloc MCP

Clé racine `mcpServers`, en **YAML** — c'est la seule fiche du dossier où le
bloc n'est pas du JSON.

```yaml
mcpServers:
  coffre-parent:
    type: stdio
    command: npx
    args:
      - -y
      - '@modelcontextprotocol/server-filesystem'
      - '/chemin/absolu/vers/Mon coffre'
    timeout: 30000
    initTimeout: 10000
    stderr: inherit

  git-hub:
    type: streamable-http
    url: https://api.githubcopilot.com/mcp/
    headers:
      Authorization: 'Bearer ${GITHUB_TOKEN}'
    timeout: 30000
```

Types distants : `sse`, `streamable-http`, `websocket`. Les champs de processus
(`command`, `args`, `env`, `cwd`, `stderr`) n'existent que pour `stdio`.

Le chemin du coffre contient une espace : le citer, comme partout (§7).

## 3. Secrets et variables

Trois substitutions, à ne pas confondre :

| Forme | Résout en | Usage ici |
| --- | --- | --- |
| `${ENV_VAR}` | une variable d'environnement **du serveur** | les jetons (§4) |
| `{{LIBRECHAT_USER_ID}}`, `{{LIBRECHAT_USER_EMAIL}}` | l'utilisateur connecté | inutile pour un coffre mono-utilisateur |
| `{{MA_VARIABLE}}` | une variable par utilisateur, définie via `customUserVars` | identifiants propres à chacun |

Pour OBSIA, `${ENV_VAR}` suffit et c'est la seule à employer : le coffre a un
seul utilisateur, et les deux autres formes introduiraient une dépendance à la
session de l'interface.

## 4. Restreindre un serveur à un agent

L'interface porte des **agents**, et un agent déclare les outils qu'il
mobilise : c'est la traduction du §10.2. À confirmer sur l'instance réelle —
la documentation d'un agent est distincte de celle des serveurs MCP, et cette
fiche n'a vérifié que la seconde.

## 5. Charger le cerveau

Aucun mécanisme implicite : rien n'est lu depuis un répertoire de travail.
Générer le prompt et le donner comme instructions du preset ou de l'agent :

```bash
python3 scripts/generer_prompt.py -o prompt-systeme.md
```

## 6. Vérifier

Les serveurs sont initialisés **au démarrage de l'application** : un
redémarrage est nécessaire après modification. Puis, dans une conversation :
lister la racine du coffre, lire une note de `Mon coffre/-SAVOIRS/`, retrouver
le registre des tags. Si `-SAVOIRS/` n'apparaît pas, le serveur n'est pas monté
sur la bonne racine.

## Tâches planifiées — une réserve à ne pas oublier

L'interface prévoit des exécutions planifiées, donc une tâche du registre
pourrait s'y instancier en `exécutant: harness` au lieu de `local`. Deux
réserves avant de s'y fier : la forme du `quand` du coffre est un cron à cinq
champs avec fuseau (§5), à confronter à ce que l'interface accepte ; et
l'invariant du §12 tient — **au plus une instance vivante, tous exécutants
confondus**. Instancier la même tâche des deux côtés la déclencherait deux
fois, sans qu'aucune erreur ne le signale.

> Licence **MIT**, vérifiée à la source — compatible avec l'AGPL-3.0-or-later
> du dépôt. À recontrôler au moment du choix.

> Le coffre ne dépend pas de LibreChat ; cette fiche n'est qu'un gabarit
> d'intégration.
