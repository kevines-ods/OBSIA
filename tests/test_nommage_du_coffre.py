#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deux règles de nommage, deux usages — et le pont qui rend l'écart sans danger.

Le coffre replie un mot en nom de fichier de deux façons, et c'est **assumé**,
pas subi :

- `serveur.porte_entree.nom_de_note` **fabrique** le nom d'une note. Il garde les
  accents : le coffre nomme ses notes en français lisible (« Idées — résumé.md »,
  « Séance d'équipe — … »), et le nom qu'un humain ou un modèle fournit ne se
  défigure pas tout seul ;
- `scripts.convention_des_notes.tige_de_nom` **calcule** la clé d'identité. Elle
  replie accents, casse et séparateurs, pour décider si une note existe déjà.

Réunir les deux coûterait cher dans les deux sens : garder les accents dans la
clé rouvrirait les doublons (« creee » et « créée » cesseraient d'être la même
note) ; replier les accents dans le nom contredirait le coffre tel qu'il est et
changerait un test écrit exprès (`test_porte_entree.py`).

Ce qui rend l'écart inoffensif, c'est **le pont** : la clé de ce que la porte
écrit est la clé du sujet qu'on lui a donné —

    nom_comparable(nom_de_note(sujet)) == tige_de_nom(sujet)

La comparaison reste donc plus stricte que la fabrication : l'unicité ne se
troue pas. C'est ce pont que ces tests tiennent ; sans lui, les deux règles
dériveraient en silence.
"""

import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))
sys.path.insert(0, str(RACINE / "scripts"))

import serveur.porte_entree as PORTE                       # noqa: E402
import convention_des_notes as MOTEUR                      # noqa: E402

#: Des sujets que le coffre peut porter : français, tirets, ponctuation, et les
#: caractères de compatibilité que le repli doit translittérer au lieu de perdre.
SUJETS = (
    "Ma note sur Docker",
    "Mémoire vive",
    "Créée à l'écran",
    "Homelab — vision",
    "Déjà-vu",
    "Noël",
    "0-EN-VRAC",
    "Points de suspension…",
    "Réseau vlan",
    "Straße",
    "½ part",
    "Ⅻ siècle",
    "２026 budget",
    "ﬁchier",
    "Rapport ﬁnal",
    "㎏ de sucre",
    "① premier",
)

#: Les caractères que la fabrication perdait avant le pont : un nom qui commence
#: par eux se faisait rogner (`"ﬁchier"` → `"chier.md"`), et la clé divergeait.
CARACTERES_DE_COMPATIBILITE = ("½ part", "Ⅻ siècle", "２026 budget",
                               "ﬁchier", "Rapport ﬁnal", "㎏ de sucre",
                               "① premier")


class TestLePontEntreLesDeuxRegles(unittest.TestCase):

    def _la_cle_de_ce_que_la_porte_ecrit(self, sujet):
        nom = PORTE.nom_de_note(sujet)
        if nom is None:                 # un sujet sans lettre : rien à écrire
            return ""
        return MOTEUR.nom_comparable(nom)

    def test_la_cle_du_nom_fabrique_est_la_cle_du_sujet(self):
        for sujet in SUJETS:
            with self.subTest(sujet=sujet):
                self.assertEqual(self._la_cle_de_ce_que_la_porte_ecrit(sujet),
                                 MOTEUR.tige_de_nom(sujet),
                                 "le pont entre les deux règles a cédé")

    def test_aucun_caractere_ne_se_perd_en_chemin(self):
        # Le cas qui a fait mal : `"ﬁchier"` donnait `"chier.md"`, la ligature
        # avalée par le rognage. Un nom ne perd pas une lettre en silence.
        for sujet in CARACTERES_DE_COMPATIBILITE:
            with self.subTest(sujet=sujet):
                nom = PORTE.nom_de_note(sujet)
                self.assertIsNotNone(nom)
                self.assertEqual(MOTEUR.nom_comparable(nom),
                                 MOTEUR.tige_de_nom(sujet))


class TestLesDeuxReglesRestentCeQuEllesSont(unittest.TestCase):
    """L'écart est assumé : ces tests le figent, ils ne le corrigent pas."""

    def test_la_fabrication_garde_les_accents(self):
        # Le choix, écrit noir sur blanc : un nom de note reste lisible.
        self.assertEqual(PORTE.nom_de_note("Mémoire vive"), "mémoire-vive.md")
        self.assertEqual(PORTE.nom_de_note("Créée à l'écran"),
                         "créée-à-l-écran.md")

    def test_la_cle_replie_accent_casse_et_separateurs(self):
        # La clé, elle, aplatit : c'est ce qui décide qu'une note existe déjà.
        self.assertEqual(MOTEUR.tige_de_nom("Mémoire vive"), "memoire-vive")
        self.assertEqual(MOTEUR.tige_de_nom("Créée à l'écran"), "creee-a-l-ecran")


if __name__ == "__main__":
    unittest.main()
