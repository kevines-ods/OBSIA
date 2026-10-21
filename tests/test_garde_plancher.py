"""Le garde-plancher : ce qu'il attrape, et surtout ce qu'il ne doit pas attraper.

Les motifs surveillés sont **assemblés à l'exécution**. Écrits en clair dans ce
fichier, ils apparaîtraient dans le *diff* qui l'ajoute — et le garde, qui juge ce
*diff*, les signalerait. Un test du garde ne doit pas déclencher le garde.

Deux étages :

- les fonctions pures du garde (motifs, ratchet des seuils), importées
  directement : ce qu'une ligne isolée suffit à décider ;
- le garde entier lancé sur un dépôt git jetable : ce qui ne se lit que dans un
  *diff* — le fichier d'exemption lu sur la base, un changement de ce fichier, le
  code de sortie.
"""

import ast
import importlib.util
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
GARDE = RACINE / "IA" / "skills" / "plancher-qualite" / "scripts" / "garde_plancher.py"


def _charger():
    """Importe le garde comme module, sans lancer sa ligne de commande."""
    specification = importlib.util.spec_from_file_location("garde_plancher_essai", GARDE)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


GARDE_MODULE = _charger()


def _m(*bouts):
    """Assemble un motif : jamais littéral dans le source de ce fichier."""
    return "".join(bouts)


# Un motif nu neutralise la règle entière ; le même suivi d'un code, non.
NEUTRALISATION_NUE = "x = 1  " + _m("# no", "qa")
NEUTRALISATION_NOMMEE = "x = 1  " + _m("# no", "qa: E402")
TYPE_NOMME = "x = 1  " + _m("# type: ig", "nore[arg-type]")
SAUT_INCONDITIONNEL = _m("@unittest.sk", "ip", '("raison")')
# Le saut conditionnel est **réellement** conditionnel : sa condition dépend de
# la machine. Sous ce nom dormait `skipIf(True, …)` — un saut définitif —, et le
# test qui s'y appuyait affirmait que le garde n'avait rien à dire d'un test qui
# ne tourne jamais. C'était le trou, écrit comme voulu.
SAUT_CONDITIONNEL = _m("@unittest.sk", "ipIf(sys.platform == ", '"win32", "raison")')
# Un saut qui ne dépend de rien : le test ne tourne jamais, quel que soit le
# poste. Le motif de ligne ne le voit pas — il cherche un point, puis skip ou
# todo, puis une parenthèse, et `skipIf(` comme `skipTest(` ne s'y lisent pas ;
# c'est l'arbre qui le juge, et ce fichier-ci ne doit pas le déclencher — d'où
# l'assemblage.
SAUT_CONSTANT = _m("@unittest.sk", "ipIf(True, ", '"raison")')
SAUT_CONSTANT_INVERSE = _m("@unittest.sk", "ipUnless(False, ", '"raison")')
SAUT_NU = "        self." + _m("skip", "Test('raison')") + "\n"
RESTE_A_FAIRE = _m("TO", "DO: finir un truc")

# Un test qui reste, dont une assertion s'en va. Ces sources sont assemblées à
# l'exécution pour la raison déjà dite : le *diff* qui les ajoute ne doit pas
# être jugé par la règle qu'elles éprouvent.
#
# C'est ici que le motif de ligne se tait : dans « self.assertEqu », le `\b`
# final d'`ASSERTION` bute sur le `E` de `assertEqual`, la ligne retirée ne
# correspond à rien, et un test qui perd trois assertions sort du garde sans un
# mot. La règle juge donc **par test survivant**, sur l'arbre syntaxique.
TEST_AFFIRME = (
    "import unittest\n"
    "\n"
    "\n"
    "class TestEssai(unittest.TestCase):\n"
    "    def test_double_controle(self):\n"
    "        self.assertEqual(2 + 2, 4)\n"
    "        self.assertTrue(True)\n"
)
TEST_AMOINDRI = (
    "import unittest\n"
    "\n"
    "\n"
    "class TestEssai(unittest.TestCase):\n"
    "    def test_double_controle(self):\n"
    "        self.assertTrue(True)\n"
)
TEST_SANS_TEST = (
    "import unittest\n"
    "\n"
    "\n"
    "class TestEssai(unittest.TestCase):\n"
    "    def aider(self):\n"
    "        return True\n"
)
TEST_JAVASCRIPT = "expect(1).toBe(1);\nexpect(2).toBe(2);\n"
TEST_JAVASCRIPT_AMOINDRI = "expect(1).toBe(1);\n"
TEST_NU = "def test_x():\n    assert 2 + 2 == 4\n    assert True\n"
TEST_NU_AMOINDRI = "def test_x():\n    assert True\n"

# M-K du Contradicteur : les assertions vivent **hors des tests** — une fonction
# d'aide, une méthode qui n'est pas un test, le niveau module. Le cas est
# comparable — même fichier, mêmes noms, deux versions lisibles — donc la règle
# sait le faire, et une limite écrite ici serait un trou élargi, pas un trou
# fermé.
TEST_AVEC_AIDE = (
    "import unittest\n"
    "\n"
    "assert __name__ != \"\", \"au moins un nom\"\n"
    "\n"
    "\n"
    "def _aide_avec_assert(valeur):\n"
    "    assert valeur is not None\n"
    "    return valeur\n"
    "\n"
    "\n"
    "class TestEssai(unittest.TestCase):\n"
    "    def _verifie(self, valeur):\n"
    "        self.assertIsNotNone(valeur)\n"
    "        return valeur\n"
    "\n"
    "    def test_utilise_l_aide(self):\n"
    "        self.assertEqual(_aide_avec_assert(self._verifie(1)), 1)\n"
)
TEST_AIDE_SANS_ASSERT = (
    "import unittest\n"
    "\n"
    "\n"
    "def _aide_avec_assert(valeur):\n"
    "    return valeur\n"
    "\n"
    "\n"
    "class TestEssai(unittest.TestCase):\n"
    "    def _verifie(self, valeur):\n"
    "        return valeur\n"
    "\n"
    "    def test_utilise_l_aide(self):\n"
    "        self.assertEqual(_aide_avec_assert(self._verifie(1)), 1)\n"
)

