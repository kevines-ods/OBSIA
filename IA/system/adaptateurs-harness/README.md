# Adaptateurs harness — gabarits d'intégration

> **Statut : gabarits, non normatifs.** Les règles du coffre vivent dans
> `../VAULT-CONTRACT.md`, qui fait foi. Ce dossier recueille des **exemples
> d'intégration** : comment brancher un harness donné sur OBSIA et sur le
> coffre parent. Les noms de harness n'apparaissent qu'ici, dans les gabarits,
> jamais dans les règles — parce qu'un gabarit sert justement à brancher un
> outil précis.

## Pourquoi ce dossier

Le coffre décrit *quoi* faire, le harness fournit *avec quoi*. Ce qui est
portable (agents, skills, tâches, mémoire, registre des tags) vit dans OBSIA.
Ce qui ne l'est pas — la manière dont un harness précis accède au coffre — se
reconfigure à chaque changement de harness. Ces gabarits réduisent cette
friction à quelques minutes, sans faire dépendre OBSIA d'aucun harness.

## Les trois besoins communs (détail : `commun.md`)

1. **charger le cerveau** — prompt système / `CLAUDE.md` / index ;
2. **atteindre le coffre parent** — la racine du coffre (parent du dépôt),
   pas seulement `OBSIA/` ;
3. **connaître les repères** — racine du coffre, `_maintenance/`, registre des
   tags.

## Règle d'or

La **configuration réelle** (chemins, clés) vit **hors du dépôt**. Ces
gabarits ne contiennent que des chemins fictifs, à remplacer localement — un
gabarit rempli ne se re-versionne pas.

## Fiches

- `claude-code.md` — Claude Code
- `opencode.md` — OpenCode
- `deepseek-harness.md` — DeepSeek Harness (DSH)
- `openclaw.md` — OpenClaw 2.0
- `aionui-obsiaui.md` — AionUi / ObsiaUi (interface)
- `librechat.md` — LibreChat
