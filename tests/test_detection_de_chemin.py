"""Le motif qui reconnaît un chemin absolu de machine.

Il sert deux fois : les tests vérifient qu'aucun chemin absolu n'entre dans le
texte engendré, et `verifier_coffre.py` contrôle le prompt réel du catalogue. Un
motif trop étroit laisserait passer un chemin ; trop large, il accuserait une
adresse ou un chemin relatif, et l'alerte serait ignorée à force de crier à tort.
Les deux bords sont donc sondés ici.

  - reconnu : racine POSIX (`/srv`, seule ou suivie), relatif au foyer (`~/…`),
    lecteur Windows (`C:\\…`, `C:/…`), premier segment à espaces ;
  - permis : adresse (`https://…`), chemin relatif du coffre (`IA/skills/`),
    dossier nommé sans racine (`OBSIA/`), barre de prose (« et/ou », « 1/2 »).

Le motif vit dans `scripts/generer_prompt.py`, pas ici : c'est lui qui engendre
le texte, et deux copies finiraient par ne plus dire la même chose.
"""

import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True          # ne pas semer de __pycache__ dans le dépôt
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from generer_prompt import CHEMIN_ABSOLU, chemins_absolus    # noqa: E402


class TestLeMotifReconnait(unittest.TestCase):
    def test_une_racine_posix_seule(self):
        for texte in ("/srv", "voir /etc", "racine : /home"):
            self.assertTrue(CHEMIN_ABSOLU.search(texte), texte)

    def test_un_chemin_posix_complet(self):
        for texte in ("/home/moi/coffre/OBSIA", "/home/moi/coffre"):
            self.assertTrue(CHEMIN_ABSOLU.search(texte), texte)

    def test_un_premier_segment_a_espaces(self):
        self.assertTrue(CHEMIN_ABSOLU.search("/home/moi/Mon coffre/OBSIA"))
        self.assertTrue(CHEMIN_ABSOLU.search("Mon coffre vit dans /Mon coffre"))

    def test_un_chemin_relatif_au_foyer(self):
        self.assertTrue(CHEMIN_ABSOLU.search("cd ~/coffre"))
        self.assertTrue(CHEMIN_ABSOLU.search("~/Mon coffre/AGENTS.md"))

    def test_un_lecteur_windows(self):
        for texte in (r"voir C:\coffre", "voir C:/coffre"):
            self.assertTrue(CHEMIN_ABSOLU.search(texte), texte)


class TestLeMotifLaissePasser(unittest.TestCase):
    """Sans ces gardes, le contrôle crierait sur du texte honnête — celui du
    prompt engendré, par exemple — et finirait par être ignoré."""

    def test_une_adresse(self):
        for texte in ("https://exemple.fr/x", "http://exemple.fr",
                      "voir https://exemple.fr/a/b"):
            self.assertIsNone(CHEMIN_ABSOLU.search(texte), texte)

    def test_un_chemin_relatif_du_coffre(self):
        for texte in ("IA/skills/", "0-SAVOIRS/", "`IA/system/VAULT-CONTRACT.md`",
                      "0-PROJETS/<projet>/code/"):
            self.assertIsNone(CHEMIN_ABSOLU.search(texte), texte)

    def test_le_repere_du_sous_dossier(self):
        self.assertIsNone(CHEMIN_ABSOLU.search("son sous-dossier OBSIA/"))
        self.assertIsNone(CHEMIN_ABSOLU.search(
            "Coffre (la mémoire) : le dossier qui contient le sous-dossier "
            "OBSIA/ — celui de l'AGENTS.md d'OBSIA."))

    def test_une_barre_de_prose(self):
        for texte in ("et/ou", "1/2", "mot/clef", "sécurité/qualité", " / "):
            self.assertIsNone(CHEMIN_ABSOLU.search(texte), texte)


class TestCheminsAbsolus(unittest.TestCase):
    def test_rend_les_lignes_fautives_dans_l_ordre(self):
        texte = "Une ligne honnête.\n/home/moi/coffre\nEt ~/coffre aussi.\n"

        self.assertEqual(["/home/moi/coffre", "Et ~/coffre aussi."],
                         chemins_absolus(texte))

    def test_un_texte_propre_ne_rend_rien(self):
        self.assertEqual([],
                         chemins_absolus("IA/skills/\nhttps://exemple.fr/\n"))
