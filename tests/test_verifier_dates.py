"""Contrôles de `scripts/verifier_dates.py`.

Le harnais de robustesse n'est utile que si son mensonge est **vrai** : une date
forcée qui ne déplacerait rien rendrait six lignes vertes sur l'horloge du jour,
et le contrôle mentirait en silence. Ces tests le mesurent sans lancer la suite —
le budget de processus de la suite est déjà à cinq de marge, et un test qui
lancerait les 1 146 autres le mangerait d'un coup.

Aucun sous-processus réel ici : on éprouve les pièces (la liste, la validation,
la lecture de la sortie, le substitut de `date`) **et** le lancement lui-même,
`subprocess.run` remplacé côté module. Le parent croit lancer six enfants, la
suite n'en lance aucun, et le budget de processus reste intact. Laisser le
lancement sans test serait la faute de la tranche 2 refaite : un contrôle dont
la décision finale n'est jamais exercée.
"""

import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.dont_write_bytecode = True          # ne pas semer de __pycache__ dans le dépôt
SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))        # `scripts/` n'est pas un paquet

import verifier_coffre as VC            # noqa: E402
import verifier_dates as VD             # noqa: E402


class TestDatesDeclarees(unittest.TestCase):
    """La liste de dates est la déclaration du contrôle : elle doit tenir debout."""

    def test_la_liste_n_est_pas_vide(self):
        self.assertGreater(len(VD.DATES), 0)

    def test_la_liste_est_triee_et_sans_doublon(self):
        # Triée : la sortie se lit dans l'ordre du calendrier. Sans doublon :
        # une date répétée donnerait deux lignes vertes pour une seule question.
        self.assertEqual(list(VD.DATES), sorted(set(VD.DATES)))

    def test_chaque_date_existe_au_calendrier(self):
        for texte in VD.DATES:
            with self.subTest(date=texte):
                self.assertTrue(VD.date_valide(texte))

    def test_la_liste_interroge_les_deux_cotes_de_la_bascule(self):
        """Le jour d'avant et le jour d'après, sinon la bascule n'est pas éprouvée."""
        fin = date.fromisoformat(VC.BASCULE_FIN)
        avant = [d for d in VD.DATES if date.fromisoformat(d) <= fin]
        apres = [d for d in VD.DATES if date.fromisoformat(d) > fin]
        self.assertTrue(avant, "aucune date déclarée avant la fin de la bascule")
        self.assertTrue(apres, "aucune date déclarée après la fin de la bascule")


class TestDateValide(unittest.TestCase):
    """Une date mal formée doit être refusée avant toute exécution."""

    def test_les_dates_declarees_sont_acceptees(self):
        for texte in VD.DATES:
            with self.subTest(date=texte):
                self.assertTrue(VD.date_valide(texte))

    def test_les_formes_approchantes_sont_refusees(self):
        for texte in ("2027-1-1", "2027-01-1", "20270101", "2027-01-01T00:00",
                      "demain", "", " 2027-01-01", "2027-01-01 ", None, 20270101):
            with self.subTest(date=texte):
                self.assertFalse(VD.date_valide(texte))

    def test_une_date_bien_formee_mais_inexistante_est_refusee(self):
        for texte in ("2028-02-30", "2027-02-29", "2026-13-01", "2027-00-10"):
            with self.subTest(date=texte):
                self.assertFalse(VD.date_valide(texte))


class TestLireSortie(unittest.TestCase):
    """Ce qui se lit dans une sortie d'unittest, et ce qui ne s'y lit pas."""

    def test_une_execution_verte(self):
        texte = ("......\n"
                 "----------------------------------------------------------------------\n"
                 "Ran 1146 tests in 41.118s\n\n"
                 "OK\n")
        self.assertEqual((1146, "OK"), VD.lire_sortie(texte))

    def test_une_execution_rouge(self):
        texte = ("======================================================================\n"
                 "FAIL: test_la_tolerance_expire (test_verifier_coffre.TestCarnets)\n"
                 "----------------------------------------------------------------------\n"
                 "Ran 1146 tests in 41.118s\n\n"
                 "FAILED (failures=2)\n")
        self.assertEqual((1146, "ECHEC"), VD.lire_sortie(texte))

    def test_une_sortie_muette_se_lit_echec(self):
        # Pas de « Ran », pas de verdict : ce n'est pas un vert par défaut.
        self.assertEqual((None, "ECHEC"), VD.lire_sortie(""))
        self.assertEqual((None, "ECHEC"), VD.lire_sortie("ImportError: tout casse\n"))


