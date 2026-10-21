#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Le serveur MCP de l'écrivain : l'écrivain exposé à un harnais pilotant un
modèle local.

La tranche P6 livre l'écrivain en **serveur MCP** : un harnais l'appelle par
stdio, sur proposition d'un modèle local, et la porte et le socle font le
reste — ou le refusent avec son motif. Ce que ces tests montrent, un par un :

- `tools/list` nomme **exactement** les quatre gestes de l'écrivain, et rien d'autre ;
- **aucun outil ne prend de chemin** : le modèle dit *quoi*, jamais *où* — le coffre
  vient de `OBSIA_COFFRE`, pas du message ;
- un acte passé par le serveur est **un seul commit**, comme un acte en direct ;
- un **refus est dit** avec son motif, et rien n'est écrit ;
- **fail-closed** : sans `OBSIA_COFFRE`, ou devant un dossier qui n'est pas un dépôt
  de données, l'écrivain refuse — il ne se rabat jamais sur un autre coffre ;
- le serveur **ne laisse rien** derrière lui : ni fichier compilé, ni acte à moitié.

Comme les autres bancs du produit, le dépôt de données est **jetable** : ces tests
n'écrivent jamais dans un coffre réel. `git` peut manquer : les tests qui en
dépendent sautent alors, jamais la règle.
"""

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
RACINE = Path(__file__).resolve().parent.parent
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

import serveur.mcp_ecrivain as MCP  # noqa: E402

SERVEUR = RACINE / "serveur" / "mcp_ecrivain.py"

GIT = shutil.which("git")

#: « OBSIA_COFFRE n'est pas posée du tout » — distinct de « posée mais vide ».
RETIREE = object()

#: Les quatre gestes, dans l'ordre où le serveur les annonce.
LES_QUATRE_GESTES = ["ecrire_un_carnet", "ranger_une_note", "completer_une_note",
                     "notes_du_coffre"]

#: Ce qu'un outil ne doit **jamais** demander : un endroit où écrire.
DES_NOMS_DE_LIEU = {"coffre", "chemin", "chemin_absolu", "dossier", "fichier",
                    "racine", "depot", "répertoire"}


def git(ou, *arguments):
    """Lance `git` dans `ou` et rend le résultat, sans lever."""
    return subprocess.run(["git", "-C", str(ou), *arguments],
                          capture_output=True, text=True, check=False)


def requete(id_, methode, params=None):
    """Un message JSON-RPC 2.0 prêt à être écrit au serveur."""
    message = {"jsonrpc": "2.0", "id": id_, "method": methode}
    if params is not None:
        message["params"] = params
    return message


def lancer(messages, coffre=RETIREE, cwd=None):
    """Lance le serveur une fois, lui écrit `messages`, rend le processus fini.

    `coffre` : la valeur posée dans `OBSIA_COFFRE`. `RETIREE` (le défaut) retire
    la variable — ce n'est pas la même chose que la poser vide.
    """
    entree = "".join(json.dumps(m, ensure_ascii=False) + "\n" for m in messages)
    return lancer_octets(entree.encode("utf-8"), coffre=coffre, cwd=cwd)


def lancer_octets(octets, coffre=RETIREE, cwd=None):
    """Comme `lancer`, mais on écrit au serveur des **octets** bruts.

    C'est la seule façon d'éprouver ce qu'un harnais peut réellement lui envoyer :
    une ligne qui n'est pas de l'UTF-8 valide n'est pas une chaîne.
    """
    env = dict(os.environ)
    env.pop("OBSIA_COFFRE", None)
    if coffre is not RETIREE:
        env["OBSIA_COFFRE"] = str(coffre)
    return subprocess.run([sys.executable, "-B", str(SERVEUR)], input=octets,
                          capture_output=True, check=False, env=env,
                          cwd=str(cwd) if cwd else None)


def reponses(fini):
    """Les réponses du serveur, décodées — une par ligne non vide de la sortie."""
    brut = fini.stdout
    if isinstance(brut, bytes):
        brut = brut.decode("utf-8", "replace")
    return [json.loads(ligne) for ligne in brut.splitlines() if ligne.strip()]


def appeler_un_outil(nom, arguments, coffre, cwd=None):
    """Un `tools/call`, et le couple (texte, isError) qu'il rend."""
    reponse = appeler_et_rendre(nom, arguments, coffre, cwd=cwd)
    if "result" not in reponse:
        raise AssertionError("pas de résultat : %r" % (reponse,))
    resultat = reponse["result"]
    return resultat["content"][0]["text"], resultat["isError"]


