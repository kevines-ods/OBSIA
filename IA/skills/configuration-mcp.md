---
schema: 1
kind: skill
name: configuration-mcp
description: Rendre les MCP déclarés dans `IA/MCP/` réellement fonctionnels sur un harness — traduire chaque fiche en configuration écrite hors dépôt, secrets en variables d'environnement, puis vérifier serveur par serveur que les outils répondent vraiment. À charger en branchant OBSIA sur un harness neuf, ou quand un serveur MCP déclaré ne répond pas. Ne rédige pas de fiche MCP : `createur-de-skill` et le §5 s'en chargent.
type: outil
read_only: false
---

# Skill — Configuration des MCP

Une fiche de `IA/MCP/` **déclare** un outil : son transport, sa permission, ses
règles de sécurité. Elle ne le branche pas. Le branchement est une
**instance** — un bloc JSON chez un harness précis, sur une machine précise,
avec un chemin et des jetons réels.

C'est exactement le partage du §12 pour les tâches planifiées : le registre
déclare, l'exécutant instancie. Et la même panne guette — une instance qui
n'existe qu'à un seul endroit se perd sans que rien ne le signale. D'où la
règle : **la fiche fait foi, la configuration se reconstruit.**

Ce skill fait la traduction, dans ce sens-là uniquement.

## Avant de commencer

Trois choses doivent être vraies, sinon s'arrêter et le dire :

| Prérequis | Où le vérifier | Si absent |
| --- | --- | --- |
| le harness est choisi | l'utilisateur l'a nommé | demander — ce skill n'en recommande aucun (§3) |
| il a une fiche d'adaptation | `IA/system/adaptateurs-harness/<harness>.md` | l'écrire d'abord, par patch : elle dit *où* vit la configuration |
| l'agent tourne sur la machine du harness | l'environnement d'exécution | écrire est possible, **vérifier ne l'est pas** — voir l'étape 6 |

## Procédure

### 1. Ne configurer que ce qu'un agent déclare

Un MCP n'est utilisable que **déclaré par un agent** (§10.2). Un serveur
branché que personne ne déclare est une surface d'attaque sans usage.

```bash
grep -A20 '^mcp:' IA/agents/*.md | grep '^\S*- ' | sort -u
```

L'union des listes `mcp:` des agents à brancher donne la liste exacte à
configurer. Ni plus — un serveur en trop s'enlève —, ni moins.

### 2. Lire chaque fiche avant de la traduire

Pour chaque nom retenu, lire `IA/MCP/<nom>.md`. Trois champs pilotent la
traduction, et le corps porte le reste :

| Champ | Ce qu'il décide |
| --- | --- |
| `transport` | `stdio` → commande + arguments ; `http` → URL + en-têtes |
| `permission` | `elevated` → l'écrire à l'utilisateur avant de brancher, pas après |
| le corps | les limites que le serveur **n'applique pas lui-même** |

Ce dernier point est le cœur du sujet : un serveur de fichiers braqué sur la
racine du coffre peut écrire partout, alors que le §7.3 n'ouvre que quelques
zones. Aucune configuration ne porte cette limite. Elle vit dans la fiche, et
c'est l'agent qui la respecte.

### 3. Partir du gabarit versionné

`IA/MCP/mcp.example.json` porte un bloc par serveur, avec des valeurs fictives.
C'est la source à copier — jamais un bloc réécrit de mémoire, qui dérivera de
la fiche à la première correction.

Adapter ensuite la **forme** au harness, que la fiche d'adaptation donne :
nom du fichier, emplacement, et si le harness attend `mcpServers`, une liste,
ou un format à lui.

### 4. Remplacer les valeurs fictives — jamais un secret en clair

| Valeur fictive | Ce qu'on met | Où ça vit |
| --- | --- | --- |
| `/chemin/absolu/vers/Mon coffre` | le chemin réel, **cité** — il contient une espace | la config, hors dépôt |
| `${GITHUB_TOKEN}`, `${OBSIDIAN_API_KEY}` | **la référence telle quelle** | la valeur : variable d'environnement, hors dépôt |
| `https://searxng.example.tld` | l'URL réelle du service | la config, hors dépôt |

