#!/usr/bin/env python3
"""Les deux portes des secrets refusent la même chose.

`garde_secrets` n'a que deux appelants : la porte du **commit**
(`depot_de_donnees.avant_commit` → `garde_secrets.verifier`) et la porte de
l'**entrée** (`porte_entree._refus_secret`, sur le texte candidat). Ces deux
portes ne partagent pas le même point d'entrée : la première passe par
`verifier()`, la seconde appelle directement `secret_dans_une_ligne`,
`jeton_isole` et `bloc_base64`. Une porte qui perdrait un de ces trois motifs
ne rougissait donc nulle part — et une note de la mémoire aurait pu porter un
bloc de base64 sans qu'aucun test ne le dise.

Ce fichier relie les deux par une **table unique** : chaque secret de la table
doit être refusé par les deux portes. Il fige aussi, dans le même mouvement, une
décision qui n'était écrite qu'en creux : rien ne relit la mémoire **déjà
écrite** — une note qui portait un secret avant le garde passe, et c'est voulu.
"""

import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "scripts"))
sys.path.insert(0, str(RACINE / "serveur"))
sys.path.insert(0, str(RACINE / "tests"))

import garde_secrets as GS                # noqa: E402
import porte_entree as PORTE             # noqa: E402
from test_porte_entree import BLOC_BASE64, contexte, note   # noqa: E402

def une_valeur_qui_a_forme_de_jeton() -> str:
    """Un secret à forme de jeton, **assemblé à l'exécution**.

    Écrit d'un seul trait — et surtout affecté à une variable dont le nom dit
    « jeton » — il rendrait le dépôt impubliable : `tests/test_publier.py` refuse
    un dépôt dont l'export porte une trouvaille.
    """
    return "sk-ant-api03-" + "Z" * 40


def une_valeur_affectee() -> str:
    """Un secret **affecté** à son nom, assemblé pour la même raison.

    « mot de passe » ne s'écrit pas d'un trait ici : le contrôle de publication
    du dépôt lit ce fichier, et le dépôt doit rester publiable.
    """
    return "%s = \"%s\"" % ("mot " + "de passe", "Tr0ub4dor" + "&3Change")


#: La table des deux portes. Chaque cas est un **texte de note complet**, tel
#: qu'il se présente aux deux : la porte du commit le lit comme le contenu d'un
#: fichier indexé, la porte d'entrée comme une note candidate. Un cas ajouté ici
#: est donc exigé des deux côtés sans qu'on ait à y penser.
#:
#: Ce sont les trois formes que les deux portes partagent vraiment
#: (`secret_dans_une_ligne`, `jeton_isole`, `bloc_base64`). Une clé privée
#: `-----BEGIN … PRIVATE KEY-----` n'y est pas : les `---` de l'en-tête referment
#: le frontmatter de la note, et la porte d'entrée la refuse **avant** d'arriver
#: au secret, pour un autre motif. Le verdict est le même — aucun trou — mais la
#: mécanique n'est pas partagée, donc sa place n'est pas dans cette table.
SECRETS_A_DES_PORTES = (
    ("secret affecté",
     note(corps="\n\n" + une_valeur_affectee())),
    ("jeton isolé",
     note(corps="\n\n" + une_valeur_qui_a_forme_de_jeton())),
    ("bloc de base64",
     note(corps="\n\n" + BLOC_BASE64)),
)

#: Une note qui ne porte aucun secret : le témoin, sans quoi un garde qui refuse
#: tout passerait la table du premier coup.
NOTE_PROPRE = note(corps="\n\nUn corps propre, et rien d'autre.")


