---
schema: 1
kind: contract
name: vault-contract
description: Règles communes à tous les agents et skills du coffre OBSIA. Source unique de vérité.
---

# Contrat du coffre — OBSIA

Ce fichier est la **source unique** des règles qui s'appliquent à tous les agents
et tous les skills. Un fichier agent ou skill ne redéfinit jamais ces règles :
il les référence. En cas de contradiction entre ce contrat et un autre fichier,
**ce contrat fait foi**.

Emplacement attendu : `IA/system/VAULT-CONTRACT.md`, depuis la racine du dépôt.

---

## 1. Vocabulaire (à ne pas confondre)

| Terme | Nature | Emplacement | Rôle |
| --- | --- | --- | --- |
| **agent** | un interlocuteur | `IA/agents/` | possède un system prompt, mène une conversation, décide |
| **skill** | une compétence | `IA/skills/` | décrit *comment* faire une chose, ne décide pas |
| **MCP** | un outil | `IA/MCP/` | expose des actions structurées |

Un agent **utilise** des skills. Un skill n'est jamais un agent.

Piège historique à ne pas reproduire : **`obsidian-manager` est un SKILL** ; il a
longtemps été confondu avec un agent « bibliothécaire » qui n'existait pas en
tant que fichier. Toute formulation suggérant qu'un skill est un agent est une
erreur à corriger, pas une convention à suivre.

---

## 2. Écriture dans le coffre

- Le coffre est en **lecture seule pour les agents** dont `read_only: true`.
- Un agent `read_only: false` peut écrire **directement, sans patch**, dans
  trois zones seulement :
  - `brouillon/` — sans restriction ;
  - `mémoire/<son-propre-nom-d'agent>/` — jamais dans le dossier mémoire d'un
    autre agent ;
  - `IA/skills/` — uniquement s'il déclare le skill `createur-de-skill` dans
    son frontmatter.
- Tout le reste du coffre (`IA/agents/`, `IA/system/`, la structure du dépôt)
  reste protégé : toute modification durable y passe par un **patch Git**
  soumis à revue humaine. Les interventions hors du coffre relèvent du §3.
- Aucune suppression sans archivage préalable dans `.archive/`, y compris dans
  une zone en écriture directe.
- Toute action touchant plusieurs fichiers exige un **preview** affiché avant
  exécution, listant les chemins concernés — que l'écriture soit directe ou
  passe par patch.
- Les **fichiers générés** ne sont jamais édités à la main ni par un agent,
  même dans une zone en écriture directe : `sommaire.md`, `agents-index.md` et
  `skills-index.md` sont régénérés par les scripts du §11, qui donne la liste
  complète et la commande.
- Ces trois zones sont les seules **du dépôt**. Hors du dépôt, une quatrième
  zone est en écriture directe : `0-EN VRAC/` dans le coffre parent (§7).

## 3. Périmètre hors du coffre

Ce coffre ne dépend d'aucun harness et n'en connaît aucun : il décrit *quoi*
faire, le harness fournit *avec quoi*. Aucune base de code extérieure n'est
nommée ici, et aucun agent n'en a le monopole.

Quand un agent dont le frontmatter porte `read_only: false` intervient sur un
dépôt extérieur (interface, outillage, infrastructure), les règles suivantes
s'appliquent — elles ne dépendent ni du langage ni du projet :

- Toute modification passe par un **patch Git revu** — jamais de commit direct
  sur la branche par défaut.
- Les vérifications du projet visé (compilation, analyse statique, tests)
  passent **avant** de proposer le patch.
- **Jamais de secret** (clé API, jeton) dans le code : variables
  d'environnement ou configuration hors dépôt uniquement.
- Ajouter une fonctionnalité = d'abord un **skill** documenté dans
  `IA/skills/`, puis l'implémentation.

## 4. Exécution de code

- Toute exécution de code se fait en **sandbox**, sans exception.
- Aucun accès réseau implicite : il doit être demandé explicitement.
- Les secrets ne sortent jamais du coffre et ne sont jamais écrits dans une note.

## 5. Frontmatter — format obligatoire

Tout fichier agent ou skill commence par un frontmatter YAML valide.

