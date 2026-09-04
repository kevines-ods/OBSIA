# 2026-09-03 — Sommaires enrichis en couche de résumé

Application du point 2 de [[2026-09-03-comparaison-openviking]] : faire du
`sommaire.md` l'équivalent des couches L0/L1 d'OpenViking, sans serveur ni
modèle.

## Statut
🟢 Appliqué — `scripts/regenerate_sommaire.py` réécrit, 8 sommaires régénérés.

---

## Décisions

- **Rien n'est résumé par un modèle.** Chaque cellule est *prélevée* dans la
  note : le titre vient du H1, le statut de la section `## Statut`, le résumé du
  chapeau ou de la première section utile. Une information qui n'est pas écrite
  dans la note n'apparaît pas dans le sommaire.
- **La ligne de couverture est factuelle, pas sémantique.** « 6 sous-dossiers,
  7 notes, du 2026-08-15 au 2026-09-03. » Elle est dérivée, donc exacte. C'est
  un substitut honnête au L0 d'OpenViking, qui est lui produit par un LLM.
- **Remontée de bas en haut.** Un dossier parent affiche, pour chaque enfant, son
  nombre de notes et sa note la plus récente. C'est le mécanisme de *bubbling*
  d'OpenViking, réduit à des chiffres vérifiables.
- **Liens relatifs au dossier du sommaire.** Correction d'un bug : les liens
  étaient écrits relativement à la racine du dépôt.
- **Mode `--verifier` ajouté.** N'écrit rien, sort en code 1 si un sommaire est
  périmé. Prévu pour le point 4 ; utilisable dès maintenant avant un commit.

---

## Évidence

**L'intention était déjà écrite.** `mémoire/README.md` ligne 20 : *« chaque
`sommaire.md` énumère ses sous-dossiers **+ un court résumé** »*. Le résumé n'a
jamais été implémenté. Ce travail comble un écart entre la documentation et le
code, il n'invente pas de convention.

**Les liens étaient cassés.** L'ancien script écrivait
`[note](mémoire/assistant/projet/note.md)` *à l'intérieur de*
`mémoire/assistant/projet/sommaire.md`, soit une cible
`mémoire/assistant/projet/mémoire/assistant/projet/note.md`. Le repli d'Obsidian
sur une résolution depuis la racine du coffre ne sauve pas ce cas : le dépôt est
cloné **dans** un coffre parent, donc le chemin réel commence par `OBSIA/`.
Corrigé en liens relatifs au dossier courant (`note.md`, `sous-dossier/`).

**Le titre du sommaire était du code mort.** L'ancien
`base.split("—", 1)[1]` s'appliquait au nom de fichier `sommaire.md`, qui ne
contient jamais de tiret cadratin : la valeur retombait toujours sur « Sommaire ».
Le titre porte désormais le nom du dossier.

**Toutes les notes ne se ressemblent pas.** Sur 7 notes, 3 ont une section
`## Statut` ; les autres ouvrent sur `## Objectif`, `## Composants` ou
`## Layout` — cette dernière commençant par un schéma en caractères
d'encadrement. L'extraction écarte donc blocs de code, tableaux, titres, filets
et dessins ASCII, et exige au moins trois lettres dans une ligne pour la
retenir.

**Vérifications passées** : deuxième exécution sans écriture (idempotent) ;
`--verifier` sort 0 à jour, 1 après ajout d'une ligne dans une note, 0 après
restauration.

---

## Interprétation

Le gain se voit sur `mémoire/assistant/sommaire.md` : il listait six noms de
dossiers. Il donne maintenant, pour chacun, son volume et sa note la plus
récente datée. Décider où chercher ne demande plus d'ouvrir quoi que ce soit.

La limite s'est vue sur une note dépourvue de chapeau et de `## Statut`, qui
s'ouvrait sur un schéma en caractères d'encadrement : le générateur a pris la
première phrase de prose qu'il a trouvée, vraie mais secondaire. Ce n'est pas
un défaut du script — c'est une note mal structurée pour l'extraction, et le
sommaire l'a rendu visible. La réponse est d'ajouter un chapeau à la note, pas
de complexifier le générateur.

(La note en question a depuis été archivée pour une autre raison ; la leçon,
elle, vaut toujours.)

Enseignement plus large : plus les notes suivent une structure régulière
(chapeau, `## Statut`), meilleur est le sommaire. Le générateur récompense la
discipline d'écriture au lieu de l'imposer.

---

## Questions ouvertes

- [ ] Faut-il un ordre de sections imposé dans les notes de mémoire — un
      chapeau d'une ligne, puis `## Statut` — pour que l'extraction soit
      toujours bonne ? Cela relèverait du contrat §6.
- [ ] La ligne de couverture doit-elle compter les notes archivées ?
      `.archive/` est écarté aujourd'hui, comme tout dossier caché.
- [ ] Brancher `--verifier` en CI : point 4.

---

## Synthèse IA

Le point 2 tenait en une promesse : décider sans ouvrir. Elle est tenue pour
les dossiers, où les chiffres et la note la plus récente suffisent, et tenue
pour les notes bien structurées. Le coût réel n'a pas été le résumé lui-même
mais la tolérance de l'extraction — un coffre réel contient des schémas ASCII
et des tableaux là où un exemple de documentation n'aurait eu que des
paragraphes.

Deux bugs anciens sont tombés au passage : des liens qui ne pointaient nulle
part depuis le début, et un titre calculé par du code mort. Aucun des deux
n'était visible tant que personne ne regardait le fichier produit.

## URLs sources

- Couches L0/L1/L2, génération de bas en haut et `freshness` :
  https://github.com/volcengine/OpenViking/blob/main/docs/en/concepts/03-context-layers.md
