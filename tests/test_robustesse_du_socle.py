#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""La **robustesse du socle d'écriture** — lot « avant P6 », onze points.

Ces tests figent ce que le socle doit tenir hors du cas nominal (§7.4) :

1. **fichier d'identité sans liens physiques** : là où ``os.link`` est refusé (FAT,
   SMB, montages réseau), l'identifiant est posé par une création **exclusive**
   — **jamais** par un repli silencieux sur l'empreinte de la machine ;
2. **le motif d'un refus de garde dit la vérité** : quand l'échec n'est pas une
   contention, il **ne dit pas** qu'un verrou est déjà posé ;
3. ``EINTR`` sur ``flock`` est **réessayé**, pas pris pour un refus ;
4. une **ouverture impossible** du fichier de garde donne un refus **motivé**, pas une
   ``OSError`` brute ;
5. la **fenêtre de ``checkout``** : la branche du répertoire de travail est **relue**
   juste avant l'échange, et l'acte refuse si elle a changé ;
6. **ce qu'un crochet ``pre-commit`` indexe n'entre pas dans le commit** : l'arbre est
   écrit **avant** le crochet, le commit porte exactement la pose de l'acte ; un
   crochet qui **réécrit** les fichiers sur le disque laisse, lui, après un acte
   réussi, un disque **différent du commit** ;
7. le **ménage de reprise** est **consigné** et **remonte avec les incidents** vers
   l'agent — il ne disparaît pas en silence ;
8. **pid recyclé côté ménage** : le ménage joint au pid le **même marqueur de
   naissance** que le verrou, pour ne pas prendre l'index d'un mort pour celui d'un
   vivant ;
9. **le verrou naît entier ou pas du tout** : la fiche est écrite dans un
   **temporaire** puis publiée par ``os.link`` ; un processus tué entre la création
   et la fiche ne laisse plus un verrou **vide** — un coffre verrouillé à vie. Là où
   les liens physiques sont refusés (FAT, SMB), le repli **réserve le nom puis publie
   la fiche par ``os.replace``** : le nom est **vide un court instant**, donc un
   verrou vide n'est **pas** forcément un reste mort — un écrivain **vivant** peut
   être en train de le poser. Un verrou vide **n'est jamais retiré** : la reprise
   refuse (§7.4), et son motif nomme le **fichier exact** et le **geste humain** en
   prévenant que le retirer pendant qu'un écrivain le tient laisserait **deux
   écrivains** écrire ; un verrou **illisible** garde, lui, le refus historique ;
10. **le repli de l'identifiant est privé** : là où les liens physiques manquent,
   le fichier est créé en ``0600``, jamais en ``0644`` ;
11. **le repli publie par un remplacement atomique** : le nom réservé est remplacé
   d'un geste, jamais un identifiant partiel ; la *fenêtre* où le nom est vide est
   documentée, faute de renommage « sans écrasement » dans ``os``.
"""

import errno
import json
import os
import stat
import sys
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

from test_ecrivain import git                                          # noqa: E402
from test_gestes_des_notes import chemins_du_commit, note              # noqa: E402
from test_p5_concurrence_et_panne import BaseDeLaConcurrence           # noqa: E402

import serveur.socle_ecriture as SOCLE                                 # noqa: E402


class BaseDeLaRobustesse(BaseDeLaConcurrence):
    """De quoi éprouver les onze points — le coffre, le verrou, l'index, les crochets."""

    def sans_liens_physiques(self, numero=errno.EPERM):
        """Un ``os.link`` qui refuse comme FAT ou SMB — posé le temps d'une épreuve."""
        vrai = SOCLE.os.link

        def lien_refuse(*args, **kwargs):
            raise OSError(numero, os.strerror(numero))

        SOCLE.os.link = lien_refuse
        self.addCleanup(setattr, SOCLE.os, "link", vrai)

    def chemin_de_station(self, nom="station"):
        return self.parent / "etats" / nom / SOCLE.IDENTIFIANT_ECRIVAIN

    def poser_index(self, numero, marque=None):
        """Un index dédié laissé dans ``.git``, comme après un acte tué."""
        nom = (("%s-%d" % (SOCLE.INDEX, numero)) if marque is None
               else ("%s-%d-%s" % (SOCLE.INDEX, numero, marque)))
        reste = self.dossier_git() / nom
        reste.write_bytes(b"index d'essai\n")
        return reste

    def poser_un_crochet_qui_indexe(self):
        """Un ``pre-commit`` qui ajoute un fichier à l'index **et le consigne**."""
        crochet = self.dossier_git() / "hooks" / "pre-commit"
        crochet.parent.mkdir(parents=True, exist_ok=True)
        crochet.write_text(
            "#!/bin/sh\n"
            "racine=$(git rev-parse --show-toplevel) || exit 0\n"
            "cd \"$racine\" || exit 0\n"
            ": > extra.txt\n"
            "git add -- extra.txt\n"
            "git diff --cached --name-only > index-du-crochet.txt\n"
            "exit 0\n",
            encoding="utf-8")
        os.chmod(crochet, 0o755)
        return crochet


