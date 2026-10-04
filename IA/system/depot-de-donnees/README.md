# Dépôt de données du coffre — gabarits

Ce dossier porte les gabarits que `scripts/installer.py` pose à la racine du
**coffre parent** pour y créer son **dépôt de données** (§7.1 du contrat). Le
dépôt produit ne suit pas la mémoire ; le dépôt de données ne suit qu'elle.

| Gabarit | Posé sous | Jamais écrasé ? |
| --- | --- | --- |
| `gitignore-coffre` | `<coffre>/.gitignore` | oui — une fois posé, il appartient au coffre |
| `pre-commit` | `<coffre>/.githooks/pre-commit` | non — réinstaller le rafraîchit |
| `post-commit` | `<coffre>/.githooks/post-commit` | non — réinstaller le rafraîchit |

Le jeton `@PRODUIT@` des crochets est remplacé à l'installation par le nom du
dossier du dépôt produit, tel qu'il est à la racine du coffre. Rien ici ne
pousse : `post-commit` lance la poussée en arrière-plan, et
`scripts/depot_de_donnees.py fraicheur` dit si la dernière poussée réussie a
moins de 48 heures — c'est ce que surveille un moniteur push.
