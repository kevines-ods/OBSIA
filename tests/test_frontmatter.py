"""Parseur de frontmatter et découverte des fichiers déclaratifs (§5).

Ces tests figent le comportement de `scripts/generer_prompt.py` avant de le
modifier : le parseur est le point par lequel passe tout l'index des agents et
des skills, une régression ici se propage silencieusement dans le prompt
système.

Deux formes sont admises par le §5 : plate (`<dossier>/<nom>.md`) et dossier
(`<dossier>/<nom>/<nom>.md`).

Chaque test écrit dans un coffre temporaire ; le coffre réel n'est jamais lu.
"""

import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path

sys.dont_write_bytecode = True          # ne pas semer de __pycache__ dans le dépôt
SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))        # `scripts/` n'est pas un paquet

from generer_prompt import (            # noqa: E402  (après l'aménagement du chemin)
    collecter,
    fichiers_declaratifs,
    lire_frontmatter,
)


class BaseCoffreTemporaire(unittest.TestCase):
    """Un dossier jetable par test, effacé à la fin quoi qu'il arrive."""

    def setUp(self):
        self.racine = Path(tempfile.mkdtemp(prefix="obsia-test-frontmatter-"))
        self.addCleanup(shutil.rmtree, self.racine, ignore_errors=True)

    def ecrire(self, relatif: str, contenu: str) -> Path:
        chemin = self.racine / relatif
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(contenu, encoding="utf-8")
        return chemin


class TestLireFrontmatter(BaseCoffreTemporaire):
    def test_valeur_contenant_des_deux_points(self):
        """`description: Vérifier le coffre : chemins` n'a qu'une seule clé.

        Le partage se fait sur le premier « : » ; le reste de la ligne est du
        texte. Une valeur à deux points ne doit pas créer de clé fantôme.
        """
        chemin = self.ecrire(
            "note.md",
            "---\n"
            "name: batisseur\n"
            "description: Vérifier le coffre : chemins cités et frontmatter\n"
            "---\n",
        )

        fm = lire_frontmatter(chemin)

        self.assertEqual(fm["description"],
                         "Vérifier le coffre : chemins cités et frontmatter")
        self.assertEqual(sorted(fm), ["description", "name"])

    def test_valeur_contenant_une_url(self):
        """« https:// » comporte des deux points et reste une valeur entière."""
        chemin = self.ecrire(
            "note.md", "---\nsource: Voir https://exemple.test/x:y\n---\n")

        self.assertEqual(lire_frontmatter(chemin)["source"],
                         "Voir https://exemple.test/x:y")

    def test_liste_a_tirets(self):
        chemin = self.ecrire(
            "note.md",
            "---\n"
            "name: batisseur\n"
            "skills:\n"
            "  - inventaire-de-lexistant\n"
            "  - interrogation-du-besoin\n"
            "---\n",
        )

        self.assertEqual(lire_frontmatter(chemin)["skills"],
                         ["inventaire-de-lexistant", "interrogation-du-besoin"])

    def test_liste_tolere_lignes_vides_et_commentaires(self):
        """Une liste ouverte reste ouverte malgré les lignes qu'on ignore."""
        chemin = self.ecrire(
            "note.md",
            "---\n"
            "skills:\n"
            "\n"
            "# le rôle d'abord\n"
            "  - inventaire-de-lexistant\n"
            "   - interrogation-du-besoin\n"
            "---\n",
        )

        self.assertEqual(lire_frontmatter(chemin)["skills"],
                         ["inventaire-de-lexistant", "interrogation-du-besoin"])

    def test_liste_vide(self):
        """Une clé sans valeur ouvre une liste ; sans élément, elle reste vide."""
        chemin = self.ecrire("note.md", "---\nname: x\nmcp:\n---\n")

        self.assertEqual(lire_frontmatter(chemin)["mcp"], [])

    def test_booleen_et_entier(self):
        """`true`/`false` deviennent des booléens, `1` un entier — pas des mots."""
        chemin = self.ecrire(
            "module.md",
            "---\n"
            "name: planification\n"
            "essentiel: true\n"
            "actif: false\n"
            "schema: 1\n"
            "---\n",
        )

        fm = lire_frontmatter(chemin)

        self.assertIs(fm["essentiel"], True)
        self.assertIs(fm["actif"], False)
        self.assertEqual(fm["schema"], 1)
        self.assertNotIsInstance(fm["schema"], str)

    def test_seule_une_valeur_entierement_numerique_devient_un_entier(self):
        """`1.2` et `2x` restent du texte : `isdigit()` est strict."""
        chemin = self.ecrire("note.md", "---\nversion: 1.2\nname: 2x\n---\n")

        fm = lire_frontmatter(chemin)

        self.assertEqual(fm["version"], "1.2")
        self.assertEqual(fm["name"], "2x")
        self.assertIsInstance(fm["version"], str)

    def test_guillemets_retires(self):
        """Un scalaire peut être encadré de guillemets, droits ou obliques."""
        chemin = self.ecrire(
            "note.md",
            "---\n"
            'description: "Vérifier : le coffre"\n'
            "name: 'batisseur'\n"
            "---\n",
        )

        fm = lire_frontmatter(chemin)

        self.assertEqual(fm["description"], "Vérifier : le coffre")
        self.assertEqual(fm["name"], "batisseur")

    def test_sans_frontmatter(self):
        chemin = self.ecrire("note.md", "# Titre\n\nDu texte.\n")

        self.assertIsNone(lire_frontmatter(chemin))

    def test_frontmatter_non_ferme(self):
        """Un `---` ouvrant sans `---` fermant n'est pas un frontmatter."""
        chemin = self.ecrire("note.md", "---\nname: batisseur\n\n# Titre\n")

        self.assertIsNone(lire_frontmatter(chemin))


