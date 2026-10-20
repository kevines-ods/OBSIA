#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Les gestes des notes — ranger une note du vrac, compléter une note sur place.

Ces tests figent le contrat de la phase 4 : le rangement vient **du vrac seul**,
garde le nom exact, refuse un homonyme du coffre entier, et fait voyager le
registre `notes_remplies.md` dans le **même** commit. La complétion n'ajoute
qu'à la fin du corps, ne retire ni ne modifie une clé du frontmatter, et ne fait
croître `tags` que vers le vocabulaire contrôlé — le **seul** retrait permis étant
celui d'un tag hors vocabulaire (§7.5). Elle ne touche ni une note d'une zone où
la matrice la ferme, ni un résumé, une vision, des préférences ou une expérience :
ces genres se tiennent au fil de l'eau, hors P4 — mais elle **tient désormais au fil
de l'eau un carnet** d'un projet ou d'un chantier, que le contrat reconnaît comme une
note tenue sur place (phase 5, §7.3). Un refus n'écrit
rien ; un acte dont le commit est refusé se défait **sans perdre** la note visée —
un fichier créé s'efface, un fichier déplacé ou modifié se restaure à son contenu
d'avant, octet pour octet. L'écriture passe par le socle — encoder d'abord, puis
poser par fichier temporaire : un texte inencodable (demi-surrogate) échoue **sans**
avoir vidé la note, et toute exception rend un refus après avoir défait l'acte.
Chaque geste porte sa marque d'outil (`ranger-une-note`,
`completer-une-note`), que l'écrivain sait relire.

Un **seul aperçu par note, par dossier d'origine et par jour**
(`<date>-apercu-<dossier>--<nom>`) : le premier acte du jour lu à ce dossier le crée,
les suivants y ajoutent une section — deux commits, un fichier — et un acte raté rend
l'aperçu à son état d'avant. C'est le chemin normal du traitement : remplir, puis
classer, tous deux lus au vrac.
"""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
RACINE = Path(__file__).resolve().parent.parent
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))
if str(RACINE / "tests") not in sys.path:
    sys.path.insert(0, str(RACINE / "tests"))

from test_ecrivain import BaseDuCoffreDeTest, git  # noqa: E402

import serveur.ecrivain as ECRIVAIN                # noqa: E402
import serveur.gestes_des_notes as GESTES          # noqa: E402

sys.path.insert(0, str(RACINE / "scripts"))
import convention_des_notes as CONVENTION          # noqa: E402


def note(front: str = "kind: note\n---", corps: str = "\n\nUn corps.") -> str:
    """Une note d'essai : son frontmatter (sans les ``---``) puis son corps."""
    return "---\n%s%s" % (front, corps)


def chemins_du_commit(coffre, commit) -> tuple:
    """Les chemins portés par un commit, déplacement compris (les deux chemins)."""
    rendu = git(coffre, "-c", "core.quotePath=false", "show", "--name-status",
                "--format=", "-z", "--no-renames", str(commit))
    champs = rendu.stdout.split("\0")
    return tuple(sorted(champs[i + 1] for i in range(0, len(champs) - 1, 2)
                        if champs[i + 1]))


class BaseDesNotes(BaseDuCoffreDeTest):
    """Un coffre de test avec les zones d'une note et son registre d'amorce."""

    REGISTRE = "_MAINTENANCE/notes_remplies.md"
    AMORCE_REGISTRE = "# Notes Remplies (log)\n\nRegistre d'essai.\n"

    def setUp(self):
        super().setUp()
        for zone in ("0-EN-VRAC", "0-SAVOIRS", "0-DOCUMENTS"):
            (self.coffre / zone).mkdir(parents=True, exist_ok=True)
        (self.coffre / "_MAINTENANCE").mkdir(parents=True, exist_ok=True)
        self.ecrire_fichier(self.REGISTRE, self.AMORCE_REGISTRE)
        self.commiter("amorce des zones")

    def ecrire_fichier(self, relatif, texte):
        fichier = self.coffre / relatif
        fichier.parent.mkdir(parents=True, exist_ok=True)
        fichier.write_text(texte, encoding="utf-8")
        return fichier

    def commiter(self, message):
        git(self.coffre, "add", "-A")
        git(self.coffre, "commit", "--quiet", "-m", message)

    def poser_note(self, relatif, texte):
        self.ecrire_fichier(relatif, texte)
        self.commiter("note d'essai : %s" % relatif)
        return relatif

    def tete(self):
        return git(self.coffre, "rev-parse", "HEAD").stdout.strip()

    def lire(self, relatif):
        return (self.coffre / relatif).read_text(encoding="utf-8")


