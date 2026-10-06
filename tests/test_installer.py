"""`installer.py --appliquer` et l'AGENTS.md qu'il pose à côté du coffre.

Les harness lisent le fichier de consignes du dépôt dans lequel ils s'ouvrent
(une fiche par harness dans `IA/system/adaptateurs-harness/`). Le coffre n'étant
pas ce dépôt, le fichier se pose chez le parent — hors dépôt, donc hors
publication, et porteur d'un marqueur qui dit à qui il appartient.

Le coffre de test n'a pas de `scripts/` : `regenerer()` s'arrête alors
proprement, et ces tests ne jugent que l'AGENTS.md. Le seul endroit où une
cible en reçoit un est `TestRegenerationSansLien` — parce que la régénération
est justement ce qu'on y juge.
"""

import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
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

    def test_l_etape_de_reprise_borne_son_champ(self):
        """L'étape 0 vaut pour qui écrit, dans l'arbre principal et les worktrees."""
        self.ecrire("IA/agents/agent-ecrit.md",
                    "---\nschema: 1\nkind: agent\nname: agent-ecrit\n"
                    "description: Un agent qui écrit.\nread_only: false\n"
                    "module: construction\n---\n\nCorps.\n")
        self.profil()

        self.lancer("--appliquer")

        texte = self.agents_md().read_text(encoding="utf-8")
        # L'étape 0 engendrée reprend le §10 du contrat, mot pour mot — le
        # passage est long, il se replie : on compare mot à mot, pas ligne à ligne.
        normalise = " ".join(texte.replace("**", "").split())
        self.assertIn("dans l'arbre principal et dans chaque worktree lié", normalise)
        self.assertIn("Un agent `read_only: true` n'a pas de carnet : il saute "
                      "cette étape.", normalise)
        # L'index marque les agents en lecture seule, comme les skills.
        self.assertIn("**agent-verif** [lecture seule]", texte)
        self.assertIn("**agent-ecrit** —", texte)

    def test_l_etape_0_engendree_reprend_celle_du_contrat(self):
        """N1 : l'étape 0 de l'`AGENTS.md` et celle du §10 disent la même chose."""
        def etape_0(texte):
            bloc = re.search(r"^0\. Au démarrage.*?(?=\n1\. |\Z)", texte,
                             re.MULTILINE | re.DOTALL).group(0)
            return " ".join(bloc.replace("**", "").split())

        self.profil()
        self.lancer("--appliquer")
        contrat = (SCRIPTS.parent / "IA" / "system"
                   / "VAULT-CONTRACT.md").read_text(encoding="utf-8")
        self.assertEqual(etape_0(contrat),
                         etape_0(self.agents_md().read_text(encoding="utf-8")))

    def test_la_methode_renvoie_au_noyau_et_pas_aux_annexes(self):
        """N3 : le noyau se lit en entier, une annexe seulement avant son acte.

        Le contrat est découpé en un noyau (`IA/system/VAULT-CONTRACT.md`) et
        des annexes (`IA/system/contrat/`) : la méthode doit dire lequel des
        deux se lit à l'entrée — sinon « lire le contrat en entier » se lit
        comme la somme des deux, ce qui coûte plus qu'avant le découpage.
        """
        self.profil()
        self.lancer("--appliquer")
        texte = self.agents_md().read_text(encoding="utf-8")

        methode = re.search(r"^## Méthode\n(.*?)(?=\n## |\Z)", texte,
                            re.MULTILINE | re.DOTALL).group(1)
        self.assertIn("Lis en entier le noyau `IA/system/VAULT-CONTRACT.md`",
                      methode)
        self.assertIn("`IA/system/contrat/`", methode)
        self.assertIn("avant l'acte", methode)

        # Le prompt cite les fichiers, il n'en recopie aucune ligne — sauf
        # l'étape 0 du §10, copiée exprès (le test voisin la tient égale). Ce
        # qui entrerait par une annexe entrerait sans qu'on le voie.
        racine = SCRIPTS.parent / "IA" / "system"
        dossier = racine / "contrat"
        annexes = sorted(a for a in dossier.glob("*.md")
                         if a.name != "registre.md")
        self.assertTrue(annexes, "aucune annexe trouvée : rien n'est prouvé")
        self.assertEqual(len(annexes), 6, "le nombre d'annexes a changé")

        def sans_etape_0(texte):
            coupe, n = re.subn(r"^0\. Au démarrage.*?(?=\n1\. |\n## |\Z)", "",
                               texte, flags=re.MULTILINE | re.DOTALL)
            self.assertEqual(n, 1, "étape 0 du §10 introuvable")
            # L'étape 0 porte la clause de transition — trois emplacements à
            # essayer, une date de fin — et se replie sur huit lignes : elle est
            # longue à dessein. Ce qui est contrôlé ici, c'est que la coupe
            # n'emporte pas une section entière avec elle.
            self.assertLess(len(texte) - len(coupe), 800,
                            "la coupe de l'étape 0 a emporté trop de texte")
            return coupe

        sources = [sans_etape_0((racine / "VAULT-CONTRACT.md")
                                .read_text(encoding="utf-8")),
                   *(annexe.read_text(encoding="utf-8") for annexe in annexes)]
        recopiees = [ligne.strip()
                     for source in sources
                     for ligne in source.splitlines()
                     if len(ligne.strip()) > 40 and ligne.strip() in texte]
        self.assertEqual(recopiees, [])

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


