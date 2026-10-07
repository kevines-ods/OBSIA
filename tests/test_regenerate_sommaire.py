"""Le générateur de sommaires lit une note sans prendre son frontmatter pour du texte."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True          # ne pas semer de __pycache__ dans le dépôt
SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))        # `scripts/` n'est pas un paquet
CONVENTION = (Path(__file__).resolve().parent.parent
              / "IA" / "skills" / "traitement-des-notes" / "scripts")
sys.path.insert(0, str(CONVENTION))     # ni le dossier d'un skill

import regenerate_sommaire as RS                    # noqa: E402
import appliquer_convention_parent as AC            # noqa: E402


class TestFrontmatter(unittest.TestCase):
    def lire(self, texte):
        with tempfile.TemporaryDirectory() as d:
            chemin = Path(d) / "2026-10-02-projet-sujet.md"
            chemin.write_text(texte, encoding="utf-8")
            return RS.lire_note(str(chemin))

    def test_le_frontmatter_n_entre_pas_dans_le_resume(self):
        note = self.lire("---\nagent: assistant\nprojet: projet\nstatut: clos\n---\n\n"
                         "# Titre\n\nLe vrai chapeau de la note, en prose.\n")
        self.assertNotIn("agent:", note["resume"])
        self.assertIn("vrai chapeau", note["resume"])

    def test_le_statut_du_frontmatter_fait_foi(self):
        note = self.lire("---\nagent: assistant\nprojet: projet\nstatut: clos\n---\n\n"
                         "# Titre\n\n## Statut\n🟡 En attente — piste ouverte.\n")
        self.assertEqual(note["statut"], "clos")

    def test_sans_frontmatter_le_statut_du_corps_reste_lu(self):
        note = self.lire("# Titre\n\nChapeau.\n\n## Statut\n🟢 Livré et fusionné.\n")
        self.assertIn("Livré", note["statut"])


class TestZonesDEcriture(unittest.TestCase):
    """Où les sommaires se sèment — et surtout où ils ne se sèment pas (§2)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.racine = base / "OBSIA"
        self.coffre = base
        self.racine.mkdir()
        self._avant = (RS.RACINE, RS.COFFRE, RS.ANCIENNE_MEMOIRE)
        self.addCleanup(self._restaurer)
        RS.RACINE = str(self.racine)
        RS.COFFRE = str(self.coffre)
        RS.ANCIENNE_MEMOIRE = str(self.racine / "mémoire")

    def _restaurer(self):
        RS.RACINE, RS.COFFRE, RS.ANCIENNE_MEMOIRE = self._avant

    def dossier(self, relatif):
        chemin = self.coffre / relatif
        chemin.mkdir(parents=True, exist_ok=True)
        return chemin

    def test_les_projets_et_les_chantiers_geles_portent_des_sommaires(self):
        self.dossier("0-PROJETS")
        self.dossier("0-MEMOIRES")
        self.assertEqual([str(self.coffre / "0-MEMOIRES"), str(self.coffre / "0-PROJETS")],
                         RS.racines_de_memoire())

    def test_les_autres_zones_n_en_portent_pas(self):
        for nom in ("0-SAVOIRS", "0-DOCUMENTS", "0-PERSONNELS", "0-EN-VRAC",
                    "-PROJETS", "-SAVOIRS", "-EN-VRAC", "0-MAINTENANCE"):
            self.dossier(nom)
        self.assertEqual([], RS.racines_de_memoire())

    def test_l_ancienne_memoire_du_produit_est_encore_servie(self):
        """Tant que la bascule dure, ses sommaires existent là (§11)."""
        (self.racine / "mémoire" / "projets").mkdir(parents=True)
        self.assertEqual([str(self.racine / "mémoire")], RS.racines_de_memoire())

    def test_sans_coffre_ni_ancienne_memoire_il_n_y_a_rien_a_resumer(self):
        self.assertEqual([], RS.racines_de_memoire())

    def test_l_ancienne_memoire_du_coffre_parent_n_est_pas_servie(self):
        """`-PROJETS` n'a jamais porté de sommaire : la bascule n'en sème pas."""
        self.dossier("-PROJETS/obsia/allegement")
        self.assertEqual([], RS.racines_de_memoire())

    def test_le_code_d_un_projet_ne_recoit_pas_de_sommaire(self):
        """Le `code/` d'un projet est un dépôt Git distinct (§7.3) : hors mémoire."""
        projet = self.dossier("0-PROJETS/monprojet")
        (projet / "2026-10-01-monprojet-note.md").write_text(
            "# Note\n\nLe chapeau du projet.\n", encoding="utf-8")
        code = projet / "code"
        (code / ".git").mkdir(parents=True)
        (code / "README.md").write_text("# Code\n\nUn dépôt.\n", encoding="utf-8")

        RS.main()

        sommaire = (projet / "sommaire.md").read_text(encoding="utf-8")
        self.assertNotIn("code/", sommaire)          # ni sommaire, ni mention
        self.assertFalse((code / "sommaire.md").exists())

    def test_un_depot_git_imbrique_ne_recoit_pas_de_sommaire(self):
        """Tout dossier portant un `.git` (dossier ou fichier) est hors mémoire."""
        gel = self.dossier("0-MEMOIRES/assistant")
        (gel / "2026-10-01-assistant-note.md").write_text(
            "# Note\n\nLe chapeau du chantier.\n", encoding="utf-8")
        imbrique = gel / "outil"
        (imbrique / ".git").mkdir(parents=True)
        (imbrique / "note.md").write_text("# Note\n\nDans le dépôt.\n", encoding="utf-8")
        fichier = gel / "sous-module"                # `.git` en fichier : worktree
        fichier.mkdir()
        (fichier / ".git").write_text("gitdir: ailleurs\n", encoding="utf-8")
        (fichier / "note.md").write_text("# Note\n\nAussi dans un dépôt.\n", encoding="utf-8")

        RS.main()

        self.assertTrue((gel / "sommaire.md").is_file())
        self.assertFalse((imbrique / "sommaire.md").exists())
        self.assertFalse((fichier / "sommaire.md").exists())

    def test_la_racine_du_parcours_n_est_jamais_filtree(self):
        """Une racine de mémoire est résumée même si elle porte un `.git`.

        La règle du dépôt imbriqué s'arrête aux dossiers **rencontrés sous** une
        racine : on résume toujours le dossier par lequel on entre — sans quoi
        le coffre, qui est lui-même un dépôt, n'aurait aucun sommaire.
        """
        memoire = self.dossier("0-MEMOIRES")
        (memoire / ".git").write_text("gitdir: ailleurs\n", encoding="utf-8")
        (memoire / "2026-10-02-agent-note.md").write_text(
            "# Note\n\nLe chapeau de la note.\n", encoding="utf-8")

        RS.main()

        self.assertTrue((memoire / "sommaire.md").is_file())


