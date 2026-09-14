---
schema: 1
kind: mcp
name: coffre-parent
description: Lire et écrire dans les fichiers du coffre parent `Mon coffre/` via un serveur MCP « fichiers » monté sur sa racine. À charger quand le harness n'ouvre pas déjà la racine du coffre comme dossier de travail. Le serveur peut écrire partout ; les zones autorisées restent celles du §7.3.
type: tool
transport: stdio
permission: elevated
---

# MCP — Coffre parent (serveur de fichiers)

Serveur MCP « fichiers » monté sur la **racine du coffre parent** — le dossier
`Mon coffre/`, celui qui contient `OBSIA/` et les dossiers de connaissance.
C'est la troisième des voies d'accès du §7.6 : celle qu'on emploie quand le
harness ne sait pas ouvrir la racine du coffre comme dossier de travail, ni
ajouter des répertoires supplémentaires.

Gabarit de config prêt à copier : `IA/MCP/mcp.example.json`, entrée
`coffre-parent`, où le chemin fictif est à remplacer par le chemin réel.

## Pourquoi cette fiche existe

Le serveur voit **toute** la racine du coffre et peut y écrire partout. Le
contrat, lui, n'en ouvre qu'une poignée en écriture — la liste fait foi au
§7.3, et n'est pas recopiée ici. Aucune de ces
limites n'est portée par le serveur : elles vivent ici, et c'est pourquoi le
§10.2 impose de lire cette fiche avant d'appeler un de ses outils.

Un serveur de fichiers ne refuse rien. C'est l'agent qui refuse.

## Permissions

`permission: elevated`. Le serveur ne sort pas de la machine, mais il touche
des fichiers **non versionnés** : une écriture erronée dans `Mon coffre/` n'a
pas d'historique Git pour la rattraper, contrairement au dépôt. C'est ce
caractère irréversible qui justifie le niveau, pas la distance.

Ce qui reste autorisé, malgré la portée du serveur :

| Zone | Lecture | Écriture |
| --- | --- | --- |
| `Mon coffre/-EN-VRAC/` | oui | oui — remplir, tagger, rétrolier |
| `Mon coffre/-SAVOIRS/` | oui | compléter seulement, sans déplacer |
| `Mon coffre/_maintenance/` | oui | oui — previews, actions, registre |
| `Mon coffre/-PROJETS/` | oui | la **note de suivi** `<projet> — résumé.md`, dont l'agent est l'auteur ; sinon classement seul |
| `Mon coffre/-DOCUMENTS/`, `-PERSONNELS/` | oui | **classement seul** : y déposer une note venue d'`-EN-VRAC/` |
| `Mon coffre/OBSIA/` | oui | non par ce serveur — le dépôt passe par Git (§2) |

Le détail fait foi au §7.3 du contrat, qui n'est pas reformulé ici.

## Règles d'usage

- **Preview avant écriture** : toute action touchant plusieurs fichiers,
  déplaçant une note ou écrivant hors d'`-EN-VRAC/` s'affiche d'abord et se
  consigne, datée, dans `Mon coffre/_maintenance/` (§7.4). Sans Git, le
  preview *est* la trace.
- **Consigner l'usage** : tout appel de ce serveur laisse une ligne dans le log
  de session (§9) — quoi, où, résultat.
- **Ne pas recopier** : le coffre parent est privé, le dépôt est public (§7.2).
  Rien de ce qu'on y lit ne migre dans `OBSIA/`. Dans l'autre sens, la note de
  suivi d'un projet de l'utilisateur s'écrit **ici**, jamais dans
  `mémoire/projets/` qui est public (§7.3.1).
- **Ne pas toucher la structure** : les dossiers de premier niveau
  appartiennent à l'utilisateur (§7.1). Ce serveur pourrait en créer un ; il
  ne le fait pas.

## Sécurité

- Le chemin réel du coffre n'entre **jamais** dans le dépôt : il vit dans la
  configuration du harness, hors dépôt. `mcp.example.json` ne porte qu'un
  chemin fictif.
- Le chemin contient une espace (`Mon coffre`) : le citer dans toute commande.
- Les dossiers commencent par `-` : dans une commande, les préfixer de `../`
  ou `./`, sans quoi ils sont lus comme des options (§7).
- `Mon coffre/-PERSONNELS/` porte du contenu personnel. Il se lit et se relie
  (§7.3), mais son contenu ne sort pas du coffre.
- Monter le serveur sur la racine du coffre, jamais plus haut : un serveur
  pointé sur `$HOME` donnerait accès à tout le poste.
