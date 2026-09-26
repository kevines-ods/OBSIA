# DeepSeek Harness (DSH)

**Statut : NON VÉRIFIÉ — recherché le 2026-09-14, sans résultat exploitable.
La documentation officielle (`https://deepseek-harness.github.io/deepseek-harness/`)
ne publie ni chemin de configuration, ni clés MCP ; un guide tiers indique
explicitement que la syntaxe MCP de la version courante « n'a pas été
testée » et renvoie à la documentation de sa propre version.**

Harness « tout est plugin », compatible MCP et skills. Le projet existe et est
actif ; c'est sa **configuration** qui n'est pas documentée publiquement de
façon stable.

---

## Ce que cette fiche ne donne pas, et pourquoi

Les sections 1 à 4 de la forme commune (`commun.md`) sont **absentes** :
chemin du fichier de configuration, clé racine du bloc MCP, syntaxe des
secrets, restriction par agent. Aucune source ne les donne.

Elles ne sont pas remplies par déduction, et c'est délibéré. Un format inventé
s'écrit exactement comme un format vérifié, et rien ne les distingue une fois
dans le fichier — c'est la panne que le coffre a déjà subie sur les noms du
coffre parent
(leçon `nommage-verifie-a-la-source`, dans la mémoire du dépôt privé).

## Conséquence pour `configuration-mcp`

Le skill (`../../skills/configuration-mcp.md`) exige une fiche d'adaptation qui
dise *où* écrire et *sous quelle forme*. Celle-ci ne le dit pas.

**L'agent s'arrête donc ici et le signale**, au lieu d'écrire un fichier au
hasard. Une configuration écrite à un mauvais endroit ne produit pas d'erreur :
elle ne fait rien, et laisse croire que le branchement a eu lieu.

Ce qu'il peut faire à la place, et qui a de la valeur :

1. donner le bloc MCP universel de `commun.md`, à transposer par l'utilisateur ;
2. lui demander le chemin réel de sa configuration, ou la sortie de l'aide du
   binaire (`dsh --help`, ou l'équivalent de sa version) ;
3. **compléter cette fiche par patch** avec ce qui remonte — c'est ainsi
   qu'elle passera au statut vérifié.

## Ce qui est vérifié

- le projet est un harness d'agent à architecture de greffons, publié par
  DeepSeek AI ;
- des greffons MCP existent dans son écosystème, dans les deux sens : exposer
  DSH **comme** serveur MCP, et le brancher **sur** un serveur MCP externe ;
- la commande de lancement de l'interface web citée par un guide tiers est
  `pnpm dsh web`.

Rien de plus. Ce qui précède ne suffit pas à écrire une configuration.

## 5. Charger le cerveau

Non vérifié non plus. Le cerveau se génère comme partout —
`python3 scripts/generer_prompt.py -o prompt-systeme.md` — mais la manière de
le donner au harness dépend d'un mécanisme que la documentation ne décrit pas.

## 6. Vérifier

Si un branchement a lieu malgré tout : lister la racine du coffre, y voir
`OBSIA/` et les dossiers en `-`. Écrire `../-SAVOIRS`, jamais `-SAVOIRS` nu (§7).

> Le coffre ne dépend pas de DSH ; cette fiche n'est qu'un gabarit
> d'intégration — ici, un gabarit qui assume de ne pas pouvoir être rempli.
