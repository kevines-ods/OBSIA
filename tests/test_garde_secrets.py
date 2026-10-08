#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`garde_secrets.py` : ce que le pre-commit du dépôt de données refuse d'ajouter.

Le 2026-10-04, un mot de passe est entré en clair dans la mémoire du coffre
(`_MAINTENANCE/opencode.md`), puis a été recopié par un index régénéré. Rien ne
l'a arrêté : le motif « secret affecté » de `publier.py` ne voit qu'une valeur
**nommée**, et un mot de passe collé seul, sans le mot « mot de passe », passe
au travers.

Ces tests fixent les deux refus — la valeur nommée, reprise à la source unique
qu'est `publier.BLOQUANTS`, et le jeton isolé à forte entropie — ainsi que les
faux positifs qu'ils ne doivent pas emporter : une prose légitime du coffre
(gabarit, chemin, phrase), une empreinte sha256, un identifiant de commit, un
fichier qui n'est pas de l'UTF-8.

Les faux secrets sont recollés au moment du test (cf. `assemble`) : le contrôle
de fuite de `publier.py` lit aussi ce fichier.
"""

import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import garde_secrets as GS      # noqa: E402
import publier as PUB           # noqa: E402


def assemble(*morceaux: str) -> str:
    """Recolle un faux secret au moment du test — le fichier est relu aussi."""
    return "".join(morceaux)


#: Un mot de passe factice : 32 caractères, trois familles, forte entropie.
#: Il imite la forme du vrai cas qui a échoué, jamais sa valeur.
JETON = assemble("Vf7K", "q2Zm", "9Xt4", "Lp6R", "n3Wc", "8Bd5", "Gy1H", "s0Uj")

#: Un mot de passe à symboles, du genre que `openssl rand` ne produit pas.
SYMBOLES = assemble("P@ssw0rd", "-x9K", "f2Lm7", "Qw8Z")

#: Ce que rend `openssl rand -hex 16` : 32 hexadécimaux, sans structure.
HEX32 = "6f1d2a3b4c5d6e7f8a9b0c1d2e3f4a5b"

#: Une empreinte sha256 citée dans une note : 64 hexadécimaux minuscules.
SHA256 = "0d96a4ff68ad6d4b6f1f30f713b18d5184912ba8dd389f86aa7710db079abcb0"

#: Un identifiant de commit : 40 hexadécimaux minuscules.
COMMIT = "a4867830d96a4ff68ad6d4b6f1f30f713b18d518"

#: Un mot-note légitime, mais qui n'est qu'un mot : une seule famille.
MOT = "anticonstitutionnellement"


def git(ou, *arguments):
    return subprocess.run(["git", "-C", str(ou), *arguments],
                          capture_output=True, text=True, check=False)


class BaseDepot(unittest.TestCase):
    """Un dépôt de données minimal, monté une fois par test."""

    def setUp(self):
        self.parent = Path(tempfile.mkdtemp(prefix="obsia-test-garde-"))
        self.addCleanup(shutil.rmtree, self.parent, ignore_errors=True)
        self.vault = self.parent / "coffre"
        self.vault.mkdir()
        git(self.vault, "init", "--quiet")
        git(self.vault, "config", "user.email", "test@exemple.invalid")
        git(self.vault, "config", "user.name", "Test")
        (self.vault / "0-PROJETS").mkdir(parents=True)
        (self.vault / "0-PROJETS" / "note.md").write_text("Corps.\n", encoding="utf-8")
        git(self.vault, "add", "-A")
        git(self.vault, "commit", "--quiet", "-m", "amorce")

    def poser(self, chemin: str, contenu: str):
        """Écrit un fichier texte et le met à l'index — ce que verra le pre-commit."""
        fichier = self.vault / chemin
        fichier.parent.mkdir(parents=True, exist_ok=True)
        fichier.write_text(contenu, encoding="utf-8")
        git(self.vault, "add", "--", chemin)

    def poser_octets(self, chemin: str, octets: bytes):
        """Écrit un fichier en octets — binaire ou mal encodé."""
        fichier = self.vault / chemin
        fichier.parent.mkdir(parents=True, exist_ok=True)
        fichier.write_bytes(octets)
        git(self.vault, "add", "--", chemin)

    def juger(self):
        with redirect_stdout(StringIO()) as sortie, redirect_stderr(StringIO()) as err:
            code = GS.verifier(self.vault)
        return code, sortie.getvalue() + err.getvalue()