class TestToutEnModeCopie(BaseInstalleur):
    """`--tout` veut dire « catalogue complet », dans les deux modes.

    En copie, le `--tout` sautait la copie : on demandait le catalogue entier et
    la cible restait vide, pendant que le profil annonçait un état qu'elle
    n'avait pas. Un catalogue complet ne pose pas de profil — c'est le profil
    qui dit « ce coffre est réduit » — mais il se copie entièrement.
    """

    def cible(self) -> Path:
        return self.parent / "chez-moi" / "OBSIA"

    def module_en_plus(self) -> None:
        """Un troisième module, hors du profil : c'est lui qui prouve `--tout`."""
        self.ecrire("IA/system/modules/ailleurs.md",
                    "---\nschema: 1\nkind: module\nname: ailleurs\n"
                    "description: Ailleurs.\nessentiel: false\n"
                    "requiert:\n  - noyau\n---\n\nCorps.\n")
        self.ecrire("IA/agents/agent-ailleurs.md",
                    "---\nschema: 1\nkind: agent\nname: agent-ailleurs\n"
                    "description: Un autre agent.\nread_only: true\n"
                    "module: ailleurs\n---\n\nCorps.\n")

    def test_la_cible_recoit_les_fichiers_de_tous_les_modules(self):
        self.profil(modules="construction", mode="copie")
        self.module_en_plus()

        resultat = self.lancer("--tout", "--appliquer",
                               "--installer", str(self.cible()))

        self.assertEqual(resultat.returncode, 0, resultat.stdout + resultat.stderr)
        for relatif in ("IA/agents/agent-verif.md",
                        "IA/skills/a-verifie.md",
                        "IA/agents/agent-ailleurs.md"):
            self.assertTrue((self.cible() / relatif).is_file(), relatif)

    def test_la_copie_n_emporte_pas_de_profil(self):
        """Catalogue complet : il n'y a rien à rejouer, donc rien à décrire."""
        self.profil(modules="construction", mode="copie")

        self.lancer("--tout", "--appliquer", "--installer", str(self.cible()))

        self.assertFalse((self.cible() / "obsia.local.yml").exists())

    def test_l_apercu_ne_promet_pas_de_profil(self):
        self.profil(modules="construction", mode="copie")

        resultat = self.lancer("--tout", "--installer", str(self.cible()))

        self.assertIn("aucun — catalogue complet", resultat.stdout)
        self.assertFalse(self.cible().exists())

    def test_en_place_le_profil_disparait(self):
        """En place, `--tout` reste ce qu'il était : plus rien à réduire."""
        self.profil(modules="construction")

        resultat = self.lancer("--tout", "--appliquer")

        self.assertEqual(resultat.returncode, 0, resultat.stdout + resultat.stderr)
        self.assertFalse((self.racine / "obsia.local.yml").exists())

    def test_la_source_garde_son_profil(self):
        """`--installer` copie : il n'a aucune raison de modifier la source."""
        self.profil(modules="construction", mode="copie")
        avant = (self.racine / "obsia.local.yml").read_text(encoding="utf-8")

        resultat = self.lancer("--tout", "--appliquer",
                               "--installer", str(self.cible()))

        self.assertEqual(resultat.returncode, 0, resultat.stdout + resultat.stderr)
        self.assertTrue((self.racine / "obsia.local.yml").is_file(),
                        "la source ne se modifie pas, on ne fait que la lire")
        self.assertEqual((self.racine / "obsia.local.yml").read_text("utf-8"),
                         avant)

    def test_le_profil_de_la_cible_disparait(self):
        """Le profil à supprimer, en copie, c'est celui de la cible."""
        self.profil(modules="construction", mode="copie")
        self.cible().mkdir(parents=True)
        (self.cible() / "obsia.local.yml").write_text(
            "schema: 1\nmode: copie\nmodules:\n  - noyau\n", encoding="utf-8")

        resultat = self.lancer("--tout", "--appliquer",
                               "--installer", str(self.cible()))

        self.assertEqual(resultat.returncode, 0, resultat.stdout + resultat.stderr)
        self.assertFalse((self.cible() / "obsia.local.yml").exists(),
                         "catalogue complet : la cible n'a rien à rejouer")
        self.assertTrue((self.racine / "obsia.local.yml").is_file())


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