**Champs communs**

| Champ | Type | Obligatoire | Notes |
| --- | --- | --- | --- |
| `schema` | entier | oui | version du format. Actuellement `1`. |
| `kind` | `agent` \| `skill` \| `contract` | oui | permet de valider le type sans se fier au dossier |
| `name` | texte | oui | minuscules, tirets, **sans espaces**. Identique au nom du fichier. |
| `description` | texte | oui | une ligne. Réutilisée par le générateur de sommaires. |
| `read_only` | booléen | oui | cf. sémantique ci-dessous |

**Sémantique de `read_only`**

| Valeur | Signification |
| --- | --- |
| `true` | **Lecture seule absolue** : aucune écriture nulle part (ni coffre, ni hors coffre, même via patch). |
| `false` | **Écriture directe** dans `brouillon/`, `mémoire/<nom-agent>/`, et `IA/skills/` si `createur-de-skill` est déclaré (détail au §2) ; écriture hors coffre autorisée (§3) ; le reste du coffre passe par patch Git revu. |

**Champs propres aux agents**

| Champ | Type | Notes |
| --- | --- | --- |
| `skills` | liste | une entrée par ligne, tirets YAML |
| `mcp` | liste | idem |

**Champs propres aux skills**

| Champ | Type | Notes |
| --- | --- | --- |
| `type` | `core` \| `outil` | `core` = indispensable au fonctionnement du coffre |

**Emplacement d'un agent ou d'un skill**

Deux formes, au choix :

```
IA/skills/pdf.md                 forme plate — par défaut
IA/skills/pdf/pdf.md             forme dossier — quand le skill grossit
IA/skills/pdf/references/        détails consultatifs, chargés au besoin
IA/skills/pdf/scripts/           code exécuté, jamais chargé en contexte
IA/skills/pdf/assets/            fichiers repris dans le résultat produit
```

Le point d'entrée porte **le nom du skill**, jamais `SKILL.md` : le `name` doit
valoir le nom du fichier (ci-dessus), et le §6 impose l'unicité des noms de
notes dans le coffre parent — une douzaine de `SKILL.md` la violerait.

Passer à la forme dossier quand le corps approche des 500 lignes, ou quand une
information est consultative plutôt que procédurale. Une information vit soit
dans le corps, soit dans une référence — **jamais les deux**, sinon les deux
divergent. Tout fichier de `references/` est **cité explicitement** depuis le
corps, en disant quand le lire : un fichier qu'on ne sait pas exister n'est
jamais consulté.

Seuls `references/` contient des notes ; `scripts/` et `assets/` sont écartés
du balayage des noms.

**Règles de syntaxe**

- Les listes s'écrivent en YAML, une entrée par ligne précédée d'un tiret.
  Jamais `skills: a, b` — ça vaut une chaîne de caractères, pas une liste.
- Les clés utilisent l'underscore (`read_only`), pas le tiret.
- Les noms (fichier, `name`) sont en minuscules avec tirets, **sans espaces**.
  Les accents sont autorisés (`bibliothécaire`, `développeur`).
- Un champ déclaré dans le frontmatter n'est **pas** répété dans le corps du
  fichier : le frontmatter est la vérité machine.

## 6. Nommage, rétroliens et mémoire

- Le coffre est la **racine du dépôt** (`OBSIA/`) : il n'y a pas de sous-dossier
  intermédiaire. Tous les chemins de ce contrat partent de cette racine.
- Le dépôt est destiné à être cloné **dans** un coffre Obsidian préexistant,
  appelé ici *coffre parent* (non versionné). Les rétroliens Obsidian se
  résolvent à l'échelle de ce coffre parent, **pas** de `OBSIA/`.
- Conséquence : les noms de notes doivent être **uniques dans tout le coffre
  parent**, pas seulement dans `OBSIA/`.
- Les liens vers ce contrat s'écrivent en chemin relatif depuis `IA/agents/` ou
  `IA/skills/` : `../system/VAULT-CONTRACT.md`.