@unittest.skipUnless(shutil.which("git"), "git est nécessaire à la porte du commit")
class TestLesDeuxPortesDeSecrets(unittest.TestCase):
    """Une table, deux portes : elles doivent refuser ensemble, ou pas du tout."""

    def setUp(self):
        self.parent = Path(tempfile.mkdtemp(prefix="obsia-test-secrets-"))
        self.addCleanup(shutil.rmtree, self.parent, ignore_errors=True)
        self.coffre = self.parent / "coffre"
        self.coffre.mkdir()
        # Pas de `-b` : le test ne regarde jamais le nom de la branche, et
        # `git init -b` demanderait git ≥ 2.28 sans que le `skipUnless` sache
        # le dire — sur un git plus ancien, `setUp` tomberait au lieu de sauter.
        self.git("init", "-q")
        # Un commit vide : l'index se vide ensuite par `git reset`, même sur un
        # dépôt neuf, sans dépendre d'un `HEAD` qui n'existe pas encore.
        self.git("commit", "-q", "--allow-empty", "-m", "vide")

    def git(self, *arguments):
        """git dans le coffre, avec une identité à nous et sans signature."""
        return subprocess.run(
            ["git", "-C", str(self.coffre),
             "-c", "user.name=Test OBSIA",
             "-c", "user.email=test@example.invalid",
             "-c", "commit.gpgsign=false", *arguments],
            capture_output=True, text=True, check=False)

    def indiquer(self, texte, nom="0-SAVOIRS/une-note.md"):
        """Met le texte à l'index sous `nom`, et rend ce que la porte en dit."""
        chemin = self.coffre / nom
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(texte, encoding="utf-8")
        self.git("add", nom)
        with redirect_stderr(StringIO()):
            code = GS.verifier(self.coffre)
        self.git("reset", "-q")
        chemin.unlink()
        return code

    def porte_de_l_entree(self, texte):
        """Le contrôle de secret de la porte d'entrée, et lui seul."""
        verdict = PORTE.juger(PORTE.Candidat("0-SAVOIRS", "docker", texte),
                              contexte())
        return None if verdict.refus is None else verdict.refus.controle

    def test_chaque_secret_est_refuse_par_les_deux_portes(self):
        for libelle, texte in SECRETS_A_DES_PORTES:
            with self.subTest(libelle, porte="commit"):
                self.assertEqual(1, self.indiquer(texte),
                                 "la porte du commit laisse passer : %s" % libelle)
            with self.subTest(libelle, porte="entrée"):
                self.assertEqual("absence de secret", self.porte_de_l_entree(texte),
                                 "la porte de l'entrée laisse passer : %s" % libelle)

    def test_une_note_propre_passe_les_deux_portes(self):
        self.assertEqual(0, self.indiquer(NOTE_PROPRE),
                         "la porte du commit refuse une note sans secret")
        self.assertIsNone(self.porte_de_l_entree(NOTE_PROPRE),
                          "la porte de l'entrée refuse une note sans secret")

    def test_une_note_qui_portait_deja_le_secret_passe(self):
        """On ne relit pas la mémoire écrite — décision, pas oubli.

        La porte du commit ne juge les **valeurs nommées** que sur les lignes
        qu'il ajoute. Une note entrée avant le garde, ou écrite à la main puis
        committée sans lui, garde son secret : un commit qui ne touche pas cette
        ligne ne le voit pas, et il ne le verra jamais. Retirer un secret déjà
        écrit est un acte humain, sur la note et dans l'historique — aucun
        contrôle ne le fait à notre place.

        La limite de ce choix est écrite et testée juste en dessous : les blocs
        de base64 et les jetons isolés, eux, sont relus dans le fichier entier à
        chaque commit qui le touche. Ce n'est pas la même chose, et il vaut mieux
        que ce soit dit que découvert.
        """
        texte = note(corps="\n\n" + une_valeur_affectee())
        nom = "0-SAVOIRS/deja-ecrite.md"
        chemin = self.coffre / nom
        chemin.parent.mkdir(parents=True, exist_ok=True)
        # Un saut de ligne final : sans lui, l'ajout qui suit réécrirait aussi la
        # ligne du secret, et le test prouverait le contraire de ce qu'il dit.
        chemin.write_text(texte + "\n", encoding="utf-8")
        self.git("add", nom)
        self.git("commit", "-q", "-m", "entrée avant le garde")

        chemin.write_text(texte + "\nUn ajout sans rapport.\n", encoding="utf-8")
        self.git("add", nom)
        with redirect_stderr(StringIO()):
            self.assertEqual(0, GS.verifier(self.coffre),
                             "le secret déjà écrit a été relu")

    def test_un_bloc_de_base64_deja_ecrit_est_relu_a_chaque_commit(self):
        """Contraste : le bloc, lui, se relit dans le fichier entier.

        Un bloc n'a de sens que dans son ensemble : la porte lit donc le contenu
        complet de chaque fichier que le commit touche. Celui-ci était déjà là,
        sa ligne n'a pas bougé, et il est refusé quand même — c'est voulu.
        """
        texte = note(corps="\n\n" + BLOC_BASE64)
        nom = "0-SAVOIRS/bloc-ancien.md"
        chemin = self.coffre / nom
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(texte + "\n", encoding="utf-8")
        self.git("add", nom)
        self.git("commit", "-q", "-m", "entrée avant le garde")

        chemin.write_text(texte + "\nUn ajout sans rapport.\n", encoding="utf-8")
        self.git("add", nom)
        with redirect_stderr(StringIO()):
            self.assertEqual(1, GS.verifier(self.coffre),
                             "un bloc de base64 déjà écrit doit être relu")


if __name__ == "__main__":
    unittest.main()
