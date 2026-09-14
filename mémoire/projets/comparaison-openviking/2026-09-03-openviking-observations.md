# 2026-09-03 — OpenViking, les sept observations

Évidence relevée dans la documentation d'OpenViking : sept conventions de
fichiers qu'OBSIA n'avait pas. Détachée le 2026-09-09 de
[[2026-09-03-comparaison-openviking]], qui pesait le double du seuil et où
vivent l'interprétation et les décisions.

## Statut
🟢 Évidence figée — constatée le 2026-09-03, non révisée depuis.

---

## 1. Trois couches par dossier : L0 / L1 / L2

Chaque dossier porte deux fichiers cachés « sidecar » :

```
viking://resources/docs/auth/
├── .abstract.md      # L0 — 256 caractères max — une phrase
├── .overview.md      # L1 — 4000 caractères max — plan navigable
├── oauth.md          # L2 — contenu intégral
└── jwt.md
```

Règle explicite du projet : *« relevance can be judged before any full file is
read »*. L0 filtre, L1 choisit, L2 ne s'ouvre qu'une fois décidé. Les sidecars
décrivent un **dossier**, jamais un fichier isolé, et sont générés de bas en
haut (résumés de fichiers → L1 de la feuille → L0 → dossier parent).

Le frontmatter des sidecars porte un champ `freshness` :

```yaml
freshness:
  total_entries: 3
  sampled_entries: 3
  pending_child_changes: 0
```

`pending_child_changes > 0` signifie : ce résumé est lisible mais en retard sur
son contenu.

## 2. Sous-types de mémoire nommés

OpenViking ne stocke pas « des notes ». Il a des types de mémoire déclarés,
chacun avec son emplacement et son gabarit :

| Type | Emplacement | Contenu |
|---|---|---|
| `profile` | `~/memories/profile.md` | qui est l'utilisateur |
| `preferences` | `~/memories/preferences/` | préférences par sujet |
| `entities` | `~/memories/entities/` | personnes, projets, machines |
| `events` | `~/memories/events/` | décisions, jalons |
| `experiences` | `~/memories/experiences/` | leçons réutilisables |
| `trajectories` | `~/memories/trajectories/` | déroulés de tâches réutilisables |
| `identity` / `soul` | `~/memories/*.md` | nom, ton, principes, limites |

Chaque type est défini par un YAML (`memory_type`, `fields`, `merge_op`,
`filename_template`, `directory`, `operation_mode: upsert`).

## 3. Le commit de session déclenche une extraction

`session.commit()` archive la conversation (synchrone) **puis** extrait en
arrière-plan préférences, entités et expériences durables vers la mémoire long
terme, en comptant ce qui a été extrait (`memories_extracted`). L'archive brute
et le savoir distillé sont deux choses séparées.

## 4. Le skill est un dossier, pas un fichier

```
skills/{nom}/
├── .abstract.md
├── .overview.md
├── SKILL.md          # point d'entrée
├── references/       # détails chargés seulement si besoin
└── scripts/
```

Et la `description` du frontmatter dit **quoi ET quand**, y compris quand ne
pas s'en servir. Extrait réel de `openviking-memory/SKILL.md` :

> *« Use at the start of any substantive task (coding, configuration,
> debugging…) … **Do not use** for casual chat or simple factual questions the
> model can answer directly. »*

## 5. Les prompts sont des gabarits versionnés

`openviking/prompts/templates/<catégorie>/*.yaml`, avec `metadata.id`,
`variables`, `template` (Jinja2), `output_schema`, `llm_config`. Modifiables
sans toucher au code.

## 6. Récupération observable

*« Each query preserves its directory-browsing trajectory. When a result looks
wrong, you can see exactly which path produced it. »* Le chemin parcouru est
conservé, donc une mauvaise réponse est débogable.

## 7. Le dépôt se vérifie lui-même

OpenViking a `tests/`, `build_support/`, une CI, `CONTRIBUTING.md`,
`SECURITY.md`, `RELEASE.md`.

---

## État d'OBSIA face à chacune — au 2026-09-03

Constat du jour, conservé tel quel. La colonne de droite dit ce que le coffre
en a fait depuis — écrite le 2026-09-09, à corriger sur place, pas à empiler.

| # | Manque constaté le 2026-09-03 | Depuis |
|---|---|---|
| 1 | `sommaire.md` ne portait qu'un tableau nom / type : navigation, pas sélection — il fallait ouvrir pour savoir | statut et résumé remontés par script |
| 2 | mémoire plate et chronologique ; un fait stable sur l'utilisateur n'avait nulle part où vivre | `profil-utilisateur.md`, `préférences/`, `expériences/` |
| 3 | le §9 produisait une archive, rien ne remontait vers la mémoire réutilisable | skill `cloture-de-session` |
| 4 | un skill = un fichier plat ; les descriptions disaient ce que le skill *est*, pas quand l'ouvrir | forme dossier (§5), descriptions réécrites |
| 5 | le prompt système était codé en dur dans `construire_prompt()` | inchangé — seule piste jamais reprise |
| 6 | le §10.4 exigeait déjà de citer les chemins ; il manquait le *pourquoi* de chaque ouverture | inchangé, jugé acquis |
| 7 | `.github/` ne contenait que `dependabot.yml` ; le contrat posait des règles que **rien** ne contrôlait | `verifier_coffre.py`, CI, crochet de pré-commit |

---

## URLs sources

- Dépôt OpenViking : https://github.com/volcengine/OpenViking
- Couches de contexte L0/L1/L2 : https://github.com/volcengine/OpenViking/blob/main/docs/en/concepts/03-context-layers.md
- Types de contexte (Resource / Memory / Skill) : https://github.com/volcengine/OpenViking/blob/main/docs/en/concepts/02-context-types.md
- Extraction et génération des résumés : https://github.com/volcengine/OpenViking/blob/main/docs/en/concepts/06-extraction.md
- Mécanisme de récupération : https://github.com/volcengine/OpenViking/blob/main/docs/en/concepts/07-retrieval.md
- Sessions et commit : https://github.com/volcengine/OpenViking/blob/main/docs/en/concepts/08-session.md
- Gabarits de prompts : https://github.com/volcengine/OpenViking/blob/main/docs/en/guides/10-prompt-guide.md
- Exemple de SKILL.md : https://github.com/volcengine/OpenViking/blob/main/agent-plugins/skills/openviking-memory/SKILL.md
- Licence : https://github.com/volcengine/OpenViking/blob/main/LICENSE
