#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Les crochets du dépôt de données, exécutés par un vrai `git commit`.

Rien dans la suite ne laissait git appeler un crochet :
`tests/test_installer.py` vérifiait que `.githooks/pre-commit` existe, est
exécutable et que `core.hooksPath` le désigne — sans jamais le lancer ;
`tests/test_garde_noms.py` montait bien un dépôt réel mais lançait son crochet
par `sh` ; `tests/test_depot_de_donnees.py` appelait `avant_commit()` en
processus. Un crochet plus jamais appelé, ou qui appellerait un script déplacé,
ne rougissait donc nulle part : le coffre aurait accepté des secrets en silence.

Ce fichier fait le chemin entier, tel qu'installé : `git init` par l'installeur,
crochets posés par `installer.preparer_depot_de_donnees()`, un fichier mis à
l'index, puis **`git commit`** — et c'est git qui appelle le crochet.

**Isolation du produit** — le produit du coffre temporaire était un **lien**
vers le vrai dépôt. Le crochet y lisait `obsia.local.yml`, le profil de la
machine : le test passait dans un worktree (pas de profil) et rougissait dans
un coffre installé (profil posé), en annonçant que l'avertissement « pas
d'écrivain » manquait. Un test qui raconte l'état de la machine ne garde rien.
Le produit est désormais une **copie**, et
`TestLeProduitResteDansLeCoffreTemporaire` interdit le retour du lien. Ce n'est
pas `HOME` qui manquait d'isolation, c'est le produit.
"""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "scripts"))

import installer as INST            # noqa: E402
import modules as MOD               # noqa: E402

#: Ce qu'on ne recopie pas du dépôt pour fabriquer le produit du test :
#: ses objets, ses caches, et surtout `obsia.local.yml` — le profil de la
#: machine, qui décidait du verdict avant l'isolation.
NON_RECOPIE = shutil.ignore_patterns(
    ".git", "obsia.local.yml", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".venv")

def une_valeur_qui_a_forme_de_jeton() -> str:
    """Un secret à forme de jeton, **assemblé à l'exécution**.

    Écrit d'un seul trait, il rendrait le dépôt impubliable : `tests/test_publier.py`
    refuse un dépôt dont l'export porte une trouvaille, et le contrôle de
    publication bloquerait la livraison du produit lui-même.
    """
    return "sk-ant-api03-" + "Z" * 40


#: Une note de mémoire qui n'a rien d'un secret.
NOTE_PROPRE = ("---\nkind: note\ntags:\n  - docker\n---\n\nUne note propre.\n")


@unittest.skipUnless(shutil.which("git"), "git est nécessaire pour exécuter un crochet")
class BaseCrochet(unittest.TestCase):
    """Un coffre temporaire outillé par l'installeur, rien de plus."""

    def setUp(self):
        self.parent = Path(tempfile.mkdtemp(prefix="obsia-test-crochet-"))
        self.addCleanup(shutil.rmtree, self.parent, ignore_errors=True)
        self.coffre = self.parent / "coffre"
        self.coffre.mkdir()
        # Le dépôt de données n'est outillé qu'autour d'un vrai coffre (§7.1) :
        # un marqueur de coffre suffit à l'installeur pour le reconnaître.
        (self.coffre / "0-SAVOIRS").mkdir()
        # Le produit vit à la racine du coffre, comme après une installation :
        # le crochet l'appelle par `$racine/@PRODUIT@`. C'est une **copie**, et
        # pas un lien vers le vrai dépôt : tant que c'en était un, le crochet
        # lisait le profil de la machine et le test racontait l'état de cette
        # machine-là (voir la docstring du module). Mesuré : 0,04 s et 2,9 Mo
        # par cas, aucun processus lancé.
        self.produit = self.coffre / RACINE.name
        shutil.copytree(RACINE, self.produit, ignore=NON_RECOPIE)
        INST.preparer_depot_de_donnees(self.produit, RACINE)

    def git(self, *arguments):
        """git dans le coffre, avec une identité à nous et sans signature."""
        return subprocess.run(
            ["git", "-C", str(self.coffre),
             "-c", "user.name=Test OBSIA", "-c", "user.email=test@example.invalid",
             "-c", "commit.gpgsign=false", *arguments],
            capture_output=True, text=True, check=False)

    def ecrire_et_indexer(self, nom, contenu):
        chemin = self.coffre / nom
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(contenu, encoding="utf-8")
        self.git("add", nom)

    def commit(self, message):
        return self.git("commit", "-m", message)

    def tete(self):
        """Le nom du commit de tête, ou la chaîne vide si le dépôt est nu."""
        return self.git("rev-parse", "HEAD").stdout.strip()


class TestLeCrochetRefuseUnSecret(BaseCrochet):
    """`git commit` d'un fichier qui ajoute un secret : refusé par le crochet."""

    def test_un_secret_mis_a_l_index_arrete_le_commit(self):
        self.ecrire_et_indexer(
            "0-SAVOIRS/avec-secret.md",
            "---\nkind: note\ntags:\n  - docker\n---\n\njeton = \"%s\"\n"
            % une_valeur_qui_a_forme_de_jeton())
        avant = self.tete()
        resultat = self.commit("une note qui n'aurait pas dû passer")
        # Le refus doit venir du crochet : son message, pas une erreur de git.
        self.assertIn("Refusé : ce commit ajoute une valeur à forme de secret",
                      resultat.stderr, resultat.stdout)
        self.assertIn("0-SAVOIRS/avec-secret.md", resultat.stderr,
                      "le refus doit nommer le fichier fautif")
        self.assertNotEqual(resultat.returncode, 0, "le commit a été accepté")
        self.assertEqual(self.tete(), avant, "un commit a été créé malgré le refus")


