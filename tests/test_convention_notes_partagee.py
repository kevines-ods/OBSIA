#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""La convention des notes du coffre parent — filet de la tranche P1.

P1 sort la convention des notes de ses trois copies (l'applicateur, l'indexeur,
`regenerate_sommaire.py`) vers un seul module, `scripts/convention_des_notes.py`.
Ce fichier-ci fige **ce que font les outils aujourd'hui**, pour qu'une
régression se voie : les classes `…Caracterise` passent sur le code d'avant
comme sur celui d'après l'extraction.

Elles n'appellent que ce qui est observable — les fonctions publiques des outils
et le contenu de l'index rendu — jamais un détail interne qui a le droit de
changer de forme en chemin (l'indexeur, par exemple, ne garde pas sa propre
lecture du frontmatter : il emprunte celle du moteur).

Les classes `TestUneSeuleCopie*` ne s'exécutent que lorsque le moteur partagé
existe : elles ne caractérisent pas l'ancien code, elles vérifient la copie
unique et ses fonctions pures.
"""

import contextlib
import importlib.util
import io
import re
import sys
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent

CHEMINS = {
    "APPLICATEUR": (RACINE / "IA" / "skills" / "traitement-des-notes"
                    / "scripts" / "appliquer_convention_parent.py"),
    "INDEXEUR": (RACINE / "IA" / "skills" / "traitement-des-notes"
                 / "scripts" / "indexer_coffre_parent.py"),
    "SOMMAIRE": RACINE / "scripts" / "regenerate_sommaire.py",
}


def charger(nom: str):
    """Charge un outil par son chemin (ils ne sont pas importables en paquet)."""
    spec = importlib.util.spec_from_file_location("carac_" + nom, CHEMINS[nom])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


APPLICATEUR = charger("APPLICATEUR")
INDEXEUR = charger("INDEXEUR")
SOMMAIRE = charger("SOMMAIRE")

# Le moteur partagé : présent seulement après l'extraction de P1.
sys.path.insert(0, str(RACINE / "scripts"))
try:
    import convention_des_notes as MOTEUR
except ImportError:                       # avant P1 : la copie n'existe pas
    MOTEUR = None


NOTE = (
    "---\n"
    "type: concept\n"
    "schema: 1\n"
    "essentiel: true\n"
    "tags:\n"
    "  - reseau\n"
    "  - docker\n"
    "description: Un essai.\n"
    "---\n"
    "\n"
    "# Titre de la note\n"
    "\n"
    "Le corps commence ici.\n"
)
SANS = "# Sans frontmatter\n\ntexte\n"
NON_FERME = "---\ntype: concept\n\n# Titre\n"

ATTENDU_NOTE = {
    "type": "concept",
    "schema": 1,
    "essentiel": True,
    "tags": ["reseau", "docker"],
    "description": "Un essai.",
}


def _noms_listes(index: str) -> list:
    """Les noms de notes listés par un index rendu, dans l'ordre."""
    return re.findall(r"^\| `([^`]+)` \|", index, flags=re.M)


class TestFrontmatterCaracterise(unittest.TestCase):
    """Une seule lecture du frontmatter, avec sa position de corps."""

    def test_l_applicateur_rend_les_valeurs_typees_et_la_fin_du_bloc(self):
        donnees, fin = APPLICATEUR.extraire_frontmatter(NOTE)
        self.assertEqual(donnees, ATTENDU_NOTE)
        self.assertEqual(NOTE[fin:], "\n# Titre de la note\n\nLe corps commence ici.\n")

    def test_une_note_sans_frontmatter_n_est_pas_un_bloc(self):
        self.assertEqual(APPLICATEUR.extraire_frontmatter(SANS), (None, 0))

    def test_un_frontmatter_non_ferme_n_est_pas_un_frontmatter(self):
        self.assertEqual(APPLICATEUR.extraire_frontmatter(NON_FERME), (None, 0))

    def test_l_indexeur_lit_la_meme_note_et_la_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            note = Path(tmp) / "note.md"
            note.write_text(NOTE, encoding="utf-8")
            self.assertEqual(
                INDEXEUR.ligne(note),
                "| `note.md` | Un essai. | concept | `reseau`, `docker` |")

    def test_l_indexeur_nomme_une_note_sans_frontmatter_par_son_titre(self):
        with tempfile.TemporaryDirectory() as tmp:
            note = Path(tmp) / "sans.md"
            note.write_text(SANS, encoding="utf-8")
            self.assertEqual(
                INDEXEUR.ligne(note),
                "| `sans.md` | Sans frontmatter | — | — |")


