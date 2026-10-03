"""Ligne de commande de `scripts/generer_prompt.py`.

Le script est appelé par `installer.py` (écriture du prompt système réduit au
profil) : son contrat de sortie compte donc autant que le filtrage lui-même.

  - sans `-o`, le prompt va sur la sortie standard ;
  - avec `-o`, rien sur la sortie standard, tout dans le fichier ;
  - une racine absente ou un coffre vide font un code de retour 1, pas une
    trace d'exception.

Chaque test écrit dans un coffre temporaire ; le coffre réel n'est jamais lu.
"""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True          # ne pas semer de __pycache__ dans le dépôt
SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
GENERATEUR = SCRIPTS / "generer_prompt.py"
INSTALLATEUR = SCRIPTS / "installer.py"

PREMIERE_LIGNE = "Tu opères sur le coffre OBSIA."


class BaseLigneDeCommande(unittest.TestCase):
    """Un coffre temporaire minimal, deux modules, un agent, deux skills."""

    def setUp(self):
        self.racine = Path(tempfile.mkdtemp(prefix="obsia-test-cli-"))
        self.addCleanup(shutil.rmtree, self.racine, ignore_errors=True)

        self.ecrire("IA/system/modules/noyau.md",
                    "---\nschema: 1\nkind: module\nname: noyau\n"
                    "description: Le socle.\nessentiel: true\n---\n")
        self.ecrire("IA/system/modules/construction.md",
                    "---\nschema: 1\nkind: module\nname: construction\n"
                    "description: Bâtir.\nessentiel: false\n"
                    "requiert:\n  - noyau\n---\n")
        self.ecrire("IA/agents/a-construction.md",
                    "---\nschema: 1\nkind: agent\nname: a-construction\n"
                    "description: L'agent de construction.\nmodule: construction\n"
                    "skills:\n  - s-construction\n  - s-conteneurs\n"
                    "mcp:\n  - bruno\n---\n")
        self.ecrire("IA/agents/a-administration.md",
                    "---\nschema: 1\nkind: agent\nname: a-administration\n"
                    "description: L'agent d'administration.\n"
                    "module: administration-homelab\n---\n")
        self.ecrire("IA/skills/s-construction.md",
                    "---\nschema: 1\nkind: skill\nname: s-construction\n"
                    "description: Livrer en branche.\nmodule: construction\n---\n")
        self.ecrire("IA/skills/s-conteneurs/s-conteneurs.md",
                    "---\nschema: 1\nkind: skill\nname: s-conteneurs\n"
                    "description: Gérer les conteneurs.\nmodule: conteneurs\n---\n")
        self.ecrire("IA/MCP/bruno.md",
                    "---\nschema: 1\nkind: mcp\nname: bruno\n"
                    "description: Le MCP de test.\nmodule: construction\n---\n")

    def ecrire(self, relatif: str, contenu: str) -> Path:
        chemin = self.racine / relatif
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(contenu, encoding="utf-8")
        return chemin

    def lancer(self, *arguments: str) -> subprocess.CompletedProcess:
        """Lance le générateur dans un sous-processus : c'est ainsi qu'il sert.

        `-B` : pas de `__pycache__` semé dans `scripts/` par un test.
        """
        return self.lancer_depuis(GENERATEUR, *arguments)

    def lancer_depuis(self, script: Path,
                      *arguments: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-B", str(script), "--racine", str(self.racine),
             *arguments],
            capture_output=True, text=True, check=False)


class TestSortie(BaseLigneDeCommande):
    def test_sortie_standard_par_defaut(self):
        resultat = self.lancer()

        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertTrue(resultat.stdout.startswith(PREMIERE_LIGNE))
        self.assertIn("## Agents disponibles", resultat.stdout)
        self.assertIn("## Skills disponibles", resultat.stdout)
        self.assertIn("## Méthode", resultat.stdout)

    def test_o_ecrit_dans_un_fichier_sans_rien_ecrire_sur_la_sortie(self):
        sortie = self.racine / "prompt.txt"

        resultat = self.lancer("-o", str(sortie))

        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertEqual(resultat.stdout, "")
        self.assertTrue(sortie.is_file())
        self.assertTrue(sortie.read_text(encoding="utf-8").startswith(PREMIERE_LIGNE))

    def test_le_fichier_ecrit_se_termine_par_un_saut_de_ligne(self):
        """Le prompt est un fichier texte : pas de dernière ligne tronquée."""
        sortie = self.racine / "prompt.txt"

        self.lancer("-o", str(sortie))

        self.assertTrue(sortie.read_text(encoding="utf-8").endswith("\n"))

    def test_o_ecrase_un_fichier_existant(self):
        """Le générateur écrit, il ne protège pas : c'est à `installer.py` de le faire.

        Le marqueur « généré — ne pas éditer » et le refus d'écraser un fichier
        sans ce marqueur vivent dans l'appelant (§13), pas ici.
        """
        sortie = self.ecrire("AGENTS.md", "rédigé à la main, à ne pas perdre\n")

        self.lancer("-o", str(sortie))

        self.assertTrue(sortie.read_text(encoding="utf-8").startswith(PREMIERE_LIGNE))
        self.assertNotIn("à ne pas perdre", sortie.read_text(encoding="utf-8"))

    def test_racine_introuvable(self):
        fichier = self.racine / "inexistant.md"

        resultat = subprocess.run(
            [sys.executable, "-B", str(GENERATEUR), "--racine",
             str(self.racine / "pas-la"), "-o", str(fichier)],
            capture_output=True, text=True, check=False)

        self.assertEqual(resultat.returncode, 1)
        self.assertIn("Racine introuvable", resultat.stderr)
        self.assertFalse(fichier.is_file())

    def test_coffre_sans_agent_ni_skill(self):
        vide = Path(tempfile.mkdtemp(prefix="obsia-test-vide-"))
        self.addCleanup(shutil.rmtree, vide, ignore_errors=True)

        resultat = subprocess.run(
            [sys.executable, "-B", str(GENERATEUR), "--racine", str(vide)],
            capture_output=True, text=True, check=False)

        self.assertEqual(resultat.returncode, 1)
        self.assertIn("Aucun agent ni skill trouvé", resultat.stderr)


