---
schema: 1
kind: skill
name: traitement-des-notes
description: Traiter les notes brutes du coffre parent — remplir, tagger (vocabulaire contrôlé), rétrolier, prévisualiser dans _MAINTENANCE/, classer depuis 0-EN-VRAC et mettre à jour notes_remplies.md. À charger pour toute note brute ou toute note déposée dans 0-SAVOIRS à compléter.
module: coffre-obsidian
type: outil
read_only: false
---

# Skill — Traitement des notes

Fait passer une note brute du coffre parent à l'état de note de connaissance
classée : remplir le corps, poser frontmatter et tags, créer les rétroliens,
prévisualiser, classer, tracer. La règle d'ensemble est au §7 de
`../../system/VAULT-CONTRACT.md`, qui fait foi.

## Deux cas d'entrée

`0-EN-VRAC/` est un **tampon** : une session de rangement le vide entièrement
(§7.7 du contrat). Le critère d'achèvement n'est pas « quelques notes
traitées » mais « le dossier est vide » ; ce qui reste est ce qu'on n'a pas su
trancher, et se dit comme tel.

| Situation | Où | Ce que le skill fait |
| --- | --- | --- |
| une note brute dans `0-EN-VRAC/` | `Mon coffre/0-EN-VRAC/` | remplir, tagger, rétrolier, **classer** vers sa destination |
| une note déposée brute dans `0-SAVOIRS/` | `Mon coffre/0-SAVOIRS/` | compléter (tags, rétroliens, corps manquant) **sans la déplacer** |

## Vocabulaire et format

- Les **tags** viennent du vocabulaire contrôlé :
  `../../system/tags-du-coffre-parent.md`. Jamais de tag hors liste : un tag
  nouveau se propose par patch sur ce registre, il ne s'invente pas dans une
  note.
- Le **frontmatter minimal** d'une note de connaissance : `type` (parmi
  `concept`, `revue`, `projet`, `personnel`, `maintenance`, `idée`, `note`) et `tags`. `source`
  (URL) s'ajoute pour une note venue de l'extérieur (`0-DOCUMENTS/`).
- La **`description`** — un champ d'une seule ligne — n'est pas obligatoire,
  mais c'est elle que les index du coffre parent reprennent pour décider
  d'ouvrir une note **sans l'ouvrir**. L'écrire au remplissage, quand la note
  dit de quoi elle parle ; à défaut, les index se rabattent sur le premier
  titre. Le passage rétroactif ne la pose pas : elle demande un jugement sur le
  contenu.
- Les **rétroliens** s'écrivent `[[Nom exact de la note]]`, sans chemin de
  dossier, vers des notes existantes et au nom unique (§7.5).

## Procédure — note d'`0-EN-VRAC/`

1. Lister `Mon coffre/0-EN-VRAC/` — depuis la racine du dépôt, `ls ../0-EN-VRAC/` ;
   lire la note ; comprendre l'intention (parfois un simple titre).
2. Vérifier par la recherche (`obsidian-manager`) qu'une note équivalente
   n'existe pas déjà — sinon proposer la fusion au lieu d'un doublon.
3. Remplir le corps dans la note, sans dénaturer l'intention de départ.
4. Poser le frontmatter (`type`, `tags` du vocabulaire, `description`) et les
   rétroliens vers les notes liées.
5. Décider la destination : projet → `Mon coffre/0-PROJETS/<projet>/documents/`
   (le dossier du projet, §7.3 — jamais à plat dans `0-PROJETS/`) ; revue, article,
   transcription → `Mon coffre/0-DOCUMENTS/` ; fait personnel → `Mon coffre/0-PERSONNELS/` ;
   concept → `Mon coffre/0-SAVOIRS/`.
   **Idée** — titre commençant par `Idée` ou `type: idée` →
   `Mon coffre/0-PROJETS/Idées/documents/Idée — <sujet>.md`, frontmatter
   `statut: à évaluer` et `ajoutée: AAAA-MM-JJ`, une section vide
   « Faisabilité — revue d'équipe » ; puis ajouter sa ligne au tableau
   d'`Idées — résumé.md`. La faisabilité ne se juge pas au tri : elle se
   tranche en revue d'équipe, à la demande de l'utilisateur.
6. Afficher le preview (contenu final + destination), en conserver une copie
   datée dans `Mon coffre/_MAINTENANCE/` (§7.4).
