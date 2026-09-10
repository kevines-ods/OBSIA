---
schema: 1
kind: skill
name: traitement-des-notes
description: Traiter les notes brutes du coffre parent — remplir, tagger (vocabulaire contrôlé), rétrolier, prévisualiser dans _maintenance/, classer depuis EN-VRAC et mettre à jour notes_remplies.md. À charger pour toute note brute ou toute note déposée dans SAVOIRS à compléter.
type: outil
read_only: false
---

# Skill — Traitement des notes

Fait passer une note brute du coffre parent à l'état de note de connaissance
classée : remplir le corps, poser frontmatter et tags, créer les rétroliens,
prévisualiser, classer, tracer. La règle d'ensemble est au §7 de
`../../system/VAULT-CONTRACT.md`, qui fait foi.

## Deux cas d'entrée

`EN-VRAC/` est un **tampon** : une session de rangement le vide entièrement
(§7.7 du contrat). Le critère d'achèvement n'est pas « quelques notes
traitées » mais « le dossier est vide » ; ce qui reste est ce qu'on n'a pas su
trancher, et se dit comme tel.

| Situation | Où | Ce que le skill fait |
| --- | --- | --- |
| une note brute dans `EN-VRAC/` | `Mon coffre/EN-VRAC/` | remplir, tagger, rétrolier, **classer** vers sa destination |
| une note déposée brute dans `SAVOIRS/` | `Mon coffre/SAVOIRS/` | compléter (tags, rétroliens, corps manquant) **sans la déplacer** |

## Vocabulaire et format

- Les **tags** viennent du vocabulaire contrôlé :
  `../../system/tags-du-coffre-parent.md`. Jamais de tag hors liste : un tag
  nouveau se propose par patch sur ce registre, il ne s'invente pas dans une
  note.
- Le **frontmatter minimal** d'une note de connaissance : `type` (parmi
  `concept`, `revue`, `projet`, `personnel`, `note`) et `tags`. `source`
  (URL) s'ajoute pour une note venue de l'extérieur (`DOCUMENTS/`).
- La **`description`** — un champ d'une seule ligne — n'est pas obligatoire,
  mais c'est elle que les index du coffre parent reprennent pour décider
  d'ouvrir une note **sans l'ouvrir**. L'écrire au remplissage, quand la note
  dit de quoi elle parle ; à défaut, les index se rabattent sur le premier
  titre. Le passage rétroactif ne la pose pas : elle demande un jugement sur le
  contenu.
- Les **rétroliens** s'écrivent `[[Nom exact de la note]]`, sans chemin de
  dossier, vers des notes existantes et au nom unique (§7.5).

## Procédure — note d'`EN-VRAC/`

1. Lister `Mon coffre/EN-VRAC/` — depuis la racine du dépôt, `ls ../EN-VRAC/` ;
   lire la note ; comprendre l'intention (parfois un simple titre).
2. Vérifier par la recherche (`obsidian-manager`) qu'une note équivalente
   n'existe pas déjà — sinon proposer la fusion au lieu d'un doublon.
3. Remplir le corps dans la note, sans dénaturer l'intention de départ.
4. Poser le frontmatter (`type`, `tags` du vocabulaire, `description`) et les
   rétroliens vers les notes liées.
5. Décider la destination : projet → `Mon coffre/PROJETS/` ; revue, article,
   transcription → `Mon coffre/DOCUMENTS/` ; fait personnel → `Mon coffre/PERSONNELS/` ;
   concept → `Mon coffre/SAVOIRS/`.
6. Afficher le preview (contenu final + destination), en conserver une copie
   datée dans `Mon coffre/_maintenance/` (§7.4).
7. Classer (déplacer), puis mettre à jour `Mon coffre/_maintenance/notes_remplies.md`.

## Procédure — note déposée dans `SAVOIRS/`

1. Vérifier dans `Mon coffre/_maintenance/notes_remplies.md` que la note n'a pas déjà été
   traitée ; si elle y figure, ne rien refaire.
2. Compléter : frontmatter minimal si absent, tags du vocabulaire, rétroliens,
   `description`, corps manquant — sans changer le sens ni déplacer le fichier.
3. Prévisualiser si plusieurs fichiers sont touchés (copie datée dans
   `Mon coffre/_maintenance/`), puis consigner la note dans `notes_remplies.md`.

## Passage rétroactif (notes existantes)

Le script `IA/skills/traitement-des-notes/scripts/appliquer_convention_parent.py`
ajoute le frontmatter minimal aux notes du coffre parent qui en manquent,
reprend les tags inline existants et signale ceux qui sortent du vocabulaire.
Il ne modifie rien par défaut : lancer l'aperçu d'abord, appliquer ensuite,
depuis la racine du dépôt OBSIA.

Un dossier à la fois, car le `type` posé dépend du dossier :

```bash
python3 IA/skills/traitement-des-notes/scripts/appliquer_convention_parent.py                     # SAVOIRS → concept
python3 IA/skills/traitement-des-notes/scripts/appliquer_convention_parent.py --dossier DOCUMENTS  # revue
python3 IA/skills/traitement-des-notes/scripts/appliquer_convention_parent.py --dossier EN-VRAC    # tags seulement
```

Dans `EN-VRAC/`, aucun `type` n'est figé : il sera décidé au classement, quand
la note rejoindra sa destination. Après l'aperçu, appliquer avec `--appliquer`.

C'est un outil de votre machine : il lit le coffre parent réel. Il ne tourne
pas en CI.

## Index du coffre parent

Les index — `Mon coffre/_maintenance/index-<dossier>.md`, un par dossier du
coffre parent — sont produits depuis les notes elles-mêmes, par
`IA/skills/traitement-des-notes/scripts/indexer_coffre_parent.py`. Le skill
`recherche` les lit avant les notes : ils servent à décider d'ouvrir une note
sans l'ouvrir.

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
  (`EN-VRAC/`, complétion `SAVOIRS/`, `_maintenance/`, classement). Rien
  d'autre n'est modifié, déplacé ni supprimé sans demande explicite.
- Un tag hors liste n'est jamais posé : proposer son ajout au registre par
  patch.
- Une note déjà dans `notes_remplies.md` n'est pas retraitée.
- `Mon coffre/PERSONNELS/` porte du personnel **non critique** : il se lit et
  se relie comme le reste (§7.3), mais on n'y **écrit** que pour y classer une
  note manifestement personnelle, et rien de son contenu ne part dans `OBSIA/`,
  qui est public.