class TestLaCopieNeTouchePasALInstance(BaseInstalleur):
    """En mode copie, ce qui appartient au copié lui reste.

    `mémoire/`, `brouillon/` et les journaux de session sont les trois dossiers
    où le travail du copié vit. L'installeur les crée s'ils manquent, avec leur
    README, mais ne les vide jamais : réinstaller ne doit pas effacer.
    """

    def cible(self) -> Path:
        return self.parent / "chez-moi" / "OBSIA"

    def test_la_memoire_du_copie_est_conservee(self):
        self.profil(mode="copie")
        note = self.cible() / "mémoire" / "mes-notes.md"
        note.parent.mkdir(parents=True)
        note.write_text("mon travail\n", encoding="utf-8")

        resultat = self.lancer("--appliquer", "--installer", str(self.cible()))

        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertTrue(note.is_file(), "la note du copié a été effacée")
        self.assertEqual(note.read_text(encoding="utf-8"), "mon travail\n")

    def test_le_profil_du_copie_est_conserve(self):
        self.profil(mode="copie")
        profil = self.cible() / "mémoire" / "profil-utilisateur.md"
        profil.parent.mkdir(parents=True)
        profil.write_text("je suis le copié\n", encoding="utf-8")

        self.lancer("--appliquer", "--installer", str(self.cible()))

        self.assertEqual(profil.read_text(encoding="utf-8"), "je suis le copié\n")

    def test_le_journal_de_la_source_ne_part_pas_chez_le_copie(self):
        self.profil(mode="copie")
        self.ecrire("IA/system/session-log/2026-01-01-ailleurs.md", "mes notes\n")

        self.lancer("--appliquer", "--installer", str(self.cible()))

        self.assertFalse((self.cible() / "IA" / "system" / "session-log"
                          / "2026-01-01-ailleurs.md").exists())

    def test_le_journal_du_copie_est_conserve(self):
        self.profil(mode="copie")
        journal = self.cible() / "IA" / "system" / "session-log" / "2026-01-01-moi.md"
        journal.parent.mkdir(parents=True)
        journal.write_text("ma session\n", encoding="utf-8")

        self.lancer("--appliquer", "--installer", str(self.cible()))

        self.assertTrue(journal.is_file(), "le journal du copié a été effacé")

    def test_brouillon_est_cree_avec_son_readme(self):
        self.profil(mode="copie")
        self.ecrire("brouillon/README.md", "# Brouillon\n")

        self.lancer("--appliquer", "--installer", str(self.cible()))

        lireme = self.cible() / "brouillon" / "README.md"
        self.assertTrue(lireme.is_file(), "brouillon/ est créé sans son README")
        self.assertEqual(lireme.read_text(encoding="utf-8"), "# Brouillon\n")

    def test_l_apercu_dit_conserve(self):
        self.profil(mode="copie")
        note = self.cible() / "brouillon" / "mes-notes.md"
        note.parent.mkdir(parents=True)
        note.write_text("mon travail\n", encoding="utf-8")
        # La mémoire se lit à côté du dépôt, pas dedans (§7.1).
        profil = self.cible().parent / "0-PERSONNELS" / "profil-utilisateur.md"
        profil.parent.mkdir(parents=True)
        profil.write_text("Nom : moi\n", encoding="utf-8")

        resultat = self.lancer("--installer", str(self.cible()))

        self.assertIn("conservé", resultat.stdout)
        self.assertIn("0-PERSONNELS/profil-utilisateur.md", resultat.stdout)
        self.assertIn("0-MEMOIRES/README.md", resultat.stdout)


