# routage-attendu.md — Le bon skill sort-il devant ?

La `description` d'un skill est le **seul** élément toujours présent en
contexte : c'est elle, et elle seule, qui décide qu'un skill se charge. Ce
registre la met à l'épreuve. Chaque ligne est une demande écrite comme
l'utilisateur la formulerait vraiment — pas une reprise de la description,
ce qui reviendrait à truquer l'épreuve.

`scripts/evaluer_routage.py` lit ce tableau, classe les skills par
proximité lexicale, et sort en erreur si le skill attendu n'arrive pas au
rang exigé. Il signale aussi deux descriptions trop semblables.

**Un échec veut dire : corriger la `description` du skill.** Pas ce
registre, et pas le script. Si une demande réaliste ne trouve pas son
skill, c'est un vrai défaut — le skill ne se déclenchera pas davantage en
conversation.

La mesure est **lexicale**, pas sémantique : elle ne comprend rien. Elle
attrape les deux pannes qui dominent — un mot que l'utilisateur emploie et
que la description n'a pas, et une description trop large qui passe devant
la bonne. Le reste lui échappe, et c'est assumé.

## Le tableau

Quatre colonnes : la demande · le skill qui doit répondre · le rang qu'il ne
doit pas dépasser · un skill qui ne doit pas le devancer (`—` s'il n'y a pas
de confusion à craindre).

Un rang de `1` se réserve à la demande signature d'un skill. `3` suffit
partout ailleurs : en conversation, l'agent lit les trois premières
descriptions et tranche.

| Demande | Skill attendu | Rang au plus | Ne doit pas devancer |
|---|---|---|---|
| « j'ai une idée d'application mais elle est encore floue » | interrogation-du-besoin | 3 | — |
| « avant de commencer, regarde ce que j'ai déjà essayé de construire » | inventaire-de-lexistant | 3 | — |
| « écris-moi le document qui fige ce qu'on veut construire » | cadrage-produit | 3 | — |
| « quel langage et quelle base de données pour ce projet ? » | choix-de-la-stack | 3 | — |
| « il faut choisir les couleurs et la typographie de l'interface » | systeme-de-design | 3 | — |
| « découpe le projet en étapes livrables une par une » | plan-de-livraison | 3 | — |
| « prépare le dépôt : licence, gitignore, readme » | amorcage-du-projet | 3 | — |
| « je veux un niveau de qualité écrit, que l'agent ne puisse pas contourner » | plancher-qualite | 3 | — |
| « attaque la première tranche du plan » | construction-dune-tranche | 3 | — |
| « écris le test avant le code » | tests-dabord | 2 | — |
| « vérifie dans la documentation officielle avant d'écrire ce code » | verification-aux-sources | 3 | — |
| « ouvre la page dans un navigateur et montre-moi ce qu'elle affiche » | test-navigateur | 3 | — |
| « ça plante quand je clique sur enregistrer, trouve pourquoi » | investigation-de-bug | 3 | — |
| « commit, pousse et ouvre la pull request » | livraison-git | 2 | — |
| « déploie le service et rends-le joignable par son nom de domaine » | mise-en-ligne | 2 | — |
| « le service répond en direct mais pas par son domaine » | traefik | 2 | mise-en-ligne |
| « le conteneur redémarre en boucle » | conteneurs-docker | 3 | traefik |
| « est-ce que mes sauvegardes se restaurent vraiment ? » | sauvegardes | 2 | — |
| « le disque est plein et un service est tombé, constate l'état » | diagnostic-linux | 3 | — |
| « redémarre le service et libère de la place » | remediation-linux | 3 | — |
| « retrouve la note où j'avais décidé ça » | obsidian-manager | 3 | — |
| « où est-ce que je dois chercher cette information ? » | recherche | 3 | — |
| « fais-moi un schéma de l'enchaînement » | mermaid | 2 | — |
| « extrais le tableau de ce pdf » | pdf | 2 | — |
| « mets à jour ce fichier excel » | bureautique | 2 | — |
| « range les notes brutes que j'ai déposées » | traitement-des-notes | 3 | — |
| « cette action doit se répéter tous les lundis matin » | cron | 3 | — |
| « fais le point sur la santé du coffre, les notes orphelines » | cartographie-du-coffre | 3 | — |
| « on clôt la séance, écris ce qui a été décidé » | cloture-de-session | 3 | — |
| « je veux écrire un nouveau skill pour le coffre » | createur-de-skill | 3 | — |
| « relis ce diff et dis-moi ce qui cloche avant que je fusionne » | revue-de-code | 3 | — |
| « cette décision d'architecture me paraît risquée, cherche ce qui la ferait tomber » | relecture-adverse | 3 | — |
| « combien de ressources restent sur l'hôte de virtualisation ? » | proxmox | 3 | — |

## Une attente qui a été corrigée, et pourquoi

La demande « déploie le service et rends-le joignable par son nom de
domaine » exigeait d'abord que `mise-en-ligne` **devance** `traefik`. Cette
attente était fausse, et la corriger n'est pas un renoncement :

- « nom de domaine » et « joignable » sont le vocabulaire **signature** de
  `traefik` — c'est par ces mots qu'on décrit un service derrière un proxy ;
- pour que `mise-en-ligne` les emporte, il faudrait charger sa description du
  vocabulaire de `traefik`, ce qui **dégraderait** le cas inverse : « le
  service répond en direct mais pas par son domaine », où `traefik` doit
  gagner, et gagne aujourd'hui largement ;
- les deux descriptions disent explicitement quand prendre l'autre. Les voir
  toutes deux dans les deux premiers rangs est le bon résultat : l'agent lit,
  et tranche.

Ce qui reste exigé est réel et vérifiable : `mise-en-ligne` dans les **deux
premiers** rangs. Le vrai défaut trouvé par le script était son rang 6 —
« déployer » manquait à sa description.

La règle générale : on corrige une attente quand elle demande l'impossible à
une mesure lexicale, jamais quand elle a simplement trouvé un défaut. La
distinction se juge en regardant le cas symétrique.

## Collisions admises

Deux skills peuvent légitimement se ressembler quand ils forment une paire
assumée — constater puis agir, ou deux couches d'un même symptôme. Ces
exemptions vivent **dans le script**, jamais dans le frontmatter d'un skill :
un skill qui se déclare lui-même dispensé du contrôle annule le contrôle.
Chacune y porte sa raison.

## Ajouter une demande

Quand un skill naît, lui écrire au moins une ligne ici. Quand une demande
réelle a mal été routée en conversation, l'ajouter telle qu'elle a été
formulée : c'est la meilleure source de cas, parce qu'elle n'est pas
imaginée.
