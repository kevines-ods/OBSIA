#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Le dépôt de données du coffre parent (§7.1) — ce que ses crochets appellent.

La mémoire vit hors du dépôt produit, dans un dépôt git à part, à la racine du
coffre parent. Ce script est ce que ses crochets déclenchent. Il ne lit ni
n'écrit rien d'autre que ce dépôt-là et l'état de poussée qui vit dans son
`.git/` (hors version, et donc hors synchronisation).

    python3 scripts/depot_de_donnees.py avant-commit --coffre <coffre> [--produit <dépôt produit>]
    python3 scripts/depot_de_donnees.py apres-commit --coffre <coffre>
    python3 scripts/depot_de_donnees.py fraicheur    --coffre <coffre> [--heures 48]

`avant-commit` refuse, dans l'ordre : un commit venu d'une autre machine que
l'écrivain déclaré (« un seul écrivain », §7.1) ; une valeur à forme de secret
que le commit ajoute à la mémoire (`garde_secrets.py`, §7.1) ; puis il contrôle
la mémoire du coffre avec `verifier_coffre.py --coffre <coffre> --carnets`.

`apres-commit` pousse vers `origin` et note l'instant du succès dans
`<coffre>/.git/obsia-derniere-poussee`. Un échec est journalisé, jamais
bloquant : le commit a déjà eu lieu.

`fraicheur` dit si la dernière poussée réussie a moins du seuil d'heures (48 h
par défaut) — c'est la sonde qu'un moniteur push peut brancher.
"""

from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import garde_secrets as GS  # noqa: E402
import modules as MOD  # noqa: E402

RACINE_DEFAUT = Path(__file__).resolve().parent.parent
NOM_DISTANT = "origin"
HEURES_FRAICHEUR = 48
FICHIER_DERNIERE_POUSSEE = "obsia-derniere-poussee"
FICHIER_JOURNAL = "obsia-poussee.log"


# ------------------------------------------------------------------- lecture

def _git(coffre: Path, *arguments: str, delai: int | None = None) -> subprocess.CompletedProcess:
    """Lance git dans le coffre. Ne lève jamais : rend le résultat, code inclus."""
    return subprocess.run(
        ["git", "-C", str(coffre), *arguments],
        capture_output=True, text=True, timeout=delai,
    )


def dossier_git(coffre: Path) -> Path | None:
    """Le `.git` du coffre, ou None si le coffre n'est pas un dépôt git."""
    resultat = _git(coffre, "rev-parse", "--git-dir")
    if resultat.returncode != 0:
        return None
    chemin = Path(resultat.stdout.strip())
    return chemin if chemin.is_absolute() else coffre / chemin


def nom_du_distant(coffre: Path) -> str | None:
    """L'URL du distant `origin`, ou None s'il n'est pas configuré."""
    resultat = _git(coffre, "remote", "get-url", NOM_DISTANT)
    if resultat.returncode != 0:
        return None
    return resultat.stdout.strip() or None


def branche_courante(coffre: Path) -> str:
    resultat = _git(coffre, "rev-parse", "--abbrev-ref", "HEAD")
    return resultat.stdout.strip() if resultat.returncode == 0 else "HEAD"