class TestLIdentifiantSansLiensPhysiques(BaseDeLaRobustesse):
    """Point 1 — sans liens physiques, on garde un identifiant **tiré**."""

    def test_un_systeme_sans_liens_physiques_se_replie_sur_la_creation_exclusive(self):
        self.sans_liens_physiques()
        chemin = self.chemin_de_station()
        tire = SOCLE._identifiant_d_ecrivain(chemin)
        self.assertTrue(tire)
        self.assertNotEqual(SOCLE._machine(), tire,
                            "on ne retombe **pas** en silence sur l'empreinte de machine")
        self.assertEqual(tire, chemin.read_text(encoding="utf-8").strip())
        self.assertEqual(tire, SOCLE._identifiant_d_ecrivain(chemin), "relu tel quel")
        self.assertEqual((), tuple(chemin.parent.glob("*.tmp")),
                         "aucun fichier temporaire laissé derrière soi")

    def test_un_systeme_sans_liens_physiques_ne_remplace_pas_un_identifiant_pose(self):
        chemin = self.chemin_de_station("prise")
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text("deja-la\n", encoding="utf-8")
        self.sans_liens_physiques()
        self.assertTrue(SOCLE._poser_l_identifiant(chemin, "un-autre"),
                        "l'emplacement a bien été tenu sans liens physiques")
        self.assertEqual("deja-la", chemin.read_text(encoding="utf-8").strip(),
                         "un identifiant déjà utilisable n'est jamais écrasé")
        self.assertEqual("deja-la", SOCLE._identifiant_d_ecrivain(chemin))

    def test_un_systeme_sans_liens_physiques_repare_un_fichier_vide(self):
        chemin = self.chemin_de_station("vide")
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text("", encoding="utf-8")
        self.sans_liens_physiques()
        tire = SOCLE._identifiant_d_ecrivain(chemin)
        self.assertTrue(tire)
        self.assertNotEqual(SOCLE._machine(), tire)
        self.assertEqual(tire, chemin.read_text(encoding="utf-8").strip())

    def test_le_repli_cree_le_fichier_en_0600(self):
        """Le repli protège le nom exactement comme ``mkstemp`` : mode ``0600``."""
        self.sans_liens_physiques()
        chemin = self.chemin_de_station("mode")
        self.assertTrue(SOCLE._poser_l_identifiant(chemin, "tire"))
        self.assertEqual(0o600, stat.S_IMODE(chemin.stat().st_mode),
                         "un identifiant de station est privé : 0600, jamais 0644")

    def test_le_repli_publie_l_identifiant_par_un_remplacement_atomique(self):
        """Le repli **réserve** le nom puis le remplace : jamais un identifiant partiel."""
        self.sans_liens_physiques()
        chemin = self.chemin_de_station("renomme")
        vus = []
        vrai_remplacement = SOCLE.os.replace

        def remplacement_observant(source, cible, **reste):
            # À l'instant du remplacement, le nom officiel existe (réservé) mais
            # **vide** : il ne montre jamais un identifiant à moitié écrit.
            cible = Path(cible)
            vus.append(cible.read_text(encoding="utf-8") if cible.exists() else None)
            return vrai_remplacement(source, cible, **reste)

        with mock.patch.object(SOCLE.os, "replace", remplacement_observant):
            self.assertTrue(SOCLE._poser_l_identifiant(chemin, "tire"))
        self.assertEqual([""], vus,
                         "le repli publie par un remplacement atomique du nom réservé")
        self.assertEqual("tire", chemin.read_text(encoding="utf-8").strip())
        self.assertEqual([], list(chemin.parent.glob("*.tmp")),
                         "aucun temporaire ne reste après la publication")

    def test_la_documentation_dit_la_fenetre_du_repli(self):
        doc = " ".join((SOCLE._installer_l_identifiant.__doc__ or "").split())
        self.assertIn("fenêtre", doc.lower())
        self.assertIn("vide", doc)
        self.assertIn("sans écrasement", doc)


