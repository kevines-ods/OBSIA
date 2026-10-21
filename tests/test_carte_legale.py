# -*- coding: utf-8 -*-
"""`serveur/carte_legale.py` : la carte des destinations, pas celle de ce qu'on
peut lire (P2).

La carte est en **lecture seule** : elle montre les destinations ouvertes à
l'écriture et ce qui s'y trouve déjà, et rien d'autre. Elle ne dit jamais ce que
le modèle a le droit de lire — la lecture du coffre reste ouverte (§7.2). Elle ne
montre jamais une zone qu'on ne lui a pas donnée, elle écarte une zone absolue,
un dépôt imbriqué ou un chantier gelé, et elle ne crée, ne modifie ni ne supprime
rien — le test le vérifie par une photo du dossier témoin avant et après.

Elle rend les **zones données par l'appelant, moins les exclusions
structurelles**, et elle n'ouvre que ce que la **matrice du §7.3** nomme pour
l'**auteur** déclaré. Cet auteur est obligatoire : sans lui la carte n'ouvre
rien — l'ignorance ferme, elle n'ouvre pas. La matrice vit dans le moteur
partagé, un seul exemplaire (`docs/PLAN.md`).
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

import serveur.carte_legale as CARTE                  # noqa: E402
import convention_des_notes as CONVENTION             # noqa: E402

#: L'auteur des tests : un agent du contrat, assez nommé pour juger le §7.3.
AUTEUR = "assistant"


def _coffre(tmp):
    """Un coffre témoin : trois zones du contrat, plus une qu'on ne donnera pas."""
    coffre = Path(tmp)
    for zone in ("0-EN-VRAC", "0-SAVOIRS", "_MAINTENANCE", "0-DOCUMENTS"):
        (coffre / zone).mkdir()
    (coffre / "0-SAVOIRS" / "docker.md").write_text("note", encoding="utf-8")
    (coffre / "0-SAVOIRS" / "réseau.md").write_text("note", encoding="utf-8")
    (coffre / "0-SAVOIRS" / "sommaire.md").write_text("index", encoding="utf-8")
    (coffre / "0-DOCUMENTS" / "prive.md").write_text("note", encoding="utf-8")
    (coffre / "0-EN-VRAC" / "brouillon.md").write_text("note", encoding="utf-8")
    return coffre