Un jeton ne s'écrit **jamais** dans le fichier de configuration, même hors
dépôt : il se référence. Le §4 est sans exception, et le dépôt est public —
une configuration remplie ne revient jamais dedans.

### 5. Prévisualiser, sauvegarder, écrire

Écrire la configuration d'un harness écrase ce qui était branché avant, y
compris ce que l'utilisateur avait mis à la main et dont OBSIA ne sait rien.

1. **Afficher** le fichier final en entier, et ce qu'il remplace ;
2. **sauvegarder** l'existant à côté, daté — sans quoi il n'y a pas de retour
   arrière : ces fichiers ne sont pas versionnés ;
3. écrire ;
4. **consigner** au log de session (§9) : quoi, où, résultat. Brancher un
   serveur est une action à effet externe, quel que soit son `permission`.

### 6. Vérifier — un serveur par un serveur

Une configuration écrite n'est pas une configuration qui marche. Redémarrer le
harness, puis appeler **un outil en lecture** de chaque serveur :

| Serveur | L'appel qui prouve | Ce qu'on doit voir |
| --- | --- | --- |
| `coffre-parent` | lister la racine du coffre | `OBSIA/` et les dossiers en `-` |
| `git-hub` | lire un dépôt public | son arborescence |
| `chrome-devtools` | ouvrir une page vide | la page rendue, sans erreur de lancement |
| `obsidian` | lister les notes | une liste non vide |
| `searxng` | une recherche triviale | des résultats |

Deux règles pour que la vérification veuille dire quelque chose :

- **un serveur qui n'a pas été appelé n'est pas vérifié.** « Le harness l'a
  chargé sans erreur » prouve que le processus démarre, pas que l'outil
  répond ;
- **si l'agent ne tourne pas sur la machine du harness**, la vérification est
  impossible : le dire, lister les appels à faire, et ne pas annoncer un
  branchement réussi. Une session distante écrit la configuration, elle ne la
  constate pas.

### 7. Ce qui reste à faire, le dire

Ce qui échoue est normal au premier branchement : un binaire absent (`npx`,
`uvx`), un jeton non exporté, un service local éteint. Rendre la liste — un
serveur, sa panne, ce qu'il faut installer ou exporter — plutôt que retirer le
serveur de la configuration pour obtenir un vert complet.

## Ce que ce skill ne fait pas

- **Il ne crée pas de fiche MCP.** Une fiche neuve suit le §5 et
  `createur-de-skill` ; ce skill traduit ce qui existe.
- **Il ne choisit pas de harness.** Le coffre n'en recommande aucun (§3).
- **Il ne branche pas le cerveau.** Charger `CLAUDE.md` ou le prompt généré, et
  donner accès au coffre parent, sont les deux autres besoins — ils vivent dans
  `IA/system/adaptateurs-harness/commun.md`.

## Rationalisations

| Ce qu'on se dit | La réalité |
| --- | --- |
| « je mets le jeton en clair, le fichier est hors dépôt » | il est lisible par tout ce qui tourne sur la machine, et il sera copié un jour dans un rapport ou une capture |
| « le harness démarre sans erreur, donc c'est bon » | un serveur stdio ne se lance qu'au premier appel : le silence au démarrage ne prouve rien |
| « je branche tous les serveurs, ça évitera d'y revenir » | un serveur que personne ne déclare est une surface d'attaque sans usage, et le vérificateur le signale déjà comme code mort |
| « je recopie le bloc de mémoire, c'est plus rapide » | il divergera de la fiche à la première correction, et rien ne le dira |
| « j'écrase la config, elle était sûrement vide » | elle contenait peut-être ce que l'utilisateur avait branché à la main ; sans Git, rien ne le rend |
| « searxng ne répond pas, je l'enlève de la liste » | l'agent qui le déclare perdra sa recherche sans comprendre pourquoi — dire la panne vaut mieux que la masquer |

## Le retour dans le coffre

Rien de ce qui a été écrit ne revient dans le dépôt : ni le chemin réel, ni
l'URL du service, ni le fichier rempli (§7.2, §9). Ce qui y revient, s'il y a
lieu, c'est la **fiche d'adaptation** du harness — mise à jour par patch quand
le branchement a appris quelque chose de reproductible.
