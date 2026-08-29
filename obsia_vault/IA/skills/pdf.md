---
schema: 1
kind: skill
name: pdf
description: Manipuler des PDF — extraire texte et tableaux, fusionner, découper, pivoter, remplir des formulaires.
type: outil
read_only: false
---

# Skill — PDF

Traitement de PDF avec des bibliothèques libres.

> **Écrit à neuf, pas traduit.** Le skill `pdf` d'AionUi est sous licence
> propriétaire (© Anthropic, PBC, tous droits réservés). Il ne peut pas être
> republié dans un dépôt public, même traduit. Ce fichier couvre les mêmes
> besoins avec les mêmes bibliothèques, qui sont elles libres.

## Outils et licences

| Outil | Licence | Rôle |
| --- | --- | --- |
| `pypdf` | BSD | fusion, découpe, rotation, métadonnées |
| `pdfplumber` | MIT | extraction de texte et de tableaux |
| `pikepdf` | MPL-2.0 | chiffrement, réparation, opérations bas niveau |
| `poppler` (`pdftotext`, `pdfimages`) | GPL-2.0 | extraction rapide en ligne de commande |
| `ocrmypdf` | MPL-2.0 | OCR sur PDF scannés |
| `qpdf` | Apache-2.0 | déchiffrement, linéarisation |

Installation sur CachyOS :

```bash
sudo pacman -S poppler python-pypdf qpdf
paru -S python-pdfplumber ocrmypdf
```

Ou en environnement virtuel, pour ne rien installer en système :

```bash
python -m venv .venv && source .venv/bin/activate
pip install pypdf pdfplumber pikepdf
```

## Extraire du texte

Le plus rapide, sans Python :

```bash
pdftotext -layout document.pdf sortie.txt
```

Avec contrôle fin :

```python
import pdfplumber

with pdfplumber.open("document.pdf") as pdf:
    for i, page in enumerate(pdf.pages, 1):
        texte = page.extract_text() or ""
        print(f"--- page {i} ---\n{texte}")
```

Si le texte extrait est vide, le PDF est probablement un scan : passer par l'OCR.

```bash
ocrmypdf --language fra document.pdf document-ocr.pdf
```

## Extraire des tableaux

```python
import pdfplumber

with pdfplumber.open("rapport.pdf") as pdf:
    for page in pdf.pages:
        for tableau in page.extract_tables():
            for ligne in tableau:
                print(" | ".join(c or "" for c in ligne))
```

## Fusionner

```python
from pypdf import PdfWriter

writer = PdfWriter()
for fichier in ["a.pdf", "b.pdf", "c.pdf"]:
    writer.append(fichier)
writer.write("fusion.pdf")
```

## Découper

```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("entree.pdf")
for i, page in enumerate(reader.pages, 1):
    writer = PdfWriter()
    writer.add_page(page)
    writer.write(f"page_{i}.pdf")
```

Extraire une plage précise :

```bash
qpdf entree.pdf --pages . 5-12 -- extrait.pdf
```

## Pivoter

```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("entree.pdf")
writer = PdfWriter()
for page in reader.pages:
    page.rotate(90)
    writer.add_page(page)
writer.write("pivote.pdf")
```

## Métadonnées

```python
from pypdf import PdfReader

meta = PdfReader("document.pdf").metadata
print(meta.title, meta.author, meta.creation_date)
```

## Formulaires

Lister les champs :

```python
from pypdf import PdfReader

champs = PdfReader("formulaire.pdf").get_fields() or {}
for nom, champ in champs.items():
    print(nom, champ.get("/FT"), champ.get("/V"))
```

Remplir :

```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("formulaire.pdf")
writer = PdfWriter(clone_from=reader)
writer.update_page_form_field_values(
    writer.pages[0],
    {"nom": "Dupont", "date": "2026-08-29"},
)
writer.write("rempli.pdf")
```

Si les champs restent invisibles à l'ouverture, forcer le rendu :

```python
writer.set_need_appearances_writer(True)
```

## Chiffrement

```bash
qpdf --decrypt --password=MOTDEPASSE chiffre.pdf clair.pdf
```

> Ne jamais écrire un mot de passe dans un fichier du coffre. Le passer en
> argument au moment de l'exécution, et vérifier qu'il ne finit pas dans
> l'historique du shell.

## Pièges courants

| Piège | Ce qu'il faut faire |
| --- | --- |
| Texte extrait vide | Le PDF est un scan → passer par `ocrmypdf` |
| Ordre des colonnes mélangé | Utiliser `pdftotext -layout`, pas `pdftotext` seul |
| Accents cassés | Vérifier l'encodage de sortie, forcer UTF-8 |
| `extract_tables` ne trouve rien | Le tableau n'a pas de bordures → ajuster `table_settings` |
| Formulaire rempli mais vide à l'écran | `set_need_appearances_writer(True)` |

## Contraintes

Ce skill écrit des fichiers. Les règles de preview et d'archivage du contrat
s'appliquent : voir `../system/VAULT-CONTRACT.md`.
