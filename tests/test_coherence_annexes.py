"""Le préambule du noyau et le dossier des annexes s'accordent (§5).

Le préambule de `IA/system/VAULT-CONTRACT.md` porte le tableau qui fait foi :
quelle annexe se lit avant quel acte. Rien ne tenait cet accord. Une annexe
présente mais jamais citée — écrite, publiée, et lue par personne — ou une
annexe citée mais absente — un renvoi mort — partait en silence. La scission
des annexes par acte agrandit ce trou ; on le ferme d'abord.

Chaque test travaille sur un dépôt témoin : deux fichiers suffisent pour
éprouver la réciprocité dans les deux sens, et pour distinguer les deux
échecs. Le dernier test porte sur le vrai dépôt.

L'exemption de l'index du dossier n'est pas écrite ici ni dans le contrôle :
elle est importée de `verif_catalogue`, son unique endroit (§5).
"""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True          # ne pas semer de __pycache__ dans le dépôt
RACINE_DEPOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE_DEPOT / "scripts"))      # `scripts/` n'est pas un paquet

import verif_catalogue as VCA           # noqa: E402
import verif_contrat as VCT             # noqa: E402


def noyau(citees, ligne_en_trop=None):
    """Un noyau minimal : le seul tableau que la réciprocité lit."""
    lignes = ["# Contrat", "", VCT.ENTETE_DU_TABLEAU, "| --- | --- |"]
    lignes += ["| `contrat/%s` | un acte quelconque |" % nom for nom in citees]
    if ligne_en_trop:
        lignes.append(ligne_en_trop)
    lignes += ["", "---", "", "## 1. Vocabulaire", "", "| Terme | Nature |", "| --- | --- |"]
    return "\n".join(lignes) + "\n"


class DepotTemoin(unittest.TestCase):
    """Un dépôt témoin : un noyau, un dossier d'annexes, des erreurs à plat."""

    def setUp(self):
        self.racine = Path(tempfile.mkdtemp(prefix="obsia-test-annexes-"))
        self.addCleanup(shutil.rmtree, self.racine, ignore_errors=True)
        (self.racine / VCT.DOSSIER_ANNEXES).mkdir(parents=True)
        self.erreurs = []
        self.ecrire_index()

    def ecrire_noyau(self, texte):
        chemin = self.racine / VCT.NOYAU
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(texte, encoding="utf-8")

    def ecrire_annexe(self, nom):
        (self.racine / VCT.DOSSIER_ANNEXES / nom).write_text(
            "---\nkind: contrat\n---\n\nUne annexe.\n", encoding="utf-8")

    def ecrire_index(self):
        """L'index du dossier : présent dans un dossier bien formé, exempté."""
        self.ecrire_annexe(VCA.NOM_EXEMPT_CONTRAT)

    def verifier(self):
        return VCT.verifier_annexes_du_preambule(self.racine, self._erreur)

    def _erreur(self, chemin, message):
        self.erreurs.append((str(chemin), message))

    def textes(self):
        return "\n".join("%s : %s" % (chemin, message) for chemin, message in self.erreurs)


