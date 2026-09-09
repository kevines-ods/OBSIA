# 2026-09-09 — Un second agent, dédié à la construction

Le coffre a désormais deux agents. Le nouveau, `batisseur`, construit des
applications et des sites web, et son intérêt n'est pas de savoir coder mais
de refuser de coder trop tôt : six portes à franchir, chacune validée par
l'utilisateur, avant la première ligne.

## Statut

🟢 Écrit et vérifié — `verifier_coffre.py` sort en 0 avec 2 agents et 23
skills. Jamais éprouvé sur un projet réel : la valeur du protocole ne sera
connue qu'au premier chantier.

## Décisions

- **Le déclencheur, énoncé par l'utilisateur** : « j'ai construit plusieurs
  outils IA, aucun n'est vraiment ce que je voulais même si tous ont des
  choses bien ». Un outil qui a de bonnes parties sans être le bon outil est
  la signature d'un cadrage sauté — pas d'un défaut de modèle ni de langage.
- **Six portes, sans voie rapide.** L'utilisateur a écarté un mode court pour
  les petits projets : il serait choisi par confort, et le problème
  reviendrait. Une porte peut se franchir en deux minutes ; ce qui est
  interdit, c'est de ne pas la poser.
- **Deux skills sans équivalent dans la source d'inspiration** :
  `inventaire-de-lexistant`, parce que rien ne regardait les tentatives
  précédentes, et `choix-de-la-stack`, parce que la source interdit de nommer
  une technologie dans le cadrage et ne la choisit ensuite nulle part.
- **Un projet vit dans `PROJETS/<nom-du-projet>/`**, dépôt git créé à la porte
  3, poussé seulement à la porte 8. Une idée abandonnée ne laisse pas de dépôt
  vide en ligne.
- **L'agent va jusqu'à la mise en ligne**, action par action annoncée puis
  vérifiée. Proxmox reste en lecture seule.

## Évidence

- Le dépôt d'inspiration est `naiersaidane/claude-mastery`, MIT, en français,
  huit skills. Six ont été repris et adaptés ; `/illustre` ne l'a pas été,
  `mermaid` couvrant déjà le besoin dans ce coffre.
- Le contrat interdisait littéralement un second agent : « un seul agent peut
  être nommé dans le coffre ». La note du 2026-09-03 sur la comparaison
  OpenViking avait pourtant laissé une piste explicitement en attente d'un
  second agent — la règle et le projet du coffre se contredisaient déjà.

## Interprétation

L'intention du §1 n'a jamais été de plafonner le nombre d'agents : elle
visait les agents **fantômes**, nommés dans des notes sans avoir de fichier.
La formulation confondait l'interdiction et un plafond. Reformulée en « un
agent n'est nommé que s'il a son fichier », elle interdit toujours la même
chose et n'empêche plus rien de légitime — et c'est `agents-index.md`, généré,
qui dit désormais lesquels existent.

Le vrai risque de cette livraison n'est pas technique. C'est que les six
portes soient franchies pour la forme : un document validé sans être lu vaut
moins qu'un document absent, parce qu'il donne l'illusion du cadrage. D'où
les critères de franchissement écrits en toutes lettres dans le fichier de
l'agent, et l'aperçu HTML que l'utilisateur doit **voir**, pas seulement lire.

## Le trou que la relecture a montré

Le protocole livré d'abord savait **penser** et **livrer**, pas **construire** :
l'étape de construction n'avait aucun skill, et la mise en ligne s'appuyait sur
deux skills de diagnostic. L'utilisateur l'a vu immédiatement — « il a la
procédure mais rien pour la construire réellement ».

Leçon réutilisable, valable pour tout protocole en étapes : une table dont une
case « skill » est vide n'est pas une étape libre, c'est une étape non pensée.
La table rend le trou visible ; encore faut-il la lire comme un inventaire, pas
comme une illustration.

Trois skills l'ont comblé — `amorcage-du-projet`, `construction-dune-tranche`,
`mise-en-ligne` — et `sauvegardes` est entré dans la liste de l'agent.

## Questions ouvertes

- Le protocole n'a jamais tourné. Huit à quinze questions à la porte 2 est un
  ordre de grandeur repris de la source, pas une mesure faite ici.
- Mettre un dépôt git dans `PROJETS/` oblige à exclure ce dossier de l'index
  d'Obsidian, réglage manuel côté application. Rien dans le coffre ne peut
  vérifier qu'il a été fait ; l'oubli se verra à la recherche polluée.
- La mémoire de `batisseur` n'existe pas encore comme dossier : elle naîtra à
  son premier projet.
- Aucune licence par défaut pour les projets : la question est posée à chaque
  démarrage. C'est un choix de l'utilisateur, pas un oubli — reste à voir si
  la question devient lassante à la cinquième fois.

## Synthèse IA

Trois changements de contrat accompagnent l'agent : §1 (la règle de nommage),
§6 (`profil-utilisateur.md` reste unique et partagé entre agents, lu par tous,
écrit par patch), §7.3 (le dépôt de projet devient une zone d'écriture
autorisée du coffre parent, la seule où du code vit).

## URLs sources

- https://github.com/naiersaidane/claude-mastery