class TestProfilDeBoutEnBout(BaseLigneDeCommande):
    """Le profil gouverne le prompt produit — et lui seul, plus les index.

    Les index versionnés restent au catalogue complet ; c'est
    `test_regenerate_index.py` qui le garantit.
    """

    def test_sans_profil_tout_apparait(self):
        resultat = self.lancer()

        self.assertIn("a-administration", resultat.stdout)
        self.assertIn("s-conteneurs", resultat.stdout)
        self.assertIn("MCP : bruno", resultat.stdout)

    def test_avec_profil_les_modules_ecartes_disparaissent(self):
        self.ecrire("obsia.local.yml", "schema: 1\nmodules:\n  - construction\n")

        resultat = self.lancer()

        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertIn("a-construction", resultat.stdout)
        self.assertIn("s-construction", resultat.stdout)
        self.assertNotIn("a-administration", resultat.stdout)
        self.assertNotIn("s-conteneurs", resultat.stdout)
        # bruno reste déclaré : c'est un MCP, pas un module.
        self.assertIn("MCP : bruno", resultat.stdout)

    def test_avec_profil_le_skill_ecarte_ne_reste_pas_cite_par_lagent(self):
        self.ecrire("obsia.local.yml", "schema: 1\nmodules:\n  - construction\n")

        resultat = self.lancer()

        ligne = [l for l in resultat.stdout.splitlines()
                 if "skills :" in l][0]
        self.assertEqual(ligne.strip(), "(skills : s-construction ; MCP : bruno)")


class TestProfilFautif(BaseLigneDeCommande):
    """§13 : un profil qui nomme un module du catalogue doit le signaler.

    Le nom hors catalogue ne désigne rien : la génération aboutit, mais sans
    mot l'écart entre ce qu'on croit installé et ce qui l'est reste invisible.
    """

    FAUTIF = "schema: 1\nmodules:\n  - construction\n  - constructionn\n"

    def test_le_generateur_avertit_sans_echouer(self):
        self.ecrire("obsia.local.yml", self.FAUTIF)

        resultat = self.lancer()

        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertIn("constructionn", resultat.stderr)
        self.assertTrue(resultat.stdout.startswith(PREMIERE_LIGNE))

    def test_le_generateur_reste_muet_avec_un_profil_juste(self):
        self.ecrire("obsia.local.yml", "schema: 1\nmodules:\n  - construction\n")

        resultat = self.lancer()

        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertNotIn("Modules inconnus", resultat.stderr)

    def test_le_generateur_ecrit_quand_meme_son_fichier(self):
        """L'avertissement ne doit pas interrompre la sortie demandée."""
        self.ecrire("obsia.local.yml", self.FAUTIF)
        sortie = self.racine / "prompt.txt"

        resultat = self.lancer("-o", str(sortie))

        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertIn("constructionn", resultat.stderr)
        self.assertTrue(sortie.is_file())

    def test_l_installateur_avertit_en_rejouant_un_profil(self):
        self.ecrire("obsia.local.yml", self.FAUTIF)

        resultat = self.lancer_depuis(INSTALLATEUR, "--rejouer")

        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertIn("constructionn", resultat.stderr)

    def test_l_installateur_reste_muet_avec_un_profil_juste(self):
        self.ecrire("obsia.local.yml", "schema: 1\nmodules:\n  - construction\n")

        resultat = self.lancer_depuis(INSTALLATEUR, "--rejouer")

        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertNotIn("Modules inconnus", resultat.stderr)

    def test_un_module_inconnu_demande_a_la_main_reste_une_erreur(self):
        """`--modules` est une demande explicite : l'erreur franche est gardée."""
        resultat = self.lancer_depuis(INSTALLATEUR, "--modules", "pas-au-catalogue")

        self.assertEqual(resultat.returncode, 1)
        self.assertIn("Modules inconnus", resultat.stderr)


class TestAideDeLInstallateur(BaseLigneDeCommande):
    """L'aide de `--installer` doit dire où part l'`AGENTS.md`."""

    def test_l_aide_dit_que_l_agents_md_va_dans_cible_parent(self):
        """`CIBLE` ne suffit pas à le placer : il n'est pas dans la cible.

        `installer.py` écrit l'`AGENTS.md` un cran au-dessus de la cible
        (`cible.parent/AGENTS.md`), parce que c'est là que Codex le lit. Sans
        cette précision, on le cherche dans la cible — et il n'y est pas.
        """
        resultat = self.lancer_depuis(INSTALLATEUR, "--help")

        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        # L'aide est repliée à 80 colonnes : on compare sur une seule ligne.
        aide = " ".join(resultat.stdout.split())
        self.assertRegex(aide, r"--installer CIBLE .*CIBLE/\.\.")


if __name__ == "__main__":
    unittest.main()