class TestParcoursCaracterise(unittest.TestCase):
    """Le parcours d'un dossier : frontière de mémoire et fichiers vus."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dossier = Path(self._tmp.name) / "0-SAVOIRS"
        self.dossier.mkdir()
        (self.dossier / "note.md").write_text(NOTE, encoding="utf-8")
        (self.dossier / "sans.md").write_text(SANS, encoding="utf-8")
        (self.dossier / "sommaire.md").write_text("# Sommaire\n", encoding="utf-8")
        (self.dossier / "README.md").write_text("# Dossier\n", encoding="utf-8")
        (self.dossier / "index-0-savoirs.md").write_text(
            "# Index\n", encoding="utf-8")
        # Un dossier caché : hors mémoire, des deux côtés.
        cache = self.dossier / ".cache"
        cache.mkdir()
        (cache / "cache.md").write_text("# Cache\n", encoding="utf-8")
        # Un projet : son `code/` est un dépôt Git, et son `node_modules/` vit
        # dedans — comme dans le vrai coffre.
        code = self.dossier / "code"
        (code / ".git").mkdir(parents=True)
        (code / "x.md").write_text("# Code\n", encoding="utf-8")
        paquet = code / "node_modules" / "pkg"
        paquet.mkdir(parents=True)
        (paquet / "README.md").write_text("# Paquet\n", encoding="utf-8")
        # Une note dans un sous-dossier ordinaire : elle est vue.
        sous = self.dossier / "sous"
        sous.mkdir()
        (sous / "note2.md").write_text("# Note 2\n", encoding="utf-8")
        # Un `.md` caché et un `.md` en majuscules : l'applicateur les traite
        # comme des notes, l'indexeur doit lister les mêmes — sans filtre sur
        # les noms cachés ni sur la casse de l'extension.
        (self.dossier / ".apercu.md").write_text("# Aperçu\n", encoding="utf-8")
        (self.dossier / "MAJUSCULE.MD").write_text("# Majuscule\n", encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def _relatives(self, notes) -> list:
        return [p.relative_to(self.dossier).as_posix() for p in notes]

    def test_l_applicateur_ne_voit_que_les_notes(self):
        # Fichiers de dossier, caches, node_modules et dépôt imbriqué écartés.
        # Le `.md` caché et le `.md` en majuscules, eux, sont des notes.
        self.assertEqual(
            self._relatives(APPLICATEUR.notes_du_dossier(self.dossier)),
            [".apercu.md", "MAJUSCULE.MD", "index-0-savoirs.md", "note.md",
             "sans.md", "sous/note2.md"])

    def test_l_indexeur_ne_liste_plus_les_fichiers_du_dossier(self):
        # Aligné sur l'applicateur (phase 1 du plan) : sommaire.md et README.md,
        # des fichiers de dossier que l'installeur pose, ne sont plus des notes.
        # Il ne voit pas non plus .cache/, node_modules/, code/ (dépôt), ni son
        # propre index — mais il liste, comme l'applicateur, le `.md` caché et
        # le `.md` en majuscules.
        self.assertEqual(
            _noms_listes(INDEXEUR.rendre("0-SAVOIRS", self.dossier)),
            [".apercu.md", "MAJUSCULE.MD", "note.md", "sans.md", "note2.md"])

    def test_l_indexeur_ne_se_liste_pas_lui_meme(self):
        rendu = INDEXEUR.rendre("0-SAVOIRS", self.dossier)
        self.assertNotIn("| `index-0-savoirs.md` |", rendu)

    def test_l_indexeur_choisit_les_memes_notes_que_l_applicateur(self):
        # Une seule définition de « note » (phase 1 du plan) : l'indexeur liste
        # exactement les notes que l'applicateur écrit, moins ses propres index.
        au_moteur = [p.name for p in APPLICATEUR.notes_du_dossier(self.dossier)
                     if p.name not in INDEXEUR.INDEX_GENERES]
        self.assertEqual(
            _noms_listes(INDEXEUR.rendre("0-SAVOIRS", self.dossier)), au_moteur)


class TestFrontiereDeMemoireCaracterise(unittest.TestCase):
    """La règle de zone : un dépôt imbriqué n'est jamais de la mémoire."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.racine = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_un_dossier_a_git_est_un_depot_imbrique(self):
        projet = self.racine / "monprojet"
        (projet / ".git").mkdir(parents=True)
        self.assertTrue(APPLICATEUR.est_depot_imbrique(projet))
        self.assertTrue(SOMMAIRE.est_depot_imbrique(str(projet)))

    def test_le_fichier_git_compte_comme_le_dossier(self):
        # Un sous-module ou un arbre de travail porte un *fichier* .git.
        projet = self.racine / "lie"
        projet.mkdir()
        (projet / ".git").write_text("gitdir: ailleurs\n", encoding="utf-8")
        self.assertTrue(APPLICATEUR.est_depot_imbrique(projet))
        self.assertTrue(SOMMAIRE.est_depot_imbrique(str(projet)))

    def test_les_dossiers_hors_memoire_par_leur_nom(self):
        for nom in ("code", "node_modules"):
            self.assertTrue(SOMMAIRE.dossier_hors_memoire(
                str(self.racine / nom)))
        self.assertFalse(SOMMAIRE.dossier_hors_memoire(
            str(self.racine / "0-SAVOIRS")))

    def test_le_point_de_depart_ecarte_les_memes_zones(self):
        coffre = self.racine / "coffre"
        (coffre / "code" / ".git").mkdir(parents=True)
        self.assertTrue(APPLICATEUR.point_de_depart_ecarte(
            coffre / "code", coffre))
        self.assertTrue(APPLICATEUR.point_de_depart_ecarte(
            coffre / ".cache", coffre))
        self.assertFalse(APPLICATEUR.point_de_depart_ecarte(
            coffre / "0-SAVOIRS", coffre))