def appeler_et_rendre(nom, arguments, coffre, cwd=None):
    """La réponse **brute** d'un `tools/call` — pour lire aussi une erreur JSON-RPC."""
    fini = lancer([requete(1, "tools/call", {"name": nom, "arguments": arguments})],
                  coffre=coffre, cwd=cwd)
    sorties = reponses(fini)
    if not sorties:
        raise AssertionError("aucune réponse : %r" % (fini.stderr,))
    return sorties[0]


class FauxFlux:
    """Une entrée standard minimale : des octets, et rien d'autre."""

    def __init__(self, octets: bytes):
        self.buffer = io.BytesIO(octets)


def servir_sur_place(octets: bytes):
    """Fait tourner la boucle du serveur **dans ce processus** et rend (réponses, journal).

    Sert à bousculer le serveur là où on ne peut pas le faire de l'extérieur : une
    panne qu'on simule, par exemple.
    """
    ancien = sys.stdin
    sortie, journal = io.StringIO(), io.StringIO()
    sys.stdin = FauxFlux(octets)
    try:
        with contextlib.redirect_stdout(sortie), contextlib.redirect_stderr(journal):
            MCP.main()
    finally:
        sys.stdin = ancien
    return sortie.getvalue(), journal.getvalue()


class BaseDuServeur(unittest.TestCase):
    """Un coffre de test jetable, et l'identifiant d'écrivain dans son bac à sable."""

    AUTEUR = "batisseur"
    DATE = "2026-10-10"
    PROJET = "obsia"
    CHANTIER = "mcp-outils-du-coffre"
    SUJET = "Essai du serveur"
    CORPS = "Un carnet posé par le serveur.\n"

    def setUp(self):
        # `resolve()` : le serveur exige un chemin **réel**, et `/tmp` passe par un
        # lien sur certaines machines — le coffre du banc est donc donné canonique.
        self.parent = Path(tempfile.mkdtemp(prefix="obsia-mcp-")).resolve()
        self.addCleanup(shutil.rmtree, self.parent, ignore_errors=True)
        self.coffre = self.parent / "coffre-de-test"
        self.coffre.mkdir()
        self.initialiser(self.coffre)
        # L'identifiant d'écrivain du banc reste dans le bac à sable : sans cela, le
        # serveur tirerait pour de bon l'identifiant de la station du développeur.
        identifiant = self.parent / "etat" / "ecrivain.id"
        ancien = os.environ.get("OBSIA_ECRIVAIN_ID_FICHIER")
        os.environ["OBSIA_ECRIVAIN_ID_FICHIER"] = str(identifiant)

        def rendre():
            if ancien is None:
                os.environ.pop("OBSIA_ECRIVAIN_ID_FICHIER", None)
            else:
                os.environ["OBSIA_ECRIVAIN_ID_FICHIER"] = ancien

        self.addCleanup(rendre)

    @staticmethod
    def initialiser(coffre):
        """Un dépôt de test avec une branche nommée et un premier commit."""
        init = git(coffre, "init", "--quiet", "-b", "main")
        if init.returncode != 0:  # git d'avant `-b`
            git(coffre, "init", "--quiet")
            git(coffre, "symbolic-ref", "HEAD", "refs/heads/main")
        git(coffre, "config", "init.defaultBranch", "main")
        git(coffre, "config", "user.email", "essai@exemple.invalid")
        git(coffre, "config", "user.name", "Essai")
        (coffre / "0-PROJETS").mkdir(parents=True, exist_ok=True)
        (coffre / "0-PROJETS" / "amorce.md").write_text("Amorce.\n",
                                                        encoding="utf-8")
        git(coffre, "add", "--", "0-PROJETS/amorce.md")
        git(coffre, "commit", "--quiet", "-m", "amorce")

    def tete(self, coffre=None):
        """Le nom du commit de tête du coffre de test."""
        return git(coffre or self.coffre, "rev-parse", "HEAD").stdout.strip()

    def carnet(self, **remplacements):
        """Les arguments d'un `ecrire_un_carnet` d'essai, un champ surchargeable."""
        arguments = dict(auteur=self.AUTEUR, projet=self.PROJET, chantier=self.CHANTIER,
                         sujet=self.SUJET, corps=self.CORPS, date=self.DATE)
        arguments.update(remplacements)
        return arguments