class TestAucunLienSuivi(BaseInstalleur):
    """Un lien symbolique de la cible ne se suit ni en lecture ni en écriture.

    Un `IA` déplacé ailleurs, une `mémoire/` partagée : l'installeur écrirait
    hors du coffre qu'il croit installer. Il le dit, et passe.
    """

    def cible(self) -> Path:
        return self.parent / "chez-moi" / "OBSIA"

    def ailleurs(self) -> Path:
        chemin = self.parent / "ailleurs"
        chemin.mkdir(exist_ok=True)
        return chemin

    def test_la_copie_n_ecrit_pas_a_travers_un_lien(self):
        self.profil(mode="copie")
        cible = self.cible()
        cible.mkdir(parents=True)
        (cible / "IA").symlink_to(self.ailleurs(), target_is_directory=True)

        resultat = self.lancer("--appliquer", "--installer", str(cible))

        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertEqual(sorted(p.name for p in self.ailleurs().iterdir()), [])
        self.assertIn("lien", resultat.stderr.lower())

    def test_la_memoire_liee_n_est_pas_remplie(self):
        self.profil(mode="copie")
        cible = self.cible()
        cible.mkdir(parents=True)
        (cible / "mémoire").symlink_to(self.ailleurs(), target_is_directory=True)

        resultat = self.lancer("--appliquer", "--installer", str(cible))

        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertEqual(sorted(p.name for p in self.ailleurs().iterdir()), [])
        self.assertTrue((cible / "mémoire").is_symlink())

    def test_le_journal_lie_n_est_pas_rempli(self):
        self.profil(mode="copie")
        cible = self.cible()
        (cible / "IA" / "system").mkdir(parents=True)
        (cible / "IA" / "system" / "session-log").symlink_to(
            self.ailleurs(), target_is_directory=True)

        self.lancer("--appliquer", "--installer", str(cible))

        self.assertEqual(sorted(p.name for p in self.ailleurs().iterdir()), [])

    def test_les_agents_lies_ne_sont_pas_reduits(self):
        self.profil(mode="copie")
        cible = self.cible()
        ailleurs = self.ailleurs()
        (cible / "IA").mkdir(parents=True)
        (cible / "IA" / "agents").symlink_to(ailleurs, target_is_directory=True)
        agent = ailleurs / "agent-verif.md"
        agent.write_text("---\nname: agent-verif\nskills:\n  - absent\n"
                         "---\n\nCorps.\n", encoding="utf-8")

        self.lancer("--appliquer", "--installer", str(cible))

        self.assertIn("absent", agent.read_text(encoding="utf-8"))


