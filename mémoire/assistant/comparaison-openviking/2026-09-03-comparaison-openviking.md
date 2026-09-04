# 2026-09-03 — Comparaison OBSIA / OpenViking

## Statut
🟢 Analyse terminée. Aucune modification appliquée au coffre : ce document
liste des pistes, il ne les implémente pas.

---

## Ce qu'est OpenViking

`volcengine/OpenViking` — « base de données de contexte auto-évolutive pour
agents IA ». Publié par Volcengine (ByteDance), AGPLv3, ~10k étoiles en
1,5 mois. Serveur Rust + Python, index vectoriel, CLI `ov`, studio web,
déploiement Docker/Helm.

Le point commun avec OBSIA est frappant : OpenViking **refuse lui aussi le
modèle RAG « soupe de vecteurs »** et organise le contexte comme un système
de fichiers hiérarchique, adressable, lisible. Il découpe le contexte en
trois types — **Resource / Memory / Skill** — exactement la trichotomie
qu'OBSIA appelle ressource externe / mémoire / skill.

La divergence est tout aussi nette : OpenViking est une **infrastructure
serveur** (AGFS, index vectoriel, files asynchrones, LLM appelé à l'écriture
pour résumer). OBSIA est un **contrat en Markdown** que n'importe quel harness
lit. OpenViking a besoin d'être déployé ; OBSIA a besoin d'être lu.

Conséquence : on ne copie pas son architecture, on copie **ses conventions de
fichiers**, qui sont sa vraie trouvaille.

---

## Évidence — ce qu'OpenViking fait et qu'OBSIA ne fait pas

### 1. Trois couches par dossier : L0 / L1 / L2

Chaque dossier porte deux fichiers cachés « sidecar » :

```
viking://resources/docs/auth/
├── .abstract.md      # L0 — 256 caractères max — une phrase
├── .overview.md      # L1 — 4000 caractères max — plan navigable
├── oauth.md          # L2 — contenu intégral
└── jwt.md
```

Règle explicite du projet : *« relevance can be judged before any full file is
read »*. L0 sert au filtrage, L1 au choix, L2 seulement quand c'est décidé.
Les sidecars décrivent un **dossier**, jamais un fichier isolé, et sont
générés de bas en haut (résumés de fichiers → L1 de la feuille → L0 → dossier
parent).

Le frontmatter des sidecars porte un champ `freshness` :

```yaml
freshness:
  total_entries: 3
  sampled_entries: 3
  pending_child_changes: 0
```

`pending_child_changes > 0` signifie : ce résumé est lisible mais en retard sur
son contenu.

**État d'OBSIA** : `sommaire.md` existe et est régénéré par script — l'idée est
déjà là. Mais il ne contient qu'un tableau nom / type. Aucune description,
aucun résumé. C'est de la navigation, pas de la sélection : pour savoir si une
note est pertinente, il faut l'ouvrir.

### 2. Sous-types de mémoire nommés

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
| `identity` / `soul` | `~/memories/*.md` | nom, ton, principes, limites de l'agent |

Chaque type est défini par un YAML (`memory_type`, `fields`, `merge_op`,
`filename_template`, `directory`, `operation_mode: upsert`).

**État d'OBSIA** : la mémoire est **plate et purement chronologique** —
`mémoire/<agent>/<projet>/AAAA-MM-JJ-titre.md`. Un fait stable sur
l'utilisateur (distribution Linux, préférence logiciel libre, niveau en
codage) n'a nulle part où vivre : il finit noyé dans une note datée d'un
projet, et se re-demande à chaque session.

### 3. Le commit de session déclenche une extraction

`session.commit()` archive la conversation (synchrone) **puis** extrait en
arrière-plan les préférences, entités et expériences durables vers la mémoire
long terme. Le résultat compte ce qui a été extrait
(`memories_extracted`). L'archive brute et le savoir distillé sont deux
choses séparées.

**État d'OBSIA** : le §9 du contrat demande une note de session
(`IA/system/session-log/AAAA-MM-JJ.md`) — décisions, fichiers modifiés,
questions ouvertes. C'est **l'archive**, pas la distillation. Rien ne remonte
vers la mémoire réutilisable.

### 4. Le skill est un dossier, pas un fichier

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

**État d'OBSIA** : un skill = un fichier `.md` plat. Les descriptions de
`skills-index.md` sont des étiquettes de contenu, pas des déclencheurs :
« Manipuler des PDF », « Piloter des conteneurs Docker ». Elles disent ce que
le skill *est*, pas quand il faut l'ouvrir — or c'est exactement la décision
que l'agent doit prendre.

### 5. Les prompts sont des gabarits versionnés

`openviking/prompts/templates/<catégorie>/*.yaml`, avec `metadata.id`,
`variables`, `template` (Jinja2), `output_schema`, `llm_config`. Modifiables
sans toucher au code.

**État d'OBSIA** : le texte du prompt système est **codé en dur** dans
`construire_prompt()` de `scripts/generer_prompt.py`. Modifier une consigne =
modifier du Python.

