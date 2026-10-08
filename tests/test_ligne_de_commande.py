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

sys.path.insert(0, str(SCRIPTS))
#: Le motif vit dans le générateur, pas ici : `verifier_coffre.py` s'en sert pour
#: contrôler le prompt réel du catalogue, et deux copies du même motif finiraient
#: par ne plus dire la même chose. `tests/test_detection_de_chemin.py` le sonde.
from generer_prompt import chemins_absolus               # noqa: E402

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


class TestEnTeteDeuxRacines(BaseLigneDeCommande):
    """L'en-tête nomme **deux** racines distinctes, sans chemin absolu (§7.1).

    Le fichier se pose chez le parent du dépôt (`installer.chemin_agents`) : le
    coffre où vit la mémoire, c'est le dossier qui porte le sous-dossier `OBSIA/`,
    et `racine` n'est que le dépôt de l'outil. Annoncer le dépôt comme « racine du
    coffre » a fait écrire un `0-SAVOIRS/` dans le dépôt de code, sous Goose et
    DeepSeek Harness.

    Les deux racines sont désignées **sans aucun chemin** : l'`AGENTS.md` est
    synchronisé entre des postes où le coffre n'a ni le même chemin ni le même nom,
    et un chemin absolu y serait faux partout sauf là où il fut écrit.

    Le repère n'est pas « le dossier qui contient ce fichier » : le texte se pose
    aussi ailleurs qu'à la racine du coffre — un harness sans fichier à lire
    l'annexe (`.pi/APPEND_SYSTEM.md`, espace de travail). Le sous-dossier `OBSIA/`
    est le repère qui tient partout.
    """

    MEMOIRE = "La mémoire s'écrit dans le coffre, jamais dans le dépôt OBSIA."
    COFFRE = ("Coffre (la mémoire) : le dossier qui contient le sous-dossier "
              "OBSIA/ — celui de l'AGENTS.md d'OBSIA.")
    DEPOT = "Dépôt OBSIA (agents, skills, contrat) : son sous-dossier OBSIA/."

    def test_l_en_tete_nomme_le_coffre_puis_le_depot(self):
        resultat = self.lancer()

        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertEqual(
            [PREMIERE_LIGNE, self.COFFRE, self.DEPOT, self.MEMOIRE],
            resultat.stdout.splitlines()[:4])

    def test_le_prompt_ne_porte_aucun_chemin_absolu(self):
        """Le fichier voyage : un chemin de machine y serait faux ailleurs."""
        resultat = self.lancer()

        trouves = chemins_absolus(resultat.stdout)
        self.assertEqual([], trouves, "chemins absolus dans le prompt : %s" % trouves)

    def test_le_repere_tient_meme_hors_de_la_racine_du_coffre(self):
        """Le texte se pose aussi ailleurs qu'à la racine (relecture M1).

        `.pi/APPEND_SYSTEM.md`, un espace de travail OpenClaw : là, « le dossier
        qui contient ce fichier » désignerait le dossier d'accueil de la copie,
        pas le coffre. Le repère est le sous-dossier `OBSIA/`.
        """
        resultat = self.lancer()

        self.assertNotIn("contient ce fichier", resultat.stdout)
        self.assertIn("contient le sous-dossier OBSIA/", resultat.stdout)

    def test_l_ancienne_formule_qui_prenait_le_depot_pour_le_coffre_a_disparu(self):
        """« Racine du coffre : <le dépôt> » faisait du dépôt la racine du coffre."""
        resultat = self.lancer()

        self.assertNotIn("Racine du coffre", resultat.stdout)


