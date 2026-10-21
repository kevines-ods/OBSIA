#!/usr/bin/env python3
"""Robustesse à la date — la suite entière, tournée à six dates déclarées.

Une suite verte répond à une question **datée** : « le code est-il juste *ce
jour-là* ? ». Une date future peut la faire rougir sans qu'une ligne de produit
ait bougé ; c'est ce qui est arrivé à la tolérance de bascule, mesurée rouge le
2027-01-01 alors que la branche était verte le 2026-10-17. Ce contrôle pose la
question six fois, à six dates fixes, chaque semaine.

Comment, et pourquoi ainsi :

- **une exécution isolée par date** : le mode par défaut lance ce même script en
  sous-processus, un par date (`--une-date`). Aucun état d'une date ne fuit vers
  la suivante — ni une variable de module réécrite par un test, ni un cache.
- **le jour forcé vit ici, jamais dans le produit** : le sous-processus remplace
  `verifier_coffre.date` par un substitut qui répond toujours le jour déclaré.
  `verifier_coffre.py` n'a donc aucune variable d'environnement à lire, et
  aucune porte par laquelle on pourrait lui cacher la vraie date en production.
- **les dates sont déclarées une seule fois**, dans `DATES`, et répétées en tête
  de sortie : le journal dit quelles dates ont été interrogées sans qu'il faille
  ouvrir ce fichier.

Ce qu'il ne vérifie pas, et qu'il faut savoir :

1. Il ne juge pas **quelles** dates méritent d'être déclarées : la liste est un
   choix humain, écrit une fois, et rien ici ne dit qu'elle couvre les bords du
   code. Un nouveau bord connu s'y ajoute à la main.
2. Il ne force que `date.today()`, et dans **un seul** module, `verifier_coffre`.
   La limite est mesurée, pas garantie : `grep -rn "date.today()" scripts/` donne
   deux occurrences (l.310 et l.1595), toutes deux dans ce module. Une horloge
   lue autrement passe au travers, `datetime.now()` en premier : la décision
   « la dernière poussée est trop vieille » de `scripts/depot_de_donnees.py`
   (l.574-576) n'est donc pas forcée ici, et le seul emploi de `datetime.now()`
   de `scripts/constat_acte.py` (l.500) horodate un acte — un faux jour y
   changerait un champ, pas une décision. Couvrir ces modules demanderait un
   second substitut, et une liste de modules à tenir à jour.
3. Six dates fixes ne disent rien d'une **dérive lente** : fuseaux, changement
   d'heure, passage d'année en cours d'exécution ne sont pas couverts.
4. Vert ici ne dit pas que la suite est juste : ça dit qu'elle répond la même
   chose à six dates. Un test faux à toutes les dates reste vert.

Usage :
    python3 scripts/verifier_dates.py
    python3 scripts/verifier_dates.py --une-date 2027-01-01

Sortie : une ligne par date (`AAAA-MM-JJ : Ran N tests, OK|ECHEC`), la sortie
complète de chaque exécution fautive, puis un verdict. Le verdict tombe après
les six dates, jamais à la première rouge : un passage doit dire si c'est une
date ou plusieurs. En mode parent, code retour 0 si toutes les dates sont
vertes, 1 si au moins une rougit — y compris quand une date n'a trouvé aucun
test. Le code 2 n'existe qu'en mode `--une-date` : date refusée, ou exécution
qui n'a trouvé aucun test.
"""

import argparse
import re
import subprocess
import sys
import unittest
from datetime import date
from pathlib import Path

sys.dont_write_bytecode = True          # ne pas semer de __pycache__ dans le dépôt

RACINE = Path(__file__).resolve().parent.parent
SCRIPTS = RACINE / "scripts"            # `scripts/` n'est pas un paquet
TESTS = RACINE / "tests"

# Les dates interrogées, déclarées ici et nulle part ailleurs.
DATES = (
    "2026-12-31",   # le dernier jour de la tolérance de bascule : elle avertit
    "2027-01-01",   # le premier jour d'après : la bascule est échue, elle refuse
    "2027-06-01",   # un jour ordinaire, loin de tout bord
    "2028-02-29",   # une année bissextile, au jour qui n'existe pas les autres
    "2028-06-01",
    "2030-01-01",   # une date lointaine, deux ans après la bascule
)

# AAAA-MM-JJ, et rien d'autre : `date.fromisoformat` accepterait aussi
# `20270101`, forme qu'un humain ne lit pas dans un journal.
FORMAT = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def date_valide(texte) -> bool:
    """Vrai pour une date ISO `AAAA-MM-JJ` qui existe au calendrier."""
    if not isinstance(texte, str) or not FORMAT.match(texte):
        return False
    try:
        date.fromisoformat(texte)
    except ValueError:                  # `2028-02-30`, `2026-13-01`
        return False
    return True


