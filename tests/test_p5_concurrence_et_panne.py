#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""La sûreté de l'écriture sous **concurrence** et sous **panne** — phase 5.

Ces tests figent ce que la phase 5 ajoute au socle (§7.4) :

- **deux écritures concurrentes ne se mélangent pas** : les actes passent **en
  série** sous le verrou, et **chacun** forme son commit ;
- **un commit concurrent** posé pendant l'acte est pris **juste avant** le commit
  par la revérification de la tête et de l'empreinte, et fait **refuser** — jamais
  écraser ;
- un fichier **touché en chemin** (empreinte changée) fait refuser de même ;
- **un commit étranger** qui a emporté les fichiers de l'acte est **détecté et
  consigné** dans le journal du dépôt, et l'acte est défait — il ne lui est jamais
  attribué ;
- un **verrou périmé** — dont le porteur est mort — est **levé à la reprise**, en
  le nommant ;
- un **second écrivain** — autre machine, autre outil, ou verrou illisible — est
  **signalé**, et son verrou n'est **jamais écrasé** ;
- les **incidents du journal** sont **remontés à l'agent** par l'acte **suivant**,
  une fois et une seule, pour qu'il les consigne au carnet — sans jamais retirer la
  ligne du journal, que l'humain garde entière (constat 7) ;
- l'**identifiant d'écrivain** est **tiré au hasard une fois**, et gardé **hors du
  coffre comme hors de ``.git``** : deux stations de la même machine — ou deux
  stations clonées d'un même gabarit — ne se confondent plus (résidu (e)) ;
- le **ménage de reprise** retire ce qu'un écrivain **mort** a laissé d'orphelin
  dans ``.git`` — son index dédié —, et **jamais** la garde, dont l'inode porte le
  ``flock``, ni le journal, ni le marqueur des remontées (résidu (f)).
"""

import errno
import json
import os
import platform
import subprocess
import sys
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
RACINE = Path(__file__).resolve().parent.parent
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))
if str(RACINE / "tests") not in sys.path:
    sys.path.insert(0, str(RACINE / "tests"))

from test_ecrivain import git                                   # noqa: E402
from test_gestes_des_notes import BaseDesNotes, note            # noqa: E402

import serveur.gestes_des_notes as GESTES                       # noqa: E402
import serveur.socle_ecriture as SOCLE                          # noqa: E402


class BaseDeLaConcurrence(BaseDesNotes):
    """Un coffre de notes, et de quoi poser un verrou à la main."""

    def dossier_git(self):
        return self.coffre / ".git"

    def poser_verrou(self, **fiche):
        """Écrit un verrou *nommant son porteur* — le format de la phase 5."""
        complete = {"outil": SOCLE.OUTIL, "pid": os.getpid(),
                    "machine": SOCLE.identifiant_d_ecrivain(),
                    "naiss": SOCLE._naissance(os.getpid()),
                    "pose": "2026-01-05T00:00:00+00:00"}
        complete.update(fiche)
        fichier = self.dossier_git() / SOCLE.VERROU
        fichier.write_text(json.dumps(complete) + "\n", encoding="utf-8")
        return fichier

    def verrou_est_la(self):
        return (self.dossier_git() / SOCLE.VERROU).exists()


class TestLaSerieEtLeSecondEcrivain(BaseDeLaConcurrence):
    """Les écritures passent en série ; un second écrivain est signalé, jamais écrasé."""

    def test_deux_ecritures_concurrentes_forment_chacune_son_commit(self):
        """Critère 1 — deux actes concurrents ne se mélangent pas, chacun son commit."""
        chemins = ("0-SAVOIRS/a.md", "0-SAVOIRS/b.md")
        bases = {chemin: note(corps="\n\nCorps %s.\n" % chemin[-4])
                 for chemin in chemins}
        for chemin, base in bases.items():
            self.poser_note(chemin, base)

        actes, pannes = {}, {}

        def ecrire(chemin):
            try:
                actes[chemin] = GESTES.completer_une_note(
                    self.coffre, auteur=self.AUTEUR, source=chemin,
                    texte=bases[chemin] + "\n\nSuite %s.\n" % chemin[-4],
                    date=self.DATE)
            except Exception as erreur:                 # noqa: BLE001 — on veut le voir
                pannes[chemin] = erreur

        fils = [threading.Thread(target=ecrire, args=(chemin,)) for chemin in chemins]
        for fil in fils:
            fil.start()
        for fil in fils:
            fil.join()

        self.assertEqual({}, pannes, pannes)
        for chemin in chemins:
            acte = actes[chemin]
            self.assertIsNone(acte.refus, acte.refus)
            self.assertEqual(bases[chemin] + "\n\nSuite %s.\n" % chemin[-4],
                             self.lire(chemin))
        # deux actes, donc **deux** commits distincts — aucune fusion, aucun mélange.
        self.assertNotEqual(actes[chemins[0]].commit, actes[chemins[1]].commit)
        self.assertFalse(self.verrou_est_la(), "le verrou doit être rendu")

    def test_un_verrou_tenu_par_un_vivant_fait_attendre_puis_signale(self):
        """Critère 5 — un second écrivain vivant ne se double pas : on attend, puis on le dit."""
        base = note(corps="\n\nUn corps.\n")
        self.poser_note("0-SAVOIRS/note.md", base)
        verrou = self.poser_verrou(machine=SOCLE.identifiant_d_ecrivain(),
                                   pid=os.getpid())  # vivant, même station
        try:
            socle = SOCLE.Verrou(self.dossier_git(), delai=0.05)
            self.assertFalse(socle.__enter__())
            self.assertIn("second écrivain", socle.motif)
        finally:
            verrou.unlink(missing_ok=True)
        self.assertEqual(base, self.lire("0-SAVOIRS/note.md"))

    def test_un_second_ecrivain_d_une_autre_machine_est_signale_sans_attendre(self):
        """Critère 5 — un acte venu d'ailleurs n'est pas « le même écrivain »."""
        verrou = self.poser_verrou(machine="autre-machine")
        try:
            socle = SOCLE.Verrou(self.dossier_git(), delai=5.0)
            self.assertFalse(socle.__enter__())
            self.assertIn("second écrivain", socle.motif)
            self.assertTrue(self.verrou_est_la(), "son verrou n'est jamais écrasé")
        finally:
            verrou.unlink(missing_ok=True)

    def test_aucun_nom_d_hote_n_est_ecrit_sur_le_disque(self):
        """§9 — ni la fiche du verrou ni le journal ne portent le nom de l'hôte.

        On les désigne par un **identifiant d'écrivain** tiré au hasard pour la
        station : deux stations se distinguent encore, mais aucune ne se nomme (§9).
        """
        hote = platform.node()
        # 1. La fiche du verrou, écrite par un acte qui le prend.
        socle = SOCLE.Verrou(self.dossier_git())
        self.assertTrue(socle.__enter__())
        try:
            fiche = (self.dossier_git() / SOCLE.VERROU).read_text(encoding="utf-8")
        finally:
            socle.__exit__()
        self.assertIn(SOCLE.identifiant_d_ecrivain(), fiche)
        self.assertNotEqual(SOCLE.identifiant_d_ecrivain(), hote)
        self.assertNotIn(hote, fiche)

        # 2. Le journal — en relevant un verrou périmé qui laisse un reste d'acte.
        self.poser_verrou(pid=999_999_999)
        self.ecrire_fichier("0-EN-VRAC/un-reste.md", note())    # non commité : reste d'acte
        socle = SOCLE.Verrou(self.dossier_git())
        self.assertTrue(socle.__enter__())
        socle.__exit__()
        journal = (self.dossier_git() / SOCLE.INCIDENTS).read_text(encoding="utf-8")
        self.assertIn(SOCLE.identifiant_d_ecrivain(), journal)
        self.assertNotIn(hote, journal)

    def test_un_verrou_illisible_n_est_jamais_retire(self):
        """Un verrou qu'on ne peut pas lire garde le refus historique, mot pour mot."""
        verrou = self.dossier_git() / SOCLE.VERROU
        verrou.write_text("un autre acte tient le verrou\n", encoding="utf-8")
        try:
            socle = SOCLE.Verrou(self.dossier_git())
            self.assertFalse(socle.__enter__())
            self.assertIn("un autre acte écrit peut-être à cet instant", socle.motif)
            self.assertIn("jamais", socle.motif)
        finally:
            verrou.unlink(missing_ok=True)


