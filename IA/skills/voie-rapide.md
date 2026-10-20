---
schema: 1
kind: skill
name: voie-rapide
description: Juger si un petit outil — un script d'un seul fichier, un seul utilisateur, rien à préserver — peut sauter les portes de cadrage, puis le construire par la voie rapide du batisseur — quatre tests d'entrée, verdict de voie daté, fiche courte, une seule tranche — et repérer le signal qui le renvoie au parcours complet. À charger avant tout petit outil, et à chaque séance qui rouvre un outil construit ainsi. Ne vaut pas pour une interface, un service, une tâche planifiée ou une donnée à migrer.
module: construction
type: outil
read_only: false
---

# Skill — Voie rapide

Six portes pour un script de quatre-vingts lignes, c'est trop : personne ne les
franchit, et une règle qu'on contourne ne protège plus rien. La voie rapide est
l'exception **nommée**, pas un raccourci : elle a un critère d'entrée qu'on
vérifie, un verdict daté, et une sortie.

## Le critère d'entrée — quatre tests, tous vrais

| # | Le test | La réponse qui qualifie |
| --- | --- | --- |
| 1 | Quelqu'un d'autre l'appelle-t-il, ou est-il exposé sur le réseau ? | non — un seul utilisateur, un seul poste |
| 2 | Si je supprime le dossier maintenant, qu'est-ce qui est perdu ? | rien — pas de base, pas de format de fichier déjà en usage |
| 3 | Tient-il dans un fichier et une commande de vérification ? | oui — ordre de grandeur : environ 200 lignes |
| 4 | Manipule-t-il un secret que la machine n'a pas déjà, ou écrit-il hors de chez lui ? | non — pas de service, pas de `sudo`, pas d'infra |

Quatre disqualifiants, même si les quatre tests passent : une interface
visible ; une tâche planifiée ; un conteneur ou un service en ligne ; une
donnée à migrer.

Les tests 1 et 4 se **constatent** — l'outil est-il exposé, touche-t-il un
secret ou écrit-il hors de chez lui : deux faits observables. Les tests 2 et 3
s'**affirment** — « rien à préserver », « environ 200 lignes » : ils décrivent
l'outil d'aujourd'hui, et rien ne les stabilise. Une affirmation recopiée sans
être revérifiée devient une décoration.

**Qui tranche : les deux, dans cet ordre.** Je réponds aux quatre tests — deux
constatés, deux affirmés — et j'annonce la voie en une ligne, avec la preuve —
« un fichier, une commande de vérification, rien à préserver → voie rapide ».
L'utilisateur valide ou refuse,
en un mot. Je propose, je ne m'accorde pas la dérogation seul : sinon elle
devient un réflexe. Et l'utilisateur ne peut pas juger « 200 lignes » ou « rien
à préserver » à ma place — il doit le voir écrit. **Doute ou désaccord → le
parcours complet**, sans négociation en cours de route.

## Le verdict de voie — obligatoire, daté, révisable

Il s'écrit avant la construction, dans la note de suivi de l'outil
(`Mon coffre/0-PROJETS/<outil>/<outil> — résumé.md`) : la date, les quatre tests
**recopiés et cochés** un par un, et la voie retenue. Un verdict non écrit ne se
révise pas — et c'est lui qu'on rouvre à chaque séance qui retouche l'outil.

## Les deux étapes

**Étape 1 — Regarder, puis s'accorder.** Elle fusionne les portes 1 et 2 :
`inventaire-de-lexistant` réduit à un paragraphe — ce qui existe, ce qu'on ne
refait pas, la contrainte non négociable, plus le verdict de voie — puis
`interrogation-du-besoin` **plafonnée à un échange** : une seule question, avec
sa recommandation et le coût de l'autre choix. « Une question par message »
devient un plafond, pas une suppression.