@unittest.skipIf(MOTEUR is None, "moteur partagé absent (avant l'extraction P1)")
class TestUneSeuleCopie(unittest.TestCase):
    """Après P1 : plus qu'une définition de chaque règle partagée."""

    def test_les_trois_outils_empruntent_la_meme_lecture_du_frontmatter(self):
        self.assertIs(APPLICATEUR.extraire_frontmatter,
                      MOTEUR.extraire_frontmatter)
        self.assertIs(INDEXEUR.extraire_frontmatter,
                      MOTEUR.extraire_frontmatter)

    def test_les_outils_empruntent_le_meme_parcours_et_la_meme_frontiere(self):
        self.assertIs(APPLICATEUR.notes_du_dossier, MOTEUR.notes_du_dossier)
        self.assertIs(INDEXEUR.notes_du_dossier, MOTEUR.notes_du_dossier)
        self.assertIs(APPLICATEUR.est_depot_imbrique, MOTEUR.est_depot_imbrique)
        self.assertIs(SOMMAIRE.est_depot_imbrique, MOTEUR.est_depot_imbrique)
        self.assertIs(SOMMAIRE.dossier_hors_memoire, MOTEUR.dossier_hors_memoire)

    def test_l_applicateur_emprunte_les_regles_de_memoire_et_les_tags(self):
        # La porte les appelle pour son contrôle de mémoire gelée : le moteur en
        # reste l'unique exemplaire, et l'applicateur les emprunte comme le reste.
        self.assertIs(APPLICATEUR.est_gele, MOTEUR.est_gele)
        self.assertIs(APPLICATEUR.point_de_depart_ecarte,
                      MOTEUR.point_de_depart_ecarte)
        self.assertIs(APPLICATEUR.liste_des_agents, MOTEUR.liste_des_agents)
        self.assertIs(APPLICATEUR.lire_registre, MOTEUR.lire_registre)
        self.assertIs(APPLICATEUR.tags_inline, MOTEUR.tags_inline)


