---
schema: 1
kind: skill
name: plancher-qualite
description: Écrire le niveau de qualité d'un projet, chiffré, dans `CONSTRAINTS.md`, puis le faire respecter par un contrôle qui refuse les façons de passer au vert sans améliorer le code — faire taire un vérificateur, alléger un test, laisser un travail inachevé, desserrer un seuil, discuter la règle. À charger au démarrage d'un projet, ou dès qu'un agent contourne un contrôle. Ne détecte pas les secrets.
module: construction
type: outil
read_only: false
---

# Skill — Plancher de qualité

> **Adaptation.** Reprend `constraint-driven-development` de
> `addyosmani/agent-skills` (MIT), condensé, traduit, et son garde de
> référence réécrit en Python de la bibliothèque standard —
> `IA/skills/plancher-qualite/scripts/garde_plancher.py`.

Quand on écrit son code soi-même, le relire suffit à savoir s'il est bon. Un
agent en écrit plus en une heure qu'on n'en relit dans la semaine : le
jugement doit donc sortir de la tête et devenir un contrôle qui tourne.

`cadrage-produit` dit **quoi** construire. `tests-dabord` prouve que ça
marche. Ce skill dit ce que « assez bon pour livrer » veut dire — **avant**
qu'on en discute dans une revue.

## 1. Constater avant de demander

Ne jamais demander ce qui se lit. Avant la première question :

| Quoi | Où le lire |
| --- | --- |
| langage et pile | `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml` |
| lanceur de tests | dépendances de développement, script `test`, fichiers de test existants |
| analyse statique déjà en place | configuration d'ESLint, Biome, Ruff, Clippy |
| couverture actuelle | sortie de couverture, ou une exécution de la suite |
| intégration continue | `.github/workflows/`, `.gitlab-ci.yml` |

Rapporter la trouvaille en deux lignes, puis ne demander que le reste.

## 2. Quatre questions, chacune avec un défaut

Discipline d'`interrogation-du-besoin` — une question à la fois — avec une
différence : **chaque question a un défaut**, si bien que « je ne sais pas »
est une réponse complète qui produit quand même une configuration qui tourne.
C'est ce qui rend ce skill utilisable par quelqu'un qui ne connaît pas les
chiffres d'usage.

| | Question | Défaut si l'utilisateur ne sait pas |
| --- | --- | --- |
| 1 | Au-delà du plancher, qu'est-ce qu'on veut tenir : couverture, sécurité, performance, accessibilité, frontières d'architecture ? | couverture et sécurité — les deux qui coûtent le moins à mettre en place |
| 2 | Un contrôle qui échoue pendant le travail : il bloque, ou il avertit ? | bloquant sur le plancher, avertissement ailleurs les deux premières semaines |
| 3 | Y a-t-il des chiffres visés, ou mesure-t-on l'état actuel pour tenir cette ligne ? | mesurer et tenir — un chiffre inventé est un chiffre ignoré |
| 4 | Quel est le contrôle le plus lent qu'on accepte avant de rendre la main ? | 90 secondes en local, sans limite en intégration continue |

S'arrêter à quatre. Un questionnaire de douze produit une configuration que
personne ne comprend.

## 3. Écrire `CONSTRAINTS.md`

Un fichier à la racine du dépôt du projet. N'importe quel agent, sur
n'importe quel harness, sait le lire — et sa modification apparaît dans la
revue, là où elle doit apparaître.

```markdown
# Contraintes — <nom du projet>

Dernière revue : AAAA-MM-JJ

## Plancher — toujours tenu, aucune configuration requise

- Aucun commentaire de suppression neuf : `@ts-ignore`, `eslint-disable`, `# noqa`, `# type: ignore`
- Aucun travail inachevé : `NotImplementedError`, `catch {}` vide, `TODO`
- Aucun test ignoré ni supprimé sans raison dans le message de commit
- Aucun secret dans le code source
- Ce fichier ne se desserre pas pour faire passer un changement

## Tenu avec des chiffres

| Dimension | Règle | Vérifié par | Quand |
|---|---|---|---|
| Types | zéro erreur | la commande du projet | à chaque édition |
| Analyse statique | zéro erreur | la commande du projet | à chaque édition |
| Couverture | lignes changées **≥ 80 %** | la commande du projet | fin de tranche |
| Latence | réponse **≤ 200 ms** | banc de mesure | fin de tranche |

## Exceptions tracées