class TestLaGardeDitSonEchec(BaseDeLaRobustesse):
    """Points 2, 3 et 4 — la garde refuse **en disant pourquoi**."""

    def test_une_erreur_de_verrou_ne_se_dit_pas_comme_un_verrou_pose(self):
        if SOCLE.fcntl is None:
            self.skipTest("« flock » manque hors POSIX")
        vrai = SOCLE.fcntl.flock

        def flock_impossible(*args, **kwargs):
            raise OSError(errno.ENOLCK, os.strerror(errno.ENOLCK))

        SOCLE.fcntl.flock = flock_impossible
        self.addCleanup(setattr, SOCLE.fcntl, "flock", vrai)
        verrou = SOCLE.Verrou(self.dossier_git(), delai=5.0)
        self.assertFalse(verrou.__enter__())
        self.assertFalse(verrou.motif.startswith("un verrou d'écriture est déjà posé"),
                         verrou.motif)
        self.assertNotIn("un verrou d'écriture est déjà posé", verrou.motif)
        self.assertIn("ENOLCK", verrou.motif, "le motif nomme l'erreur")

    def test_un_flock_interrompu_est_reessaye_au_lieu_de_refuser(self):
        if SOCLE.fcntl is None:
            self.skipTest("« flock » manque hors POSIX")
        vrai = SOCLE.fcntl.flock
        essais = []

        def flock_interrompu(descripteur, operation):
            if operation != SOCLE.fcntl.LOCK_UN:
                essais.append(operation)
                if len(essais) == 1:
                    raise OSError(errno.EINTR, os.strerror(errno.EINTR))
            return vrai(descripteur, operation)

        SOCLE.fcntl.flock = flock_interrompu
        self.addCleanup(setattr, SOCLE.fcntl, "flock", vrai)
        verrou = SOCLE.Verrou(self.dossier_git(), delai=1.0)
        self.assertTrue(verrou.__enter__(),
                        "EINTR est un intermède, pas un refus : %s" % verrou.motif)
        verrou.__exit__(None, None, None)
        self.assertEqual(2, len(essais), "le verrouillage a été réessayé après EINTR")

    def test_une_ouverture_de_garde_impossible_refuse_en_nommant_l_erreur(self):
        def ouvrir_impossible(*args, **kwargs):
            raise OSError(errno.EACCES, os.strerror(errno.EACCES))

        with mock.patch.object(SOCLE.os, "open", ouvrir_impossible):
            with self.assertRaises(SOCLE.GardeNonPrise) as pris:
                with SOCLE._garde(self.dossier_git()):
                    pass
            self.assertIn("EACCES", str(pris.exception),
                          "l'ouverture impossible est nommée, pas une OSError brute")
            self.assertFalse(str(pris.exception).startswith(
                "un verrou d'écriture est déjà posé"))
            verrou = SOCLE.Verrou(self.dossier_git())
            self.assertFalse(verrou.__enter__())
        self.assertIn("EACCES", verrou.motif)
        self.assertFalse(verrou.motif.startswith("un verrou d'écriture est déjà posé"))


class TestLaFenetreDuCheckout(BaseDeLaRobustesse):
    """Point 5 — la branche du répertoire de travail est relue juste avant l'échange."""

    CHEMIN = "0-SAVOIRS/note.md"

    def test_une_branche_changee_juste_avant_l_echange_fait_refuser(self):
        base = note(corps="\n\nUn corps.\n")
        self.poser_note(self.CHEMIN, base)
        tenu = base + "\n\nSuite.\n"
        (self.coffre / self.CHEMIN).write_text(tenu, encoding="utf-8")
        depart = self.tete()

        def basculer(coffre, reference):
            # Un `git checkout` qui déplace HEAD **dans la fenêtre**, entre la
            # vérification de la branche par défaut et l'échange.
            git(coffre, "symbolic-ref", "HEAD", "refs/heads/une-autre-branche")

        commit, motif = SOCLE._committer(
            self.coffre, {self.CHEMIN: base.encode("utf-8")}, "Compléter : note",
            tete_attendue=depart, ecrits={self.CHEMIN: tenu},
            avant_l_echange=basculer)

        self.assertIsNone(commit, motif)
        self.assertIn("répertoire de travail a changé", motif)
        self.assertEqual(base, self.lire(self.CHEMIN), "l'écriture a été défaite")
        self.assertEqual(depart,
                         git(self.coffre, "rev-parse", "refs/heads/main").stdout.strip(),
                         "la branche par défaut n'a pas bougé")