class TestFichiersDeclaratifs(BaseCoffreTemporaire):
    def test_forme_plate(self):
        self.ecrire("skills/a.md", "---\nname: a\n---\n")
        self.ecrire("skills/b.md", "---\nname: b\n---\n")

        trouves = fichiers_declaratifs(self.racine / "skills")

        self.assertEqual([p.name for p in trouves], ["a.md", "b.md"])

    def test_forme_dossier(self):
        """La forme dossier est retenue par son fichier d'entrée homonyme."""
        self.ecrire("skills/a/a.md", "---\nname: a\n---\n")

        trouves = fichiers_declaratifs(self.racine / "skills")

        self.assertEqual([p.as_posix() for p in trouves],
                         [(self.racine / "skills/a/a.md").as_posix()])

    def test_formes_melangees_et_fichiers_annexes_ignores(self):
        """Dans un dossier de skill, seul le point d'entrée compte."""
        self.ecrire("skills/plate.md", "---\nname: plate\n---\n")
        self.ecrire("skills/dossier/dossier.md", "---\nname: dossier\n---\n")
        self.ecrire("skills/dossier/references/annexe.md", "# Annexe\n")
        self.ecrire("skills/dossier/notes.md", "# Notes\n")
        self.ecrire("skills/sans-entree/notes.md", "# Notes\n")
        self.ecrire("skills/.cache/plan.md", "# Plan\n")

        trouves = fichiers_declaratifs(self.racine / "skills")

        self.assertEqual([p.name for p in trouves], ["dossier.md", "plate.md"])

    def test_dossier_absent(self):
        """Un dossier qui n'existe pas rend une liste vide, sans lever."""
        self.assertEqual(fichiers_declaratifs(self.racine / "inexistant"), [])


class TestCollecter(BaseCoffreTemporaire):
    def test_forme_dossier_et_chemin_relatif(self):
        """`_fichier` dit la forme réelle, pour que le prompt la cite juste."""
        self.ecrire("skills/a/a.md", "---\nkind: skill\nname: a\n"
                                     "description: Faire a.\n---\n")

        trouves = collecter(self.racine / "skills", "skill")

        self.assertEqual(len(trouves), 1)
        self.assertEqual(trouves[0]["_fichier"], "a/a.md")

    def test_fichier_sans_frontmatter_ignore_avec_avertissement(self):
        """Un fichier illisible est signalé et écarté, jamais fatal."""
        self.ecrire("agents/bon.md", "---\nkind: agent\nname: bon\n"
                                     "description: Faire bon.\n---\n")
        self.ecrire("agents/casse.md", "# Sans frontmatter\n")

        err = StringIO()
        with redirect_stderr(err):
            trouves = collecter(self.racine / "agents", "agent")

        self.assertEqual([fm["name"] for fm in trouves], ["bon"])
        self.assertIn("casse.md", err.getvalue())

    def test_kind_etranger_ecarte(self):
        """Un genre inattendu est écarté, pas rangé de force dans le dossier."""
        self.ecrire("agents/un-skill.md", "---\nkind: skill\nname: un-skill\n"
                                          "description: Faire.\n---\n")

        with redirect_stderr(StringIO()):
            trouves = collecter(self.racine / "agents", "agent")

        self.assertEqual(trouves, [])


if __name__ == "__main__":
    unittest.main()
