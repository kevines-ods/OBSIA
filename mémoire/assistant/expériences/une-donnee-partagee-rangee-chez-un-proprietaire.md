# Une donnée partagée rangée chez un propriétaire fabrique une exception

Leçon générale, tirée de la mémoire d'OBSIA. Vaut pour toute arborescence
découpée par propriétaire — dossiers, tables, dépôts, permissions.

## Statut

🟢 Vérifiée — une exception supprimée du contrat, aucune ajoutée.

---

## Le constat

`mémoire/` était découpé par agent. `profil-utilisateur.md` et `préférences/`,
qui décrivent l'**utilisateur**, se retrouvaient rangés chez l'agent qui les
avait écrits. Le contrat portait donc cette phrase :

> il reste unique dans le coffre […] Tout agent le lit ; celui qui n'est pas
> chez lui le complète **par patch**.

Une règle écrite, cohérente, appliquée — et qui n'existait que pour réparer un
rangement faux. Elle est restée des mois sans que personne la lise comme un
symptôme, **parce qu'elle fonctionnait**.

## La leçon

Quand une donnée commune est rangée sous un propriétaire, le rangement ne
devient pas faux : il devient **coûteux**. Et le coût ne se manifeste pas en
panne, il se manifeste en **règle supplémentaire** — une exception, un droit
d'accès, une procédure de contournement.

D'où le signal à reconnaître :

> **Une exception qui existe pour rendre accessible ce qui est déjà commun est
> un défaut de rangement, pas une règle.**

Le test, avant de créer un dossier par propriétaire : *cette information
décrit-elle le propriétaire ?* Si non, elle ne va pas chez lui, même si c'est
lui qui l'a produite. Qui écrit et de quoi ça parle sont deux axes différents,
et seul le second doit décider du rangement.

## Comment on le repère

Le symptôme est toujours le même, quelle que soit la technique : une clause qui
dit **« sauf »**, **« tout le monde peut lire mais »**, **« pour modifier,
passer par »**. Relire ces clauses en se demandant ce qu'elles compensent.

Contre-épreuve utile : une refonte de rangement bien orientée **supprime** des
règles. Si elle en ajoute, c'est probablement le mauvais axe.

## Ce que ça a donné

`mémoire/` est désormais découpé par **ce que la note décrit** : profil,
préférences et projets à la racine, communs ; `<agent>/expériences/` chez
l'agent, seule chose qui lui appartienne. L'exception « par patch » a disparu
du §6 du contrat, et l'isolation qui comptait — un agent n'écrit pas chez un
autre — est intacte.

Récit complet et arbitrages :
`mémoire/projets/architecture-de-la-memoire/2026-09-14-memoire-commune-et-memoire-dagent.md`.
