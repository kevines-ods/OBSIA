#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Convention du coffre parent — ce qu'un tag est, et jusqu'où le parcours descend.

`appliquer_convention_parent.py` lit les tags `#…` du corps d'une note et
parcourt un dossier du coffre parent. Deux défauts constatés le 2026-10-06
(`_MAINTENANCE/2026-10-06-signalement-tags-hors-vocabulaire.md`) :

1. une **ancre de lien** `[Sources](#sources)` était lue comme le tag `#sources` :
   le motif cherchait un `#` n'importe où, suivi de caractères non blancs ;
2. le parcours s'arrêtait au premier niveau (`dossier.glob("*.md")`) : `0-PROJETS/`
   et `0-MEMOIRES/`, dont les notes vivent en sous-dossiers, passaient pour vides.

Ces tests figent les deux corrections, et vérifient que la descente récursive ne
rouvre pas un chantier gelé (§6).
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
SCRIPT = (RACINE / "IA" / "skills" / "traitement-des-notes" / "scripts"
          / "appliquer_convention_parent.py")


def charger(nom: str, chemin: Path):
    """Charge un script par son chemin, sous un nom de module à nous.

    Les outils de `IA/skills/*/scripts/` ne sont pas importables comme `scripts/`
    et c'est voulu : ce sont des outils de note, pas des scripts du produit.
    """
    spec = importlib.util.spec_from_file_location(nom, chemin)
    module = importlib.util.module_from_spec(spec)
    sys.modules[nom] = module
    spec.loader.exec_module(module)
    return module


CONVENTION = charger("appliquer_convention_parent_teste", SCRIPT)


class TestTagsInline(unittest.TestCase):
    """`tags_inline` ne confond ni une ancre, ni un titre, avec un tag."""

    def test_une_ancre_de_lien_n_est_pas_un_tag(self):
        note = ("# Filtrage du DNS\n\n"
                "## Sommaire\n\n"
                "1. [Introduction](#introduction)\n"
                "6. [Sources](#sources)\n")
        self.assertEqual(CONVENTION.tags_inline(note), [],
                         "`#introduction` et `#sources` sont des cibles de lien, "
                         "pas des tags")

    def test_un_titre_n_est_pas_un_tag(self):
        note = "# Titre\n\n## Installation Docker\n\nTexte.\n"
        self.assertEqual(CONVENTION.tags_inline(note), [])

    def test_un_vrai_tag_est_reconnu(self):
        note = "Une note sur le #réseau et le #docker.\n"
        self.assertEqual(CONVENTION.tags_inline(note), ["réseau", "docker"])

    def test_un_fragment_d_url_n_est_pas_un_tag(self):
        note = "Voir https://exemple.test/page#section pour le détail.\n"
        self.assertEqual(CONVENTION.tags_inline(note), [])

    def test_les_blocs_de_code_ne_sont_pas_lus(self):
        note = "Avant.\n\n```\n#pas-un-tag\n```\n\nAprès #vrai.\n"
        self.assertEqual(CONVENTION.tags_inline(note), ["vrai"])

    def test_un_diese_en_debut_de_ligne_est_un_titre(self):
        # b1 : la ligne est écartée comme titre avant tout examen ; la branche
        # « début de ligne » de l'ancien motif ne pouvait donc jamais servir.
        note = "#docker seul sur sa ligne\n"
        self.assertEqual(CONVENTION.tags_inline(note), [])

    def test_une_ponctuation_avant_le_diese_ecarte_le_tag(self):
        # b2 : `(`, `,`… ne valent pas une espace devant le `#`, pas plus que
        # pour Obsidian. Cette conséquence est documentée dans le code.
        note = "Voir (#docker) et a,#docker.\n"
        self.assertEqual(CONVENTION.tags_inline(note), [])