class TestSourceUnique(unittest.TestCase):
    """Les motifs de secret ne s'écrivent pas ici : ils viennent de `publier`."""

    def test_les_motifs_de_secret_sont_ceux_de_publier(self):
        attendus = {
            "clé privée", "jeton d'API", "secret affecté", "clé secrète AWS",
        }
        recus = {etiquette for etiquette, _ in GS.motifs_secrets()}
        self.assertEqual(attendus, recus)
        par_etiquette = {e: m for e, m in PUB.BLOQUANTS}
        for etiquette, motif in GS.motifs_secrets():
            self.assertIs(motif, par_etiquette[etiquette])

    def test_les_motifs_de_publication_ne_sont_pas_repris(self):
        """Courriel, IP privée, nom d'hôte : le coffre privé les porte."""
        recus = {etiquette for etiquette, _ in GS.motifs_secrets()}
        self.assertNotIn("adresse de courriel", recus)
        self.assertNotIn("adresse IP privée", recus)
        self.assertNotIn("nom d'hôte interne", recus)

    def test_une_etiquette_disparue_de_publier_est_signalee(self):
        """Un garde muet vaut moins que pas de garde : mieux vaut échouer fort."""
        original = PUB.BLOQUANTS
        PUB.BLOQUANTS = tuple(
            (e, m) for e, m in original if e != "secret affecté")
        try:
            with self.assertRaises(RuntimeError):
                GS.motifs_secrets()
        finally:
            PUB.BLOQUANTS = original


