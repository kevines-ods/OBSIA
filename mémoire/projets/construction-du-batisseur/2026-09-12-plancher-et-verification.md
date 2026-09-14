# 2026-09-12 — Quatre skills reprises d'addyosmani, dont un garde qui tourne

Analyse de `addyosmani/agent-skills` (MIT, 25 skills, 7 780 lignes) et reprise
de quatre manques. Le lot le plus utile n'est pas un texte : c'est un script
de 236 lignes qui refuse un diff baissant le niveau de qualité.

## Statut

🟢 Écrit, et le garde-plancher **éprouvé** sur un dépôt jetable — six cas, dont
deux bugs trouvés et corrigés. Les quatre skills eux-mêmes restent non éprouvés
sur un projet réel.

## Décisions

- **Neuf de leurs 25 skills faisaient déjà ce que `batisseur` fait.** Bonne
  nouvelle plutôt que travail perdu : deux dépôts indépendants ont convergé sur
  la même méthode — cadrer, découper en tranches verticales, reproduire avant
  de corriger, une tranche par livraison.
- **Quatre manques repris** : `plancher-qualite`, `tests-dabord`,
  `verification-aux-sources`, `test-navigateur`. Les trois derniers comblent
  des trous nets ; le premier apporte une idée qu'on n'avait pas du tout.
- **Écarté** : leurs commandes et paquets par harness (§3), le nom `SKILL.md`
  (§5 et §6), et quatre skills dont l'utilisateur n'a pas encore le problème.
- **Le volume ne se reprend pas.** Leurs skills font 311 lignes en moyenne,
  les nôtres 117. Le même contenu utile tient en 544 lignes chez nous contre
  ~1 200 chez eux.

## Évidence

- Le garde de référence du dépôt d'origine est en Node. Réécrit en Python
  bibliothèque standard, comme tous les scripts du coffre.
- Deux bugs trouvés **par le test**, pas par la relecture :
  `git diff --no-index` sort en **1** dès qu'il trouve une différence — traiter
  ce 1 comme un échec faisait ignorer en silence tous les fichiers nouveaux,
  soit précisément là où un test mis en `skip` arrive le plus souvent. Et un
  `lstrip("b/")` sur l'en-tête de diff mangeait le nom de tout fichier
  commençant par `b` : `build/x.py` devenait `uild/x.py`.
- Six cas rejoués après correction : diff propre → 0 ; barre qui monte → 0 et
  silencieux ; les cinq gestes ensemble → 1 et sept constats ; exemption par
  `.plancherignore` → respectée ; hors dépôt git → 2 ; base inexistante → 2.

## Interprétation

**Un seuil qui baisse ne desserre pas toujours.** Le garde de référence
signalait toute baisse de chiffre comme un desserrage — faux : une couverture
qui passe de 80 à 50 % desserre, un budget de latence qui passe de 200 à
100 ms resserre. Notre version lit l'opérateur écrit dans `CONSTRAINTS.md`
(`≥` ou `≤`) pour trancher, et quand il manque, elle dit « direction
indéterminée » au lieu de deviner. C'est le seul endroit où le script demande
un humain, et c'est délibéré.

Leçon plus large : un contrôle qui affirme avec certitude une chose qu'il ne
peut pas savoir est pire qu'un contrôle qui se déclare incapable de trancher.

## Questions ouvertes

- Aucun des quatre skills n'a tourné sur un projet réel.
- Le garde est volontairement superficiel — des expressions régulières. Il
  attrape les raccourcis qu'un agent prend vraiment, pas un humain déterminé.
  Le jour où ça ne suffit plus, il faudra un vrai analyseur.
- Le lot 2 reste à faire : un troisième agent en lecture seule, ses deux
  skills de revue, et le portage de l'étage 2 des évaluations — vérifier que le
  bon skill se déclenche, contrôle qui manque à `verifier_coffre.py` avec 31
  skills.

## Synthèse IA

Trois idées de méthode ont été retenues sans devenir des skills : la table des
rationalisations, désormais une convention de `createur-de-skill` ; l'idée que
les exemptions d'un validateur appartiennent au validateur et non au fichier
contrôlé ; et les trois étages d'évaluation d'un catalogue de skills, dont
l'étage de routage nous manque.

## URLs sources

- https://github.com/addyosmani/agent-skills
