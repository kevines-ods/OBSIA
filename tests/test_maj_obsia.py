"""Le moment où la mise à jour automatique doit s'arrêter (§12).

`scripts/maj_obsia.py` tourne sans personne devant l'écran, toutes les heures,
sur un poste qui n'est pas celui où l'on travaille. Ce qui doit être prouvé
n'est donc pas qu'il met à jour — c'est qu'il **s'arrête** : sur une machine
qui n'est pas la sienne, devant un arbre modifié localement, et devant deux
histoires divergentes.

La décision est isolée de toute commande. `decider()` ne reçoit que des faits,
plus une fonction qui répond « `origin/main` descend-il de `HEAD` ? ». Les
tests lui passent une fonction qui **lève** si on l'appelle là où elle ne doit
pas l'être : c'est ainsi qu'on prouve qu'aucune commande git n'est lancée pour
rien.

Peu de tests touchent le disque, et ils sont là parce que le défaut a été trouvé
en exécutant le script et non en le relisant : dans un worktree lié, `.git` est
un **fichier**, pas un répertoire — la garde qui vérifiait `is_dir()` refusait
donc le dépôt. Aucun test sur la seule décision ne pouvait le voir.
`charge_machine()` en ajoute pour la même raison : c'est de ce fichier que vient
désormais le nom du poste, et l'absence de ce fichier doit ne rien faire.
"""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True          # ne pas semer de __pycache__ dans le dépôt
SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))        # `scripts/` n'est pas un paquet

import maj_obsia                        # noqa: E402  (après l'aménagement du chemin)
from maj_obsia import (                 # noqa: E402
    A_JOUR,
    AILLEURS,
    ARBRE_SALE,
    AVANCER,
    DIVERGENT,
    decider,
    est_un_depot,
)

# Les tests n'ont pas le nom réel de la machine — ils le fournissent comme
# paramètre, comme le fait désormais `main()` via la configuration locale.
# C'est ainsi que le test reste générique et ne fuit aucun nom interne.
MACHINE_TEST = "poste-secondaire"


def interdit():
    """Sert de `est_ancetre` : l'appeler est un échec, pas une réponse."""
    raise AssertionError("est_ancetre ne devait pas être consulté ici")


def ancetre():
    """`origin/main` descend de `HEAD` : l'avancement rapide est possible."""
    return True


def pas_ancetre():
    """`origin/main` ne descend pas de `HEAD` : les histoires ont divergé."""
    return False


class TestDecider(unittest.TestCase):
    def test_machine_etrangere_ne_consulte_rien(self):
        """Ailleurs, aucune question de dépôt n'est posée : on sort tôt.

        C'est la garde qui protège les autres postes — un `git pull` sur la
        machine où l'on travaille serait au mieux inutile, au pire contraire
        à ce qu'on est en train d'y faire.
        """
        verdict, explication = decider(
            "un-autre-poste", False, "aaaa", "bbbb", interdit, MACHINE_TEST)

        self.assertEqual(verdict, AILLEURS)
        self.assertIn("un-autre-poste", explication)

    def test_machine_attendue(self):
        """Le nom configuré suffit ; rien d'autre n'est comparé."""
        verdict, _ = decider(
            MACHINE_TEST, False, "aaaa", "aaaa", interdit, MACHINE_TEST)

        self.assertEqual(verdict, A_JOUR)

    def test_arbre_sale_passe_avant_a_jour(self):
        """Sale **et** à jour reste une anomalie, et doit être signalée.

        L'ordre inverse — « à jour, donc rien à faire » — laisserait une
        modification locale dormir indéfiniment sans que personne l'apprenne.
        Un poste receveur ne doit jamais rien modifier.
        """
        verdict, _ = decider(
            MACHINE_TEST, True, "aaaa", "aaaa", interdit, MACHINE_TEST)

        self.assertEqual(verdict, ARBRE_SALE)

    def test_arbre_sale_passe_avant_l_avancement(self):
        """Même en retard, un arbre modifié interdit d'avancer."""
        verdict, _ = decider(
            MACHINE_TEST, True, "aaaa", "bbbb", interdit, MACHINE_TEST)

        self.assertEqual(verdict, ARBRE_SALE)

    def test_a_jour_n_interroge_pas_le_depot(self):
        """À jour, aucune question sur les ancêtres : rien à décider."""
        verdict, explication = decider(
            MACHINE_TEST, False, "a1b2c3d4ee", "a1b2c3d4ee", interdit,
            MACHINE_TEST)

        self.assertEqual(verdict, A_JOUR)
        self.assertIn("a1b2c3d4", explication)

    def test_en_retard_et_descendant_avance(self):
        """Le cas nominal : en retard, et l'avancement rapide est possible."""
        verdict, explication = decider(
            MACHINE_TEST, False, "a1b2c3d4ee", "9f8e7d6cbb", ancetre,
            MACHINE_TEST)

        self.assertEqual(verdict, AVANCER)
        self.assertIn("9f8e7d6c", explication)

    def test_histoires_divergentes_s_arretent(self):
        """Divergence : on s'arrête, et on le dit.

        Un `--ff-only` échouerait de toute façon ; nommer la divergence donne
        un journal lisible au lieu d'une erreur de git à déchiffrer. Il n'y a
        ni rebase ni `--force` dans ce script, et ce test est ce qui l'empêche
        d'y arriver un jour.
        """
        verdict, explication = decider(
            MACHINE_TEST, False, "a1b2c3d4ee", "9f8e7d6cbb", pas_ancetre,
            MACHINE_TEST)

        self.assertEqual(verdict, DIVERGENT)
        self.assertIn("rebase", explication)

    def test_ancetre_consulte_une_seule_fois(self):
        """Une question au dépôt, une seule, et seulement si elle sert."""
        appels = []

        def compte():
            appels.append(1)
            return True

        decider(MACHINE_TEST, False, "aaaa", "bbbb", compte, MACHINE_TEST)

        self.assertEqual(len(appels), 1)