# Un test perd une assertion, un autre en gagne deux : le fichier en compte une
# de plus. Compter par fichier — net ou brut — n'y verrait rien ; mesurer le
# total sur 120 commits a rendu 61 constats, contre 1 pour la comparaison test
# par test, dont un sur du travail honnête.
TEST_UN_PERD = (
    "import unittest\n"
    "\n"
    "\n"
    "class TestEssai(unittest.TestCase):\n"
    "    def test_double_controle(self):\n"
    "        self.assertEqual(2 + 2, 4)\n"
    "        self.assertTrue(True)\n"
    "\n"
    "    def test_gagne(self):\n"
    "        self.assertTrue(True)\n"
)
TEST_UN_AUTRE_GAGNE = (
    "import unittest\n"
    "\n"
    "\n"
    "class TestEssai(unittest.TestCase):\n"
    "    def test_double_controle(self):\n"
    "        self.assertTrue(True)\n"
    "\n"
    "    def test_gagne(self):\n"
    "        self.assertTrue(True)\n"
    "        self.assertEqual(len(\"ab\"), 2)\n"
    "        self.assertFalse(False)\n"
)

LIGNE_PLANCHER = "| Nombre de tests | **≥ 5** | un test | chaque poussée |"
LIGNE_PLAFOND = "| Noyau du contrat | **≤ 5** | un script | chaque poussée |"
PLANCHER = ("# Plancher\n"
            "\n"
            "| Dimension | Règle | Vérifié par | Quand |\n"
            "| --- | --- | --- | --- |\n"
            + LIGNE_PLANCHER + "\n")
EXCEPTION_TRACEE = "| E1 | seuil-desserre | CONSTRAINTS.md | consolidation |\n"


class TestLesMotifs(unittest.TestCase):
    """La ligne isolée : ce qui compte, et ce qui ne compte pas."""

    def test_attrape_une_neutralisation_nue(self):
        self.assertTrue(GARDE_MODULE.SUPPRESSIONS.search(NEUTRALISATION_NUE))

    def test_ne_signale_pas_une_neutralisation_nommee(self):
        self.assertIsNone(GARDE_MODULE.SUPPRESSIONS.search(NEUTRALISATION_NOMMEE))
        self.assertIsNone(GARDE_MODULE.SUPPRESSIONS.search(TYPE_NOMME))

    def test_attrape_un_saut_inconditionnel(self):
        self.assertTrue(GARDE_MODULE.TESTS_ALLEGES.search(SAUT_INCONDITIONNEL))

    def test_ne_signale_pas_un_saut_conditionnel(self):
        self.assertIsNone(GARDE_MODULE.TESTS_ALLEGES.search(SAUT_CONDITIONNEL))

    def test_le_motif_de_ligne_ne_voit_pas_un_saut_definitif(self):
        """`skipIf(True, …)` et `skipTest(…)` échappent au motif de ligne.

        `TESTS_ALLEGES` cherche un point, puis `skip` ou `todo`, puis une
        parenthèse : `skipIf(` et `skipTest(` ne s'y lisent pas, un point ne les
        précède pas. Un test sauté pour de bon passait donc au vert — c'est le
        motif incomplet du deuxième des cinq gestes. L'arbre les juge depuis
        (`TestLesSautsDefinitifs`) ; le motif de ligne reste sur ce qu'il sait
        lire, le saut littéral et le marqueur de travail en attente.
        """
        self.assertIsNone(GARDE_MODULE.TESTS_ALLEGES.search(SAUT_CONSTANT))
        self.assertIsNone(GARDE_MODULE.TESTS_ALLEGES.search(SAUT_NU.strip()))

    def test_attrape_du_travail_inacheve(self):
        self.assertTrue(GARDE_MODULE.INACHEVE.search(RESTE_A_FAIRE))