class TestCarteLegale(unittest.TestCase):
    def test_ne_montre_que_les_zones_autorisees(self):
        with tempfile.TemporaryDirectory() as tmp:
            coffre = _coffre(tmp)
            carte = CARTE.carte_legale(coffre, ("0-SAVOIRS", "0-EN-VRAC"),
                                       auteur=AUTEUR)
            self.assertEqual(set(carte), {"0-SAVOIRS", "0-EN-VRAC"})
            self.assertNotIn("0-DOCUMENTS", carte)

    def test_une_zone_hors_matrice_est_ecartee(self):
        with tempfile.TemporaryDirectory() as tmp:
            coffre = _coffre(tmp)
            # Une zone que le §7.3 ne nomme pas est écartée, même fournie.
            self.assertEqual(
                CARTE.carte_legale(coffre, ("zone-témoin",), auteur=AUTEUR),
                {})

    def test_sans_auteur_la_carte_n_ouvre_rien(self):
        # L'auteur est obligatoire : sans lui, pas de §7.3 à lire — et la carte
        # ne rend pas la liste de l'appelant comme si tout était ouvert.
        with tempfile.TemporaryDirectory() as tmp:
            coffre = _coffre(tmp)
            self.assertEqual(
                CARTE.carte_legale(coffre, ("0-SAVOIRS", "0-EN-VRAC")), {})

    def test_la_maintenance_est_une_destination(self):
        # Previews, actions, registre `notes_remplies.md` : le §7.3 ouvre
        # `_MAINTENANCE/`, et le §7.4 l'impose.
        with tempfile.TemporaryDirectory() as tmp:
            coffre = _coffre(tmp)
            carte = CARTE.carte_legale(coffre, ("_MAINTENANCE",), auteur=AUTEUR)
            self.assertEqual(set(carte), {"_MAINTENANCE"})

    def test_la_carte_n_ouvre_a_l_auteur_que_les_zones_du_contrat(self):
        with tempfile.TemporaryDirectory() as tmp:
            coffre = _coffre(tmp)
            carte = CARTE.carte_legale(coffre, ("0-SAVOIRS", "zone-témoin"),
                                       auteur=AUTEUR)
            self.assertEqual(set(carte), {"0-SAVOIRS"})
            self.assertEqual(carte["0-SAVOIRS"], ("docker.md", "réseau.md"))

    def test_la_carte_juge_l_auteur_de_la_zone(self):
        # `0-MEMOIRES/<agent>/expériences/` n'appartient qu'à l'agent nommé.
        with tempfile.TemporaryDirectory() as tmp:
            coffre = _coffre(tmp)
            zone = "%s/%s/%s" % (CONVENTION.MEMOIRES, "batisseur",
                                 CONVENTION.EXPERIENCES)
            (coffre / zone).mkdir(parents=True)
            self.assertEqual(
                set(CARTE.carte_legale(coffre, (zone,), auteur="batisseur")), {zone})
            self.assertEqual(
                CARTE.carte_legale(coffre, (zone,), auteur="assistant"), {})

    def test_le_contenu_existant_est_liste_par_zone(self):
        with tempfile.TemporaryDirectory() as tmp:
            coffre = _coffre(tmp)
            carte = CARTE.carte_legale(coffre, ("0-SAVOIRS", "0-EN-VRAC"),
                                       auteur=AUTEUR)
            self.assertEqual(carte["0-SAVOIRS"], ("docker.md", "réseau.md"))
            self.assertEqual(carte["0-EN-VRAC"], ("brouillon.md",))

    def test_un_fichier_de_dossier_n_est_pas_une_note(self):
        with tempfile.TemporaryDirectory() as tmp:
            coffre = _coffre(tmp)
            carte = CARTE.carte_legale(coffre, ("0-SAVOIRS",), auteur=AUTEUR)
            self.assertNotIn("sommaire.md", carte["0-SAVOIRS"])

    def test_une_note_en_sous_dossier_garde_son_chemin_relatif(self):
        # Un chemin **relatif à la zone**, pas un simple nom : le refus « nom
        # unique » ne doit porter que sur le même dossier de destination, pas sur
        # un homonyme rangé plus bas.
        with tempfile.TemporaryDirectory() as tmp:
            coffre = _coffre(tmp)
            (coffre / "0-SAVOIRS" / "sous").mkdir()
            (coffre / "0-SAVOIRS" / "sous" / "docker.md").write_text(
                "note", encoding="utf-8")
            carte = CARTE.carte_legale(coffre, ("0-SAVOIRS",), auteur=AUTEUR)
            self.assertEqual(carte["0-SAVOIRS"],
                             ("docker.md", "réseau.md", "sous/docker.md"))

    def test_une_zone_absente_est_vide_pas_absente(self):
        with tempfile.TemporaryDirectory() as tmp:
            coffre = _coffre(tmp)
            carte = CARTE.carte_legale(coffre, ("0-SAVOIRS/sous",), auteur=AUTEUR)
            self.assertEqual(carte["0-SAVOIRS/sous"], ())

    def test_une_zone_sous_un_depot_imbrique_est_ecartee(self):
        with tempfile.TemporaryDirectory() as tmp:
            coffre = _coffre(tmp)
            (coffre / "0-PROJETS" / "p" / "code").mkdir(parents=True)
            carte = CARTE.carte_legale(
                coffre, ("0-PROJETS/p/code", "0-SAVOIRS"), auteur=AUTEUR)
            self.assertNotIn("0-PROJETS/p/code", carte)
            self.assertIn("0-SAVOIRS", carte)

    def test_une_zone_sous_un_dossier_cache_est_ecartee(self):
        with tempfile.TemporaryDirectory() as tmp:
            coffre = _coffre(tmp)
            (coffre / ".journal").mkdir()
            carte = CARTE.carte_legale(coffre, (".journal", "0-SAVOIRS"),
                                       auteur=AUTEUR)
            self.assertNotIn(".journal", carte)

    def test_une_zone_absolue_ne_sort_pas_du_coffre(self):
        # Une zone est relative au coffre (§13) : `/etc` doit être refusé, sinon
        # la carte sortirait du coffre au lieu d'y choisir une destination.
        with tempfile.TemporaryDirectory() as tmp:
            coffre = _coffre(tmp)
            self.assertFalse(CARTE.zone_legale(coffre, "/etc", auteur=AUTEUR))
            self.assertFalse(
                CARTE.zone_legale(coffre, str(coffre / "0-SAVOIRS"),
                                  auteur=AUTEUR))
            self.assertEqual(CARTE.contenu_existant(coffre, "/etc"), ())

    def test_une_zone_dans_un_chantier_gele_est_ecartee(self):
        # Un chantier clos de la mémoire ne se rouvre pas (§6) : la carte ne le
        # propose pas, et la matrice le refuse avant même le gel.
        with tempfile.TemporaryDirectory() as tmp:
            coffre = _coffre(tmp)
            gele = "%s/%s/%s" % (CONVENTION.MEMOIRES, "obsia", "chantier-clos")
            (coffre / gele).mkdir(parents=True)
            carte = CARTE.carte_legale(coffre, (gele, "0-SAVOIRS"), auteur=AUTEUR)
            self.assertNotIn(gele, carte)
            self.assertIn("0-SAVOIRS", carte)

    def test_les_experiences_d_un_agent_non_declare_sont_ecartees(self):
        # Le §6 seul le dit : `expériences/` n'est vivant que si le dossier porte
        # le nom d'un agent déclaré. Ici `inconnu` n'en est pas un — c'est un
        # chantier, donc fermé.
        with tempfile.TemporaryDirectory() as tmp:
            coffre = _coffre(tmp)
            zone = "%s/%s/%s" % (CONVENTION.MEMOIRES, "inconnu",
                                 CONVENTION.EXPERIENCES)
            (coffre / zone).mkdir(parents=True)
            self.assertNotIn(
                zone, CARTE.carte_legale(coffre, (zone,), auteur=AUTEUR))

    def test_la_memoire_vivante_reste_une_destination(self):
        # `0-MEMOIRES/préférences/` est la mémoire vivante : elle s'écrit (§6).
        with tempfile.TemporaryDirectory() as tmp:
            coffre = _coffre(tmp)
            vivante = "%s/%s" % (CONVENTION.MEMOIRES, CONVENTION.PREFERENCES)
            (coffre / vivante).mkdir(parents=True)
            self.assertTrue(CARTE.zone_legale(coffre, vivante, auteur=AUTEUR))

    def test_la_memoire_d_un_agent_declare_reste_une_destination(self):
        # `0-MEMOIRES/<agent>/expériences/` est vivant **parce que** `<agent>` est
        # un agent : c'est la même liste des deux formes qui le dit (§6).
        with tempfile.TemporaryDirectory() as tmp:
            coffre = _coffre(tmp)
            agent = sorted(CONVENTION.liste_des_agents(CARTE.RACINE_PRODUIT))[0]
            vivante = "%s/%s/%s" % (CONVENTION.MEMOIRES, agent,
                                    CONVENTION.EXPERIENCES)
            (coffre / vivante).mkdir(parents=True)
            self.assertTrue(CARTE.zone_legale(coffre, vivante, auteur=agent))

    def test_lire_ne_modifie_rien(self):
        with tempfile.TemporaryDirectory() as tmp:
            coffre = _coffre(tmp)
            avant = sorted(str(p) for p in coffre.rglob("*"))
            CARTE.carte_legale(coffre, ("0-SAVOIRS", "0-EN-VRAC"), auteur=AUTEUR)
            self.assertEqual(sorted(str(p) for p in coffre.rglob("*")), avant)


if __name__ == "__main__":
    unittest.main()