class TestLeProtocoleEtSesOutils(unittest.TestCase):
    """Ce que le serveur annonce — et ce qu'il refuse d'annoncer."""

    def test_tools_list_nomme_exactement_les_quatre_gestes(self):
        fini = lancer([requete(1, "tools/list")])
        outils = reponses(fini)[0]["result"]["tools"]
        self.assertEqual(LES_QUATRE_GESTES, [outil["name"] for outil in outils])

    def test_chaque_outil_dit_ce_qu_il_fait_et_ce_qu_il_exige(self):
        outils = reponses(lancer([requete(1, "tools/list")]))[0]["result"]["tools"]
        for outil in outils:
            self.assertTrue(outil.get("description"), outil["name"])
            schema = outil["inputSchema"]
            self.assertEqual("object", schema["type"], outil["name"])
            for obligatoire in schema.get("required", []):
                self.assertIn(obligatoire, schema["properties"], outil["name"])

    def test_aucun_outil_ne_demande_un_endroit_ou_ecrire(self):
        """Le modèle dit *quoi*, jamais *où* : aucun paramètre ne nomme un lieu."""
        outils = reponses(lancer([requete(1, "tools/list")]))[0]["result"]["tools"]
        for outil in outils:
            demandes = set(outil["inputSchema"]["properties"])
            self.assertEqual(set(), demandes & DES_NOMS_DE_LIEU,
                             "%s demande un lieu : %s" % (outil["name"], demandes))

    def test_initialize_se_nomme_et_rend_la_capacite_des_outils(self):
        fini = lancer([requete(1, "initialize",
                               {"protocolVersion": "2025-06-18", "capabilities": {}})])
        resultat = reponses(fini)[0]["result"]
        self.assertEqual("ecrivain-du-coffre", resultat["serverInfo"]["name"])
        self.assertIn("tools", resultat["capabilities"])
        self.assertEqual("2025-06-18", resultat["protocolVersion"])

    def test_ping_repond_vide(self):
        self.assertEqual({}, reponses(lancer([requete(1, "ping")]))[0]["result"])

    def test_une_methode_inconnue_repond_une_erreur_jsonrpc(self):
        reponse = reponses(lancer([requete(1, "geste/fantaisie")]))[0]
        self.assertEqual(-32601, reponse["error"]["code"])
        self.assertIn("geste/fantaisie", reponse["error"]["message"])

    def test_un_outil_inconnu_repond_une_erreur_jsonrpc(self):
        reponse = reponses(lancer([requete(1, "tools/call",
                                           {"name": "effacer-tout", "arguments": {}})]))[0]
        self.assertEqual(-32602, reponse["error"]["code"])
        self.assertIn("effacer-tout", reponse["error"]["message"])

    def test_une_notification_ne_recoit_pas_de_reponse(self):
        """Sans `id`, c'est une notification : le serveur se tait."""
        fini = lancer([{"jsonrpc": "2.0", "method": "tools/list"}])
        self.assertEqual([], reponses(fini))

    def test_une_ligne_qui_n_est_pas_du_json_ne_fait_pas_mourir_le_serveur(self):
        fini = subprocess.run([sys.executable, "-B", str(SERVEUR)],
                              input="ceci n'est pas du json\n" + json.dumps(
                                  requete(7, "ping")) + "\n",
                              capture_output=True, text=True, check=False,
                              env=dict(os.environ, OBSIA_COFFRE=""))
        sorties = reponses(fini)
        self.assertEqual(-32700, sorties[0]["error"]["code"])
        self.assertEqual(7, sorties[-1]["id"])