class TestLeRatchetDesSeuils(unittest.TestCase):
    """Un seuil qui disparaît, se renomme ou baisse est un constat."""

    FICHIER = "CONSTRAINTS.md"

    def _constats(self, avant, apres):
        return GARDE_MODULE.analyser_seuils(
            ajoutees=[(self.FICHIER, apres)],
            retirees=[(self.FICHIER, avant)])

    def test_un_chiffre_qui_baisse_desserre(self):
        constats = self._constats(LIGNE_PLANCHER,
                                  LIGNE_PLANCHER.replace("≥ 5", "≥ 4"))
        self.assertIn("seuil-desserre", [c[0] for c in constats])

    def test_un_chiffre_qui_monte_ne_dit_rien(self):
        constats = self._constats(LIGNE_PLANCHER,
                                  LIGNE_PLANCHER.replace("≥ 5", "≥ 6"))
        self.assertEqual(constats, [])

    def test_un_plafond_qui_monte_desserre(self):
        """Un `≤` ne monte pas : le relever, c'est relâcher la contrainte."""
        constats = self._constats(LIGNE_PLAFOND,
                                  LIGNE_PLAFOND.replace("≤ 5", "≤ 6"))
        self.assertIn("seuil-desserre", [c[0] for c in constats])

    def test_un_plafond_qui_baisse_ne_dit_rien(self):
        """Un `≤` qui descend resserre : ce n'est pas un constat."""
        constats = self._constats(LIGNE_PLAFOND,
                                  LIGNE_PLAFOND.replace("≤ 5", "≤ 4"))
        self.assertEqual(constats, [])

    def test_un_millier_reformate_n_est_pas_un_constat(self):
        """« 4 560 » et « 4560 » sont le même nombre : l'espace ôté n'est pas un seuil qui bouge."""
        avant = "| Noyau du contrat | **≤ 4 560 mots** | un script | chaque poussée |"
        apres = "| Noyau du contrat | **≤ 4560 mots** | un script | chaque poussée |"
        self.assertEqual(self._constats(avant, apres), [])

    def test_le_constat_montre_les_nombres_entiers(self):
        """Le constat dit « 4 560 → 5 000 », jamais « 4 → 5 »."""
        avant = "| Noyau du contrat | **≤ 4 560 mots** | un script | chaque poussée |"
        apres = "| Noyau du contrat | **≤ 5 000 mots** | un script | chaque poussée |"
        self.assertEqual(self._constats(avant, apres),
                         [("seuil-desserre", self.FICHIER, "4 560 → 5 000")])

    def test_un_relevement_ecrit_avec_une_espace_fine_est_un_constat(self):
        """U+2009 entre les milliers : « 5 000 » reste un nombre, pas « 5 » puis « 000 ».

        Ne connaître que l'espace ordinaire ferait passer ce relèvement en
        silence — le plafond monterait sans que rien ne le dise.
        """
        avant = "| Noyau du contrat | **≤ 4 560 mots** | un script | chaque poussée |"
        apres = "| Noyau du contrat | **≤ 5\u2009000 mots** | un script | chaque poussée |"
        self.assertEqual(self._constats(avant, apres),
                         [("seuil-desserre", self.FICHIER, "4 560 → 5\u2009000")])

    def test_une_tabulation_entre_les_milliers_se_lit_aussi(self):
        """La tabulation sépare les milliers comme l'espace."""
        avant = "| Noyau du contrat | **≤ 4\t560 mots** | un script | chaque poussée |"
        apres = "| Noyau du contrat | **≤ 5\t000 mots** | un script | chaque poussée |"
        self.assertEqual(self._constats(avant, apres),
                         [("seuil-desserre", self.FICHIER, "4\t560 → 5\t000")])

    def test_une_ligne_de_seuil_disparue_est_un_constat(self):
        constats = GARDE_MODULE.analyser_seuils(ajoutees=[],
                                                retirees=[(self.FICHIER, LIGNE_PLANCHER)])
        self.assertIn("seuil-disparu", [c[0] for c in constats])

    def test_un_libelle_renomme_est_un_constat(self):
        constats = self._constats(LIGNE_PLANCHER,
                                  LIGNE_PLANCHER.replace("Nombre de tests",
                                                         "Nombre de cas"))
        self.assertIn("seuil-disparu", [c[0] for c in constats])

    def test_un_seuil_ajoute_a_la_meme_ligne_est_un_constat(self):
        """« ≥ 5 » devenu « ≥ 5 lignes, et ≥ 4 % » : le desserrement traversait le garde.

        La ligne d'après porte **deux** nombres là où celle d'avant en portait
        un. L'ancien appariement comparait les deux premiers — 5 contre 5,
        égaux — puis tombait sur le second nombre de la ligne d'après, qui n'avait
        pas de vis-à-vis, et passait au suivant : **aucun constat**. Le vrai
        seuil, lui, était descendu. Deux lignes ne s'apparient plus quand elles
        ne portent pas autant de nombres ; le garde refuse et le dit.
        """
        avant = "| Couverture | **≥ 5 %** des instructions | un script | chaque poussée |"
        apres = ("| Couverture | **≥ 5 lignes** par tranche, et **≥ 4 %** "
                 "des instructions | un script | chaque poussée |")
        constats = self._constats(avant, apres)
        self.assertEqual([c[0] for c in constats], ["seuil-modifie"])
        self.assertEqual(constats[0][2], "5 → 5 4")

    def test_un_seuil_retire_de_la_ligne_est_un_constat(self):
        """L'inverse : la ligne d'après en porte un de moins, et c'est un constat aussi."""
        avant = ("| Couverture | **≥ 5 lignes** par tranche, et **≥ 4 %** "
                 "des instructions | un script | chaque poussée |")
        apres = "| Couverture | **≥ 5 %** des instructions | un script | chaque poussée |"
        constats = self._constats(avant, apres)
        self.assertEqual([c[0] for c in constats], ["seuil-modifie"])
        self.assertEqual(constats[0][2], "5 4 → 5")

    def test_apparier_refuse_ne_perd_aucun_constat_deja_vu(self):
        """Le refus d'apparier ne peut qu'ajouter : un seuil qui baisse reste vu.

        C'est la propriété qui compte — le correctif ferme un trou sans en
        ouvrir un. Un chiffre qui descend dans une ligne dont le nombre de
        nombres ne bouge pas garde exactement le verdict d'avant.
        """
        constats = self._constats(LIGNE_PLANCHER,
                                  LIGNE_PLANCHER.replace("≥ 5", "≥ 4"))
        self.assertEqual(constats,
                         [("seuil-desserre", self.FICHIER, "5 → 4")])

    def test_un_seuil_sans_comparateur_reste_protege(self):
        """« **100 %** couverts : chaque contrôle a **≥ 1** test » — deux nombres, deux seuils.

        Le second porte un `≥`, le premier non, et pourtant **100 %** est une
        barre : la descendre à 90 % est un desserrement. Ne protéger que les
        nombres introduits par un comparateur — la piste qu'on m'avait
        suggérée — aurait laissé passer celui-là. C'est pourquoi le garde
        continue de surveiller **tous** les nombres de la ligne.
        """
        avant = ("| Contrôles de la porte | **100 %** couverts : chaque contrôle "
                 "a **≥ 1** test qui le nomme | un script | chaque poussée |")
        apres = avant.replace("**100 %**", "**90 %**")
        constats = self._constats(avant, apres)
        self.assertEqual(constats,
                         [("seuil-desserre", self.FICHIER, "100 → 90")])

    def test_ajouter_un_seuil_plus_strict_est_un_constat_annonce(self):
        """Une ligne qui gagne une borne plus stricte est un constat — assumé.

        `seuil-modifie`, direction indéterminée : deux nombres d'une même ligne
        ne mesurent pas forcément la même chose (« 5 lignes » et « 5 % »), et
        le garde ne devine pas ce que le chiffre nouveau mesure. C'est le seul
        geste bruyant qui reste, et le silence serait pire : une exception
        tracée ramène le cas en avertissement si la forme est légitime.
        """
        avant = "| Couverture | **≥ 5 %** des instructions | un script | chaque poussée |"
        apres = ("| Couverture | **≥ 5 %** des instructions, et **≥ 9** par "
                 "tranche | un script | chaque poussée |")
        constats = self._constats(avant, apres)
        self.assertEqual([c[0] for c in constats], ["seuil-modifie"])

    def test_un_nombre_insere_avant_le_seuil_n_est_pas_un_desserrement(self):
        """Un compte nouveau glissé avant le seuil : le seuil n'a pas bougé.

        Les nombres sont appariés **rang par rang**. Que la cellule « Vérifié
        par » passe de « python3 … » à « python … » — le 3 disparaît — et qu'un
        compte apparaisse avant le seuil, et les deux lignes portent toujours
        deux nombres : le garde compare alors 87 à 12 et annonce un desserrement
        qui n'a pas eu lieu. Un faux constat se conteste, donc se trace, et
        l'exception qu'on lui oppose fait taire pour ce fichier tous les vrais.
        Rien ne dit quel nombre remplace lequel : refuser d'apparier, et le dire.
        """
        avant = ("| Couverture | **≥ 87 %** des instructions | python3 tests/du-projet.py "
                 "| fin de tranche |")
        apres = ("| Couverture | **12 zones** sans test, **≥ 87 %** des instructions "
                 "| python tests/du-projet.py | fin de tranche |")
        constats = self._constats(avant, apres)
        self.assertEqual([c[0] for c in constats], ["seuil-modifie"])

    def test_retourner_le_comparateur_est_un_constat(self):
        """« ≥ 5 » devenu « ≤ 5 » : le chiffre n'a pas bougé, la barre si.

        Le nombre est identique, au même rang : l'appariement par position ne
        voit rien, et le garde se tait. Le lecteur du plancher, lui, refuse la
        ligne — un plafond n'est pas un plancher. Le garde laissait donc passer
        un seuil qui cesse d'en être un sans le dire. Le comparateur fait partie
        du seuil : quand il change, c'est un constat, et il se voit.
        """
        constats = self._constats(LIGNE_PLANCHER, LIGNE_PLANCHER.replace("≥ 5", "≤ 5"))
        self.assertEqual([c[0] for c in constats], ["seuil-modifie"])
        self.assertEqual(constats[0][2], "≥ 5 → ≤ 5")

    def test_un_desserrement_ne_se_cache_pas_derriere_un_relevement(self):
        """Deux seuils sur une ligne : le premier monte, le second baisse.

        La boucle s'arrête au **premier nombre qui diffère**, qu'il ait donné
        un constat ou non. Un premier seuil relevé — jamais un constat — suffit
        donc à la faire sortir avant le second, qui baisse pour de bon. Chaque
        nombre est examiné : le desserrement se voit, où qu'il soit sur la ligne.
        """
        avant = ("| Couverture | **≥ 5 %** des instructions et **≥ 9** cas par tranche "
                 "| un script | chaque poussée |")
        apres = ("| Couverture | **≥ 7 %** des instructions et **≥ 2** cas par tranche "
                 "| un script | chaque poussée |")
        constats = self._constats(avant, apres)
        self.assertEqual([c[0] for c in constats], ["seuil-desserre"])
        self.assertEqual(constats[0][2], "9 → 2")