class TestLeCrochetQuiAvertitLaissePasser(BaseCrochet):
    """Un crochet qui ne peut pas vérifier avertit et laisse le commit passer."""

    def test_sans_ecrivain_declare_le_commit_passe_et_le_dit(self):
        self.ecrire_et_indexer("0-SAVOIRS/une-note.md", NOTE_PROPRE)
        resultat = self.commit("une note propre")
        self.assertEqual(resultat.returncode, 0,
                         resultat.stderr or resultat.stdout)
        self.assertIn("obsia.local.yml ne déclare pas d'écrivain", resultat.stderr,
                      "l'avertissement du crochet doit apparaître")
        self.assertIn("une note propre", self.git("log", "-1", "--format=%s")
                      .stdout, "le commit doit exister")

    def test_avec_un_ecrivain_declare_le_crochet_n_avertit_pas(self):
        """Le profil est posé **dans la copie** : l'avertissement disparaît.

        Témoin du test précédent : sans lui, il pourrait être vert sur un
        `stderr` qui contient la phrase quel que soit le profil. L'écrivain
        déclaré est celui de cette machine, calculé ici — sur une autre, le
        crochet refuserait le commit, et ce test dirait autre chose.
        """
        (self.produit / "obsia.local.yml").write_text(
            "ecrivain: %s\n" % MOD.nom_machine(), encoding="utf-8")
        self.ecrire_et_indexer("0-SAVOIRS/une-note.md", NOTE_PROPRE)
        resultat = self.commit("une note propre")
        self.assertEqual(resultat.returncode, 0,
                         resultat.stderr or resultat.stdout)
        # La preuve que le crochet a **tourné**, et pas seulement qu'il s'est tu :
        # sans cette ligne, le test serait vert si le contrôle de la mémoire
        # n'était plus appelé du tout. Le vérificateur écrit son verdict sur la
        # sortie d'erreur, que le crochet relaie telle quelle.
        self.assertIn("Mémoire du coffre cohérente.", resultat.stderr,
                      "le crochet doit avoir réellement contrôlé la mémoire")
        self.assertNotIn("ne déclare pas d'écrivain", resultat.stderr,
                         "l'avertissement ne doit pas sortir quand l'écrivain "
                         "est déclaré dans le produit")


class TestLeCrochetLaissePasserCeQuiEstPropre(BaseCrochet):
    """Contrôle : le crochet n'est pas un mur — une note saine est acceptée."""

    def test_une_note_sans_secret_est_acceptee(self):
        self.ecrire_et_indexer("0-SAVOIRS/une-note.md", NOTE_PROPRE)
        resultat = self.commit("une note propre")
        self.assertEqual(resultat.returncode, 0,
                         resultat.stderr or resultat.stdout)
        self.assertNotIn("forme de secret", resultat.stderr)


class TestLeProduitResteDansLeCoffreTemporaire(BaseCrochet):
    """Le produit du test ne sort jamais de son dossier temporaire.

    C'est l'interdiction que la tranche 3 avait laissée ouverte : le produit
    était un lien vers le vrai dépôt, donc le crochet y lisait un profil qui
    vivait hors de sa portée, et le verdict changeait d'une machine à l'autre.
    Un `skipIf` sur l'environnement, un `HOME` propre ou un `stderr` filtré
    auraient caché le symptôme, pas fermé la porte.

    Les deux côtés se résolvent avant d'être comparés : `/tmp` est un vrai
    dossier sur cette machine, il ne l'est pas partout — un chemin non résolu
    ferait échouer la comparaison sans qu'aucun lien n'existe dans le coffre.
    """

    def test_le_produit_est_une_copie_sous_le_dossier_temporaire(self):
        """Rejouable : un temporaire qui est un lien, et ce cas rougit.

        Montage : `mkdir -p /tmp/dossier-reel && ln -s /tmp/dossier-reel
        /tmp/lien-tmp`, puis `TMPDIR=/tmp/lien-tmp python3 -m unittest
        tests.test_crochets_executes`. Ce qu'il prouve : sans `resolve()` des deux
        côtés, la comparaison porte sur un chemin brut et un chemin résolu, et ce
        cas échoue ; avec, il passe (six tests, `OK` au-dessus). Le voisin
        `test_aucun_lien_du_coffre_ne_ressort` reste **vert** sous ce montage :
        il ne regarde que les liens du coffre, il n'y en a pas — il n'est pas
        falsifié par là, et il ne faut pas le prétendre.
        """
        self.assertFalse(self.produit.is_symlink(),
                         "le produit doit être une copie, pas un lien vers %s"
                         % RACINE)
        self.assertTrue(self.produit.is_dir(), "le produit doit exister")
        self.assertIn(self.parent.resolve(), self.produit.resolve().parents,
                      "le produit résout hors du dossier temporaire : %s"
                      % self.produit.resolve())

    def test_aucun_lien_du_coffre_ne_ressort(self):
        for chemin in self.coffre.rglob("*"):
            if chemin.is_symlink():
                self.assertIn(self.parent.resolve(), chemin.resolve().parents,
                              "un lien du coffre sort du dossier temporaire : %s"
                              % chemin)


if __name__ == "__main__":
    unittest.main()
