---
schema: 1
kind: skill
name: bureautique
description: Créer, lire et modifier des documents Word, Excel et PowerPoint — et convertir entre formats.
type: outil
read_only: false
---

# Skill — Bureautique

Manipulation de fichiers `.docx`, `.xlsx`, `.pptx` et `.odt` / `.ods` / `.odp`
avec des outils libres.

> **Substitution assumée.** Le skill `officecli` d'AionUi documente un binaire
> propriétaire, sans sources publiées, installé par `curl … | bash` depuis
> `d.officecli.ai`. Il n'a pas sa place dans un projet libre. Ce fichier couvre
> les mêmes besoins avec `python-docx`, `openpyxl`, `python-pptx` et
> LibreOffice, tous libres et déjà présents ou installables sur CachyOS.
>
> Une conséquence à connaître : `officecli` proposait un mode « surveillance »
> avec aperçu navigateur et sélection à la souris. Rien d'équivalent ici. Si ce
> mode t'est indispensable un jour, il faudra le construire — ce sera du travail.

## Outils et licences

| Outil | Licence | Rôle |
| --- | --- | --- |
| `python-docx` | MIT | Word : paragraphes, styles, tableaux, images |
| `openpyxl` | MIT | Excel : cellules, formules, graphiques, mise en forme |
| `python-pptx` | MIT | PowerPoint : diapositives, formes, texte |
| `odfpy` | Apache-2.0 | formats OpenDocument natifs |
| LibreOffice (`soffice`) | MPL-2.0 | conversion entre formats, export PDF |

```bash
sudo pacman -S libreoffice-fresh python-openpyxl
paru -S python-docx python-pptx
```

## Choisir le bon niveau

1. **Conversion ou export** → LibreOffice en ligne de commande. Le plus simple,
   souvent suffisant.
2. **Lecture ou modification structurée** → la bibliothèque Python du format.
3. **Cas non couvert** → manipuler le XML du paquet OOXML directement (un
   `.docx` est un ZIP). Dernier recours.

Toujours préférer le niveau le plus haut qui résout le problème.

## LibreOffice en ligne de commande

Conversion (le format de sortie est déduit du filtre) :

```bash
soffice --headless --convert-to pdf rapport.docx --outdir sortie/
soffice --headless --convert-to docx rapport.odt --outdir sortie/
soffice --headless --convert-to csv donnees.xlsx --outdir sortie/
```

Traitement par lot :

```bash
soffice --headless --convert-to pdf *.docx --outdir pdf/
```

> Une seule instance de LibreOffice tourne à la fois. Si une fenêtre est déjà
> ouverte, la commande échoue silencieusement. Utiliser un profil séparé :
> `-env:UserInstallation=file:///tmp/lo-obsia`

## Word

```python
from docx import Document

doc = Document()
doc.add_heading("Résumé", level=1)
doc.add_paragraph("Le chiffre d'affaires progresse de 25 %.")

tableau = doc.add_table(rows=2, cols=2)
tableau.style = "Table Grid"
tableau.cell(0, 0).text = "Trimestre"
tableau.cell(0, 1).text = "Montant"

doc.save("rapport.docx")
```

Lire et modifier :

```python
doc = Document("rapport.docx")
for p in doc.paragraphs:
    if "brouillon" in p.text:
        for run in p.runs:
            run.text = run.text.replace("brouillon", "final")
doc.save("rapport.docx")
```

> Le remplacement se fait au niveau des *runs*, pas des paragraphes. Un mot peut
> être coupé entre plusieurs runs si sa mise en forme change en cours de route —
> c'est la source d'erreur numéro un avec `python-docx`.

## Excel

```python
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Ventes"
ws["A1"] = "Région"
ws["B1"] = "Montant"
ws["A2"], ws["B2"] = "Nord", 15000
ws["B3"] = "=SUM(B2:B2)"

wb.save("ventes.xlsx")
```

Lire les valeurs plutôt que les formules :

```python
from openpyxl import load_workbook

wb = load_workbook("ventes.xlsx", data_only=True)
```

> `data_only=True` renvoie la dernière valeur **calculée par Excel ou
> LibreOffice**. Si le fichier a été produit par openpyxl sans avoir jamais été
> ouvert, ces cellules valent `None`. Pour forcer le calcul :
> `soffice --headless --convert-to xlsx fichier.xlsx`.

## PowerPoint

```python
from pptx import Presentation
from pptx.util import Cm, Pt

prs = Presentation()
diapo = prs.slides.add_slide(prs.slide_layouts[1])
diapo.shapes.title.text = "Bilan du trimestre"
diapo.placeholders[1].text = "Croissance de 25 %"

zone = diapo.shapes.add_textbox(Cm(2), Cm(10), Cm(10), Cm(2))
zone.text_frame.text = "Note de bas de page"
zone.text_frame.paragraphs[0].runs[0].font.size = Pt(12)

prs.save("bilan.pptx")
```

## Pièges courants

| Piège | Ce qu'il faut faire |
| --- | --- |
| Fichier ouvert dans LibreOffice | Le fermer avant d'écrire, sinon corruption |
| Texte introuvable dans un `.docx` | Chercher au niveau des runs, pas des paragraphes |
| Formules à `None` en lecture | Ouvrir une fois le fichier, ou convertir via `soffice` |
| Accents dans les noms de fichiers | Toujours travailler en UTF-8, éviter les espaces |
| `soffice` qui ne fait rien | Une autre instance tourne → utiliser `-env:UserInstallation` |
| Styles Word absents | `python-docx` ne crée que les styles du gabarit par défaut |

## Contraintes

Ce skill écrit des fichiers. Preview avant toute action multi-fichiers,
archivage avant écrasement : voir `../system/VAULT-CONTRACT.md`.
