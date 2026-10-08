# Vibe Work

**Statut : constat direct le 2026-10-07 — fiche rédigée depuis Vibe Work
lui-même, par le compte qui l'utilise. Les limites ci-dessous y sont énoncées
par l'outil, pas déduites d'une documentation publique ; les ponts A et B
restent à éprouver sur un coffre complet.**

**Vibe Work** — l'agent hébergé de Mistral : une conversation d'agent dans le
navigateur, pas un programme sur la machine. Pas de répertoire de travail
local, pas de ligne de commande, pas de fichier de configuration sur le
disque. Tout ce que Vibe Work sait faire passe par des connecteurs autorisés
pour l'espace de travail (GitHub, Google Drive, Gmail, agenda…) ou par des
fichiers joints à la conversation.

La conséquence tient en une phrase : **Vibe Work ne peut pas être lancé depuis
la racine du coffre** — il ne voit aucun dossier local. La voie 1 du §7.6
(« ouvrir la racine du coffre comme dossier de travail ») n'existe pas ici :
il faut un pont, et cette fiche en décrit trois.

---

## 1. Où vit la configuration

Nulle part sur la machine : dans le compte. Les connecteurs s'activent dans
l'application : ceux observés passent par OAuth — l'utilisateur relie son compte
GitHub ou Google Drive, la plateforme garde les jetons — et la documentation
décrit aussi « aucune », « Bearer » et « Basic ». Rien à écrire dans le coffre,
rien à ignorer dans `.gitignore`, et le §4 se tient sans effort : un secret
n'entre dans aucun fichier, l'agent ne voit que des outils déjà autorisés.

Ce qui est actif sur le compte de rédaction au 2026-10-07 : GitHub, Google
Drive, Gmail, agenda Google, recherche web. Un connecteur s'active à la
demande, quand l'agent en a besoin et dit pourquoi.

## 2. Le bloc MCP — aucun à écrire ; trois ponts vers le coffre

Vibe Work n'offre **aucune clé de configuration MCP** : les connecteurs sont
posés par l'**administrateur de l'espace de travail**, pas par l'utilisateur,
qui ne peut pas en monter un sur un chemin local — pas de `coffre-parent`
possible. Le skill `configuration-mcp`
(`../../skills/configuration-mcp.md`) doit s'arrêter ici : pas de bloc stdio,
pas de bloc HTTP, pas de chemin à remplir.

> **Vibe Code CLI n'est pas couvert ici.** C'est un autre produit : un agent
> en ligne de commande, avec un dossier de travail — il lit donc `AGENTS.md`,
> et déclare ses serveurs MCP dans un `config.toml` (`[[mcp_servers]]`). Voir
> la documentation officielle : <https://docs.mistral.ai/vibe/code/cli/agents>
> et <https://docs.mistral.ai/vibe/code/cli/mcp-servers>. Fiche à venir.

Ce qui remplace le bloc, c'est le support du coffre parent. Trois ponts, du
plus automatisé au plus simple :

**Pont A — coffre synchronisé sur Google Drive.** Le coffre (ou sa partie
mémoire, les dossiers `0-…`) vit dans un dossier Drive synchronisé depuis
la machine. Le connecteur Drive lit et écrit les fichiers du coffre :
l'agent joue un harness distant — consulter `agents-index.md` et
`skills-index.md`, n'ouvrir un skill que lorsqu'il en a besoin, rédiger
uniquement dans les zones ouvertes par le §7.3, et montrer ce qui va être
modifié avant de le faire. Limites : pas d'exécution —
`installer.py`, `verifier_coffre.py`, `regenerate_sommaire.py`,
`regenerate_index.py` tournent localement, par toi, après les modifications
de l'agent ; les fichiers générés ne se régénèrent pas tout seuls.

**Pont B — le dépôt `OBSIA/` par GitHub.** Le connecteur GitHub ne porte que
le dépôt de l'outil : branches, commits, propositions de fusion. Il ne donne
**ni les notes du coffre parent** — le dépôt de données n'est pas sur GitHub
— **ni l'`AGENTS.md`**, que son `.gitignore` exclut. Le principe tombe juste
avec le design du dépôt, qui a « son propre historique Git » : chaque
modification distante y est tracée en commit, et rien n'entre sans diff relu
— l'aperçu obligatoire avant action devient la PR elle-même. Autrement dit,
ce pont sert à faire évoluer OBSIA lui-même ; pour la mémoire du coffre,
c'est le pont A.

