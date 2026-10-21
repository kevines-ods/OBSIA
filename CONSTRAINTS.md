# Plancher de qualité — `mcp-outils-du-coffre`

Ce que le code de ce chantier doit tenir **en permanence**, et à quoi on le
mesure. Il couvre `serveur/` (le serveur), le **moteur partagé**
(`scripts/convention_des_notes.py`, `scripts/garde_secrets.py`) et le **noyau du
contrat** (`IA/system/VAULT-CONTRACT.md`, lu en entier à chaque séance).

Un plancher qui ne tourne pas n'existe pas : chaque chiffre ci-dessous a un
contrôle qui le mesure, et les règles d'un *diff* sont tenues par
`IA/skills/plancher-qualite/scripts/garde_plancher.py`, branché au workflow
`plancher-de-qualite`. **On ne baisse pas un chiffre pour passer au vert** : on
corrige le code, ou on écrit l'exception ici, avec sa raison et son échéance.

Le détail des motifs surveillés (neutralisation, allègement, inachèvement, seuil)
vit dans `garde_plancher.py`. On ne le recopie pas ici : une copie se
désynchronise de la règle, et c'est la règle qui juge.

## Le plancher — tenu à chaque *diff*

Ces règles n'ont pas de chiffre : elles sont vraies ou fausses à chaque
changement. Le garde les cherche dans le *diff*.

- **Aucun vérificateur fait taire.** Pas de motif de neutralisation ajouté — type
  ignoré, analyse désactivée, contrôle de sécurité désarmé. Si un contrôle gêne,
  il se discute et se corrige à la règle, il ne s'éteint pas dans le code.
- **Aucun test allégé.** Un test neuf ne s'ajoute pas déjà sauté, ni sans son
  assertion ; une assertion utile d'un test existant ne disparaît pas. Le garde
  juge cette phrase **par portée**, sur l'arbre syntaxique : il compare chaque
  portée qui survit d'une version à l'autre — test, fonction d'aide, méthode,
  module — et nomme celle qui a perdu des assertions. Une aide qui perd son
  `assert` compte donc autant qu'un test qui perd son `assertEqual`.
  Deux cas restent hors de sa portée, et c'est une mesure, pas un oubli : une
  portée **renommée** ou **effacée** n'est plus comparable. Détecter « un
  `def test_` a disparu » a rendu 9 constats sur les 120 derniers commits, dont
  deux renommages purs, pour un seuil fixé d'avance à 3 : le contrôle a donc été
  écarté, et il ne se réinvente pas sans une nouvelle mesure.
  **Extraire** des assertions d'un test vers une aide, même légitime, **rougit** :
  le test s'allège, et c'est exactement ce qu'on veut voir. Une extraction honnête
  s'acquitte — et l'exception `E<n>` porte sur le **fichier** (glob `fnmatch`, comme
  `.plancherignore`), pas sur le test ni sur la ligne : l'écrire couvre ce fichier
  pour cette règle, tests voisins compris.
  Un test sauté pour de bon est un test qui ne tourne jamais : le garde relève un
  `skipIf`/`skipUnless` à **condition constante** (`True`, `False`, leur négation)
  et un `self.skipTest(…)` **énoncé nu** dans le corps d'un test, hors de tout
  `if`, `try` ou boucle. Les sauts **conditionnels** sur l'environnement restent
  légitimes et ne sont pas signalés. Mesure : zéro constat sur les 120 derniers
  commits, pour une trentaine de `skipIf` conditionnels dans le dépôt.
  **Ce que le garde ne sait pas peser** : il compte des nœuds, ni leur force ni
  leur exécution. `self.assertEqual(v.refus.controle, "absence de secret")`
  remplacé par `self.assertTrue(True)` le laisse à 2 → 2, et il rend 0 ; une
  assertion déplacée sous `if False:` ou dans une boucle `range(0)` compte pareil.
  C'est une limite du comptage, pas un abandon : dans le même voisinage il attrape
  encore une assertion retirée d'un test ou d'une aide, un test sauté sans
  condition, un fichier de test effacé. Une assertion comptée n'est pas une
  assertion exécutée utilement.