class TestLeRangement(BaseDesNotes):
    """Ranger déplace une note du vrac — elle ne se réécrit pas, elle change de zone."""

    def test_ranger_deplace_le_fichier_et_garde_son_nom(self):
        texte = note(corps="\n\nUne note à ranger.\n")
        self.poser_note("0-EN-VRAC/Idée Docker.md", texte)
        acte = GESTES.ranger_une_note(self.coffre, auteur=self.AUTEUR,
                                      source="0-EN-VRAC/Idée Docker.md",
                                      zone="0-SAVOIRS", date=self.DATE)
        self.assertIsNone(acte.refus, acte.refus)
        self.assertEqual("0-SAVOIRS/Idée Docker.md", acte.chemin)
        self.assertFalse((self.coffre / "0-EN-VRAC/Idée Docker.md").exists())
        self.assertEqual(texte, self.lire("0-SAVOIRS/Idée Docker.md"))

    def test_ranger_dans_un_dossier_jumeau_est_refuse(self):
        # F2 : `Réseau` et `reseau` se replient au même nom d'aperçu (§7.4) : deux
        # notes s'y disputeraient l'aperçu du jour. On ne sème pas le second dossier
        # — la règle qu'`ecrivain` tient déjà pour un projet ou un chantier (§6).
        (self.coffre / "0-SAVOIRS/Réseau").mkdir(parents=True, exist_ok=True)
        self.commiter("un dossier de savoirs")
        texte = note(corps="\n\nÀ ranger.\n")
        self.poser_note("0-EN-VRAC/Idée Docker.md", texte)
        acte = GESTES.ranger_une_note(self.coffre, auteur=self.AUTEUR,
                                      source="0-EN-VRAC/Idée Docker.md",
                                      zone="0-SAVOIRS/reseau", date=self.DATE)
        self.assertIsNotNone(acte.refus)
        self.assertIn("se replie au même nom", acte.refus)
        self.assertIn("Réseau", acte.refus)
        # Rien n'a bougé : la note est restée dans le vrac.
        self.assertEqual(texte, self.lire("0-EN-VRAC/Idée Docker.md"))

    def test_ranger_ne_change_pas_un_seul_octet(self):
        texte = note(corps="\n\nUne note au contenu exact.\n")
        self.poser_note("0-EN-VRAC/note.md", texte)
        GESTES.ranger_une_note(self.coffre, auteur=self.AUTEUR,
                               source="0-EN-VRAC/note.md", zone="0-SAVOIRS",
                               date=self.DATE)
        self.assertEqual(texte.encode("utf-8"),
                         (self.coffre / "0-SAVOIRS/note.md").read_bytes())

    def test_une_note_du_vrac_qui_commence_par_une_date_se_range(self):
        """F2 — une note datée du vrac n'est pas un carnet : elle se range.

        L'aperçu d'une note reprend son nom **tel quel**, date comprise, derrière son
        dossier d'origine ; seule la copie d'un carnet, rangée dans un ``carnets/``,
        retire la date que son nom porte déjà. Une note datée du vrac reste donc une
        note ordinaire, et son aperçu dit son dossier d'origine.
        """
        texte = note(corps="\n\nJournal du jour.\n")
        self.poser_note("0-EN-VRAC/2026-01-05-journal.md", texte)
        acte = GESTES.ranger_une_note(self.coffre, auteur=self.AUTEUR,
                                      source="0-EN-VRAC/2026-01-05-journal.md",
                                      zone="0-SAVOIRS", date=self.DATE)
        self.assertIsNone(acte.refus, acte.refus)
        self.assertEqual("0-SAVOIRS/2026-01-05-journal.md", acte.chemin)
        apercu = CONVENTION.MAINTENANCE + "/" + CONVENTION.nom_de_l_apercu(
            self.DATE, "2026-01-05-journal.md", "0-EN-VRAC")
        self.assertEqual(
            "_MAINTENANCE/2026-10-09-apercu-0-en-vrac--2026-01-05-journal.md",
            apercu)
        self.assertTrue((self.coffre / apercu).exists(), apercu)

    def test_ranger_ne_part_que_du_vrac(self):
        self.poser_note("0-SAVOIRS/note.md", note())
        avant = self.tete()
        acte = GESTES.ranger_une_note(self.coffre, auteur=self.AUTEUR,
                                      source="0-SAVOIRS/note.md", zone="0-DOCUMENTS",
                                      date=self.DATE)
        self.assertIsNotNone(acte.refus)
        self.assertEqual("le vrac seul est une source", acte.refus.split(" :")[0])
        self.assertEqual(avant, self.tete())
        self.assertTrue((self.coffre / "0-SAVOIRS/note.md").exists())

    def test_ranger_refuse_un_homonyme_du_coffre_entier(self):
        self.poser_note("0-EN-VRAC/Idée Docker.md", note())
        self.poser_note("0-DOCUMENTS/idee-docker.md", note(corps="\n\nL'autre.\n"))
        avant = self.tete()
        acte = GESTES.ranger_une_note(self.coffre, auteur=self.AUTEUR,
                                      source="0-EN-VRAC/Idée Docker.md",
                                      zone="0-SAVOIRS", date=self.DATE)
        self.assertIsNotNone(acte.refus)
        self.assertIn("nom unique dans le coffre", acte.refus)
        self.assertEqual(avant, self.tete())
        self.assertTrue((self.coffre / "0-EN-VRAC/Idée Docker.md").exists())

    def test_le_registre_voyage_dans_le_meme_commit(self):
        self.poser_note("0-EN-VRAC/note-docker.md", note())
        acte = GESTES.ranger_une_note(self.coffre, auteur=self.AUTEUR,
                                      source="0-EN-VRAC/note-docker.md",
                                      zone="0-SAVOIRS", date=self.DATE)
        self.assertIsNone(acte.refus, acte.refus)
        portes = chemins_du_commit(self.coffre, acte.commit)
        self.assertIn("0-SAVOIRS/note-docker.md", portes)
        self.assertIn(self.REGISTRE, portes)
        self.assertIn(acte.copie, portes)

    def test_le_registre_est_complete_en_ajout_seul(self):
        self.poser_note("0-EN-VRAC/note-docker.md", note())
        GESTES.ranger_une_note(self.coffre, auteur=self.AUTEUR,
                               source="0-EN-VRAC/note-docker.md", zone="0-SAVOIRS",
                               date=self.DATE)
        registre = self.lire(self.REGISTRE)
        self.assertTrue(registre.startswith(self.AMORCE_REGISTRE),
                        "le registre ne doit être qu'ajouté, jamais réécrit")
        self.assertIn("0-SAVOIRS/note-docker.md", registre)

    def test_l_apercu_porte_le_nom_recalculable(self):
        self.poser_note("0-EN-VRAC/note-docker.md", note())
        acte = GESTES.ranger_une_note(self.coffre, auteur=self.AUTEUR,
                                      source="0-EN-VRAC/note-docker.md",
                                      zone="0-SAVOIRS", date=self.DATE)
        attendu = ("_MAINTENANCE/"
                   + CONVENTION.nom_de_l_apercu(self.DATE, "note-docker.md",
                                                "0-EN-VRAC"))
        self.assertEqual(attendu, acte.copie)

    def test_l_acte_porte_la_marque_de_l_outil(self):
        self.poser_note("0-EN-VRAC/note-docker.md", note())
        acte = GESTES.ranger_une_note(self.coffre, auteur=self.AUTEUR,
                                      source="0-EN-VRAC/note-docker.md",
                                      zone="0-SAVOIRS", date=self.DATE)
        message = git(self.coffre, "log", "-1", "--format=%B", acte.commit).stdout
        self.assertEqual(self.AUTEUR, ECRIVAIN.auteur_du_commit(message))
        # Chaque geste porte **sa** marque : l'écrivain garde la sienne, ranger la
        # sienne — on lit d'un `log` quel outil a posé l'acte.
        self.assertEqual(GESTES.OUTIL_RANGER, ECRIVAIN.outil_du_commit(message))
        self.assertNotEqual(ECRIVAIN.OUTIL, ECRIVAIN.outil_du_commit(message))

    def test_la_completion_porte_sa_propre_marque(self):
        self.poser_note("0-SAVOIRS/note-docker.md", note(corps="\n\nUn corps."))
        acte = GESTES.completer_une_note(self.coffre, auteur=self.AUTEUR,
                                         source="0-SAVOIRS/note-docker.md",
                                         texte=note(corps="\n\nUn corps.\n\nSuite."),
                                         date=self.DATE)
        message = git(self.coffre, "log", "-1", "--format=%B", acte.commit).stdout
        self.assertEqual(GESTES.OUTIL_COMPLETER, ECRIVAIN.outil_du_commit(message))
        self.assertNotEqual(GESTES.OUTIL_RANGER,
                            ECRIVAIN.outil_du_commit(message))

    def test_un_lieu_refuse_n_ecrit_rien(self):
        self.poser_note("0-EN-VRAC/note.md", note())
        (self.coffre / "0-DOCUMENTS").mkdir(exist_ok=True)
        avant = self.tete()
        acte = GESTES.ranger_une_note(self.coffre, auteur=self.AUTEUR,
                                      source="0-EN-VRAC/note.md",
                                      zone="_MAINTENANCE", date=self.DATE)
        self.assertIsNotNone(acte.refus)
        self.assertEqual(avant, self.tete())
        self.assertEqual(self.AMORCE_REGISTRE, self.lire(self.REGISTRE))

    def test_le_rangement_se_defait_si_le_commit_rate(self):
        self.poser_note("0-EN-VRAC/note.md", note())
        self.poser_un_crochet("refus d'essai")
        avant = self.tete()
        acte = GESTES.ranger_une_note(self.coffre, auteur=self.AUTEUR,
                                      source="0-EN-VRAC/note.md", zone="0-SAVOIRS",
                                      date=self.DATE)
        self.assertIsNotNone(acte.refus)
        self.assertEqual(avant, self.tete())
        self.assertTrue((self.coffre / "0-EN-VRAC/note.md").exists())
        self.assertFalse((self.coffre / "0-SAVOIRS/note.md").exists())
        self.assertEqual(self.AMORCE_REGISTRE, self.lire(self.REGISTRE))

    def test_un_rangement_rate_restitue_la_note_du_vrac_octet_pour_octet(self):
        """F1 — un refus de commit ne doit pas emporter la note déplacée.

        Le socle distingue le fichier **créé** (à supprimer) du fichier **déplacé**
        (à restaurer) : ici la source est là avant le geste, elle doit y être encore
        après le refus, au même contenu près.
        """
        base = note(corps="\n\nUn corps qui ne doit pas se perdre.\n")
        self.poser_note("0-EN-VRAC/note.md", base)
        self.poser_un_crochet("refus d'essai")
        avant = self.tete()
        acte = GESTES.ranger_une_note(self.coffre, auteur=self.AUTEUR,
                                      source="0-EN-VRAC/note.md", zone="0-SAVOIRS",
                                      date=self.DATE)
        self.assertIsNotNone(acte.refus)
        self.assertEqual(avant, self.tete())
        self.assertTrue((self.coffre / "0-EN-VRAC/note.md").exists())
        self.assertEqual(base.encode("utf-8"),
                         (self.coffre / "0-EN-VRAC/note.md").read_bytes())

    def test_un_rangement_rate_restitue_une_note_crlf_octet_pour_octet(self):
        """#01a12148 — l'état d'avant se garde en **octets** : le CRLF revient tel quel.

        Lire l'avant en texte (traduction universelle des fins de ligne) puis le
        réécrire aurait rendu du LF là où la note portait du CRLF : la restauration
        n'aurait pas été « à l'octet ». Le socle lit et repose des octets, donc une
        note en CRLF revient **identique**, même après un commit refusé.
        """
        base = note(corps="\r\n\r\nUn corps en CRLF.\r\n")
        self.poser_note("0-EN-VRAC/note.md", base)
        self.assertIn(b"\r\n", (self.coffre / "0-EN-VRAC/note.md").read_bytes(),
                      "le coffre d'essai doit bien porter du CRLF")
        self.poser_un_crochet("refus d'essai")
        avant = self.tete()
        acte = GESTES.ranger_une_note(self.coffre, auteur=self.AUTEUR,
                                      source="0-EN-VRAC/note.md", zone="0-SAVOIRS",
                                      date=self.DATE)
        self.assertIsNotNone(acte.refus)
        self.assertEqual(avant, self.tete())
        self.assertEqual(base.encode("utf-8"),
                         (self.coffre / "0-EN-VRAC/note.md").read_bytes())

    def test_un_rangement_rate_restitue_une_note_non_versionnee(self):
        """F1 — la note n'était même pas suivie : le refus la laisse telle quelle."""
        base = note(corps="\n\nUne note jamais commitée.\n")
        self.ecrire_fichier("0-EN-VRAC/note.md", base)
        self.poser_un_crochet("refus d'essai")
        acte = GESTES.ranger_une_note(self.coffre, auteur=self.AUTEUR,
                                      source="0-EN-VRAC/note.md", zone="0-SAVOIRS",
                                      date=self.DATE)
        self.assertIsNotNone(acte.refus)
        self.assertEqual(base.encode("utf-8"),
                         (self.coffre / "0-EN-VRAC/note.md").read_bytes())

    def test_un_acte_ne_se_pose_pas_sur_une_autre_branche(self):
        self.poser_note("0-EN-VRAC/note.md", note())
        git(self.coffre, "checkout", "--quiet", "-b", "brouillon")
        acte = GESTES.ranger_une_note(self.coffre, auteur=self.AUTEUR,
                                      source="0-EN-VRAC/note.md", zone="0-SAVOIRS",
                                      date=self.DATE)
        self.assertIsNotNone(acte.refus)
        git(self.coffre, "checkout", "--quiet", "main")


