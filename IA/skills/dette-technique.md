---
schema: 1
kind: skill
name: dette-technique
description: Inventorier la dette technique d'un projet existant — code mort, duplications, TODO et FIXME, dépendances en retard ou abandonnées, zones sans test, contournements — puis la classer par coût et par risque dans `docs/DETTE.md` pour décider quoi rembourser et quand. À charger avant d'étoffer un projet qui a vieilli, ou quand chaque modification coûte plus cher que la précédente. Inventorie et classe : ne corrige rien.
module: construction
type: outil
read_only: false
---

# Skill — Dette technique

Toute dette n'est pas à rembourser. Celle qui dort dans un module qu'on ne
touche jamais ne coûte rien ; celle qui se trouve sur le chemin de la
prochaine fonctionnalité coûte à chaque modification. Ce skill sert à les
distinguer — pas à tout nettoyer.

## Procédure

### 1. Collecter

| Catégorie | Comment la trouver |
| --- | --- |
| aveux dans le code | première commande ci-dessous |
| code mort | l'outil du langage (`vulture`, `ts-prune`, `cargo +nightly udeps`…), sinon les fonctions jamais appelées |
| duplications | l'outil du langage (`jscpd`, `pylint --duplicate-code`…) |
| dépendances | `montee-de-version`, étape 1 : en retard, abandonnées |
| zones sans test | la couverture si l'outil existe, sinon la carte de `reprise-dun-projet` |
| points chauds | fichiers les plus modifiés : seconde commande ci-dessous |

```bash
grep -rnE "TODO|FIXME|HACK|XXX" --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=dist --exclude-dir=build --exclude-dir=vendor --exclude-dir=target --exclude-dir=.venv <dépôt>
git -C <dépôt> log --format= --name-only | sort | uniq -c | sort -rn | head -15
```

Les failles de sécurité ne se collectent pas ici : c'est l'objet de
`audit-de-securite`, porté par le relecteur (module `revue`). Si un audit a
été fait, reprendre ses constats comme entrées ; si le module n'est pas
installé, le dire dans `docs/DETTE.md` : la sécurité n'a pas été regardée.

### 2. Qualifier chaque entrée

Deux notes de 1 à 3, rien de plus fin :

- **coût** — ce que la dette fait payer aujourd'hui : 3 si elle est sur le
  chemin d'un travail prévu ou dans un point chaud, 1 si personne n'y passe ;
- **risque** — ce qui arrive si on ne fait rien : 3 pour une perte de
  données, une faille ou une dépendance abandonnée, 1 pour de l'inconfort.

Et une estimation d'**effort** : petit (moins d'une heure), moyen (une
tranche), gros (à découper).

### 3. Écrire `docs/DETTE.md`

Dans le dépôt du projet, un tableau trié par `coût × risque` décroissant :

```markdown
| # | Dette | Où | Coût | Risque | Effort | Remède |
|---|---|---|---|---|---|---|
| 1 | calcul de remise dupliqué 3 fois | `panier/`, `facture/`, `export/` | 3 | 2 | moyen | `refactoring-sur` |
```

La colonne *Remède* nomme le skill qui le traite : `refactoring-sur`,
`montee-de-version`, `tests-de-caracterisation`, `migration-de-donnees`.

### 4. Proposer, pas imposer

Présenter les cinq premières lignes à l'utilisateur, avec une recommandation :
rembourser maintenant, avant la prochaine fonctionnalité, ou accepter. Une
dette acceptée reste dans le fichier avec sa raison — c'est ce qui évite de
la redécouvrir dans six mois.

Rembourser une dette est une tranche comme une autre, dans `docs/PLAN.md`.

## Rationalisations

| Ce qu'on se dit | La réalité |
| --- | --- |
| « tant qu'on y est, on rembourse tout » | le projet s'arrête des semaines sans rien apporter de visible, puis le chantier est abandonné à moitié |
| « c'est moche, donc c'est de la dette » | du code laid qu'on ne touche jamais ne coûte rien ; le coût se mesure au passage, pas au goût |
| « ce TODO date de trois ans, il n'est plus pertinent » | peut-être — alors il se supprime en le disant, pas en l'ignorant |
| « pas besoin d'écrire, je m'en souviendrai » | la dette non écrite est redécouverte à chaque séance, et payée à chaque fois |

## Ce que ce skill ne fait pas

Il ne modifie pas le code : il écrit `docs/DETTE.md` et propose. Le travail
sur le dépôt suit le §3 de `../system/VAULT-CONTRACT.md`.
