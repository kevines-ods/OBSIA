# /mémoire/ — Substrat de mémoire

La mémoire se partage sur un seul axe : **ce que la note décrit**.

- Ce qui décrit **l'utilisateur** ou **un chantier** est commun à tous les
  agents et vit à la racine.
- Ce qu'un **agent** a appris en travaillant reste dans son dossier, nommé au
  nom de l'agent (jamais `agent 1`, `agent 2`, …).

```
mémoire/
├── sommaire.md                       ← index racine (généré)
├── profil-utilisateur.md             ← faits stables sur l'utilisateur, mis à jour sur place
├── préférences/                      ← goûts et règles transversaux, non datés
│   ├── sommaire.md                   ← (généré)
│   └── licences-et-logiciel-libre.md
├── projets/                          ← un dossier par chantier, notes datées
│   ├── sommaire.md                   ← (généré)
│   └── lancement-coffre/
│       ├── sommaire.md               ← (généré)
│       └── AAAA-MM-JJ-titre.md       ← avancement daté
└── assistant/                        ← un dossier par agent
    ├── sommaire.md                   ← (généré)
    └── expériences/                  ← leçons réutilisables tirées d'un cas réel
        ├── sommaire.md               ← (généré)
        └── index-maintenus-a-la-main.md
```

## Où écrire quoi

| Ce qu'on a appris | Destination | Commun ? |
| --- | --- | --- |
| un fait stable sur l'utilisateur ou sa machine | `profil-utilisateur.md` | oui |
| un goût, une règle qui vaudra ailleurs | `préférences/<sujet>.md` | oui |
| une décision propre à un projet | `projets/<projet>/AAAA-MM-JJ-titre.md` | oui |
| une leçon tirée d'un échec ou d'une réussite | `<agent>/expériences/<sujet>.md` | non — chez l'agent |

Seules les notes de projet sont **datées** : elles racontent une chronologie.
Les autres se corrigent sur place — ce qui change ne s'empile pas.

Dans le doute, écrire dans le projet : une note de projet se distille plus tard
vers `préférences/` ou `expériences/` ; l'inverse fait perdre le contexte.

## Pourquoi le profil et les préférences ne sont pas chez un agent

Ils décrivent **l'utilisateur**, pas l'agent qui les a écrits. Les ranger chez
un agent obligeait les autres à passer par un patch soumis à revue pour
corriger un fait sur leur propre utilisateur. Un projet non plus n'appartient à
personne : un chantier ouvert par un agent et repris par un autre y aurait vu
son histoire coupée en deux dossiers.

Ce qu'un agent apprend sur **sa propre manière de travailler** est la seule
chose qui lui appartienne vraiment — d'où `<agent>/expériences/`.

Détail et règles de nommage : `../IA/system/VAULT-CONTRACT.md` §6.

## Sommaires

Chaque `sommaire.md` porte, pour chaque note, son titre, son statut et un
résumé — tous **prélevés dans la note elle-même**, jamais rédigés à la main. Un
dossier parent reprend de ses enfants leur nombre de notes et leur entrée
représentative.

Il est fait pour décider d'ouvrir une note **sans l'ouvrir**.

> ⚠️ Les `sommaire.md` sont générés. Les régénérer via
> `../scripts/regenerate_sommaire.py`, jamais les éditer à la main
> (cf. `../IA/system/VAULT-CONTRACT.md` §11).
