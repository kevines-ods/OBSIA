# Logo et identité visuelle

Le logo d'OBSIA : un sceau hexagonal contenant un document Markdown —
trois lignes de texte et un curseur terminal — accompagné du nom en
capitales espacées.

## Fichiers et usages

| Fichier | Usage |
| --- | --- |
| logotype.svg | version de base, horizontale : sceau + nom |
| banniere.svg | bannière du README en français |
| banner.svg | bannière du README en anglais |
| avatar.svg | avatar de profil (GitHub, réseaux) : pastille sombre sans texte |
| empile.svg | version empilée, pour les visuels carrés et cartes de partage |
| icone-claire.svg | icône d'application, interface claire |
| icone-sombre.svg | icône d'application, interface sombre |
| monochrome.svg | version une couleur, impression et documents internes |

## Palette

| Rôle | Code |
| --- | --- |
| Vert profond (sceau, texte) | #14332a |
| Verts de dégradé | #0e1f1a, #1b4332, #2d6a4f |
| Vert vif (slogan, contours) | #40916c, #52b788 |
| Menthe (lignes, curseur) | #74c69d, #95d5b2, #b7e4c7 |
| Fond clair (icône claire) | #f1f7f4 |
| Monochrome | #1a1a1a |

## Règles d'usage

- Ne pas déformer le logo ; redimensionner proportionnellement.
- Conserver autour du sceau une marge au moins égale à la moitié de sa hauteur.
- Sur fond sombre, préférer avatar.svg, ou passer monochrome.svg en blanc.
- Aucune image binaire n'est versionnée ici : les PNG se génèrent depuis les SVG.

## Générer des PNG

Avec rsvg-convert, Inkscape ou tout convertisseur SVG :

```bash
rsvg-convert -w 512 logo/avatar.svg -o avatar-512.png
```

## Note

Le wordmark utilise la police système (Segoe UI, Helvetica Neue, Arial) :
le rendu varie légèrement d'une machine à l'autre. Pour un rendu identique
partout, il peut être converti en tracés vectoriels dans un fichier dédié.