class TestLesExceptions(unittest.TestCase):
    """Une exception tracée couvre son constat ; une ligne incomplète, non."""

    def test_une_exception_couvre_un_constat_de_meme_regle_et_fichier(self):
        constat = ("seuil-desserre", "CONSTRAINTS.md", "5 → 4")
        self.assertTrue(GARDE_MODULE.couverte(
            constat, [("seuil-desserre", "CONSTRAINTS.md")]))

    def test_une_exception_ne_couvre_pas_une_autre_regle(self):
        constat = ("test-supprime", "tests/x.py", "")
        self.assertFalse(GARDE_MODULE.couverte(
            constat, [("seuil-desserre", "tests/x.py")]))

    def test_une_ligne_incomplete_n_est_pas_une_exception(self):
        self.assertIsNone(GARDE_MODULE._ligne_exception(
            "| E2 | seuil-desserre | CONSTRAINTS.md |"))
        self.assertIsNone(GARDE_MODULE._ligne_exception(
            "une exception : ne pas tenir compte de ce test"))


class _DepotJetable(unittest.TestCase):
    """Un dépôt git minimal, créé à l'exécution et détruit aussitôt."""

    def setUp(self):
        self._bac = tempfile.TemporaryDirectory()
        self.depot = Path(self._bac.name)
        self._git("init", "-q")
        self._git("config", "user.email", "garde@exemple.test")
        self._git("config", "user.name", "garde")
        self._git("config", "commit.gpgsign", "false")
        self.ecrire("lisez-moi.txt", "base\n")
        self.committer("base")

    def tearDown(self):
        self._bac.cleanup()

    def _git(self, *args):
        fait = subprocess.run(["git", "-C", str(self.depot)] + list(args),
                              capture_output=True, text=True)
        self.assertEqual(fait.returncode, 0, fait.stderr)
        return fait.stdout

    def ecrire(self, chemin, contenu):
        cible = self.depot / chemin
        cible.parent.mkdir(parents=True, exist_ok=True)
        cible.write_text(contenu, encoding="utf-8")

    def committer(self, message="base"):
        self._git("add", "-A")
        self._git("commit", "-q", "-m", message)
        self.base = self._git("rev-parse", "HEAD").strip()
        return self.base

    def juger(self, base=None):
        """Juge l'arbre contre `base` (par défaut, le dernier commit posé).

        Une base explicite sert à juger une tête qui a **déjà** committé :
        l'exemption doit se lire sur ce qui précède, jamais sur la tête.
        """
        fait = subprocess.run(
            [sys.executable, str(GARDE), "--depot", str(self.depot),
             "--base", base or self.base],
            capture_output=True, text=True)
        return fait.returncode, fait.stdout + fait.stderr


class TestLeBudgetDeLectures(unittest.TestCase):
    """Le garde se paie lui-même : ce qu'il lit entre dans un budget, et il le dit.

    Un garde qui relit tout l'arbre à chaque passage finit désactivé — ou, pire,
    il ralentit la boucle de celui qui doit le faire tourner. Le coût est donc
    chiffré d'avance, et le garde **imprime son compte** : un dépassement se voit
    au lieu de se deviner.

    Ce plafond ne s'acquitte pas. Une exception `E<n>` lève un constat sur un
    fichier précis ; un budget qu'on peut lever ligne par ligne n'est pas un
    budget, c'est une décoration.
    """

    def test_le_plafond_se_calcule_sur_les_fichiers_touches(self):
        """`2 × modifiés + 1 × (ajoutés + supprimés) + 2` lectures, pas une de plus.

        Deux par fichier modifié : le garde lit la version de la base **et**
        celle de l'arbre, c'est ce qui lui permet de comparer les assertions.
        Une par fichier ajouté ou supprimé : il n'y a qu'une version à lire. Et
        deux lectures fixes, celles sans lesquelles il ne sait ni ce qu'il doit
        ignorer (`.plancherignore` sur la base) ni ce qu'il doit excepter
        (`CONSTRAINTS.md` dans l'arbre).
        """
        self.assertEqual(GARDE_MODULE.budget_de_lectures(modifies=3, ajoutes=1,
                                                         supprimes=2),
                         2 * 3 + 1 + 2 + 2)

    def test_un_depassement_de_budget_n_est_pas_acquitte(self):
        """Aucune exception tracée ne couvre `budget-de-lectures`, même `*`."""
        constat = ("budget-de-lectures", "garde_plancher.py",
                   "9 lectures pour un plafond de 6")
        exceptions = [("*", "*"), ("budget-de-lectures", "*")]
        self.assertFalse(GARDE_MODULE.couverte(constat, exceptions))


