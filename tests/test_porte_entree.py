#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`serveur/porte_entree.py` : juger un texte candidat avant tout disque (P2).

La porte est **pure** : elle reçoit un candidat et un contexte, elle rend un
verdict, elle ne touche à rien. Ces tests le prouvent de deux façons — en
exerçant chaque refus, et en montrant qu'un coffre témoin est identique avant et
après un jugement refusé (pas un octet, pas une date).

Le §7.3, lui, est une règle du **contrat** : les zones portent donc les noms du
contrat (`0-SAVOIRS`, `_MAINTENANCE/`…), et la matrice qui les ouvre vit dans le
moteur partagé — la porte la lit, elle ne la réécrit pas (`docs/PLAN.md`).

Deux déclarations sont **obligatoires** : `auteur` et `coffre`. Sans elles, la
porte refuse au lieu de laisser passer — l'ignorance ferme, elle n'ouvre pas.
`nature` dit ce que l'acte est ; ne pas la déclarer vaut « créer », l'acte le
plus étroit.
"""

import base64
import inspect
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

import serveur.porte_entree as PORTE      # noqa: E402

#: Les natures d'écriture du §7.3, lues dans le moteur partagé.
NATURE_CREER = PORTE.CONVENTION.NATURE_CREER
NATURE_DEPOSER = PORTE.CONVENTION.NATURE_DEPOSER
NATURE_COMPLETER = PORTE.CONVENTION.NATURE_COMPLETER
NATURE_CORRIGER = PORTE.CONVENTION.NATURE_CORRIGER

#: Un faux jeton : assemblé au moment du test, jamais écrit en clair.
JETON = "ghp_" + "".join(("Ab3", "Cd5", "Ef7", "Gh9", "Ij1", "Kl3", "Mn5"))

#: Un vrai bloc de base64 — le corps d'une clé recopiée **sans son en-tête**.
#: Trois lignes de 48 caractères, aucune prose : la forme que `jeton_isole`, qui
#: refuse tout espace, ne peut pas voir. Assemblé au moment du test.
_BLOC = base64.b64encode(
    b"ligne de base64 factice pour le test, aucune valeur reelle ici " * 2)
BLOC_BASE64 = "\n".join(
    _BLOC.decode()[i:i + 48] for i in range(0, len(_BLOC), 48))

#: Le corps de base64 factice ci-dessus, bon pour bâtir les armures de test.
CORPS_BASE64 = "\n".join(BLOC_BASE64.splitlines())

#: Trois empreintes à la suite — un journal de notes, pas une clé. Un hexadécimal
#: de 40 ou 64 caractères est dans l'alphabet du base64 **sans en être**.
TROIS_EMPREINTES = "\n".join([
    "a4867830d96a4ff68ad6d4b6f1f30f713b18d518",
    "b4867830d96a4ff68ad6d4b6f1f30f713b18d519",
    "c4867830d96a4ff68ad6d4b6f1f30f713b18d51a",
])

#: Une clé PGP **publique** en armure — faite pour être recopiée, exemptée.
CLE_PGP_PUBLIQUE = "\n".join([
    "-----BEGIN PGP PUBLIC KEY BLOCK-----",
    "Version: GnuPG v2",
    "",
    CORPS_BASE64,
    "=AbCd",
    "-----END PGP PUBLIC KEY BLOCK-----",
])

#: Un certificat **public**, même forme encadrée : public lui aussi.
CERTIFICAT_PUBLIC = "\n".join([
    "-----BEGIN CERTIFICATE-----",
    CORPS_BASE64,
    "-----END CERTIFICATE-----",
])

#: L'en-tête et le pied d'une clé privée PGP, **composés** : le littéral d'un
#: seul tenant serait lui-même un secret aux yeux de `publier.BLOQUANTS`
#: (« clé privée »), une catégorie que `--forcer` ne franchit pas. Laissé entier
#: dans le source, il rendrait le dépôt impubliable sans que la CI le voie —
#: c'est ce que monte `test_publier`.
DEBUT_ARMURE_PRIVEE = "-----BEGIN PGP PRIVATE KEY " "BLOCK-----"
FIN_ARMURE_PRIVEE = "-----END PGP PRIVATE KEY " "BLOCK-----"

#: Une clé **privée** en armure. Son en-tête ne l'exempte pas : seuls les deux
#: en-têtes **publics** exemptent, le secret recopié reste refusé.
CLE_PGP_PRIVEE = "\n".join([
    DEBUT_ARMURE_PRIVEE,
    "",
    CORPS_BASE64,
    FIN_ARMURE_PRIVEE,
])

#: Le détournement prouvé : une clé **privée** complète placée dans un cadre
#: public. Le délimiteur **à l'intérieur** du cadre fait tomber l'exemption.
CLE_PRIVEE_DANS_UN_CADRE_PUBLIC = "\n".join([
    "-----BEGIN CERTIFICATE-----",
    CLE_PGP_PRIVEE,
    "-----END CERTIFICATE-----",
])

#: Un corps nu entre deux faux délimiteurs publics — **limite assumée** : rien ne
#: le distingue du corps d'une vraie clé publique.
CORPS_NU_ENTRE_FAUX_CADRES = "\n".join([
    "-----BEGIN CERTIFICATE-----",
    CORPS_BASE64,
    "-----END CERTIFICATE-----",
])


#: Un coffre témoin, vide et partagé : le §6 réclame un coffre (échec fermé),
#: même quand ces tests n'ont rien de gelé à y lire.
COFFRE_TEMOIN = tempfile.TemporaryDirectory(prefix="porte-entree-")

#: L'auteur des tests : un agent du contrat, assez nommé pour juger le §7.3.
AUTEUR = "administrateur"

#: Les agents vivants du témoin : `0-MEMOIRES/<agent>/expériences/` leur reste
#: ouvert, quand un dossier inconnu est pris pour un chantier clos.
AGENTS = frozenset(("administrateur", "assistant", "batisseur", "visionnaire"))

#: Sentinelle du coffre par défaut. Distincte de `None`, qui veut dire « aucun
#: coffre déclaré » — un cas que ces tests éprouvent.
COFFRE_PAR_DEFAUT = object()


def contexte(zones=("0-EN-VRAC", "0-SAVOIRS"), presents=None,
             vocabulaire=("docker", "sauvegarde"), auteur=AUTEUR,
             coffre=COFFRE_PAR_DEFAUT, agents=AGENTS,
             nature=NATURE_DEPOSER, notes_du_coffre=()):
    """Un contexte de test : zones du contrat, auteur nommé, coffre témoin.

    La plupart des tests visent un autre contrôle que le §7.3 — la forme du nom,
    le frontmatter, les tags, le secret — et jugent donc un **dépôt**, l'acte que
    les deux zones témoins ouvrent sûrement. Ce qui touche à l'auteur, à la
    nature ou au gel se déclare explicitement, test par test. ``notes_du_coffre``
    est l'inventaire du coffre, chemins relatifs à sa racine : il sert au §6, qui
    veut l'unicité sur **tout** le coffre.
    """
    return PORTE.Contexte(
        zones=tuple(zones),
        noms_presents=presents or {},
        vocabulaire=frozenset(vocabulaire),
        auteur=auteur,
        coffre=Path(COFFRE_TEMOIN.name) if coffre is COFFRE_PAR_DEFAUT else coffre,
        agents=agents,
        nature=nature,
        notes_du_coffre=tuple(notes_du_coffre))


def note(front="kind: note\n---", corps="\n\nUn corps propre."):
    return "---\n%s%s" % (front, corps)


class TestNomDeNote(unittest.TestCase):
    """Le sujet validé devient un nom de fichier — jamais un chemin du modèle."""

    def test_un_sujet_devient_un_nom_de_fichier(self):
        self.assertEqual(PORTE.nom_de_note("Ma note sur Docker"),
                         "ma-note-sur-docker.md")

    def test_les_accents_sont_gardes(self):
        self.assertEqual(PORTE.nom_de_note("Mémoire vive"), "mémoire-vive.md")

    def test_les_espaces_multiples_ne_font_qu_un_tiret(self):
        self.assertEqual(PORTE.nom_de_note("  trop   d'espaces  "),
                         "trop-d-espaces.md")

    def test_un_sujet_vide_ne_donne_pas_de_nom(self):
        self.assertIsNone(PORTE.nom_de_note("   "))
        self.assertIsNone(PORTE.nom_de_note("***"))


class TestNomDejaCalcule(unittest.TestCase):
    """Un nom **déjà calculé** (§6 carnet, §7.4 aperçu) est recalculé, jamais cru.

    Le carnet s'appelle `AAAA-MM-JJ-dossier-sujet.md`, et son dossier garde
    l'orthographe réelle du coffre (`Homelab`) : c'est **la zone** qui la nomme. La
    porte recalcule donc le nom depuis la zone et le sujet brut, et refuse tout nom
    qui diffère — un nom fourni n'est jamais libre, sinon ce serait un chemin que le
    modèle choisit. Une note ordinaire, elle, continue de tenir son nom de son sujet.
    """

    def _carnet(self, zone, sujet, nom, zones=None, nature=NATURE_CREER):
        return PORTE.juger(PORTE.Candidat(zone, sujet, "Corps du carnet.\n", nom),
                           contexte(zones=zones or (zone,), nature=nature))

    def test_un_nom_calculé_est_pris_tel_quel(self):
        v = self._carnet("0-PROJETS/Homelab/carnets", "Bilan",
                         "2026-10-09-Homelab-bilan.md")
        self.assertIsNone(v.refus)
        self.assertEqual("0-PROJETS/Homelab/carnets/2026-10-09-Homelab-bilan.md",
                         v.destination)

    def test_la_casse_du_dossier_vient_de_la_zone(self):
        # Le dossier garde l'orthographe réelle : `Homelab`, jamais `homelab`.
        v = self._carnet("0-PROJETS/Homelab/carnets", "Bilan",
                         "2026-10-09-homelab-bilan.md")
        self.assertIsNotNone(v.refus)
        self.assertEqual(v.refus.controle, "aucun chemin ne vient du modèle")

    def test_un_nom_forgé_différent_du_dérivé_est_refusé(self):
        # Le sujet dit « Bilan », le nom prétend « X — vision » : refusé.
        v = self._carnet("0-PROJETS/obsia/carnets", "Bilan",
                         "2026-10-09-obsia-X — vision.md")
        self.assertIsNotNone(v.refus)
        self.assertEqual(v.refus.controle, "aucun chemin ne vient du modèle")

    def test_un_nom_sans_md_est_refusé(self):
        # `abc/x` : sans `.md`, l'ancienne coupe écrivait un sous-dossier.
        v = self._carnet("0-PROJETS/obsia/carnets", "Bilan", "abc/x")
        self.assertIsNotNone(v.refus)
        self.assertEqual(v.refus.controle, "aucun chemin ne vient du modèle")
        self.assertIn("`.md`", v.refus.constat, v.refus.constat)

    def test_un_nom_qui_porte_un_chemin_est_refusé(self):
        v = self._carnet("0-PROJETS/obsia/carnets", "Bilan", "abc/x.md")
        self.assertIsNotNone(v.refus)
        self.assertEqual(v.refus.controle, "aucun chemin ne vient du modèle")
        self.assertIn("nom de fichier", v.refus.constat, v.refus.constat)

    def test_un_nom_hors_d_un_carnet_est_refusé(self):
        # Hors d'un `carnets/` ou de `_MAINTENANCE/`, le nom n'est pas libre.
        v = PORTE.juger(PORTE.Candidat("0-SAVOIRS", "Bilan", "Corps.\n",
                                       "2026-10-09-x-bilan.md"),
                        contexte())
        self.assertIsNotNone(v.refus)
        self.assertEqual(v.refus.controle, "aucun chemin ne vient du modèle")

    def test_un_nom_long_en_octets_mais_court_replié_est_refusé(self):
        # Le plafond se mesure sur le nom **réel**, pas sur une forme repliée :
        # `ż` (2 octets) se replie en `-` (1 octet), et le nom dépasserait sinon.
        dossier = "\u017c" * 120
        zone = "0-PROJETS/%s/carnets" % dossier
        nom = PORTE.CONVENTION.nom_de_carnet("2026-10-09", dossier, "Bilan")
        v = self._carnet(zone, "Bilan", nom)
        self.assertIsNotNone(v.refus)
        self.assertEqual(v.refus.controle, "sujet exploitable")

    def test_un_aperçu_dérive_de_son_carnet(self):
        carnet = "2026-10-09-mcp-outils-du-coffre-ouverture.md"
        copie = PORTE.CONVENTION.nom_de_l_apercu("2026-10-09", carnet,
                                                 "0-PROJETS/obsia/carnets")
        self.assertEqual("2026-10-09-apercu-2026-10-09-mcp-outils-du-coffre-ouverture.md",
                         copie)
        v = PORTE.juger(
            PORTE.Candidat(PORTE.CONVENTION.MAINTENANCE, carnet, "Aperçu.\n",
                           copie, dossier="0-PROJETS/obsia/carnets"),
            contexte(zones=(PORTE.CONVENTION.MAINTENANCE,),
                     nature=NATURE_CREER))
        self.assertIsNone(v.refus)
        self.assertEqual("_MAINTENANCE/" + copie, v.destination)

    def test_un_aperçu_forgé_est_refusé(self):
        carnet = "2026-10-09-mcp-outils-du-coffre-ouverture.md"
        v = PORTE.juger(
            PORTE.Candidat(PORTE.CONVENTION.MAINTENANCE, carnet, "Aperçu.\n",
                           "2026-10-09-apercu-autre-chose.md"),
            contexte(zones=(PORTE.CONVENTION.MAINTENANCE,),
                     nature=NATURE_CREER))
        self.assertIsNotNone(v.refus)
        self.assertEqual(v.refus.controle, "aucun chemin ne vient du modèle")

    def test_un_nom_qui_n_est_pas_daté_est_refusé(self):
        # Dix caractères de bruit au lieu d'une date : le nom se recalculerait à
        # l'identique, et le coffre ne reconnaîtrait plus un carnet (il exige
        # `AAAA-MM-JJ-`). La forme se vérifie donc **avant** de recalculer.
        v = self._carnet("0-PROJETS/obsia/carnets", "Bilan",
                         "!@#$%^&*()-obsia-bilan.md")
        self.assertIsNotNone(v.refus)
        self.assertEqual(v.refus.controle, "aucun chemin ne vient du modèle")
        self.assertIn("date", v.refus.constat, v.refus.constat)

    def test_un_aperçu_de_carnet_porte_le_jour_de_l_acte(self):
        # L'aperçu du jour garde le nom **entier** du carnet, date comprise — la date
        # du carnet n'est pas retirée, sans quoi deux carnets du même sujet ouverts à
        # deux dates se la disputeraient. Son dossier, lui, n'est pas redoublé. La date
        # de tête de l'aperçu est celle de l'**acte**.
        carnet = "2025-01-01-obsia-bilan.md"
        apercu = PORTE.CONVENTION.nom_de_l_apercu("2026-10-09", carnet,
                                                  "0-PROJETS/obsia/carnets")
        self.assertEqual("2026-10-09-apercu-2025-01-01-obsia-bilan.md", apercu)
        v = PORTE.juger(
            PORTE.Candidat(PORTE.CONVENTION.MAINTENANCE, carnet, "Aperçu.\n", apercu,
                           dossier="0-PROJETS/obsia/carnets"),
            contexte(zones=(PORTE.CONVENTION.MAINTENANCE,), nature=NATURE_CREER))
        self.assertIsNone(v.refus, v.refus)
        self.assertEqual("_MAINTENANCE/" + apercu, v.destination)

    def test_un_aperçu_dont_le_dossier_ne_suit_pas_la_note_est_refusé(self):
        # Le dossier d'origine entre dans le nom : la porte le recalcule, donc un nom
        # qui s'attribue le dossier d'un autre est forgé.
        v = PORTE.juger(
            PORTE.Candidat(PORTE.CONVENTION.MAINTENANCE, "note.md", "Aperçu.\n",
                           "2026-10-09-apercu-0-documents-note.md",
                           dossier="0-SAVOIRS"),
            contexte(zones=(PORTE.CONVENTION.MAINTENANCE,), nature=NATURE_CREER))
        self.assertIsNotNone(v.refus)
        self.assertEqual(v.refus.controle, "aucun chemin ne vient du modèle")

    def test_un_aperçu_de_note_datée_du_vrac_est_accepté(self):
        # F2 — une note ordinaire peut porter une date, hors d'un dossier `carnets/` :
        # son aperçu reprend le nom **tel quel** derrière le dossier d'origine. La porte
        # recalcule le nom depuis le sujet et le dossier, et garde celui qui **est** le
        # nom fourni.
        note_datée = "2026-01-05-journal.md"
        apercu = PORTE.CONVENTION.nom_de_l_apercu("2026-10-09", note_datée)
        v = PORTE.juger(
            PORTE.Candidat(PORTE.CONVENTION.MAINTENANCE, note_datée, "Aperçu.\n",
                           apercu),
            contexte(zones=(PORTE.CONVENTION.MAINTENANCE,), nature=NATURE_CREER))
        self.assertIsNone(v.refus, v.refus)
        self.assertEqual("_MAINTENANCE/" + apercu, v.destination)

    def test_un_aperçu_de_la_maintenance_non_daté_est_refusé(self):
        # F2 — dix caractères de bruit ne tiennent pas lieu de date : la porte exige
        # `AAAA-MM-JJ-` en tête du nom fourni pour la maintenance.
        v = PORTE.juger(
            PORTE.Candidat(PORTE.CONVENTION.MAINTENANCE, "note.md", "Aperçu.\n",
                           "!@#$%^&*()-note.md"),
            contexte(zones=(PORTE.CONVENTION.MAINTENANCE,), nature=NATURE_CREER))
        self.assertIsNotNone(v.refus)
        self.assertEqual(v.refus.controle, "aucun chemin ne vient du modèle")
        self.assertIn("date", v.refus.constat, v.refus.constat)

    def test_l_ajout_a_l_apercu_du_jour_est_permis_la_seconde_copie_non(self):
        # Un seul aperçu par note et par jour : **ajouter** à celui du jour n'est pas
        # créer un homonyme — c'est le chemin normal du traitement (remplir, classer).
        # Mais **créer** une seconde copie du même nom reste un doublon du §6.
        copie = PORTE.CONVENTION.nom_de_l_apercu("2026-10-09", "note.md")
        chemin_copie = PORTE.CONVENTION.MAINTENANCE + "/" + copie
        presents = {PORTE.CONVENTION.MAINTENANCE: (copie,)}
        ajout = PORTE.juger(
            PORTE.Candidat(PORTE.CONVENTION.MAINTENANCE, "note.md",
                           "Copie d'avant.\n\n## Ranger — 2026-10-09\n", nom=copie,
                           source=chemin_copie, avant="Copie d'avant.\n"),
            contexte(zones=(PORTE.CONVENTION.MAINTENANCE,), presents=presents,
                     notes_du_coffre=(chemin_copie,), nature=NATURE_COMPLETER))
        self.assertIsNone(ajout.refus, ajout.refus)
        seconde = PORTE.juger(
            PORTE.Candidat(PORTE.CONVENTION.MAINTENANCE, "note.md",
                           "Copie neuve.\n", nom=copie),
            contexte(zones=(PORTE.CONVENTION.MAINTENANCE,), presents=presents,
                     notes_du_coffre=(chemin_copie,), nature=NATURE_CREER))
        self.assertIsNotNone(seconde.refus)
        self.assertIn("unique", seconde.refus.controle)

    def test_sans_nom_calculé_le_sujet_donne_le_nom(self):
        v = PORTE.juger(PORTE.Candidat("0-SAVOIRS", "Ma note sur Docker",
                                       "Corps.\n"),
                        contexte())
        self.assertIsNone(v.refus)
        self.assertEqual("0-SAVOIRS/ma-note-sur-docker.md", v.destination)


class TestAucunCheminDuModele(unittest.TestCase):
    """Le geste interdit : glisser un chemin dans le sujet."""

    def _refus(self, sujet):
        return PORTE.juger(PORTE.Candidat("0-SAVOIRS", sujet, note()),
                           contexte()).refus

    def test_un_fragment_de_chemin_est_refuse(self):
        r = self._refus("0-SAVOIRS/docker")
        self.assertIsNotNone(r)
        self.assertEqual(r.controle, "aucun chemin ne vient du modèle")
        self.assertIn("§6", r.regle)

    def test_un_sujet_qui_est_deja_un_nom_de_fichier_est_refuse(self):
        self.assertEqual(self._refus("docker.md").controle,
                         "aucun chemin ne vient du modèle")

    def test_une_remontee_de_dossier_est_refusee(self):
        self.assertEqual(self._refus("../hors-zone").controle,
                         "aucun chemin ne vient du modèle")

    def test_un_chemin_absolu_est_refuse(self):
        self.assertEqual(self._refus("/etc/passwd").controle,
                         "aucun chemin ne vient du modèle")

    def test_un_point_initial_est_refuse(self):
        self.assertEqual(self._refus(".caché").controle,
                         "aucun chemin ne vient du modèle")

    def test_un_titre_avec_des_points_reste_un_titre(self):
        v = PORTE.juger(PORTE.Candidat("0-SAVOIRS", "Points de suspension…",
                                       note()), contexte())
        self.assertTrue(v.accepte)

    def test_tout_refus_dit_le_geste(self):
        r = self._refus("a/b")
        self.assertTrue(r.geste)
        self.assertTrue(r.constat)
        self.assertTrue(r.regle)


class TestZoneAutorisee(unittest.TestCase):
    def test_une_zone_hors_de_la_liste_est_refusee(self):
        v = PORTE.juger(PORTE.Candidat("zone-interdite", "docker", note()),
                        contexte())
        self.assertFalse(v.accepte)
        self.assertEqual(v.refus.controle, "zone autorisée")
        self.assertIn("§7.3", v.refus.regle)

    def test_une_zone_autorisee_passe(self):
        v = PORTE.juger(PORTE.Candidat("0-SAVOIRS", "docker", note()),
                        contexte())
        self.assertTrue(v.accepte)
        self.assertEqual(v.destination, "0-SAVOIRS/docker.md")

    def test_la_zone_du_modele_n_est_pas_un_chemin(self):
        # Une zone autorisée ne descend jamais : le modèle choisit un nom de
        # zone, pas une arborescence.
        v = PORTE.juger(PORTE.Candidat("0-SAVOIRS/sous", "docker", note()),
                        contexte())
        self.assertFalse(v.accepte)
        self.assertEqual(v.refus.controle, "zone autorisée")


class TestMatriceDuContratALaPorte(unittest.TestCase):
    """Le §7.3 jugé par la porte : la zone, l'auteur, la nature d'écriture.

    La règle vit dans le moteur partagé, la porte la lit — et elle ne laisse pas
    passer un « tout est ouvert » : sans auteur, elle refuse.
    """

    def juger(self, zone, sujet, auteur, nature=NATURE_DEPOSER, presents=None):
        return PORTE.juger(PORTE.Candidat(zone, sujet, note()),
                           contexte(zones=(zone,), auteur=auteur, nature=nature,
                                    presents=presents))

    def test_une_zone_hors_matrice_est_refusee_meme_fournie(self):
        # La porte ne se fie pas à la liste de l'appelant : `0-ARCHIVES` y
        # fût-elle, le contrat ne la nomme pas.
        v = self.juger("0-ARCHIVES", "docker", "assistant")
        self.assertFalse(v.accepte)
        self.assertEqual(v.refus.controle, "zone du contrat")

    def test_la_maintenance_du_coffre_est_ouverte(self):
        # Previews, actions, registre `notes_remplies.md` : le §7.3 ouvre
        # `_MAINTENANCE/`, et le §7.4 l'impose — à tout auteur.
        v = self.juger("_MAINTENANCE", "apercu-2026-10-09", "assistant",
                       nature=NATURE_CREER)
        self.assertTrue(v.accepte, v.refus)

    def test_un_dossier_inconnu_est_refuse(self):
        v = self.juger("mon-dossier", "docker", "assistant")
        self.assertFalse(v.accepte)
        self.assertEqual(v.refus.controle, "zone du contrat")

    def test_une_vision_est_refusee_a_un_autre_agent(self):
        v = self.juger("0-PROJETS/mon-projet", "mon-projet — vision", "batisseur",
                       nature=NATURE_CREER)
        self.assertFalse(v.accepte)
        self.assertEqual(v.refus.controle, "zone du contrat")
        self.assertIn("visionnaire", v.refus.constat)

    def test_une_vision_est_acceptee_au_visionnaire(self):
        v = self.juger("0-PROJETS/mon-projet", "mon-projet — vision",
                       "visionnaire", nature=NATURE_CREER)
        self.assertTrue(v.accepte, v.refus)

    def test_une_vision_tient_sur_le_nom_reel_du_dossier(self):
        # Deux règles rencontrent cette note : le §7.3 (visionnaire seul) et
        # l'unicité. Le dossier s'écrit `Homelab`, la note `Homelab — vision.md` ;
        # le sujet `Homelab — vision` dérive `homelab-vision.md` — la même note.
        refuse = self.juger("0-PROJETS/Homelab", "Homelab — vision", "batisseur",
                            nature=NATURE_CREER)
        accepte = self.juger("0-PROJETS/Homelab", "Homelab — vision",
                             "visionnaire", nature=NATURE_CREER)
        self.assertFalse(refuse.accepte)
        self.assertIn("visionnaire", refuse.refus.constat)
        self.assertTrue(accepte.accepte, accepte.refus)
        # Moitié règle tenue. Moitié unicité : la vision déjà posée, écrite
        # `Homelab — vision.md`, bloque le même sujet — même au visionnaire.
        doublon = self.juger("0-PROJETS/Homelab", "Homelab — vision", "visionnaire",
                             nature=NATURE_CREER,
                             presents={"0-PROJETS/Homelab": ("Homelab — vision.md",)})
        self.assertFalse(doublon.accepte, doublon.refus)
        self.assertEqual(doublon.refus.controle, "nom unique")

    def test_une_vision_tient_sur_un_nom_a_accent(self):
        # `Café` et `cafe` désignent le même projet : l'accent n'ouvre pas la
        # vision à un autre auteur.
        v = self.juger("0-PROJETS/Café", "Café — vision", "batisseur",
                       nature=NATURE_CREER)
        self.assertFalse(v.accepte)
        self.assertIn("visionnaire", v.refus.constat)

    def test_les_experiences_d_un_agent_sont_refusees_a_un_autre(self):
        v = self.juger("0-MEMOIRES/batisseur/expériences", "lecon-docker",
                       "assistant", nature=NATURE_CREER)
        self.assertFalse(v.accepte)
        self.assertEqual(v.refus.controle, "zone du contrat")

    def test_les_experiences_sont_acceptees_a_l_agent_nomme(self):
        v = self.juger("0-MEMOIRES/batisseur/expériences", "lecon-docker",
                       "batisseur", nature=NATURE_CREER)
        self.assertTrue(v.accepte, v.refus)

    def test_creer_une_note_neuve_dans_les_savoirs_est_refuse(self):
        # `0-SAVOIRS/` ne s'ouvre qu'au complément et au dépôt : on n'y crée pas
        # une note neuve (§7.3).
        v = self.juger("0-SAVOIRS", "docker", "assistant",
                       nature=NATURE_CREER)
        self.assertFalse(v.accepte)
        self.assertEqual(v.refus.controle, "zone du contrat")
        self.assertIn("créer", v.refus.constat)

    def test_deposer_une_note_classee_dans_les_savoirs_est_accepte(self):
        # Le classement d'une note venue d'`0-EN-VRAC/` peut aboutir aux savoirs.
        v = self.juger("0-SAVOIRS", "docker", "assistant",
                       nature=NATURE_DEPOSER)
        self.assertTrue(v.accepte, v.refus)

    def test_sans_nature_declaree_l_acte_le_plus_etroit_s_applique(self):
        # Ne rien dire de l'acte ne dispense pas de le juger : c'est « créer ».
        v = PORTE.juger(PORTE.Candidat("0-SAVOIRS", "docker", note()),
                        contexte(zones=("0-SAVOIRS",), auteur=AUTEUR, nature=""))
        self.assertFalse(v.accepte)
        self.assertEqual(v.refus.controle, "zone du contrat")

    def test_sans_auteur_declare_la_porte_refuse(self):
        # La matrice est une fonction de l'auteur : sans auteur, il n'y a rien à
        # juger — et l'ignorance n'ouvre pas, elle ferme.
        v = PORTE.juger(PORTE.Candidat("0-SAVOIRS", "docker", note()),
                        contexte(auteur=""))
        self.assertFalse(v.accepte)
        self.assertEqual(v.refus.controle, "zone du contrat")
        self.assertIn("auteur", v.refus.constat)

    def test_un_auteur_blanc_ne_vaut_pas_mieux_qu_un_auteur_absent(self):
        v = PORTE.juger(PORTE.Candidat("0-SAVOIRS", "docker", note()),
                        contexte(auteur="   "))
        self.assertFalse(v.accepte)
        self.assertEqual(v.refus.controle, "zone du contrat")


class TestMemoireGelee(unittest.TestCase):
    """§6 : un chantier clos ne s'écrit plus, quand la mémoire vivante s'écrit."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.coffre = Path(self.tmp.name)
        self.agents = frozenset(("batisseur",))

    def tearDown(self):
        self.tmp.cleanup()

    def juger(self, zone, sujet, auteur, nature=NATURE_COMPLETER):
        return PORTE.juger(
            PORTE.Candidat(zone, sujet, note()),
            contexte(zones=(zone,), auteur=auteur, coffre=self.coffre,
                     agents=self.agents, nature=nature))

    def test_un_chantier_clos_est_refuse(self):
        v = self.juger("0-MEMOIRES/2026-01-chantier", "note", "assistant")
        self.assertFalse(v.accepte)
        self.assertEqual(v.refus.controle, "mémoire gelée")

    def test_les_preferences_restent_vivantes(self):
        v = self.juger("0-MEMOIRES/préférences", "style", "assistant")
        self.assertTrue(v.accepte, v.refus)

    def test_les_experiences_de_l_agent_restent_vivantes(self):
        v = self.juger("0-MEMOIRES/batisseur/expériences", "lecon", "batisseur")
        self.assertTrue(v.accepte, v.refus)

    def test_sans_coffre_la_porte_refuse_de_juger_le_gel(self):
        # Sans coffre, le §6 ne se lit pas : la porte refuse plutôt que de
        # laisser écrire dans un chantier clos faute d'avoir regardé.
        v = PORTE.juger(PORTE.Candidat("0-SAVOIRS", "docker", note()),
                        contexte(zones=("0-SAVOIRS",), auteur=AUTEUR, coffre=None))
        self.assertFalse(v.accepte)
        self.assertEqual(v.refus.controle, "mémoire gelée")
        self.assertIn("coffre", v.refus.constat)