class TestPromptIndependantDeLEmplacement(unittest.TestCase):
    """Deux coffres au même contenu, à des chemins différents : même texte.

    C'est la garantie qui compte pour un `AGENTS.md` synchronisé (Syncthing)
    entre deux postes : rien dans le prompt engendré ne doit dépendre de
    l'endroit où le coffre se trouve, ni du nom qu'il porte.
    """

    def setUp(self):
        self.brut = Path(tempfile.mkdtemp(prefix="obsia-test-ou-"))
        self.addCleanup(shutil.rmtree, self.brut, ignore_errors=True)

    def batir(self, racine: Path) -> Path:
        """Un coffre minimal — toujours le même contenu — à l'endroit demandé."""
        (racine / "IA/system/modules").mkdir(parents=True)
        (racine / "IA/agents").mkdir(parents=True)
        (racine / "IA/skills/s-un").mkdir(parents=True)
        (racine / "IA/system/modules/noyau.md").write_text(
            "---\nschema: 1\nkind: module\nname: noyau\n"
            "description: Le socle.\nessentiel: true\n---\n", encoding="utf-8")
        (racine / "IA/agents/agent-un.md").write_text(
            "---\nschema: 1\nkind: agent\nname: agent-un\n"
            "description: Un agent.\nread_only: false\nmodule: noyau\n---\n\n"
            "Corps.\n", encoding="utf-8")
        (racine / "IA/skills/s-un/skill.md").write_text(
            "---\nschema: 1\nkind: skill\nname: s-un\ndescription: Un skill.\n"
            "module: noyau\n---\n\nCorps.\n", encoding="utf-8")
        (racine / "obsia.local.yml").write_text(
            "schema: 1\nmodules:\n  - noyau\n", encoding="utf-8")
        return racine

    def prompt_de(self, racine: Path) -> str:
        resultat = subprocess.run(
            [sys.executable, str(GENERATEUR), "--racine", str(racine)],
            capture_output=True, text=True)

        self.assertEqual(0, resultat.returncode, resultat.stderr)
        return resultat.stdout

    def test_le_meme_coffre_ailleurs_donne_le_meme_prompt(self):
        # Des noms et des longueurs de chemin franchement différents : un chemin
        # absolu glissé dans le texte les ferait diverger.
        haut = self.batir(self.brut / "un-coffre-au-nom-tres-long" / "OBSIA")
        bas = self.batir(self.brut / "x" / "OBSIA")

        self.assertEqual(self.prompt_de(haut), self.prompt_de(bas))


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


class TestSansProfil(BaseLigneDeCommande):
    """`--sans-profil` : produire le catalogue entier, comme le fait la garde.

    `verifier_coffre.py` mesure le pire cas — catalogue entier, profil ignoré —
    pour qu'aucun `obsia.local.yml` local ne masque un dépassement du plafond de
    Codex. La projection de `codex.md` annonce ce même chiffre : sans ce
    drapeau, la recette documentée mesurait le profil courant sous l'étiquette
    « sans profil ».
    """

    PROFIL = "schema: 1\nmodules:\n  - construction\n"

    def test_sans_drapeau_le_profil_est_applique(self):
        self.ecrire("obsia.local.yml", self.PROFIL)

        resultat = self.lancer()

        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertNotIn("a-administration", resultat.stdout)

    def test_le_drapeau_rend_le_catalogue_entier(self):
        self.ecrire("obsia.local.yml", self.PROFIL)

        resultat = self.lancer("--sans-profil")

        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertIn("a-administration", resultat.stdout)
        self.assertIn("s-conteneurs", resultat.stdout)
        self.assertNotIn("Modules inconnus", resultat.stderr)

    def test_le_catalogue_entier_n_est_jamais_le_plus_petit(self):
        """Le pire cas est bien celui-là : un profil ne fait que retirer."""
        self.ecrire("obsia.local.yml", self.PROFIL)

        avec_profil = self.lancer()
        sans_profil = self.lancer("--sans-profil")

        self.assertGreater(len(sans_profil.stdout.encode("utf-8")),
                           len(avec_profil.stdout.encode("utf-8")))

    def test_l_aide_nomme_le_drapeau(self):
        resultat = self.lancer("--help")

        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertIn("--sans-profil", resultat.stdout)


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