@unittest.skipUnless(GIT, "git est absent de cette machine")
class TestUnActeParLeServeurEstUnCommit(BaseDuServeur):
    """Ce que le serveur fait écrire est un acte comme un autre : un seul commit."""

    def test_un_carnet_ecrit_par_le_serveur_est_un_seul_commit_de_plus(self):
        avant = self.tete()
        texte, en_erreur = appeler_un_outil("ecrire_un_carnet", self.carnet(),
                                            coffre=self.coffre)
        self.assertFalse(en_erreur, texte)
        apres = self.tete()
        self.assertNotEqual(avant, apres)
        parents = git(self.coffre, "rev-list", "--parents", "-n", "1", apres).stdout.split()
        self.assertEqual(avant, parents[1])

    def test_le_carnet_est_reellement_pose_et_se_relit(self):
        texte, en_erreur = appeler_un_outil("ecrire_un_carnet", self.carnet(),
                                            coffre=self.coffre)
        self.assertFalse(en_erreur, texte)
        chemin = ("0-PROJETS/obsia/mcp-outils-du-coffre/carnets/"
                  "2026-10-10-mcp-outils-du-coffre-essai-du-serveur.md")
        self.assertIn(chemin, texte)
        self.assertTrue((self.coffre / chemin).is_file())
        contenu = (self.coffre / chemin).read_text(encoding="utf-8")
        self.assertIn("agent: batisseur", contenu)
        self.assertIn("statut: en cours", contenu)
        self.assertIn("Un carnet posé par le serveur.", contenu)

    def test_la_trace_de_l_acte_porte_le_chemin_et_le_commit(self):
        texte, en_erreur = appeler_un_outil("ecrire_un_carnet", self.carnet(),
                                            coffre=self.coffre)
        self.assertFalse(en_erreur, texte)
        self.assertIn(self.tete()[:12], texte)
        self.assertIn("Copie", texte)

    def test_le_serveur_ne_laisse_pas_de_fichier_compile(self):
        """Un serveur lancé par un harnais ne doit pas salir l'arbre de travail."""
        avant = (set((RACINE / "serveur").rglob("__pycache__")) |
                 set((RACINE / "scripts").rglob("__pycache__")))
        appeler_un_outil("ecrire_un_carnet", self.carnet(), coffre=self.coffre)
        apres = (set((RACINE / "serveur").rglob("__pycache__")) |
                 set((RACINE / "scripts").rglob("__pycache__")))
        self.assertEqual(avant, apres)


@unittest.skipUnless(GIT, "git est absent de cette machine")
class TestLeServeurRefuseEtLeDit(BaseDuServeur):
    """Un refus est **dit**, avec son motif, et n'écrit rien."""

    def test_un_doublon_est_refuse_et_le_motif_est_dit(self):
        premier, en_erreur = appeler_un_outil("ecrire_un_carnet", self.carnet(),
                                              coffre=self.coffre)
        self.assertFalse(en_erreur, premier)
        avant = self.tete()
        second, en_erreur = appeler_un_outil("ecrire_un_carnet", self.carnet(),
                                             coffre=self.coffre)
        self.assertTrue(en_erreur, second)
        self.assertIn("Refus", second)
        self.assertIn("unique", second)
        self.assertEqual(avant, self.tete())

    def test_un_statut_hors_convention_est_refuse_et_nomme(self):
        avant = self.tete()
        texte, en_erreur = appeler_un_outil("ecrire_un_carnet",
                                            self.carnet(statut="terminé"),
                                            coffre=self.coffre)
        self.assertTrue(en_erreur, texte)
        self.assertIn("terminé", texte)
        self.assertEqual(avant, self.tete())

    def test_un_carnet_sans_sujet_est_refuse(self):
        avant = self.tete()
        texte, en_erreur = appeler_un_outil("ecrire_un_carnet",
                                            self.carnet(sujet="   "),
                                            coffre=self.coffre)
        self.assertTrue(en_erreur, texte)
        self.assertIn("sujet", texte)
        self.assertEqual(avant, self.tete())

    def test_une_note_a_ranger_qui_manque_est_refusee_et_le_motif_est_dit(self):
        avant = self.tete()
        texte, en_erreur = appeler_un_outil(
            "ranger_une_note",
            {"auteur": self.AUTEUR, "source": "note-qui-n-existe-pas.md",
             "zone": "0-SAVOIRS", "date": self.DATE},
            coffre=self.coffre)
        self.assertTrue(en_erreur, texte)
        self.assertIn("Refus", texte)
        self.assertEqual(avant, self.tete())

    def test_un_refus_n_est_pas_ecrit_dans_un_fichier(self):
        appeler_un_outil("ecrire_un_carnet", self.carnet(), coffre=self.coffre)
        appeler_un_outil("ecrire_un_carnet", self.carnet(), coffre=self.coffre)
        carnets = list((self.coffre / "0-PROJETS" / "obsia" /
                        "mcp-outils-du-coffre" / "carnets").iterdir())
        self.assertEqual(1, len(carnets), [p.name for p in carnets])