class TestDepotImbrique(unittest.TestCase):
    def test_une_part_de_depot_imbrique_est_refusee(self):
        # `code/` est hors mémoire : la règle vit dans le moteur partagé, la carte
        # légale l'applique, la porte l'emprunte à la carte — une seule règle.
        v = PORTE.juger(PORTE.Candidat("0-PROJETS/p/code", "docker", note()),
                        contexte(zones=("0-PROJETS/p/code",)))
        self.assertFalse(v.accepte)
        self.assertEqual(v.refus.controle, "dépôt imbriqué")

    def test_le_refus_nomme_la_part_qui_sort_de_la_memoire(self):
        v = PORTE.juger(PORTE.Candidat("0-PROJETS/p/code", "docker", note()),
                        contexte(zones=("0-PROJETS/p/code",)))
        self.assertIn("code", v.refus.constat)

    def test_une_zone_propre_passe(self):
        v = PORTE.juger(PORTE.Candidat("0-PROJETS/p/documents", "docker", note()),
                        contexte(zones=("0-PROJETS/p/documents",)))
        self.assertTrue(v.accepte)


class TestNomUniqueEtReserve(unittest.TestCase):
    def test_un_nom_deja_pris_est_refuse(self):
        v = PORTE.juger(
            PORTE.Candidat("0-SAVOIRS", "docker", note()),
            contexte(presents={"0-SAVOIRS": ("docker.md",)}))
        self.assertFalse(v.accepte)
        self.assertEqual(v.refus.controle, "nom unique")
        self.assertIn("§6", v.refus.regle)

    def test_un_homonyme_se_compare_sous_forme_normalisee(self):
        # Le sujet donne un kebab (`homelab-vision.md`), la note présente s'appelle
        # `Homelab — vision.md` : c'est **la même note**. Comparer octet à octet
        # laisserait passer un doublon en silence — la comparaison se fait donc sur
        # la même clé des deux côtés (`nom_comparable`, le moteur partagé).
        presents = {"0-PROJETS/Homelab": ("Homelab — vision.md",)}
        v = PORTE.juger(
            PORTE.Candidat("0-PROJETS/Homelab", "Homelab — vision", note()),
            contexte(zones=("0-PROJETS/Homelab",), auteur="visionnaire",
                     nature=NATURE_CREER, presents=presents))
        self.assertFalse(v.accepte, v.refus)
        self.assertEqual(v.refus.controle, "nom unique")
        # Et il cite la note qui existe — pas le kebab qu'on allait écrire.
        self.assertIn("Homelab — vision.md", v.refus.constat)
        self.assertIn("0-PROJETS/Homelab/Homelab — vision.md", v.refus.geste)

    def test_le_refus_unique_dit_ou_vit_la_note_homonyme(self):
        # Le geste doit envoyer le modèle au bon endroit, pas seulement lui dire
        # « non » : le chemin qu'il cite est celui d'une note qui **existe** dans
        # le dossier de destination — pas un chemin inventé.
        presents = {"0-SAVOIRS": ("archives.md", "docker.md")}
        v = PORTE.juger(
            PORTE.Candidat("0-SAVOIRS", "docker", note()),
            contexte(presents=presents))
        self.assertEqual(v.refus.controle, "nom unique")
        cite = v.refus.geste.split("`")[1]        # le chemin entre accents graves
        zone, _, relatif = cite.partition("/")
        self.assertIn(relatif, presents[zone])    # il existe bien dans la zone
        self.assertEqual(cite, "0-SAVOIRS/docker.md")

    def test_le_meme_nom_dans_une_autre_zone_passe(self):
        v = PORTE.juger(
            PORTE.Candidat("0-SAVOIRS", "docker", note()),
            contexte(presents={"0-EN-VRAC": ("docker.md",)}))
        self.assertTrue(v.accepte)

    def test_un_homonyme_en_sous_dossier_ne_bloque_pas_la_racine(self):
        # `noms_presents` porte des chemins **relatifs à la zone** : un `docker.md`
        # rangé dans `sous/` n'occupe pas le dossier de destination. Le refus ne
        # porte que sur le même dossier — et son geste ne cite donc jamais un
        # chemin qui n'existe pas.
        v = PORTE.juger(
            PORTE.Candidat("0-SAVOIRS", "docker", note()),
            contexte(presents={"0-SAVOIRS": ("sous/docker.md",)}))
        self.assertTrue(v.accepte)

    def test_un_sous_dossier_ne_se_confond_pas_avec_un_titre_de_la_racine(self):
        # `nom_comparable` aplatit *aussi* la barre oblique : `sous/docker.md` et
        # un titre « sous docker » à la racine rendent la **même** clé. Ce ne sont
        # pourtant pas les mêmes dossiers — le préfixe de dossier se compare à
        # l'identique, et seul le nom de fichier passe par la forme comparable.
        v = PORTE.juger(
            PORTE.Candidat("0-SAVOIRS", "sous docker", note()),
            contexte(presents={"0-SAVOIRS": ("sous/docker.md",)}))
        self.assertTrue(v.accepte, v.refus)

    def test_un_nom_reserve_est_refuse(self):
        v = PORTE.juger(PORTE.Candidat("0-SAVOIRS", "sommaire", note()),
                        contexte())
        self.assertFalse(v.accepte)
        self.assertEqual(v.refus.controle, "nom réservé")