def faux_jour(jour: date):
    """Un substitut de `datetime.date` qui répond toujours `jour` à `today()`.

    `verifier_coffre` n'emploie que deux formes de `date` : `today()` et
    `fromisoformat()`. Le substitut les porte exactement, et rien d'autre : une
    troisième forme ajoutée un jour au produit échouera bruyamment
    (`AttributeError`) plutôt que de lire silencieusement la vraie date. Un
    contrôle qui se tait est pire qu'un contrôle qui casse.
    """
    class JourForce:
        @staticmethod
        def today():
            return jour

        @staticmethod
        def fromisoformat(texte):
            return date.fromisoformat(texte)

    return JourForce


def lire_sortie(texte: str):
    """(nombre de tests, « OK » ou « ECHEC ») lus dans la sortie d'une exécution.

    Aucun nombre trouvé, ou aucun verdict lisible, se lit « ECHEC » : un
    contrôle muet ne vaut pas un contrôle vert.
    """
    nombres = re.findall(r"^Ran (\d+) tests? in ", texte, re.MULTILINE)
    verdict = "OK" if re.search(r"^OK\b", texte, re.MULTILINE) else "ECHEC"
    return (int(nombres[-1]) if nombres else None), verdict


def executer_a_une_date(texte_date: str) -> int:
    """Mode enfant : force le jour, puis exécute la suite dans ce processus.

    Le jour forcé est posé **ici**, après l'import du produit : aucune ligne de
    `verifier_coffre.py` ne sait qu'on peut lui mentir, et rien dans son
    environnement ne le lui dit.
    """
    sys.path.insert(0, str(SCRIPTS))
    import verifier_coffre             # noqa: E402  (import tardif : voir ci-dessus)

    verifier_coffre.date = faux_jour(date.fromisoformat(texte_date))
    suite = unittest.TestLoader().discover(start_dir=str(TESTS), pattern="test_*.py")
    resultat = unittest.TextTestRunner(verbosity=1, stream=sys.stderr).run(suite)
    if resultat.testsRun == 0:
        # Sous 3.11 — la version que le workflow épingle — zéro test exécuté rend
        # « Ran 0 tests, OK » et le code 0 : un vert qui ne prouve rien. Si
        # `tests/` disparaît ou si le motif de découverte ne trouve plus rien, le
        # contrôle hebdomadaire passerait au vert sans avoir interrogé une ligne.
        print("ECHEC — 0 test exécuté : la découverte n'a rien trouvé dans %s"
              % TESTS, file=sys.stderr)
        return 2
    return 0 if resultat.wasSuccessful() else 1


def executer_toutes_dates() -> int:
    """Mode parent : une exécution isolée par date déclarée, puis le verdict."""
    print("Dates déclarées (%d) : %s" % (len(DATES), ", ".join(DATES)))
    rouges = []
    for texte in DATES:
        commande = [sys.executable, str(Path(__file__).resolve()),
                    "--une-date", texte]
        fini = subprocess.run(commande, cwd=str(RACINE),
                              capture_output=True, text=True)
        sortie = (fini.stdout or "") + (fini.stderr or "")
        nombre, verdict = lire_sortie(sortie)
        if fini.returncode != 0:
            verdict = "ECHEC"
        print("%s : Ran %s tests, %s"
              % (texte, nombre if nombre is not None else "?", verdict))
        if verdict != "OK":
            rouges.append(texte)
            # La sortie est recopiée telle quelle, sans réindentation : ce sont
            # les noms des tests fautifs qui disent où le produit a glissé.
            print("--- sortie de %s ---" % texte)
            print(sortie.rstrip("\n"))
            print("--- fin de la sortie de %s ---" % texte)
    if rouges:
        print("VERDICT : ECHEC — %d date(s) rouge(s) sur %d : %s"
              % (len(rouges), len(DATES), ", ".join(rouges)))
        return 1
    print("VERDICT : OK — %d dates vertes sur %d" % (len(DATES), len(DATES)))
    return 0


def main(argv=None) -> int:
    analyseur = argparse.ArgumentParser(
        description="La suite entière, tournée à chaque date déclarée.")
    analyseur.add_argument(
        "--une-date", metavar="AAAA-MM-JJ",
        help="exécute la suite dans ce processus, le jour forcé à cette date")
    arguments = analyseur.parse_args(argv)

    if arguments.une_date is None:
        return executer_toutes_dates()
    if not date_valide(arguments.une_date):
        print("date refusée : « %s » — attendu AAAA-MM-JJ, une date du calendrier"
              % arguments.une_date, file=sys.stderr)
        return 2
    return executer_a_une_date(arguments.une_date)


if __name__ == "__main__":
    sys.exit(main())