class TestRegenerationSansLien(BaseInstalleur):
    """La régénération n'écrit pas à travers un lien de la cible.

    `regenerate_sommaire.py` pose les `sommaire.md` dans la mémoire du coffre
    parent — le dossier qui contient la cible (§7.1) —, `regenerate_index.py`
    les index dans `IA/system/`. Si l'une de ces racines est un lien, ces
    scripts écrivent hors du coffre visé ; le vérificateur, lui, lit des
    fichiers qui ne sont pas au coffre.

    Les coffres des autres tests n'ont pas de `scripts/`, donc rien n'y est
    régénéré. Ici on en pose un, avec trois béquilles qui écrivent exactement
    là où écrivent les vrais générateurs et qui disent la phrase du
    vérificateur — « index et sommaires à jour ».
    """

    def cible(self) -> Path:
        return self.parent / "chez-moi" / "OBSIA"

    def memoire(self) -> Path:
        """La mémoire du coffre cible : à côté du dépôt, pas dedans (§7.1)."""
        return self.cible().parent / "0-SAVOIRS"

    def ailleurs(self) -> Path:
        chemin = self.parent / "ailleurs"
        chemin.mkdir(exist_ok=True)
        return chemin

    def poser_les_generateurs(self) -> None:
        """Trois béquilles : elles écrivent et parlent comme les vrais scripts."""
        scripts = self.cible() / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        (scripts / "regenerate_sommaire.py").write_text(
            "from pathlib import Path\n"
            "racine = Path(__file__).resolve().parent.parent\n"
            "cible = racine.parent / '0-SAVOIRS' / 'sommaire.md'\n"
            "cible.parent.mkdir(parents=True, exist_ok=True)\n"
            "cible.write_text('sommaire\\n', encoding='utf-8')\n", encoding="utf-8")
        (scripts / "regenerate_index.py").write_text(
            "from pathlib import Path\n"
            "racine = Path(__file__).resolve().parent.parent\n"
            "index = racine / 'IA' / 'system' / 'agents-index.md'\n"
            "index.parent.mkdir(parents=True, exist_ok=True)\n"
            "index.write_text('index\\n', encoding='utf-8')\n", encoding="utf-8")
        (scripts / "verifier_coffre.py").write_text(
            "print('1 fichier, 1 tâche, index et sommaires à jour.')\n",
            encoding="utf-8")

    def test_les_bequilles_servent_quand_rien_n_est_lie(self):
        """Sans lien, la régénération va bien jusqu'au bout : la preuve est là.

        Sans ce test, les autres passeraient même si les béquilles n'étaient
        jamais lancées.
        """
        self.profil(mode="copie")
        cible = self.cible()
        cible.mkdir(parents=True)
        self.memoire().mkdir(parents=True)
        self.poser_les_generateurs()

        resultat = self.lancer("--appliquer", "--installer", str(cible))

        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertTrue((self.memoire() / "sommaire.md").is_file())
        self.assertTrue((cible / "IA" / "system" / "agents-index.md").is_file())
        self.assertIn("index et sommaires à jour", resultat.stdout)

    def test_la_memoire_liee_n_est_pas_regeneree(self):
        self.profil(mode="copie")
        cible = self.cible()
        cible.mkdir(parents=True)
        self.memoire().symlink_to(self.ailleurs(), target_is_directory=True)
        self.poser_les_generateurs()

        resultat = self.lancer("--appliquer", "--installer", str(cible))

        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertEqual(sorted(p.name for p in self.ailleurs().iterdir()), [],
                         "la régénération a écrit à travers le lien")
        self.assertIn("lien", resultat.stderr.lower())
        self.assertNotIn("index et sommaires à jour",
                         resultat.stdout + resultat.stderr)
        self.assertIn("sans régénération", resultat.stdout)

    def test_l_ia_lie_n_est_pas_regenere(self):
        self.profil(mode="copie")
        cible = self.cible()
        cible.mkdir(parents=True)
        (cible / "IA").symlink_to(self.ailleurs(), target_is_directory=True)
        self.poser_les_generateurs()

        resultat = self.lancer("--appliquer", "--installer", str(cible))

        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertEqual(sorted(p.name for p in self.ailleurs().iterdir()), [],
                         "la régénération a écrit à travers le lien")
        self.assertIn("lien", resultat.stderr.lower())
        self.assertNotIn("index et sommaires à jour",
                         resultat.stdout + resultat.stderr)
        self.assertIn("sans régénération", resultat.stdout)

    def test_un_lien_imbrique_dans_l_ia_n_est_pas_regenere(self):
        """Un lien plus profond suffit : `IA/system` posé ailleurs.

        `regenerate_index.py` écrit sous `IA/system/`. Ne regarder que `IA`
        laissait donc ce lien-là passer, et les index partir hors de la cible
        sans un mot — il faut parcourir l'arbre, pas ses deux racines.
        """
        self.profil(mode="copie")
        cible = self.cible()
        (cible / "IA").mkdir(parents=True)
        (cible / "IA" / "system").symlink_to(self.ailleurs(),
                                            target_is_directory=True)
        self.poser_les_generateurs()

        resultat = self.lancer("--appliquer", "--installer", str(cible))

        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertEqual(sorted(p.name for p in self.ailleurs().iterdir()), [],
                         "la régénération a écrit à travers le lien")
        self.assertIn("lien", resultat.stderr.lower())
        self.assertNotIn("index et sommaires à jour",
                         resultat.stdout + resultat.stderr)
        self.assertIn("sans régénération", resultat.stdout)

    def test_un_fichier_lie_dans_la_memoire_n_est_pas_regenere(self):
        """Même un fichier lié compte : `0-SAVOIRS/sommaire.md` pointé ailleurs."""
        self.profil(mode="copie")
        cible = self.cible()
        self.memoire().mkdir(parents=True)
        (self.memoire() / "sommaire.md").symlink_to(
            self.ailleurs() / "sommaire.md")
        self.poser_les_generateurs()

        resultat = self.lancer("--appliquer", "--installer", str(cible))

        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertEqual(sorted(p.name for p in self.ailleurs().iterdir()), [],
                         "la régénération a écrit à travers le lien")
        self.assertIn("lien", resultat.stderr.lower())
        self.assertNotIn("index et sommaires à jour",
                         resultat.stdout + resultat.stderr)
        self.assertIn("sans régénération", resultat.stdout)