class TestFrontmatter(unittest.TestCase):
    def test_un_frontmatter_sain_passe(self):
        v = PORTE.juger(PORTE.Candidat("0-SAVOIRS", "docker", note()), contexte())
        self.assertTrue(v.accepte)

    def test_un_second_bloc_de_frontmatter_est_refuse(self):
        texte = note(corps="\n---\nkind: note\n---\n\ncorps\n")
        v = PORTE.juger(PORTE.Candidat("0-SAVOIRS", "docker", texte), contexte())
        self.assertFalse(v.accepte)
        self.assertEqual(v.refus.controle, "frontmatter conforme")
        self.assertIn("§5", v.refus.regle)

    def test_une_cle_repetee_est_refusee(self):
        texte = note(front="kind: note\nkind: projet\n---")
        v = PORTE.juger(PORTE.Candidat("0-SAVOIRS", "docker", texte), contexte())
        self.assertFalse(v.accepte)
        self.assertEqual(v.refus.controle, "frontmatter conforme")
        self.assertIn("kind", v.refus.constat)

    def test_un_frontmatter_non_ferme_est_refuse(self):
        texte = "---\nkind: note\nUn corps qui n'est jamais refermé."
        v = PORTE.juger(PORTE.Candidat("0-SAVOIRS", "docker", texte), contexte())
        self.assertFalse(v.accepte)
        self.assertEqual(v.refus.controle, "frontmatter conforme")

    def test_une_liste_yaml_sur_une_ligne_est_refusee(self):
        # Le contrat veut une entrée par ligne (§5). Sans ce contrôle, la valeur
        # serait lue comme un tag unique `[docker, reseau]` : le refus parlerait
        # du vocabulaire, hors sujet, et n'enverrait pas réécrire la liste.
        texte = note(front="kind: note\ntags: [docker, reseau]\n---")
        v = PORTE.juger(PORTE.Candidat("0-SAVOIRS", "docker", texte), contexte())
        self.assertFalse(v.accepte)
        self.assertEqual(v.refus.controle, "listes YAML sur une ligne")
        self.assertIn("§5", v.refus.regle)
        self.assertIn("une entrée par ligne", v.refus.geste)
        self.assertIn("tags", v.refus.constat)

    def test_la_meme_liste_en_colonne_passe(self):
        texte = note(front="kind: note\ntags:\n  - docker\n---")
        v = PORTE.juger(PORTE.Candidat("0-SAVOIRS", "docker", texte), contexte())
        self.assertTrue(v.accepte)

    def test_un_sujet_trop_long_est_refuse(self):
        sujet = "mot " * PORTE.NOM_MAX_OCTETS
        v = PORTE.juger(PORTE.Candidat("0-SAVOIRS", sujet, note()), contexte())
        self.assertFalse(v.accepte)
        self.assertEqual(v.refus.controle, "sujet exploitable")

    def test_une_note_sans_frontmatter_passe(self):
        # Le frontmatter se pose plus tard (P4/P5) : son absence n'est pas un refus.
        v = PORTE.juger(PORTE.Candidat("0-SAVOIRS", "docker", "Un simple corps."),
                        contexte())
        self.assertTrue(v.accepte)