class TestLaCompletion(BaseDesNotes):
    """Compléter remplit une note sur place, sans jamais lui faire dire autre chose."""

    def _completer(self, source, texte, **reste):
        return GESTES.completer_une_note(self.coffre, auteur=self.AUTEUR,
                                         source=source, texte=texte,
                                         date=self.DATE, **reste)

    def test_completer_ajoute_a_la_fin_et_ecrit_sur_place(self):
        base = note(corps="\n\nUn corps propre.")
        self.poser_note("0-SAVOIRS/note-docker.md", base)
        ajout = base + "\n\nUne section ajoutée.\n"
        acte = self._completer("0-SAVOIRS/note-docker.md", ajout)
        self.assertIsNone(acte.refus, acte.refus)
        self.assertEqual("0-SAVOIRS/note-docker.md", acte.chemin)
        self.assertEqual(ajout, self.lire("0-SAVOIRS/note-docker.md"))

    def test_completer_ne_reecrit_pas_le_sens(self):
        base = note(corps="\n\nUn corps propre.")
        self.poser_note("0-SAVOIRS/note-docker.md", base)
        avant = self.tete()
        acte = self._completer("0-SAVOIRS/note-docker.md",
                               note(corps="\n\nUn corps réécrit."))
        self.assertIsNotNone(acte.refus)
        self.assertIn("compléter n'ajoute qu'à la fin", acte.refus)
        self.assertEqual(base, self.lire("0-SAVOIRS/note-docker.md"))
        self.assertEqual(avant, self.tete())

    def test_completer_fait_croitre_les_tags_du_vocabulaire(self):
        base = note(front="kind: note\ntags:\n- docker\n---",
                    corps="\n\nUn corps propre.")
        self.poser_note("0-SAVOIRS/note-docker.md", base)
        ajout = note(front="kind: note\ntags:\n- docker\n- sauvegarde\n---",
                     corps="\n\nUn corps propre.\n\nSuite.")
        acte = self._completer("0-SAVOIRS/note-docker.md", ajout)
        self.assertIsNone(acte.refus, acte.refus)
        self.assertEqual(ajout, self.lire("0-SAVOIRS/note-docker.md"))

    def test_completer_refuse_un_tag_hors_vocabulaire(self):
        base = note(front="kind: note\ntags:\n- docker\n---", corps="\n\nUn corps.")
        self.poser_note("0-SAVOIRS/note-docker.md", base)
        ajout = note(front="kind: note\ntags:\n- docker\n- trucbidule\n---",
                     corps="\n\nUn corps.\n\nSuite.")
        acte = self._completer("0-SAVOIRS/note-docker.md", ajout)
        self.assertIsNotNone(acte.refus)
        self.assertIn("tags du vocabulaire", acte.refus)
        self.assertEqual(base, self.lire("0-SAVOIRS/note-docker.md"))

    def test_completer_retire_une_cle_du_frontmatter_refuse(self):
        base = note(front="kind: note\ntag: docker\n---", corps="\n\nUn corps.")
        self.poser_note("0-SAVOIRS/note-docker.md", base)
        ajout = note(front="kind: note\n---", corps="\n\nUn corps.\n\nSuite.")
        acte = self._completer("0-SAVOIRS/note-docker.md", ajout)
        self.assertIsNotNone(acte.refus)
        self.assertIn("compléter garde le frontmatter", acte.refus)
        self.assertEqual(base, self.lire("0-SAVOIRS/note-docker.md"))

    def test_completer_refuse_dans_une_zone_fermee_a_la_modification(self):
        base = note(corps="\n\nUn corps.")
        self.poser_note("0-DOCUMENTS/document.md", base)
        avant = self.tete()
        acte = self._completer("0-DOCUMENTS/document.md", base + "\n\nSuite.\n")
        self.assertIsNotNone(acte.refus)
        self.assertEqual(base, self.lire("0-DOCUMENTS/document.md"))
        self.assertEqual(avant, self.tete())

    def test_un_refus_de_completion_n_ecrit_rien(self):
        base = note(corps="\n\nUn corps.")
        self.poser_note("0-SAVOIRS/note-docker.md", base)
        avant = self.tete()
        self._completer("0-SAVOIRS/note-docker.md", note(corps="\n\nAutre."))
        self.assertEqual(avant, self.tete())
        self.assertEqual(self.AMORCE_REGISTRE, self.lire(self.REGISTRE))

    # — F1 : un commit refusé ne doit jamais emporter la note qu'on complétait.

    def test_une_completion_ratee_laisse_la_note_versionnee_intacte(self):
        """F1 — la note existait avant : le refus la restaure à son texte d'avant."""
        base = note(corps="\n\nUn corps propre.\n")
        self.poser_note("0-SAVOIRS/note-docker.md", base)
        self.poser_un_crochet("refus d'essai")
        avant = self.tete()
        acte = self._completer("0-SAVOIRS/note-docker.md", base + "\n\nSuite.\n")
        self.assertIsNotNone(acte.refus)
        self.assertEqual(avant, self.tete())
        self.assertEqual(base.encode("utf-8"),
                         (self.coffre / "0-SAVOIRS/note-docker.md").read_bytes())

    def test_une_completion_ratee_laisse_la_note_non_versionnee_intacte(self):
        """F1 — la note n'était même pas suivie : c'est là que `unlink` perdait tout."""
        base = note(corps="\n\nUne note jamais commitée, à ne pas perdre.\n")
        self.ecrire_fichier("0-EN-VRAC/note.md", base)
        self.poser_un_crochet("refus d'essai")
        acte = self._completer("0-EN-VRAC/note.md", base + "\n\nSuite.\n")
        self.assertIsNotNone(acte.refus)
        self.assertEqual(base.encode("utf-8"),
                         (self.coffre / "0-EN-VRAC/note.md").read_bytes())

    # — écriture atomique (socle) : encoder avant d'écrire, pour qu'aucun texte ne
    #   puisse vider une note, et que toute exception rende un refus sans perte.

    def test_une_completion_inencodable_laisse_la_note_intacte_et_dit_le_refus(self):
        """#01a12148 — un demi-surrogate ne doit pas vider la note complétée.

        ``Path.write_text`` tronquait la note **puis** échouait ; et si l'erreur
        n'était pas un ``OSError`` (c'est le cas d'``UnicodeEncodeError``), le socle ne
        la rattrapait pas : la note restait **vidée**. Désormais l'encodage précède
        toute écriture et l'écriture se fait par fichier temporaire ; toute exception
        défait l'acte et rend un refus. La note garde ses octets, et le refus le dit.
        """
        base = note(corps="\n\nUn corps propre.\n")
        self.poser_note("0-SAVOIRS/note-docker.md", base)
        avant = self.tete()
        acte = self._completer("0-SAVOIRS/note-docker.md", base + "\n\nSuite \ud800\n")
        self.assertIsNotNone(acte.refus)
        self.assertIn("l'écriture a échoué", acte.refus or "")
        self.assertEqual(base.encode("utf-8"),
                         (self.coffre / "0-SAVOIRS/note-docker.md").read_bytes())
        self.assertEqual(avant, self.tete())
        self.assertEqual([], sorted(p.name for p in
                                   (self.coffre / "0-SAVOIRS").glob(".*obsia-tmp*")),
                         "aucun fichier temporaire ne doit rester derrière")

    # — F2 : les genres tenus au fil de l'eau restent hors phase 5 **sauf les
    #   carnets** ; une note datée du vrac se complète comme une autre.

    def _refuse_le_genre(self, relatif, libelle):
        self.poser_note(relatif, note(corps="\n\nUn corps.\n"))
        avant = self.tete()
        acte = self._completer(relatif, note(corps="\n\nUn corps.\n\nSuite.\n"))
        self.assertIsNotNone(acte.refus, libelle)
        self.assertIn("au fil de l'eau", acte.refus or "")
        self.assertIn(libelle, acte.refus or "")
        self.assertEqual(avant, self.tete())
        self.assertEqual(note(corps="\n\nUn corps.\n"), self.lire(relatif))

    def test_completer_tient_un_carnet_au_fil_de_l_eau(self):
        """F5 — un carnet se tient au fil de l'eau : une étape s'ajoute en fin (§7.3).

        Le contrat range un dossier ``carnets/`` parmi les notes que l'agent tient
        **sur place**, au même titre que son `` — résumé`` ou sa `` — vision``. La
        complétion y est donc ouverte, sous les mêmes garanties qu'ailleurs : ajout
        en fin seulement, frontmatter intact.
        """
        relatif = "0-PROJETS/mon-projet/carnets/2026-01-05-suivi.md"
        base = note(front="agent: batisseur\nprojet: mon-projet\nstatut: en cours\n"
                          "date: 2026-01-05\n---",
                    corps="\n\n## Fait\n\n- Ouverture du chantier.\n")
        self.poser_note(relatif, base)
        tenu = base + "\n\n## Fait\n\n- 2026-01-05 — une étape de plus.\n"
        acte = self._completer(relatif, tenu)
        self.assertIsNone(acte.refus, acte.refus)
        self.assertEqual(tenu, self.lire(relatif))

    def test_completer_une_note_rangee_dans_un_sous_dossier_de_savoirs(self):
        """Constat 3 du contradicteur sur #154 — la matrice juge sur la **tête** de zone.

        ``ranger`` accepte ``0-SAVOIRS/Réseau/`` : la matrice §7.3 ouvre les savoirs
        quelle que soit la profondeur du sous-dossier. ``compléter`` comparait la zone
        **entière** au dossier de tête, et refusait donc la note que le rangement venait
        d'y poser. La complétion suit désormais la même tête de zone que la matrice.
        """
        texte = note(corps="\n\nUne note à ranger puis à compléter.\n")
        self.poser_note("0-EN-VRAC/note-reseau.md", texte)
        rangee = GESTES.ranger_une_note(self.coffre, auteur=self.AUTEUR,
                                        source="0-EN-VRAC/note-reseau.md",
                                        zone="0-SAVOIRS/Réseau", date=self.DATE)
        self.assertIsNone(rangee.refus, rangee.refus)
        self.assertEqual("0-SAVOIRS/Réseau/note-reseau.md", rangee.chemin)
        tenue = texte + "\n\nUne section ajoutée.\n"
        acte = self._completer("0-SAVOIRS/Réseau/note-reseau.md", tenue)
        self.assertIsNone(acte.refus, acte.refus)
        self.assertEqual(tenue, self.lire("0-SAVOIRS/Réseau/note-reseau.md"))

    def test_la_completion_ne_s_ouvre_pas_hors_des_tetes_ouvertes(self):
        """Constat 3 — juger la **tête** ne doit rien ouvrir de plus.

        Le correctif compare la tête de zone, comme la matrice : il ouvre les
        sous-dossiers du vrac et des savoirs, et **rien d'autre**. Une mémoire gelée
        (``0-MEMOIRES/<agent>/<chantier>/``, §6) et une zone fermée à la modification
        restent refusées, y compris dans un sous-dossier.
        """
        for relatif in ("0-MEMOIRES/assistant/chantier-clos/note.md",
                        "0-DOCUMENTS/sous-dossier/document.md"):
            with self.subTest(relatif=relatif):
                texte = note(corps="\n\nUn corps.\n")
                self.poser_note(relatif, texte)
                avant = self.tete()
                acte = self._completer(relatif, texte + "\n\nUne section ajoutée.\n")
                self.assertIsNotNone(acte.refus, relatif)
                self.assertEqual(texte, self.lire(relatif))
                self.assertEqual(avant, self.tete())

    def test_completer_refuse_une_vision(self):
        self._refuse_le_genre("0-PROJETS/mon-projet/mon-projet — vision.md",
                              "une note « — vision »")

    def test_completer_refuse_un_resume(self):
        self._refuse_le_genre("0-PROJETS/mon-projet/mon-projet — résumé.md",
                              "un résumé de projet")

    def test_completer_refuse_les_preferences(self):
        self._refuse_le_genre("0-MEMOIRES/préférences/regles.md",
                              "les préférences")

    def test_completer_refuse_une_experience(self):
        self._refuse_le_genre("0-MEMOIRES/assistant/expériences/2026-01-05-leçon.md",
                              "les expériences d'un agent")

    def test_une_note_du_vrac_qui_commence_par_une_date_se_complete(self):
        """F2 — la date en tête ne fait pas d'une note du vrac un carnet."""
        base = note(corps="\n\nJournal du jour.\n")
        self.poser_note("0-EN-VRAC/2026-01-05-journal.md", base)
        acte = self._completer("0-EN-VRAC/2026-01-05-journal.md", base + "\n\nSuite.\n")
        self.assertIsNone(acte.refus, acte.refus)
        self.assertEqual(base + "\n\nSuite.\n",
                         self.lire("0-EN-VRAC/2026-01-05-journal.md"))

    # — F3 : seul un tag **hors** vocabulaire peut être retiré (§7.5).

    def test_completer_retire_un_tag_hors_vocabulaire_pour_ranger(self):
        base = note(front="kind: note\ntags:\n- idée\n---", corps="\n\nUn corps.\n")
        self.poser_note("0-EN-VRAC/note.md", base)
        propre = note(front="kind: note\ntags:\n- docker\n---",
                      corps="\n\nUn corps.\n\nSuite.\n")
        acte = self._completer("0-EN-VRAC/note.md", propre)
        self.assertIsNone(acte.refus, acte.refus)
        self.assertEqual(propre, self.lire("0-EN-VRAC/note.md"))
        # Le rangement refuse, lui, une note au tag hors vocabulaire ; la note nettoyée
        # passe — le **même jour**, chemin normal du traitement (remplir, puis classer).
        rangeage = GESTES.ranger_une_note(self.coffre, auteur=self.AUTEUR,
                                          source="0-EN-VRAC/note.md",
                                          zone="0-SAVOIRS", date=self.DATE)
        self.assertIsNone(rangeage.refus, rangeage.refus)
        self.assertEqual("0-SAVOIRS/note.md", rangeage.chemin)

    def test_completer_ne_retire_pas_un_tag_du_vocabulaire(self):
        base = note(front="kind: note\ntags:\n- docker\n- sauvegarde\n---",
                    corps="\n\nUn corps.\n")
        self.poser_note("0-SAVOIRS/note.md", base)
        avant = self.tete()
        depouille = note(front="kind: note\ntags:\n- docker\n---",
                         corps="\n\nUn corps.\n\nSuite.\n")
        acte = self._completer("0-SAVOIRS/note.md", depouille)
        self.assertIsNotNone(acte.refus)
        self.assertIn("du vocabulaire", acte.refus)
        self.assertEqual(base, self.lire("0-SAVOIRS/note.md"))
        self.assertEqual(avant, self.tete())

    def test_ranger_refuse_toujours_un_tag_hors_vocabulaire(self):
        """F3 — c'est compléter qui nettoie ; ranger, lui, ne pose pas une note sale."""
        base = note(front="kind: note\ntags:\n- idée\n---", corps="\n\nUn corps.\n")
        self.poser_note("0-EN-VRAC/note.md", base)
        acte = GESTES.ranger_une_note(self.coffre, auteur=self.AUTEUR,
                                      source="0-EN-VRAC/note.md", zone="0-SAVOIRS",
                                      date=self.DATE)
        self.assertIsNotNone(acte.refus)
        self.assertIn("tags du vocabulaire", acte.refus)
        self.assertTrue((self.coffre / "0-EN-VRAC/note.md").exists())

    def test_le_verrou_empeche_un_second_acte(self):
        base = note(corps="\n\nUn corps.")
        self.poser_note("0-SAVOIRS/note-docker.md", base)
        verrou = self.coffre / ".git" / ECRIVAIN.VERROU
        verrou.write_text("", encoding="utf-8")
        try:
            acte = self._completer("0-SAVOIRS/note-docker.md", base + "\n\nSuite.\n")
        finally:
            verrou.unlink(missing_ok=True)
        self.assertIsNotNone(acte.refus)
        self.assertIn("verrou", acte.refus)
        self.assertEqual(base, self.lire("0-SAVOIRS/note-docker.md"))


