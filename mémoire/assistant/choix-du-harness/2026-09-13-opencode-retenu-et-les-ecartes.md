# 2026-09-13 — OpenCode retenu, et pourquoi les autres sont écartés

Sept critères posés par l'utilisateur, cinq harness confrontés. La comparaison
est faite **sur documentation en ligne**, aucun n'a été installé : c'est un
choix de direction, pas un retour d'usage.

## Statut

🟡 Décision prise, **rien d'installé**. La fiche d'intégration est écrite ; la
validation sur la VM reste à faire, et c'est elle qui pourra infirmer.

---

## Les sept critères

Énoncés tels quels par l'utilisateur : héberger sur la VM Fedora du Proxmox ;
brancher des modèles locaux **et** des API ; administrer l'hôte Proxmox et le
PC de jeu ; y accéder depuis le PC et le téléphone **sans perdre le fil des
discussions** ; ajouter des MCP, dont GitHub ; travail en équipe de plusieurs
agents (souhaité, non bloquant) ; multi-sessions.

## Décisions

- **OpenCode est retenu**, en mode serveur sur la VM Fedora, joint par réseau
  privé. Seul candidat à couvrir les sept critères avec un seul processus.
- **Il est retenu autant pour sa forme que pour ses fonctions.** Sa structure
  décalque celle du coffre : un agent = un fichier à frontmatter, les MCP se
  déclarent par agent, et `read_only: true` devient une permission du moteur au
  lieu d'une consigne de prompt. C'est le premier harness examiné qui rend
  exécutoire une règle que le contrat ne pouvait qu'énoncer.
- **Le harness sera lancé depuis la racine du coffre parent**, pas depuis le
  dépôt. Première voie du §7.6 : le MCP `coffre-parent` devient inutile, un
  composant de moins à surveiller.
- **Les tâches restent `exécutant: local`.** Ce harness n'a pas de
  planificateur documenté : l'invariant du §12 n'est pas menacé, rien à
  réconcilier.
- **OpenClaw est écarté malgré sa supériorité sur le critère « téléphone ».**
  C'est le seul arbitrage douloureux du lot — voir l'évidence ci-dessous.
- **Un nom de harness dans cette note n'enfreint pas le §3.** La règle
  interdit qu'un harness soit nommé dans les *règles* du coffre ; une note de
  mémoire est un récit, et le dossier des adaptateurs existe précisément pour
  accueillir ces noms.

## Évidence

Vérifiée dans la documentation des projets, pas à l'usage.

- **Mode serveur et sessions.** `opencode serve` expose une API HTTP ; les
  sessions sont conservées côté serveur — on les crée, les liste, les reprend,
  les duplique. `opencode web` ouvre une interface navigateur, avec
  `--hostname` pour le réseau local. Authentification par mot de passe en
  variable d'environnement. [1][2]
- **Agents et permissions.** `mode: primary | subagent | all`, `model`,
  `prompt: "{file:./chemin}"`, et `permission` à trois valeurs
  (`allow`/`ask`/`deny`) sur `edit` et `bash`. La documentation nomme
  elle-même ce réglage « accès en lecture seule ». [3]
- **MCP par agent.** Formes `local` (stdio) et `remote` (HTTP). Le motif
  documenté est de désactiver les outils globalement et de les réactiver par
  agent, pour ne pas charger le contexte de tous. [4]
- **Fichiers de règles.** `AGENTS.md` est le fichier attendu ; `CLAUDE.md`
  n'est lu qu'en repli, en son absence. Le champ `instructions` accepte des
  chemins, des motifs et des URL. [5]
- **Modèles.** 75+ fournisseurs, modèles locaux pris en charge, déclarables
  côte à côte et permutables en session. [6]
- **Téléphone.** Clients mobiles Android (F-Droid) et iOS existants,
  connectés à un serveur auto-hébergé par réseau local, tunnel ou VPN, avec
  reprise des sessions ouvertes ailleurs. **Ce sont des projets tiers**, pas
  officiels. [7][8]