class TestTagsDuVocabulaire(unittest.TestCase):
    def test_un_tag_du_frontmatter_hors_vocabulaire_est_refuse(self):
        texte = note(front="kind: note\ntags:\n  - hors-registre\n---")
        v = PORTE.juger(PORTE.Candidat("0-SAVOIRS", "docker", texte), contexte())
        self.assertFalse(v.accepte)
        self.assertEqual(v.refus.controle, "tags du vocabulaire")
        self.assertIn("hors-registre", v.refus.constat)
        self.assertIn("§7.5", v.refus.regle)

    def test_un_tag_inline_hors_vocabulaire_est_refuse(self):
        texte = note(corps="\n\nUn corps #hors-registre.")
        v = PORTE.juger(PORTE.Candidat("0-SAVOIRS", "docker", texte), contexte())
        self.assertFalse(v.accepte)
        self.assertEqual(v.refus.controle, "tags du vocabulaire")

    def test_des_tags_du_vocabulaire_passent(self):
        texte = note(front="kind: note\ntags:\n  - docker\n---",
                     corps="\n\nUn corps #sauvegarde.")
        v = PORTE.juger(PORTE.Candidat("0-SAVOIRS", "docker", texte), contexte())
        self.assertTrue(v.accepte)


class TestAbsenceDeSecret(unittest.TestCase):
    def test_un_secret_nomme_est_refuse(self):
        texte = note(corps="\n\njeton = " + JETON)
        v = PORTE.juger(PORTE.Candidat("0-SAVOIRS", "docker", texte), contexte())
        self.assertFalse(v.accepte)
        self.assertEqual(v.refus.controle, "absence de secret")
        self.assertIn("§7.1", v.refus.regle)

    def test_le_secret_n_est_pas_recopie_dans_le_refus(self):
        texte = note(corps="\n\njeton = " + JETON)
        v = PORTE.juger(PORTE.Candidat("0-SAVOIRS", "docker", texte), contexte())
        self.assertNotIn(JETON, v.refus.constat)

    def test_une_note_propre_passe(self):
        texte = note(corps="\n\nAucun secret ici, seulement de la prose.")
        v = PORTE.juger(PORTE.Candidat("0-SAVOIRS", "docker", texte), contexte())
        self.assertTrue(v.accepte)

    def test_un_jeton_isole_dans_le_corps_est_refuse(self):
        """Le corps **seul** est un jeton : le frontmatter le masquait.

        `jeton_isole` était jugé sur la note entière, frontmatter compris ; la
        note contenant des espaces, il ne se déclenchait jamais dans le passage
        de l'écrivain. Il se juge maintenant sur le corps, hors frontmatter.
        """
        texte = note(corps="\n\n" + JETON)
        v = PORTE.juger(PORTE.Candidat("0-SAVOIRS", "docker", texte), contexte())
        self.assertFalse(v.accepte)
        self.assertEqual(v.refus.controle, "absence de secret")
        self.assertNotIn(JETON, v.refus.constat)

    def test_un_bloc_de_base64_est_refuse(self):
        """La clé recopiée sans son en-tête — le cas qu'a montré le Contradicteur."""
        texte = note(corps="\n\n" + BLOC_BASE64)
        v = PORTE.juger(PORTE.Candidat("0-SAVOIRS", "docker", texte), contexte())
        self.assertFalse(v.accepte)
        self.assertEqual(v.refus.controle, "absence de secret")
        self.assertNotIn(BLOC_BASE64.splitlines()[0], v.refus.constat)

    def test_trois_empreintes_consecutives_passent(self):
        """Un journal d'empreintes n'est pas un secret : le hex n'est pas du base64 de clé."""
        texte = note(corps="\n\n" + TROIS_EMPREINTES)
        v = PORTE.juger(PORTE.Candidat("0-SAVOIRS", "docker", texte), contexte())
        self.assertTrue(v.accepte)

    def test_une_cle_pgp_publique_passe(self):
        """Une clé **publique** est faite pour être recopiée : la porte ne la refuse pas.

        La prose avant l'armure est là pour une autre règle du §5 : un corps qui
        **commence** par `---` passerait pour un second frontmatter, et le refus
        masquerait celui du bloc.
        """
        texte = note(corps="\n\nLa clé publique du dépôt, à recopier :\n\n"
                           + CLE_PGP_PUBLIQUE)
        v = PORTE.juger(PORTE.Candidat("0-SAVOIRS", "docker", texte), contexte())
        self.assertTrue(v.accepte)

    def test_un_certificat_public_passe(self):
        texte = note(corps="\n\nLe certificat public du service :\n\n"
                           + CERTIFICAT_PUBLIC)
        v = PORTE.juger(PORTE.Candidat("0-SAVOIRS", "docker", texte), contexte())
        self.assertTrue(v.accepte)

    def test_une_cle_privee_en_armure_est_refusee(self):
        """Seuls les en-têtes publics exemptent : une clé privée en armure reste refusée."""
        texte = note(corps="\n\nLa clé privée du dépôt :\n\n" + CLE_PGP_PRIVEE)
        v = PORTE.juger(PORTE.Candidat("0-SAVOIRS", "docker", texte), contexte())
        self.assertFalse(v.accepte)
        self.assertEqual(v.refus.controle, "absence de secret")

    def test_un_cadre_public_non_ferme_ne_protege_pas(self):
        """Un `BEGIN` orphelin n'ouvre pas un trou : la paire complète est requise."""
        texte = note(corps="\n\nLa clé, à recopier :\n\n"
                           "-----BEGIN CERTIFICATE-----\n" + BLOC_BASE64)
        v = PORTE.juger(PORTE.Candidat("0-SAVOIRS", "docker", texte), contexte())
        self.assertFalse(v.accepte)
        self.assertEqual(v.refus.controle, "absence de secret")

    def test_un_en_tete_de_cle_privee_est_refuse(self):
        """L'en-tête privé seul est un secret — trou indépendant de l'exemption.

        Il n'y a **pas** de corps de base64 ici : c'est le motif de ligne qui
        refuse, et il manquait à la liste.
        """
        texte = note(corps="\n\nLa clé privée du dépôt :\n\n"
                           + DEBUT_ARMURE_PRIVEE)
        v = PORTE.juger(PORTE.Candidat("0-SAVOIRS", "docker", texte), contexte())
        self.assertFalse(v.accepte)
        self.assertEqual(v.refus.controle, "absence de secret")
        self.assertNotIn(DEBUT_ARMURE_PRIVEE, v.refus.constat)

    def test_une_cle_privee_dans_un_cadre_public_est_refusee(self):
        """Le détournement prouvé : le délimiteur intérieur fait tomber l'exemption."""
        texte = note(corps="\n\nLe certificat public du service :\n\n"
                           + CLE_PRIVEE_DANS_UN_CADRE_PUBLIC)
        v = PORTE.juger(PORTE.Candidat("0-SAVOIRS", "docker", texte), contexte())
        self.assertFalse(v.accepte)
        self.assertEqual(v.refus.controle, "absence de secret")

    def test_un_corps_nu_entre_deux_faux_cadres_publics_passe(self):
        """**Limite assumée** : un corps nu entre deux faux délimiteurs publics.

        Rien ne distingue ce corps de celui d'une **vraie** clé publique — les
        deux sont du base64 entre deux lignes d'armure valides. Consigné ici pour
        que personne ne croie l'exemption plus forte qu'elle n'est ; le refus du
        secret recopié tient à l'**en-tête privé**, pas à cette forme.
        """
        texte = note(corps="\n\nLe certificat public du service :\n\n"
                           + CORPS_NU_ENTRE_FAUX_CADRES)
        v = PORTE.juger(PORTE.Candidat("0-SAVOIRS", "docker", texte), contexte())
        self.assertTrue(v.accepte)

    def test_un_mot_de_passe_en_phrase_est_une_limite_connue(self):
        """Limite assumée : le filet ne voit pas un secret noyé dans la prose.

        Ni `secret_dans_une_ligne` (aucune affectation, aucun motif nommé) ni
        `jeton_isole`, que les espaces arrêtent, ne l'attrapent. Ce n'est pas un
        oubli : la barrière n'est pas ici, elle est de **borner `read`** — ce que
        le modèle ne peut pas lire, il ne peut pas le recopier. Le filet est un
        filet, pas un mur.
        """
        texte = note(corps="\n\nLe mot de passe du routeur est Tr0ub4dor&3x9.")
        v = PORTE.juger(PORTE.Candidat("0-SAVOIRS", "docker", texte), contexte())
        self.assertTrue(v.accepte)

    def test_un_secret_nu_est_une_limite_connue(self):
        """Limite assumée : un secret trop court, seul sur sa ligne, passe.

        `jeton_isole` exige vingt caractères au moins et deux familles de
        caractères : un mot de passe court ne les a pas. Comme ci-dessus, c'est
        `read` qu'il faut borner, pas le filet qu'il faut épaissir sans fin.
        """
        texte = note(corps="\n\nTr0ub4dor&3")
        v = PORTE.juger(PORTE.Candidat("0-SAVOIRS", "docker", texte), contexte())
        self.assertTrue(v.accepte)