class TestExclusionsPartagees(unittest.TestCase):
    """Les deux marcheurs écartent la même chose, sans module partagé.

    `appliquer_convention_parent.py` (skill `traitement-des-notes`) et
    `regenerate_sommaire.py` appliquent la même règle : ne jamais écrire dans un
    dossier technique, ni dans un autre dépôt. Tant qu'ils ne partagent pas de
    module, ce test empêche les deux de diverger en silence.
    """

    def test_la_meme_liste_de_dossiers_hors_memoire(self):
        self.assertEqual(set(AC.DOSSIERS_HORS_MEMOIRE),
                         set(RS.DOSSIERS_HORS_MEMOIRE))

    def test_les_deux_reconnaissent_un_depot_imbrique(self):
        """Le marqueur `.git` compte en dossier (dépôt) comme en fichier."""
        for forme in ("dossier", "fichier"):
            with tempfile.TemporaryDirectory() as d:
                racine = Path(d)
                marque = racine / ".git"
                if forme == "dossier":
                    marque.mkdir()
                else:
                    marque.write_text("gitdir: ailleurs\n", encoding="utf-8")
                self.assertTrue(AC.est_depot_imbrique(racine), forme)
                self.assertTrue(RS.est_depot_imbrique(racine), forme)



if __name__ == "__main__":
    unittest.main()