class TestReciprocite(DepotTemoin):
    """Présente ⟺ citée. Les deux sens, deux échecs distincts."""

    def test_accord_parfait_ne_dit_rien(self):
        self.ecrire_noyau(noyau(["contrat-a.md"]))
        self.ecrire_annexe("contrat-a.md")
        self.verifier()
        self.assertEqual([], self.erreurs, self.textes())

    def test_annexe_presente_mais_jamais_citee(self):
        self.ecrire_noyau(noyau(["contrat-a.md"]))
        self.ecrire_annexe("contrat-a.md")
        self.ecrire_annexe("contrat-b.md")
        self.verifier()
        self.assertEqual(1, len(self.erreurs), self.textes())
        self.assertIn("contrat-b.md", self.textes())
        self.assertIn("jamais citée", self.textes())

    def test_annexe_citee_mais_absente(self):
        self.ecrire_noyau(noyau(["contrat-a.md", "contrat-b.md"]))
        self.ecrire_annexe("contrat-a.md")
        self.verifier()
        self.assertEqual(1, len(self.erreurs), self.textes())
        self.assertIn("contrat-b.md", self.textes())
        self.assertIn("absent", self.textes())

    def test_annexe_citee_hors_du_dossier(self):
        self.ecrire_noyau(noyau(["contrat-a.md"], "| `contrat/contrat-a.md` et `ailleurs.md` | un acte |"))
        self.ecrire_annexe("contrat-a.md")
        self.verifier()
        self.assertEqual(1, len(self.erreurs), self.textes())
        self.assertIn("ailleurs.md", self.textes())

    def test_index_du_dossier_n_est_pas_une_annexe(self):
        self.ecrire_noyau(noyau(["contrat-a.md"]))
        self.ecrire_annexe("contrat-a.md")
        self.ecrire_annexe(VCA.NOM_EXEMPT_CONTRAT)
        self.verifier()
        self.assertEqual([], self.erreurs, self.textes())
        # L'exemption n'est pas recopiée : c'est le même objet que celui du
        # contrôle du catalogue, donc une seule règle pour un seul cas.
        self.assertIs(VCT.NOM_EXEMPT_CONTRAT, VCA.NOM_EXEMPT_CONTRAT)

    def test_exemption_ne_protege_pas_un_vide(self):
        # Une exemption qui ne nomme rien de présent ne protège qu'un trou : le
        # dossier des annexes a un index ou n'en a pas, et s'il n'en a pas, ce
        # n'est pas une annexe de moins, c'est une liste qui manque.
        self.ecrire_noyau(noyau(["contrat-a.md"]))
        self.ecrire_annexe("contrat-a.md")
        (self.racine / VCT.DOSSIER_ANNEXES / VCA.NOM_EXEMPT_CONTRAT).unlink()
        self.verifier()
        self.assertEqual(1, len(self.erreurs), self.textes())
        self.assertIn(VCA.NOM_EXEMPT_CONTRAT, self.textes())

    def test_tableau_absent_est_signale(self):
        self.ecrire_noyau("# Contrat\n\nPlus de tableau.\n")
        self.ecrire_annexe("contrat-a.md")
        self.verifier()
        self.assertEqual(1, len(self.erreurs), self.textes())
        self.assertIn(VCT.ENTETE_DU_TABLEAU, self.textes())

    def test_sans_noyau_rien_a_dire(self):
        self.ecrire_annexe("contrat-a.md")
        self.assertIsNone(self.verifier())
        self.assertEqual([], self.erreurs, self.textes())

    def test_les_autres_tableaux_ne_sont_pas_lus(self):
        self.ecrire_noyau(noyau(["contrat-a.md"]))
        self.ecrire_annexe("contrat-a.md")
        self.ecrire_annexe("vocabulaire.md")   # cité nulle part, et c'est un défaut
        texte = noyau(["contrat-a.md"]).replace(
            "| Terme | Nature |", "| `contrat/vocabulaire.md` | piège |")
        self.ecrire_noyau(texte)
        self.verifier()
        self.assertEqual(1, len(self.erreurs), self.textes())
        self.assertIn("vocabulaire.md", self.textes())


class TestLeVraiDepot(unittest.TestCase):
    """Le dépôt tel qu'il est : l'accord doit tenir aujourd'hui."""

    def test_le_preambule_cite_des_annexes(self):
        citees = VCT.annexes_citees(RACINE_DEPOT)
        self.assertTrue(citees, "le tableau du préambule ne cite aucune annexe")

    def test_le_depot_s_accorde(self):
        erreurs = []
        VCT.verifier_annexes_du_preambule(
            RACINE_DEPOT, lambda chemin, message: erreurs.append((chemin, message)))
        self.assertEqual([], erreurs, "\n".join("%s : %s" % e for e in erreurs))


if __name__ == "__main__":
    unittest.main()