class TestValeurAffectee(unittest.TestCase):
    """Constat 1 — la valeur d'un « secret affecté » doit avoir forme de secret.

    Les remontées réelles du coffre sont des gabarits, des chemins et une phrase.
    Les refuser serait refuser la mémoire ; garder le garde exige de les
    reconnaître pour ce qu'ils sont.
    """

    def test_un_gabarit_entier_ou_en_tete_n_est_pas_un_secret(self):
        for valeur in ("mot-de-passe", "yourpassword", "change-root-password",
                       "change-user-password", "change-me", "changez-moi",
                       "placeholder", "example", "à changer"):
            with self.subTest(valeur=valeur):
                self.assertFalse(GS.valeur_a_forme_de_secret(valeur))

    def test_un_secret_qui_porte_un_mot_de_gabarit_reste_un_secret(self):
        """Le gabarit se juge **en tête** de la valeur, pas quelque part dedans."""
        for valeur in ("k7maQ2pL9vR4tW8yZ1a", "Tr0ub4dor&3Change",
                       "8f3Qz2Lm91Rt4W8yExemple"):
            with self.subTest(valeur=valeur):
                self.assertTrue(GS.valeur_a_forme_de_secret(valeur))

    def test_un_chemin_n_est_exempte_qu_en_tete(self):
        for valeur in ("/root/.restic-exemple.pw", "~/cle.pw",
                       "./cle.pw", "../cle.pw",
                       "**`/root/.restic-exemple.pw`**"):
            with self.subTest(valeur=valeur):
                self.assertFalse(GS.valeur_a_forme_de_secret(valeur))

    def test_un_slash_au_milieu_n_est_pas_un_chemin(self):
        self.assertTrue(GS.valeur_a_forme_de_secret("8f3/Qz2!Lm91Rt4W8y"))

    def test_une_prose_non_guillemetee_n_est_pas_un_secret(self):
        for valeur in ("correct horse battery staple",
                       "T; echo; set -e; cp -a /etc/x"):
            with self.subTest(valeur=valeur):
                self.assertFalse(GS.valeur_a_forme_de_secret(valeur))

    def test_une_phrase_de_passe_guillemetee_est_un_secret(self):
        self.assertTrue(GS.valeur_a_forme_de_secret(
            "correct horse battery staple", guillemetee=True))

    def test_une_ligne_de_commande_guillemetee_n_est_pas_une_phrase_de_passe(self):
        self.assertFalse(GS.valeur_a_forme_de_secret(
            "T; echo; set -e; cp -a /etc/x", guillemetee=True))

    def test_une_valeur_guillemetee_qui_n_est_pas_une_commande_est_un_secret(self):
        """Resserré : `&` ne trahit plus une commande, et une espace ne suffit pas."""
        for valeur in ("Tr0ub4dor&3Change", "Kf7&Lm2Qw9Zx",
                       "correct horse & battery staple"):
            with self.subTest(valeur=valeur):
                self.assertTrue(GS.valeur_a_forme_de_secret(
                    valeur, guillemetee=True))

    def test_une_espace_et_un_marqueur_shell_exemptent_ensemble(self):
        """Un séparateur de commande (`;`, `|`), un accent grave ou `$(` — rien d'autre."""
        for valeur in ("cp -a /etc/x; echo ok", "a | b", "a `b c`", "a $(b c)"):
            with self.subTest(valeur=valeur):
                self.assertFalse(GS.valeur_a_forme_de_secret(
                    valeur, guillemetee=True))

    def test_un_marqueur_shell_sans_espace_n_exempte_pas(self):
        """Les deux conditions sont exigées : `Kf7&Lm2Qw9Zx` reste un mot de passe."""
        for valeur in ("Kf7&Lm2Qw9Zx", "a;b;c;d;e;f;g;h;i;j", "$(k7maQ2pL9vR4tW8y)"):
            with self.subTest(valeur=valeur):
                self.assertTrue(GS.valeur_a_forme_de_secret(
                    valeur, guillemetee=True))

    def test_la_ponctuation_ordinaire_n_exempte_plus(self):
        """`&`, `$` seul, parenthèses, accolades et chevrons vivent dans la prose."""
        for valeur in ("coût $5 par mois et par personne",
                       "voir (annexe) du guide",
                       "a <b> c",
                       "x {y} z"):
            with self.subTest(valeur=valeur):
                self.assertTrue(GS.valeur_a_forme_de_secret(
                    valeur, guillemetee=True))

    def test_un_mot_de_passe_est_une_valeur_de_secret(self):
        self.assertTrue(GS.valeur_a_forme_de_secret(JETON))
        self.assertTrue(GS.valeur_a_forme_de_secret(SYMBOLES))


class TestJetonIsole(unittest.TestCase):
    """Tout le contenu d'un fichier n'est qu'un jeton : le cas qui a échoué."""

    def test_un_mot_de_passe_seul_est_un_jeton(self):
        self.assertEqual(JETON, GS.jeton_isole(JETON + "\n"))

    def test_un_mot_de_passe_a_symboles_est_un_jeton(self):
        self.assertEqual(SYMBOLES, GS.jeton_isole(SYMBOLES))

    def test_un_aleatoire_hex_de_seize_octets_est_un_jeton(self):
        """`openssl rand -hex 16` : 32 hexadécimaux, pas une empreinte connue."""
        self.assertEqual(HEX32, GS.jeton_isole(HEX32 + "\n"))

    def test_une_empreinte_sha256_n_est_pas_un_jeton(self):
        self.assertIsNone(GS.jeton_isole(SHA256))

    def test_un_identifiant_de_commit_n_est_pas_un_jeton(self):
        self.assertIsNone(GS.jeton_isole(COMMIT))
        self.assertIsNone(GS.jeton_isole(COMMIT[:12]))
        self.assertIsNone(GS.jeton_isole(COMMIT[:7]))

    def test_une_phrase_avec_espaces_n_est_pas_un_jeton(self):
        self.assertIsNone(GS.jeton_isole("Voici une note ordinaire, avec des espaces."))

    def test_un_mot_unique_n_est_pas_un_jeton(self):
        self.assertIsNone(GS.jeton_isole(MOT))

    def test_un_jeton_trop_court_n_est_pas_un_jeton(self):
        self.assertIsNone(GS.jeton_isole(assemble("aB3", "xY9")))

    def test_une_adresse_avec_point_n_est_pas_un_jeton(self):
        self.assertIsNone(GS.jeton_isole(assemble("zq3rT9wP4mK7", "@", "local.net")))

    def test_une_adresse_sans_point_n_est_pas_une_adresse(self):
        """Constat 3 — `_ADRESSE` exige un point dans le domaine."""
        self.assertIn("@", assemble("zq3rT9wP4mK7", "@", "localnet"))
        self.assertIsNotNone(GS.jeton_isole(assemble("zq3rT9wP4mK7", "@", "localnet")))

    def test_une_url_seule_n_est_pas_un_jeton(self):
        self.assertIsNone(GS.jeton_isole("https://exemple.fr/un/chemin/assez/long"))