class TestLeCoffreVientDeLaVariableJamaisDuMessage(BaseDuServeur):
    """Fail-closed : sans coffre désigné, ou devant autre chose qu'un dépôt, on n'écrit pas.

    Le modèle ne désigne pas le coffre — il ne *peut* pas le désigner — donc c'est
    la variable d'environnement qui décide. Si elle manque, l'écrivain refuse, et
    il ne se rabat **jamais** sur le dossier courant : ce serait écrire quelque part
    que personne n'a désigné.
    """

    def test_sans_variable_l_ecriture_est_refusee(self):
        texte, en_erreur = appeler_un_outil("ecrire_un_carnet", self.carnet(),
                                            coffre=RETIREE, cwd=self.coffre)
        self.assertTrue(en_erreur, texte)
        self.assertIn("OBSIA_COFFRE", texte)
        self.assertIn("refuse", texte)

    def test_une_variable_vide_refuse_l_ecriture(self):
        texte, en_erreur = appeler_un_outil("ecrire_un_carnet", self.carnet(),
                                            coffre="", cwd=self.coffre)
        self.assertTrue(en_erreur, texte)
        self.assertIn("OBSIA_COFFRE", texte)

    def test_sans_variable_rien_n_est_ecrit_meme_dans_le_dossier_courant(self):
        """Le dossier courant est le coffre de test : il ne doit pas servir de repli."""
        avant = self.tete()
        appeler_un_outil("ecrire_un_carnet", self.carnet(), coffre=RETIREE,
                         cwd=self.coffre)
        self.assertEqual(avant, self.tete())
        self.assertEqual("", git(self.coffre, "status", "--porcelain").stdout.strip())

    def test_un_dossier_qui_n_est_pas_un_depot_refuse_l_ecriture(self):
        pas_un_depot = self.parent / "pas-un-depot"
        pas_un_depot.mkdir()
        texte, en_erreur = appeler_un_outil("ecrire_un_carnet", self.carnet(),
                                            coffre=pas_un_depot)
        self.assertTrue(en_erreur, texte)
        self.assertIn("dépôt de données", texte)
        self.assertEqual([], list(pas_un_depot.iterdir()))

    def test_le_refus_sans_coffre_vaut_pour_les_lectures_aussi(self):
        texte, en_erreur = appeler_un_outil("notes_du_coffre", {}, coffre=RETIREE)
        self.assertTrue(en_erreur, texte)
        self.assertIn("OBSIA_COFFRE", texte)


@unittest.skipUnless(GIT, "git est absent de cette machine")
class TestLInventaireDesNotes(BaseDuServeur):
    """Le quatrième geste lit, et ne modifie rien."""

    def test_l_inventaire_liste_les_notes_du_coffre(self):
        appeler_un_outil("ecrire_un_carnet", self.carnet(), coffre=self.coffre)
        texte, en_erreur = appeler_un_outil("notes_du_coffre", {}, coffre=self.coffre)
        self.assertFalse(en_erreur, texte)
        self.assertIn("0-PROJETS/amorce.md", texte)
        self.assertIn("2026-10-10-mcp-outils-du-coffre-essai-du-serveur.md", texte)

    def test_l_inventaire_ne_modifie_rien(self):
        avant = self.tete()
        appeler_un_outil("notes_du_coffre", {}, coffre=self.coffre)
        self.assertEqual(avant, self.tete())
        self.assertEqual("", git(self.coffre, "status", "--porcelain").stdout.strip())