- **Structure de la mémoire.** L'espace d'un agent porte son nom — jamais
  `agent 1`, `agent 2` — et distingue ce qui est **daté** de ce qui est
  **durable** :

  ```
  mémoire/<nom-agent>/
  ├── profil-utilisateur.md          faits stables sur l'utilisateur et sa machine
  ├── préférences/<sujet>.md         goûts et règles de conduite transversaux
  ├── expériences/<sujet>.md         leçons réutilisables, tirées d'un cas réel
  └── <nom-projet>/AAAA-MM-JJ-titre.md   avancement daté d'un projet
  ```

  Les noms de projet sont explicites — jamais `projets 1`, `projets 2`.

- **Où écrire, selon la nature de l'information** :

  | Ce qu'on a appris | Destination |
  | --- | --- |
  | un fait stable sur l'utilisateur, son poste, son infrastructure | `profil-utilisateur.md`, **mis à jour sur place** |
  | un goût ou une règle qui vaudra pour d'autres projets | `préférences/<sujet>.md` |
  | une leçon tirée d'un échec ou d'une manœuvre qui a marché | `expériences/<sujet>.md` |
  | une décision ou un avancement propre à un projet | `<nom-projet>/AAAA-MM-JJ-titre.md` |

  Les trois premières ne sont **pas datées** : une préférence qui change se
  corrige, elle ne s'empile pas. Seules les notes de projet portent une date,
  parce qu'elles racontent une chronologie.

  Dans le doute, écrire dans le projet : une note de projet peut être distillée
  plus tard vers `préférences/` ou `expériences/`, l'inverse fait perdre le
  contexte.

- Une note durable n'est utile que si elle est **retrouvée** : son nom dit son
  sujet (`licences-et-logiciel-libre.md`, pas `notes.md`) et respecte la règle
  d'unicité ci-dessus.

## 7. Périmètre de lecture et coffre parent

- [x] **Tranché le 2026-09-03.** Les agents peuvent lire le coffre parent
      (`0-PROJETS`, `1-CONCEPTS`, `2-RESSOURCES`, …). Le confinement à
      `OBSIA/` qui valait par défaut est levé.

Le coffre parent est donc en **lecture seule**, à une exception près :

| Zone du coffre parent | Lecture | Écriture |
| --- | --- | --- |
| `0-EN VRAC/` | oui | **oui, directe** |
| tout le reste (`0-PROJETS`, `1-CONCEPTS`, `2-RESSOURCES`, …) | oui | **non** |

Précisions qui découlent de cette règle :

- Le nom du dossier s'écrit `0-EN VRAC`, en capitales et avec une espace,
  comme les autres dossiers du coffre parent. Le système de fichiers distingue
  la casse : `0-en vrac` désignerait un autre dossier, et un agent qui le
  créerait écrirait à côté. L'espace impose aussi de citer le chemin dans une
  commande shell (`"$COFFRE/0-EN VRAC"`).
- Le coffre parent **n'est pas versionné**. Un patch Git y est donc impossible :
  hors de `0-EN VRAC/`, il n'existe aucune voie d'écriture, même soumise à
  revue. « Lecture seule » y est absolu.
- `0-EN VRAC/` est une zone de dépôt, comparable à `brouillon/` : contenus
  provisoires, non garantis conservés. Un contenu qui doit durer est recopié
  dans `mémoire/<nom-agent>/` (§2), à l'intérieur du dépôt, où Git le suit.
- Le coffre parent n'est **pas** un « dépôt extérieur » au sens du §3 : ce
  paragraphe vise des bases de code, pas des notes.
- Les règles générales du §2 s'appliquent à `0-EN VRAC/` comme partout
  ailleurs : aucune suppression sans archivage, preview obligatoire avant une
  action touchant plusieurs fichiers.
- La règle d'unicité des noms de notes (§6) prend ici tout son sens : elle
  porte sur le coffre parent entier, désormais lisible.
- Lire n'est pas recopier. Le contenu du coffre parent ne migre pas dans
  `OBSIA/` au fil des réponses : le dépôt est **public** (§4), le coffre
  parent ne l'est pas.

## 8. Sources et citations

Une note durable distingue explicitement trois natures d'information :
**évidence** (avec son URL source), **interprétation** et **synthèse produite
par un agent**. Les URLs sont regroupées en fin de fichier.