@unittest.skipIf(MOTEUR is None, "moteur partagé absent (avant l'extraction P1)")
class TestMoteurPartage(unittest.TestCase):
    """Les fonctions pures du moteur, une par une."""

    def test_est_note_ecarte_les_fichiers_de_dossier(self):
        self.assertTrue(MOTEUR.est_note("note.md"))
        self.assertTrue(MOTEUR.est_note("NOTE.MD"))
        self.assertFalse(MOTEUR.est_note("sommaire.md"))
        self.assertFalse(MOTEUR.est_note("README.md"))
        self.assertFalse(MOTEUR.est_note("readme.md"))
        self.assertFalse(MOTEUR.est_note("image.png"))

    def test_extraire_frontmatter_type_les_valeurs(self):
        donnees, fin = MOTEUR.extraire_frontmatter(NOTE)
        self.assertEqual(donnees, ATTENDU_NOTE)
        self.assertEqual(MOTEUR.corps(NOTE), NOTE[fin:])

    def test_les_guillemets_tombent_aussi_autour_des_puces_de_liste(self):
        # Seul comportement qui change volontairement en P1 : la lecture unique
        # reprend le nettoyage des guillemets de l'ancien indexeur, que
        # l'ancien applicateur oubliait (`- 'reseau'` donnait `'reseau'`).
        texte = ("---\n"
                 "type: \"concept\"\n"
                 "tags:\n"
                 "  - 'reseau'\n"
                 "  - docker\n"
                 "---\n"
                 "\n"
                 "Corps.\n")
        donnees, _ = MOTEUR.extraire_frontmatter(texte)
        self.assertEqual(donnees["type"], "concept")
        self.assertEqual(donnees["tags"], ["reseau", "docker"])

    def test_corps_rend_le_texte_entier_sans_frontmatter(self):
        self.assertEqual(MOTEUR.corps(SANS), SANS)
        self.assertEqual(MOTEUR.corps(NON_FERME), NON_FERME)

    def test_dossier_hors_memoire_se_lit_sur_la_copie_unique(self):
        self.assertTrue(MOTEUR.dossier_hors_memoire("code"))
        self.assertTrue(MOTEUR.dossier_hors_memoire("node_modules"))
        self.assertFalse(MOTEUR.dossier_hors_memoire("0-SAVOIRS"))

    def test_les_constantes_de_la_convention(self):
        self.assertEqual(sorted(MOTEUR.DOSSIERS_HORS_MEMOIRE),
                         ["code", "node_modules"])
        self.assertEqual(sorted(MOTEUR.FICHIERS_DE_DOSSIER),
                         ["readme.md", "sommaire.md"])

    def test_la_forme_de_la_date_est_ancree_aux_deux_bouts(self):
        # `$` laisse passer un saut de ligne final : `2026-10-10\n` était accepté
        # comme date d'acte. La forme est ancrée, sans quoi une date de carnet
        # pourrait porter une ligne de trop.
        self.assertTrue(MOTEUR.DATE_ISO.match("2026-10-10"))
        self.assertFalse(MOTEUR.DATE_ISO.match("2026-10-10\n"))
        self.assertFalse(MOTEUR.DATE_ISO.match("2026-10-10 "))
        self.assertFalse(MOTEUR.DATE_ISO.match("\n2026-10-10"))

    def test_le_vocabulaire_se_lit_sur_le_texte_du_registre(self):
        # Seule la table « Vocabulaire » fait foi ; celle des types et celle des
        # candidats ne comptent pas.
        texte = ("## Type d'une note\n\n"
                 "| Type | Ce que c'est |\n| --- | --- |\n"
                 "| Concept | `concept` |\n\n"
                 "## Vocabulaire\n\n"
                 "| Domaine | Tags |\n| --- | --- |\n"
                 "| Conteneurs | `docker`, `podman` |\n\n"
                 "## Candidats\n\n"
                 "| Domaine | Tags |\n| --- | --- |\n"
                 "| Divers | `hors-registre` |\n")
        self.assertEqual(MOTEUR.vocabulaire_des_tags(texte), {"docker", "podman"})

    def test_les_tags_inline_ecartent_titres_et_ancres(self):
        self.assertEqual(
            MOTEUR.tags_inline("# Titre\n\ncorps #docker et #docker\n"
                               "[lien](#ancre) et a,b#pas-un-tag\n"),
            ["docker"])

    def test_une_liste_yaml_sur_une_ligne_se_voit(self):
        # Le contrat veut une entrée par ligne : la forme en ligne doit être vue,
        # sinon elle serait lue comme un tag unique `[docker, reseau]`, absent du
        # vocabulaire, et le refus parlerait des tags au lieu de la forme.
        self.assertEqual(
            MOTEUR.listes_en_ligne(
                "---\ntags: [docker, reseau]\nkind: note\n---\n\nCorps.\n"),
            ["tags"])
        self.assertEqual(MOTEUR.listes_en_ligne(NOTE), [])
        self.assertEqual(MOTEUR.listes_en_ligne(SANS), [])

    def test_une_part_hors_memoire_a_une_seule_definition(self):
        # La règle vit dans le moteur ; la carte et la porte l'empruntent.
        self.assertTrue(MOTEUR.partie_hors_memoire("code"))
        self.assertTrue(MOTEUR.partie_hors_memoire(".cache"))
        self.assertFalse(MOTEUR.partie_hors_memoire("0-SAVOIRS"))

    def test_un_agent_se_declare_en_fichier_plat_ou_en_dossier(self):
        # Les deux formes du §5 comptent : un agent déclaré en dossier a lui
        # aussi une mémoire vivante, à ne pas confondre avec un chantier gelé.
        with tempfile.TemporaryDirectory() as tmp:
            racine = Path(tmp)
            agents = racine / "IA" / "agents"
            agents.mkdir(parents=True)
            (agents / "plat.md").write_text("---\nkind: agent\n---\n",
                                            encoding="utf-8")
            dossier = agents / "dossier"
            dossier.mkdir()
            (dossier / "dossier.md").write_text("---\nkind: agent\n---\n",
                                                encoding="utf-8")
            self.assertEqual(MOTEUR.liste_des_agents(racine),
                             {"plat", "dossier"})

    def test_un_champ_de_frontmatter_repete_se_voit(self):
        texte = "---\ntype: concept\ntype: projet\n---\n\nCorps.\n"
        self.assertEqual(MOTEUR.cles_repetees(texte), ["type"])
        self.assertEqual(MOTEUR.frontmatter_brut(texte),
                         "\ntype: concept\ntype: projet")
        self.assertEqual(MOTEUR.cles_repetees(NOTE), [])
        self.assertIsNone(MOTEUR.frontmatter_brut(SANS))
        self.assertIsNone(MOTEUR.frontmatter_brut(NON_FERME))

    def test_notes_du_dossier_retenir_resserre_la_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            dossier = Path(tmp)
            (dossier / "note.md").write_text("# n\n", encoding="utf-8")
            (dossier / "sommaire.md").write_text("# s\n", encoding="utf-8")
            (dossier / "visible.md").write_text("# v\n", encoding="utf-8")
            (dossier / ".cache.md").write_text("# c\n", encoding="utf-8")

            def seulement(nom):
                return nom.endswith(".md") and not nom.startswith(".")

            self.assertEqual(
                [p.name for p in MOTEUR.notes_du_dossier(dossier)],
                [".cache.md", "note.md", "visible.md"])
            self.assertEqual(
                [p.name for p in MOTEUR.notes_du_dossier(
                    dossier, retenir=seulement)],
                ["note.md", "sommaire.md", "visible.md"])