class TestLeCompteDeLecturesImprime(_DepotJetable):
    """Le compte est public : c'est ce qui rend le budget vérifiable."""

    def test_le_garde_imprime_son_nombre_de_lectures(self):
        code, sortie = self.juger()
        self.assertEqual(code, 0, sortie)
        self.assertRegex(sortie, r"\d+ lecture\(s\) pour un plafond de \d+")


class TestLeGardeSurUnDepotJetable(_DepotJetable):
    """Le garde entier, sur un *diff* réel."""

    def test_signale_un_test_allege_de_deux_facons(self):
        """Deux règles, un dépôt jetable — et deux constats indépendants.

        Un dépôt jetable coûte onze processus sous le compteur du banc, et la
        marge du plafond n'en laisse plus cinq. Les deux `assertIn` restent
        séparés : lequel tombe dit laquelle des deux règles a lâché. La
        neutralisation nue et le saut définitif ont le même sens ici — un test
        qui ne prouve plus rien —, c'est ce qui rend le partage lisible.
        """
        self.ecrire("exemple.py", NEUTRALISATION_NUE + "\n")
        self.ecrire("tests/test_saute.py",
                    "import unittest\n"
                    "class TestSaute(unittest.TestCase):\n"
                    "    def test_jamais(self):\n"
                    + SAUT_NU
                    + "        self.assertEqual(1, 1)\n")
        code, sortie = self.juger()
        self.assertEqual(code, 1, sortie)
        self.assertIn("verificateur-fait-taire", sortie)
        self.assertIn("test-allege", sortie)
        self.assertIn("skipTest : TestSaute.test_jamais", sortie)

    def test_ne_signale_pas_une_neutralisation_nommee(self):
        self.ecrire("exemple.py", NEUTRALISATION_NOMMEE + "\n")
        code, sortie = self.juger()
        self.assertEqual(code, 0, sortie)

    def test_ne_signale_pas_un_saut_conditionnel(self):
        self.ecrire("exemple.py", SAUT_CONDITIONNEL + "\n")
        code, sortie = self.juger()
        self.assertEqual(code, 0, sortie)

    def test_un_fichier_accentue_nouveau_est_juge(self):
        """Un chemin non ASCII ne se dérobe pas au garde.

        Sans `core.quotePath=false`, git **cite** le nom (`"ex\\303\\251mple.py"`) :
        le chemin restitué n'existe pas, `diff --no-index` échoue sur un fichier
        nouveau, et la neutralisation qu'il porte passe en silence.
        """
        self.ecrire("exémple.py", NEUTRALISATION_NUE + "\n")
        code, sortie = self.juger()
        self.assertEqual(code, 1, sortie)
        self.assertIn("verificateur-fait-taire", sortie)
        self.assertIn("exémple.py", sortie, sortie)

    def test_un_test_accentue_supprime_est_un_constat(self):
        """Même piège sur un nom **suivi** puis supprimé : `--name-status` le cite.

        `test_écrit.py` commence bien par `test_` — mais précédé d'un guillemet
        quand git le cite, le motif `(^|/)test_` ne le voit plus.
        """
        self.ecrire("test_écrit.py", "def test_x():\n    assert True\n")
        self.committer("un test accentué")
        base = self.base
        (self.depot / "test_écrit.py").unlink()
        self.committer("on le supprime")
        code, sortie = self.juger(base=base)
        self.assertEqual(code, 1, sortie)
        self.assertIn("test-supprime", sortie)

    def test_un_fichier_a_retour_a_la_ligne_nouveau_est_juge(self):
        """`ls-files -z` : le nom arrive **entier**, séparé par des NUL.

        Sans `-z`, la sortie se découpe en lignes : « neutralise » puis
        « la_ci.py » — deux chemins qui n'existent pas. Leur contenu n'est jamais
        lu par `--no-index`, et la neutralisation qu'ils portent dort. Un retour
        à la ligne, git le cite toujours (comme un antislash ou un guillemet),
        `core.quotePath=false` n'y peut rien : seul `-z` donne le chemin brut.
        """
        self.ecrire("neutralise\nla_ci.py", NEUTRALISATION_NUE + "\n")
        code, sortie = self.juger()
        self.assertEqual(code, 1, sortie)
        self.assertIn("verificateur-fait-taire", sortie)

    def test_un_test_au_nom_portant_une_tabulation_supprime_est_un_constat(self):
        """`--name-status -z` : l'état et le chemin ne se coupent plus.

        Sans `-z`, git cite le nom (une tabulation le force) : le champ lu devient
        `"test_avec\\ttab.py"`, guillemet de tête compris, et le motif `(^|/)test_`
        — qui exige « test_ » au début — ne le voit plus. Le test supprimé passe
        alors inaperçu.
        """
        self.ecrire("test_avec\ttab.py", "def test_x():\n    assert True\n")
        self.committer("un test au nom tabulé")
        base = self.base
        (self.depot / "test_avec\ttab.py").unlink()
        self.committer("on le supprime")
        code, sortie = self.juger(base=base)
        self.assertEqual(code, 1, sortie)
        self.assertIn("test-supprime", sortie)

    def test_lit_le_fichier_d_exemption_sur_la_base(self):
        self.ecrire(".plancherignore", "exemple.py\n")
        self.committer("exemption")
        self.ecrire("exemple.py", NEUTRALISATION_NUE + "\n")
        code, sortie = self.juger()
        self.assertEqual(code, 0, sortie)

    def test_modifier_le_fichier_d_exemption_est_un_constat(self):
        self.ecrire(".plancherignore", "exemple.py\n")
        code, sortie = self.juger()
        self.assertEqual(code, 1, sortie)
        self.assertIn("plancherignore-modifie", sortie)

    def test_une_exemption_ajoutee_sur_la_tete_ne_couvre_rien(self):
        """Le `.plancherignore` lu sur la tête ne doit pas blanchir la tête.

        Une PR qui ajoute son propre fichier d'exemption *et* le fichier fautif
        ne doit pas se couvrir elle-même : la base n'a pas encore d'exemption,
        donc le constat sur le fichier fautif reste levé. Juger contre la tête
        (déjà commitée ici) ferait disparaître `verificateur-fait-taire` et ce
        test tomberait.
        """
        base = self.base                       # avant l'exemption
        self.ecrire(".plancherignore", "exemple.py\n")
        self.ecrire("exemple.py", NEUTRALISATION_NUE + "\n")
        self.committer("exemption et fichier fautif")
        code, sortie = self.juger(base=base)
        self.assertEqual(code, 1, sortie)
        self.assertIn("verificateur-fait-taire", sortie)

    def test_modifier_un_plancherignore_deja_suivi_est_un_constat(self):
        """Un `.plancherignore` suivi sur la base puis modifié se voit dans le
        `--name-status` du diff, pas dans la liste des fichiers non suivis.

        Restreindre cette branche aux ajouts (`A`) laisserait passer une
        exemption élargie par une modification, et ce test tomberait.
        """
        self.ecrire(".plancherignore", "inexistant.py\n")
        self.committer("exemption suivie")
        base = self.base                       # l'exemption, sur la base
        self.ecrire(".plancherignore", "inexistant.py\nexemple.py\n")
        self.committer("exemption elargie")
        code, sortie = self.juger(base=base)
        self.assertEqual(code, 1, sortie)
        self.assertIn("plancherignore-modifie", sortie)

    def test_une_ligne_de_seuil_disparue_est_un_constat(self):
        self.ecrire("CONSTRAINTS.md", PLANCHER)
        self.committer("plancher")
        self.ecrire("CONSTRAINTS.md", PLANCHER.replace(LIGNE_PLANCHER, ""))
        code, sortie = self.juger()
        self.assertEqual(code, 1, sortie)
        self.assertIn("seuil-disparu", sortie)

    def test_baisser_un_seuil_sans_exception_est_un_constat(self):
        self.ecrire("CONSTRAINTS.md", PLANCHER)
        self.committer("plancher")
        self.ecrire("CONSTRAINTS.md", PLANCHER.replace("≥ 5", "≥ 4"))
        code, sortie = self.juger()
        self.assertEqual(code, 1, sortie)
        self.assertIn("seuil-desserre", sortie)

    def test_baisser_un_seuil_avec_exception_est_signale_sans_echouer(self):
        self.ecrire("CONSTRAINTS.md", PLANCHER)
        self.committer("plancher")
        self.ecrire("CONSTRAINTS.md",
                    PLANCHER.replace("≥ 5", "≥ 4") + "\n" + EXCEPTION_TRACEE)
        code, sortie = self.juger()
        self.assertEqual(code, 0, sortie)
        self.assertIn("avertissement", sortie)