@unittest.skipUnless(GIT, "git est absent de cette machine")
class TestLeServeurNeMeurtPasSurUnMessageMalForme(BaseDuServeur):
    """Un message reçu n'est pas forcément un objet JSON-RPC — et le suivant passe.

    ``null``, un nombre, une chaîne, une liste sont du JSON parfaitement valide :
    le serveur doit les refuser **et continuer**. De même pour une ligne qui n'est
    pas de l'UTF-8 : elle se refuse, elle ne tue pas la boucle. Un serveur qui
    meurt sur un message mal formé est un serveur qu'un harnais ne peut pas
    laisser tourner.
    """

    def apres(self, octets_bruts: bytes):
        """Écrit ces octets, puis un `ping` — et rend toutes les réponses."""
        suite = (json.dumps(requete(9, "ping")) + "\n").encode("utf-8")
        return reponses(lancer_octets(octets_bruts + suite, coffre=self.coffre))

    def test_un_message_qui_n_est_pas_un_objet_est_refuse_et_le_suivant_passe(self):
        for brut in (b"null\n", b"123\n", b'"abc"\n', b"[]\n", b"true\n"):
            sorties = self.apres(brut)
            self.assertEqual(-32600, sorties[0]["error"]["code"], brut)
            self.assertEqual(9, sorties[-1]["id"], brut)
            self.assertEqual({}, sorties[-1]["result"], brut)

    def test_une_ligne_qui_n_est_pas_de_l_utf8_est_refusee_et_le_suivant_passe(self):
        sorties = self.apres(b"\xff\xfe ceci n'est pas de l'utf-8\n")
        self.assertEqual(-32700, sorties[0]["error"]["code"])
        self.assertEqual(9, sorties[-1]["id"])

    def test_une_ligne_qui_n_est_pas_du_json_est_refusee_et_le_suivant_passe(self):
        sorties = self.apres(b"ceci n'est pas du json\n")
        self.assertEqual(-32700, sorties[0]["error"]["code"])
        self.assertEqual(9, sorties[-1]["id"])


@unittest.skipUnless(GIT, "git est absent de cette machine")
class TestUnePanneInterneNeDitPasLeChemin(BaseDuServeur):
    """Ce qui part au modèle ne doit porter aucun chemin de machine (§13).

    Une panne d'écriture — disque plein, disque monté en lecture seule — lève une
    ``OSError`` dont Python compose le texte **en y mettant le chemin visé**. Ce
    texte ne doit pas partir au modèle : il reste au journal local, que seul celui
    qui exploite le serveur lit.
    """

    CHEMIN_DU_DISQUE = "/un/endroit/tres/prive/du/disque/note.md"

    def panne(self, *ignores, **reste):
        raise OSError(28, "No space left on device", self.CHEMIN_DU_DISQUE)

    def test_une_oserror_ne_laisse_fuir_aucun_chemin(self):
        octets = (json.dumps(requete(1, "tools/call", {
            "name": "ecrire_un_carnet", "arguments": self.carnet()})) + "\n").encode("utf-8")
        ancien = os.environ.get("OBSIA_COFFRE")
        os.environ["OBSIA_COFFRE"] = str(self.coffre)
        try:
            with mock.patch.object(MCP.ECRIVAIN, "ecrire_un_carnet", self.panne):
                dit_au_modele, journal = servir_sur_place(octets)
        finally:
            if ancien is None:
                os.environ.pop("OBSIA_COFFRE", None)
            else:
                os.environ["OBSIA_COFFRE"] = ancien
        self.assertNotIn(self.CHEMIN_DU_DISQUE, dit_au_modele)
        self.assertNotIn("No space left", dit_au_modele)
        self.assertIn("panne interne", dit_au_modele)
        self.assertEqual(-32603,
                         json.loads(dit_au_modele.splitlines()[0])["error"]["code"])
        self.assertIn(self.CHEMIN_DU_DISQUE, journal)
        self.assertEqual("", git(self.coffre, "status", "--porcelain").stdout.strip())


