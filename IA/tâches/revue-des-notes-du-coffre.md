---
schema: 1
kind: tâche
name: revue-des-notes-du-coffre
description: Traiter les notes brutes du coffre parent — remplir et classer celles d'EN-VRAC, compléter celles déposées dans SAVOIRS, et signaler les tags hors vocabulaire contrôlé. À charger via le skill traitement-des-notes.
mode: agent
quand: "0 10 * * 1"
fuseau: Europe/Paris
exécutant: local
agent: assistant
actif: true
---

# Tâche — Revue des notes du coffre parent

## Intention

`EN-VRAC/` est un **tampon** : des notes y attendent d'être remplies puis
classées, et le dossier doit être vide en fin de passage, et des notes déposées brutes dans `SAVOIRS/` attendent d'être
complétées. Sans passage régulier, la file grossit et la base de connaissances
vieillit.

`exécutant: local` : la tâche a besoin du coffre parent sous la main (le dépôt
est cloné à sa racine, §7) — un planificateur distant n'aurait rien à traiter.

## Instruction

Charge le skill `traitement-des-notes`
(`IA/skills/traitement-des-notes/traitement-des-notes.md`) et applique sa
procédure, depuis la racine du dépôt OBSIA :

1. Liste `Mon coffre/EN-VRAC/` (`ls ../EN-VRAC/` depuis la racine du dépôt) :
   pour chaque note brute, vérifie par la recherche
   (`obsidian-manager`) qu'une note équivalente n'existe pas déjà, remplis le
   corps, pose le frontmatter minimal et les tags du vocabulaire contrôlé
   (`IA/system/tags-du-coffre-parent.md`), crée les rétroliens, puis classe la
   note selon sa nature vers `Mon coffre/PROJETS/`,
   `Mon coffre/DOCUMENTS/`, `Mon coffre/PERSONNELS/` ou `Mon coffre/SAVOIRS/`.
2. Vérifie `Mon coffre/_maintenance/notes_remplies.md`, puis complète les notes de
   `Mon coffre/SAVOIRS/` déposées brutes qui n'y figurent pas encore.
3. Consigne chaque preview (copie datée) et chaque action dans
   `Mon coffre/_maintenance/` (§7.4) et tiens le registre `notes_remplies.md` à jour.

Tout tag rencontré hors du vocabulaire contrôlé est **signalé**, jamais posé :
propose son ajout au registre par patch, ou son retrait. Ne modifie rien hors
des zones du §7.3.

Rapporte en clair : notes traitées et classées, notes complétées, tags hors
vocabulaire signalés, fichiers de `Mon coffre/_maintenance/` écrits. Termine en
disant si `EN-VRAC/` est vide : c'est le critère d'achèvement (§7.7), et ce qui
y reste est ce que tu n'as pas su trancher.