## 9. Log des sessions

À la fin de chaque session de travail, une note est **proposée en patch** dans
`IA/system/session-log/AAAA-MM-JJ.md` : décisions prises, fichiers modifiés,
questions restées ouvertes. Ce dossier vit sous `IA/system/`, donc son
écriture suit la règle générale du §2 (patch Git revu) — ce n'est pas une des
trois zones en écriture directe.

## 10. Méthode d'exécution

Ce contrat lu, l'ordre à suivre pour toute demande — un harness peut le
citer ou l'injecter, il ne le redéfinit jamais (cf. préambule) :

1. Choisis l'agent pertinent pour la demande, via `IA/system/agents-index.md`
   ou l'index fourni par le harness. S'il n'y en a qu'un, c'est lui par
   défaut. Lis `IA/agents/<nom>.md` pour son rôle et ses règles propres.
2. Identifie, PARMI les skills et les MCP déclarés par cet agent, ce qui est
   nécessaire à la demande — et seulement ça.
   - Skill : lis `IA/skills/<nom>.md`, applique la procédure décrite.
   - MCP : lis `IA/MCP/<nom>.md` avant d'appeler un de ses outils — il donne
     les permissions et les règles de sécurité propres à cet outil (marqué
     `permission: elevated` quand il touche un système externe : réseau,
     dépôt distant).
3. Mémoire — dès qu'une décision est prise ou qu'une information mérite
   d'être retrouvée plus tard : écris-la à l'emplacement que le §6 assigne à
   sa nature — `profil-utilisateur.md`, `préférences/`, `expériences/`, ou le
   dossier du projet. Crée le dossier s'il n'existe pas. Vérifie au §2 si
   l'écriture est directe ou passe par patch.

   Avant d'écrire une note durable, **lis celle qui existe déjà** sur le même
   sujet : un fait qui change se corrige sur place, il ne se réécrit pas à
   côté. Ne touche JAMAIS un fichier généré à la main — voir §11.
4. Cite les chemins des fichiers utilisés dans ta réponse.

Ne charge pas de fichier « pour voir ». Si aucun skill ne correspond, réponds
directement en le signalant. Un skill `read_only: true` n'exécute aucune
commande modifiant l'état du système : s'il conclut à une action, énonce-la
sans la faire.

## 11. Fichiers générés et vérification

Certains fichiers du coffre **décrivent** d'autres fichiers. Ils sont produits
par script, jamais saisis : écrits à la main, ils divergent de leur source sans
que rien ne le signale.

| Fichier | Produit par | Source de vérité |
| --- | --- | --- |
| `mémoire/**/sommaire.md` | `scripts/regenerate_sommaire.py` | le contenu des notes |
| `IA/system/agents-index.md` | `scripts/regenerate_index.py` | le frontmatter des agents |
| `IA/system/skills-index.md` | `scripts/regenerate_index.py` | le frontmatter des skills |

Corollaire : si un index et un frontmatter se contredisent, **le frontmatter a
raison**. On corrige la source, puis on régénère — jamais l'inverse.

`scripts/verifier_coffre.py` refuse un coffre incohérent : frontmatter
invalide, `name` différent du nom de fichier, liste écrite en chaîne,
description repliée sur plusieurs lignes physiques, agent déclarant un skill ou
un MCP inexistant, nom de note en double, fichier généré périmé. Il n'écrit
rien et sort en code 1.

Il tourne en intégration continue à chaque poussée
(`.github/workflows/verifier-coffre.yml`), et localement en crochet de
pré-commit — à activer une fois par clone :

```bash
git config core.hooksPath .githooks
```

Le crochet refuse alors un commit qui laisserait le coffre incohérent, et
rappelle la commande de régénération. `git commit --no-verify` le contourne
ponctuellement ; la CI, elle, ne se contourne pas.

À lancer aussi à la main, avant un commit :

```bash
python3 scripts/regenerate_sommaire.py
python3 scripts/regenerate_index.py
python3 scripts/verifier_coffre.py
```

Ces scripts n'utilisent que la bibliothèque standard de Python, à dessein : le
coffre ne doit dépendre d'aucune installation pour être vérifiable.