### 6. Récupération observable

*« Each query preserves its directory-browsing trajectory. When a result looks
wrong, you can see exactly which path produced it. »* Le chemin parcouru est
conservé, donc une mauvaise réponse est débogable.

**État d'OBSIA** : le §10.4 du contrat exige déjà de citer les chemins
utilisés. Le principe est acquis ; il manque le *pourquoi* de chaque ouverture.

### 7. Le dépôt se vérifie lui-même

OpenViking a `tests/`, `build_support/`, CI, `CONTRIBUTING.md`, `SECURITY.md`,
`RELEASE.md`.

**État d'OBSIA** : `.github/` ne contient que `dependabot.yml`. Aucun workflow.
Rien ne garantit qu'un frontmatter est valide, qu'un `name` correspond au nom
du fichier, qu'un skill déclaré par l'agent existe, ou qu'un `sommaire.md` est
à jour. Le contrat pose des règles strictes que **rien ne contrôle**.

---

## Interprétation — ce qui vaut la peine d'être copié

Classé par rapport valeur / effort. Rien ici n'exige de serveur, d'index
vectoriel ni d'appel LLM : ce sont des conventions de fichiers.

| # | À copier | Effort | Gain |
|---|---|---|---|
| 1 | Descriptions « quoi + quand + quand pas » | très faible | fort |
| 2 | `sommaire.md` enrichi = un vrai L1 | faible | fort |
| 3 | Sous-types de mémoire (`profil.md`, `préférences/`, `expériences/`) | faible | fort |
| 4 | Validation du coffre en CI | moyen | fort |
| 5 | Skill-dossier avec `references/` | moyen | moyen |
| 6 | Clôture de session : archive **et** distillation | moyen | moyen |
| 7 | Gabarits de prompt hors du code Python | moyen | faible |

### 1. Réécrire les 12 descriptions de skills

Coût : une heure d'écriture, zéro code. C'est le levier le plus rentable du
lot, parce que le contrat §10.2 demande à l'agent de choisir ses skills à
partir de l'index seul — et l'index actuel ne lui en donne pas les moyens.

Avant — la ligne de `skills-index.md` :
```markdown
| [pdf](../skills/pdf.md) | outil | Manipuler des PDF | assistant |
```
Après, dans le frontmatter du skill, sur **une seule ligne physique** :
```yaml
description: Extraire texte et tableaux, fusionner, découper, pivoter, chiffrer, remplir des formulaires, appliquer l'OCR sur des PDF. À charger dès qu'un fichier .pdf est en entrée ou en sortie. Pas pour Word, Excel ou PowerPoint — voir `bureautique`.
```

Le scalaire replié YAML (`description: >` suivi de lignes indentées) est
**exclu** : `lire_frontmatter()` de `scripts/generer_prompt.py` ne le gère pas
et renvoie littéralement `>` comme description. Vérifié le 2026-09-03.

### 2. Faire du `sommaire.md` une couche L1

`regenerate_sommaire.py` sait déjà parcourir l'arborescence. Il suffit qu'il
lise, pour chaque note, son titre H1 et sa ligne de **Statut**, et les mette
dans le tableau. Aucun LLM : l'information est déjà écrite dans les notes.

```markdown
| Élément | Statut | Résumé |
|---|---|---|
| [2026-08-27-lancement-coffre-obsia.md](…) | 🟢 Actif | Fondations posées : orchestration, multi-fournisseur, coffre Obsidian |
```

Ajouter en tête du fichier un paragraphe d'une ligne décrivant le dossier =
l'équivalent du L0, et le tableau = le L1. La règle « jamais édité à la main »
du §2 tient toujours, puisque tout est dérivé.

### 3. Ouvrir des sous-types de mémoire

Le découpage actuel `mémoire/<agent>/<projet>/` est bon pour ce qui est daté et
lié à un projet. Il lui manque un endroit pour ce qui est **stable et
transversal**. Proposition minimale, trois entrées seulement :

```
mémoire/assistant/
├── profil.md          # faits durables sur l'utilisateur
├── préférences/       # une note par sujet — licences, distribution, style
├── expériences/       # leçons réutilisables : cause racine + correctif
└── <projet>/          # inchangé — les notes datées
```

`profil.md` est celui qui change tout au quotidien : il évite de re-expliquer à
chaque session le contexte CachyOS/KDE, la préférence pour le logiciel libre,
et le niveau souhaité d'explication du code.

Attention : cela suppose de modifier le §6 du contrat, qui fige aujourd'hui la
structure en `mémoire/<agent>/<projet>/AAAA-MM-JJ-titre.md`. À faire par patch.

### 4. Un contrôle automatique du coffre

Un script `scripts/verifier_coffre.py` + un workflow GitHub qui échoue si :

- un frontmatter est absent, invalide, ou son `name` ≠ nom du fichier ;
- une liste est écrite `skills: a, b` au lieu de tirets YAML (piège déjà
  signalé dans le README, mais jamais vérifié) ;
- un agent déclare un skill ou un MCP qui n'existe pas dans `IA/skills/`
  ou `IA/MCP/` ;
