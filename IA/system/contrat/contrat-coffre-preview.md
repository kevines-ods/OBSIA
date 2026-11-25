---
schema: 1
kind: contract
name: contrat-coffre-preview
description: Le preview et la traçabilité d'une écriture dans le coffre parent : copie datée dans _MAINTENANCE (7.4), exceptions bornées, consignation.
module: noyau
---

# Annexe du contrat — coffre-preview

> **À lire avant l'acte qui la convoque.** Annexe du contrat (`../VAULT-CONTRACT.md`).
> Elle précise, elle n'ajoute aucune règle : toute règle qu'on peut enfreindre
> sans avoir rien chargé est aussi au noyau, et en cas de contradiction le
> noyau fait foi — l'annexe est alors à corriger. Découpée en six annexes par
> acte (elle fut `contrat-coffre-parent.md`) : les sections ont déménagé,
> sans qu'une phrase ne soit réécrite. La correspondance avec l'ancien
> contrat est suivie dans `registre.md`, document de travail non normatif.

### 7.4 Preview et traçabilité — `_MAINTENANCE/`

La mémoire se versionne (§7.1), mais le preview reste la trace lisible au moment
de l'acte. Avant toute écriture dans le coffre parent hors d'`0-EN-VRAC/` — note
créée, complétée, déplacée, création du carnet d'un projet comprise —, et avant
toute action qui touche plusieurs fichiers, l'agent :

1. affiche le preview — fichiers concernés, contenu final, destination ;
2. en **conserve une copie datée dans `_MAINTENANCE/`** ;
3. exécute, puis consigne l'action (quoi, où, résultat) dans `_MAINTENANCE/`.

`_MAINTENANCE/` ne porte que l'**entretien du coffre parent** : previews,
actions consignées, registre, index. Le récit d'un chantier va dans son
carnet (§6), pas ici. Une action se consigne au carnet — du chantier,
ou du jour si la séance laisse un suspens ; à défaut, au journal des séances,
`_MAINTENANCE/journal-des-seances.md` (`contrat-memoire-carnets`). Un
carnet dont l'agent est l'auteur se met ensuite à jour sur place sans
nouveau preview, et une ligne ajoutée au journal n'en demande pas non plus :
c'est de la consignation, pas une écriture de note. Exiger un preview à chaque étape pousserait à tout écrire
en fin de séance, ce que le §6 interdit.

**La correction du profil et des préférences ne demande aucun preview** : elle
se fait directement, sur place (§6), et se relit dans le commit suivant du dépôt
de données. Le preview protège une note qu'on ne possède pas ; celle-ci est faite
pour être corrigée à mesure.

**Une exception, bornée — l'écriture portée par un outil déclaré, pour un
harnais pilotant un modèle local.** Un outil **déclaré comme MCP dans
`IA/MCP/`** (§5), dont la **fiche dit qu'il écrit pour un harnais pilotant un
modèle local**, et dont **chaque écriture est consignée au
carnet de la session** (§9), peut rendre le preview **avec l'écriture** au lieu de
l'afficher avant : l'**annonce et la trace** — fichiers concernés, contenu final,
destination ; copie datée dans `_MAINTENANCE/` ; action consignée — accompagnent
l'écriture accomplie.

Cette exception tient à une **condition**, non à une conséquence : l'écriture doit
être **annulable**, et elle ne l'est que si

- **un acte = un commit ne portant que les fichiers de cet acte** — un acte peut en
  toucher plusieurs (un déplacement et la ligne qu'il change au registre des notes
  traitées) ; le commit est limité aux chemins de l'acte, **jamais
  `git commit -a`** ;
- l'outil **sérialise ses écritures** et n'y mêle jamais le travail d'un autre ;
- si le commit est **refusé**, ou ne porte pas exactement l'acte, l'écriture est
  **défaite** et l'échec **consigné** — et **l'exception tombe**.

Le commit se **reconnaît à une marque dans son message** ; il se fait sur la
**branche par défaut du dépôt de données** (§7.1), de sorte qu'un `git revert` du
seul commit défait l'acte sans toucher au reste. « Annulable » n'est pas
« effaçable » : un commit déjà poussé reste dans l'historique distant. Et la
**garde des secrets reste avant l'écriture** : elle ne s'appuie jamais sur
l'annulabilité.