class TestExclusionObsidian(BaseInstalleur):
    """`installer.py` exclut le `code/` des projets des Fichiers exclus d'Obsidian.

    Le motif est écrit en regex entre barres obliques (§7.3) ; l'ancien motif à
    joker `0-PROJETS/*/code`, non documenté, est retiré au passage."""

    def app_json(self) -> Path:
        return self.parent / ".obsidian" / "app.json"

    def coffre_obsidian(self) -> None:
        """Un coffre parent qui a de quoi exclure : `.obsidian/` et `0-PROJETS/`."""
        (self.parent / ".obsidian").mkdir()
        (self.parent / "0-PROJETS").mkdir()

    def test_sans_coffre_obsidian_rien_n_est_ecrit(self):
        (self.parent / "0-PROJETS").mkdir()
        INS.exclure_code_d_obsidian(self.racine)
        self.assertFalse(self.app_json().exists())

    def test_sans_projets_rien_n_est_ecrit_et_le_dit(self):
        # Rien à exclure : on ne touche pas au réglage d'un autre usage, et on
        # prévient qu'il faudra relancer l'installeur après le premier projet.
        (self.parent / ".obsidian").mkdir()
        sortie = StringIO()
        with redirect_stdout(sortie):
            INS.exclure_code_d_obsidian(self.racine)
        self.assertFalse(self.app_json().exists())
        self.assertIn("pas de 0-PROJETS/ : exclusion Obsidian non posée",
                      sortie.getvalue())

    def test_un_fichier_neuf_nait_en_0600(self):
        self.coffre_obsidian()
        INS.exclure_code_d_obsidian(self.racine)
        mode = stat.S_IMODE(os.stat(self.app_json()).st_mode)
        self.assertEqual(0o600, mode)

    def test_le_mode_existant_est_preserve(self):
        self.coffre_obsidian()
        self.app_json().write_text('{"userIgnoreFilters": []}\n', encoding="utf-8")
        os.chmod(self.app_json(), 0o644)
        INS.exclure_code_d_obsidian(self.racine)
        self.assertEqual(0o644, stat.S_IMODE(os.stat(self.app_json()).st_mode))

    def test_le_motif_vise_le_code_des_projets_et_rien_d_autre(self):
        # Obsidian délimite ses motifs par des barres obliques : on compile le
        # corps pour vérifier ce que le motif attrape vraiment.
        corps = INS.MOTIF_CODE_OBSIDIAN[1:-1]
        motif = re.compile(corps)
        for chemin in ("0-PROJETS/mon-projet/code/",
                       "0-PROJETS/mon-projet/code/src/main.py"):
            self.assertIsNotNone(motif.search(chemin), chemin)
        for chemin in ("0-PROJETS/mon-projet/",
                       "0-PROJETS/mon-projet/docs/code/x.md",
                       "0-PROJETS/code/",
                       "notes/0-PROJETS/mon-projet/code/x.py"):
            self.assertIsNone(motif.search(chemin), chemin)

    def test_le_motif_est_ajoute_sans_ecraser(self):
        self.coffre_obsidian()
        self.app_json().write_text('{"userIgnoreFilters": ["autre"]}\n',
                                   encoding="utf-8")
        INS.exclure_code_d_obsidian(self.racine)
        donnees = json.loads(self.app_json().read_text(encoding="utf-8"))
        self.assertIn(INS.MOTIF_CODE_OBSIDIAN, donnees["userIgnoreFilters"])
        self.assertIn("autre", donnees["userIgnoreFilters"])

    def test_deja_present_ne_reecrit_pas(self):
        self.coffre_obsidian()
        self.app_json().write_text(
            json.dumps({"userIgnoreFilters": [INS.MOTIF_CODE_OBSIDIAN]}) + "\n",
            encoding="utf-8")
        avant = self.app_json().read_text(encoding="utf-8")
        INS.exclure_code_d_obsidian(self.racine)
        self.assertEqual(avant, self.app_json().read_text(encoding="utf-8"))

    def test_l_ancien_motif_a_joker_est_retire(self):
        self.coffre_obsidian()
        self.app_json().write_text(
            json.dumps({"userIgnoreFilters": [INS.MOTIF_CODE_OBSIDIAN_ANCIEN,
                                              "autre"]}) + "\n",
            encoding="utf-8")
        INS.exclure_code_d_obsidian(self.racine)
        donnees = json.loads(self.app_json().read_text(encoding="utf-8"))
        self.assertNotIn(INS.MOTIF_CODE_OBSIDIAN_ANCIEN,
                         donnees["userIgnoreFilters"])
        self.assertIn(INS.MOTIF_CODE_OBSIDIAN, donnees["userIgnoreFilters"])
        self.assertIn("autre", donnees["userIgnoreFilters"])

    def test_deux_passages_laissent_le_meme_fichier(self):
        self.coffre_obsidian()
        INS.exclure_code_d_obsidian(self.racine)
        apres_un = self.app_json().read_text(encoding="utf-8")
        INS.exclure_code_d_obsidian(self.racine)
        self.assertEqual(apres_un, self.app_json().read_text(encoding="utf-8"))

    def test_l_ecriture_ne_laisse_pas_de_temporaire(self):
        self.coffre_obsidian()
        INS.exclure_code_d_obsidian(self.racine)
        restes = [f.name for f in (self.parent / ".obsidian").iterdir()
                  if f.name != "app.json"]
        self.assertEqual([], restes,
                         "l'écriture atomique doit nettoyer son temporaire")

    def test_un_user_ignore_filters_d_un_autre_type_n_est_pas_touche(self):
        self.coffre_obsidian()
        avant = '{"userIgnoreFilters": "pas une liste"}\n'
        self.app_json().write_text(avant, encoding="utf-8")
        INS.exclure_code_d_obsidian(self.racine)
        self.assertEqual(avant, self.app_json().read_text(encoding="utf-8"))

    def test_un_lien_symbolique_sur_app_json_n_est_pas_suivi(self):
        self.coffre_obsidian()
        cible = self.parent / "ailleurs.json"
        cible.write_text('{"userIgnoreFilters": []}\n', encoding="utf-8")
        os.symlink(cible, self.app_json())
        INS.exclure_code_d_obsidian(self.racine)
        self.assertTrue(self.app_json().is_symlink())
        self.assertEqual('{"userIgnoreFilters": []}\n',
                         cible.read_text(encoding="utf-8"))

    def test_config_illisible_laissee_telle_quelle(self):
        self.coffre_obsidian()
        self.app_json().write_text("{pas du json", encoding="utf-8")
        INS.exclure_code_d_obsidian(self.racine)
        self.assertEqual("{pas du json", self.app_json().read_text(encoding="utf-8"))