class TestMatriceDuContrat(unittest.TestCase):
    """La matrice du §7.3 : zone × auteur × nature d'écriture, en un exemplaire.

    Le premier critère de P3 veut que la règle vive dans le moteur partagé et que
    la carte comme la porte la lisent de là. Ces tests la tiennent des trois
    côtés : la zone ouverte, l'auteur nommé, la nature permise.
    """

    def ouvert(self, chemin, auteur, nature=None):
        return MOTEUR.zone_autorisee(chemin, auteur, nature)[0]

    def test_le_vrac_et_les_savoirs_sont_ouverts_a_tout_auteur(self):
        # `0-EN-VRAC/` se remplit et se classe ; `0-SAVOIRS/` se complète.
        for auteur in ("utilisateur", "assistant", "batisseur"):
            self.assertTrue(self.ouvert("0-EN-VRAC/docker.md", auteur), auteur)
            self.assertTrue(self.ouvert("0-SAVOIRS/docker.md", auteur), auteur)
        self.assertTrue(self.ouvert("0-EN-VRAC/docker.md", "assistant",
                                    MOTEUR.NATURE_DEPOSER))

    def test_une_vision_n_est_ouverte_qu_au_visionnaire(self):
        chemin = "0-PROJETS/mon-projet/mon-projet — vision.md"
        self.assertTrue(self.ouvert(chemin, MOTEUR.AUTEUR_VISIONNAIRE))
        self.assertFalse(self.ouvert(chemin, "batisseur"))
        # L'utilisateur lui-même ne l'écrit pas en direct : le §7.3 la réserve au
        # visionnaire, qui la pose après sa validation.
        self.assertFalse(self.ouvert(chemin, MOTEUR.AUTEUR_UTILISATEUR))
        _, motif = MOTEUR.zone_autorisee(chemin, "batisseur")
        self.assertIn(MOTEUR.AUTEUR_VISIONNAIRE, motif)

    def test_une_vision_tient_sur_le_nom_reel_du_dossier(self):
        # Le dossier porte `Homelab` : c'est bien `Homelab — vision.md` qui est
        # *sa* vision, réservée au visionnaire.
        chemin = "0-PROJETS/Homelab/Homelab — vision.md"
        self.assertTrue(self.ouvert(chemin, MOTEUR.AUTEUR_VISIONNAIRE))
        self.assertFalse(self.ouvert(chemin, "batisseur"))
        self.assertFalse(self.ouvert(chemin, MOTEUR.AUTEUR_UTILISATEUR))

    def test_une_vision_tient_sur_un_nom_a_espace_ou_a_accent(self):
        # Majuscules, espaces, accents : le nom du dossier et le nom de la note
        # se comparent sous forme normalisée, pas au caractère près — une casse
        # ou un accent d'écart ne doit pas sortir la note de sa règle.
        for chemin in ("0-PROJETS/mon coffre/mon coffre — vision.md",
                       "0-PROJETS/préférences/preferences — vision.md",
                       "0-PROJETS/préférences/préférences-vision.md",
                       "0-PROJETS/Homelab/homelab — vision.md",
                       "0-PROJETS/Homelab/homelab-vision.md"):
            self.assertTrue(self.ouvert(chemin, MOTEUR.AUTEUR_VISIONNAIRE), chemin)
            self.assertFalse(self.ouvert(chemin, "batisseur"), chemin)
            self.assertFalse(self.ouvert(chemin, MOTEUR.AUTEUR_UTILISATEUR), chemin)

    def test_une_note_hors_projet_n_est_pas_la_vision(self):
        # La comparaison porte sur le nom **du dossier** : `autre-projet — vision`
        # dans le dossier `Homelab` n'est pas la vision de `Homelab`.
        hors = "0-PROJETS/Homelab/autre — vision.md"
        self.assertNotEqual(MOTEUR.regle_de_zone(hors),
                            MOTEUR.regle_de_zone("0-PROJETS/Homelab/Homelab — vision.md"))

    def test_la_vision_n_a_qu_une_regle_pour_deux_graphies(self):
        # `Homelab — vision.md` et `homelab-vision.md` désignent la même note :
        # les comparer en normalisé interdit qu'un doublon se glisse entre deux
        # règles et échappe au visionnaire seul.
        tiret = "0-PROJETS/Homelab/Homelab — vision.md"
        trait = "0-PROJETS/Homelab/homelab-vision.md"
        self.assertEqual(MOTEUR.regle_de_zone(tiret), MOTEUR.regle_de_zone(trait))
        self.assertFalse(self.ouvert(trait, "batisseur"))

    def test_les_carnets_et_documents_d_un_chantier_sont_modelises(self):
        # Le §7.3 (annexe) : `0-PROJETS/<projet>/<chantier>/` porte ses
        # `carnets/`, ses `documents/` et son `<chantier> — résumé.md` ; un seul
        # niveau.
        carnet = "0-PROJETS/projet/chantier/carnets/jour.md"
        self.assertTrue(self.ouvert(carnet, "batisseur", MOTEUR.NATURE_CREER))
        document = "0-PROJETS/projet/chantier/documents/spec.md"
        self.assertTrue(self.ouvert(document, "batisseur", MOTEUR.NATURE_DEPOSER))
        resume = "0-PROJETS/projet/chantier/chantier — résumé.md"
        self.assertTrue(self.ouvert(resume, "batisseur", MOTEUR.NATURE_CREER))
        # Deux niveaux de chantier n'existent pas : plus de tenue sur place.
        trop = "0-PROJETS/projet/chantier/sous-chantier/carnets/jour.md"
        self.assertFalse(self.ouvert(trop, "batisseur", MOTEUR.NATURE_CREER))

    def test_le_dossier_d_un_projet_ne_s_ouvre_pas_sans_projet(self):
        # `0-PROJETS/` seul n'est pas un projet, et `0-PROJETS/<projet>/` seul ne
        # reçoit qu'un dépôt de note classée — jamais une note neuve.
        self.assertIsNone(MOTEUR.regle_de_zone("0-PROJETS"))
        self.assertFalse(self.ouvert("0-PROJETS/projet/inventee.md", "batisseur",
                                     MOTEUR.NATURE_CREER))

    def test_les_experiences_d_un_agent_ne_sont_ouvertes_qu_a_lui(self):
        chemin = "0-MEMOIRES/batisseur/expériences/lecon.md"
        self.assertTrue(self.ouvert(chemin, "batisseur"))
        self.assertFalse(self.ouvert(chemin, "assistant"))
        self.assertFalse(self.ouvert(chemin, MOTEUR.AUTEUR_UTILISATEUR))

    def test_les_preferences_et_le_profil_restent_vivants(self):
        # La moitié vivante de `0-MEMOIRES/`, et le profil : c'est ce qui
        # distingue une mémoire qui vit d'un chantier gelé (§6).
        self.assertTrue(self.ouvert("0-MEMOIRES/préférences/style.md", "assistant"))
        self.assertTrue(self.ouvert("0-PERSONNELS/profil-utilisateur.md", "batisseur"))

    def test_la_note_de_reference_d_un_agent_se_tient_sur_place(self):
        # La note de référence de `0-PERSONNELS/` : l'agent que son champ `auteur:`
        # nomme la tient **sur place** ; tout autre agent ne l'écrit pas. Le **dépôt**
        # d'une note classée y reste ouvert à tous — c'est la nature qui sépare les deux.
        chemin = "0-PERSONNELS/ordonnanceur.md"
        texte = "---\nauteur: batisseur\nkind: note\ntags:\n- coffre\n---\n\n# Là\n"
        ouvert, _ = MOTEUR.zone_autorisee(chemin, "batisseur", MOTEUR.NATURE_COMPLETER,
                                          note=texte, avant=texte)
        self.assertTrue(ouvert)
        self.assertTrue(MOTEUR.zone_autorisee(chemin, "batisseur", MOTEUR.NATURE_CREER,
                                              note=texte)[0])
        ouvert, motif = MOTEUR.zone_autorisee(chemin, "assistant",
                                              MOTEUR.NATURE_COMPLETER,
                                              note=texte, avant=texte)
        self.assertFalse(ouvert)
        self.assertIn("auteur", motif)
        self.assertTrue(self.ouvert(chemin, "assistant", MOTEUR.NATURE_DEPOSER))

    def test_la_note_de_reference_ne_change_pas_de_main(self):
        # Double condition : le champ `auteur:` doit nommer l'agent **dans la note
        # existante** et **dans le texte proposé**. Ni une note à un autre qu'on
        # s'attribue, ni un texte qui change de main.
        chemin = "0-PERSONNELS/ordonnanceur.md"
        mien = "---\nauteur: batisseur\nkind: note\n---\n\n# Mien\n"
        sien = "---\nauteur: assistant\nkind: note\n---\n\n# Sien\n"
        self.assertFalse(MOTEUR.zone_autorisee(chemin, "batisseur",
                                               MOTEUR.NATURE_COMPLETER,
                                               note=sien, avant=mien)[0])
        self.assertFalse(MOTEUR.zone_autorisee(chemin, "batisseur",
                                               MOTEUR.NATURE_COMPLETER,
                                               note=mien, avant=sien)[0])
        self.assertFalse(MOTEUR.zone_autorisee(chemin, "batisseur",
                                               MOTEUR.NATURE_CREER, note=sien)[0],
                         "on ne pose pas une note de référence au nom d'un autre")

    def test_un_chantier_de_memoire_est_ferme(self):
        # Un chantier de `0-MEMOIRES/` n'est pas une zone de la matrice, et le
        # refus doit le dire comme un chantier gelé, pas comme un dossier inconnu.
        chemin = "0-MEMOIRES/2026-01-chantier/note.md"
        self.assertIsNone(MOTEUR.regle_de_zone(chemin))
        ouvert, motif = MOTEUR.zone_autorisee(chemin, "assistant")
        self.assertFalse(ouvert)
        self.assertIn("gelé", motif)

    def test_la_maintenance_du_coffre_est_ouverte(self):
        # Le §7.4 fait de `_MAINTENANCE/` la zone de passage — previews, actions,
        # registre `notes_remplies.md` ; le §7.3 l'ouvre donc, à tout auteur.
        for chemin in ("_MAINTENANCE/apercu.md",
                       "_MAINTENANCE/actions/2026-10-09.md",
                       "_MAINTENANCE/notes_remplies.md"):
            self.assertIsNotNone(MOTEUR.regle_de_zone(chemin), chemin)
            self.assertTrue(self.ouvert(chemin, "assistant"), chemin)
        self.assertTrue(self.ouvert("_MAINTENANCE/apercu.md", "batisseur",
                                    MOTEUR.NATURE_CREER))

    def test_tout_autre_dossier_est_refuse(self):
        for chemin in ("1-ARCHIVES/note.md", "mon-dossier/note.md", "note.md"):
            self.assertIsNone(MOTEUR.regle_de_zone(chemin), chemin)
            self.assertFalse(self.ouvert(chemin, "assistant"), chemin)

    def test_sans_auteur_declare_la_matrice_ne_s_ouvre_pas(self):
        # Échec fermé : un auteur absent ne fait pas retomber le §7.3 sur
        # « tout est ouvert » — il le ferme, et d'un seul mot.
        for auteur in (None, "", "   "):
            ouvert, motif = MOTEUR.zone_autorisee("0-EN-VRAC/docker.md", auteur)
            self.assertFalse(ouvert, auteur)
            self.assertEqual(motif, MOTEUR.MOTIF_AUTEUR_ABSENT)

    def test_la_nature_d_ecriture_est_verifiee(self):
        # `0-SAVOIRS/` ne reçoit pas de note neuve : le §7.3 y ouvre la
        # complétion d'une note déposée par l'utilisateur, et le classement d'une
        # note venue d'`0-EN-VRAC/` — jamais la création.
        self.assertTrue(self.ouvert("0-SAVOIRS/docker.md", "assistant",
                                    MOTEUR.NATURE_COMPLETER))
        self.assertTrue(self.ouvert("0-SAVOIRS/docker.md", "assistant",
                                    MOTEUR.NATURE_DEPOSER))
        self.assertFalse(self.ouvert("0-SAVOIRS/docker.md", "assistant",
                                     MOTEUR.NATURE_CREER))
        _, motif = MOTEUR.zone_autorisee("0-SAVOIRS/docker.md", "assistant",
                                         MOTEUR.NATURE_CREER)
        self.assertIn(MOTEUR.NATURE_COMPLETER, motif)

    def test_la_matrice_ne_reconnait_que_les_dossiers_du_contrat(self):
        self.assertIn("0-PROJETS", MOTEUR.ZONES_DU_CONTRAT)
        self.assertIn(MOTEUR.MEMOIRES, MOTEUR.ZONES_DU_CONTRAT)
        self.assertIn(MOTEUR.MAINTENANCE, MOTEUR.ZONES_DU_CONTRAT)
        self.assertNotIn("1-ARCHIVES", MOTEUR.ZONES_DU_CONTRAT)

    def test_la_table_nomme_les_tetes_simples_du_contrat(self):
        # La table est l'exemplaire lisible de la matrice : les têtes sans
        # sous-règle y sont nommées, et rien d'autre.
        for tete in ("0-EN-VRAC", "0-SAVOIRS", "0-DOCUMENTS", "0-PERSONNELS",
                     MOTEUR.MAINTENANCE):
            self.assertIn(tete, MOTEUR.MATRICE_MEMOIRE)
        self.assertNotIn("1-ARCHIVES", MOTEUR.MATRICE_MEMOIRE)