7. Classer (déplacer), puis mettre à jour `Mon coffre/_MAINTENANCE/notes_remplies.md`.

## Procédure — note déposée dans `0-SAVOIRS/`

1. Vérifier dans `Mon coffre/_MAINTENANCE/notes_remplies.md` que la note n'a pas déjà été
   traitée ; si elle y figure, ne rien refaire.
2. Compléter : frontmatter minimal si absent, tags du vocabulaire, rétroliens,
   `description`, corps manquant — sans changer le sens ni déplacer le fichier.
3. Prévisualiser si plusieurs fichiers sont touchés (copie datée dans
   `Mon coffre/_MAINTENANCE/`), puis consigner la note dans `notes_remplies.md`.

## Passage rétroactif (notes existantes)

Le script `IA/skills/traitement-des-notes/scripts/appliquer_convention_parent.py`
ajoute le frontmatter minimal aux notes du coffre parent qui en manquent,
reprend les tags inline existants et signale ceux qui sortent du vocabulaire.
Il ne modifie rien par défaut : lancer l'aperçu d'abord, appliquer ensuite,
depuis la racine du dépôt OBSIA.

Un dossier à la fois, car le `type` posé dépend du dossier :

```bash
python3 IA/skills/traitement-des-notes/scripts/appliquer_convention_parent.py                     # 0-SAVOIRS → concept
python3 IA/skills/traitement-des-notes/scripts/appliquer_convention_parent.py --dossier=0-DOCUMENTS  # revue
python3 IA/skills/traitement-des-notes/scripts/appliquer_convention_parent.py --dossier=0-EN-VRAC    # tags seulement
```

Dans `0-EN-VRAC/`, aucun `type` n'est figé : il sera décidé au classement, quand
la note rejoindra sa destination. Après l'aperçu, appliquer avec `--appliquer`.

C'est un outil de votre machine : il lit le coffre parent réel. Il ne tourne
pas en CI.

## Index du coffre parent

Les index — `Mon coffre/_MAINTENANCE/index-<dossier>.md`, un par dossier du
coffre parent (`index-0-savoirs.md`, `index-0-memoires.md`, …) — sont produits
depuis les notes elles-mêmes, par
`IA/skills/traitement-des-notes/scripts/indexer_coffre_parent.py`. Le skill
`recherche` les lit avant les notes : ils servent à décider d'ouvrir une note
sans l'ouvrir.

L'indexeur **lit** ce qu'il indexe : il couvre donc aussi les chantiers gelés de
`0-MEMOIRES/`, et n'écrit jamais que dans `_MAINTENANCE/`. Le passage rétroactif
(`appliquer_convention_parent.py`), lui, **refuse d'écrire** dans un chantier gelé
— la mémoire des agents (`préférences/`, `<nom-agent>/expériences/`) est vivante,
un chantier clos ne l'est plus (§6).

Après un traitement de notes, les régénérer :

```bash
python3 IA/skills/traitement-des-notes/scripts/indexer_coffre_parent.py --verifier    # constate, n'écrit rien
python3 IA/skills/traitement-des-notes/scripts/indexer_coffre_parent.py --appliquer   # écrit, après l'aperçu
```

L'aperçu s'affiche par défaut : `--appliquer` est requis pour écrire (§7.4).
Comme le passage rétroactif, c'est un outil de votre machine — il lit le coffre
parent réel et ne tourne pas en CI.

## Garde-fous

- `read_only: false` : les écritures se limitent aux zones du §7.3 du contrat
  (`0-EN-VRAC/`, complétion `0-SAVOIRS/`, `_MAINTENANCE/`, classement). Rien
  d'autre n'est modifié, déplacé ni supprimé sans demande explicite.
- Un tag hors liste n'est jamais posé : proposer son ajout au registre par
  patch.
- Une note déjà dans `notes_remplies.md` n'est pas retraitée.
- `Mon coffre/0-PERSONNELS/` porte du personnel **non critique** : il se lit et
  se relie comme le reste (§7.3), mais on n'y **écrit** que pour y classer une
  note manifestement personnelle, et rien de son contenu ne part dans `OBSIA/`,
  qui est public. Une note qui porte `auteur: <nom-agent>` est une note de
  référence tenue par cet agent (§7.3) : ce skill ne la retraite pas.
