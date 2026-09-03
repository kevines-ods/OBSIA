# 2026-09-03 — Réécriture des descriptions de skills

Application du point 1 de
[[2026-09-03-comparaison-openviking]] : donner à chaque skill une description
qui dise **quoi, quand, et quand pas**.

## Statut
🟢 Appliqué — 12 skills + `IA/system/skills-index.md`.

---

## Décisions

- **Le frontmatter fait foi.** `IA/system/skills-index.md` reproduit désormais
  le champ `description` mot pour mot. En cas de divergence, c'est l'index
  qu'on corrige, jamais le skill.
- **Une seule ligne physique, obligatoire.** Le scalaire replié YAML
  (`description: >` puis lignes indentées) est interdit dans ce coffre : le
  lecteur de frontmatter de `scripts/generer_prompt.py` ne le gère pas. Voir
  l'évidence ci-dessous. Les descriptions font entre 233 et 301 caractères,
  toutes sur une ligne.
- **Le « quand pas » renvoie vers le skill concurrent**, pas vers le vide :
  `pdf` ↔ `bureautique`, `diagnostic-linux` → `remediation-linux`,
  `traefik` ↔ `conteneurs-docker`. Ce sont les trois confusions réellement
  possibles dans le coffre actuel.
- **Colonne renommée** dans l'index : « Description courte » → « Description —
  quoi, quand, quand pas ». L'ancien intitulé encourageait la troncature qui
  était précisément le problème.

---

## Évidence

**Le scalaire replié casse le parser.** Test conduit sur un coffre jetable :

```yaml
description: >
  Ligne un.
  Ligne deux.
```

`python3 scripts/generer_prompt.py` produit :

```
- **plie** [lecture seule] — >
```

La description vaut le caractère `>`. Cause : `lire_frontmatter()`
(`scripts/generer_prompt.py`) fait `cle, _, valeur = nu.partition(":")` et
stocke `valeur` telle quelle ; les lignes de continuation, dépourvues de `:`,
tombent dans `if ":" not in nu: continue`. Une description longue sur une seule
ligne, y compris avec virgules, tirets cadratins et deux-points, passe en
revanche sans dommage — testé également.

**Deux descriptions étaient fausses.**

- `mermaid` annonçait une sortie « en SVG ou en ASCII », alors que le corps du
  même fichier dit : *« La sortie ASCII pour terminal n'existe pas dans
  `mermaid-cli` »*. Corrigé en « en SVG ».
- `skills-index.md` attribuait `proxmox` et `traefik` à l'agent `assistant`,
  alors que `IA/agents/assistant.md` ne les déclare pas dans sa liste `skills`.
  L'index régénéré depuis les frontmatters affiche désormais `—`.

---

## Interprétation

L'écart `proxmox` / `traefik` n'est pas une coquille d'index : c'est une
**question ouverte sur le périmètre de l'agent**. Soit `assistant` doit
mobiliser ces deux skills et sa liste est incomplète, soit ils attendent un
agent d'infrastructure qui n'existe pas encore. Le contrat §10 demandant de
demander plutôt que d'agir en cas de doute sur le périmètre, l'index dit la
vérité (`—`) et la décision reste à prendre.

Le fait qu'un index maintenu à la main ait pu mentir pendant des mois sans que
rien ne le signale est l'argument le plus concret en faveur du point 4 de
l'analyse — la vérification automatique. Ici, c'est la simple régénération de
l'index depuis les frontmatters qui a fait tomber l'écart.

---

## Questions ouvertes

- [ ] `assistant` doit-il déclarer `proxmox` et `traefik` ?
- [ ] `skills-index.md` doit-il devenir un fichier généré par script, comme
      `sommaire.md` ? La régénération de ce jour a été faite par un script
      jetable. Le pérenniser relève du point 4.
- [ ] Faut-il apprendre les scalaires repliés à `lire_frontmatter()` plutôt que
      de les interdire ? Une ligne de 300 caractères reste pénible à relire
      dans un éditeur.

---

## Synthèse IA

Le coût réel a été l'inverse de celui annoncé : écrire les douze descriptions
fut rapide, mais les vérifier a révélé deux affirmations fausses que personne
ne pouvait voir, parce que rien ne confrontait l'index aux fichiers. Le gain
immédiat est que l'agent peut désormais choisir ses skills depuis le seul
index, comme le §10.2 du contrat le lui demande ; le gain durable est d'avoir
établi une source unique entre le frontmatter et l'index.

## URLs sources

- Convention « quoi + quand + quand pas », exemple d'origine :
  https://github.com/volcengine/OpenViking/blob/main/agent-plugins/skills/openviking-memory/SKILL.md
