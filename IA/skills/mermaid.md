---
schema: 1
kind: skill
name: mermaid
description: Générer des diagrammes Mermaid en SVG — flux, séquences, états, classes, entités. À charger quand une structure, un enchaînement ou une machine à états se lit mieux en image qu'en texte. Inutile pour une simple liste ou un tableau, que le Markdown rend déjà.
module: diagrammes
type: outil
read_only: false
---

# Skill — Mermaid

Produit des diagrammes à partir de code Mermaid. Utile pour visualiser une
arborescence du coffre, un flux de décision d'agent, ou une machine à états.

> **Adaptation.** La version d'origine (AionUi) appelait un script maison
> `scripts/render.ts` reposant sur la bibliothèque `beautiful-mermaid`. Ce
> script n'est pas fourni de manière portable, donc cette version utilise
> `@mermaid-js/mermaid-cli`, l'outil officiel, installable partout par npm.

## Prérequis

```bash
# via npm (recommandé, pas d'installation système)
npx -y @mermaid-js/mermaid-cli -h

# ou en paquet système, là où la distribution en fournit un
#   (`mermaid-cli` existe sur l'AUR ; ailleurs, npm reste la voie sûre)
```

`-h` répond même quand la génération échouera : il prouve l'installation, pas
le rendu. Sous le capot, `mermaid-cli` pilote un Chromium par Puppeteer, et ce
Chromium refuse de démarrer là où il n'y a ni session graphique ni utilisateur
non privilégié — conteneur, VM sans bureau, intégration continue. L'erreur
vient alors de `@puppeteer/browsers`, sans jamais nommer Mermaid.

Le prérequis à vérifier est donc **que la commande arrive au bout**, sur un
diagramme jetable :

```bash
echo "graph LR; A-->B" | npx -y @mermaid-js/mermaid-cli -i /dev/stdin -o /tmp/essai.svg
```

Si elle échoue, passer une configuration Puppeteer avec `-p` :

```bash
echo '{"args":["--no-sandbox","--disable-gpu","--disable-dev-shm-usage"]}' > pptr.json
npx -y @mermaid-js/mermaid-cli -p pptr.json -i diagramme.mmd -o diagramme.svg
```

Ces options désactivent des protections du navigateur : elles se réservent à la
machine sans bureau qui les exige. Sur un poste avec session graphique elles
sont inutiles, et les traîner par habitude affaiblit le navigateur pour rien.

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
  agent[assistant] --> skill[obsidian-manager]
  skill --> coffre[(OBSIA)]
​```
```

## Contraintes

Ce skill écrit des fichiers. Les règles de preview et d'écriture du coffre
s'appliquent : voir `../system/VAULT-CONTRACT.md`.