GABARITS_DEPOT = (Path(__file__).resolve().parent.parent
                  / "IA" / "system" / "depot-de-donnees")
LISTE_BLANCHE = (GABARITS_DEPOT / "gitignore-coffre").read_text(encoding="utf-8")


def git(ou, *arguments):
    return subprocess.run(["git", "-C", str(ou), *arguments],
                          capture_output=True, text=True)


class TestDepotDeDonnees(BaseInstalleur):
    """§7.1 : l'installeur outille le dépôt de données du coffre parent — sa
    liste blanche (jamais écrasée), son `git init`, son distant, ses crochets.

    Le coffre parent, ici, est le dossier qui contient le dépôt produit.
    """

    def marquer_le_coffre(self):
        """Un coffre parent reconnaissable : un marqueur suffit (§7.1)."""
        (self.parent / "0-PROJETS").mkdir(parents=True, exist_ok=True)

    def outiller_le_produit(self):
        """Le produit porte ses gabarits, comme le dépôt versionné les publie."""
        for nom in ("gitignore-coffre", "pre-commit", "post-commit"):
            self.ecrire("IA/system/depot-de-donnees/" + nom,
                        (GABARITS_DEPOT / nom).read_text(encoding="utf-8"))

    def profil_avec_distant(self, url="ssh://nas/volume/coffre.git"):
        self.ecrire("obsia.local.yml",
                    "schema: 1\nmode: en-place\nmodules:\n  - construction\n"
                    "coffre_distant: %s\n" % url)

    def test_la_liste_blanche_est_posee_depuis_le_gabarit(self):
        self.marquer_le_coffre()
        self.outiller_le_produit()
        self.profil()
        resultat = self.lancer("--appliquer")
        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertEqual(LISTE_BLANCHE,
                         (self.parent / ".gitignore").read_text(encoding="utf-8"))
        self.assertIn("liste blanche", resultat.stdout)

    def test_la_liste_blanche_n_est_jamais_ecrasee(self):
        self.marquer_le_coffre()
        self.outiller_le_produit()
        self.profil()
        (self.parent / ".gitignore").write_text("# à moi\n", encoding="utf-8")
        resultat = self.lancer("--appliquer")
        self.assertEqual("# à moi\n",
                         (self.parent / ".gitignore").read_text(encoding="utf-8"))
        self.assertIn("reste tel quel", resultat.stderr)

    def test_le_depot_de_donnees_est_initialise(self):
        self.marquer_le_coffre()
        self.outiller_le_produit()
        self.profil()
        self.lancer("--appliquer")
        self.assertTrue((self.parent / ".git").is_dir())

    def test_les_crochets_sont_poses_et_actives(self):
        self.marquer_le_coffre()
        self.outiller_le_produit()
        self.profil()
        self.lancer("--appliquer")
        crochet = self.parent / ".githooks" / "pre-commit"
        self.assertTrue(crochet.is_file())
        self.assertTrue(os.access(crochet, os.X_OK), "un crochet doit être exécutable")
        texte = crochet.read_text(encoding="utf-8")
        self.assertNotIn("@PRODUIT@", texte)
        self.assertIn('outils="$racine/OBSIA"', texte)
        self.assertEqual(".githooks",
                         git(self.parent, "config", "core.hooksPath").stdout.strip())

    def test_le_crochet_arme_le_garde_de_secrets(self):
        """Le crochet posé mène à `avant-commit`, qui porte le refus de secret.

        Le gabarit est posé par l'installeur : c'est lui qui arme le garde. Le
        corps du garde vit dans le dépôt produit et suit ses mises à jour.
        """
        self.marquer_le_coffre()
        self.outiller_le_produit()
        self.profil()
        self.lancer("--appliquer")
        texte = (self.parent / ".githooks" / "pre-commit").read_text(encoding="utf-8")
        self.assertIn("avant-commit", texte)
        self.assertIn("forme de secret", texte)

    def test_le_distant_declare_devient_origin_sans_jamais_pousser(self):
        self.marquer_le_coffre()
        self.outiller_le_produit()
        self.profil_avec_distant()
        self.lancer("--appliquer")
        self.assertEqual("ssh://nas/volume/coffre.git",
                         git(self.parent, "remote", "get-url", "origin").stdout.strip())
        # L'installeur n'enregistre que l'adresse : aucun commit n'est fait.
        self.assertNotEqual(0, git(self.parent, "rev-parse", "--verify", "HEAD").returncode)

    def test_le_distant_declare_survit_a_une_reinstallation(self):
        self.marquer_le_coffre()
        self.outiller_le_produit()
        self.profil_avec_distant()
        self.lancer("--appliquer")
        self.lancer("--appliquer")
        self.assertIn("coffre_distant: ssh://nas/volume/coffre.git",
                      (self.racine / "obsia.local.yml").read_text(encoding="utf-8"))

    def test_un_profil_rempli_n_est_pas_ecrase_par_le_gabarit(self):
        """§7.1 : un profil rempli quelque part fait refuser la pose du gabarit."""
        self.marquer_le_coffre()
        self.outiller_le_produit()
        self.profil()
        ancien = self.parent / "-PERSONNELS" / "profil-utilisateur.md"
        ancien.parent.mkdir(parents=True, exist_ok=True)
        ancien.write_text("---\nschema: 1\n---\n\nQuelqu'un, et ce qu'il aime.\n",
                          encoding="utf-8")
        resultat = self.lancer("--appliquer")
        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertFalse((self.parent / "0-PERSONNELS" / "profil-utilisateur.md").exists())
        self.assertIn("migration", resultat.stderr)
        self.assertIn("Quelqu'un, et ce qu'il aime.",
                      ancien.read_text(encoding="utf-8"))

    def test_sans_marqueur_de_coffre_rien_n_est_outille(self):
        self.outiller_le_produit()
        self.profil()
        resultat = self.lancer("--appliquer")
        self.assertIn("pas de coffre parent reconnu", resultat.stdout)
        self.assertFalse((self.parent / ".git").exists())
        self.assertFalse((self.parent / ".gitignore").exists())
        self.assertFalse((self.parent / ".githooks").exists())

    def test_le_readme_de_la_memoire_dit_les_deux_memoires(self):
        """§6 : `0-MEMOIRES/` n'est pas qu'une archive, et son README le dit."""
        self.marquer_le_coffre()
        self.outiller_le_produit()
        self.profil()

        self.lancer("--appliquer")

        lireme = (self.parent / "0-MEMOIRES" / "README.md").read_text(encoding="utf-8")
        self.assertIn("préférences/", lireme)
        self.assertIn("expériences/", lireme)
        self.assertIn("gelé", lireme)
        self.assertIn("ne peut s'appeler", lireme)

    def test_les_preferences_ont_un_dossier_des_l_installation(self):
        """§6 : `0-MEMOIRES/préférences/` est posé même vide, et se retrouve."""
        self.marquer_le_coffre()
        self.outiller_le_produit()
        self.profil()

        self.lancer("--appliquer")

        self.assertTrue((self.parent / "0-MEMOIRES" / "préférences").is_dir())