class TestUneAssertionQuiDisparait(_DepotJetable):
    """Un test qui reste en perdant une assertion : ce que la règle voit, et où elle s'arrête."""

    def test_une_assertion_retiree_d_un_test_qui_reste_est_un_constat(self):
        """`self.assertEqual` s'en va, le test demeure : le garde doit le dire.

        `ASSERTION` cherche `\\bassert\\b`, et dans `self.assertEqual(…)` le `\\b`
        final bute sur le `E` : la ligne retirée ne correspond à rien. Le test
        survit, une de ses assertions est partie, et le garde se taît — un
        verdict qui protège pour le mauvais motif. La comparaison se fait donc
        par test **survivant**, sur l'arbre syntaxique, et elle nomme le test.
        """
        self.ecrire("tests/test_essai.py", TEST_AFFIRME)
        base = self.committer("un test qui affirme")
        self.ecrire("tests/test_essai.py", TEST_AMOINDRI)

        code, sortie = self.juger(base=base)

        self.assertEqual(code, 1, sortie)
        self.assertIn("assertion-retiree", sortie)
        self.assertIn("test_double_controle", sortie, sortie)
        self.assertIn("2 → 1", sortie, sortie)

    def test_une_assertion_nue_retiree_reste_un_constat(self):
        """`assert x` nu : la règle de ligne le voyait déjà, l'arbre le voit aussi.

        Le cas est ici pour que le changement de méthode ne perde rien de ce que
        l'ancienne méthode attrapait.
        """
        self.ecrire("tests/test_nu.py", TEST_NU)
        base = self.committer("un test nu")
        self.ecrire("tests/test_nu.py", TEST_NU_AMOINDRI)

        code, sortie = self.juger(base=base)

        self.assertEqual(code, 1, sortie)
        self.assertIn("assertion-retiree", sortie)

    def test_un_test_javascript_perd_toujours_son_assertion(self):
        """Hors Python il n'y a pas d'arbre à lire : la règle de ligne reste.

        La remplacer partout aurait rendu le garde muet sur les dépôts
        JavaScript, où `expect(` ne se lit pas autrement.
        """
        self.ecrire("tests/essai.spec.js", TEST_JAVASCRIPT)
        base = self.committer("un test javascript")
        self.ecrire("tests/essai.spec.js", TEST_JAVASCRIPT_AMOINDRI)

        code, sortie = self.juger(base=base)

        self.assertEqual(code, 1, sortie)
        self.assertIn("assertion-retiree", sortie)

    def test_une_assertion_retiree_d_une_fonction_d_aide_est_un_constat(self):
        """M-K du Contradicteur : l'aide, la méthode non-test et le module perdent leur assertion.

        La première formulation de la règle par arbre ne regardait que les
        `def test_*` : une assertion retirée d'une aide devenait invisible, alors
        que la règle de ligne, elle, la voyait — un `assert` nu. La portée du
        contrôle avait donc **rétréci** en s'élargissant aux `self.assertX`.
        Le cas est comparable : même fichier, mêmes noms, deux versions lisibles.

        Les trois portées sont dans le même cas pour une raison de budget : trois
        dépôts jetables de plus coûteraient une trentaine de processus, et la
        marge du plafond n'en laisse plus cinq.
        """
        self.ecrire("tests/test_essai.py", TEST_AVEC_AIDE)
        base = self.committer("une aide qui affirme")
        self.ecrire("tests/test_essai.py", TEST_AIDE_SANS_ASSERT)

        code, sortie = self.juger(base=base)

        self.assertEqual(code, 1, sortie)
        self.assertIn("assertion-retiree", sortie)
        self.assertIn("_aide_avec_assert : 1 → 0", sortie, sortie)
        self.assertIn("TestEssai._verifie : 1 → 0", sortie, sortie)
        self.assertIn("<module> : 1 → 0", sortie, sortie)
        self.assertNotIn("test_utilise_l_aide", sortie, sortie)

    def test_une_aide_reformulee_sans_perte_reste_verte(self):
        """Même nombre d'assertions, un message en plus, un ordre changé : rien n'a été retiré.

        Sans ce cas, la règle élargie pourrait signaler toute aide touchée — et un
        contrôle qui crie sur un remaniement honnête finit desserré, puis tracé en
        exception.
        """
        self.ecrire("tests/test_essai.py", TEST_AVEC_AIDE)
        base = self.committer("une aide qui affirme")
        self.ecrire("tests/test_essai.py", TEST_AVEC_AIDE.replace(
            "    assert valeur is not None\n",
            "    assert isinstance(valeur, int), \"un entier attendu\"\n"
            "    assert valeur is not None\n"))

        code, sortie = self.juger(base=base)

        self.assertEqual(code, 0, sortie)
        self.assertNotIn("assertion-retiree", sortie)

    def test_une_assertion_perdue_ne_se_cache_pas_derriere_une_autre_gagnee(self):
        """Le fichier gagne une assertion et en perd une : le test amoindri se nomme.

        C'est ce cas qui sépare la comparaison **test par test** du compte par
        fichier. Sur 120 commits, le compte net par fichier a rendu 61 constats
        et la comparaison par test 1 : le premier se tait quand un test perd ce
        qu'un autre gagne, et c'est exactement l'échange qu'un allègement
        discret utilise. Ce que la règle protège, c'est **ce test-là**, pas le
        total du fichier.
        """
        self.ecrire("tests/test_essai.py", TEST_UN_PERD)
        base = self.committer("un test qui perd, un autre qui gagne")
        self.ecrire("tests/test_essai.py", TEST_UN_AUTRE_GAGNE)

        code, sortie = self.juger(base=base)

        self.assertEqual(code, 1, sortie)
        self.assertIn("test_double_controle", sortie, sortie)
        self.assertNotIn("test_gagne :", sortie, sortie)

    def test_un_test_renomme_ne_perd_pas_d_assertion(self):
        """Le corps est intact, seul le nom change : rien n'a été retiré.

        Comparer par nom de test a rendu **1** constat sur 120 commits, là où la
        règle de ligne en rendait 0, le compte par fichier 61 et le compte net
        par diff 136. Un renommage ne doit pas devenir un constat : une règle
        qui crie sur un travail honnête finit tracée en exception, et elle ne
        protège plus rien.
        """
        self.ecrire("tests/test_essai.py", TEST_AFFIRME)
        base = self.committer("un test qui affirme")
        self.ecrire("tests/test_essai.py",
                    TEST_AFFIRME.replace("test_double_controle",
                                         "test_double_controle_renomme"))

        code, sortie = self.juger(base=base)

        self.assertEqual(code, 0, sortie)
        self.assertNotIn("assertion-retiree", sortie)

    def test_un_test_efface_entierement_reste_hors_de_portee_de_la_regle(self):
        """La règle ne juge que les tests qui **restent** — limite mesurée, assumée.

        Détecter « un `def test_` a disparu » a été mesuré **avant** d'être
        construit : 9 occurrences sur les 120 derniers commits, pour un seuil
        fixé d'avance à 3, dont deux renommages purs — un constat sur neuf serait
        tombé sur du travail honnête. Le contrôle n'a donc pas été construit, et
        ce test fige la limite au lieu de la découvrir.
        """
        self.ecrire("tests/test_essai.py", TEST_AFFIRME)
        base = self.committer("un test qui affirme")
        self.ecrire("tests/test_essai.py", TEST_SANS_TEST)

        code, sortie = self.juger(base=base)

        self.assertEqual(code, 0, sortie)
        self.assertNotIn("assertion-retiree", sortie)