class TestLeSecretAvantLaForme(unittest.TestCase):
    """Quand les deux portes se ferment, laquelle parle : le secret, pas la forme.

    Un corps qui **commence** par `---` et qui contient une clé privée ferme
    deux portes à la fois. L'ordre des contrôles décidait laquelle répondait, et
    c'était la forme : « un second bloc de frontmatter s'ouvre dans le corps »,
    un constat de mise en forme, quand la note recopiait une clé privée. Le
    refus est juste — la note ne passe pas — mais il n'envoie pas réécrire au
    bon endroit : on corrige des `---`, on repasse, et le secret reste.

    Le contrôle du secret passe donc **juste avant** celui du frontmatter : assez
    tôt pour gagner sur la forme, assez tard pour ne pas voler la parole aux
    règles qui la méritent davantage (le nom, la zone, ce que le §7 réclame
    d'abord). Ces trois cas tiennent cet ordre : deux qui doivent voir le
    secret, un qui doit entendre le §5 mot pour mot.
    """

    def test_une_cle_privee_dans_un_corps_qui_commence_par_trois_tirets(self):
        """La clé privée complète, derrière des `---` : le refus parle du secret."""
        texte = note(corps="\n---\n\nLa clé privée du dépôt :\n\n" + CLE_PGP_PRIVEE)
        v = PORTE.juger(PORTE.Candidat("0-SAVOIRS", "docker", texte), contexte())
        self.assertFalse(v.accepte)
        self.assertEqual(v.refus.controle, "absence de secret")
        self.assertIn("§7.1", v.refus.regle)
        self.assertNotIn(CORPS_BASE64.splitlines()[0], v.refus.constat)

    def test_l_en_tete_de_cle_privee_seul_derriere_trois_tirets(self):
        """Sans corps de base64 : c'est le motif de ligne qui refuse, et il gagne."""
        texte = note(corps="\n---\n\nLa clé privée du dépôt :\n\n"
                           + DEBUT_ARMURE_PRIVEE)
        v = PORTE.juger(PORTE.Candidat("0-SAVOIRS", "docker", texte), contexte())
        self.assertFalse(v.accepte)
        self.assertEqual(v.refus.controle, "absence de secret")
        self.assertNotIn(DEBUT_ARMURE_PRIVEE, v.refus.constat)

    def test_un_corps_qui_commence_par_trois_tirets_sans_secret_dit_le_cinq(self):
        """Sans secret, le §5 retrouve la parole — et son message, mot pour mot."""
        texte = note(corps="\n---\n\nAucun secret ici, seulement de la prose.")
        v = PORTE.juger(PORTE.Candidat("0-SAVOIRS", "docker", texte), contexte())
        self.assertFalse(v.accepte)
        self.assertEqual(v.refus.controle, "frontmatter conforme")
        self.assertIn("§5", v.refus.regle)
        self.assertEqual(v.refus.constat,
                         "un second bloc de frontmatter s'ouvre dans le corps")


