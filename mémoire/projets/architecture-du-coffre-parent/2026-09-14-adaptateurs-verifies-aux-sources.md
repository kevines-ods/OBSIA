# 2026-09-14 — Les adaptateurs de harness, vérifiés aux sources

Les six fiches d'`adaptateurs-harness/` passent à une forme commune en six
sections, et leur contenu est vérifié sur la documentation officielle de chaque
projet. Cinq sur six aboutissent ; la sixième assume de ne pas pouvoir.

## Statut

🟢 Vérifié sur documentation, daté et sourcé fiche par fiche. **Aucune éprouvée
sur machine réelle** — et c'est écrit en tête de chacune plutôt que déduit d'un
branchement qui aurait l'air de marcher.

---

## Le déclencheur

« Avec le nouveau skill il faut donc que adaptateurs-harness soit documenté à
fond pour chaque harness. » Juste : `configuration-mcp` lit ces fiches pour
savoir où écrire, et cinq d'entre elles faisaient 16 à 47 lignes de généralités.

## Décisions

- **Une forme commune en six sections**, fixée dans `commun.md` : où vit la
  configuration · le bloc MCP · secrets et variables · restreindre un serveur à
  un agent · charger le cerveau · vérifier. Sans forme prévisible, un skill ne
  peut pas savoir où lire.

- **Les quatre premières sections décident de ce qui s'écrit.** Si l'une
  manque, le skill s'arrête au lieu d'écrire au hasard — nouvelle étape « 2 bis.
  Quand la fiche ne suffit pas », avec ce qu'il demande à la place.

- **Tout est vérifié à la source, daté, avec l'URL.** Trois de ces projets sont
  postérieurs à la date de connaissance du modèle : écrire leurs formats de
  mémoire aurait répété exactement l'erreur des noms du coffre parent.

- **DSH reste explicitement non vérifié.** Sa documentation officielle ne
  publie pas de chemin de configuration ni de clés MCP, et un guide tiers écrit
  que la syntaxe MCP « n'a pas été testée ». La fiche dit ce qui manque et
  pourquoi elle ne le comble pas.

## Évidence — ce que la vérification a appris

| Harness | Clé du bloc MCP | Secrets |
| --- | --- | --- |
| Claude Code | `mcpServers` | `${VAR}` et `${VAR:-défaut}` |
| OpenCode | `mcp` | `${VAR}` |
| LibreChat | `mcpServers`, en **YAML** | `${ENV_VAR}` |
| OpenClaw | `mcp.servers` | **non documenté** |
| AionUi | `mcpServers`, saisi dans l'interface | **aucun** — jeton en clair |
| DSH | inconnue | inconnue |

Trois constats qu'aucune supposition n'aurait donnés :

- **`mcpServers` n'est pas une norme.** Deux harness sur six attendent autre
  chose. Recopier le bloc universel sans lire la fiche échoue en silence.
- **Deux harness ne peuvent pas porter un jeton.** AionUi écrit le secret en
  clair dans sa documentation, ce que le §4 interdit ; OpenClaw ne documente
  pas d'interpolation alors qu'un de ses propres exemples en emploie une. Les
  serveurs authentifiés s'y déclarent autrement, ou pas du tout.
- **OpenClaw a `toolFilter`**, qui restreint les outils exposés d'un serveur
  par motif. C'est la traduction la plus fine du §10.2 de tout le dossier, et
  `openclaw mcp doctor --probe` est la seule commande qui *connecte et énumère*
  au lieu de constater l'absence d'erreur — exactement ce que le §6 du skill
  demande.

## Interprétation

Le skill a révélé la faiblesse des fiches, pas l'inverse. Tant que rien ne les
lisait, « à valider sur machine réelle » passait pour une réserve prudente ;
dès qu'une procédure s'appuie dessus, c'est un trou. Écrire ce qui consomme une
documentation est un bon moyen de découvrir qu'elle n'en est pas une.

## Questions ouvertes

- **Aucune fiche n'est éprouvée sur machine.** La vérification documentaire
  attrape les formats, pas les comportements.
- **OpenClaw, interpolation des secrets** : la documentation se contredit. À
  trancher au premier branchement réel, avant d'y mettre un jeton.
- **LibreChat, restriction par agent** : la page des agents n'a pas été lue,
  seulement celle des serveurs MCP. La section 4 de sa fiche le dit.
- **DSH** reste à compléter par patch quand l'utilisateur y aura accès.