class TestLeVerrouPerimeALaReprise(BaseDeLaConcurrence):
    """Un verrou dont le porteur est mort se relève à la reprise, en le nommant."""

    def test_un_verrou_perime_est_leve_et_nomme(self):
        """Critère 4 — le porteur est mort : le verrou est périmé, on le relève."""
        # Un pid hors de portée : `os.kill` le dit mort (ProcessLookupError).
        verrou = self.poser_verrou(pid=999_999_999)
        socle = SOCLE.Verrou(self.dossier_git())
        self.assertTrue(socle.__enter__())
        try:
            self.assertEqual(999_999_999, socle.perime_leve["pid"])
            self.assertTrue(self.verrou_est_la(), "le verrou est repris, pas laissé vide")
        finally:
            socle.__exit__()
        self.assertFalse(self.verrou_est_la(), "le verrou repris se rend à la sortie")

    def test_la_reprise_apres_une_panne_laisse_ecrire(self):
        """Critère 4 — après la mort du porteur, l'acte suivant passe au lieu de refuser."""
        base = note(corps="\n\nUn corps.\n")
        self.poser_note("0-SAVOIRS/note.md", base)
        self.poser_verrou(pid=999_999_999)
        acte = GESTES.completer_une_note(self.coffre, auteur=self.AUTEUR,
                                         source="0-SAVOIRS/note.md",
                                         texte=base + "\n\nSuite.\n", date=self.DATE)
        self.assertIsNone(acte.refus, acte.refus)
        self.assertEqual(base + "\n\nSuite.\n", self.lire("0-SAVOIRS/note.md"))

    def test_la_fiche_du_verrou_nomme_la_naissance_du_porteur(self):
        """Le verrou joint au pid le **marqueur de naissance** du processus."""
        socle = SOCLE.Verrou(self.dossier_git())
        self.assertTrue(socle.__enter__())
        try:
            fiche = json.loads((self.dossier_git() / SOCLE.VERROU)
                               .read_text(encoding="utf-8"))
        finally:
            socle.__exit__()
        self.assertEqual(SOCLE._naissance(os.getpid()), fiche["naiss"])
        self.assertIsNotNone(fiche["naiss"])

    def test_un_pid_reutilise_est_tenu_pour_perime(self):
        """Critère 5 — un pid **vivant** mais d'un autre processus est bien mort."""

        # Le pid est le nôtre, donc vivant ; mais le marqueur de naissance dit un
        # autre processus — le noyau a recyclé ce pid depuis. Le porteur est mort.
        self.poser_verrou(pid=os.getpid(), naiss="un-autre-instant")
        socle = SOCLE.Verrou(self.dossier_git())
        self.assertTrue(socle.__enter__())
        try:
            self.assertEqual(os.getpid(), socle.perime_leve["pid"])
        finally:
            socle.__exit__()

    def test_un_pid_hors_bornes_est_tenu_pour_mort(self):
        """Un pid qui déborde l'entier du noyau ne fait pas lever le socle."""
        self.assertFalse(SOCLE._processus_vivant(10 ** 30))
        self.assertFalse(SOCLE._processus_vivant(0))
        self.assertFalse(SOCLE._processus_vivant(-4))

    def test_la_garde_qui_ne_se_prend_pas_dans_le_delai_refuse(self):
        """La garde se prend sans bloquer : au-delà du délai, la reprise refuse.

        Un ``flock`` bloquant suspendait la reprise tant qu'un autre tenait la garde.
        Elle se prend désormais en **non bloquant**, dans une boucle bornée par le
        délai : si la garde est encore tenue au bout, la reprise **refuse** et le dit,
        au lieu d'attendre sans fin (§7.4).
        """
        if SOCLE.fcntl is None:
            self.skipTest("« flock » manque hors POSIX")
        tenue = os.open(str(self.dossier_git() / SOCLE.GARDE),
                        os.O_CREAT | os.O_RDWR, 0o644)
        try:
            SOCLE.fcntl.flock(tenue, SOCLE.fcntl.LOCK_EX)
            verrou = SOCLE.Verrou(self.dossier_git(), delai=0.05)
            self.assertFalse(verrou.__enter__(),
                             "la garde tenue au-delà du délai fait refuser la reprise")
            self.assertIn("garde", verrou.motif)
        finally:
            SOCLE.fcntl.flock(tenue, SOCLE.fcntl.LOCK_UN)
            os.close(tenue)

    def test_une_erreur_de_verrou_autre_qu_une_contention_refuse_tout_de_suite(self):
        """Un ``flock`` qui échoue pour une **autre** raison refuse, sans boucler.

        ``EWOULDBLOCK`` dit « un autre la tient, attends » ; errno ``ENOLCK`` (un
        système de fichiers qui ne sait pas verrouiller, sur NFS par exemple) dit
        « on ne peut pas verrouiller ici ! ». Traiter les deux comme une contention
        ferait boucler la reprise jusqu'au délai et rendrait un motif **faux** ; on
        refuse donc tout de suite, en nommant l'erreur.
        """
        if SOCLE.fcntl is None:
            self.skipTest("« flock » manque hors POSIX")
        erreur = OSError(errno.ENOLCK, os.strerror(errno.ENOLCK))
        vrai_flock = SOCLE.fcntl.flock

        def flock_impossible(*args, **kwargs):
            raise erreur

        SOCLE.fcntl.flock = flock_impossible
        self.addCleanup(setattr, SOCLE.fcntl, "flock", vrai_flock)
        debut = time.monotonic()
        verrou = SOCLE.Verrou(self.dossier_git(), delai=5.0)
        self.assertFalse(verrou.__enter__(),
                         "une erreur de verrou n'est pas une contention à attendre")
        self.assertLess(time.monotonic() - debut, 1.0,
                        "le refus est immédiat : on n'attend pas un délai qui ne viendra pas")
        self.assertIn("ENOLCK", verrou.motif,
                      "le motif nomme l'erreur, pour qu'on sache quoi réparer")


