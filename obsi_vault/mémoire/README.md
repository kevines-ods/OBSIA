# /mémoire/ — Substrat de mémoire

Chaque sous-dossier `agent N/` est l'espace mémoire d'un agent. La hiérarchie est :

```
agent N/
├── sommaire.md          ← index global de l'agent (généré)
├── projets 1/
│   ├── sommaire.md       ← index du projet (généré)
│   └── AAAA-MM-JJ-titre.md   ← entrées de projet datées
├── projets 2/
└── projets 3/
```

**Rétroliens** : chaque `sommaire.md` énumère ses sous-dossiers + un court résumé.
C'est ce qui permet à l'agent de **découvrir le contexte** sans deviner.

> ⚠️ Régénère toujours les `sommaire.md` via `scripts/regenerate_sommaire.py`,
> jamais à la main (garde la fiabilité du diff Git).
