#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Indexer 0-MEMOIRES/ — et n'y écrire jamais un chantier gelé.

`0-MEMOIRES/` porte deux mémoires (VAULT-CONTRACT.md §6) :

- **vivante** — `0-MEMOIRES/préférences/` et `0-MEMOIRES/<nom-agent>/expériences/`,
  corrigées sur place ;
- **gelée** — `0-MEMOIRES/<projet>/<chantier>/`, jamais retouchée après clôture.

Ces tests vérifient :

1. que l'indexeur couvre `0-MEMOIRES/` et **lit** la partie gelée ;
2. qu'il n'écrit **rien** hors de `_MAINTENANCE/` — donc rien dans la mémoire ;
3. que la convention rétroactive reconnaît un chantier gelé **par la forme** du
   chemin, sans lire la note ;
4. qu'elle **refuse d'écrire** dans la partie gelée, tout en continuant d'écrire
   dans la partie vivante (la garde n'est pas un interrupteur global).

Les deux outils de `IA/skills/traitement-des-notes/scripts/` sont chargés par
leur chemin : ils ne sont pas importables comme `scripts/`, et c'est voulu — ce
sont des outils de note, pas des scripts du produit.
"""

import contextlib
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

RACINE = Path(__file__).resolve().parent.parent
SKILL = RACINE / "IA" / "skills" / "traitement-des-notes" / "scripts"


def charger(nom: str, chemin: Path):
    """Charge un script par son chemin, sous un nom de module à nous."""
    spec = importlib.util.spec_from_file_location(nom, chemin)
    module = importlib.util.module_from_spec(spec)
    sys.modules[nom] = module
    spec.loader.exec_module(module)
    return module


INDEXEUR = charger("indexeur_coffre_parent", SKILL / "indexer_coffre_parent.py")
CONVENTION = charger("appliquer_convention_parent",
                     SKILL / "appliquer_convention_parent.py")

MEMOIRE_VIVANTE = "# Préférences de syntaxe\n\nPas de tabulations, jamais.\n"
LECON_VIVANTE = "# Livraison\n\nUne branche par tranche, une PR par branche.\n"
BILAN_GELE = "# Bilan du chantier\n\nClos le 2026-10-04, on n'y touche plus.\n"
README = "# 0-MEMOIRES\n\nDeux mémoires, une seule est gelée.\n"


class CoffreTemporaire(unittest.TestCase):
    """Un coffre parent minimal, avec les deux moitiés de `0-MEMOIRES/`."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.coffre = Path(self._tmp.name).resolve()

        (self.coffre / "_MAINTENANCE").mkdir()
        memoires = self.coffre / "0-MEMOIRES"
        (memoires / "préférences").mkdir(parents=True)
        (memoires / "batisseur" / "expériences").mkdir(parents=True)
        (memoires / "obsia" / "souverainete").mkdir(parents=True)

        (memoires / "README.md").write_text(README, encoding="utf-8")
        (memoires / "préférences" / "syntaxe.md").write_text(
            MEMOIRE_VIVANTE, encoding="utf-8")
        (memoires / "batisseur" / "expériences" / "livraison.md").write_text(
            LECON_VIVANTE, encoding="utf-8")
        (memoires / "obsia" / "souverainete" / "bilan.md").write_text(
            BILAN_GELE, encoding="utf-8")

    def etat(self) -> dict:
        """Contenu de chaque fichier du coffre, indexé par chemin relatif."""
        return {p.relative_to(self.coffre).as_posix(): p.read_bytes()
                for p in self.coffre.rglob("*") if p.is_file()}

    def executer(self, module, *argv):
        """Lance `main()` avec des arguments, en capturant la sortie standard."""
        ancien = sys.argv
        sys.argv = ["script"] + [str(a) for a in argv]
        tampon = io.StringIO()
        try:
            with contextlib.redirect_stdout(tampon):
                code = module.main()
        finally:
            sys.argv = ancien
        return code, tampon.getvalue()


class TestIndexeurCouvreLaMemoire(CoffreTemporaire):

    def test_le_dossier_des_memoires_est_indexe(self):
        self.assertIn("0-MEMOIRES", INDEXEUR.DOSSIERS,
                      "0-MEMOIRES/ doit être indexé (§11)")
        self.assertEqual(INDEXEUR.nom_index("0-MEMOIRES"), "index-0-memoires.md")
        self.assertIn("index-0-memoires.md", INDEXEUR.INDEX_GENERES)

    def test_l_index_lit_la_partie_gelee(self):
        index = INDEXEUR.rendre("0-MEMOIRES", self.coffre / "0-MEMOIRES")
        for nom in ("syntaxe.md", "livraison.md", "bilan.md"):
            self.assertIn(nom, index,
                          "un chantier gelé se lit encore — c'est l'intérêt "
                          "de l'indexer")

    def test_l_indexeur_n_ecrit_que_dans_maintenance(self):
        avant = self.etat()
        code, _ = self.executer(INDEXEUR, "--racine", self.coffre, "--appliquer")
        self.assertEqual(code, 0)
        apres = self.etat()

        for relatif, contenu in avant.items():
            if relatif.startswith("_MAINTENANCE/"):
                continue
            self.assertIn(relatif, apres, "%s a disparu" % relatif)
            self.assertEqual(apres[relatif], contenu,
                             "%s a été modifié par l'indexeur" % relatif)
        self.assertTrue((self.coffre / "_MAINTENANCE" / "index-0-memoires.md").is_file(),
                        "l'index de 0-MEMOIRES/ doit exister")


class TestChantierGele(CoffreTemporaire):

    def test_le_gele_est_reconnu_par_la_forme_du_chemin(self):
        m = self.coffre / "0-MEMOIRES"
        attendu = {
            self.coffre / "0-MEMOIRES": False,
            m / "README.md": False,
            m / "préférences": False,
            m / "préférences" / "syntaxe.md": False,
            m / "batisseur": False,
            m / "batisseur" / "expériences": False,
            m / "batisseur" / "expériences" / "livraison.md": False,
            m / "obsia": False,
            m / "obsia" / "souverainete": True,
            m / "obsia" / "souverainete" / "bilan.md": True,
            self.coffre / "0-SAVOIRS": False,
        }
        for chemin, gele in attendu.items():
            self.assertEqual(CONVENTION.est_gele(chemin, self.coffre), gele,
                             "mauvais verdict pour %s" % chemin)

    def test_la_convention_refuse_d_ecrire_dans_un_chantier_gele(self):
        avant = self.etat()
        code, sortie = self.executer(
            CONVENTION, "--racine", self.coffre, "--appliquer",
            "--dossier", "0-MEMOIRES/obsia/souverainete")

        self.assertEqual(code, 0, "le dossier reste lisible")
        self.assertIn("gelé", sortie)
        self.assertEqual(
            self.etat()["0-MEMOIRES/obsia/souverainete/bilan.md"],
            avant["0-MEMOIRES/obsia/souverainete/bilan.md"],
            "un chantier gelé n'est jamais réécrit (§6)")
        self.assertFalse(
            self.etat()["0-MEMOIRES/obsia/souverainete/bilan.md"].startswith(b"---"),
            "aucun frontmatter ne doit être ajouté dans un chantier gelé")

    def test_la_convention_ecrit_dans_la_memoire_vivante(self):
        code, _ = self.executer(
            CONVENTION, "--racine", self.coffre, "--appliquer",
            "--dossier", "0-MEMOIRES/préférences")

        self.assertEqual(code, 0)
        apres = self.etat()["0-MEMOIRES/préférences/syntaxe.md"]
        self.assertTrue(apres.startswith(b"---"),
                        "une préférence est vivante : elle se corrige sur place")
        self.assertIn(b"Pas de tabulations", apres)

    def test_le_readme_du_dossier_n_est_pas_une_note(self):
        avant = self.etat()
        self.executer(CONVENTION, "--racine", self.coffre, "--appliquer",
                      "--dossier", "0-MEMOIRES")
        self.assertEqual(self.etat()["0-MEMOIRES/README.md"],
                         avant["0-MEMOIRES/README.md"],
                         "un fichier de dossier posé par l'installeur n'est pas "
                         "une note : on n'y ajoute pas de frontmatter")


if __name__ == "__main__":
    unittest.main()