class TestLeNomDUnCarnet(unittest.TestCase):
    """Le nom d'un carnet (§6), en un seul exemplaire dans le moteur.

    La tranche qui écrit s'en sert pour nommer, la vérification du coffre pour
    reconnaître. Recopier la règle d'un côté ferait diverger les deux — ces tests
    figent la règle là où elle vit.
    """

    def test_le_nom_suit_la_date_le_dossier_puis_le_sujet(self):
        self.assertEqual(
            MOTEUR.nom_de_carnet("2026-10-09", "mcp-outils-du-coffre", "ouverture"),
            "2026-10-09-mcp-outils-du-coffre-ouverture.md")

    def test_le_sujet_se_replie_en_tige_mais_le_dossier_reste_tel_quel(self):
        # Le sujet est un nom de coffre : il se replie. Le dossier, lui, est le
        # nom **réel** du dossier — la vérification compare à ce qui est sur le
        # disque, pas à une tige devinée.
        self.assertEqual(
            MOTEUR.nom_de_carnet("2026-10-09", "Préférences", "Créée à l'écran"),
            "2026-10-09-Préférences-creee-a-l-ecran.md")

    def test_la_tige_du_nom_est_la_meme_cle_que_la_comparaison(self):
        # Une seule façon de replier un nom : le nommage du carnet et la clé
        # d'identité des notes passent par la même tige.
        self.assertEqual(MOTEUR.tige_de_nom("Créée à l'écran"), "creee-a-l-ecran")
        self.assertEqual(MOTEUR.nom_comparable("Créée — vision.md"),
                         "creee-vision")

    def test_la_forme_et_le_dossier_se_verifient(self):
        nom = "2026-10-09-mcp-outils-du-coffre-ouverture.md"
        self.assertTrue(MOTEUR.carnet_a_la_forme(nom))
        self.assertTrue(MOTEUR.carnet_du_dossier(nom, "mcp-outils-du-coffre"))
        self.assertFalse(MOTEUR.carnet_du_dossier(nom, "obsia"))
        # Une note ordinaire n'a pas la forme d'un carnet : les carnets sont les
        # seules notes datées (§6).
        self.assertFalse(MOTEUR.carnet_a_la_forme("ouverture.md"))
        self.assertFalse(MOTEUR.carnet_du_dossier("ouverture.md",
                                                  "mcp-outils-du-coffre"))

    def test_le_dossier_se_compare_tel_quel(self):
        # `Homelab` et `homelab` sont deux dossiers : rangé dans l'un, le carnet
        # ne vaut pas pour l'autre.
        self.assertFalse(MOTEUR.carnet_du_dossier("2026-10-09-Homelab-x.md",
                                                  "homelab"))

    def test_les_statuts_du_carnet_sont_ceux_du_contrat(self):
        self.assertEqual(MOTEUR.STATUTS_CARNET, ("en cours", "en attente", "clos"))
        self.assertEqual(MOTEUR.STATUT_EN_COURS, "en cours")


