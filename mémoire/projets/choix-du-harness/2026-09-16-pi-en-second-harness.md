# 2026-09-16 — Pi en second harness, et ce que coûte d'en avoir deux

Le harness Pi n'avait jamais été évoqué : la comparaison du 2026-09-13 lui est
antérieure et confrontait cinq candidats, pas six. Il est examiné ici pour une
place différente de celle d'OpenCode — pas pour le remplacer.

## Statut

🟡 Direction prise, **rien d'installé** — ni l'un ni l'autre harness. La fiche
d'intégration est écrite ; c'est un gabarit vérifié sur documentation, jamais
éprouvé sur machine.

---

## Décisions

- **Un poste à deux harness, par usage.** Pi sur le poste de travail, pour la
  gestion et l'optimisation ponctuelles de la machine ; OpenCode sur la VM
  dédiée à l'IA, pour les travaux lourds, les tâches planifiées et ce qui
  demande un suivi depuis plusieurs appareils.
- **La fiche d'intégration est écrite** :
  `IA/system/adaptateurs-harness/pi.md`, à la forme commune en six sections,
  plus deux sections propres (tâches planifiées, réserves).
- **Ce partage est un test de la règle de portabilité**, pas seulement un
  confort. Deux harness sur le même coffre, c'est la première occasion de
  vérifier que rien du coffre n'a été écrit pour un outil précis.

## Évidence

Vérifiée dans la documentation du projet, pas à l'usage. Les URLs sont dans la
fiche.

- **Pas de MCP intégré, pas de sous-agents, pas de permissions.** La
  documentation l'énonce comme un choix de conception, et ajoute que tout cela
  s'obtient en extensions TypeScript. Un adaptateur MCP tiers existe sur npm ;
  il n'est ni officiel ni audité.
- **Pas de système de permissions du tout** : le processus tourne avec les
  droits de qui l'a lancé. La réponse du projet à ce sujet est la
  conteneurisation, documentée en trois motifs.
- **Ce qui tient lieu de `read_only`** est l'allowlist d'outils au lancement,
  que la documentation nomme elle-même « read-only mode ».
- **Contexte chargé en remontant** depuis le répertoire de travail. Lancé à la
  racine du coffre, le harness ne voit donc pas le `CLAUDE.md` du dépôt, qui
  est en dessous — d'où le prompt généré posé en `.pi/APPEND_SYSTEM.md`.
- **Sessions sur disque**, reprises par `-c`, arbre de session, export HTML.
  Pas de mode serveur ni d'interface web : le critère « téléphone » n'est pas
  couvert, ce qui est cohérent avec la place qu'on lui donne.
- **Pas de planificateur** : les tâches restent `exécutant: local`.

## Interprétation

**Le partage tient parce que les deux outils échouent à des endroits
différents.** Ce harness-ci n'a ni accès distant ni permissions par agent —
inutilisable pour ce qui demande un suivi depuis le téléphone, sans importance
pour trois commandes tapées sur sa propre machine. L'autre porte les MCP et les
permissions, mais suppose un serveur qui tourne : lourd pour une question
ponctuelle.

**Le vrai coût n'est pas là où on l'attend.** Ce n'est ni la configuration en
double ni la mémoire — elle vit dans le dépôt, donc suivie par Git, et
n'appartient à aucun des deux. C'est l'invariant du §12 : deux harness qui
savent tous deux lire `IA/tâches/` peuvent instancier la même tâche chacun de
son côté, et une tâche déclenchée deux fois ne produit aucune erreur. La
décision à écrire avant de brancher le second est donc : **lequel des deux
instancie**. Rien dans le registre ne le dit à leur place ; `exécutant` dit
quelle classe d'exécutant a le droit, pas quelle machine l'a fait.

**Le second coût est de sécurité, et il est déjà connu.** Tout ce qui manque à
ce harness s'obtient en code tiers exécuté avec les droits de l'utilisateur —
la même famille de risque que la place de marché qui avait fait écarter un
candidat le 2026-09-13, sans le passif documenté. Chaque extension ajoutée est
un arbitrage à part entière.

## Synthèse IA

Le coffre a été écrit pour ne dépendre d'aucun harness, et cette fiche n'a rien
coûté au contrat : aucune règle n'a bougé, seule une fiche d'adaptateur s'est
ajoutée. C'était la promesse ; c'est la première fois qu'elle est tenue dans le
sens qui compte, celui d'un harness **ajouté** plutôt que remplacé.

Ce que le branchement révélera, et que la documentation ne dira pas : si un
`read_only: true` qui redevient une ligne de commande tient à l'usage. Le
contrat pouvait l'énoncer, l'autre harness l'exécutait ; ici il dépend d'un
alias qu'on peut oublier de taper. C'est la seule régression assumée du
partage, et elle vise l'agent qui en a le plus besoin.