| Réf | Ce qui est exempté | Pourquoi, et jusqu'à quand |
|---|---|---|
```

**L'opérateur de comparaison n'est pas décoratif.** Un seuil qui baisse ne
desserre pas toujours : une couverture qui passe de 80 à 50 % desserre, un
budget de latence qui passe de 200 à 100 ms resserre. C'est `≥` ou `≤` qui le
dit, et c'est ce que le garde lit. Un seuil écrit sans opérateur est signalé
comme « direction indéterminée » : le garde demande un humain plutôt que de
deviner.

**Le nombre se lit tel qu'il s'écrit.** « 4 560 » et « 4560 » sont le même
nombre : le garde ôte **tout blanc** séparant les milliers — espace ordinaire,
insécable (U+00A0), fine (U+2009), fine insécable (U+202F), tabulation — avant de
comparer, et le constat montre les écritures entières (« 4 560 → 5 000 », jamais
« 4 → 5 »). Un simple reformatage ne passe donc pas pour un seuil qui bouge, et
un relèvement écrit avec une espace fine ne passe pas en silence.

**Deux lignes ne s'apparient que si elles portent autant de nombres.** Le garde
apparie les seuils d'une ligne à ceux de la **même** ligne — son premier champ —
nombre pour nombre. Si la ligne en gagne ou en perd un, il **refuse
l'appariement** et rend `seuil-modifie`, direction indéterminée : deux nombres
d'une même ligne ne mesurent pas forcément la même chose (« 87 lignes » et
« 80 % »), et il ne devine pas ce que le chiffre nouveau mesure. Sans ce refus,
« `≥ 87 %` » devenu « `≥ 87 lignes, et ≥ 80 %` » passait sans un mot : les deux
premiers nombres étaient comparés — 87 contre 87 —, le second n'avait pas de
vis-à-vis, et la boucle passait au suivant. Le refus ne peut qu'**ajouter** des
constats : à nombre de nombres égal, la comparaison est exactement celle d'avant.

**Un seuil sans opérateur reste protégé.** « **100 %** couverts » est une barre
même sans `≥` : la descendre est un desserrement. Le garde surveille donc **tous**
les nombres d'une ligne de seuil, jamais seulement ceux qui suivent un
comparateur — ne garder que ces derniers laisserait filer celui-là.

## 4. Le garde-plancher

Le plancher ne se vérifie par aucun outil du marché : c'est un contrôle sur le
**diff**. Sans implémentation livrée, chaque agent réinvente la sienne et deux
exécutions donnent deux résultats — exactement le flottement que ce skill
existe pour supprimer.

```bash
python3 IA/skills/plancher-qualite/scripts/garde_plancher.py --depot <dépôt> --base main
```

**Le garde est lu ailleurs, à sa source.** La CI d'OBSIA-UI exécute ce script
tel qu'il est sur la branche par défaut de ce dépôt, sans copie : un changement
de `garde_plancher.py` s'applique à la prochaine exécution de la CI de ses PR, sans
pull request de ce côté-là. Toute PR qui le touche se fait donc relire par le
`contradicteur` (`revue-de-code`) **en pensant à OBSIA-UI** : ce qui deviendrait
rouge, ou vert à tort, sur ses PR ouvertes.

| Il cherche | Dans |
| --- | --- |
| un vérificateur qu'on a fait taire | les lignes **ajoutées** |
| un test allégé — `skip`, fichier supprimé, assertion retirée | les lignes ajoutées **et** retirées, et les fichiers supprimés ; une assertion se juge **par portée survivante**, sur l'arbre syntaxique ; un saut définitif, sur l'arbre |
| du travail inachevé — stub, `catch` vide, `TODO` | les lignes ajoutées |
| un seuil desserré | `CONSTRAINTS.md`, selon l'opérateur |
| une exception ajoutée au plancher | `CONSTRAINTS.md` |

Sortie : **0** propre, **1** au moins une violation, **2** n'a pas pu tourner.
Un 2 ne se lit jamais comme un 0 — un garde qui n'a pas tourné n'a rien
approuvé.

**Le garde se compte, et se budgette.** Chaque passage imprime « *N lecture(s)
pour un plafond de M* », où M vaut `2 × fichiers modifiés + 1 × (ajoutés +
supprimés) + 2`. Une **lecture** est un fichier dont le garde a eu besoin du
contenu, quel que soit le moyen : deux versions du même fichier comptent pour
deux, une relecture du même contenu pour une. Au-delà du plafond il rend un
constat `budget-de-lectures`, que **aucune exception ne couvre** — un budget
qu'une ligne lève n'est pas un budget. La suite du projet se compte de la même
façon, avec `scripts/banc_de_processus.py`, et un plafond chiffré dans
`CONSTRAINTS.md`. Les deux mesurent un **coût** : on n'économise pas des
processus en achetant du couplage entre tests. Le compteur a une **limite de
profondeur** : il vit dans le processus de la suite, donc un test qui lance un
script qui lance lui-même des processus n'est compté qu'au premier étage — neuf
scripts du dépôt lancent des processus. Le biais est constant, le plafond reste
cohérent ; la conséquence utile est qu'**un test qui externalise du travail dans
un sous-processus échappe au budget** — le budget ne se contourne pas par là, il
se contournerait en trichant.

**Une portée, pas un test.** La comparaison porte sur toute portée survivante —
test, fonction d'aide, méthode, module (`<module>`) —, par nom qualifié : une
aide qui perd son `assert` se voit comme un test qui perd son `assertEqual`, et
le constat nomme la portée (`_aide_avec_assert : 1 → 0 assertions`). Les portées
à zéro assertion restent dans la carte, sinon perdre la **dernière** ressemblerait
à une fonction effacée. **Extraire** des assertions d'un test vers une aide
légitime allège le test et **rougit** — c'est voulu ; l'acquitter se fait par une
exception `E<n>`, qui porte sur le **fichier** (glob `fnmatch`, comme
`.plancherignore`) et non sur le test ni sur la ligne.

**Un test qu'on n'exécute plus.** Le garde relève deux formes seulement, parce
que les autres sont honnêtes : un `skipIf`/`skipUnless` à **condition constante**
(`True`, `False`, leur négation) et un `self.skipTest(…)` **énoncé nu** dans le
corps d'un test, hors de tout `if`, `try` ou boucle. Un saut conditionnel sur
l'environnement (`sys.platform`, `shutil.which(…)`) reste légitime et se tait.
Mesure d'avant implémentation : zéro constat sur les 120 derniers commits, pour
une trentaine de `skipIf` conditionnels dans le dépôt — la règle n'a pas de bruit
à acquitter.

**Ce qu'il ne sait pas peser : ni la force d'une assertion, ni son exécution.**
Il compte des nœuds ; `self.assertEqual(v.refus.controle, "absence de secret")`
remplacé par `self.assertTrue(True)` le laisse à 2 → 2 et il rend 0, et une
assertion déplacée sous `if False:` ou dans une boucle `range(0)` compte pareil.
C'est une limite du comptage, écrite pour ne pas être prise pour une garantie.
Dans le même voisinage il attrape encore : une assertion retirée d'un test ou
d'une aide, un test sauté sans condition, un fichier de test supprimé.

Trois propriétés à connaître :

- **Resserrer est silencieux, desserrer est bruyant.** Rien n'est signalé
  quand la barre monte.
- **Il ne voit que les portées qui restent.** Une portée renommée ou effacée
  n'est plus comparable à rien : le détecteur « un `def test_` a disparu » a été
  **mesuré** — 9 constats sur les 120 derniers commits, dont deux renommages
  purs, pour un seuil fixé d'avance à 3 — puis écarté. Ne le réinvente pas sans
  une nouvelle mesure.
- **Le plafond de processus se relève, mais pas pour finir vert.** Le *lead* du
  chantier re-mesure avec `scripts/banc_de_processus.py`, quand une tranche qui
  touche la suite en a un besoin légitime : re-mesure → `mesure + 2 %` → mise à
  jour de `MESURE`/`PLAFOND` dans le banc **et** du chiffre de `CONSTRAINTS.md`
  (un test tient les deux ensemble). La PR dit ce qui a été ajouté, combien de
  processus cela coûte et pourquoi ce coût est justifié ; relever sans le dire
  dans la description est un défaut de livraison. La procédure complète est dans
  `CONSTRAINTS.md`, section « Comment le plafond de processus se relève ».
- Il **ne cherche pas les secrets**, et ne rapporte jamais la valeur trouvée
  — seulement la règle et l'emplacement. Les secrets relèvent du `.gitignore`
  posé par `amorcage-du-projet` et du §4 du contrat.

Un chemin légitimement hors périmètre s'exempte par un `.plancherignore` à la
racine du dépôt, un motif par ligne : une exemption devient alors un fichier
suivi par Git, donc visible en revue, au lieu d'une règle assouplie.

Le garde est volontairement superficiel : il attrape les raccourcis qu'un
agent prend vraiment, pas un humain déterminé à contourner. C'est le bon
compromis pour un contrôle qui tourne à chaque diff.

## 5. Les exceptions

Une exception se **trace**, elle ne se négocie pas en silence : une ligne dans
le tableau, avec sa raison et son échéance. Le garde la signale — c'est
voulu. Une exception visible qu'on assume vaut mieux qu'un seuil discrètement
abaissé.

## Rationalisations

| Ce qu'on se dit | La réalité |
| --- | --- |
| « je remettrai le test après » | le `skip` restera. Un test ignoré est un test mort, et personne ne saura pourquoi |
| « ce `type: ignore` est temporaire » | rien n'est plus durable qu'un contournement qui a marché une fois |
| « le seuil était trop ambitieux » | peut-être. Alors on le change en revue, avec la raison écrite — pas dans le commit qui en avait besoin |
| « le garde ne comprend pas mon cas » | c'est possible : il y a `.plancherignore` pour ça, et il laisse une trace |
| « on mettra les contraintes quand le projet sera sérieux » | le moment où on en a besoin est celui où l'agent produit plus que ce qu'on relit, soit dès la première tranche |

## Contraintes

`CONSTRAINTS.md` et `.plancherignore` vivent dans le dépôt du projet
(§7.3 de `../../system/VAULT-CONTRACT.md`), jamais dans `OBSIA/`. Le garde ne
modifie rien : il lit un diff et rend un code de sortie.

Ce skill a besoin d'un utilisateur joignable pour ses quatre questions. Dans
un déclenchement automatique — une tâche planifiée, une boucle — appliquer le
**plancher** seul, le dire, et laisser le reste à un humain.
