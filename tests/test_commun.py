"""Le vérificateur ne dépend ni de l'installeur ni de la publication.

Ce qu'ils partagent vit dans `scripts/commun.py`, qui n'importe aucun des trois :
une modification d'`installer.py` ou de `publier.py` ne casse plus
`verifier_coffre.py` à l'import.
"""

import ast
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


def modules_importes(fichier: Path) -> set:
    arbre = ast.parse(fichier.read_text(encoding="utf-8"))
    noms = set()
    for noeud in ast.walk(arbre):
        if isinstance(noeud, ast.Import):
            noms |= {a.name.split(".")[0] for a in noeud.names}
        elif isinstance(noeud, ast.ImportFrom) and noeud.module:
            noms.add(noeud.module.split(".")[0])
    return noms


class Decouplage(unittest.TestCase):

    def test_verificateur_sans_installeur_ni_publication(self):
        importes = modules_importes(SCRIPTS / "verifier_coffre.py")
        self.assertFalse(importes & {"installer", "publier"}, importes)

    def test_commun_n_importe_aucun_des_trois(self):
        importes = modules_importes(SCRIPTS / "commun.py")
        self.assertFalse(importes & {"installer", "publier", "verifier_coffre"}, importes)


if __name__ == "__main__":
    unittest.main()
