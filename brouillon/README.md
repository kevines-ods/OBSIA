# brouillon/

Zone d'**écriture autorisée** pour les agents `read_only: false`.

- L'écriture y est **directe et sans restriction**, sans patch Git revu. Ce
  n'est pas la seule zone dans ce cas : `IA/system/VAULT-CONTRACT.md` §2 en
  définit trois, dont `mémoire/<nom-agent>/`. Le contrat fait foi, ce README
  ne le reformule pas.
- Les contenus y sont **provisoires** : notes de travail, brouillons, réflexions.
- Dès qu'un contenu est stable, il est déplacé dans `mémoire/<agent>/<projet>/`
  — également en écriture directe, donc sans patch.
- Cette zone est nettoyée régulièrement ; rien ici n'est garanti conservé.
- Elle échappe aux sommaires générés et à `scripts/verifier_coffre.py` : rien
  de ce qui vit ici n'est indexé.