class TestLeNomDUnApercu(unittest.TestCase):
    """Le nom de l'aperçu du jour (§7.4) : deux notes ne se le disputent pas.

    Le dossier d'origine entre dans le nom — sans lui, deux notes homonymes de
    deux dossiers le disputeraient. Encore faut-il que la jointure du dossier et
    du nom ne se relise pas de deux façons.
    """

    def test_deux_chemins_ressemblants_donnent_deux_apercus(self):
        # `0-SAVOIRS/reseau-note.md` — dossier `0-SAVOIRS`, puis un nom qui porte un
        # tiret — et `0-SAVOIRS/Réseau/note.md` — dossier plus profond, puis un nom
        # nu. Joints par un simple tiret, les deux replis tombaient sur la même
        # suite : `2026-10-09-apercu-0-savoirs-reseau-note.md`.
        premier = MOTEUR.nom_de_l_apercu("2026-10-09", "reseau-note.md", "0-SAVOIRS")
        second = MOTEUR.nom_de_l_apercu("2026-10-09", "note.md", "0-SAVOIRS/Réseau")
        self.assertNotEqual(premier, second)
        self.assertEqual("2026-10-09-apercu-0-savoirs--reseau-note.md", premier)
        self.assertEqual("2026-10-09-apercu-0-savoirs-reseau--note.md", second)

    def test_le_separateur_ne_peut_pas_venir_d_une_tige(self):
        # C'est ce qui rend la relecture sûre : une tige ramène toute suite de
        # ponctuation à un seul `-`, donc n'en porte jamais deux de suite.
        self.assertEqual("reseau", MOTEUR.tige_de_nom("Réseau"))
        self.assertNotIn("--", MOTEUR.tige_de_nom("a--b  c"))
        self.assertNotIn("--", MOTEUR.tige_de_nom("2026-10-09 — Réseau"))

    def test_deux_carnets_ne_different_que_par_leur_date_ont_deux_apercus(self):
        # La branche carnet retirait la date que le nom du carnet porte déjà : deux
        # bilans du même sujet, ouverts à deux dates, partageaient alors l'aperçu du
        # jour (`2026-10-09-apercu-obsia-bilan.md`). Le nom entier les sépare.
        veille = MOTEUR.nom_de_l_apercu(
            "2026-10-09", "2026-10-08-obsia-bilan.md", "0-PROJETS/obsia/carnets")
        jour = MOTEUR.nom_de_l_apercu(
            "2026-10-09", "2026-10-09-obsia-bilan.md", "0-PROJETS/obsia/carnets")
        self.assertNotEqual(veille, jour)
        self.assertEqual("2026-10-09-apercu-2026-10-08-obsia-bilan.md", veille)
        self.assertEqual("2026-10-09-apercu-2026-10-09-obsia-bilan.md", jour)


class TestLAuteurDUneNote(unittest.TestCase):
    """Le champ `auteur:` d'une note — celui qui la désigne, ou personne.

    La note de référence d'un agent ne se tient sur place que si `auteur:` le
    désigne (§7.3) : un champ qui se contredit ne désigne personne.
    """

    def test_un_auteur_repete_ne_designe_personne(self):
        # Le frontmatter n'est pas un dictionnaire : deux lignes `auteur:`, et la
        # dernière l'emporte. `batisseur` s'y trouverait, mais à la faveur d'une
        # ligne qui écrase celle d'`assistant` — le champ se contredit, on ne lit
        # personne.
        deux = "---\nkind: note\nauteur: assistant\nauteur: batisseur\n---\n\n# Là\n"
        self.assertEqual("", MOTEUR.auteur_de_la_note(deux))

    def test_un_seul_auteur_est_lu(self):
        une = "---\nkind: note\nauteur: batisseur\n---\n\n# Là\n"
        self.assertEqual("batisseur", MOTEUR.auteur_de_la_note(une))
        self.assertEqual("", MOTEUR.auteur_de_la_note("---\nkind: note\n---\n\n# Là\n"))


if __name__ == "__main__":
    unittest.main()
