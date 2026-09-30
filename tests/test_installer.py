"""`installer.py --appliquer` et l'AGENTS.md qu'il pose à côté du coffre.

Les harness lisent le fichier de consignes du dépôt dans lequel ils s'ouvrent
(une fiche par harness dans `IA/system/adaptateurs-harness/`). Le coffre n'étant
pas ce dépôt, le fichier se pose chez le parent — hors dépôt, donc hors
publication, et porteur d'un marqueur qui dit à qui il appartient.

Le coffre de test n'a pas de `scripts/` : `regenerer()` s'arrête alors
proprement, et ces tests ne jugent que l'AGENTS.md.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True          # ne pas semer de __pycache__ dans le dépôt
SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import installer as INS                 # noqa: E402

GENERATEUR = SCRIPTS / "generer_prompt.py"
INSTALLATEUR = SCRIPTS / "installer.py"
MARQUEUR = "généré par OBSIA/scripts/installer.py"


class BaseInstalleur(unittest.TestCase):
    """Un coffre temporaire, et un dossier parent à lui, pour y poser AGENTS.md."""

    def setUp(self):
        self.parent = Path(tempfile.mkdtemp(prefix="obsia-test-install-"))
        self.addCleanup(shutil.rmtree, self.parent, ignore_errors=True)
        self.racine = self.parent / "OBSIA"
        self.racine.mkdir()

        self.ecrire("IA/system/modules/noyau.md",
                    "---\nschema: 1\nkind: module\nname: noyau\n"
                    "description: Le socle.\nessentiel: true\n---\n\nCorps.\n")
        self.ecrire("IA/system/modules/construction.md",
                    "---\nschema: 1\nkind: module\nname: construction\n"
                    "description: Bâtir.\nessentiel: false\n"
                    "requiert:\n  - noyau\n---\n\nCorps.\n")
        self.ecrire("IA/agents/agent-verif.md",
                    "---\nschema: 1\nkind: agent\nname: agent-verif\n"
                    "description: Un agent.\nread_only: true\n"
                    "module: construction\nskills:\n  - a-verifie\n---\n\nCorps.\n")
        self.ecrire("IA/skills/a-verifie.md",
                    "---\nschema: 1\nkind: skill\nname: a-verifie\n"
                    "description: Un skill.\nread_only: false\n"
                    "module: construction\ntype: core\n---\n\nCorps.\n")

    def ecrire(self, relatif: str, contenu: str) -> Path:
        chemin = self.racine / relatif
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(contenu, encoding="utf-8")
        return chemin

    def profil(self, modules: str = "construction",
               mode: str = "en-place") -> Path:
        return self.ecrire("obsia.local.yml",
                           "schema: 1\nmode: %s\nmodules:\n  - %s\n"
                           % (mode, modules))

    def agents_md(self, coffre: Path | None = None) -> Path:
        return (coffre or self.racine).parent / "AGENTS.md"

    def lancer(self, *arguments: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-B", str(INSTALLATEUR), "--racine", str(self.racine),
             *arguments],
            capture_output=True, text=True, check=False)

    def prompt_de_reference(self, coffre: Path | None = None) -> str:
        """La sortie de `generer_prompt.py -o` : la référence du contenu."""
        coffre = coffre or self.racine
        sortie = self.parent / "reference.txt"
        resultat = subprocess.run(
            [sys.executable, "-B", str(GENERATEUR), "--racine", str(coffre),
             "-o", str(sortie)],
            capture_output=True, text=True, check=False)
        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        return sortie.read_text(encoding="utf-8")

    def corps(self, chemin: Path) -> str:
        """L'AGENTS.md sans sa première ligne de marqueur ni la ligne vide."""
        lignes = chemin.read_text(encoding="utf-8").splitlines(keepends=True)
        return "".join(lignes[2:])


class TestEcritureAgentsMd(BaseInstalleur):
    """--appliquer écrit AGENTS.md à côté du coffre, avec le bon contenu."""

    def test_le_fichier_est_cree_a_cote_du_coffre(self):
        self.profil()

        resultat = self.lancer("--appliquer")

        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertTrue(self.agents_md().is_file())
        self.assertIn("créé", resultat.stdout)

    def test_le_fichier_n_est_pas_dans_le_coffre(self):
        """Il ne doit pas pouvoir partir à la publication (publier.py, §13.4)."""
        self.profil()

        self.lancer("--appliquer")

        self.assertFalse((self.racine / "AGENTS.md").exists())

    def test_le_marqueur_ouvre_le_fichier(self):
        self.profil()

        self.lancer("--appliquer")

        premiere = self.agents_md().read_text(encoding="utf-8").splitlines()[0]
        self.assertIn(MARQUEUR, premiere)
        self.assertIn("ne pas éditer", premiere)
        self.assertIn("installer.py --appliquer", premiere)

    def test_le_corps_est_le_prompt_du_coffre(self):
        self.profil()

        self.lancer("--appliquer")

        self.assertEqual(self.corps(self.agents_md()),
                         self.prompt_de_reference())

    def test_le_contenu_suit_le_profil(self):
        """Même réduction que le prompt système : les modules écartés sortent."""
        self.ecrire("IA/agents/agent-hors-profil.md",
                    "---\nschema: 1\nkind: agent\nname: agent-hors-profil\n"
                    "description: Ailleurs.\nread_only: true\n"
                    "module: ailleurs\n---\n\nCorps.\n")
        self.profil(modules="construction")

        self.lancer("--appliquer")

        texte = self.agents_md().read_text(encoding="utf-8")
        self.assertIn("agent-verif", texte)
        self.assertNotIn("agent-hors-profil", texte)

    def test_le_fichier_se_termine_par_un_saut_de_ligne(self):
        self.profil()

        self.lancer("--appliquer")

        self.assertTrue(self.agents_md().read_text(encoding="utf-8").endswith("\n"))