class TestLesSautsDefinitifs(unittest.TestCase):
    """Un test qu'on n'exécute plus s'allège sans perdre une seule assertion.

    C'est le deuxième des cinq gestes, et son motif était incomplet : ni
    `skipIf(` ni `skipTest(` ne tombent sous le motif de ligne. Ce qui se lit
    dans l'arbre, c'est la **condition** du saut et sa **place** — un saut qui ne
    dépend de rien, ou un saut nu, est un test qui ne tourne jamais.
    """

    def _trouves(self, source):
        return GARDE_MODULE.tests_jamais_executes(ast.parse(textwrap.dedent(source)))

    def test_un_skip_if_a_condition_constante_est_releve(self):
        trouves = self._trouves("""
            import unittest
            class TestEssai(unittest.TestCase):
                @unittest.skipIf(True, "raison")
                def test_x(self):
                    self.assertEqual(1, 1)
            """)
        self.assertEqual([(nom, forme) for nom, forme, _ in trouves],
                         [("TestEssai.test_x", "skipIf")])

    def test_un_skip_unless_a_condition_constante_est_releve(self):
        trouves = self._trouves("""
            import unittest
            class TestEssai(unittest.TestCase):
                @unittest.skipUnless(False, "raison")
                def test_x(self):
                    self.assertEqual(1, 1)
            """)
        self.assertEqual([(nom, forme) for nom, forme, _ in trouves],
                         [("TestEssai.test_x", "skipUnless")])

    def test_une_negation_de_constante_est_une_condition_constante(self):
        trouves = self._trouves("""
            import unittest
            class TestEssai(unittest.TestCase):
                @unittest.skipIf(not True, "raison")
                def test_x(self):
                    self.assertEqual(1, 1)
            """)
        self.assertEqual([(nom, forme) for nom, forme, _ in trouves],
                         [("TestEssai.test_x", "skipIf")])

    def test_un_skip_test_nu_est_releve(self):
        trouves = self._trouves("""
            import unittest
            class TestEssai(unittest.TestCase):
                def test_x(self):
                    self.skipTest("raison")
                    self.assertEqual(1, 1)
            """)
        self.assertEqual([(nom, forme) for nom, forme, _ in trouves],
                         [("TestEssai.test_x", "skipTest")])

    def test_un_skip_test_sous_condition_reste_tranquille(self):
        """`if not shutil.which("git")` : le test tourne quand il le peut."""
        trouves = self._trouves("""
            import shutil, unittest
            class TestEssai(unittest.TestCase):
                def test_x(self):
                    if not shutil.which("git"):
                        self.skipTest("pas de git ici")
                    self.assertEqual(1, 1)
            """)
        self.assertEqual(trouves, [])

    def test_un_skip_if_sur_l_environnement_reste_tranquille(self):
        trouves = self._trouves("""
            import sys, unittest
            class TestEssai(unittest.TestCase):
                @unittest.skipIf(sys.platform == "win32", "raison")
                def test_x(self):
                    self.assertEqual(1, 1)
            """)
        self.assertEqual(trouves, [])

    def test_une_aide_qui_saute_n_est_pas_un_test(self):
        """Seule une méthode de test est jugée : une aide acquitterait à tort."""
        trouves = self._trouves("""
            import unittest
            class TestEssai(unittest.TestCase):
                def _aide(self):
                    self.skipTest("raison")
                def test_x(self):
                    self.assertEqual(1, 1)
            """)
        self.assertEqual(trouves, [])

    def test_une_classe_qui_n_est_pas_un_testcase_n_est_pas_jugee(self):
        trouves = self._trouves("""
            class PasUnTest:
                def test_x(self):
                    self.skipTest("raison")
            """)
        self.assertEqual(trouves, [])

    def test_la_portee_est_nommee_par_son_chemin(self):
        trouves = self._trouves("""
            import unittest
            class Dehors(unittest.TestCase):
                class Dedans(unittest.TestCase):
                    def test_x(self):
                        self.skipTest("raison")
            """)
        self.assertEqual([nom for nom, _, _ in trouves], ["Dehors.Dedans.test_x"])