class TestAucunOctetSurLeDisque(unittest.TestCase):
    """Le refus ne doit rien écrire : preuve par un coffre témoin inchangé."""

    def _photo(self, racine):
        etat = {}
        for chemin in sorted(Path(racine).rglob("*")):
            stat = chemin.stat()
            etat[str(chemin)] = (stat.st_mtime_ns, stat.st_size,
                                 chemin.read_text(encoding="utf-8")
                                 if chemin.is_file() else None)
        return etat

    def test_un_texte_fautif_ne_touche_rien(self):
        with tempfile.TemporaryDirectory() as tmp:
            coffre = Path(tmp)
            (coffre / "0-SAVOIRS").mkdir()
            (coffre / "0-SAVOIRS" / "existant.md").write_text(
                "---\nkind: note\n---\n\nDéjà là.", encoding="utf-8")
            avant = self._photo(coffre)

            candidat = PORTE.Candidat(
                "0-SAVOIRS", "existant",
                note(corps="\n\njeton = " + JETON))
            verdict = PORTE.juger(candidat, contexte())

            self.assertFalse(verdict.accepte)
            self.assertEqual(self._photo(coffre), avant)

    def test_la_date_de_reference_ne_change_pas(self):
        # Une écriture « invisible » (même contenu, mtime neuf) se verrait ici.
        with tempfile.TemporaryDirectory() as tmp:
            coffre = Path(tmp)
            fichier = coffre / "0-SAVOIRS" / "existant.md"
            fichier.parent.mkdir()
            fichier.write_text("contenu", encoding="utf-8")
            os.utime(fichier, (1_000_000, 1_000_000))
            avant = fichier.stat().st_mtime_ns
            PORTE.juger(PORTE.Candidat("0-SAVOIRS", "docker",
                                       note(corps="\n\njeton = " + JETON)),
                        contexte())
            self.assertEqual(fichier.stat().st_mtime_ns, avant)


