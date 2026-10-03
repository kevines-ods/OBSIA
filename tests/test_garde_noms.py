"""La garde des noms interdits — `.githooks/pre-commit.d/20-noms-interdits`.

Elle relit les lignes **ajoutées** du commit contre la liste locale. Prouvé ici,
sur un vrai dépôt : un nom ajouté est **signalé en avertissement sans refuser**
(le commit passe), un nom seulement retiré ne dit rien, un nom trop court est
ignoré, un tiret compte comme un caractère de mot et la frontière est Unicode
comme `\\w` en Python (même règle que `motif_des_noms()` de `publier.py`), et
sans liste rien n'est contrôlé. La liste retient des identités mais frappe des
mots : la garde avertit, elle ne refuse plus.
"""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

GARDE = (Path(__file__).resolve().parent.parent
         / ".githooks" / "pre-commit.d" / "20-noms-interdits")


def utf8_disponible() -> bool:
    """Le crochet borne en `[[:alnum:]]`, Unicode seulement en locale UTF-8.

    Il essaie lui-même `C.UTF-8`, `fr_FR.UTF-8`, `en_US.UTF-8` ; on vérifie
    qu'au moins une répond, sinon la frontière retombe en ASCII et le test de
    frontière Unicode ci-dessous n'a plus de sens.
    """
    for essai in ("C.UTF-8", "fr_FR.UTF-8", "en_US.UTF-8"):
        env = dict(os.environ, LC_ALL=essai)
        vues = subprocess.run(["locale", "charmap"], env=env,
                              capture_output=True, text=True)
        if vues.returncode == 0 and "utf" in vues.stdout.lower():
            return True
    return False


@unittest.skipUnless(shutil.which("git") and shutil.which("sh"), "git et sh requis")
class GardeNoms(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.depot = self.tmp / "depot"
        self.depot.mkdir()
        self.liste = self.tmp / "noms-interdits"
        self.liste.write_text("# hôtes\nposte-atelier\nia\n", encoding="utf-8")
        self.git("init", "-q", "-b", "main")
        (self.depot / "note.md").write_text("poste-atelier\n", encoding="utf-8")
        self.git("add", "-A")
        self.git("-c", "user.name=t", "-c", "user.email=t@example.com",
                 "commit", "-q", "--no-verify", "-m", "racine")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.depot, check=True, capture_output=True)

    def lancer(self, liste=None, environ=None):
        env = dict(os.environ, OBSIA_NOMS_INTERDITS=str(liste or self.liste))
        env.update(environ or {})
        return subprocess.run(["sh", str(GARDE)], cwd=self.depot, env=env,
                              capture_output=True, text=True)

    def ajouter(self, texte):
        (self.depot / "autre.md").write_text(texte, encoding="utf-8")
        self.git("add", "-A")

    def test_un_nom_ajoute_est_signalé_sans_refuser(self):
        """Un nom ajouté avertit : stderr le cite, mais le commit passe (exit 0)."""
        self.ajouter("À lancer sur Poste-Atelier.\n")
        resultat = self.lancer()
        self.assertEqual(resultat.returncode, 0)
        self.assertIn("Poste-Atelier", resultat.stderr)

    def test_retirer_un_nom_passe(self):
        (self.depot / "note.md").write_text("le poste secondaire\n", encoding="utf-8")
        self.git("add", "-A")
        self.assertEqual(self.lancer().returncode, 0)

    def test_un_nom_trop_court_est_ignore(self):
        self.ajouter("Voir IA/system/.\n")
        resultat = self.lancer()
        self.assertEqual(resultat.returncode, 0)
        self.assertEqual(resultat.stderr, "")

    def test_sans_liste_rien_n_est_controle(self):
        self.ajouter("poste-atelier\n")
        self.assertEqual(self.lancer(self.tmp / "absente").returncode, 0)

    def test_un_tiret_compte_comme_un_caractere_de_mot(self):
        """Même règle que `motif_des_noms()` : `poste-atelier` ne se trouve ni
        dans `poste-atelier-2` ni dans `mon-poste-atelier` — un tiret compte
        comme un caractère de mot ; `grep -w` s'y arrêterait et signalerait à
        tort."""
        self.ajouter("Le poste-atelier-2 et le mon-poste-atelier sont prêts.\n")
        resultat = self.lancer()
        self.assertEqual(resultat.returncode, 0)
        self.assertEqual(resultat.stderr, "")

    @unittest.skipUnless(utf8_disponible(), "aucune locale UTF-8 disponible")
    def test_la_frontiere_de_mot_suit_python_en_unicode(self):
        """`\\w` de Python est Unicode : une lettre accentuée est un caractère de
        mot. `Caféposte-atelier` ne contient donc pas le nom, comme dans
        `motif_des_noms()` — le crochet s'aligne en posant lui-même une locale
        UTF-8, même quand l'appelant lui en impose une ASCII."""
        self.ajouter("Caféposte-atelier et puis rien.\n")
        resultat = self.lancer(environ={"LC_ALL": "C", "LANG": "C"})
        self.assertEqual(resultat.returncode, 0)
        self.assertEqual(resultat.stderr, "",
                         "une frontière Unicode ne doit pas signaler un faux positif")

    def test_un_nom_encadre_de_slashs_est_signale(self):
        """Le nom reste trouvé quand un chemin l'encadre — un nom d'hôte dans
        un chemin `~/.config/`, comme dans `publier.py`."""
        self.ajouter("Config lue dans ~/.config/poste-atelier/\n")
        resultat = self.lancer()
        self.assertEqual(resultat.returncode, 0)
        self.assertIn("poste-atelier", resultat.stderr)


if __name__ == "__main__":
    unittest.main()