@unittest.skipUnless(GIT, "git est absent de cette machine")
class TestLeCoffreDoitEtreUnCheminReel(BaseDuServeur):
    """Le coffre est désigné par son chemin **réel** : absolu, sans détour.

    Un chemin relatif dépendrait du dossier d'où le serveur a été lancé ; un
    chemin qui passe par un lien mènerait ailleurs que là où l'on croit écrire.
    Dans les deux cas l'écrivain refuse plutôt que de deviner.
    """

    def test_un_chemin_relatif_est_refuse(self):
        texte, en_erreur = appeler_un_outil("ecrire_un_carnet", self.carnet(),
                                            coffre="coffre-relatif", cwd=self.parent)
        self.assertTrue(en_erreur, texte)
        self.assertIn("chemin absolu", texte)

    def test_un_chemin_qui_passe_par_un_lien_est_refuse(self):
        lien = self.parent / "coffre-par-un-lien"
        try:
            lien.symlink_to(self.coffre, target_is_directory=True)
        except OSError:
            self.skipTest("les liens symboliques ne sont pas disponibles ici")
        texte, en_erreur = appeler_un_outil("ecrire_un_carnet", self.carnet(), coffre=lien)
        self.assertTrue(en_erreur, texte)
        self.assertIn("lien", texte)
        self.assertEqual("", git(self.coffre, "status", "--porcelain").stdout.strip())

    def _poser_un_lien(self, lien, cible):
        """Un lien symbolique, ou le test s'esquive là où la machine n'en a pas."""
        try:
            lien.symlink_to(cible, target_is_directory=True)
        except OSError:
            self.skipTest("les liens symboliques ne sont pas disponibles ici")

    def _coffre_sous(self, *morceaux):
        """Un dépôt de test neuf à un chemin construit, prêt à recevoir un acte."""
        coffre = self.parent.joinpath(*morceaux)
        coffre.mkdir(parents=True)
        self.initialiser(coffre)
        return coffre

    def test_un_lien_sur_un_parent_du_chemin_est_refuse(self):
        """Le lien n'est pas le dernier composant : il coiffe le coffre."""
        coffre = self._coffre_sous("vrai-dossier", "coffre-sous-lien")
        self._poser_un_lien(self.parent / "dossier-par-un-lien",
                            self.parent / "vrai-dossier")
        texte, en_erreur = appeler_un_outil(
            "ecrire_un_carnet", self.carnet(),
            coffre=self.parent / "dossier-par-un-lien" / "coffre-sous-lien")
        self.assertTrue(en_erreur, texte)
        self.assertIn("lien", texte)
        self.assertEqual("", git(coffre, "status", "--porcelain").stdout.strip())

    def test_un_lien_au_milieu_du_chemin_est_refuse(self):
        """Le lien est un composant intermédiaire, ni la tête ni la queue."""
        coffre = self._coffre_sous("vrai-milieu", "sous", "coffre-milieu")
        self._poser_un_lien(self.parent / "vrai-milieu" / "sous-par-un-lien",
                            self.parent / "vrai-milieu" / "sous")
        texte, en_erreur = appeler_un_outil(
            "ecrire_un_carnet", self.carnet(),
            coffre=self.parent / "vrai-milieu" / "sous-par-un-lien" / "coffre-milieu")
        self.assertTrue(en_erreur, texte)
        self.assertIn("lien", texte)
        self.assertEqual("", git(coffre, "status", "--porcelain").stdout.strip())

    def test_un_lien_a_but_relatif_est_refuse(self):
        """Un lien dont la cible est écrite en relatif mène tout autant ailleurs."""
        coffre = self._coffre_sous("vrai-relatif", "coffre-relatif")
        self._poser_un_lien(self.parent / "lien-relatif",
                            Path("vrai-relatif") / "coffre-relatif")
        texte, en_erreur = appeler_un_outil("ecrire_un_carnet", self.carnet(),
                                            coffre=self.parent / "lien-relatif")
        self.assertTrue(en_erreur, texte)
        self.assertIn("lien", texte)
        self.assertEqual("", git(coffre, "status", "--porcelain").stdout.strip())

    def test_le_chemin_reel_du_coffre_est_accepte(self):
        texte, en_erreur = appeler_un_outil("ecrire_un_carnet", self.carnet(),
                                            coffre=self.coffre)
        self.assertFalse(en_erreur, texte)

    def test_un_chemin_qui_remonte_par_deux_points_est_accepte(self):
        """Un `..` qui revient sur le coffre n'est pas un détour."""
        detour = "%s/../%s" % (self.coffre, self.coffre.name)
        texte, en_erreur = appeler_un_outil("ecrire_un_carnet", self.carnet(),
                                            coffre=detour)
        self.assertFalse(en_erreur, texte)

    def test_un_chemin_avec_des_barres_doublees_est_accepte(self):
        """Une double barre en tête n'est pas un détour : elle mène au même lieu."""
        detour = "/" + str(self.coffre)
        texte, en_erreur = appeler_un_outil("ecrire_un_carnet", self.carnet(),
                                            coffre=detour)
        self.assertFalse(en_erreur, texte)

    def test_un_dossier_qui_n_est_pas_un_depot_refuse_l_inventaire(self):
        pas_un_depot = self.parent / "pas-un-depot"
        pas_un_depot.mkdir()
        texte, en_erreur = appeler_un_outil("notes_du_coffre", {}, coffre=pas_un_depot)
        self.assertTrue(en_erreur, texte)
        self.assertIn("dépôt de données", texte)

    def test_un_dossier_qui_n_est_pas_un_depot_refuse_les_gestes_de_note(self):
        pas_un_depot = self.parent / "pas-un-depot-note"
        pas_un_depot.mkdir()
        texte, en_erreur = appeler_un_outil(
            "ranger_une_note",
            {"auteur": "batisseur", "source": "0-EN-VRAC/x.md", "zone": "0-SAVOIRS"},
            coffre=pas_un_depot)
        self.assertTrue(en_erreur, texte)
        self.assertIn("dépôt de données", texte)


