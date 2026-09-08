---
schema: 1
kind: skill
name: traitement-des-notes
description: Traiter les notes brutes du coffre parent — remplir, tagger (vocabulaire contrôlé), rétrolier, prévisualiser dans _maintenance/, classer depuis EN-VRAC et mettre à jour notes_remplies. À charger pour toute note brute ou toute note déposée dans SAVOIRS à compléter.
type: outil
read_only: false
---

# Skill — Traitement des notes

Fait passer une note brute du coffre parent à l'état de note de connaissance
classée : remplir le corps, poser frontmatter et tags, créer les rétroliens,
prévisualiser, classer, tracer. La règle d'ensemble est au §7 de
`../../system/VAULT-CONTRACT.md`, qui fait foi.

## Deux cas d'entrée

| Situation | Où | Ce que le skill fait |
| --- | --- | --- |
| une note brute dans `EN-VRAC/` | `../EN-VRAC/` | remplir, tagger, rétrolier, **classer** vers sa destination |
| une note déposée brute dans `SAVOIRS/` | `../SAVOIRS/` | compléter (tags, rétroliens, corps manquant) **sans la déplacer** |

## Vocabulaire et format

- Les **tags** viennent du vocabulaire contrôlé :
  `../../system/tags-du-coffre-parent.md`. Jamais de tag hors liste : un tag
  nouveau se propose par patch sur ce registre, il ne s'invente pas dans une
  note.
- Le **frontmatter minimal** d'une note de connaissance : `type` (parmi
  `concept`, `revue`, `projet`, `personnel`, `note`) et `tags`. `source`
  (URL) s'ajoute pour une note venue de l'extérieur (`DOCUMENTS/`).
- Les **rétroliens** s'écrivent `[[Nom exact de la note]]`, sans chemin de
  dossier, vers des notes existantes et au nom unique (§7.5).

## Procédure — note d'`EN-VRAC/`

1. Lister `../EN-VRAC/` ; lire la note ; comprendre l'intention (parfois un
   simple titre).
2. Vérifier par la recherche (`obsidian-manager`) qu'une note équivalente
   n'existe pas déjà — sinon proposer la fusion au lieu d'un doublon.
3. Remplir le corps dans la note, sans dénaturer l'intention de départ.
4. Poser le frontmatter minimal (`type`, `tags` du vocabulaire) et les
   rétroliens vers les notes liées.
5. Décider la destination : projet → `../PROJETS/` ; revue, article,
   transcription → `../DOCUMENTS/` ; fait personnel → `../PERSONNELS/` ;
   concept → `../SAVOIRS/`.
6. Afficher le preview (contenu final + destination), en conserver une copie
   datée dans `../_maintenance/` (§7.4).
7. Classer (déplacer), puis mettre à jour `../_maintenance/notes_remplies`.

## Procédure — note déposée dans `SAVOIRS/`

1. Vérifier dans `../_maintenance/notes_remplies` que la note n'a pas déjà été
   traitée ; si elle y figure, ne rien refaire.
2. Compléter : frontmatter minimal si absent, tags du vocabulaire, rétroliens,
   corps manquant — sans changer le sens ni déplacer le fichier.
3. Prévisualiser si plusieurs fichiers sont touchés (copie datée dans
   `../_maintenance/`), puis consigner la note dans `notes_remplies`.

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

## Garde-fous

- `read_only: false` : les écritures se limitent aux zones du §7.3 du contrat
  (`EN-VRAC/`, complétion `SAVOIRS/`, `_maintenance/`, classement). Rien
  d'autre n'est modifié, déplacé ni supprimé sans demande explicite.
- Un tag hors liste n'est jamais posé : proposer son ajout au registre par
  patch.
- Une note déjà dans `notes_remplies` n'est pas retraitée.
- Le contenu de `../PERSONNELS/` est privé : lecture sur demande, classement
  seulement si la nature est manifestement personnelle.
