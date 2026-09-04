# Nommer un agent le fait exister

Leçon tirée d'un agent fantôme resté quatre corrections dans le coffre. Vaut
pour tout nom cité dans une documentation normative.

## Statut
🟢 Vérifiée le 2026-09-04 — le nom a disparu, un contrôle empêche son retour.

---

## Le constat

Un skill du coffre avait été pris pour un agent. Le contrat corrigeait
l'erreur explicitement — **en citant le nom fautif**, pour le démentir. Ce nom
s'est alors propagé : dans le prompt fondateur, dans `HISTORIQUE.md`, et
jusque dans un **exemple de diagramme** d'un skill, sous la forme
`agent[<nom>] --> skill[obsidian-manager]`.

C'est le pire endroit possible : un exemple est fait pour être copié. Le
contrat interdisait le fantôme à un endroit et le donnait en modèle à un autre.

Une seconde occurrence, indépendante, était installée dans une note de mémoire :
un second agent, nommé, qui n'a jamais eu de fichier — à côté d'un skill lui
aussi inexistant.

## La leçon

**Démentir un nom le maintient en vie.** Un lecteur — humain ou modèle — retient
le nom, pas la négation qui l'accompagne. La seule façon de faire disparaître un
agent imaginaire est de ne plus l'écrire du tout, y compris dans le paragraphe
qui explique qu'il n'existe pas.

Formulé en règle, désormais au §1 du contrat : **un seul agent peut être nommé,
`assistant`**. Un agent n'existe que s'il a son fichier dans `IA/agents/`.

## Ce qui rend la règle tenable

Une règle qu'aucun outil ne vérifie se re-viole. `scripts/verifier_coffre.py`
repère les trois formes sous lesquelles un nom d'agent apparaît réellement :

```
l'agent `<nom>`      un agent « <nom> »      agent[<nom>] --> …
```

et refuse le coffre si le nom capturé n'a pas de fichier. Deux réglages ont été
nécessaires :

- le motif retenait d'abord `read_only: false` et un séparateur de tableau ;
  exclure « : » et « | » du nom capturé a suffi ;
- `agent 1`, `agent 2` sont des contre-exemples de nommage de dossier, pas des
  noms : ils sont explicitement tolérés.

Le contrôle a immédiatement pris en défaut **ma propre rédaction**, à deux
reprises : dans la note corrective, puis dans celle-ci, où j'avais chaque fois
écrit le nom pour expliquer qu'il n'existait pas. Meilleure preuve que la règle
est intenable sans outil — même en la connaissant, on la viole en l'expliquant.

## Généralisation

Quand une documentation corrige une confusion, elle doit nommer ce qui **est**,
jamais ce qui n'est pas. « `obsidian-manager` est un skill » suffit ; ajouter
« et non l'agent X » ressuscite X.