class TestEstUnDepot(unittest.TestCase):
    """Ce que la garde doit accepter, et ce qu'elle doit refuser.

    Un clone présente `.git` comme répertoire ; un worktree lié le présente
    comme fichier. Les deux **sont** des dépôts, et le script doit tourner dans
    les deux : c'est ainsi que ce dépôt se travaille sans que deux séances se
    disputent le même arbre de travail.
    """

    def test_dossier_sans_depot_refuse(self):
        with tempfile.TemporaryDirectory() as dossier:
            self.assertFalse(est_un_depot(Path(dossier)))

    def test_clone_accepte(self):
        with tempfile.TemporaryDirectory() as dossier:
            (Path(dossier) / ".git").mkdir()
            self.assertTrue(est_un_depot(Path(dossier)))

    def test_worktree_lie_accepte(self):
        """Le défaut trouvé à l'exécution : `.git` est un fichier, ici."""
        with tempfile.TemporaryDirectory() as dossier:
            (Path(dossier) / ".git").write_text("gitdir: /ailleurs\n")
            self.assertTrue(est_un_depot(Path(dossier)))


class TestChargeMachine(unittest.TestCase):
    """Le nom du poste vient d'un fichier hors dépôt, et de nulle part ailleurs.

    C'est la contrepartie d'une fuite : le nom de la machine était écrit en dur
    dans le script, donc recopié dans un dépôt publié. Ces tests tiennent les
    deux bouts — plus aucun nom dans le code, et une configuration absente qui
    ne fait rien plutôt qu'une supposition.
    """

    def charge(self, contenu):
        """`charge_machine()` sur un fichier de configuration jetable."""
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "maj_obsia.conf"
            if contenu is not None:
                chemin.write_text(contenu, encoding="utf-8")
            with mock.patch.object(maj_obsia, "CONFIG", chemin):
                return maj_obsia.charge_machine()

    def test_sans_fichier_rien_ne_sort(self):
        """Pas de configuration : None, et l'appelant sort sans rien faire."""
        self.assertIsNone(self.charge(None))

    def test_la_cle_donne_le_poste(self):
        """La valeur de `machine_cible` est rendue telle quelle."""
        self.assertEqual(self.charge("machine_cible = poste-secondaire\n"),
                         "poste-secondaire")

    def test_commentaires_et_lignes_vides_ignores(self):
        """Le gabarit imprimé par `--config` se relit sans erreur."""
        contenu = "# un commentaire\n\nmachine_cible = poste-secondaire\n"
        self.assertEqual(self.charge(contenu), "poste-secondaire")

    def test_cle_absente_ou_vide_rend_none(self):
        """Clé absente, ou laissée vide : aucun nom, donc rien à faire."""
        self.assertIsNone(self.charge("# rien à configurer\n"))
        self.assertIsNone(self.charge("machine_cible =\n"))

    def test_le_gabarit_imprime_se_relit(self):
        """`--config` et `charge_machine()` parlent du même format."""
        self.assertIsNone(self.charge(maj_obsia.GABARIT_CONFIG))


if __name__ == "__main__":
    unittest.main()