- **Aucun test supprimé** pour faire passer un changement.
- **Aucun travail inachevé laissé** dans le code livré : pas de marqueur de
  reste-à-faire, pas de raccourci avoué dans le code.
- **Aucun seuil desserré en silence.** Baisser un chiffre du tableau ci-dessous se
  voit : c'est une décision, elle se dit.

Les sauts **conditionnels** déjà présents dans la suite (selon `git`, `sh`, ou la
locale UTF-8) ne sont pas des allègements : ils portent sur l'environnement, pas
sur la règle. Ce qui est interdit, c'est d'en ajouter un pour éviter d'affronter
un échec.

## Tenu avec des chiffres

| Dimension | Règle | Vérifié par | Quand |
| --- | --- | --- | --- |
| Suite de tests | **0 échec, 0 erreur** | `python3 -m unittest discover -s tests` (et la CI) | chaque poussée |
| Nombre de tests | **≥ 981** — le plancher monte, il ne descend pas | `tests/test_plancher_du_projet.py`, sur le compte de la suite | chaque poussée |
| Contrôles de la porte | **100 %** couverts : chaque contrôle a **≥ 1** test qui le nomme | `tests/test_plancher_du_projet.py`, contrôle par contrôle | chaque poussée |
| Dépendances | **0 paquet tiers** — bibliothèque standard seule | `tests/test_plancher_du_projet.py` (imports) et la CI, qui n'installe rien | chaque poussée |
| Écritures disque | **0 écriture** pendant le jugement et la carte | `tests/test_porte_entree.py` (`TestAucunOctetSurLeDisque`, `TestPuretePositive`) | chaque poussée |
| Noms de harnais | **0** dans `serveur/` et le moteur partagé (§3) | `tests/test_plancher_du_projet.py` | chaque poussée |
| Chemins de machine | **0** chemin absolu ou personnel dans `serveur/` et le moteur partagé (§13) | `tests/test_plancher_du_projet.py` | chaque poussée |
| Noyau du contrat | **≤ 4 016 mots** — le plafond descend, il ne monte pas en silence | `scripts/verifier_coffre.py`, sur `IA/system/VAULT-CONTRACT.md` | chaque poussée |
| Processus de la suite | **≤ 5 287** processus enfants — la mesure plus 2 % (5 183 le 2026-10-17, pour 1 098 tests) | `scripts/banc_de_processus.py` | chaque tranche qui touche la suite |
| Lectures du garde | **≤ 2 × modifiés + 1 × (ajoutés + supprimés) + 2** fichiers lus, et le garde **imprime** son compte | `garde_plancher.py` lui-même, constat `budget-de-lectures` | chaque *diff* |

Les deux derniers mesurent un **coût**, pas un résultat, et c'est pour cela qu'ils
ne s'achètent pas : aucune exception `E<n>` ne couvre `budget-de-lectures`, et le
banc rend 1 sans qu'on puisse le faire taire. La règle qui les tient ensemble :
**on n'économise pas des processus en achetant du couplage entre tests** — un test
qui profite de l'état laissé par un autre épargne quelques processus et coûte une
panne qu'on cherche une heure. Une lecture s'entend comme **un fichier dont le
garde a eu besoin du contenu, quel que soit le moyen** ; deux versions du même
fichier comptent pour deux, une relecture du même contenu pour une.

Le plafond de processus a une **limite de profondeur**, et ce n'est pas une erreur
de mesure : le compteur vit dans le processus de la suite, donc un test qui lance
un script qui lance lui-même des processus n'est compté qu'au premier étage — neuf
scripts du dépôt lancent des processus. Le biais est **constant** (la mesure de
référence le partage), le plafond reste donc cohérent avec la suite qu'il plafonne.
La conséquence utile est ailleurs : **un test qui externalise du travail dans un
sous-processus échappe au budget**. Le budget ne se contourne donc pas par là, il
se contournerait **en trichant** — et c'est le geste que le garde et la revue
attrapent, pas le compteur.

