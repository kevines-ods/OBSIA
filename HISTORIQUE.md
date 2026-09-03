# HISTORIQUE

Ce fichier recueille ce qui a été décidé puis dépassé. Il n'a **aucune valeur
normative** : les règles en vigueur vivent dans
`IA/system/VAULT-CONTRACT.md`, qui fait foi. L'intention d'origine,
elle aussi non normative, est conservée dans
`IA/system/prompt-fondateur.md`.

Il existe pour une seule raison : éviter qu'un agent relisant le dépôt
reconstruise ce qui a été écarté.

---

## `obsia_vault/` a disparu : la racine du dépôt est le coffre (31 août 2026)

Le coffre a longtemps vécu dans un sous-dossier `obsia_vault/`. Ce niveau
n'avait plus de raison d'être une fois l'interface partie : le dossier du dépôt
cloné fournit déjà l'encapsulation recherchée. Le chemin réel était
`coffre-parent/OBSIA/obsia_vault/IA/…` — deux dossiers pour une seule frontière.

`IA/`, `mémoire/`, `brouillon/` et `scripts/` vivent désormais à la racine.

### Ce qu'il ne faut pas reconstruire

- **Ne pas recréer `obsia_vault/`.** La racine du dépôt *est* le coffre. Un
  chemin qui commence par `obsia_vault/` dans un fichier est une survivance à
  corriger, pas une convention à suivre.
- La distinction coffre / coffre parent, elle, **reste valable** : `OBSIA/` se
  clone dans un coffre Obsidian préexistant et non versionné, dont les
  rétroliens portent au-delà du dépôt (cf. `VAULT-CONTRACT.md` §6). C'est ce
  coffre-là, et lui seul, qu'on appelle désormais « parent ».
- Le `.gitignore` du sous-dossier a été fusionné dans celui de la racine ; ses
  motifs `target/`, `node_modules/` et `dist/` y ont été dé-ancrés pour rester
  actifs à toute profondeur.

---

## Le dépôt n'est plus un monorepo (30 août 2026)

OBSIA a d'abord réuni sous une même racine Git le coffre et l'interface
graphique qui le consommait. Ce n'est plus le cas.

Le coffre est désormais **seul et autonome**. Il ne nomme aucune interface,
aucun langage, aucun outil de construction : il décrit *quoi* faire, et
n'importe quel harness — Claude Code, OpenCode, Aider, Goose, ou une interface
dédiée — fournit *avec quoi*.

L'interface vit dans son propre dépôt : **https://github.com/kevines-ods/ObsiaUi**.
Son historique complet (29 commits) y a été transféré ; rien n'a été perdu.

### Ce qui a disparu du coffre avec ce changement

- Le **périmètre spécial** qui réservait une base de code extérieure à l'agent
  `assistant`. Le contrat traite désormais toute intervention hors du coffre de
  façon générique (`VAULT-CONTRACT.md` §3), sans nommer de projet ni imposer
  d'outillage.
- La description de l'interface (fenêtre à trois zones, sélecteur de
  fournisseur, modification de l'UI par le chat). Cette ambition reste valable,
  mais elle appartient à ObsiaUi.
- Trois documents du coffre — `RUNTIME.md`, `VAULT.md`, `README.md` — qui
  décrivaient le système à travers son interface et redisaient, parfois en se
  contredisant, ce que le contrat énonce déjà. Deux règles qu'eux seuls
  portaient ont été reprises dans le contrat : **sources et citations** (§8) et
  **log des sessions** (§9).

### Esquisse d'architecture d'interface (ancien `RUNTIME.md` de la racine)

Un `RUNTIME.md` vivait à la racine, distinct de celui du coffre — d'où des
ouvertures du mauvais fichier. Son seul contenu propre :

> ## Architecture backend
> ### Modules principaux
> - `app`: Gestion des fenêtres et menus Tauri
> - `state`: Gestion de l'état (State<'_, T>)
> - `commands`: Commandes Tauri (IPC)
> - `sandbox`: Sécurité et capability-based permissions

Conservé pour mémoire ; concerne l'interface, donc ObsiaUi.

### Dossiers du coffre parent (ancien `VAULT.md` de la racine)

Même situation : un `VAULT.md` de racine, doublon de celui du coffre, dont le
seul contenu propre était la nomenclature du **coffre Obsidian parent** — celui
qui contient le dépôt et qui n'est pas versionné :

> ### Dossiers
> - `0-PROJETS`: Projets en cours
> - `1-CONCEPTS`: Idées et prototypes
> - `2-RESSOURCES`: Documentation et ressources externes

Le périmètre de lecture de ce coffre parent a été tranché le 2026-09-03
(cf. `VAULT-CONTRACT.md` §7) : les agents peuvent le lire, mais n'y écrivent
que dans `0-EN VRAC/`. Le confinement à la racine du dépôt, qui valait par
défaut jusque-là, est levé.

---

## Le bibliothécaire n'a jamais existé

Une confusion récurrente a fait croire que le skill `obsidian-manager` avait été
renommé en un agent `bibliothécaire`.

Aucun fichier `IA/agents/bibliothécaire.md` n'a jamais existé dans ce dépôt.
`obsidian-manager` est un **skill**, utilisé par l'agent `assistant`.

C'est ce qu'établit `VAULT-CONTRACT.md` §1, qui fait foi.

---

## Le projet « système d'exploitation »

Écarté. OBSIA est un **système d'orchestration agentic**, jamais un système
d'exploitation. Toute formulation en ce sens est une erreur à corriger.
