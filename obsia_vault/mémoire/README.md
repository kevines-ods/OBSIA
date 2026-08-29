# /mémoire/ — Substrat de mémoire

Chaque sous-dossier `<agent>/` est l'espace mémoire d'un agent, nommé **au nom
de l'agent** (jamais `agent 1`, `agent 2`, …). La hiérarchie est :

```
assistant/
├── sommaire.md                  ← index global de l'agent (généré)
├── lancement-coffre/
│   ├── sommaire.md              ← index du projet (généré)
│   └── AAAA-MM-JJ-titre.md      ← entrées de projet datées
├── recherche-contextuelle/
├── stack-tauri/
└── automatisation-bureautique/
```

Règle (cf. `IA/system/VAULT-CONTRACT.md` §6) : les dossiers portent le **nom de
l'agent** et le **nom du projet** — jamais `agent 1`, `projets 2`, etc.

**Rétroliens** : chaque `sommaire.md` énumère ses sous-dossiers + un court résumé.
C'est ce qui permet à l'agent de **découvrir le contexte** sans deviner.

> ⚠️ Régénère toujours les `sommaire.md` via `scripts/regenerate_sommaire.py`,
> jamais à la main (garde la fiabilité du diff Git).