class TestLeCrochetQuiIndexe(BaseDeLaRobustesse):
    """Point 6 — ce qu'un crochet indexe n'entre pas dans le commit."""

    def test_ce_qu_un_crochet_ajoute_a_l_index_n_entre_pas_dans_le_commit(self):
        self.poser_un_crochet_qui_indexe()
        acte = self.ecrire()
        self.assertIsNone(acte.refus, acte.refus)
        portes = chemins_du_commit(self.coffre, acte.commit)
        self.assertEqual((self.CHEMIN, self.COPIE), portes,
                         "le commit porte exactement la pose de l'acte, rien de plus")
        self.assertIn("extra.txt", self.lire("index-du-crochet.txt"),
                      "le crochet a bien indexé son fichier — et il n'est pas entré")

    def test_la_documentation_dit_que_l_arbre_precede_le_crochet(self):
        doc = SOCLE._committer.__doc__
        self.assertIn("write-tree", doc)
        self.assertIn("pre-commit", doc)
        self.assertIn("n'entre pas dans le commit", doc)

    def test_la_documentation_dit_que_le_crochet_peut_diverger_le_disque(self):
        """Un crochet qui **réécrit** les fichiers laisse un disque ≠ commit."""
        doc = SOCLE._committer.__doc__
        self.assertIn("réécrit", doc)
        self.assertIn("disque", doc)
        self.assertIn("différent du commit", doc)


class TestLeMenageEstRapporte(BaseDeLaRobustesse):
    """Point 7 — le ménage de reprise est consigné et remonte avec les incidents."""

    def test_le_menage_est_consigne_et_remonte_avec_les_incidents(self):
        orphelin = self.poser_index(999_999_999)             # mort : sera retiré
        self.poser_verrou(pid=999_999_999)
        verrou = SOCLE.Verrou(self.dossier_git(), delai=1.0)
        self.assertTrue(verrou.__enter__(), verrou.motif)
        verrou.__exit__(None, None, None)
        self.assertFalse(orphelin.exists(), "le ménage a retiré l'orphelin")
        remontes = SOCLE.incidents_non_remontes(self.coffre)
        self.assertTrue(any("ménage" in ligne and orphelin.name in ligne
                            for ligne in remontes),
                        "le ménage doit remonter avec les incidents : %s" % (remontes,))


class TestLeMenageEtLePidRecycle(BaseDeLaRobustesse):
    """Point 8 — le ménage joint au pid le marqueur de naissance, comme le verrou."""

    def test_le_nom_de_l_index_porte_et_relit_la_naissance(self):
        pid = os.getpid()
        nom = SOCLE._nom_de_l_index(pid)
        self.assertEqual((pid, SOCLE._marque_de_naissance(pid)),
                         SOCLE._reste_de_l_index(nom))
        self.assertEqual((4321, None),
                         SOCLE._reste_de_l_index("%s-4321" % SOCLE.INDEX),
                         "un nom d'avant, sans marqueur, reste lisible")

    def test_le_menage_retire_l_index_d_un_pid_recycle(self):
        # Notre pid est vivant, mais le marqueur inscrit est celui d'un **autre**
        # processus : le noyau a recyclé le numéro. Ce n'est donc pas le nôtre.
        reste = self.poser_index(os.getpid(), "0000dead")
        self.assertEqual((reste.name,), SOCLE._menage_de_reprise(self.dossier_git()))
        self.assertFalse(reste.exists())

    def test_le_menage_laisse_l_index_dont_la_naissance_correspond(self):
        reste = self.poser_index(os.getpid(), SOCLE._marque_de_naissance(os.getpid()))
        self.assertEqual((), SOCLE._menage_de_reprise(self.dossier_git()))
        self.assertTrue(reste.exists(), "un index dont l'écrivain est vivant reste en place")