if __name__ == "__main__":
    unittest.main()


class TestDossierPersonnel(BaseInstalleur):
    """Un clone posé directement dans le dossier personnel n'en fait pas un coffre."""

    def test_refus_sans_rien_ecrire(self):
        env = dict(os.environ, HOME=str(self.parent))
        resultat = subprocess.run(
            [sys.executable, "-B", str(INSTALLATEUR), "--racine", str(self.racine),
             "--appliquer", "--tout"],
            capture_output=True, text=True, check=False, env=env)
        self.assertEqual(1, resultat.returncode, resultat.stdout)
        self.assertIn("Rien n'a été écrit", resultat.stderr)
        for nom in ("0-PERSONNELS", "0-MEMOIRES", ".git", "AGENTS.md"):
            self.assertFalse((self.parent / nom).exists(), nom)
        self.assertFalse((self.racine / "obsia.local.yml").exists())

    def test_refus_en_copie_sans_creer_la_cible(self):
        env = dict(os.environ, HOME=str(self.parent))
        cible = self.parent / "OBSIA-copie"
        resultat = subprocess.run(
            [sys.executable, "-B", str(INSTALLATEUR), "--racine", str(self.racine),
             "--installer", str(cible), "--appliquer", "--tout"],
            capture_output=True, text=True, check=False, env=env)
        self.assertEqual(1, resultat.returncode, resultat.stdout)
        self.assertIn("--installer", resultat.stderr)
        self.assertFalse(cible.exists())
        self.assertFalse((self.parent / "AGENTS.md").exists())

    def test_detection(self):
        ancien = os.environ.get("HOME")
        self.addCleanup(os.environ.__setitem__, "HOME", ancien or "")
        os.environ["HOME"] = str(self.parent)
        self.assertTrue(INS.parent_est_le_dossier_personnel(self.racine))
        os.environ["HOME"] = str(self.racine)
        self.assertFalse(INS.parent_est_le_dossier_personnel(self.racine))