class TestLaRepriseAtomique(BaseDeLaConcurrence):
    """Deux **processus** qui voient le **même** porteur mort ne le relèvent pas chacun.

    Le verrou d'écriture se crée et se retire : son inode change à chaque acte. Deux
    reprises qui visaient le **même** verrou périmé pouvaient donc le retirer toutes
    les deux — la seconde retirant, sans le savoir, le verrou **neuf** de la première.
    Les deux se croyaient alors seules, et écrivaient de front : c'est exactement le
    double écrivain que le verrou existe pour empêcher (§7.4). L'épreuve est
    **inter-processus** — deux **processus**, pas deux fils — et les fait viser le
    même porteur mort : un seul doit relever, l'autre doit attendre.
    """

    #: Le petit acte joué par chaque processus : poser le verrou, tenir un instant en
    #: le disant, le rendre. Chaque tour est consigné, horodaté, dans un journal.
    ACTE = """
import json, os, sys, time
sys.dont_write_bytecode = True
sys.path.insert(0, sys.argv[1])
import serveur.socle_ecriture as SOCLE
dossier_git, journal, tenue = sys.argv[2], sys.argv[3], float(sys.argv[4])
verrou = SOCLE.Verrou(dossier_git, delai=30.0)
if not verrou.__enter__():
    with open(journal, "a", encoding="utf-8") as suite:
        suite.write(json.dumps({"pid": os.getpid(), "tour": "refus",
                                "motif": verrou.motif}) + "\\n")
    raise SystemExit(3)
with open(journal, "a", encoding="utf-8") as suite:
    suite.write(json.dumps({"pid": os.getpid(), "tour": "entre", "temps": time.time(),
                            "perime": verrou.perime_leve is not None}) + "\\n")
time.sleep(tenue)
with open(journal, "a", encoding="utf-8") as suite:
    suite.write(json.dumps({"pid": os.getpid(), "tour": "sort",
                            "temps": time.time()}) + "\\n")
verrou.__exit__()
"""

    def test_deux_processus_ne_relevent_pas_le_meme_verrou_perime(self):
        """Les deux voient le porteur mort : un seul le relève, l'autre attend."""
        self.poser_verrou(pid=999_999_999)              # le porteur mort, commun
        # Le journal vit **dans ``.git``** : hors du travail, il ne salit pas le
        # constat des restes d'acte (``git status`` ne voit pas le dossier ``.git``).
        journal = self.dossier_git() / "journal-des-reprises.jsonl"
        dossier_git = self.dossier_git()
        fils = [subprocess.Popen(
            [sys.executable, "-c", self.ACTE, str(RACINE), str(dossier_git),
             str(journal), "0.3"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE) for _ in range(2)]
        codes = []
        for fil in fils:
            _, erreur = fil.communicate(timeout=60)
            codes.append((fil.returncode, erreur.decode("utf-8", "replace")))
        for code, erreur in codes:
            self.assertEqual(0, code, erreur)

        tours = [json.loads(ligne) for ligne in
                 journal.read_text(encoding="utf-8").splitlines() if ligne.strip()]
        entrees = [tour for tour in tours if tour["tour"] == "entre"]
        self.assertEqual(2, len(entrees), "les deux processus doivent finir par écrire")
        self.assertEqual(1, sum(1 for tour in entrees if tour["perime"]),
                         "un seul des deux doit avoir relevé le verrou périmé")

        # Aucune fenêtre où deux processus tiennent le verrou à la fois : les tours,
        # remis dans l'ordre du temps, s'alternent « entre » / « sort ».
        dans_le_verrou = 0
        for tour in sorted(tours, key=lambda tour: tour["temps"]):
            if tour["tour"] == "entre":
                dans_le_verrou += 1
                self.assertLessEqual(dans_le_verrou, 1,
                                     "deux processus tiennent le verrou à la fois")
            else:
                dans_le_verrou -= 1
        self.assertEqual(0, dans_le_verrou)
        self.assertFalse(self.verrou_est_la(), "le verrou est rendu à la fin")


class TestLaTeteEtLesEmpreintes(BaseDeLaConcurrence):
    """Juste avant le commit, on relit la tête et l'empreinte — on refuse, on n'écrase pas."""

    def test_un_commit_concurrent_fait_refuser_et_defaire(self):
        """Critère 2 — un commit concurrent pendant l'acte : refus, jamais un écrasement."""
        base = note(corps="\n\nUn corps.\n")
        self.poser_note("0-SAVOIRS/note.md", base)
        tete_avant = self.tete()
        # Un « commit concurrent » : la tête avance pendant que l'acte travaille.
        self.poser_note("0-SAVOIRS/autre.md", note())
        chemin = "0-SAVOIRS/note.md"
        (self.coffre / chemin).write_text(base + "\n\nSuite.\n", encoding="utf-8")

        commit, motif = SOCLE._committer(self.coffre, {chemin: base.encode("utf-8")},
                                         "Compléter : note", tete_attendue=tete_avant)

        self.assertIsNone(commit)
        self.assertIn("commit concurrent", motif)
        self.assertEqual(base, self.lire(chemin), "l'acte doit être défait, pas écrasé")

    def test_un_fichier_touche_apres_ecriture_fait_refuser(self):
        """Critère 2 — l'empreinte du fichier lu change : refus, jamais un écrasement.

        Le fichier porte un texte **tiers** : le défaire est conditionnel, il ne
        restaure pas le contenu d'avant **par-dessus** l'écriture de quelqu'un
        d'autre — il la **laisse telle quelle** et le dit dans le motif (§7.4).
        """
        base = note(corps="\n\nUn corps.\n")
        self.poser_note("0-SAVOIRS/note.md", base)
        chemin = "0-SAVOIRS/note.md"
        # Ce que l'acte croit avoir écrit… et ce que le disque porte réellement.
        (self.coffre / chemin).write_text("un autre texte\n", encoding="utf-8")

        commit, motif = SOCLE._committer(self.coffre, {chemin: base.encode("utf-8")},
                                         "Compléter : note",
                                         tete_attendue=self.tete(),
                                         ecrits={chemin: base + "\n\nSuite.\n"})

        self.assertIsNone(commit)
        self.assertIn("empreinte", motif)
        self.assertIn("laissé tel quel", motif)
        self.assertIn(chemin, motif)
        self.assertEqual("un autre texte\n", self.lire(chemin),
                         "le texte du tiers doit survivre au défaire")

    def test_le_defaire_conditionnel_restaure_ce_que_l_acte_a_pose(self):
        """Le corollaire — un chemin encore intact est bel et bien défait."""
        base = note(corps="\n\nUn corps.\n")
        self.poser_note("0-SAVOIRS/note.md", base)
        chemin = "0-SAVOIRS/note.md"
        tenu = base + "\n\nSuite.\n"
        (self.coffre / chemin).write_text(tenu, encoding="utf-8")
        tete_avant = self.tete()
        # Un « commit concurrent » avance la tête, mais le fichier, lui, est intact.
        self.poser_note("0-SAVOIRS/autre.md", note())

        commit, motif = SOCLE._committer(self.coffre, {chemin: base.encode("utf-8")},
                                         "Compléter : note", tete_attendue=tete_avant,
                                         ecrits={chemin: tenu})

        self.assertIsNone(commit)
        self.assertIn("commit concurrent", motif)
        self.assertNotIn("laissé tel quel", motif)
        self.assertEqual(base, self.lire(chemin),
                         "un chemin encore intact doit reprendre son état d'avant")

    def test_le_defaire_ne_touche_pas_a_l_index_du_coffre(self):
        """Le défaire ne réinitialise pas l'index du dépôt : l'acte vit sur un index à part.

        L'acte se construit sur un index **dédié** : l'index réel du coffre n'a jamais
        porté son écriture. Le défaire n'a donc rien à y réinitialiser — s'il le
        faisait, il effacerait ce qu'un humain y avait mis **en attente** pour ces
        mêmes chemins.
        """
        base = note(corps="\n\nUn corps.\n")
        self.poser_note("0-SAVOIRS/note.md", base)
        chemin = "0-SAVOIRS/note.md"
        # Un humain met en attente, dans l'index réel, un contenu à lui…
        self.ecrire_fichier(chemin, "trois\n")
        git(self.coffre, "add", "--", chemin)
        # … puis un tiers écrit autre chose sur le disque. L'acte, lui, croit avoir posé
        # son texte : la revérification de l'empreinte refuse, et le défaire s'exécute.
        self.ecrire_fichier(chemin, "un autre texte\n")

        commit, motif = SOCLE._committer(self.coffre, {chemin: base.encode("utf-8")},
                                         "Compléter : note", tete_attendue=self.tete(),
                                         ecrits={chemin: base + "\n\nSuite.\n"})

        self.assertIsNone(commit)
        self.assertIn("empreinte", motif)
        self.assertEqual("trois\n", git(self.coffre, "show", ":%s" % chemin).stdout,
                         "le défaire ne touche pas à l'index réel")

    def test_le_commit_qui_porte_l_acte_passe(self):
        """Le corollaire — quand la tête et l'empreinte concordent, l'acte se pose."""
        base = note(corps="\n\nUn corps.\n")
        self.poser_note("0-SAVOIRS/note.md", base)
        chemin = "0-SAVOIRS/note.md"
        tenu = base + "\n\nSuite.\n"
        (self.coffre / chemin).write_text(tenu, encoding="utf-8")

        commit, motif = SOCLE._committer(self.coffre, {chemin: base.encode("utf-8")},
                                         "Compléter : note",
                                         tete_attendue=self.tete(),
                                         ecrits={chemin: tenu})

        self.assertIsNone(motif, motif)
        self.assertEqual(tenu, self.lire(chemin))
        self.assertEqual((chemin,), self.chemins_du_commit(commit))

    def chemins_du_commit(self, commit):
        rendu = git(self.coffre, "-c", "core.quotePath=false", "show", "--name-only",
                    "--format=", "-z", str(commit))
        return tuple(sorted(c for c in rendu.stdout.split("\0") if c))


class TestLeCommitEtranger(BaseDeLaConcurrence):
    """Un commit étranger qui a emporté l'acte est détecté et consigné, jamais attribué."""

    def test_un_commit_etranger_est_detecte_et_consigne(self):
        """Critère 3 — le commit ne porte pas l'acte : on défait, et on le consigne."""
        base = note(corps="\n\nUn corps.\n")
        self.poser_note("0-SAVOIRS/note.md", base)
        chemin = "0-SAVOIRS/note.md"
        tenu = base + "\n\nSuite.\n"
        (self.coffre / chemin).write_text(tenu, encoding="utf-8")

        def lister_etranger(_coffre, _commit):
            return ("un/autre/fichier.md",)

        commit, motif = SOCLE._committer(self.coffre, {chemin: base.encode("utf-8")},
                                         "Compléter : note",
                                         lister=lister_etranger,
                                         tete_attendue=self.tete())

        self.assertIsNone(commit)
        self.assertIn("ne porte pas exactement l'acte", motif)
        self.assertEqual(base, self.lire(chemin))

        journal = self.dossier_git() / SOCLE.INCIDENTS
        self.assertTrue(journal.exists(), "l'incident doit être consigné")
        lignes = journal.read_text(encoding="utf-8").splitlines()
        self.assertEqual(1, len(lignes))
        self.assertIn("un/autre/fichier.md", lignes[0])
        self.assertIn(chemin, lignes[0])
        # L'incident vit **hors du coffre** : rien de tout cela n'est une note.
        self.assertFalse((self.coffre / SOCLE.INCIDENTS).exists())


class TestLaFenetreEntreLaVerificationEtLeCommit(BaseDeLaConcurrence):
    """Rien ne s'empile sur un commit qui atterrit entre la vérification et le commit.

    La vérification de la tête et le `git commit` n'étaient pas un seul geste : un
    commit pouvait atterrir **entre** les deux, et l'acte se posait alors sur une
    nouvelle tête sans que rien ne le voie. L'acte se construit désormais sur un
    **index dédié** (`GIT_INDEX_FILE`), puis la branche n'avance que par
    **comparaison-et-échange** (`git update-ref <ref> <nouveau> <attendu>`) : si la
    tête a bougé dans la fenêtre, l'échange échoue et l'acte est refusé.
    """

    def test_un_commit_qui_atteint_dans_la_fenetre_refuse_l_acte(self):
        """On ouvre la fenêtre de l'extérieur, sans toucher au code."""
        base = note(corps="\n\nUn corps.\n")
        self.poser_note("0-SAVOIRS/note.md", base)
        chemin = "0-SAVOIRS/note.md"
        tenu = base + "\n\nSuite.\n"
        (self.coffre / chemin).write_text(tenu, encoding="utf-8")
        attendue = self.tete()

        def lister_en_bougant(_coffre, commit):
            # Un autre acte atterrit **dans la fenêtre**, juste avant que la branche
            # ne soit déplacée : la tête n'est plus celle qui avait été vérifiée.
            (self.coffre / "0-SAVOIRS/concurrent.md").write_text(note(),
                                                                 encoding="utf-8")
            git(self.coffre, "add", "--", "0-SAVOIRS/concurrent.md")
            git(self.coffre, "commit", "--quiet", "-m", "un autre acte")
            return SOCLE.fichiers_du_commit(_coffre, commit)

        commit, motif = SOCLE._committer(self.coffre, {chemin: base.encode("utf-8")},
                                         "Compléter : note", lister=lister_en_bougant,
                                         tete_attendue=attendue)

        self.assertIsNone(commit)
        self.assertIn("commit concurrent", motif)
        self.assertNotEqual(attendue, self.tete(), "la tête a bel et bien bougé")
        self.assertEqual(base, self.lire(chemin))

    def test_un_index_qui_ne_porte_pas_la_pose_refuse_l_acte(self):
        """L'index est revérifié avant l'objet : il porte la pose de l'acte, ou rien.

        L'ajout lit le disque ; un contenu qui a bougé entre la pose et l'ajout se
        retrouverait gravé sans que rien ne le dise. On relit donc l'index contre la
        pose de l'acte : s'il ne la porte pas, l'acte **refuse** et défait (§7.4).
        """
        base = note(corps="\n\nUn corps.\n")
        self.poser_note("0-SAVOIRS/note.md", base)
        chemin = "0-SAVOIRS/note.md"
        tenu = base + "\n\nSuite.\n"
        (self.coffre / chemin).write_text(tenu, encoding="utf-8")
        autre = subprocess.run(
            ["git", "-C", str(self.coffre), "hash-object", "-w", "--stdin"],
            input=b"un autre texte\n", capture_output=True).stdout.strip().decode()

        def index_malin(_coffre, environnement, _chemins):
            # Un tiers glisse un autre contenu dans l'index dédié, après l'ajout.
            SOCLE._git(_coffre, "update-index", "--cacheinfo",
                       "100644,%s,%s" % (autre, chemin),
                       environnement=environnement)

        commit, motif = SOCLE._committer(self.coffre, {chemin: base.encode("utf-8")},
                                         "Compléter : note", tete_attendue=self.tete(),
                                         ecrits={chemin: tenu},
                                         apres_l_ajout=index_malin)

        self.assertIsNone(commit)
        self.assertIn("index", motif)
        self.assertEqual(base, self.lire(chemin), "l'écriture a été défaite")

    def test_une_autre_branche_que_la_par_defaut_est_refusee_avant_l_echange(self):
        """La branche est comparée à la branche par défaut juste avant l'échange.

        Un changement de branche pendant l'acte ferait avancer une référence qui n'est
        pas celle qu'on croit : l'acte refuse et défait, plutôt que de poser son commit
        ailleurs que sur la branche par défaut du dépôt de données (§7.4).
        """
        base = note(corps="\n\nUn corps.\n")
        self.poser_note("0-SAVOIRS/note.md", base)
        chemin = "0-SAVOIRS/note.md"
        tenu = base + "\n\nSuite.\n"
        (self.coffre / chemin).write_text(tenu, encoding="utf-8")
        git(self.coffre, "checkout", "--quiet", "-b", "une-autre-branche")

        commit, motif = SOCLE._committer(self.coffre, {chemin: base.encode("utf-8")},
                                         "Compléter : note", tete_attendue=self.tete(),
                                         ecrits={chemin: tenu})

        self.assertIsNone(commit)
        self.assertIn("branche", motif)
        self.assertEqual(base, self.lire(chemin), "l'écriture a été défaite")


class TestLaTenueAuFilDeLEau(BaseDeLaConcurrence):
    """La tenue au fil de l'eau d'un carnet existant — l'engagement envers le visionnaire."""

    def test_on_ajoute_une_etape_a_un_carnet_existant(self):
        """Le carnet se complète en fin, comme une note tenue sur place (§7.3)."""
        relatif = "0-PROJETS/mon-projet/carnets/2026-01-05-suivi.md"
        base = note(front="agent: batisseur\nprojet: mon-projet\nstatut: en cours\n"
                          "date: 2026-01-05\n---",
                    corps="\n\n## Fait\n\n- Ouverture du chantier.\n")
        self.poser_note(relatif, base)
        tenu = base + "\n\n## Fait\n\n- 2026-01-05 — une étape de plus.\n"
        acte = GESTES.completer_une_note(self.coffre, auteur=self.AUTEUR,
                                         source=relatif, texte=tenu, date=self.DATE)
        self.assertIsNone(acte.refus, acte.refus)
        self.assertEqual(tenu, self.lire(relatif))

    def test_un_resume_reste_ferme_a_la_tenue_au_fil_de_l_eau(self):
        """Tous les genres tenus sur place ne s'ouvrent pas : le résumé attend encore."""
        relatif = "0-PROJETS/mon-projet/mon-projet — résumé.md"
        base = note(corps="\n\nUn résumé.\n")
        self.poser_note(relatif, base)
        acte = GESTES.completer_une_note(self.coffre, auteur=self.AUTEUR,
                                         source=relatif, texte=base + "\n\nSuite.\n",
                                         date=self.DATE)
        self.assertIsNotNone(acte.refus)
        self.assertIn("au fil de l'eau", acte.refus)
        self.assertEqual(base, self.lire(relatif))


class TestLaRemonteeDesIncidents(BaseDeLaConcurrence):
    """L'acte suivant remonte à l'agent les incidents qu'il n'a pas encore vus (§7.4).

    Un incident — un verrou périmé relevé, un commit étranger — est consigné au
    **journal du dépôt** (dans ``.git``), mais personne ne le lit sur le moment. C'est
    l'acte **suivant** qui le rend à l'agent, pour qu'il le consigne à son carnet :
    une fois, jamais deux — et la ligne ne quitte jamais le journal, l'humain garde la
    trace entière.
    """

    def journal_des_incidents(self):
        return self.dossier_git() / SOCLE.INCIDENTS

    def test_l_acte_suivant_remonte_l_incident_une_seule_fois(self):
        """Un incident laissé par un écrivain mort est remonté, une fois et une seule."""
        base = note(corps="\n\nUn corps.\n")
        self.poser_note("0-SAVOIRS/note.md", base)
        # Ce qu'un écrivain mort a laissé de non commité, et son verrou périmé qui le
        # dit : en relevant le verrou, le socle consigne l'incident au journal.
        self.ecrire_fichier("0-SAVOIRS/oublie.md", note())
        self.poser_verrou(pid=999_999_999)

        premier = GESTES.completer_une_note(self.coffre, auteur=self.AUTEUR,
                                            source="0-SAVOIRS/note.md",
                                            texte=base + "\n\nSuite.\n", date=self.DATE)
        self.assertIsNone(premier.refus, premier.refus)
        self.assertEqual(1, len(premier.incidents),
                         "l'acte suivant remonte l'incident à l'agent")
        self.assertIn("verrou périmé levé", premier.incidents[0])

        deuxieme = GESTES.completer_une_note(self.coffre, auteur=self.AUTEUR,
                                             source="0-SAVOIRS/note.md",
                                             texte=base + "\n\nSuite.\n\nEncore.\n",
                                             date=self.DATE)
        self.assertIsNone(deuxieme.refus, deuxieme.refus)
        self.assertEqual((), deuxieme.incidents, "un incident ne se remonte pas deux fois")
        # La ligne reste au journal : c'est la **remontée** qui ne se répète pas.
        self.assertIn("verrou périmé levé",
                      self.journal_des_incidents().read_text(encoding="utf-8"))

    def test_la_remontee_se_marque_dans_le_depot_sans_entamer_le_journal(self):
        """La remontée avance un marqueur dans ``.git`` ; le journal garde ses lignes."""
        ligne = "2026-01-05T00:00:00+00:00\tun incident d'essai"
        journal = self.journal_des_incidents()
        journal.write_text(ligne + "\n", encoding="utf-8")

        # Lire ne consomme rien : deux lectures rendent le même incident.
        self.assertEqual((ligne,), SOCLE.incidents_non_remontes(self.coffre))
        self.assertEqual((ligne,), SOCLE.incidents_non_remontes(self.coffre))

        # La remontée, elle, le rend une fois et avance le marqueur.
        self.assertEqual((ligne,), SOCLE.remonter_les_incidents(self.coffre))
        self.assertEqual((), SOCLE.incidents_non_remontes(self.coffre))
        # Le journal n'est pas entamé, et le marqueur ne vit pas dans le coffre.
        self.assertEqual(ligne + "\n", journal.read_text(encoding="utf-8"))
        marqueur = self.dossier_git() / SOCLE.REMONTES
        self.assertTrue(marqueur.exists(), "le marqueur vit dans le dépôt, pas dans le coffre")
        self.assertEqual("1", marqueur.read_text(encoding="utf-8"))

    def test_un_marqueur_plus_grand_que_le_journal_remonte_tout_a_nouveau(self):
        """Journal rétréci : on repart de zéro et on remonte tout à nouveau.

        Si le marqueur dit qu'on a déjà remonté **plus de lignes que le journal n'en
        porte**, c'est que le journal a été tronqué ou repris : on ne peut plus savoir
        ce qui a été vu. On repart de zéro et on remonte **tout** à nouveau — au pire
        un incident se consigne deux fois, jamais zéro.
        """
        ligne = "2026-01-05T00:00:00+00:00\tun incident d'essai"
        (self.dossier_git() / SOCLE.INCIDENTS).write_text(ligne + "\n", encoding="utf-8")
        (self.dossier_git() / SOCLE.REMONTES).write_text("5", encoding="utf-8")

        self.assertEqual((ligne,), SOCLE.incidents_non_remontes(self.coffre))


class TestLIdentifiantDEcrivain(BaseDeLaConcurrence):
    """L'identifiant d'écrivain est propre à **chaque station**, pas à la machine (§9, §7.4).

    ``/etc/machine-id`` est partagé par tout ce qui vit sur un même hôte : deux
    stations — conteneurs ou machines tirés d'un même gabarit, ou deux profils d'une
    même machine — porteraient la même empreinte et se croiraient le même écrivain.
    L'identifiant est donc **tiré au hasard une fois**, et gardé **hors du coffre
    comme hors de ``.git``** : posé dans le dépôt, il voyagerait avec les clones et
    le remède serait annulé.
    """

    def chemin_de_station(self, nom):
        """Un emplacement d'identifiant propre à une station, dans le bac à sable du test."""
        return self.parent / nom / "ecrivain.id"

    def test_l_identifiant_est_tire_une_fois_et_relu_tel_quel(self):
        """Le premier tirage crée le fichier ; les lectures suivantes le rendent tel quel."""
        chemin = self.chemin_de_station("station")
        premier = SOCLE._identifiant_d_ecrivain(chemin)
        self.assertTrue(premier, "un identifiant vide ne distinguerait aucune station")
        self.assertEqual(premier, chemin.read_text(encoding="utf-8").strip())
        self.assertEqual(premier, SOCLE._identifiant_d_ecrivain(chemin),
                         "l'identifiant d'une station ne change pas d'une lecture à l'autre")
        self.assertEqual([], list(chemin.parent.glob("*.tmp")),
                         "l'écriture ne laisse pas de fichier temporaire derrière elle")

    def test_une_creation_n_ecrase_pas_un_identifiant_deja_pose(self):
        """Le premier tirage fait foi : un second n'écrase pas un identifiant utilisable.

        C'est ce qui fait **converger** deux stations qui se créent au même instant :
        l'une pose, l'autre **lit** — elle ne remplace pas. Sans cette exclusivité, deux
        processus tireraient deux identifiants et se prendraient l'un l'autre pour un
        « second écrivain » (§7.4).
        """
        chemin = self.chemin_de_station("station-courante")
        self.assertTrue(SOCLE._poser_l_identifiant(chemin, "le-premier"))
        self.assertTrue(SOCLE._poser_l_identifiant(chemin, "le-second"))
        self.assertEqual("le-premier", chemin.read_text(encoding="utf-8").strip(),
                         "un identifiant déjà posé n'est jamais écrasé")

    def test_un_fichier_d_identifiant_vide_est_repare(self):
        """Un fichier présent mais **vide** est réparé, pas contourné en silence.

        Un fichier vide est ce qu'une course à la première création aurait pu laisser,
        ou ce qu'un disque plein a tronqué : le laisser tel quel ferait retomber, sans
        rien dire, sur l'empreinte de ``/etc/machine-id`` — et deux stations clonées se
        confondraient de nouveau. On tire donc un nouvel identifiant, et on l'écrit.
        """
        chemin = self.chemin_de_station("station-vide")
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text("", encoding="utf-8")
        repare = SOCLE._identifiant_d_ecrivain(chemin)
        self.assertTrue(repare, "le tirage rend toujours un identifiant")
        self.assertEqual(repare, chemin.read_text(encoding="utf-8").strip(),
                         "l'identifiant rendu est celui que le fichier porte")
        self.assertNotEqual(SOCLE._machine(), repare,
                            "un fichier vide ne fait pas retomber sur l'empreinte")

    def test_un_fichier_d_identifiant_illisible_est_repare(self):
        """Un fichier **illisible** est réparé lui aussi : on tire et on remplace."""
        if getattr(os, "geteuid", lambda: -1)() == 0:
            self.skipTest("root lit un fichier fermé : le cas ne se reproduit pas")
        chemin = self.chemin_de_station("station-fermee")
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text("un identifiant que personne ne peut lire\n", encoding="utf-8")
        chemin.chmod(0o000)
        self.addCleanup(chemin.chmod, 0o600)
        repare = SOCLE._identifiant_d_ecrivain(chemin)
        self.assertTrue(repare, "l'illisible est réparé, pas contourné")
        self.assertNotEqual("un identifiant que personne ne peut lire", repare)
        self.assertEqual(repare, chemin.read_text(encoding="utf-8").strip(),
                         "le fichier est devenu lisible et porte le nouvel identifiant")

    def test_le_banc_ne_touche_pas_au_vrai_dossier_personnel(self):
        """Le banc force ``OBSIA_ECRIVAIN_ID_FICHIER`` : rien ne s'écrit dans le vrai ``$HOME``.

        Un test qui prenait un verrou faisait tirer, pour de bon, l'identifiant de la
        **station du développeur** — un fichier dans son dossier personnel, créé par une
        exécution de tests. On exige donc que l'emplacement résolu reste dans le bac à
        sable du test, et que le fichier du vrai ``$HOME`` n'y soit pas touché.
        """
        defaut = Path.home() / ".local" / "state" / "obsia" / SOCLE.IDENTIFIANT_ECRIVAIN
        avant = defaut.read_text(encoding="utf-8") if defaut.exists() else None
        verrou = SOCLE.Verrou(self.dossier_git())
        self.assertTrue(verrou.__enter__())
        try:
            chemin = SOCLE._chemin_de_l_identifiant()
        finally:
            verrou.__exit__()
        self.assertTrue(str(chemin).startswith(str(self.parent)),
                        "le banc doit forcer l'emplacement dans son bac à sable, "
                        "pas dans le vrai dossier personnel")
        apres = defaut.read_text(encoding="utf-8") if defaut.exists() else None
        self.assertEqual(avant, apres, "rien ne s'écrit dans le vrai dossier personnel")

    def test_deux_stations_de_la_meme_machine_ne_se_confondent_pas(self):
        """Même ``/etc/machine-id`` : deux stations ont pourtant deux identifiants.

        C'est le cœur du résidu : sans cela, deux stations clonées porteraient le
        même identifiant et le refus du « second écrivain » ne se déclencherait pas.
        """
        une = SOCLE._identifiant_d_ecrivain(self.chemin_de_station("station-a"))
        autre = SOCLE._identifiant_d_ecrivain(self.chemin_de_station("station-b"))
        self.assertNotEqual(une, autre)
        self.assertNotEqual(SOCLE._machine(), une,
                            "l'identifiant n'est plus l'empreinte de la machine")

    def test_l_identifiant_ne_vit_ni_dans_le_coffre_ni_dans_le_git(self):
        """L'emplacement par défaut sort du dépôt — il ne voyage pas avec les clones."""
        propre = {"XDG_STATE_HOME": str(self.parent / "etat")}
        with mock.patch.dict(os.environ, propre, clear=True):
            # `clear=True` défait le forçage du banc : on éprouve ici l'emplacement **par défaut**.
            chemin = SOCLE._chemin_de_l_identifiant()
        self.assertFalse(str(chemin).startswith(str(self.coffre) + os.sep),
                         "l'identifiant d'une station ne vit pas dans le coffre")
        self.assertNotIn(".git", chemin.parts, "…ni dans le .git, qui se synchronise")

    def test_l_emplacement_se_force_par_l_environnement(self):
        """Un emplacement explicite l'emporte — pour les tests et les stations partagées."""
        force = self.parent / "ailleurs" / "id"
        with mock.patch.dict(os.environ, {"OBSIA_ECRIVAIN_ID_FICHIER": str(force)}):
            self.assertEqual(force, SOCLE._chemin_de_l_identifiant())
            tire = SOCLE._identifiant_d_ecrivain()
        self.assertEqual(force.read_text(encoding="utf-8").strip(), tire,
                         "l'identifiant suit l'emplacement forcé")

    def test_un_emplacement_impossible_retombe_sur_l_empreinte_de_la_machine(self):
        """Emplacement inscriptible impossible : repli sur l'empreinte, jamais un échec.

        La station n'a pas à refuser d'écrire parce qu'elle ne peut pas garder son
        identifiant : elle se rabat alors sur l'empreinte de ``/etc/machine-id``,
        qui reste déterministe d'une exécution à l'autre.
        """
        obstacle = self.parent / "un-fichier-pas-un-dossier"
        obstacle.write_text("un fichier\n", encoding="utf-8")
        chemin = obstacle / "ecrivain.id"
        self.assertEqual(SOCLE._machine(), SOCLE._identifiant_d_ecrivain(chemin))


class TestLeMenageDeReprise(BaseDeLaConcurrence):
    """Le ménage de reprise retire l'index orphelin d'un mort — **jamais** la garde (f).

    L'index dédié d'un acte (``.git/obsia-ecriture.index-*``) disparaît à la sortie
    normale de l'acte. Un acte **tué** entre l'ouverture de cet index et sa fermeture
    en laisse un orphelin, qui ne sert plus à personne et s'accumulerait. La reprise le
    retire — mais elle ne touche **jamais** la garde, dont l'inode porte le ``flock``,
    ni le journal des incidents, ni le marqueur des remontées.
    """

    def poser_index(self, pid):
        """Un index dédié posé comme le laisserait un acte mort — ou vivant, selon le pid."""
        fichier = self.dossier_git() / ("%s-%d" % (SOCLE.INDEX, pid))
        fichier.write_text("index dédié d'un acte\n", encoding="utf-8")
        return fichier

    def test_le_menage_retire_l_index_d_un_ecrivain_mort(self):
        """Un index dont le pid est mort est un orphelin : le ménage le retire et le nomme."""
        orphelin = self.poser_index(999_999_999)
        retires = SOCLE._menage_de_reprise(self.dossier_git())
        self.assertIn(orphelin.name, retires)
        self.assertFalse(orphelin.exists())

    def test_le_menage_laisse_l_index_d_un_ecrivain_vivant(self):
        """L'index d'un processus vivant n'est pas un orphelin : on n'y touche pas."""
        vivant = self.poser_index(os.getpid())
        SOCLE._menage_de_reprise(self.dossier_git())
        self.assertTrue(vivant.exists(), "un index en cours d'usage n'est pas retiré")

    def test_le_menage_ne_retire_ni_la_garde_ni_les_journaux(self):
        """La garde porte le ``flock`` : elle ne se supprime **jamais**, pas plus que les journaux."""
        intouchables = {}
        for nom in (SOCLE.GARDE, SOCLE.INCIDENTS, SOCLE.REMONTES):
            fichier = self.dossier_git() / nom
            fichier.write_text("à garder\n", encoding="utf-8")
            intouchables[nom] = fichier
        SOCLE._menage_de_reprise(self.dossier_git())
        for nom, fichier in intouchables.items():
            self.assertTrue(fichier.exists(), "%s ne doit jamais être retiré" % nom)

    def test_la_reprise_retire_l_index_orphelin_du_mort(self):
        """De bout en bout : la reprise d'un verrou périmé emporte l'index orphelin."""
        orphelin = self.poser_index(999_999_999)
        self.poser_verrou(pid=999_999_999)
        socle = SOCLE.Verrou(self.dossier_git())
        self.assertTrue(socle.__enter__())
        try:
            self.assertFalse(orphelin.exists(),
                             "le ménage de reprise emporte l'index du mort")
        finally:
            socle.__exit__()

    def test_la_documentation_dit_l_exigence_et_la_regle(self):
        """Le socle écrit noir sur blanc l'exigence de version et la garde intouchable.

        La règle « la garde ne se supprime jamais » n'a de valeur que si on peut la
        lire là où le code la pose : le docstring du socle est cet endroit.
        """
        doc = SOCLE.__doc__ or ""
        self.assertIn("2.36", doc, "l'exigence « git ≥ 2.36 » doit être écrite")
        self.assertIn(SOCLE.GARDE, doc, "la garde doit être nommée telle quelle")
        self.assertIn("ne se supprime jamais", doc)
        self.assertIn(SOCLE.INDEX + "-*", doc, "le ménage doit nommer l'index orphelin")


if __name__ == "__main__":
    unittest.main()
