"""Le banc de processus de la suite : compter ce que la suite lance, et refuser le dépassement.

Pourquoi un banc et pas un test : la mesure porte sur **toute** la suite, elle se
lance donc après elle, dans un processus qui l'exécute. Un test qui mesurerait la
suite ferait partie de la suite qu'il mesure.

    python3 scripts/banc_de_processus.py            # compte, compare, rend 0 ou 1
    python3 scripts/banc_de_processus.py --detail   # et dit ce qui dépasse

Ce qui est compté : les processus **enfants** créés par la suite, par les voies
qui existent ici — `subprocess.Popen` (donc `subprocess.run` et `check_output`)
et `os.system`. `os.posix_spawn` est compté **à part** : sur cette machine
`subprocess` s'en sert en interne, et l'additionner aux `Popen` compterait un
processus deux fois — la première mesure du banc l'a fait, et a annoncé un
dépassement de 211 processus qui n'existait pas. Un `posix_spawn` appelé sans
`Popen` reste visible dans le rapport, à côté du total.

Le plafond est dans `CONSTRAINTS.md` et ici, et un test tient les deux ensemble.
Il ne s'achète pas : on n'économise pas des processus en achetant du couplage
entre tests. Un test qui dépend de l'état laissé par un autre économise quelques
processus et coûte une panne qu'on mettra une heure à comprendre.

Limite de **profondeur**, et non erreur de mesure : le compteur vit dans ce
processus. Un test qui lance un script qui lance lui-même des processus n'est
compté qu'au premier étage — neuf scripts du dépôt lancent des processus. Le biais
est **constant** : la mesure de référence le partage, donc le plafond reste
cohérent avec la suite qu'il plafonne. La conséquence utile est ailleurs : un test
qui externalise du travail dans un sous-processus **échappe au budget**. Le budget
ne se contourne donc pas par là — il se contournerait **en trichant**, et c'est le
geste que le garde et la revue attrapent, pas le compteur.
"""
import argparse
import os
import subprocess
import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent

# Le 2026-10-17, dans un worktree neuf depuis 18ed66e : 5 183 processus enfants
# pour 1 098 tests. Le plafond est cette mesure plus 2 %, arrondie vers le haut :
# de la place pour une tranche normale, pas pour une dérive.
MESURE = 5_183
PLAFOND = 5_287


class Compteur:
    """Compte les processus enfants lancés par le processus courant.

    `installer()` remplace trois fonctions du module par des versions qui
    comptent puis appellent l'originale ; `desinstaller()` les remet en place.
    Une sous-classe de `Popen` plutôt qu'une fonction : `subprocess.run` et
    `check_output` passent par `subprocess.Popen`, ils sont donc comptés sans
    qu'on ait à les connaître.
    """

    def __init__(self):
        self.popen = 0
        self.system = 0
        self.posix_spawn = 0
        self._originaux = {}
        self._installe = False

    def installer(self):
        if self._installe:
            return self
        self._originaux["popen"] = subprocess.Popen
        self._originaux["system"] = os.system
        self._originaux["posix_spawn"] = getattr(os, "posix_spawn", None)
        compteur = self
        original = self._originaux["popen"]

        class Popen(original):  # noqa: N801 — le nom est celui qu'on remplace
            def __init__(suite, *args, **kwargs):
                compteur.popen += 1
                super().__init__(*args, **kwargs)

        def system(commande):
            compteur.system += 1
            return compteur._originaux["system"](commande)

        def posix_spawn(*args, **kwargs):
            compteur.posix_spawn += 1
            return compteur._originaux["posix_spawn"](*args, **kwargs)

        subprocess.Popen = Popen
        os.system = system
        if self._originaux["posix_spawn"] is not None:
            os.posix_spawn = posix_spawn
        self._installe = True
        return self

    def desinstaller(self):
        if not self._installe:
            return self
        subprocess.Popen = self._originaux["popen"]
        os.system = self._originaux["system"]
        if self._originaux["posix_spawn"] is not None:
            os.posix_spawn = self._originaux["posix_spawn"]
        self._installe = False
        return self

    def total(self):
        """Les processus comptés une fois.

        `os.posix_spawn` n'entre pas dans le total : sur cette machine,
        `subprocess` s'en sert **en interne**, si bien qu'un `Popen` y apparaît
        deux fois — une fois comme `Popen`, une fois comme `posix_spawn`. La
        mesure de référence est celle de `Popen` ; ajouter `posix_spawn`
        inventerait un dépassement de 211 processus qui n'existe pas. Il reste
        compté et affiché, parce qu'un `posix_spawn` appelé **sans** `Popen`
        serait, lui, un processus de plus.
        """
        return self.popen + self.system

    def rapport(self):
        return ("COMPTEUR_PROCESSUS total=%d popen=%d system=%d "
                "posix_spawn=%d (dont, déjà vus par popen)"
                % (self.total(), self.popen, self.system, self.posix_spawn))


def depasse(total, plafond):
    """Dépasser, c'est **strictement** plus que le plafond."""
    return total > plafond


def main(argv=None):
    a = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    a.add_argument("--detail", action="store_true",
                   help="dire combien de tests ont tourné et où le compte se forme")
    opts = a.parse_args(argv)

    compteur = Compteur().installer()
    try:
        # La suite n'a pas de paquet `tests` : elle s'importe par nom de module,
        # comme le fait `python3 -m unittest discover -b -s tests`.
        sys.path.insert(0, str(RACINE / "tests"))
        sys.path.insert(0, str(RACINE))
        suite = unittest.TestLoader().discover(str(RACINE / "tests"))
        resultat = unittest.TextTestRunner(verbosity=1).run(suite)
    finally:
        compteur.desinstaller()

    print()
    print(compteur.rapport())
    print("banc-de-processus : plafond %d, mesuré le 2026-10-17 : %d."
          % (PLAFOND, MESURE))

    if not resultat.wasSuccessful():
        print("banc-de-processus : la suite n'est pas verte, la mesure ne vaut rien.",
              file=sys.stderr)
        return 2
    if depasse(compteur.total(), PLAFOND):
        print("banc-de-processus : DÉPASSEMENT de %d processus."
              % (compteur.total() - PLAFOND), file=sys.stderr)
        if opts.detail:
            print("banc-de-processus : %d tests ont lancé ces processus — "
                  "chercher un test qui en lance beaucoup n'a pas de sens ; "
                  "chercher un test qui dépend de l'état d'un autre, si."
                  % resultat.testsRun, file=sys.stderr)
        return 1
    print("banc-de-processus : dans le budget (%d de marge)."
          % (PLAFOND - compteur.total()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