**Pont C — prompt transposé.** Sans connecteur : localement, depuis
`OBSIA/`,

```bash
python3 scripts/generer_prompt.py -o prompt-systeme.md
```

puis coller ce texte au début de la conversation et échanger les fichiers
en pièces jointes. L'agent suit le contrat sur la foi du prompt ; tout ce
qui n'est pas transmis n'existe pas pour lui. C'est le pont minimal, et le
plus lourd à tenir : chaque session repart du prompt.

Pour les trois ponts, une limite commune : **les tâches planifiées ne se
branchent pas**. Les timers systemd du skill `cron` n'existent pas chez un
harness hébergé, et les rappels propres à Vibe Work ne lancent pas de commande
locale. Les tâches restent l'affaire d'un harness local.

## 3. Secrets et variables

Aucune interpolation, aucun fichier : les jetons OAuth vivent côté
plateforme, hors du coffre. Le test du §4 se tient : montre à l'agent une
valeur factice qui ressemble à un jeton, il ne peut la répéter que si elle
est écrite dans le coffre ou dans la conversation — et le contrat lui
interdit les deux. Il doit la refuser et la désigner par son nom.

## 4. Restreindre un serveur à un agent

**Pas de traduction directe** — même constat que la fiche Claude Code : les
connecteurs valent pour la session, pas par agent. Le §10.2 reste une
consigne de prompt : déclarer en début de session quels connecteurs l'agent
en cours a le droit d'appeler, et n'activer que ceux que les agents présents
utilisent réellement — rien ne les cloisonnera ensuite.

## 5. Charger le cerveau

Vibe Work ne lit aucun `AGENTS.md` au démarrage : il n'a pas de répertoire
de travail. Trois voies :

- **Pont A (Drive)** : ouvrir la session en demandant à l'agent de lire
  l'`AGENTS.md` posé à la racine du coffre, puis le contrat et les index
  qu'il ordonne de lire. Rien n'est automatique : c'est à refaire à chaque
  session.
- **Pont B (GitHub)** : cet `AGENTS.md` n'est pas dans le dépôt — le dépôt
  de données ne le versionne pas. Mais `OBSIA/CLAUDE.md` en tient lieu : il
  porte le contrat et l'index à lire, avec leurs chemins.
- **Pont C** : le prompt généré par `scripts/generer_prompt.py`, donné en
  ouverture, qui tient lieu de cerveau entier.

Ses « connaissances personnelles » (une mémoire propre au compte) peuvent
garder un résumé du contrat et des ponts choisis : utile pour retrouver les
repères d'une session à l'autre, mais ce n'est pas le coffre — la mémoire de
référence reste dans les dossiers `0-…`.

## 6. Vérifier

Conversation de test, sur le pont choisi :

1. lister ce que le pont porte : par le connecteur Drive (pont A),
   `0-SAVOIRS/` doit apparaître ; par le connecteur GitHub (pont B), le seul
   dépôt `OBSIA/` — les notes du coffre n'y sont pas ;
2. lire une note de `0-SAVOIRS/` et retrouver le registre des tags (pont A
   ou C ; le pont B ne les porte pas) ;
3. test d'échec : demander une tâche qui appelle un skill absent du coffre ;
   l'agent doit dire qu'il ne le trouve pas, pas improviser (§10) ;
4. test de secret : lui montrer une valeur factice qui ressemble à un jeton ;
   il doit refuser de la répéter et la désigner par son nom ou son
   emplacement (§4).

Puis, **localement**, car rien de tout ça ne tourne chez l'hébergeur :

```bash
python3 scripts/verifier_coffre.py
python3 scripts/regenerate_sommaire.py
python3 scripts/regenerate_index.py
```

> Le coffre ne dépend pas de Vibe Work ; cette fiche n'est qu'un gabarit
> d'intégration.