class TestEmpreintes(unittest.TestCase):
    """Constat 3 — `_EMPREINTE` borné aux longueurs réelles, ou à sha/commit."""

    def test_les_longueurs_reelles_sont_des_empreintes(self):
        self.assertTrue(GS.est_empreinte(SHA256))            # 64
        self.assertTrue(GS.est_empreinte(COMMIT))            # 40
        self.assertTrue(GS.est_empreinte(COMMIT[:12]))       # 12
        self.assertTrue(GS.est_empreinte(COMMIT[:7]))        # 7

    def test_un_aleatoire_hex_n_est_pas_une_empreinte(self):
        self.assertFalse(GS.est_empreinte("a" * 8 + "b" * 8))     # 16
        self.assertFalse(GS.est_empreinte(HEX32))                 # 32
        self.assertFalse(GS.est_empreinte("a" * 20))              # 20

    def test_un_hex_pres_d_un_mot_sha_ou_commit_est_une_empreinte(self):
        self.assertTrue(GS.est_empreinte(HEX32, contexte="sha256 : %s" % HEX32))
        self.assertTrue(GS.est_empreinte(HEX32, contexte="commit %s" % HEX32))
        self.assertTrue(GS.est_empreinte(HEX32, contexte="empreinte git"))

    def test_un_non_hex_ne_devient_pas_une_empreinte_par_le_contexte(self):
        self.assertFalse(GS.est_empreinte(SYMBOLES, contexte="commit sha256"))


