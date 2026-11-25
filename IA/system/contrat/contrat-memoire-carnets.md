---
schema: 1
kind: contract
name: contrat-memoire-carnets
description: Le carnet et sa reprise : tenue au fil de l'eau, séance sans chantier, commit à chaque étape, transition ; limites de ce que le carnet porte (§9) et pourquoi.
module: noyau
---

# Annexe du contrat — memoire-carnets

> **À lire avant l'acte qui la convoque.** Annexe du contrat (`../VAULT-CONTRACT.md`).
> Elle précise, elle n'ajoute aucune règle : toute règle qu'on peut enfreindre
> sans avoir rien chargé est aussi au noyau, et en cas de contradiction le
> noyau fait foi — l'annexe est alors à corriger. Découpée en trois annexes par
> acte (elle fut `contrat-memoire.md`) : les sections ont déménagé,
> sans qu'une phrase ne soit réécrite. La correspondance avec l'ancien
> contrat est suivie dans `registre.md`, document de travail non normatif.

- **Le carnet.** Un carnet par chantier, nommé
  `AAAA-MM-JJ-<chantier>-<sujet>.md` : `<chantier>` est le nom du dossier qui
  porte le `carnets/` — le chantier, ou le projet pour une séance sans
  chantier — et c'est ce nom, le même que celui du frontmatter `projet:`, qui
  doit rester unique dans tout le coffre parent (§6, §7.5) : deux chantiers
  homonymes sous deux projets feraient deux carnets homonymes. Frontmatter
  `agent:`, `projet:` et `statut: en cours | en attente | clos`. Il vit dans le
  `carnets/` du **dossier de son chantier** —
  `0-PROJETS/<projet>/<chantier>/carnets/` ; une séance sans chantier écrit dans
  le `carnets/` du projet. Il porte la demande, le plan,
  l'**étape en cours écrite avant d'agir**, les actions horodatées — effets
  externes compris (§9) —, les worktrees et branches ouverts, les questions
  en attente. Un carnet écrit après coup ne sert pas à reprendre : entre la
  dernière ligne et la coupure, il y a un trou que rien ne comble. Un
  chantier qui touche plusieurs projets écrit dans le carnet du projet
  `obsia`, sauf ce qui décrit un projet de l'utilisateur.

- **Une séance sans chantier** — dépannage ponctuel, correction sur un
  système, question qui finit en action — ne crée pas de chantier pour avoir
  un carnet, et n'ouvre un **carnet du jour** que si elle laisse un travail
  **en suspens** : une PR ouverte, une question qui attend l'utilisateur, une
  étape à reprendre après une coupure. Ce carnet vit dans le projet qui la
  porte : `0-PROJETS/obsia/` si elle touche le coffre, sinon le projet de
  domaine tenu pour ce sujet (`0-PROJETS/<domaine>/`). S'il n'y en a aucun,
  demander à l'utilisateur où l'écrire, plutôt que de rattacher la séance
  d'autorité au projet le plus proche.

  Dès qu'un carnet du jour passe `statut: clos` — le suspens qu'il portait est
  levé —, il quitte au même instant `0-PROJETS/<projet>/carnets/` pour
  `0-MEMOIRES/<projet>/carnets/`, gelé comme un chantier clos mais à l'écart des
  dossiers de chantier, pour ne pas faire passer une séance pour un chantier.
  Le dossier `carnets/` n'existe que si le projet a au moins un carnet de ce
  type.

  **Sinon — rien en suspens —, aucun carnet** : un dépannage bouclé dans la
  séance ne laisse pas un fichier de plus dans `carnets/`, que personne ne
  reprendra et qui noie les carnets vivants. Ce qu'il en reste se range par
  nature :

  - ses **actions** — effets externes compris (§9) — au **journal des
    séances**, `_MAINTENANCE/journal-des-seances.md`, une ligne horodatée par
    action, sous un titre daté de la séance : agent, quoi, où, résultat. Même
    règle de nature que le carnet (§9) : jamais d'IP privée, de nom d'hôte
    interne ni d'identifiant ;
  - la **leçon**, s'il y en a une, dans `0-MEMOIRES/<nom-agent>/expériences/` ;
  - un **savoir** réutilisable, par `0-EN-VRAC/` vers `0-SAVOIRS/` ;
  - un **fait** sur l'infrastructure de l'utilisateur, dans le profil.

  Le journal n'a ni `statut` ni reprise : il ne se relit que pour savoir ce qui
  a été fait. Une séance qui découvre en route qu'elle laisse un suspens ouvre
  son carnet à ce moment, et y reporte les lignes déjà écrites au journal.

  Un agent `read_only: true` n'écrit aucun carnet ni aucune ligne de journal :
  c'est l'agent qui reprend son travail qui consigne ses constats et les
  appels qu'il a menés.

