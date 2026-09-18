# 2026-09-18 — Règle ou procédure : le critère qui décide où une information vit

L'utilisateur a demandé si le contrat n'était pas surchargé, et si certaines
informations ne devraient pas vivre dans le skill qui s'en sert. La réponse
tient en un critère, et il n'est pas celui qu'on croit.

## Statut

🟢 Appliqué. Cinq blocs déplacés, les quatre contrôles du §11 passent.

---

## Décisions

- **Le critère n'est pas « qui s'en sert » mais « qui peut la violer sans avoir
  rien chargé ».** Une règle rangée dans un skill ne s'applique que si le skill
  est chargé — or les fautes coûteuses (fuite du privé vers le public, agent
  fantôme, fichier généré édité, suppression sans archivage) se commettent
  sans avoir rien chargé du tout.
- **Trois catégories en découlent** : une **règle** reste dans le contrat ; une
  **procédure** part dans le skill ; un **format déjà contrôlé par un script**
  part avec la procédure, puisque le script rattrape l'erreur.
- **Quatre blocs déplacés** : §7.5 et §7.7 vers `traitement-des-notes` (ils y
  étaient déjà, mot pour mot) ; §7.6 vers
  `IA/system/adaptateurs-harness/README.md` ; les tables « emplacement d'un
  skill » et « champs propres aux MCP » du §5 vers `createur-de-skill`.
- **Le §11 suit le même sort** : la liste de ce que `verifier_coffre.py`
  refuse, ce qu'il avertit et la portée exacte du contrôle des chemins passent
  dans son propre docstring. Le contrat garde la table des fichiers générés,
  les trois règles de conduite et la chaîne de commandes.
- **La règle du non-doublon est désormais écrite dans le contrat**, au §5, et
  elle vaut pour le contrat lui-même : une information vit à un seul endroit.
- **L'index hiérarchique est ajourné**, pas abandonné : à ouvrir vers 60 skills.

## Évidence

Mesuré sur le dépôt, le 2026-09-18.

- Le §7.7 du contrat et la section « Procédure — note d'`-EN-VRAC/` » du skill
  `traitement-des-notes` décrivaient les **mêmes sept étapes**, dans le même
  ordre. Le §7.5 recopiait de même le format des rétroliens, le vocabulaire des
  tags et le frontmatter minimal d'une note.
- Le bloc « Emplacement d'un agent ou d'un skill » du §5 était **intégralement**
  couvert par la section « Structure d'un skill » de `createur-de-skill` — y
  compris la phrase sur les 500 lignes et celle sur les références citées.
- Le docstring d'`evaluer_routage.py` portait **déjà** ce que le §11 en disait
  — jusqu'à la phrase « un échec veut dire corriger la description ». Le §11
  documentait un script qui se documentait lui-même.
- **Le gain de contexte reste modeste : −3 593 octets, soit −5,6 %** de la
  charge permanente (63 997 → 60 404 o) ; le contrat seul passe de 43 286 à
  39 634 octets, −8,4 %. J'en avais annoncé environ 10 500 après les quatre
  premiers blocs : l'estimation était trop optimiste, parce que remplacer un
  bloc par un renvoi qui explique *pourquoi* le renvoi existe coûte presque
  autant que le bloc. Le gain réel est la suppression du doublon, pas le poids.
- **Le contrôle a attrapé une duplication que j'avais moi-même créée** : la
  phrase « on falsifierait le récit pour faire taire le contrôle » s'est
  retrouvée à la fois au §11 et dans le docstring. Retirée du docstring, qui
  renvoie au contrat. Un `grep` de phrases-témoins suffit à le voir ; rien dans
  l'outillage ne le verrait tout seul.
- **Ce n'est pas le contrat qui monte en charge, c'est l'index des skills** :
  435 octets par skill, toujours en contexte. À 35 skills il pèse 15 Ko ; à 100,
  il dépasserait le contrat entier (43 Ko).

## Interprétation

**La duplication était un bug en attente, pas seulement du poids.** Corriger la
procédure dans le skill aurait laissé le contrat affirmer l'ancienne version, et
`verifier_coffre.py` n'aurait rien vu : il contrôle les chemins, pas la
cohérence de deux textes qui disent la même chose. C'est la panne que le §11
décrit pour les index générés, à un endroit où personne ne l'attendait.

**Le contrat enfreignait sa propre règle.** Le §5 posait déjà « une information
vit soit dans le corps, soit dans une référence — jamais les deux » à propos des
skills. Il ne se l'appliquait pas. La règle est maintenant énoncée pour le
coffre entier, contrat compris.

**Se tromper de levier coûte plus que de ne rien faire.** Alléger le contrat
était le geste intuitif ; c'est celui qui rapporte le moins. Le contrat est de
taille fixe — il décrit des formats et des zones, pas des fonctionnalités —
tandis que l'index croît linéairement avec les skills. Un allègement du contrat
qui aurait supprimé une règle aurait échangé un gain nul contre un risque réel.

## Synthèse IA

Le motif rejoint celui de la note du même jour sur le choix du modèle : **ce
qui protège le coffre, c'est l'impossibilité, pas la consigne.** Ici il prend
une forme inattendue — une règle déplacée dans un skill devient une consigne
qu'on peut ne jamais lire. Déplacer n'est donc jamais neutre : ça change *quand*
la règle s'applique, pas seulement *où* elle est écrite.

Reste une question ouverte que ce chantier n'a pas tranchée : les deux harness
ne chargent pas le contrat de la même façon — collé en permanence d'un côté,
lu au besoin de l'autre. Tant que cet écart existe, « alléger le contrat » ne
veut pas dire la même chose selon la machine qui l'exécute.