class TestPuretePositive(unittest.TestCase):
    """L'autre face de la pureté : une écriture *impossible* ne gêne pas `juger()`.

    Le coffre témoin montre qu'aucun octet ne change ; ces espions montrent
    qu'aucune écriture n'est seulement *possible*, car `open`, `write_text`,
    `mkdir` et `touch` échouent pendant le jugement. Une porte pure y survit ;
    une porte qui écrit tomberait ici, même sans témoin à comparer.
    """

    def test_juger_survit_a_des_ecritures_impossibles(self):
        def sabotage(*args, **kwargs):
            raise AssertionError("la porte a touché le disque")

        with mock.patch("builtins.open", sabotage), \
                mock.patch.object(Path, "write_text", sabotage), \
                mock.patch.object(Path, "write_bytes", sabotage), \
                mock.patch.object(Path, "mkdir", sabotage), \
                mock.patch.object(Path, "touch", sabotage):
            accepte = PORTE.juger(PORTE.Candidat("0-SAVOIRS", "docker", note()),
                                  contexte())
            refuse = PORTE.juger(
                PORTE.Candidat("0-SAVOIRS", "docker",
                               note(corps="\n\njeton = " + JETON)),
                contexte())

        self.assertTrue(accepte.accepte)
        self.assertFalse(refuse.accepte)


class TestLePlanDeControleDitVrai(unittest.TestCase):
    """La docstring du module numérote les contrôles de la porte, dans l'ordre.

    Elle est le mode d'emploi du refus : un contrôle qu'elle omet, ou qu'elle
    range ailleurs que ``juger``, est un mode d'emploi qui trompe. Ce garde tient
    la docstring collée au code — le §7.3 y est entré au bon rang.
    """

    def _controles_reels(self) -> list:
        """Les libellés de ``Refus``, dans l'ordre où ``juger`` les appelle."""
        source = inspect.getsource(PORTE.juger)
        libelles: list = []
        for nom in re.findall(r"_refus_(\w+)\(", source):
            corps = inspect.getsource(getattr(PORTE, "_refus_" + nom))
            libelle = re.search(r'Refus\(\s*"([^"]+)"', corps).group(1)
            if libelle not in libelles:
                libelles.append(libelle)
        return libelles

    def test_la_docstring_nomme_les_controles_dans_l_ordre_du_code(self):
        numerotes = re.findall(r"^\s*\d+\. ``([^`]+)``", PORTE.__doc__, re.M)
        self.assertEqual(numerotes, self._controles_reels())


