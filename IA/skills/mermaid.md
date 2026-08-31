---
schema: 1
kind: skill
name: mermaid
description: Générer des diagrammes Mermaid en SVG ou en ASCII — flux, séquences, états, classes, entités.
type: outil
read_only: false
---

# Skill — Mermaid

Produit des diagrammes à partir de code Mermaid. Utile pour visualiser une
arborescence du coffre, un flux de décision d'agent, ou une machine à états.

> **Adaptation.** La version d'origine (AionUi) appelait un script maison
> `scripts/render.ts` reposant sur la bibliothèque `beautiful-mermaid`. Ce
> script n'est pas fourni de manière portable, donc cette version utilise
> `@mermaid-js/mermaid-cli`, l'outil officiel, disponible sur Arch / CachyOS.

## Prérequis

```bash
# via npm (recommandé, pas d'installation système)
npx -y @mermaid-js/mermaid-cli -h

# ou en paquet AUR sur CachyOS
paru -S mermaid-cli
```

## Utilisation

Depuis un fichier :

```bash
npx -y @mermaid-js/mermaid-cli -i diagramme.mmd -o diagramme.svg
```

Depuis l'entrée standard :

```bash
echo "graph LR; A-->B-->C" | npx -y @mermaid-js/mermaid-cli -i /dev/stdin -o flux.svg
```

Thème sombre :

```bash
npx -y @mermaid-js/mermaid-cli -i diagramme.mmd -o sortie.svg -t dark
```

> La sortie ASCII pour terminal n'existe pas dans `mermaid-cli`. Si tu y tiens,
> `graph-easy` (Perl) fait ça, mais avec une syntaxe différente. À évaluer plus
> tard, ce n'est pas bloquant.

## Types de diagrammes

| Type | Syntaxe | Usage typique |
| --- | --- | --- |
| Flux | `graph TD` / `graph LR` | processus, décisions |
| Séquence | `sequenceDiagram` | échanges agent ↔ outil |
| États | `stateDiagram-v2` | machines à états |
| Classes | `classDiagram` | structure objet |
| Entités | `erDiagram` | schémas de données |

## Intégration au coffre

Obsidian sait afficher Mermaid nativement dans un bloc de code ` ```mermaid `.
Pour une note du coffre, **préférer le bloc Mermaid brut au SVG généré** : il
reste lisible, modifiable, et versionnable en Git. Ne générer un SVG que pour
un usage hors coffre (documentation, export, README GitHub).

```markdown
​```mermaid
graph TD
  agent[bibliothécaire] --> skill[obsidian-manager]
  skill --> coffre[(OBSIA)]
​```
```

## Contraintes

Ce skill écrit des fichiers. Les règles de preview et d'écriture du coffre
s'appliquent : voir `../system/VAULT-CONTRACT.md`.