class TestApercuSansAppliquer(BaseInstalleur):
    """Sans --appliquer, l'aperçu annonce AGENTS.md et n'écrit rien."""

    def test_l_apercu_annonce_la_creation(self):
        self.profil()

        resultat = self.lancer()

        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertIn("AGENTS.md", resultat.stdout)
        self.assertIn("créé", resultat.stdout)
        self.assertFalse(self.agents_md().exists())

    def test_l_apercu_annonce_la_regeneration(self):
        self.profil()
        self.agents_md().write_text(
            "%s\n\nvieux prompt\n" % INS.MARQUEUR_AGENTS, encoding="utf-8")

        resultat = self.lancer()

        self.assertIn("régénéré", resultat.stdout)
        self.assertEqual(self.agents_md().read_text(encoding="utf-8"),
                         "%s\n\nvieux prompt\n" % INS.MARQUEUR_AGENTS)

    def test_l_apercu_annonce_qu_il_sera_saute(self):
        self.profil()
        self.agents_md().write_text("écrit à la main\n", encoding="utf-8")

        resultat = self.lancer()

        self.assertIn("sauté", resultat.stdout)
        self.assertEqual(self.agents_md().read_text(encoding="utf-8"),
                         "écrit à la main\n")

    def test_l_apercu_annonce_le_chemin(self):
        self.profil()

        resultat = self.lancer()

        self.assertIn(str(self.agents_md()), resultat.stdout)


class TestFichierEtranger(BaseInstalleur):
    """Un AGENTS.md sans le marqueur n'est jamais écrasé."""

    def test_un_fichier_sans_marqueur_est_laisse_intact(self):
        self.profil()
        self.agents_md().write_text("# Mes consignes à moi\n", encoding="utf-8")

        resultat = self.lancer("--appliquer")

        self.assertEqual(self.agents_md().read_text(encoding="utf-8"),
                         "# Mes consignes à moi\n")
        self.assertIn("AGENTS.md", resultat.stderr)
        self.assertIn("marqueur", resultat.stderr)

    def test_le_code_de_retour_n_est_pas_change_par_le_saut(self):
        """Sauter ce fichier n'est pas une erreur du coffre."""
        self.profil()
        self.agents_md().write_text("à moi\n", encoding="utf-8")

        resultat = self.lancer("--appliquer")

        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertIn("Installation terminée", resultat.stdout)

    def test_un_fichier_avec_marqueur_est_regenere(self):
        self.profil()
        self.agents_md().write_text(
            "%s\n\nvieux prompt\n" % INS.MARQUEUR_AGENTS, encoding="utf-8")

        resultat = self.lancer("--appliquer")

        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertEqual(self.corps(self.agents_md()),
                         self.prompt_de_reference())
        self.assertNotIn("vieux prompt", self.agents_md().read_text(encoding="utf-8"))

    def test_un_marqueur_apres_une_ligne_vide_suffit(self):
        """Le marqueur reste reconnaissable même précédé de blancs."""
        self.profil()
        self.agents_md().write_text(
            "\n%s\n\nvieux prompt\n" % INS.MARQUEUR_AGENTS, encoding="utf-8")

        self.lancer("--appliquer")

        self.assertEqual(self.corps(self.agents_md()),
                         self.prompt_de_reference())


class TestRegenerationIdempotente(BaseInstalleur):
    def test_deux_installations_donnent_le_meme_fichier(self):
        self.profil()

        self.lancer("--appliquer")
        premier = self.agents_md().read_bytes()
        resultat = self.lancer("--appliquer")

        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertEqual(self.agents_md().read_bytes(), premier)