@unittest.skipUnless(GIT, "git est absent de cette machine")
class TestUnParametreMalTapeEstRefuse(BaseDuServeur):
    """Le schéma annonce des chaînes : ce qui n'en est pas une est mal formé.

    Un nombre, une liste ou un objet là où le schéma dit « chaîne » n'est pas une
    demande qu'on juge : c'est une demande mal formée, et la réponse le dit
    (``-32602``) au lieu de la traduire en douce.
    """

    def test_un_corps_qui_n_est_pas_une_chaine_est_refuse(self):
        reponse = appeler_et_rendre("ecrire_un_carnet", dict(self.carnet(), corps=123),
                                    coffre=self.coffre)
        self.assertEqual(-32602, reponse["error"]["code"])
        self.assertIn("corps", reponse["error"]["message"])

    def test_un_texte_qui_n_est_pas_une_chaine_est_refuse(self):
        reponse = appeler_et_rendre(
            "completer_une_note",
            {"auteur": "batisseur", "source": "0-EN-VRAC/x.md",
             "texte": ["une", "liste"]},
            coffre=self.coffre)
        self.assertEqual(-32602, reponse["error"]["code"])
        self.assertIn("texte", reponse["error"]["message"])

    def test_une_date_qui_n_est_pas_une_chaine_est_refusee(self):
        reponse = appeler_et_rendre(
            "ranger_une_note",
            {"auteur": "batisseur", "source": "0-EN-VRAC/x.md", "zone": "0-SAVOIRS",
             "date": 20261010},
            coffre=self.coffre)
        self.assertEqual(-32602, reponse["error"]["code"])
        self.assertIn("date", reponse["error"]["message"])

    def test_un_objet_ne_vaut_pas_une_chaine(self):
        reponse = appeler_et_rendre("ecrire_un_carnet",
                                    dict(self.carnet(), sujet={"texte": "non"}), 
                                    coffre=self.coffre)
        self.assertEqual(-32602, reponse["error"]["code"])


if __name__ == "__main__":
    unittest.main()