class TestL_ApercuDuJour(BaseDesNotes):
    """Un seul aperçu par note, par dossier d'origine et par jour : le premier le crée.

    Le chemin normal du traitement — **remplir, puis classer** — passe par deux
    gestes le même jour sur la même note, tous deux lus au vrac. Deux commits, mais
    **un** fichier d'aperçu, qui grandit d'une section par acte et ne se réécrit
    jamais. Le dossier d'origine fait partie de l'identité de l'aperçu : une note qui
    change de dossier le même jour (rangée, puis complétée au savoirs) en reçoit un
    **second** — le prix de la distinction de deux homonymes de deux dossiers. Et si
    l'acte échoue, l'aperçu revient à son état d'avant, à l'octet près (F1).
    """

    def _apercu(self, nom, dossier="0-EN-VRAC"):
        return "_MAINTENANCE/" + CONVENTION.nom_de_l_apercu(self.DATE, nom, dossier)

    def _completer(self, source, texte):
        return GESTES.completer_une_note(self.coffre, auteur=self.AUTEUR,
                                         source=source, texte=texte,
                                         date=self.DATE)

    def test_un_apercu_vide_ne_bloque_pas_les_actes_du_jour(self):
        """Un aperçu vide posé en début de journée ne bloque pas l'acte qui suit.

        Reproduction de la piste (b) : le fichier d'aperçu du jour **existe** mais ne
        porte rien. L'acte suivant doit pouvoir le remplir — y déposer la copie du
        jour — au lieu de buter sur un aperçu vide.
        """
        base = note(corps="\n\nUn corps.\n")
        self.poser_note("0-EN-VRAC/note.md", base)
        apercu = self._apercu("note.md")
        (self.coffre / apercu).write_text("", encoding="utf-8")
        acte = self._completer("0-EN-VRAC/note.md", base + "\n\nSuite.\n")
        self.assertIsNone(acte.refus, acte.refus)
        self.assertIn("Suite.", self.lire(apercu))

    def test_completer_puis_ranger_le_meme_jour_laisse_un_seul_apercu(self):
        base = note(corps="\n\nUn corps.\n")
        self.poser_note("0-EN-VRAC/note.md", base)
        premier = self._completer("0-EN-VRAC/note.md", base + "\n\nSuite du jour.\n")
        self.assertIsNone(premier.refus, premier.refus)
        apercu = self._apercu("note.md")
        apres_le_premier = self.lire(apercu)

        second = GESTES.ranger_une_note(self.coffre, auteur=self.AUTEUR,
                                        source="0-EN-VRAC/note.md",
                                        zone="0-SAVOIRS", date=self.DATE)
        self.assertIsNone(second.refus, second.refus)

        # deux actes, donc deux commits distincts…
        self.assertNotEqual(premier.commit, second.commit)
        # …mais **un seul** fichier d'aperçu du jour pour cette note : le rangement
        # part du vrac, donc son dossier d'origine est le vrac, ici comme au remplissage.
        copies = sorted(p.name for p in (self.coffre / CONVENTION.MAINTENANCE).glob(
            "*-apercu-0-en-vrac--note.md"))
        self.assertEqual(
            [CONVENTION.nom_de_l_apercu(self.DATE, "note.md", "0-EN-VRAC")], copies)
        finale = self.lire(apercu)
        # le second acte n'a fait qu'**ajouter** : le texte d'avant est intact devant
        self.assertTrue(finale.startswith(apres_le_premier))
        self.assertIn("## Ranger — %s" % self.DATE, finale)
        self.assertIn("- Geste : Ranger", finale)
        self.assertIn("- Chemin : `0-SAVOIRS/note.md`", finale)
        # et l'aperçu du second acte porte le contenu réellement déposé
        self.assertIn(base + "\n\nSuite du jour.\n", finale)
        self.assertEqual("0-SAVOIRS/note.md", second.chemin)

    def test_une_note_qui_change_de_dossier_change_d_apercu(self):
        """F3, rendu exact : l'aperçu est solidaire du **dossier d'origine**.

        Remplir puis classer le même jour garde un seul aperçu — les deux actes sont lus
        au vrac (`test_completer_puis_ranger_le_meme_jour_laisse_un_seul_apercu`). Mais
        compléter ensuite la note **là où elle a été classée** la lit dans un autre
        dossier : elle reçoit un **second** aperçu du jour. L'unicité tient par note **et
        par dossier d'origine**, pas par note seule — c'est le prix de la distinction de
        deux homonymes de deux dossiers.
        """
        base = note(corps="\n\nUn corps.\n")
        self.poser_note("0-EN-VRAC/note.md", base)
        remplir = self._completer("0-EN-VRAC/note.md", base + "\n\nSuite.\n")
        self.assertIsNone(remplir.refus, remplir.refus)
        ranger = GESTES.ranger_une_note(self.coffre, auteur=self.AUTEUR,
                                        source="0-EN-VRAC/note.md",
                                        zone="0-SAVOIRS", date=self.DATE)
        self.assertIsNone(ranger.refus, ranger.refus)
        # les deux premiers actes partagent l'aperçu du vrac, leur dossier d'origine
        self.assertEqual(self._apercu("note.md", "0-EN-VRAC"), ranger.copie)

        ailleurs = self._completer("0-SAVOIRS/note.md",
                                   self.lire("0-SAVOIRS/note.md") + "\n\nPlus.\n")
        self.assertIsNone(ailleurs.refus, ailleurs.refus)
        # la note a changé de dossier : un second aperçu, nommé du savoirs
        self.assertEqual(self._apercu("note.md", "0-SAVOIRS"), ailleurs.copie)
        self.assertNotEqual(ranger.copie, ailleurs.copie)
        copies = sorted(p.name for p in (self.coffre / CONVENTION.MAINTENANCE).glob(
            "*-apercu-*--note.md"))
        self.assertEqual(2, len(copies))

    def test_un_acte_rate_restaure_l_apercu_a_son_etat_d_avant(self):
        """F1 sur l'aperçu : l'addendum d'un acte raté ne reste pas dans le fichier."""
        base = note(corps="\n\nUn corps.\n")
        self.poser_note("0-EN-VRAC/note.md", base)
        premier = self._completer("0-EN-VRAC/note.md", base + "\n\nSuite.\n")
        self.assertIsNone(premier.refus, premier.refus)
        apercu = self._apercu("note.md")
        apres_le_premier = self.lire(apercu)

        self.poser_un_crochet("refus d'essai")
        tete = self.tete()
        second = GESTES.ranger_une_note(self.coffre, auteur=self.AUTEUR,
                                        source="0-EN-VRAC/note.md",
                                        zone="0-SAVOIRS", date=self.DATE)
        self.assertIsNotNone(second.refus)
        self.assertEqual(tete, self.tete())
        self.assertEqual(apres_le_premier.encode("utf-8"),
                         (self.coffre / apercu).read_bytes())
        # rien n'a bougé : la note reste dans le vrac, rien n'est déposé dans les savoirs
        self.assertTrue((self.coffre / "0-EN-VRAC/note.md").exists())
        self.assertFalse((self.coffre / "0-SAVOIRS/note.md").exists())

    def test_deux_notes_homonymes_de_deux_dossiers_ont_deux_apercus(self):
        """Le dossier d'origine entre dans le nom : deux homonymes ne se le disputent pas.

        Deux notes du **même nom**, dans deux dossiers différents, le même jour : chacune
        a **son** aperçu, et l'aperçu porte le dossier d'origine devant le nom de la note.
        Sans cela, la seconde se serait ajoutée à l'aperçu de la première, et les deux
        notes auraient partagé un seul fichier de revue.
        """
        texte = note(corps="\n\nUn corps.\n")
        self.poser_note("0-SAVOIRS/note.md", texte)
        self.poser_note("0-SAVOIRS/Réseau/note.md", texte)
        savoirs = self._completer("0-SAVOIRS/note.md", texte + "\n\nSavoirs.\n")
        reseau = self._completer("0-SAVOIRS/Réseau/note.md", texte + "\n\nRéseau.\n")
        self.assertIsNone(savoirs.refus, savoirs.refus)
        self.assertIsNone(reseau.refus, reseau.refus)
        self.assertEqual("_MAINTENANCE/2026-10-09-apercu-0-savoirs--note.md",
                         savoirs.copie)
        self.assertEqual("_MAINTENANCE/2026-10-09-apercu-0-savoirs-reseau--note.md",
                         reseau.copie)
        self.assertNotEqual(savoirs.copie, reseau.copie)
        self.assertIn("Savoirs.", self.lire(savoirs.copie))
        self.assertNotIn("Réseau.", self.lire(savoirs.copie))

    def test_un_carnet_a_une_seule_forme_d_apercu(self):
        """Le carnet a **une** forme d'aperçu — la même, créé ou complété (§7.4).

        L'aperçu garde le nom **entier** du carnet, date comprise : deux carnets du
        même sujet ouverts à deux dates se disputeraient sinon l'aperçu du jour. Il ne
        redouble pas son dossier. La forme est la même que le carnet soit **créé**
        (`ecrire_un_carnet`) ou **complété** le même jour : deux formes feraient deux
        fichiers pour un seul carnet.
        """
        acte = ECRIVAIN.ecrire_un_carnet(self.coffre, auteur=self.AUTEUR,
                                         projet=self.PROJET, chantier=self.CHANTIER,
                                         sujet=self.SUJET, corps=self.CORPS,
                                         date=self.DATE)
        self.assertIsNone(acte.refus, acte.trace())
        attendu = ("_MAINTENANCE/2026-10-09-apercu-"
                   "2026-10-09-mcp-outils-du-coffre-ouverture.md")
        self.assertEqual(attendu, acte.copie)

        suite = self._completer(acte.chemin, self.lire(acte.chemin)
                                + "\n\n## Suite\n\nEncore.\n")
        self.assertIsNone(suite.refus, suite.refus)
        self.assertEqual(attendu, suite.copie, "la même forme, pas de date redoublée")
        copies = sorted(p.name for p in (self.coffre / CONVENTION.MAINTENANCE).glob(
            "*-apercu-*ouverture.md"))
        self.assertEqual(
            ["2026-10-09-apercu-2026-10-09-mcp-outils-du-coffre-ouverture.md"],
            copies)

    def test_l_apercu_du_jour_est_date_et_porte_le_nom_de_la_note(self):
        """Le nom de l'aperçu n'est pas libre : la porte le recalcule (§7.4).

        L'aperçu porte la date du jour, le **dossier d'origine** de la note et son nom
        tel quel : ici la note est dans le vrac, donc l'aperçu le dit.
        """
        base = note(corps="\n\nUn corps.\n")
        self.poser_note("0-EN-VRAC/ma-note.md", base)
        premier = self._completer("0-EN-VRAC/ma-note.md", base + "\n\nSuite.\n")
        self.assertIsNone(premier.refus, premier.refus)
        self.assertEqual("_MAINTENANCE/" + CONVENTION.nom_de_l_apercu(
            self.DATE, "ma-note.md", "0-EN-VRAC"), premier.copie)
        self.assertEqual("_MAINTENANCE/2026-10-09-apercu-0-en-vrac--ma-note.md",
                         premier.copie)
        self.assertTrue((self.coffre / premier.copie).exists())