- un skill existe sans apparaître dans `skills-index.md` ;
- `regenerate_sommaire.py` produit un diff non vide (l'équivalent pauvre et
  fiable du `pending_child_changes` d'OpenViking).

`generer_prompt.py` contient déjà la moitié de cette logique : `lire_frontmatter()`
et `collecter()` émettent des avertissements sur stderr. Il suffit de les
transformer en code de sortie non nul.

### 5. Autoriser le skill-dossier

Un skill reste `IA/skills/<nom>.md` par défaut, mais peut devenir
`IA/skills/<nom>/<nom>.md` avec un `references/` à côté quand il grossit. Le
corps du skill ne garde que la procédure ; les tableaux de commandes, les
pièges rares et les exemples longs partent dans `references/`. C'est le même
mécanisme de chargement paresseux que le README revendique déjà au niveau de
l'index, appliqué un cran plus bas.

Bénéfice secondaire : c'est la convention Agent Skills d'Anthropic
(`SKILL.md` + `references/`), donc un skill OBSIA devient importable ailleurs,
et réciproquement.

### 6. Séparer l'archive de la distillation en fin de session

Le §9 produit aujourd'hui un journal. Y ajouter une seconde étape : relire ce
journal et en extraire ce qui mérite de survivre au projet — une préférence
(→ `préférences/`), une leçon (→ `expériences/`), un fait sur l'utilisateur
ou sa machine (→ `profil.md`). Formalisable en un skill `cloture-de-session`.

C'est le mécanisme « self-evolving » d'OpenViking réduit à sa forme manuelle —
et la forme manuelle suffit, parce qu'un humain relit le patch.

---

## Ce qu'il ne faut PAS copier

- **L'index vectoriel, AGFS, le serveur Rust, Helm, Docker.** Ils contredisent
  frontalement la promesse du README d'OBSIA : « pas de base de données, pas de
  format propriétaire ; le coffre se lit et s'édite à la main ». Un coffre
  Obsidian n'a pas besoin d'être déployé.
- **La génération LLM des L0/L1 à l'écriture.** Coûteuse, asynchrone, elle
  exige un serveur et des files d'attente. OBSIA peut extraire les mêmes
  résumés de façon déterministe depuis le titre et le statut déjà écrits dans
  ses notes.
- **Multi-tenant, ACL, chiffrement, quotas, WebDAV.** Réponses à un problème
  d'hébergeur multi-clients. OBSIA a un utilisateur.
- **Les 24 fichiers d'API et le SDK.** OBSIA n'expose pas d'API : il expose des
  fichiers.
- **`identity.md` / `soul.md`.** Techniquement copiables, mais ils décrivent le
  ton et la personnalité de l'assistant — ce qu'OBSIA place déjà, et mieux,
  dans `IA/agents/assistant.md`. Les dupliquer créerait deux sources de vérité,
  ce que le contrat interdit.

---

## Licence

OpenViking : **AGPLv3** pour le projet principal, Apache 2.0 pour `crates/ov_cli`
et `examples/`. OBSIA : **AGPL-3.0-or-later**.

Les deux sens sont praticables : AGPLv3 → AGPLv3 est identique, et
Apache 2.0 → AGPLv3 est une compatibilité admise dans ce sens uniquement.
Aucun obstacle, donc — y compris pour reprendre du texte de gabarit ou de
documentation, à condition de citer la source, comme l'exige le §8 du contrat.

Réserve : les conventions décrites ici (trois couches, sous-types de mémoire,
skill-dossier) sont des **idées d'organisation**, pas du code. Les reprendre ne
crée pas d'œuvre dérivée. Copier littéralement un fichier YAML de gabarit, si.

---

## Synthèse IA

OpenViking et OBSIA ont eu la même intuition — le contexte d'un agent est une
arborescence de fichiers, pas un nuage de vecteurs — et l'ont poussée à deux
échelles opposées : une infrastructure serveur d'un côté, un contrat Markdown
de l'autre.

Ce qu'OBSIA a de meilleur, OpenViking ne l'a pas : un contrat unique qui fait
foi, une séparation nette agent / skill / MCP, et l'indépendance vis-à-vis de
tout harness.

Ce qui manque à OBSIA tient en une phrase : **ses index savent où sont les
choses, pas ce qu'elles valent.** `sommaire.md` liste, `skills-index.md`
étiquette, mais ni l'un ni l'autre ne permet de décider sans ouvrir. La couche
L0/L1 d'OpenViking est précisément la réponse à ce manque, et elle est copiable
sans une ligne d'infrastructure : les résumés sont déjà écrits dans les notes,
il suffit de les remonter.

Second manque, plus discret : **le contrat n'est vérifié par rien.** Un dépôt
dont toutes les règles reposent sur la bonne volonté du lecteur dérive. Un
workflow CI de cinquante lignes réglerait ça.

Ordre suggéré, du plus rentable au moins : descriptions de skills → sommaires
enrichis → `profil.md` → vérification CI → le reste.

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