class TestOctets(BaseDepot):
    """Constat 2 — un fichier qui n'est pas de l'UTF-8 ne fait pas tomber le garde."""

    def test_un_binaire_ne_fait_pas_tomber_le_garde(self):
        self.poser_octets("0-PROJETS/image.png",
                          b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x01\x00")
        code, _ = self.juger()
        self.assertEqual(0, code)

    def test_un_fichier_latin1_garde_le_secret(self):
        # Recollée à l'exécution : la ligne du test ne doit pas porter elle-même
        # un secret affecté, sinon l'aperçu de publication la signale.
        self.poser_octets("0-PROJETS/note.md",
                          b"caf\xe9\n"
                          + assemble("mot de passe", " : ", JETON).encode("ascii")
                          + b"\n")
        code, _ = self.juger()
        self.assertEqual(1, code)


class TestSurUnDepot(BaseDepot):
    """Le garde jugé là où il vit : l'index du dépôt de données."""

    def test_le_cas_reel_est_refuse(self):
        """Un fichier dont tout le contenu est un jeton — le 2026-10-04."""
        self.poser("_MAINTENANCE/opencode.md", JETON + "\n")
        code, message = self.juger()
        self.assertEqual(1, code)
        self.assertIn("opencode.md", message)
        self.assertNotIn(JETON, message)

    def test_une_valeur_nommee_ajoutee_est_refusee(self):
        self.poser("0-PROJETS/note.md",
                   "Corps.\nmot de passe : %s\n" % JETON)
        code, message = self.juger()
        self.assertEqual(1, code)
        self.assertIn("secret affecté", message)

    def test_les_formes_reelles_du_coffre_passent(self):
        """Les gabarits, chemins et phrases relevés au corpus ne se refusent pas."""
        contenu = "\n".join([
            "password: mot-de-passe",
            "MYSQL_ROOT_PASSWORD: change-root-password",
            "MYSQL_PASSWORD: change-user-password",
            "DB_PASSWORD=yourpassword",
            "- Mot de passe : **`%s`** (600)" % assemble("/root/.restic-", "exemple.pw"),
            "export RESTIC_PASSWORD_FILE=/root/.restic-exemple.pw",
        ]) + "\n"
        self.poser("0-PROJETS/labo.md", contenu)
        code, message = self.juger()
        self.assertEqual(0, code, message)

    def test_une_note_ordinaire_passe(self):
        """Ni courriel ni IP privée ne sont des secrets : le coffre les porte."""
        self.poser("0-PROJETS/note.md",
                   "Corps.\nContact : qui@exemple.fr, hôte 192.0.2.10\n")
        code, _ = self.juger()
        self.assertEqual(0, code)

    def test_une_ligne_de_commande_guillemetee_passe(self):
        """Les deux lignes de commande recopiées du coffre restent tolérées."""
        self.poser("0-PROJETS/commande.md",
                   "ssh hote 'read -rsp \"nouveau jeton : \" T; echo; set -e; "
                   "cp -a /etc/check.env /tmp/x'\n")
        self.poser("0-PROJETS/commande-2.md",
                   "jeton : \" T; echo; set -e; cp -a /etc/check.env "
                   "/etc/check.env.backup.$(date +%F); { printf \"\n")
        code, message = self.juger()
        self.assertEqual(0, code, message)

    def test_une_empreinte_citee_passe(self):
        self.poser("0-PROJETS/licence.md",
                   "LICENSE sha256 : %s\ncommit %s\n" % (SHA256, COMMIT))
        code, _ = self.juger()
        self.assertEqual(0, code)

    def test_sans_depot_git_le_garde_se_tait(self):
        autre = self.parent / "pas-un-depot"
        autre.mkdir()
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            self.assertEqual(0, GS.verifier(autre))


class TestDansLeCrochet(unittest.TestCase):
    """Le garde est armé par le pre-commit, dans `avant_commit`."""

    def setUp(self):
        self.parent = Path(tempfile.mkdtemp(prefix="obsia-test-crochet-"))
        self.addCleanup(shutil.rmtree, self.parent, ignore_errors=True)
        self.vault = self.parent / "coffre"
        self.vault.mkdir()
        git(self.vault, "init", "--quiet")
        git(self.vault, "config", "user.email", "test@exemple.invalid")
        git(self.vault, "config", "user.name", "Test")
        (self.vault / "note.md").write_text("Corps.\n", encoding="utf-8")
        git(self.vault, "add", "-A")
        git(self.vault, "commit", "--quiet", "-m", "amorce")
        self.produit = self.parent / "OBSIA"
        (self.produit / "scripts").mkdir(parents=True)
        import modules as MOD
        (self.produit / MOD.NOM_PROFIL).write_text(
            "ecrivain: %s\n" % MOD.nom_machine(), encoding="utf-8")
        (self.produit / "scripts" / "verifier_coffre.py").write_text(
            "import sys\nsys.exit(0)\n", encoding="utf-8")
        import depot_de_donnees as DD
        self.DD = DD

    def test_un_secret_refuse_le_commit_avant_les_carnets(self):
        (self.vault / "opencode.md").write_text(JETON + "\n", encoding="utf-8")
        git(self.vault, "add", "-A")
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            self.assertEqual(1, self.DD.avant_commit(self.vault, self.produit))

    def test_une_note_ordinaire_laisse_passer_le_commit(self):
        (self.vault / "note.md").write_text("Corps.\nSuite.\n", encoding="utf-8")
        git(self.vault, "add", "-A")
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            self.assertEqual(0, self.DD.avant_commit(self.vault, self.produit))


if __name__ == "__main__":
    unittest.main()