class TestFauxJour(unittest.TestCase):
    """Le substitut de `date` : il doit mentir juste, et mentir peu."""

    def test_today_rend_le_jour_force(self):
        jour = date(2027, 1, 1)
        self.assertEqual(jour, VD.faux_jour(jour).today())

    def test_fromisoformat_reste_la_vraie(self):
        self.assertEqual(date(2026, 12, 31),
                         VD.faux_jour(date(2027, 1, 1)).fromisoformat("2026-12-31"))

    def test_le_substitut_ne_porte_que_les_deux_formes_du_produit(self):
        # Une troisième forme lue par le produit doit casser bruyamment, pas
        # rendre la vraie date en silence.
        with self.assertRaises(AttributeError):
            VD.faux_jour(date(2027, 1, 1)).now()

    def test_le_faux_jour_deplace_reellement_la_decision(self):
        """Le cœur : la même ligne de produit change de réponse sous le faux jour."""
        avant = VC.date
        self.addCleanup(setattr, VC, "date", avant)

        VC.date = VD.faux_jour(date(2026, 12, 31))
        self.assertFalse(VC.bascule_echue(), "le 2026-12-31, la tolérance tient")

        VC.date = VD.faux_jour(date(2027, 1, 1))
        self.assertTrue(VC.bascule_echue(), "le 2027-01-01, la tolérance est échue")


class TestModeUneDate(unittest.TestCase):
    """Le mode enfant refuse une date avant de lancer quoi que ce soit."""

    def lancer(self, *arguments):
        sortie, erreur = StringIO(), StringIO()
        with redirect_stdout(sortie), redirect_stderr(erreur):
            code = VD.main(list(arguments))
        return code, sortie.getvalue(), erreur.getvalue()

    def test_une_date_mal_formee_est_refusee_sans_execution(self):
        code, sortie, erreur = self.lancer("--une-date", "2027-1-1")
        self.assertEqual(2, code)
        self.assertIn("date refusée", erreur)
        # La preuve qu'aucune suite n'a tourné : pas une ligne de résultat.
        self.assertNotIn("Ran ", sortie + erreur)

    def test_une_date_inexistante_est_refusee_sans_execution(self):
        code, sortie, erreur = self.lancer("--une-date", "2028-02-30")
        self.assertEqual(2, code)
        self.assertIn("date refusée", erreur)
        self.assertNotIn("Ran ", sortie + erreur)