- **Reprise.** Au démarrage, un agent cherche — dans l'arbre principal **et
  dans chaque worktree lié**, où vit le carnet d'un chantier en cours
  (§2.1) — les carnets `statut: en cours`
  qui portent son nom d'agent — le repère reste l'agent, jamais un harness, qui change. Il rapproche ce que le carnet déclare de l'état réel
  — `git status`, `git worktree list`, fichiers cités — avant de proposer de
  reprendre ; s'il en trouve plusieurs, il les liste et l'utilisateur
  choisit. La procédure vit dans `cloture-de-session`.
- **Un chantier repris change de nom d'agent.** L'agent qui reprend le
  carnet d'un autre y passe `agent:` à son nom à sa première ligne écrite, et
  le dit dans cette ligne : c'est ce champ qui désigne l'agent qui reprendra,
  et un carnet resté au nom de celui qui l'a ouvert relance le mauvais agent.

- **Le carnet se commite à chaque étape**, dans le dépôt de données du coffre
  (§7.1) : un worktree se perd (dossier temporaire vidé, `git worktree prune`),
  un commit non. Seul ce qui est commité survit à la coupure.

- **Transition.** Tant que la bascule dure — chantier `souverainete-des-donnees`,
  au plus tard le 2026-12-31 (§11) — les carnets, les projets et les notes
  personnelles se cherchent à **tout emplacement qui existe**, dans cet ordre :
  `0-PROJETS/`, l'ancien nom du coffre `-PROJETS/`, puis l'ancien
  `mémoire/projets/` du dépôt ; le profil sous `0-PERSONNELS/`, `-PERSONNELS/`,
  puis `mémoire/` ; les préférences, les expériences et le courrier sous `0-MEMOIRES/`
  (`préférences/`, `<nom-agent>/expériences/`, `courrier/`), puis `0-PERSONNELS/`,
  `-PERSONNELS/`, puis `mémoire/`. Des projets
  gardent l'ancienne forme — notes datées à plat dans le dossier du projet,
  vision ou résumé à plat à côté. Leur absence de `carnets/` ne veut pas dire
  absence d'historique : lire aussi ces notes avant de conclure.

  `IA/system/session-log/` — des notes de séance, donc de la **mémoire** — suit
  `mémoire/` : il quitte le dépôt à la bascule, pour
  `0-MEMOIRES/obsia/session-log/`, gelé. Passé le jour dit, ni lui ni `mémoire/`
  ne doivent rester dans le dépôt (§11, `verifier_coffre.py`).

## 9. Trace des séances — les limites du carnet

Le carnet **n'est pas un journal d'audit infalsifiable** : ce qui le rend
contradictoire, c'est l'historique du dépôt de données et, pour le produit, la
relecture de la PR. On y consigne la **nature** d'une action, pas
nécessairement sa cible ; les interdits (adresse IP privée, nom d'hôte interne,
URL interne, identifiant) sont au noyau, §9.
Une trace qu'on ne pourrait pas publier ne s'écrit pas davantage dans le
privé. Le carnet d'un projet de l'utilisateur n'a que l'aperçu du §7.4.

## Pourquoi — repris des sections restées au noyau

### §1 — d'où vient la règle des agents nommés

Le coffre n'a longtemps porté qu'un agent, et cette règle s'écrivait « un seul
agent peut être nommé ». La formulation confondait l'interdiction — les agents
fantômes — avec un plafond qui n'a jamais été l'intention.

Les tournures `agent 1`, `agent 2` restent employées ailleurs dans ce contrat :
ce ne sont pas des noms d'agents mais des **contre-exemples de nommage de
dossier**, et elles ne désignent personne.

### §9 — pourquoi l'horodatage, pourquoi `normal` ne dispense pas

L'horodatage
n'est pas décoratif : une séance qui touche plusieurs chantiers écrit dans
plusieurs carnets, et c'est lui qui rend l'ordre réel des actions
reconstituable.

`permission: normal` dit qu'un outil ne sort pas de la machine ; il ne
dispense pas d'en consigner l'usage. Un serveur « local » qui crée et
modifie des notes du coffre parent produit des effets aussi durables qu'un
serveur distant. Le dépôt de données rattrape désormais ce qui est commité
(§7.1), mais pas ce qu'aucune étape n'a pris le temps d'écrire. Ce que la
permission gradue, c'est la prudence avant d'appeler —
pas la trace après.