class TestModeCopie(BaseInstalleur):
    """En copie, AGENTS.md va chez le coffre copié, pas chez la source.

    La cible est placée dans son propre dossier : ailleurs, les deux coffres
    partageraient le même parent et le test ne prouverait rien.
    """

    def cible(self) -> Path:
        return self.parent / "chez-moi" / "OBSIA"

    def test_le_fichier_va_chez_la_copie(self):
        self.profil(mode="copie")

        resultat = self.lancer("--appliquer", "--installer", str(self.cible()))

        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertTrue(self.agents_md(self.cible()).is_file())
        self.assertFalse(self.agents_md(self.racine).exists())

    def test_le_contenu_est_celui_de_la_copie(self):
        self.profil(mode="copie")

        self.lancer("--appliquer", "--installer", str(self.cible()))

        self.assertEqual(self.corps(self.agents_md(self.cible())),
                         self.prompt_de_reference(self.cible()))

    def test_l_apercu_annonce_la_cible_du_fichier(self):
        self.profil(mode="copie")

        resultat = self.lancer("--installer", str(self.cible()))

        self.assertIn(str(self.agents_md(self.cible())), resultat.stdout)
        self.assertFalse(self.agents_md(self.cible()).exists())


class TestEcritureImpossible(BaseInstalleur):
    """Écrire AGENTS.md ne doit jamais faire tomber l'installation.

    Un dossier à sa place, un lien cassé, un parent refusé : autant de raisons
    d'y renoncer — mais en le disant, et sans changer le code de retour.
    """

    def test_un_dossier_a_la_place_du_fichier_est_saute(self):
        self.profil()
        self.agents_md().mkdir()

        resultat = self.lancer("--appliquer")

        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertIn("AGENTS.md", resultat.stderr)
        self.assertTrue(self.agents_md().is_dir())

    def test_un_lien_casse_est_saute_sans_ecrire_derriere(self):
        """Un lien cassé pointe ailleurs : écrire au travers créerait un fichier
        à l'endroit visé, qui n'a rien à voir avec le coffre."""
        self.profil()
        vise = self.parent / "vise.md"
        self.agents_md().symlink_to(vise)

        resultat = self.lancer("--appliquer")

        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertTrue(self.agents_md().is_symlink())
        self.assertFalse(vise.exists(), "le fichier visé a été créé")
        self.assertIn("AGENTS.md", resultat.stderr)

    def test_un_lien_valide_est_saute_meme_marque(self):
        """Même marqué, un lien n'est pas réécrit : il appartient à qui l'a posé."""
        self.profil()
        cible = self.parent / "ailleurs.md"
        cible.write_text("%s\n\nvieux prompt\n" % INS.MARQUEUR_AGENTS,
                         encoding="utf-8")
        self.agents_md().symlink_to(cible)

        resultat = self.lancer("--appliquer")

        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertTrue(self.agents_md().is_symlink())
        self.assertIn("vieux prompt", cible.read_text(encoding="utf-8"))

    def test_l_apercu_annonce_le_saut_d_un_dossier(self):
        self.profil()
        self.agents_md().mkdir()

        resultat = self.lancer()

        self.assertIn("sauté", resultat.stdout)
        self.assertEqual(list(self.agents_md().iterdir()), [])

    def test_un_parent_en_lecture_seule_est_saute(self):
        """Le dossier où poser AGENTS.md refuse l'écriture : on le dit et on
        continue. Un droit manquant n'est pas une raison d'échouer."""
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            self.skipTest("root ignore les droits d'écriture")
        self.profil()
        os.chmod(self.parent, 0o555)
        self.addCleanup(os.chmod, self.parent, 0o755)

        resultat = self.lancer("--appliquer")

        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertIn("AGENTS.md", resultat.stderr)
        self.assertFalse(self.agents_md().exists())


class TestMarqueur(BaseInstalleur):
    """Le marqueur décide : reconnu, le fichier est à nous ; sinon, il ne l'est pas."""

    def test_un_marqueur_precede_d_un_bom_est_reconnu(self):
        """Un BOM en tête ne doit pas rendre le fichier étranger à lui-même."""
        self.profil()
        self.agents_md().write_text(
            "\ufeff%s\n\nvieux prompt\n" % INS.MARQUEUR_AGENTS, encoding="utf-8")

        resultat = self.lancer("--appliquer")

        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertEqual(self.corps(self.agents_md()),
                         self.prompt_de_reference())
        self.assertNotIn("vieux prompt",
                         self.agents_md().read_text(encoding="utf-8"))

    def test_un_ancien_libelle_reste_reconnu(self):
        """Changer le marqueur un jour ne doit pas orpheliner les installations.

        Un fichier posé par une version antérieure porte le libellé reconnu dans
        une formule différente : il doit être régénéré, pas délaissé.
        """
        self.profil()
        self.agents_md().write_text(
            "<!-- généré par OBSIA/scripts/installer.py, version antérieure -->\n"
            "\nvieux prompt\n", encoding="utf-8")

        self.lancer("--appliquer")

        self.assertEqual(self.corps(self.agents_md()),
                         self.prompt_de_reference())

    def test_l_avertissement_dit_quoi_faire(self):
        """Un avertissement qui ne dit pas comment s'en défaire ne sert à rien."""
        self.profil()
        self.agents_md().write_text("mes consignes\n", encoding="utf-8")

        resultat = self.lancer("--appliquer")

        self.assertIn("marqueur", resultat.stderr)
        self.assertIn("supprimez", resultat.stderr.lower())


if __name__ == "__main__":
    unittest.main()