class TestLeVerrouNaissantEntier(BaseDeLaRobustesse):
    """Point 9 — le verrou est publié **entier ou pas du tout**, jamais vide."""

    def test_le_verrou_est_publie_entier_par_le_lien(self):
        """À l'instant de la pose, le nom du verrou n'existe pas encore."""
        etat = {}
        vrai_lien = SOCLE.os.link

        def lien_observant(source, cible, **reste):
            etat["nom_absent_a_la_pose"] = not Path(cible).exists()
            return vrai_lien(source, cible, **reste)

        verrou = SOCLE.Verrou(self.dossier_git())
        with mock.patch.object(SOCLE.os, "link", lien_observant):
            self.assertTrue(verrou._prendre())
        try:
            self.assertTrue(etat.get("nom_absent_a_la_pose"),
                            "le verrou est publié par le lien, pas créé vide d'abord")
            fiche = json.loads((self.dossier_git() / SOCLE.VERROU)
                               .read_text(encoding="utf-8"))
            self.assertEqual(SOCLE.OUTIL, fiche["outil"])
            self.assertEqual(os.getpid(), fiche["pid"])
            self.assertEqual((), tuple(self.dossier_git().glob(SOCLE.VERROU + ".*")),
                             "aucun temporaire ne reste après la pose")
        finally:
            verrou.__exit__(None, None, None)

    def test_un_ecrivain_qui_perd_la_course_relit_la_fiche_du_gagnant(self):
        """Le lien échoue sur un nom pris : le perdant relit la fiche, jamais un vide."""
        fiche_gagnante = {"outil": SOCLE.OUTIL, "pid": 424242,
                          "machine": "station-du-gagnant", "naiss": None,
                          "pose": "2026-01-05T00:00:00+00:00"}

        def lien_perdant(source, cible, **reste):
            # Le gagnant a publié sa fiche un cheveu avant nous : le lien échoue.
            Path(cible).write_text(json.dumps(fiche_gagnante) + "\n", encoding="utf-8")
            raise FileExistsError(errno.EEXIST, os.strerror(errno.EEXIST), str(cible))

        verrou = SOCLE.Verrou(self.dossier_git())
        with mock.patch.object(SOCLE.os, "link", lien_perdant):
            self.assertFalse(verrou._prendre(), "le nom est pris : le lien échoue")
        try:
            porteur = verrou._proprietaire()
            self.assertIsNotNone(porteur, "le perdant relit la fiche du gagnant")
            self.assertEqual(424242, porteur["pid"])
        finally:
            (self.dossier_git() / SOCLE.VERROU).unlink(missing_ok=True)

    def test_un_verrou_vide_est_refuse_sans_etre_retire(self):
        """Un verrou vide n'a **aucune** identité : on refuse, on ne le retire pas.

        On ne peut pas dire **pourquoi** il est vide : sans liens physiques,
        ``_prendre`` réserve le nom vide un court instant avant d'y publier sa fiche
        (voir ``test_le_repli_sans_liens_physiques_montre_un_verrou_vide_un_instant``),
        donc un écrivain **vivant** peut être en train de le poser. §7.4 interdit
        d'écraser un verrou qu'on ne peut pas lire, et rien ne prouve que son porteur
        est mort : la reprise **refuse**, sans retrait automatique, et **laisse le
        fichier en place**. C'est à l'humain, qui sait la station libre, de le retirer.
        """
        verrou = self.dossier_git() / SOCLE.VERROU
        verrou.write_text("", encoding="utf-8")
        try:
            socle = SOCLE.Verrou(self.dossier_git())
            self.assertFalse(socle.__enter__())
            self.assertIn("vide", socle.motif)
            self.assertTrue(verrou.exists(), "un verrou vide n'est jamais retiré tout seul")
        finally:
            verrou.unlink(missing_ok=True)

    def test_le_motif_du_verrou_vide_nomme_le_fichier_et_le_geste(self):
        """Le refus d'un verrou vide dit **quel** fichier, et **quoi** faire.

        On garde le refus et on ne retire rien d'office, mais le motif nomme le
        **fichier exact** et le **geste humain** : vérifier qu'aucun écrivain ne tourne,
        puis le supprimer à la main. Il **ne dit pas la cause** du vide — un écrivain
        vivant peut être en train de poser le verrou — et il **prévient** que le
        supprimer pendant qu'un écrivain le tient laisserait deux écrivains écrire.
        """
        verrou = self.dossier_git() / SOCLE.VERROU
        verrou.write_text("", encoding="utf-8")
        try:
            socle = SOCLE.Verrou(self.dossier_git())
            self.assertFalse(socle.__enter__())
            motif = socle.motif
            self.assertIn(str(verrou), motif, "le motif doit nommer le fichier exact")
            self.assertIn("aucun écrivain", motif)
            self.assertIn("supprime", motif.lower())
            self.assertNotIn("reste d'une version d'avant", motif,
                             "le motif ne doit plus affirmer la cause du vide")
            self.assertIn("vivant", motif,
                          "le motif doit prévenir qu'un écrivain vivant peut le poser")
            self.assertIn("deux écrivains", motif,
                          "le motif doit dire le risque : deux écrivains à la fois")
        finally:
            verrou.unlink(missing_ok=True)

    def test_un_verrou_illisible_garde_le_motif_historique(self):
        """Un verrou **illisible** (non vide) garde le refus mot pour mot d'avant."""
        verrou = self.dossier_git() / SOCLE.VERROU
        verrou.write_text("un autre acte tient le verrou\n", encoding="utf-8")
        try:
            socle = SOCLE.Verrou(self.dossier_git())
            self.assertFalse(socle.__enter__())
            self.assertIn("un autre acte écrit peut-être à cet instant", socle.motif)
        finally:
            verrou.unlink(missing_ok=True)

    def test_le_repli_sans_liens_physiques_montre_un_verrou_vide_un_instant(self):
        """Sans liens physiques, ``_prendre`` **réserve** le nom **vide** un court instant.

        Le nom est réservé en ``O_CREAT|O_EXCL`` puis la fiche publiée par
        ``os.replace`` : entre les deux, le verrou existe et ne porte **rien**. C'est
        cette fenêtre qui interdit d'affirmer qu'un verrou vide est forcément un reste
        mort — un écrivain **vivant** peut l'avoir posé à cet instant même.
        """
        self.sans_liens_physiques()
        verrou = self.dossier_git() / SOCLE.VERROU
        vus = []
        vrai_remplacement = SOCLE.os.replace

        def remplacement_observant(source, cible, **reste):
            # À l'instant du remplacement, le nom est réservé mais **vide**.
            cible = Path(cible)
            vus.append(cible.read_text(encoding="utf-8") if cible.exists() else None)
            return vrai_remplacement(source, cible, **reste)

        socle = SOCLE.Verrou(self.dossier_git())
        with mock.patch.object(SOCLE.os, "replace", remplacement_observant):
            self.assertTrue(socle._prendre(), "le repli réserve le nom et publie la fiche")
        try:
            self.assertEqual([""], vus,
                             "entre la réservation et la publication, le verrou est vide")
            fiche = json.loads(verrou.read_text(encoding="utf-8"))
            self.assertEqual(SOCLE.OUTIL, fiche["outil"])
            self.assertEqual(os.getpid(), fiche["pid"])
            self.assertEqual((), tuple(self.dossier_git().glob(SOCLE.VERROU + ".*")),
                             "aucun temporaire ne reste après le repli")
        finally:
            socle.__exit__(None, None, None)

    def test_des_blancs_seuls_comptent_comme_vide(self):
        """Un verrou fait de blancs seuls est **vide** : on le refuse comme tel.

        ``_verrou_vide`` lit puis retire les blancs : un fichier qui ne porte qu'un
        saut de ligne, des espaces ou une tabulation n'est pas un verrou « illisible »
        — c'est un verrou **vide**, refusé avec le motif qui nomme le fichier et le
        geste humain.
        """
        verrou = self.dossier_git() / SOCLE.VERROU
        verrou.write_text("  \n\t\n  \n", encoding="utf-8")
        try:
            socle = SOCLE.Verrou(self.dossier_git())
            self.assertFalse(socle.__enter__())
            self.assertIn("vide", socle.motif)
            self.assertIn(str(verrou), socle.motif,
                          "des blancs seuls : le motif vide, pas le motif historique")
        finally:
            verrou.unlink(missing_ok=True)

    def test_la_documentation_dit_que_des_blancs_comptent_comme_vide(self):
        """La docstring de ``_verrou_vide`` doit dire que des blancs seuls = vide."""
        doc = " ".join((SOCLE.Verrou._verrou_vide.__doc__ or "").split())
        self.assertNotIn(
            "pas même des blancs", doc,
            "la docstring affirmait le contraire : « rien, pas même des blancs »")
        self.assertIn("vide", doc)
        self.assertIn("blancs", doc,
                      "la docstring doit dire que des blancs seuls comptent comme vide")
        self.assertIn("blancs seuls", doc)

    def test_la_documentation_dit_que_le_verrou_nait_entier(self):
        classe = " ".join((SOCLE.Verrou.__doc__ or "").split())
        prise = " ".join((SOCLE.Verrou._prendre.__doc__ or "").split())
        self.assertIn("os.link", classe)
        self.assertIn("temporaire", prise)
        self.assertIn("vide", prise)


if __name__ == "__main__":
    unittest.main()
