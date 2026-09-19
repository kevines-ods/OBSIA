---
schema: 1
kind: module
name: documents
description: Documents bureautiques et PDF — lire, produire, convertir, extraire, remplir des formulaires, appliquer l'OCR.
essentiel: false
question: Traites-tu des PDF ou des documents Word, Excel, PowerPoint, OpenDocument ?
requiert:
  - noyau
---

## Ce que ce module apporte

Les skills `pdf` et `bureautique`. Ils vont ensemble parce qu'ils se renvoient
l'un à l'autre : chacun dit explicitement de charger le second quand le format
n'est pas le sien. Installer l'un sans l'autre laisserait un renvoi dans le
vide.

## Pourquoi aucune sonde

Les bibliothèques que ces skills utilisent s'installent au premier usage. Leur
absence aujourd'hui ne dit rien de l'usage de demain — la question est le seul
signal fiable.