class TestModeParent(unittest.TestCase):
    """Le parent : il lance, il lit, il tranche. Sans lancer un seul processus.

    C'est ici que la tranche 2 a menti une fois : une ligne rouge, un verdict
    vert, et le workflow content. Le parent n'était couvert par rien.
    `subprocess.run` est donc remplacé côté module, et on lui donne les sorties
    qu'un enfant produirait.
    """

    VERT = ("......\n"
            "----------------------------------------------------------------------\n"
            "Ran 1146 tests in 41.118s\n\n"
            "OK\n")
    ROUGE = ("======================================================================\n"
             "FAIL: test_la_tolerance_expire (test_verifier_coffre.TestCarnets)\n"
             "----------------------------------------------------------------------\n"
             "Ran 1146 tests in 41.118s\n\n"
             "FAILED (failures=2)\n")

    def lancer(self, reponses):
        """Lance le parent ; `reponses` donne (code, sortie) pour chaque date."""
        appels = []

        def faux_run(commande, **options):
            # Un appel de trop déborderait de la liste et le test le dirait :
            # c'est précisément le nombre de lancements qu'on veut savoir.
            appels.append(list(commande))
            code, sortie = reponses[len(appels) - 1]
            return subprocess.CompletedProcess(commande, code,
                                               stdout=sortie, stderr="")

        sortie, erreur = StringIO(), StringIO()
        with mock.patch.object(VD, "subprocess", SimpleNamespace(run=faux_run)), \
                redirect_stdout(sortie), redirect_stderr(erreur):
            code = VD.executer_toutes_dates()
        return code, sortie.getvalue(), appels

    def test_six_dates_vertes_rendent_zero_et_un_verdict_ok(self):
        code, sortie, appels = self.lancer([(0, self.VERT)] * len(VD.DATES))
        self.assertEqual(0, code)
        self.assertIn("VERDICT : OK — %d dates vertes sur %d"
                      % (len(VD.DATES), len(VD.DATES)), sortie)
        # Une exécution par date, et la date passée en argument : c'est la seule
        # chose qui distingue les six lancements l'un de l'autre.
        self.assertEqual(list(VD.DATES),
                         [appel[appel.index("--une-date") + 1] for appel in appels])
        # Rien à recopier quand tout est vert.
        self.assertNotIn("--- sortie de", sortie)

    def test_une_date_rouge_rend_un_et_nomme_la_date(self):
        reponses = [(0, self.VERT)] * len(VD.DATES)
        reponses[1] = (1, self.ROUGE)
        code, sortie, appels = self.lancer(reponses)
        self.assertEqual(1, code)
        self.assertIn("VERDICT : ECHEC — 1 date(s) rouge(s) sur %d : %s"
                      % (len(VD.DATES), VD.DATES[1]), sortie)
        self.assertIn("%s : Ran 1146 tests, ECHEC" % VD.DATES[1], sortie)
        # La boucle ne s'arrête pas à la première rouge : les six dates sont
        # visitées, et la dernière ligne reste verte. Une seule exécution doit
        # dire si c'est une date ou plusieurs qui ont glissé.
        self.assertEqual(len(VD.DATES), len(appels))
        self.assertIn("%s : Ran 1146 tests, OK" % VD.DATES[-1], sortie)

    def test_la_sortie_de_l_enfant_rouge_est_recopiee(self):
        reponses = [(0, self.VERT)] * len(VD.DATES)
        reponses[1] = (1, self.ROUGE)
        code, sortie, _ = self.lancer(reponses)
        self.assertIn("--- sortie de %s ---" % VD.DATES[1], sortie)
        # Le nom du test fautif est la seule chose qui dise où le produit a
        # glissé : il doit traverser intact.
        self.assertIn("FAIL: test_la_tolerance_expire "
                      "(test_verifier_coffre.TestCarnets)", sortie)
        self.assertIn("FAILED (failures=2)", sortie)
        self.assertIn("--- fin de la sortie de %s ---" % VD.DATES[1], sortie)

    def test_un_enfant_sorti_en_erreur_rougit_meme_si_sa_sortie_est_verte(self):
        # Zéro test exécuté rend « Ran 0 tests, OK » sous 3.11 : le code 2 de
        # l'enfant doit suffire à faire rougir le parent.
        reponses = [(0, self.VERT)] * len(VD.DATES)
        reponses[1] = (2, self.VERT)
        code, sortie, _ = self.lancer(reponses)
        self.assertEqual(1, code)
        self.assertIn("%s : Ran 1146 tests, ECHEC" % VD.DATES[1], sortie)

    def test_un_enfant_sorti_zero_avec_une_sortie_rouge_rougit(self):
        # Le miroir : un code nul ne blanchit pas une sortie qui dit FAILED.
        reponses = [(0, self.VERT)] * len(VD.DATES)
        reponses[1] = (0, self.ROUGE)
        code, sortie, _ = self.lancer(reponses)
        self.assertEqual(1, code)
        self.assertIn("%s : Ran 1146 tests, ECHEC" % VD.DATES[1], sortie)


class TestModeEnfantSansTest(unittest.TestCase):
    """`Ran 0 tests, OK` : le vert qui ne prouve rien, refusé par l'enfant."""

    def test_zero_test_execute_rend_deux(self):
        vide = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, str(vide), True)
        self.addCleanup(setattr, VD, "TESTS", VD.TESTS)
        self.addCleanup(setattr, VC, "date", VC.date)
        VD.TESTS = vide
        erreur = StringIO()
        with redirect_stderr(erreur):
            code = VD.executer_a_une_date("2027-01-01")
        self.assertEqual(2, code)
        self.assertIn("0 test exécuté", erreur.getvalue())


if __name__ == "__main__":
    unittest.main()


class TestFauxJourDansLesClausesDatees(unittest.TestCase):
    """Les clauses datées vivent dans `verif_contrat`, mais le jour se lit dans
    `verifier_coffre` : le faux jour doit les atteindre."""

    def test_le_faux_jour_atteint_les_clauses_datees(self):
        racine = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, racine)
        noyau = racine / VC.NOYAU
        noyau.parent.mkdir(parents=True)
        noyau.write_text("Se retire au plus tard le 2026-12-31.\n", encoding="utf-8")
        for attribut in ("date", "RACINE"):
            self.addCleanup(setattr, VC, attribut, getattr(VC, attribut))
        self.addCleanup(VC.avertissements.clear)
        VC.RACINE = racine

        VC.date = VD.faux_jour(date(2026, 12, 31))
        VC.avertissements.clear()
        VC.verifier_clauses_datees_du_noyau()
        self.assertEqual(VC.avertissements, [])

        VC.date = VD.faux_jour(date(2027, 1, 1))
        VC.verifier_clauses_datees_du_noyau()
        self.assertEqual(len(VC.avertissements), 1)