class TestLaSourceSeJugeSansLecture(BaseDesNotes):
    """La source est jugée **avant toute lecture**, dans le geste lui-même.

    Une source absolue, ou qui remonte par `..`, sort du coffre. La lire avant de
    la juger dirait, par sa seule forme, si un fichier qui n'est pas une note
    existe : un **oracle d'existence** sur tout le disque. On ne lit donc rien, et
    le motif de refus ne dépend ni du contenu ni de l'existence du fichier visé.
    """

    def refus_sans_lecture(self, geste, source, **reste):
        """Joue le geste en surveillant la lecture : elle n'aura pas lieu."""
        with mock.patch.object(Path, "read_bytes") as octets, \
                mock.patch.object(Path, "read_text") as texte:
            acte = geste(self.coffre, auteur=self.AUTEUR, source=source,
                         date=self.DATE, **reste)
        self.assertFalse(octets.called, "le geste a lu des octets avant de juger")
        self.assertFalse(texte.called, "le geste a lu du texte avant de juger")
        return acte

    def test_ranger_refuse_une_source_absolue_sans_la_lire(self):
        hors = str(self.parent / "hors-du-coffre.md")
        acte = self.refus_sans_lecture(GESTES.ranger_une_note, hors,
                                       zone="0-SAVOIRS")
        self.assertIsNotNone(acte.refus)
        self.assertIn("chemin absolu", acte.refus)
        self.assertIsNone(acte.chemin)

    def test_completer_refuse_une_source_qui_remonte_sans_la_lire(self):
        acte = self.refus_sans_lecture(GESTES.completer_une_note,
                                       "../hors-du-coffre.md",
                                       texte=note(corps="\n\nUne suite."))
        self.assertIsNotNone(acte.refus)
        self.assertIn("sort du coffre", acte.refus)

    def test_le_motif_ne_depend_pas_de_l_existence_du_fichier(self):
        """Le même refus que le fichier visé existe ou non — pas d'oracle."""
        cible = self.parent / "hors-du-coffre.md"
        cible.write_text("un secret hors du coffre", encoding="utf-8")
        avec = self.refus_sans_lecture(GESTES.ranger_une_note, str(cible),
                                       zone="0-SAVOIRS")
        cible.unlink()
        sans = self.refus_sans_lecture(GESTES.ranger_une_note, str(cible),
                                       zone="0-SAVOIRS")
        self.assertIsNotNone(avec.refus)
        self.assertEqual(avec.refus, sans.refus)

    def test_un_refus_de_source_ne_touche_ni_tete_ni_note(self):
        self.poser_note("0-EN-VRAC/note.md", note())
        tete = self.tete()
        acte = GESTES.ranger_une_note(self.coffre, auteur=self.AUTEUR,
                                      source="../evade.md", zone="0-SAVOIRS",
                                      date=self.DATE)
        self.assertIsNotNone(acte.refus)
        self.assertEqual(tete, self.tete())
        self.assertTrue((self.coffre / "0-EN-VRAC/note.md").exists())
        self.assertFalse((self.coffre / "0-SAVOIRS/note.md").exists())