def lire_profil(produit: Path) -> dict:
    """`obsia.local.yml`, ou {} s'il est absent ou illisible.

    Il n'est pas versionné et décrit cette machine-ci : on ne s'en étonne pas.
    """
    chemin = produit / MOD.NOM_PROFIL
    if not chemin.is_file():
        return {}
    try:
        return MOD.lire_yaml_simple(chemin.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return {}


# ---------------------------------------------------------------- avant-commit

def verifier_ecrivain(produit: Path) -> int:
    """Refuse un commit qui ne vient pas de la machine écrivain (§7.1).

    L'écrivain est déclaré dans `obsia.local.yml`, écrit par l'installeur sur la
    machine concernée : aucun nom d'hôte n'entre dans un fichier versionné.
    """
    ecrivain = lire_profil(produit).get("ecrivain")
    if not ecrivain:
        print("  ! obsia.local.yml ne déclare pas d'écrivain : la règle « un seul "
              "écrivain » n'est pas vérifiable ici (§7.1).", file=sys.stderr)
        return 0
    ici = MOD.nom_machine()
    if ici and ici != ecrivain:
        print("Refus : le dépôt de données du coffre a pour écrivain « %s », et "
              "cette machine est « %s ».\nLa mémoire s'écrit depuis une seule "
              "machine (§7.1). Pour la poursuivre ailleurs, relancer l'installeur "
              "sur cette autre machine et lui passer la main." % (ecrivain, ici),
              file=sys.stderr)
        return 1
    return 0


def verifier_memoire(coffre: Path, produit: Path) -> int:
    """Contrôle les carnets du coffre (§6) avec le vérificateur du produit."""
    verificateur = produit / "scripts" / "verifier_coffre.py"
    if not verificateur.is_file():
        print("  ! %s introuvable : la mémoire du coffre n'a pas été contrôlée."
              % verificateur, file=sys.stderr)
        return 0
    resultat = subprocess.run(
        [sys.executable, str(verificateur), "--coffre", str(coffre), "--carnets"],
        cwd=str(produit),
    )
    return resultat.returncode


def avant_commit(coffre: Path, produit: Path) -> int:
    code = verifier_ecrivain(produit)
    if code != 0:
        return code
    # Le secret avant les carnets : on refuse d'écrire la fuite, pas seulement
    # d'en signaler le voisinage. La raison du refus s'imprime dans le garde.
    code = GS.verifier(coffre)
    if code != 0:
        return code
    return verifier_memoire(coffre, produit)


# ---------------------------------------------------------------- apres-commit

def apres_commit(coffre: Path) -> int:
    """Pousse vers `origin`, note le succès, journalise l'échec. Jamais bloquant."""
    if nom_du_distant(coffre) is None:
        return 0
    branche = branche_courante(coffre)
    try:
        resultat = _git(coffre, "push", NOM_DISTANT, branche, delai=120)
    except subprocess.TimeoutExpired:
        resultat = None
    git = dossier_git(coffre)
    maintenant = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

    if resultat is not None and resultat.returncode == 0:
        if git is not None:
            (git / FICHIER_DERNIERE_POUSSEE).write_text(maintenant, encoding="utf-8")
        return 0

    detail = "délai dépassé" if resultat is None else \
        (resultat.stderr or resultat.stdout or "").strip().replace("\n", " ")
    if git is not None:
        try:
            with (git / FICHIER_JOURNAL).open("a", encoding="utf-8") as journal:
                journal.write("%s  %s  %s\n" % (maintenant, branche, detail))
        except OSError:
            pass
    print("  ! poussée vers %s échouée (journalisé sous .git/%s) : %s"
          % (NOM_DISTANT, FICHIER_JOURNAL, detail), file=sys.stderr)
    return 1


# ------------------------------------------------------------------ fraicheur

def fraicheur(coffre: Path, heures: int = HEURES_FRAICHEUR) -> int:
    """Dit si la dernière poussée réussie a moins de `heures`."""
    if nom_du_distant(coffre) is None:
        print("Aucun distant configuré pour le dépôt de données du coffre : "
              "rien à surveiller (§7.1).")
        return 0
    git = dossier_git(coffre)
    if git is None:
        print("Le coffre n'est pas un dépôt git : aucune poussée à vérifier.",
              file=sys.stderr)
        return 1
    marque = git / FICHIER_DERNIERE_POUSSEE
    if not marque.is_file():
        print("Aucune poussée réussie connue : le dépôt de données du coffre n'a "
              "jamais atteint son distant.", file=sys.stderr)
        return 1
    try:
        quand = dt.datetime.fromisoformat(marque.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        print("Marque de poussée illisible : %s" % marque, file=sys.stderr)
        return 1
    if quand.tzinfo is None:
        quand = quand.replace(tzinfo=dt.timezone.utc)
    age = dt.datetime.now(dt.timezone.utc) - quand
    ecoule = int(age.total_seconds() // 3600)
    if age > dt.timedelta(hours=heures):
        print("Dernière poussée réussie il y a %d h (seuil %d h) : la mémoire du "
              "coffre n'atteint plus son distant." % (ecoule, heures),
              file=sys.stderr)
        return 1
    print("Dernière poussée réussie il y a %d h (seuil %d h) : à jour."
          % (ecoule, heures))
    return 0


# ---------------------------------------------------------------------- main

def main(argv=None) -> int:
    analyseur = argparse.ArgumentParser(
        description="Le dépôt de données du coffre parent (§7.1).")
    analyseur.add_argument("commande",
                           choices=["avant-commit", "apres-commit", "fraicheur"])
    analyseur.add_argument("--coffre", type=Path, default=Path.cwd(),
                           help="racine du coffre parent, où vit le dépôt de données")
    analyseur.add_argument("--produit", type=Path, default=RACINE_DEFAUT,
                           help="racine du dépôt produit (pour lire obsia.local.yml)")
    analyseur.add_argument("--heures", type=int, default=HEURES_FRAICHEUR,
                           help="seuil de fraîcheur, en heures (défaut : 48)")
    args = analyseur.parse_args(argv)

    coffre = Path(args.coffre).resolve()
    if args.commande == "avant-commit":
        return avant_commit(coffre, Path(args.produit).resolve())
    if args.commande == "apres-commit":
        return apres_commit(coffre)
    return fraicheur(coffre, args.heures)


if __name__ == "__main__":
    sys.exit(main())