class CoffreTemporaire(unittest.TestCase):
    """Un coffre parent minimal : un projet aux notes en sous-dossier, et les
    deux moitiés de `0-MEMOIRES/`."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.coffre = Path(self._tmp.name).resolve()
        (self.coffre / "_MAINTENANCE").mkdir()

        # Des notes de savoir, dont une non UTF-8 : le lot ne doit pas s'arrêter.
        (self.coffre / "0-SAVOIRS").mkdir()
        (self.coffre / "0-SAVOIRS" / "note.md").write_text(
            "# Concept\n\nTexte.\n", encoding="utf-8")
        (self.coffre / "0-SAVOIRS" / "illisible.md").write_bytes(
            b"# Illisible\n\n\xff\xfe pas de l'UTF-8.\n")

        # Un projet dont les notes vivent en sous-dossier, et qui porte à côté un
        # dépôt Git (`code/`), un cache d'outil et un dossier technique.
        projet = self.coffre / "0-PROJETS" / "demo" / "documents"
        projet.mkdir(parents=True)
        (projet / "note.md").write_text("# Note de projet\n\nTexte.\n",
                                        encoding="utf-8")
        (self.coffre / "0-PROJETS" / "demo" / "README.md").write_text(
            "# demo\n\nFichier de dossier.\n", encoding="utf-8")
        for technique in ("code", "node_modules/pkg", ".stversions"):
            d = self.coffre / "0-PROJETS" / "demo" / technique
            d.mkdir(parents=True)
            (d / "hors-memoire.md").write_text(
                "# Hors mémoire\n\nÀ ne pas toucher.\n", encoding="utf-8")

        # Dossiers techniques à la racine, atteints par `--dossier=.`.
        for technique in (".opencode/node_modules/truc", ".stversions"):
            d = self.coffre / technique
            d.mkdir(parents=True)
            (d / "racine.md").write_text(
                "# Racine\n\nÀ ne pas toucher.\n", encoding="utf-8")

        memoires = self.coffre / "0-MEMOIRES"
        (memoires / "préférences").mkdir(parents=True)
        (memoires / "obsia" / "souverainete").mkdir(parents=True)
        (memoires / "préférences" / "syntaxe.md").write_text(
            "# Syntaxe\n\nPas de tabulations.\n", encoding="utf-8")
        (memoires / "obsia" / "souverainete" / "bilan.md").write_text(
            "# Bilan\n\nClos, on n'y touche plus.\n", encoding="utf-8")
        # N1 : un chantier qui imite la mémoire d'un agent. `obsia` n'est pas un
        # agent, donc ce dossier `expériences/` est un chantier — jamais écrit.
        (memoires / "obsia" / "expériences").mkdir(parents=True)
        (memoires / "obsia" / "expériences" / "lecon.md").write_text(
            "# Leçon close\n\nÀ ne pas toucher.\n", encoding="utf-8")
        # La vraie mémoire d'un agent, elle, reste vivante.
        (memoires / "batisseur" / "expériences").mkdir(parents=True)
        (memoires / "batisseur" / "expériences" / "livraison.md").write_text(
            "# Leçon vivante\n\nSe corrige sur place.\n", encoding="utf-8")

        # Des dépôts Git imbriqués dont le NOM n'est pas dans la liste : seul le
        # `.git` doit les faire écarter.
        for base in ("0-PROJETS/demo/outils", "outils"):
            d = self.coffre / base
            (d / ".git").mkdir(parents=True)
            (d / ".git" / "config").write_text("[core]\n", encoding="utf-8")
            (d / "hors-memoire.md").write_text(
                "# Dépôt imbriqué\n\nÀ ne pas toucher.\n", encoding="utf-8")

        # Le coffre lui-même est un dépôt : il ne doit pas s'auto-écarter.
        (self.coffre / ".git").mkdir()

    def lire(self, *morceaux):
        return (self.coffre.joinpath(*morceaux)).read_bytes()

    def executer(self, *argv):
        """Lance `main()` avec des arguments, en capturant la sortie standard."""
        ancien = sys.argv
        sys.argv = ["script"] + [str(a) for a in argv]
        tampon = io.StringIO()
        try:
            with contextlib.redirect_stdout(tampon):
                code = CONVENTION.main()
        finally:
            sys.argv = ancien
        return code, tampon.getvalue()


class TestParcoursEnProfondeur(CoffreTemporaire):

    def test_les_notes_en_sous_dossier_sont_vues(self):
        code, sortie = self.executer(
            "--racine", self.coffre, "--dossier", "0-PROJETS")
        self.assertEqual(code, 0)
        self.assertIn("demo/documents/note.md", sortie,
                      "les notes de 0-PROJETS/ vivent en sous-dossier : "
                      "un parcours d'un seul niveau ne les voit pas")
        self.assertNotIn("README.md", sortie,
                         "un fichier de dossier n'est pas une note")

    def test_la_convention_ecrit_dans_un_sous_dossier_de_projet(self):
        code, _ = self.executer(
            "--racine", self.coffre, "--appliquer", "--dossier", "0-PROJETS")
        self.assertEqual(code, 0)
        note = self.lire("0-PROJETS", "demo", "documents", "note.md")
        self.assertTrue(note.startswith(b"---"),
                        "une note en sous-dossier doit recevoir son frontmatter")
        self.assertIn(b"type: projet", note)

    def test_le_depot_git_du_projet_est_hors_memoire(self):
        # B1 : `0-PROJETS/<projet>/code/` est un dépôt Git distinct, hors mémoire.
        avant = self.lire("0-PROJETS", "demo", "code", "hors-memoire.md")
        code, sortie = self.executer(
            "--racine", self.coffre, "--appliquer", "--dossier", "0-PROJETS")
        self.assertEqual(code, 0)
        self.assertNotIn("code/hors-memoire.md", sortie,
                         "le code d'un projet n'est pas parcouru")
        self.assertEqual(self.lire("0-PROJETS", "demo", "code",
                                   "hors-memoire.md"), avant,
                         "aucun frontmatter n'est posé dans le dépôt du projet")

    def test_les_dossiers_techniques_sont_hors_memoire(self):
        # B2 : `node_modules/` et les dossiers en `.` ne sont jamais parcourus.
        avant = {
            "node_modules": self.lire("0-PROJETS", "demo", "node_modules", "pkg",
                                      "hors-memoire.md"),
            "stversions": self.lire("0-PROJETS", "demo", ".stversions",
                                    "hors-memoire.md"),
        }
        code, sortie = self.executer(
            "--racine", self.coffre, "--appliquer", "--dossier", "0-PROJETS")
        self.assertEqual(code, 0)
        for marque in ("node_modules", ".stversions"):
            self.assertNotIn(marque, sortie)
        self.assertEqual(self.lire("0-PROJETS", "demo", "node_modules", "pkg",
                                   "hors-memoire.md"), avant["node_modules"])
        self.assertEqual(self.lire("0-PROJETS", "demo", ".stversions",
                                   "hors-memoire.md"), avant["stversions"])

    def test_la_racine_ne_descend_pas_dans_les_dossiers_techniques(self):
        # B2, cas `--dossier=.` : `.opencode/node_modules/` et `.stversions/`.
        avant = (self.lire(".opencode", "node_modules", "truc", "racine.md"),
                 self.lire(".stversions", "racine.md"))
        code, sortie = self.executer(
            "--racine", self.coffre, "--dossier", ".")
        self.assertEqual(code, 0)
        for marque in (".opencode", ".stversions", "node_modules"):
            self.assertNotIn(marque, sortie)
        self.assertEqual(
            (self.lire(".opencode", "node_modules", "truc", "racine.md"),
             self.lire(".stversions", "racine.md")), avant)

    def test_un_depot_imbrique_sans_nom_connu_est_ecarte(self):
        # La règle `.git` dépasse la liste de noms : `outils/` n'est ni technique
        # ni caché, mais c'est un dépôt — on n'y pose pas de frontmatter.
        avant = self.lire("0-PROJETS", "demo", "outils", "hors-memoire.md")
        code, sortie = self.executer(
            "--racine", self.coffre, "--appliquer", "--dossier", "0-PROJETS")
        self.assertEqual(code, 0)
        self.assertNotIn("outils/hors-memoire.md", sortie,
                         "un dossier contenant un `.git` est un dépôt imbriqué")
        self.assertEqual(self.lire("0-PROJETS", "demo", "outils",
                                   "hors-memoire.md"), avant)

    def test_le_coffre_n_est_pas_ecarte_par_son_propre_depot(self):
        # La règle ne vise que les dépôts *imbriqués* : le coffre racine reste
        # parcouru, même quand c'est lui-même un dépôt.
        code, sortie = self.executer("--racine", self.coffre, "--dossier", ".")
        self.assertEqual(code, 0)
        self.assertIn("0-SAVOIRS/note.md", sortie,
                      "le coffre racine n'est pas écarté par son propre `.git`")
        self.assertNotIn("outils/hors-memoire.md", sortie,
                         "mais le dépôt `outils/` qu'il contient l'est")

    def test_un_dossier_sans_type_connu_n_ecrit_rien(self):
        # M1 : hors 0-EN-VRAC, un dossier sans `type` connu n'est pas écrit —
        # un frontmatter sans type resterait « partiel » à jamais.
        avant = self.lire("0-SAVOIRS", "note.md")
        code, sortie = self.executer(
            "--racine", self.coffre, "--appliquer", "--dossier", ".")
        self.assertEqual(code, 0)
        self.assertIn("sans `type` connu", sortie)
        self.assertEqual(self.lire("0-SAVOIRS", "note.md"), avant,
                         "rien n'est écrit là où le type est inconnu")

    def test_la_descente_recursive_ne_rouvre_pas_un_chantier_gele(self):
        gele = self.coffre / "0-MEMOIRES" / "obsia" / "souverainete" / "bilan.md"
        avant = gele.read_bytes()
        code, _ = self.executer(
            "--racine", self.coffre, "--appliquer", "--dossier", "0-MEMOIRES")
        self.assertEqual(code, 0)
        self.assertEqual(gele.read_bytes(), avant,
                         "la descente récursive ne rouvre jamais un chantier "
                         "gelé (§6)")
        vivante = self.lire("0-MEMOIRES", "préférences", "syntaxe.md")
        self.assertTrue(vivante.startswith(b"---"),
                        "la mémoire vivante, elle, se corrige sur place")
        self.assertIn(b"type: note", vivante,
                      "M1 : la mémoire vivante prend le type attrape-tout du "
                      "registre, jamais un frontmatter sans type")

    def test_un_sous_dossier_herite_du_type_de_son_dossier(self):
        # `--dossier=0-MEMOIRES/préférences` doit poser le même type que 0-MEMOIRES.
        code, _ = self.executer(
            "--racine", self.coffre, "--appliquer", "--dossier",
            "0-MEMOIRES/préférences")
        self.assertEqual(code, 0)
        self.assertIn(b"type: note", self.lire("0-MEMOIRES", "préférences",
                                               "syntaxe.md"))


class TestChantierGeleEtPointDeDepart(CoffreTemporaire):

    def test_un_experiences_sous_un_projet_est_un_chantier_gele(self):
        # N1 : la vivacité s'indexe sur la liste des agents, pas sur le nom
        # `expériences` seul.
        avant = self.lire("0-MEMOIRES", "obsia", "expériences", "lecon.md")
        code, _ = self.executer(
            "--racine", self.coffre, "--appliquer", "--dossier", "0-MEMOIRES")
        self.assertEqual(code, 0)
        self.assertEqual(self.lire("0-MEMOIRES", "obsia", "expériences",
                                   "lecon.md"), avant,
                         "`obsia` n'est pas un agent : ce dossier `expériences/` "
                         "est un chantier, pas de la mémoire vivante")
        self.assertIn(b"type: note", self.lire("0-MEMOIRES", "batisseur",
                                               "expériences", "livraison.md"),
                      "la mémoire d'un vrai agent, elle, reste vivante")

    def test_un_point_de_depart_sous_code_est_refuse(self):
        # N2 : viser `code/` ne doit pas ouvrir le dépôt au frontmatter.
        avant = self.lire("0-PROJETS", "demo", "code", "hors-memoire.md")
        code, sortie = self.executer(
            "--racine", self.coffre, "--appliquer",
            "--dossier", "0-PROJETS/demo/code")
        self.assertEqual(code, 0)
        self.assertIn("hors mémoire", sortie)
        self.assertEqual(self.lire("0-PROJETS", "demo", "code",
                                   "hors-memoire.md"), avant)

    def test_un_point_de_depart_dans_un_depot_imbrique_est_refuse(self):
        avant = self.lire("0-PROJETS", "demo", "outils", "hors-memoire.md")
        code, sortie = self.executer(
            "--racine", self.coffre, "--appliquer",
            "--dossier", "0-PROJETS/demo/outils")
        self.assertEqual(code, 0)
        self.assertIn("hors mémoire", sortie)
        self.assertEqual(self.lire("0-PROJETS", "demo", "outils",
                                   "hors-memoire.md"), avant)

    def test_un_point_de_depart_prefixe_par_point_est_normalise(self):
        # N3 : `./0-MEMOIRES` doit poser le même type que `0-MEMOIRES`.
        code, _ = self.executer(
            "--racine", self.coffre, "--appliquer", "--dossier", "./0-MEMOIRES")
        self.assertEqual(code, 0)
        self.assertIn(b"type: note", self.lire("0-MEMOIRES", "préférences",
                                               "syntaxe.md"))


class TestLectureRobuste(CoffreTemporaire):

    def test_une_note_non_utf8_n_arrete_pas_le_lot(self):
        # b4 : une note illisible est signalée, le reste du lot est traité.
        avant = self.lire("0-SAVOIRS", "illisible.md")
        code, sortie = self.executer(
            "--racine", self.coffre, "--appliquer", "--dossier", "0-SAVOIRS")
        self.assertEqual(code, 0)
        self.assertIn("illisible", sortie)
        self.assertEqual(self.lire("0-SAVOIRS", "illisible.md"), avant,
                         "la note non UTF-8 n'est pas touchée")
        self.assertIn(b"type: concept", self.lire("0-SAVOIRS", "note.md"),
                      "les autres notes du dossier sont bien traitées")


if __name__ == "__main__":
    unittest.main()
