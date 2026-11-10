"""La frontière publique : ce que le coffre a le droit de porter ne part pas.

Le §7.1 du contrat du coffre parent laisse la mémoire privée porter une adresse
IP privée et un nom d'hôte interne — les refuser fermerait la mémoire au nom de
la publication. La frontière ne se joue donc pas dans le coffre : elle se joue
dans **l'artefact**, c'est-à-dire dans ce qui sort de `HEAD`, moins les zones
privées et les fichiers qui ne se publient jamais.

Ce fichier le vérifie de bout en bout, depuis une note piégée jusqu'à l'arbre
exporté, pour les trois formes que la publication refuse. Il caractérise un
comportement qui existe déjà : c'est un filet, pas une construction.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))                              # `scripts/` n'est pas un paquet

import publier as PUB                                          # noqa: E402

#: Les trois formes, assemblées pour que ce fichier — publié — n'en porte aucune.
PIEGE_IP = ".".join(("192", "168", "1", "42"))
PIEGE_COURRIEL = "@".join(("jean.dupont", "mon-entreprise.fr"))
PIEGE_HOTE = ".".join(("nas", "maison", "ts.net"))

NOTE_PIEGEE = """# Note de la mémoire privée

Le stockage répond sur {ip}.
Le contrôleur vit sous {hote}.
Écrire à {courriel}.
"""


def note_piegee() -> str:
    return NOTE_PIEGEE.format(ip=PIEGE_IP, courriel=PIEGE_COURRIEL, hote=PIEGE_HOTE)


class BaseFrontiere(unittest.TestCase):
    """Un dépôt source jetable, et son export."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.racine = Path(self.tmp.name)
        self.source = self.racine / "source"
        self.source.mkdir()
        PUB.git(self.source, "init", "-q")
        PUB.git(self.source, "config", "user.email", "test@" + "exemple.fr")
        PUB.git(self.source, "config", "user.name", "test")

    def ecrire(self, relatif: str, texte: str):
        chemin = self.source / relatif
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(texte, encoding="utf-8")

    def valider(self, message="note"):
        PUB.git(self.source, "add", "-A")
        PUB.git(self.source, "commit", "-q", "-m", message)

    def exporter(self) -> Path:
        vers = self.racine / "export"
        PUB.exporter(self.source, vers)
        return vers

    def contenu_de_l_export(self, vers: Path) -> str:
        return "\n".join(chemin.read_text(encoding="utf-8", errors="replace")
                         for chemin in sorted(vers.rglob("*")) if chemin.is_file())

    def etiquettes(self, controle) -> set:
        return {trouvaille[2] for trouvaille in controle.trouvailles}


class TestLaMemoirePriveeNePartPas(BaseFrontiere):
    def test_une_note_piegee_dans_une_zone_privee_ne_part_pas(self):
        self.ecrire("mémoire/note.md", note_piegee())
        self.valider()
        vers = self.exporter()
        contenu = self.contenu_de_l_export(vers)
        self.assertNotIn(PIEGE_IP, contenu)
        self.assertNotIn(PIEGE_COURRIEL, contenu)
        self.assertNotIn(PIEGE_HOTE, contenu)
        self.assertEqual(set(), self.etiquettes(PUB.controler_fuites(vers)))

    def test_un_fichier_de_la_liste_jamais_ne_part_pas_meme_commite(self):
        self.ecrire(".env", note_piegee())
        self.valider()
        contenu = self.contenu_de_l_export(self.exporter())
        self.assertNotIn(PIEGE_IP, contenu)
        self.assertNotIn(PIEGE_COURRIEL, contenu)


class TestLaFrontiereRefuseLeReste(BaseFrontiere):
    def test_la_meme_note_dans_un_fichier_publie_est_refusee(self):
        self.ecrire("README.md", note_piegee())
        self.valider()
        controle = PUB.controler_fuites(self.exporter())
        self.assertEqual({"adresse IP privée", "adresse de courriel", "nom d'hôte interne"},
                         self.etiquettes(controle))

    def test_le_refus_dit_ou_regarder(self):
        self.ecrire("docs/note.md", "Corps.\n" + note_piegee())
        self.valider()
        controle = PUB.controler_fuites(self.exporter())
        lieux = {(str(l[0]), l[1]) for l in controle.trouvailles}
        self.assertIn("docs/note.md", {lieu[0] for lieu in lieux})
        self.assertTrue(all(numero for _, numero in lieux))

    def test_l_arbre_de_travail_sale_ne_part_pas(self):
        self.ecrire("README.md", "Rien de privé.\n")
        self.valider()
        self.ecrire("brouillon-de-passage.md", note_piegee())
        controle = PUB.controler_fuites(self.exporter())
        self.assertEqual(set(), self.etiquettes(controle))


if __name__ == "__main__":
    unittest.main()