class TestLeRangementEtLaCompletion(unittest.TestCase):
    """Ranger déplace une note du vrac ; compléter reprend la sienne **sur place**.

    Un acte qui part d'une note **présente** apporte son chemin (``source``) et le
    nom exact de son fichier : la porte juge alors **deux** chemins — la source et
    la destination — et refuse tout nom qui ne serait pas celui de la note visée.
    """

    def _controle(self, verdict):
        self.assertIsNotNone(verdict.refus, verdict)
        return verdict.refus.controle

    def test_ranger_depuis_le_vrac_ne_fait_que_deplacer(self):
        verdict = PORTE.juger(
            PORTE.Candidat("0-SAVOIRS", "note docker", note(),
                           nom="note-docker.md", source="0-EN-VRAC/note-docker.md"),
            contexte(zones=("0-EN-VRAC", "0-SAVOIRS"), nature=NATURE_DEPOSER,
                     notes_du_coffre=("0-EN-VRAC/note-docker.md",)))
        self.assertTrue(verdict.accepte, verdict.refus)
        self.assertEqual("0-SAVOIRS/note-docker.md", verdict.destination)

    def test_le_vrac_seul_est_une_source(self):
        verdict = PORTE.juger(
            PORTE.Candidat("0-SAVOIRS", "note docker", note(),
                           nom="note-docker.md", source="0-SAVOIRS/note-docker.md"),
            contexte(zones=("0-EN-VRAC", "0-SAVOIRS"), nature=NATURE_DEPOSER,
                     notes_du_coffre=("0-SAVOIRS/note-docker.md",)))
        self.assertEqual("le vrac seul est une source",
                         self._controle(verdict))

    def test_la_note_visee_n_est_pas_la(self):
        verdict = PORTE.juger(
            PORTE.Candidat("0-SAVOIRS", "note docker", note(),
                           nom="note-docker.md", source="0-EN-VRAC/note-docker.md"),
            contexte(zones=("0-EN-VRAC", "0-SAVOIRS"), nature=NATURE_DEPOSER,
                     notes_du_coffre=()))
        self.assertEqual("la note visée n'est pas là",
                         self._controle(verdict))

    def test_le_geste_et_le_chemin_s_accordent(self):
        # Ranger vers la zone d'où la note vient : la destination est la source.
        verdict = PORTE.juger(
            PORTE.Candidat("0-EN-VRAC", "note docker", note(),
                           nom="note-docker.md", source="0-EN-VRAC/note-docker.md"),
            contexte(zones=("0-EN-VRAC",), nature=NATURE_DEPOSER,
                     notes_du_coffre=("0-EN-VRAC/note-docker.md",)))
        self.assertEqual("le geste et le chemin s'accordent",
                         self._controle(verdict))

    def test_le_geste_et_le_chemin_s_accordent_quand_on_deplace(self):
        # Compléter, à l'inverse, ne déplace pas : une destination autre refuse.
        verdict = PORTE.juger(
            PORTE.Candidat("0-SAVOIRS", "note docker", note(),
                           nom="note-docker.md", source="0-EN-VRAC/note-docker.md"),
            contexte(zones=("0-EN-VRAC", "0-SAVOIRS"), nature=NATURE_COMPLETER,
                     notes_du_coffre=("0-EN-VRAC/note-docker.md",)))
        self.assertEqual("le geste et le chemin s'accordent",
                         self._controle(verdict))

    def test_nom_unique_dans_le_coffre(self):
        # Un homonyme ailleurs dans le coffre interdit le rangement (§6, tout le coffre).
        verdict = PORTE.juger(
            PORTE.Candidat("0-SAVOIRS", "note docker", note(),
                           nom="note-docker.md", source="0-EN-VRAC/note-docker.md"),
            contexte(zones=("0-EN-VRAC", "0-SAVOIRS"), nature=NATURE_DEPOSER,
                     notes_du_coffre=("0-EN-VRAC/note-docker.md",
                                      "0-DOCUMENTS/note-docker.md")))
        self.assertEqual("nom unique dans le coffre", self._controle(verdict))

    def test_completer_juge_la_note_presente(self):
        # Sans le texte d'avant, l'ajout ne se mesure pas : échec fermé.
        verdict = PORTE.juger(
            PORTE.Candidat("0-SAVOIRS", "note docker", note(),
                           nom="note-docker.md", source="0-SAVOIRS/note-docker.md"),
            contexte(zones=("0-SAVOIRS",), nature=NATURE_COMPLETER,
                     notes_du_coffre=("0-SAVOIRS/note-docker.md",)))
        self.assertEqual("compléter juge la note présente",
                         self._controle(verdict))

    def test_corriger_juge_aussi_la_note_presente(self):
        # `corriger` change le texte d'une note **tenue sur place** : comme
        # `compléter`, il ne se mesure pas sans le texte qu'elle porte déjà. Sans ce
        # refus, l'acte partait sans rien à quoi se comparer — et sur la note de
        # référence d'un agent, la garde du champ `auteur:` se lisait dans un texte
        # absent (l'`AttributeError` que ce test refuse de laisser passer).
        verdict = PORTE.juger(
            PORTE.Candidat("0-SAVOIRS", "note docker",
                           note(corps="\n\nUn corps corrigé."),
                           nom="note-docker.md", source="0-SAVOIRS/note-docker.md"),
            contexte(zones=("0-SAVOIRS",), nature=NATURE_CORRIGER,
                     notes_du_coffre=("0-SAVOIRS/note-docker.md",)))
        self.assertEqual("corriger juge la note présente",
                         self._controle(verdict))

    def test_corriger_change_le_texte_de_la_note(self):
        # `corriger` n'est pas `compléter` : il change le texte au lieu d'y ajouter.
        # La règle de l'ajout ne le juge donc pas — sinon aucune correction ne
        # passerait. Seul le texte d'avant est exigé, pour que la garde du champ
        # `auteur:` ait de quoi se lire.
        verdict = PORTE.juger(
            PORTE.Candidat("0-SAVOIRS", "note docker",
                           note(corps="\n\nUn corps corrigé."),
                           nom="note-docker.md", source="0-SAVOIRS/note-docker.md",
                           avant=note(corps="\n\nUn corps propre.")),
            contexte(zones=("0-SAVOIRS",), nature=NATURE_CORRIGER,
                     notes_du_coffre=("0-SAVOIRS/note-docker.md",)))
        self.assertTrue(verdict.accepte, verdict.refus)

    def test_completer_une_note_au_texte_vide_est_juge(self):
        # Une note dont le texte est **vide** a bien un texte d'avant : `""`, que la
        # règle mesure — un corps vide est le préfixe de tout corps. C'est ce qui
        # distingue « pas donné » (`avant=None`, refusé juste au-dessus) d'« un texte
        # vide », et ce qui permet d'achever un aperçu vide en début de journée.
        verdict = PORTE.juger(
            PORTE.Candidat(PORTE.CONVENTION.MAINTENANCE, "2026-10-09-x-y.md",
                           "Un aperçu du jour.\n",
                           nom="2026-10-09-apercu-x-y.md",
                           source="_MAINTENANCE/2026-10-09-apercu-x-y.md",
                           avant="", dossier="0-PROJETS/x/carnets"),
            contexte(zones=(PORTE.CONVENTION.MAINTENANCE,), nature=NATURE_COMPLETER,
                     notes_du_coffre=("_MAINTENANCE/2026-10-09-apercu-x-y.md",)))
        self.assertTrue(verdict.accepte, verdict.refus)

    def test_une_note_de_reference_de_personnels_est_tenue_par_son_auteur(self):
        # La note de référence de `0-PERSONNELS/` s'ouvre à l'agent que son champ
        # `auteur:` nomme — dans la note **et** dans le texte proposé — et à personne
        # d'autre. C'est le champ, non le chemin, qui la désigne : le §7.3 la confie à
        # son auteur, comme un carnet l'est à qui le tient.
        chemin = "0-PERSONNELS/ordonnanceur.md"
        avant = note(front="kind: note\nauteur: batisseur\n---", corps="\n\nUn corps.")
        apres = avant + "\n\nUne ligne de plus.\n"
        candidat = PORTE.Candidat("0-PERSONNELS", "ordonnanceur", apres,
                                  nom="ordonnanceur.md", source=chemin, avant=avant)
        chez_lui = PORTE.juger(
            candidat,
            contexte(zones=("0-PERSONNELS",), auteur="batisseur",
                     nature=NATURE_COMPLETER, notes_du_coffre=(chemin,)))
        self.assertTrue(chez_lui.accepte, chez_lui.refus)
        chez_un_autre = PORTE.juger(
            candidat,
            contexte(zones=("0-PERSONNELS",), auteur="assistant",
                     nature=NATURE_COMPLETER, notes_du_coffre=(chemin,)))
        self.assertFalse(chez_un_autre.accepte)
        self.assertIn("auteur", chez_un_autre.refus.constat)

    def test_une_note_de_reference_a_deux_auteurs_ne_change_pas_de_main(self):
        # La note existante porte deux lignes `auteur:` : le frontmatter n'en garde
        # qu'une, la dernière. `batisseur` s'y trouverait donc, à la faveur d'une
        # ligne qui écrase celle d'`assistant` — un champ qui se contredit ne désigne
        # personne, et la tenue sur place ne s'ouvre pas.
        chemin = "0-PERSONNELS/ordonnanceur.md"
        avant = note(front="kind: note\nauteur: assistant\nauteur: batisseur\n---",
                     corps="\n\nUn corps.")
        apres = note(front="kind: note\nauteur: batisseur\n---", corps="\n\nUn corps.")
        candidat = PORTE.Candidat("0-PERSONNELS", "ordonnanceur", apres,
                                  nom="ordonnanceur.md", source=chemin, avant=avant)
        verdict = PORTE.juger(
            candidat,
            contexte(zones=("0-PERSONNELS",), auteur="batisseur",
                     nature=NATURE_COMPLETER, notes_du_coffre=(chemin,)))
        self.assertFalse(verdict.accepte)
        self.assertIn("auteur", verdict.refus.constat)

    def test_completer_n_ajoute_qu_a_la_fin(self):
        verdict = PORTE.juger(
            PORTE.Candidat("0-SAVOIRS", "note docker",
                           note(corps="\n\nUn corps réécrit."),
                           nom="note-docker.md", source="0-SAVOIRS/note-docker.md",
                           avant=note(corps="\n\nUn corps propre.")),
            contexte(zones=("0-SAVOIRS",), nature=NATURE_COMPLETER,
                     notes_du_coffre=("0-SAVOIRS/note-docker.md",)))
        self.assertEqual("compléter n'ajoute qu'à la fin",
                         self._controle(verdict))

    def test_completer_garde_le_frontmatter(self):
        verdict = PORTE.juger(
            PORTE.Candidat("0-SAVOIRS", "note docker",
                           note(front="kind: note\n---",
                                corps="\n\nUn corps propre.\n\nSuite."),
                           nom="note-docker.md", source="0-SAVOIRS/note-docker.md",
                           avant=note(front="kind: note\ntag: docker\n---",
                                      corps="\n\nUn corps propre.")),
            contexte(zones=("0-SAVOIRS",), nature=NATURE_COMPLETER,
                     notes_du_coffre=("0-SAVOIRS/note-docker.md",)))
        self.assertEqual("compléter garde le frontmatter",
                         self._controle(verdict))

    def test_completer_ajoute_a_la_fin_et_accepte(self):
        verdict = PORTE.juger(
            PORTE.Candidat("0-SAVOIRS", "note docker",
                           note(front="kind: note\ntags:\n- docker\n- sauvegarde\n---",
                                corps="\n\nUn corps propre.\n\nSuite."),
                           nom="note-docker.md", source="0-SAVOIRS/note-docker.md",
                           avant=note(front="kind: note\ntags:\n- docker\n---",
                                      corps="\n\nUn corps propre.")),
            contexte(zones=("0-SAVOIRS",), nature=NATURE_COMPLETER,
                     notes_du_coffre=("0-SAVOIRS/note-docker.md",)))
        self.assertTrue(verdict.accepte, verdict.refus)
        self.assertEqual("0-SAVOIRS/note-docker.md", verdict.destination)


class TestDossierJumeau(unittest.TestCase):
    """F2 : un dossier qui se replie au même nom qu'un voisin est refusé (§6, §7.4).

    L'aperçu du jour replie le dossier d'origine en tige : `Réseau` et `reseau` y
    tombent sur le **même** nom, et deux notes de deux dossiers se disputeraient
    l'aperçu. On refuse donc le second dossier — la règle qu'`ecrivain` tient déjà
    pour les dossiers de projet et de chantier.
    """

    def _coffre(self, dossiers):
        racine = tempfile.TemporaryDirectory(prefix="porte-dossier-jumeau-")
        self.addCleanup(racine.cleanup)
        for chemin in dossiers:
            (Path(racine.name) / chemin).mkdir(parents=True, exist_ok=True)
        return Path(racine.name)

    def _deposer(self, coffre, zone):
        return PORTE.juger(
            PORTE.Candidat(zone, "Note", note(), nom="Note.md",
                           source="0-EN-VRAC/Note.md"),
            contexte(zones=("0-EN-VRAC", zone), coffre=coffre,
                     nature=NATURE_DEPOSER,
                     notes_du_coffre=("0-EN-VRAC/Note.md",)))

    def test_un_dossier_jumeau_est_refuse(self):
        coffre = self._coffre(("0-SAVOIRS/Réseau",))
        verdict = self._deposer(coffre, "0-SAVOIRS/reseau")
        self.assertFalse(verdict.accepte)
        self.assertEqual("dossier jumeau", verdict.refus.controle)
        self.assertIn("Réseau", verdict.refus.constat)

    def test_un_dossier_au_nom_distinct_est_accepte(self):
        coffre = self._coffre(("0-SAVOIRS/Réseau",))
        verdict = self._deposer(coffre, "0-SAVOIRS/Stockage")
        self.assertTrue(verdict.accepte, verdict.refus)


if __name__ == "__main__":
    unittest.main()
