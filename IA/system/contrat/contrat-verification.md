---
schema: 1
kind: contract
name: contrat-verification
description: Détail des fichiers générés et des contrôles : tableau des fichiers, ce que voient les deux contrôles, intégration continue et crochets.
module: noyau
---

# Annexe du contrat — verification

> **À lire avant de toucher un script de vérification ou un fichier généré, de relâcher une attente de routage, ou d'utiliser un clone neuf (le crochet de pré-commit s'y active une fois).** Annexe du contrat (`../VAULT-CONTRACT.md`).
> Elle précise, elle n'ajoute aucune règle : toute règle qu'on peut enfreindre
> sans avoir rien chargé est aussi au noyau, et en cas de contradiction le
> noyau fait foi — l'annexe est alors à corriger. La correspondance avec l'ancien
> contrat est suivie dans `registre.md`, document de travail non normatif.

## 11. Fichiers générés et vérification

Certains fichiers du coffre **décrivent** d'autres fichiers. Ils sont produits
par script, jamais saisis : écrits à la main, ils divergent de leur source sans
que rien ne le signale.

| Fichier | Produit par | Source de vérité |
| --- | --- | --- |
| `0-*/**/sommaire.md` | `scripts/regenerate_sommaire.py` | le contenu des notes, dans le coffre parent |
| `IA/system/agents-index.md` | `scripts/regenerate_index.py` | le frontmatter des agents |
| `IA/system/skills-index.md` | `scripts/regenerate_index.py` | le frontmatter des skills |
| `IA/system/taches-index.md` | `scripts/regenerate_index.py` | le frontmatter des tâches |
| `IA/system/modules-index.md` | `scripts/regenerate_index.py` | le frontmatter des modules |
| `IA/README.md` | `scripts/regenerate_index.py` | les frontmatters d'agents, skills, MCP et tâches |

Ces cinq index sont **versionnés** et décrivent le **catalogue entier** : ils ne
dépendent pas de la machine et ne se réduisent jamais au profil (§13). Le profil
`obsia.local.yml` ne réduit que ce qui n'est pas versionné — le prompt système et
`AGENTS.md`. C'est ce qui rend le contrôle possible : la CI tourne **sans
profil**, et compare donc toujours l'index au catalogue complet.

Les sommaires **du coffre parent** ne sont pas du ressort de la CI du produit :
un clone neuf de `OBSIA/` n'a pas de mémoire à côté, et
`regenerate_sommaire.py` le supporte — sans dossier de mémoire, il le dit et
sort proprement (§7.1). Ils se régénèrent là où vit la mémoire — crochets
`post-merge` et `post-checkout`, installeur, revue hebdomadaire — et se
versionnent avec elle, dans le dépôt de données.

Corollaire : si un index et un frontmatter se contredisent, **le frontmatter a
raison**. On corrige la source, puis on régénère — jamais l'inverse.

**Deux contrôles, qui ne voient pas la même chose :**

- `scripts/verifier_coffre.py` contrôle la **forme** — frontmatter, noms,
  chemins cités, index à jour — et refuse un coffre incohérent en sortant
  en 1, sans rien écrire.
- `scripts/evaluer_routage.py` contrôle le **déclenchement** — la
  `description` d'un skill est le seul élément toujours présent en contexte,
  donc la seule chose qui décide qu'il se charge, et rien d'autre ne vérifie
  qu'elle porte les mots que l'utilisateur emploie.

Ce que chacun contrôle exactement, ce qu'il écarte et pourquoi, vit dans **son
propre docstring** — `python3 scripts/verifier_coffre.py --help` ou la tête du
fichier. Le recopier ici en ferait une seconde version à tenir à jour, ce que
le §5 interdit.

Trois règles, en revanche, appartiennent à ce contrat et pas au code :

- **Un échec de routage veut dire « corriger la description »**, pas
  « corriger le registre ». Une attente ne se relâche que lorsqu'elle demande
  l'impossible à une mesure lexicale, et cela s'écrit dans
  `IA/system/routage-attendu.md` avec sa raison.
- **Les exemptions vivent dans le script, jamais dans le frontmatter d'un
  skill** : un skill qui se déclare lui-même dispensé d'un contrôle annule le
  contrôle.
- **Un contrôle qu'on croit plus large qu'il n'est vaut moins que pas de
  contrôle du tout.** Le contrôle des chemins couvre `IA/` et les documents de
  la racine — là où un chemin faux *agit* ; `IA/system/session-log/` en est
  exempté, parce qu'un récit cite légitimement un état révolu, et le corriger
  après coup falsifierait le récit pour faire taire le contrôle. Le coffre
  parent est hors du dépôt : ses chemins ne sont pas contrôlés ici.

Le vérificateur tourne en intégration continue à chaque poussée
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
python3 scripts/evaluer_routage.py
```

Les deux scripts du §13 — `scripts/installer.py` et `scripts/publier.py` — ne
font pas partie de cette séquence : ils ne se lancent pas avant un commit mais
à l'installation et à la publication, et ils n'écrivent qu'avec `--appliquer`.

Pour savoir quel skill répondrait à une demande, sans rien vérifier :

```bash
python3 scripts/evaluer_routage.py --explique "ça plante quand je clique"
```

Un cinquième script, `scripts/evaluer_modele.py`, éprouve un **modèle**
candidat contre les règles de ce contrat. Il ne fait pas partie de la chaîne
ci-dessus : il lui faut un serveur qui réponde, donc il ne tourne ni en crochet
ni en CI.

Ces scripts n'utilisent que la bibliothèque standard de Python, à dessein : le
coffre ne doit dépendre d'aucune installation pour être vérifiable.

## Pourquoi — repris des sections restées au noyau

### §2 — pourquoi `.archive/` est versionné, et pourquoi l'arbre principal est commun

`.archive/` reste versionné : s'il était ignoré par Git, il ne survivrait pas à
un clone neuf. Mais **ce n'est plus lui qui archive la mémoire** : elle vit dans
le dépôt de données du coffre (§7.1), dont l'historique en tient lieu — un
fichier de mémoire supprimé s'y retrouve, sans recopie préalable.

Plusieurs agents travaillent **en même temps** sur ce dépôt, chacun dans sa
conversation. L'arbre de travail principal est donc une ressource commune :
une séance qui y change de branche déplace celle d'une autre entre deux de ses
commandes, et un commit atterrit sur la mauvaise branche sans que rien ne le
signale. Les règles qui en découlent sont au noyau (§2.1) : jamais de commit dans
l'arbre principal ni de worktree sous `/tmp`, une branche au nom de son agent,
une PR ouverte sur la branche par défaut, se resynchroniser avant de pousser.

Le crochet de pré-commit refuse toujours un commit sur la branche par défaut.
Il ne fait respecter « jamais dans l'arbre principal » et « une branche au nom
de son agent » que sur une machine où `git config obsia.arbresSepares true` est
posée, en plus de `core.hooksPath`. Les commandes, la publication et le ménage :
`IA/system/travail-en-parallele.md`.