**La seconde exception — la ligne de tour d'une boucle d'équipe.** Elle ne vaut
que pour **le serveur OBSIA-UI** (`obsia_ui/`), **sur la machine qui porte les
agents** (§7.1), qui conduit une boucle d'équipe (skill `orchestration-equipe`,
§6 et §8), et **seulement une fois que son code fait chacun des gestes
ci-dessous**, ce que prouve sa suite `tests/test_ligne_de_tour.py` (un cas
par geste). L'exception tombe dès que cette suite manque ou cesse d'être verte
sur la branche par défaut d'OBSIA-UI ; le preview avant écriture s'applique
alors. Le constat revient à qui relit ou fusionne une PR d'OBSIA-UI. À chaque
tour, il ajoute à la fin du carnet du chantier que la boucle
sert **une ligne physique et une seule**, bornée :

- quatre champs — numéro de tour, membre (un agent de l'équipe déclarée), statut
  (le vocabulaire fermé `STATUTS_FINAUX` d'OBSIA-UI, jamais un texte du modèle),
  compteur (un entier) ; longueur plafonnée par la constante `LIGNE_DE_TOUR_MAX`
  d'OBSIA-UI (200 caractères) ; **hors de ces bornes, refus**, jamais une
  troncature ;
- la **garde des secrets** passe sur la ligne **avant** l'ajout ; un motif reconnu
  ⇒ refus ;
- un **verrou de fichier propre au serveur**, dans le dépôt de données et sous
  un autre nom que celui des agents, tenu de la lecture du carnet au commit
  vérifié, sérialise ses ajouts, même entre deux instances du serveur ; il ne
  prend pas le verrou d'écriture des agents, qu'il ne bloque donc jamais. Contre
  les autres écrivains, deux contrôles le remplacent : le carnet doit être
  **propre** dans le dépôt de données (aucune modification non commitée), et la
  ligne du tour précédent doit se retrouver **à l'identique** dans la version
  commitée du carnet — le gestionnaire a pu écrire avant ou après elle ; absente
  ou modifiée, refus ;
- un tour = **un commit** du seul carnet, marqué dans son message, sur la branche
  par défaut du dépôt de données ; avant de commiter, l'index ne doit porter que
  ce carnet et que cette ligne ajoutée — sinon la ligne est retirée de la copie de
  travail, rien n'est commité ;
- un commit fait et reconnu faux après coup ne se défait que par **`git revert`
  de ce seul commit** ; si le revert lui-même ne s'applique pas proprement, on
  s'arrête **sans toucher** au dépôt — jamais `reset`, jamais réécriture
  d'histoire, jamais le commit d'un autre.

Tout refus ou échec est **consigné au journal de `_MAINTENANCE/`** (la cible de la
consignation de cette exception) et **arrête la boucle** : sans ligne, pas de tour
suivant. L'annonce et la trace accompagnent la ligne — copie datée du carnet dans
`_MAINTENANCE/`, action au journal — et l'interface la montre. **Rien d'autre** ne
passe par là : ni le plan, ni la revue, ni le bilan, ni une autre note, qui gardent
leur preview avant écriture. Le gestionnaire reste l'auteur du carnet (§1 et §7 du
skill) : la ligne de tour n'en est qu'un ajout en fin de fichier, et elle cède la
place — un carnet en cours d'écriture par un autre fait refuser la ligne, jamais
l'inverse. Raison de l'exception : le carnet est la source de la reprise (§8 du
skill) et doit survivre à la perte de l'interface.

Hors de ces cas, le preview reste la règle, sans exception.

Le registre des notes traitées est le fichier
**`Mon coffre/_MAINTENANCE/notes_remplies.md`** — une note Markdown, pour
qu'Obsidian l'indexe et la rende consultable comme le reste. Il liste les
notes déjà remplies, surtout celles de `0-SAVOIRS/` que l'utilisateur dépose
brutes. Une note qui y figure n'est pas à revérifier ; le registre est mis à
jour après chaque traitement.