**Étape 2 — La fiche courte, puis la construction.** Elle fusionne les portes 3
et 6, et saute les portes 4 et 5. La fiche (5 à 10 lignes) remplace les quatre
documents : problème, ce que l'outil fait, ce qu'il ne fait **pas**, deux ou
trois critères d'acceptation, la commande de vérification. Elle vit dans le
README du dépôt produit, et se résume en une ligne dans la note de suivi.

- pas de `STACK.md` : `python3` et la bibliothèque standard, ou le langage déjà
  installé pour la tâche — s'il faut *choisir* une stack, ce n'est plus un petit
  outil ;
- pas de `DESIGN.md` : pas d'interface visible, par construction ;
- pas de `PLAN.md` par tranches : **une** tranche. Si l'outil en demande deux,
  c'est un signal de sortie ;
- amorçage réduit à trois choses — le dépôt git de l'outil, sa licence, un
  `.gitignore` qui couvre les secrets — et la commande de vérification écrite
  dès le premier jour. `plancher-qualite` ne s'installe pas.

## Ce qui ne change pas, même en voie rapide

- **Les secrets** ne vont jamais dans le dépôt : les valeurs de machine restent
  dans `obsia.local.yml` ou l'environnement. Le crochet de pré-commit et
  `publier.py` ne bougent pas.
- **La commande de vérification existe et passe**, et le comportement qui
  compte a son test écrit **avant** (`tests-dabord`).
- `verification-aux-sources` dès qu'une ligne s'appuie sur une bibliothèque ou
  un format : la documentation de la version installée, pas la mémoire.
- `livraison-git` : branche, commit qui dit le pourquoi, et **PR relue par le
  `contradicteur`** (`revue-de-code`) — c'est sa seule revue restante, et celui
  qui construit ne se relit pas. Si le module `revue` n'est pas installé, il n'y
  a pas de contradicteur : le dire à l'utilisateur, et la PR est relue par lui
  seul.
- `investigation-de-bug` devant tout symptôme, jamais un correctif à la volée.
- Rien d'irréversible, et aucun `sudo` sans accord annoncé.
- Les règles du contrat ne changent pas (§3, preview, sandbox).

Ce qui saute, nommément : `cadrage-produit`, `choix-de-la-stack`,
`systeme-de-design`, `plan-de-livraison` dans sa forme à tranches,
`plancher-qualite`, `test-navigateur`, `mise-en-ligne`, et les rappels du
`visionnaire` — ils visent les directions qui ferment des portes, pas un script
de quatre-vingts lignes. Sauf demande de l'utilisateur.

## La sortie — quand le petit outil rejoint le parcours complet

Revérifié à **chaque séance** qui rouvre l'outil, et à la clôture, à partir du
verdict daté. Un seul signal suffit :

| Le signal | Ce qu'il déclenche |
| --- | --- |
| un deuxième utilisateur, ou un accès par le réseau | `cadrage-produit`, puis `systeme-de-design` si c'est visible |
| une donnée qui coûte — base, format déjà en usage | sauvegarde, puis `migration-de-donnees` |
| une dépendance externe, ou un deuxième fichier qui ne suffit plus | `choix-de-la-stack` |
| il devient planifié ou hébergé | plan, sauvegarde, surveillance, `mise-en-ligne` |
| « rien à préserver » n'est plus vrai, ou le fichier dépasse l'ordre de grandeur des ~200 lignes | le parcours complet, au cadrage |
| deux des quatre tests d'entrée ne sont plus vrais | idem |
| il doit survivre à son auteur | `documentation-du-projet` |

Les tests 2 et 3 — « rien à préserver », « environ 200 lignes » — ne sont donc
pas des mesures qu'on coche une fois pour toutes : ce sont des **affirmations à
revérifier**, et elles figurent aussi parmi les signaux de sortie ci-dessus.

Formule : **un petit outil qui prend une donnée, un deuxième utilisateur, un
conteneur ou un cron a quitté la voie rapide.** Il rentre alors **à la porte qui
manque** — le plus souvent le cadrage. L'inventaire, déjà écrit, ne se refait
pas ; le signal s'écrit au moment où il apparaît, pas six mois après.
