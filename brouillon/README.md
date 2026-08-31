# brouillon/

Zone d'**écriture autorisée** pour les agents `read_only: false`.

- C'est le seul endroit du coffre où un agent peut écrire directement, sans
  patch Git revu (cf. `IA/system/VAULT-CONTRACT.md` §2 et §5).
- Les contenus y sont **provisoires** : notes de travail, brouillons, réflexions.
- Dès qu'un contenu est stable, il est déplacé dans `mémoire/<agent>/<projet>/`
  via un patch Git revu.
- Cette zone est nettoyée régulièrement ; rien ici n'est garanti conservé.
