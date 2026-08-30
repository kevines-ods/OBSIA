# HISTORIQUE

Ce fichier recueille ce qui a été décidé puis dépassé. Il n'a **aucune valeur
normative** : les décisions en vigueur vivent dans `obsia prompt.md` et dans
`obsia_vault/IA/system/VAULT-CONTRACT.md`, qui fait foi.

Il existe pour une seule raison : éviter qu'un agent relisant le dépôt
reconstruise ce qui a été écarté.

---

## L'interface graphique a quitté ce dépôt (30 août 2026)

Le dépôt a d'abord été un **monorepo** : le coffre `obsia_vault/` et le
framework `build/` (interface React + backend Rust/Tauri) cohabitaient sous la
même racine Git.

Ce n'est plus le cas. Le coffre est seul ici ; l'interface vit dans son propre
dépôt et consomme ce coffre sans en faire partie. L'historique complet de
`build/` (29 commits) a été extrait avant retrait — rien n'a été perdu.

Ce qui suit décrit cet état révolu.

### Ancienne intention (obsia prompt.md, en-tête)

> je veux créer un système d'orchestration agentic natif linux, complètement
> modifiable à travers le chat avec l'agent « assistant » : l'interface complète
> est modifiable, l'ajout de fonctionnalités passe par des patches.

L'ambition « l'interface est modifiable par l'agent » reste valable, mais elle
relève désormais du dépôt de l'interface, pas de celui-ci.

### Ancienne section 5 — L'interface utilisateur (Tauri/Rust, multi-fournisseur)

- Épurée : choisir un LLM. Un bouton "fournisseur" + menu déroulant.
- Trois zones redimensionnables : chat, contrôle (réflexions/écritures des
  agents), gestionnaire de fichier (le coffre). Les zones contrôle et
  gestionnaire se réduisent.
- L'UI n'est qu'un terminal humain sur le vrai système d'orchestration (le coffre).

### Ancienne section 6 — Le framework `build/`

> `build/` = **LE FRAMEWORK** : UI React + backend Rust/Tauri. Modifiable par
> l'agent `assistant` uniquement, via patch revu.

Le périmètre spécial accordé à l'agent `assistant` sur `build/`
(cf. `VAULT-CONTRACT.md` §3) n'a plus d'objet dans ce dépôt.

### Esquisse d'architecture backend (ancien `RUNTIME.md` de la racine)

Le fichier `RUNTIME.md` qui vivait à la racine — distinct de celui du coffre, et
source de confusion — ne contenait que ceci :

> ## Architecture backend
> ### Modules principaux
> - `app`: Gestion des fenêtres et menus Tauri
> - `state`: Gestion de l'état (State<'_, T>)
> - `commands`: Commandes Tauri (IPC)
> - `sandbox`: Sécurité et capability-based permissions

Conservé ici pour mémoire ; concerne l'interface, donc l'autre dépôt.

### Dossiers du coffre parent (ancien `VAULT.md` de la racine)

Même situation : un `VAULT.md` de racine, doublon de celui du coffre, dont le
seul contenu propre était la nomenclature du **coffre Obsidian parent** — celui
qui contient `obsia_vault/` et qui n'est pas versionné :

> ### Dossiers
> - `0-PROJETS`: Projets en cours
> - `1-CONCEPTS`: Idées et prototypes
> - `2-RESSOURCES`: Documentation et ressources externes

Le périmètre de lecture de ce coffre parent reste non tranché
(cf. `VAULT-CONTRACT.md` §7) : par défaut, les agents sont confinés à
`obsia_vault/`.

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