class TestLInventaireExigeUnDepotDeDonnees(BaseDesNotes):
    """`notes_du_coffre` ne dresse l'inventaire que d'un **dépôt de données**.

    Hors d'un dépôt git, il n'y a pas de coffre à lire : l'écrivain refuse plutôt
    que d'énumérer un dossier quelconque. L'inventaire n'étant pas un acte, le
    refus est **levé** — :class:`CoffreInjoignable` —, pas rendu.
    """

    def test_un_dossier_quelconque_ne_s_inventorie_pas(self):
        hors = Path(tempfile.mkdtemp(prefix="obsia-hors-depot-"))
        self.addCleanup(shutil.rmtree, hors, ignore_errors=True)
        with self.assertRaises(GESTES.CoffreInjoignable) as pris:
            GESTES.notes_du_coffre(hors)
        self.assertIn("dépôt de données", str(pris.exception))

    def test_un_depot_s_inventorie(self):
        self.poser_note("0-SAVOIRS/note.md", note())
        vues = GESTES.notes_du_coffre(self.coffre)
        self.assertIsInstance(vues, tuple)
        self.assertIn("0-SAVOIRS/note.md", vues)


class TestLaDateEstValideeParTousLesGestes(BaseDesNotes):
    """Toute date d'acte est de la forme AAAA-MM-JJ — rangement et complétion compris."""

    def test_ranger_refuse_une_date_mal_formee(self):
        self.poser_note("0-EN-VRAC/note.md", note())
        tete = self.tete()
        acte = GESTES.ranger_une_note(self.coffre, auteur=self.AUTEUR,
                                      source="0-EN-VRAC/note.md", zone="0-SAVOIRS",
                                      date="2026/10/09")
        self.assertIsNotNone(acte.refus)
        self.assertIn("mal formée", acte.refus)
        self.assertEqual(tete, self.tete())
        self.assertTrue((self.coffre / "0-EN-VRAC/note.md").exists())
        self.assertFalse((self.coffre / "0-SAVOIRS/note.md").exists())

    def test_completer_refuse_une_date_mal_formee(self):
        base = note()
        self.poser_note("0-SAVOIRS/note.md", base)
        tete = self.tete()
        acte = GESTES.completer_une_note(self.coffre, auteur=self.AUTEUR,
                                         source="0-SAVOIRS/note.md",
                                         texte=base + "\n\nUne suite.",
                                         date="hier")
        self.assertIsNotNone(acte.refus)
        self.assertIn("mal formée", acte.refus)
        self.assertEqual(tete, self.tete())
        self.assertEqual(base, self.lire("0-SAVOIRS/note.md"))

    def test_une_date_bien_formee_passe(self):
        self.poser_note("0-EN-VRAC/note.md", note())
        acte = GESTES.ranger_une_note(self.coffre, auteur=self.AUTEUR,
                                      source="0-EN-VRAC/note.md", zone="0-SAVOIRS",
                                      date=self.DATE)
        self.assertIsNone(acte.refus, acte.refus)

    def test_une_date_avec_un_saut_de_ligne_final_est_refusee(self):
        # `$` laissait passer un `\n` final : la date paraissait bien formée.
        self.poser_note("0-EN-VRAC/note.md", note())
        tete = self.tete()
        acte = GESTES.ranger_une_note(self.coffre, auteur=self.AUTEUR,
                                      source="0-EN-VRAC/note.md", zone="0-SAVOIRS",
                                      date=self.DATE + "\n")
        self.assertIsNotNone(acte.refus)
        self.assertIn("mal formée", acte.refus)
        self.assertEqual(tete, self.tete())


if __name__ == "__main__":
    unittest.main()
