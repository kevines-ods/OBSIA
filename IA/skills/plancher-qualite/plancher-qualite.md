---
schema: 1
kind: skill
name: plancher-qualite
description: Écrire le niveau de qualité d'un projet dans un `CONSTRAINTS.md` chiffré, puis le faire tenir par un garde qui lit le diff et refuse les cinq gestes qui passent au vert sans améliorer le code — faire taire un vérificateur, alléger un test, laisser un travail inachevé, desserrer un seuil, négocier la règle. À charger à l'amorçage d'un projet, ou dès qu'un agent contourne un contrôle. Ne détecte pas les secrets.
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

## 4. Le garde-plancher

Le plancher ne se vérifie par aucun outil du marché : c'est un contrôle sur le
**diff**. Sans implémentation livrée, chaque agent réinvente la sienne et deux
exécutions donnent deux résultats — exactement le flottement que ce skill
existe pour supprimer.

```bash
python3 IA/skills/plancher-qualite/scripts/garde_plancher.py --depot <dépôt> --base main
```

| Il cherche | Dans |
| --- | --- |
| un vérificateur qu'on a fait taire | les lignes **ajoutées** |
| un test allégé — `skip`, fichier supprimé, assertion retirée | les lignes ajoutées **et** retirées, et les fichiers supprimés |
| du travail inachevé — stub, `catch` vide, `TODO` | les lignes ajoutées |
| un seuil desserré | `CONSTRAINTS.md`, selon l'opérateur |
| une exception ajoutée au plancher | `CONSTRAINTS.md` |

Sortie : **0** propre, **1** au moins une violation, **2** n'a pas pu tourner.
Un 2 ne se lit jamais comme un 0 — un garde qui n'a pas tourné n'a rien
approuvé.

Deux propriétés à connaître :

- **Resserrer est silencieux, desserrer est bruyant.** Rien n'est signalé
  quand la barre monte.
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
