# /mémoire/ — Substrat de mémoire

Chaque sous-dossier `<agent>/` est l'espace mémoire d'un agent, nommé **au nom
de l'agent** (jamais `agent 1`, `agent 2`, …).

La mémoire distingue ce qui est **daté** de ce qui est **durable** :

```
assistant/
├── sommaire.md                       ← index de l'agent (généré)
├── profil-utilisateur.md             ← faits stables sur l'utilisateur, mis à jour sur place
├── préférences/                      ← goûts et règles transversaux, non datés
│   ├── sommaire.md                   ← (généré)
│   └── licences-et-logiciel-libre.md
├── expériences/                      ← leçons réutilisables tirées d'un cas réel
│   ├── sommaire.md                   ← (généré)
│   └── index-maintenus-a-la-main.md
└── lancement-coffre/                 ← un dossier par projet
    ├── sommaire.md                   ← (généré)
    └── AAAA-MM-JJ-titre.md           ← avancement daté
```

## Où écrire quoi

| Ce qu'on a appris | Destination |
| --- | --- |
| un fait stable sur l'utilisateur ou sa machine | `profil-utilisateur.md` |
| un goût, une règle qui vaudra ailleurs | `préférences/<sujet>.md` |
| une leçon tirée d'un échec ou d'une réussite | `expériences/<sujet>.md` |
| une décision propre à un projet | `<projet>/AAAA-MM-JJ-titre.md` |

Les trois premières ne sont **pas datées** : ce qui change se corrige sur
place. Seules les notes de projet racontent une chronologie.

Dans le doute, écrire dans le projet : une note de projet se distille plus tard
vers `préférences/` ou `expériences/` ; l'inverse fait perdre le contexte.

Détail et règles de nommage : `IA/system/VAULT-CONTRACT.md` §6.

## Sommaires

Chaque `sommaire.md` porte, pour chaque note, son titre, son statut et un
résumé — tous **prélevés dans la note elle-même**, jamais rédigés à la main. Un
dossier parent reprend de ses enfants leur nombre de notes et leur entrée
représentative.

Il est fait pour décider d'ouvrir une note **sans l'ouvrir**.

> ⚠️ Les `sommaire.md` sont générés. Les régénérer via
> `scripts/regenerate_sommaire.py`, jamais les éditer à la main
> (cf. `VAULT-CONTRACT.md` §11).