### Comment le plafond de processus se relève

Un plafond qu'on ne sait pas relever finit relevé en silence, ou cassé. La
procédure est donc écrite :

1. **Qui et quand.** Le *lead* du chantier re-mesure, sur la machine, avec
   `python3 scripts/banc_de_processus.py` — jamais un agent qui veut finir vert.
   **Quand** une tranche qui touche la suite en a un besoin **légitime** : de
   nouveaux cas qui prouvent quelque chose, pas un test partagé pour économiser.
2. **Comment.** Re-mesure → `mesure + 2 %` (arrondi vers le haut) → mise à jour de
   `MESURE` et `PLAFOND` dans `scripts/banc_de_processus.py` **et** du chiffre de
   la ligne « Processus de la suite » ci-dessus. Le test
   `test_le_plafond_est_le_chiffre_de_constraints` tient les deux ensemble : les
   faire diverger rougit.
3. **Ce qui empêche le réflexe.** Relever un plafond est une **décision
   motivée** : la PR dit ce qui a été ajouté, combien de processus cela coûte et
   pourquoi ce coût est justifié. On ne relève **jamais** pour finir vert, et une
   tranche qui relève sans le dire dans sa description est un défaut de
   livraison — pas un détail de procédure.

La suite et le moteur visent **Python ≥ 3.10** : le contrôle des dépendances
s'appuie sur `sys.stdlib_module_names`, disponible depuis cette version. En deçà,
il retombe sur `sys.builtin_module_names` — un contrôle partiel, jamais un
contrôle éteint.

### Hors plancher partagé — `scripts/constat_acte.py` (dépendance assumée)

Le **constat d'acte** est **lié à un harnais** par nature : il lit le journal de
session d'OpenCode (flux JSON par ligne) et connaît sa **taxonomie d'outils**. Il
vit donc **hors du moteur partagé**, dont la règle « 0 nom de harnais » protège
l'agnosticité.

**Attention** : « hors plancher partagé » ne dispense **que** de la règle « 0 nom
de harnais ». Les **autres** règles s'appliquent quand même — aucun secret dans
le code, bibliothèque standard seule, aucun chemin de machine — et elles ne sont
pas contrôlées automatiquement sur ce fichier : il faut les constater. État au
2026-10-12 : bibliothèque standard seule, aucun chemin de machine, aucun secret ;
la taxonomie et la lecture du journal sont **déclarées et isolées** dans des
constantes nommées (`OUTILS_DE_LECTURE`, lecture du journal). Brancher un autre
harnais, c'est réécrire ces deux points, pas le reste. (Décision du 2026-10-12,
après la relecture adverse de la PR #171.)

## Exceptions tracées

Une exception s'ajoute **ici, et seulement ici** ; sa forme est une ligne de
tableau, quatre colonnes dans cet ordre :

    | E<n> | règle | fichier | raison |

- **E** suivi d'un numéro : l'identifiant de l'exception, stable entre les revues.
- **règle** : le nom exact du constat visé (`seuil-desserre`, `test-supprime`…),
  ou `*` pour tous.
- **fichier** : un glob de chemin, comme dans `.plancherignore`, ou `*`.
- **raison** : pourquoi, et la date à laquelle l'exception se révise.

Le garde **annonce** chaque exception nouvelle en avertissement — visible dans le
journal et dans le résumé — et **n'échoue pas** pour autant. C'est voulu : une
exception est une décision assumée, pas une faute ; ce qui serait une faute, c'est
qu'elle passe inaperçue. Une phrase d'exception écrite hors de ce tableau ne
compte pas : le garde ne lit que le tableau, il ne devine pas une intention.

| Id | règle | fichier | raison |
| --- | --- | --- | --- |
| E1 | seuil-desserre | CONSTRAINTS.md | relèvement du plafond du noyau (3 940 → 4 016 mots) pour y porter la règle générique « Ce qui n'a pas été vérifié se dit » au §10 ; à réviser le 2027-01-11, en redescendant alors le plafond au niveau atteint |