class TestLesLignesAjoutees(unittest.TestCase):
    """Le diff dit quelles lignes sont neuves ; encore faut-il les compter.

    `--unified=0` ne rend aucun contexte : le hunk donne le premier numéro du
    côté droit, et chaque `+` prend le suivant. Sans ce compte, un saut ancien,
    dans un fichier qu'on ne fait que traverser, serait mis au compte du
    changement.
    """

    def test_les_numeros_suivent_le_hunk(self):
        diff = textwrap.dedent("""\
            +++ b/tests/test_x.py
            @@ -3,0 +4,2 @@
            +        self.assertEqual(1, 1)
            +        self.assertEqual(2, 2)
            """)
        self.assertEqual(GARDE_MODULE.lignes_ajoutees(diff), {"tests/test_x.py": {4, 5}})

    def test_une_suppression_ne_compte_pas_comme_ajout(self):
        diff = textwrap.dedent("""\
            +++ b/tests/test_x.py
            @@ -7 +8 @@
            -        self.assertTrue(True)
            +        self.assertEqual(1, 1)
            """)
        self.assertEqual(GARDE_MODULE.lignes_ajoutees(diff), {"tests/test_x.py": {8}})

    def test_un_fichier_neuf_part_de_la_ligne_un(self):
        diff = textwrap.dedent("""\
            +++ b/tests/test_neuf.py
            @@ -0,0 +1,2 @@
            +import unittest
            +class TestNeuf(unittest.TestCase): pass
            """)
        self.assertEqual(GARDE_MODULE.lignes_ajoutees(diff)["tests/test_neuf.py"], {1, 2})

    def test_chaque_fichier_a_ses_numeros(self):
        diff = textwrap.dedent("""\
            +++ b/tests/test_a.py
            @@ -1 +2 @@
            +        self.assertEqual(1, 1)
            +++ b/tests/test_b.py
            @@ -30,0 +31 @@
            +        self.assertEqual(1, 1)
            """)
        self.assertEqual(GARDE_MODULE.lignes_ajoutees(diff),
                         {"tests/test_a.py": {2}, "tests/test_b.py": {31}})


class TestLeSignalementDesSauts(unittest.TestCase):
    """La chaîne complète sans dépôt jetable : l'arbre, le diff, le constat.

    Pas de `git init` ici : `signaler_tests_jamais_executes` reçoit le texte du
    diff et le dossier, et ne lance aucun processus — c'est ce qui permet de
    couvrir les cas d'un cran plus fins sans payer un dépôt par cas.
    """

    def setUp(self):
        self.travail = tempfile.TemporaryDirectory()
        self.depot = Path(self.travail.name)
        GARDE_MODULE.LECTURES.clear()
        self.constats = []

    def tearDown(self):
        GARDE_MODULE.LECTURES.clear()
        self.travail.cleanup()

    def _ecrire(self, chemin, texte):
        cible = self.depot / chemin
        cible.parent.mkdir(parents=True, exist_ok=True)
        cible.write_text(textwrap.dedent(texte), encoding="utf-8")

    def _signaler(self, diff, globs=()):
        GARDE_MODULE.signaler_tests_jamais_executes(
            textwrap.dedent(diff), self.depot, list(globs),
            lambda regle, fichier, texte: self.constats.append((regle, fichier, texte)))
        return self.constats

    def test_seule_la_ligne_ajoutee_est_signalee(self):
        self._ecrire("tests/test_x.py", """\
            import unittest
            class TestEssai(unittest.TestCase):
                def test_ancien(self):
                    self.skipTest("raison")
                def test_neuf(self):
                    self.skipTest("raison")
            """)
        diff = """\
            +++ b/tests/test_x.py
            @@ -5,0 +6,1 @@
            +        self.skipTest("raison")
            """
        constats = self._signaler(diff)

        self.assertEqual(len(constats), 1, constats)
        regle, fichier, texte = constats[0]
        self.assertEqual((regle, fichier), ("test-allege", "tests/test_x.py"))
        self.assertIn("skipTest : TestEssai.test_neuf (ligne 6)", texte)

    def test_un_fichier_acquitte_se_tait(self):
        """La troisième porte s'applique aussi ici : un glob, et la règle se tait."""
        self._ecrire("tests/test_x.py", """\
            import unittest
            class TestEssai(unittest.TestCase):
                def test_x(self):
                    self.skipTest("raison")
            """)
        diff = """\
            +++ b/tests/test_x.py
            @@ -3,0 +4,1 @@
            +        self.skipTest("raison")
            """
        self.assertEqual(self._signaler(diff, globs=["tests/test_x.py"]), [])

    def test_un_fichier_absent_du_disque_ne_casse_pas(self):
        diff = """\
            +++ b/tests/test_absent.py
            @@ -0,0 +1,1 @@
            +        self.assertEqual(1, 1)
            """
        self.assertEqual(self._signaler(diff), [])

    def test_un_fichier_qui_n_est_pas_un_test_est_ignore(self):
        self._ecrire("serveur/outil.py", """\
            class Outil:
                def sauter(self):
                    self.skipTest("raison")
            """)
        diff = """\
            +++ b/serveur/outil.py
            @@ -3,0 +4,1 @@
            +        self.skipTest("raison")
            """
        self.assertEqual(self._signaler(diff), [])


if __name__ == "__main__":
    unittest.main()