- **OpenClaw.** Le mieux placé sur l'accès téléphone : 23+ messageries, MCP
  client *et* serveur, multi-agents, conversation qui vit sur le serveur. Mais
  CVE-2026-25253 — prise de contrôle en un clic menant à exécution de code, y
  compris sur une instance liée à `localhost`, par détournement de WebSocket
  depuis le navigateur de la victime — et environ **824 skills malveillants**
  sur sa place de marché, soit près de 20 % du catalogue au moment de la
  découverte. [9][10]
- **Les trois autres.** LibreChat : n'administre rien par lui-même, tout
  passerait par des MCP ; conversations en base MongoDB. OpenHands : un
  conteneur bac à sable par tâche, conçu pour **protéger** l'hôte — l'inverse
  du besoin. Goose : pas d'interface serveur ni web documentée, le critère
  téléphone tombe. [11][12][13]

## Interprétation

**Le critère qui a réellement trié, c'est le troisième.** Administrer
l'hyperviseur et le PC de jeu suppose un agent qui exécute du shell hors
conteneur, avec SSH sortant. Ce seul critère élimine OpenHands (bac à sable par
conception) et relègue LibreChat au rang d'interface de conversation. Les six
autres critères, presque tout le monde les remplit.

**Le second tri est de sécurité, et il coûte quelque chose.** OpenClaw gagnait
sur le confort — répondre depuis WhatsApp vaut mieux qu'ouvrir une interface
web. Lui donner un accès SSH à l'hyperviseur, avec le passif documenté
ci-dessus, était un mauvais échange. Le confort perdu est réel et assumé ; si
l'utilisateur veut y revenir, ça se durcit (pairage obligatoire, allowlist
d'outils, bac à sable, mDNS coupé) et ce sera son arbitrage, pas le mien.

**Ce qui reste incertain.** Trois choses, dans l'ordre de ce qu'elles
coûteraient : la syntaxe `@` d'import de `CLAUDE.md` n'est peut-être pas
résolue par ce harness — contournée d'avance en listant les fichiers un par un,
donc sans risque ; les clients mobiles sont tiers, donc leur qualité n'est pas
garantie dans la durée — le navigateur reste le repli ; et rien de tout cela
n'a tourné sur la VM.

## Synthèse IA

Le coffre a été écrit pour ne dépendre d'aucun harness, et c'est ce qui rend ce
choix réversible : ce qui bascule ici, c'est un fichier de configuration hors
dépôt, pas une ligne du coffre. Le test de portabilité de
[[portabilite-entre-harness]] est passé sans avoir eu à être appliqué — il n'y
avait rien à protéger, parce que rien n'a été mis au mauvais endroit.

Le fait notable est ailleurs : c'est le premier harness examiné qui **contraint**
au lieu de faire confiance. `read_only: true` était jusqu'ici une phrase que
l'agent pouvait ignorer. Devenir `permission: deny` change sa nature.

## URLs sources

1. https://opencode.ai/docs/server/
2. https://www.opencode.asia/web/
3. https://opencode.ai/docs/agents/
4. https://opencode.ai/docs/mcp-servers/
5. https://opencode.ai/docs/rules/
6. https://docs.ollama.com/integrations/opencode
7. https://github.com/dzianisv/opencode-mobile
8. https://apps.apple.com/us/app/openclient-for-opencode/id6763641767
9. https://adversa.ai/blog/openclaw-security-101-vulnerabilities-hardening-2026/
10. https://blog.cyberdesserts.com/openclaw-malicious-skills-security/
11. https://blog.elest.io/librechat-vs-openwebui-vs-lobe-chat-which-to-self-host-in-2026/
12. https://dev.to/lynkr/run-openhands-on-any-model-you-want-1mnd
13. https://en.wikipedia.org/wiki/Goose_(AI_agent)
