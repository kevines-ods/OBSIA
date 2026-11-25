#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Le garde du registre des leçons : une PR qui touche un skill rend sa trace.

L'audit de la boucle d'auto-amélioration (novembre 2026) a montré la panne :
le registre `IA/system/impact-des-skills.md` vivait sur la bonne volonté — la
moitié des lignes qui s'y ajoutaient disaient « non rejoué » sans que rien ne
le demande, et une PR pouvait modifier un skill sans dire ce que la leçon
avait changé ni comment cela avait été vérifié. La colonne « Vérifié par »
restait du bruit, relue par personne.

Ce garde refuse, dans le *diff* d'une PR qui touche `IA/skills/` :

  * l'absence du registre : la PR ne modifie pas
    `IA/system/impact-des-skills.md` ;
  * la ligne de leçon sans « Vérifié par » rempli ;
  * un « non rejoué » **sans son pourquoi** — le garde ne rejette pas le
    constat lui-même : certaines règles ne se rejouent pas, le registre le dit
    lui-même (« il trace, il ne mesure pas »). Ce qu'il refuse, c'est l'aveu
    nu : un « non rejoué » doit continuer par la raison, le coût constaté,
    l'épreuve qui l'a remplacée ;
  * la tentative de vider une preuve **ancienne** — le garde compare lignes
    retirées et lignes ajoutées : une ligne de leçon qui disparaît sans
    remplaçante, ou dont la remplaçante a la colonne « Vérifié par » vide,
    refuse la PR (trou relevé en relecture adverse, novembre 2026) ;
  * la ligne **non conforme** — un pipe non échappé dans une cellule décale
    toute la découpe ; le garde le dit au lieu de lire une cellule au hasard.

Ce qu'il ne juge pas : la *qualité* de la preuve ni la justesse de la leçon —
demi-verrou assumé, comme ceux du plancher. La relecture humaine reste la voie
de secours.

Conventions de sortie : 0 = rien à réclamer, 1 = constat (refus), 2 = n'a pas
pu tourner (git indisponible, base absente) — un 2 ne se lit jamais comme un 0.
"""

import argparse
import re
import subprocess
import sys

REGISTRE = "IA/system/impact-des-skills.md"

# La ligne de leçon commence par sa date : `| 2026-09-13 | `leçon` | …`.
MOTIF_LIGNE_DE_LECON = re.compile(r"^\|\s*20\d\d-")

# Sept colonnes : Date, Leçon, Skill touché, Ce qui a changé, Vérifié par,
# Statut, Revue. Découpée sur `|` — une ligne saine donne 9 morceaux (les
# deux bords vides compris) et « Vérifié par » est le cinquième.
CELLULE_VERIFIE_PAR = 5
NOMBRE_DE_MORCEAUX = 9

# Un pipe échappé (`\|`) sépare deux cellules pour un lecteur, pas pour
# markdown : il sort de la découpe avant le split, sinon toute ligne qui le
# porte — et le registre en porte, dans ses liens `[[…\|…]]` — glisse d'une
# colonne.
PIPE_ECHAPPE = chr(92) + "|"


def _git(depot, *args):
    """Un appel git qui échoue en sortie 2, jamais en trace Python."""
    process = subprocess.run(
        ["git", "-C", depot, *args],
        capture_output=True,
        text=True,
    )
    if process.returncode != 0:
        sys.stderr.write(process.stderr)
        sys.exit(2)
    return process.stdout


def fichiers_touches(depot, plage):
    """Les chemins du diff, sans préfixe de statut."""
    sortie = _git(depot, "diff", "--name-only", plage)
    return [ligne.strip() for ligne in sortie.splitlines() if ligne.strip()]


def cellule(ligne_de_lecon, index):
    """La cellule n d'une ligne de leçon, ou None si la découpe est faussée.

    Une cellule qui porte un pipe **non échappé** décale toute la ligne :
    plutôt que de lire une cellule au hasard, on rend None — la ligne est
    non conforme, le garde le dira au lieu de valider un glissement.
    """
    morceaux = ligne_de_lecon.replace(PIPE_ECHAPPE, "\x00").split("|")
    morceaux = [m.replace("\x00", "|") for m in morceaux]
    if len(morceaux) != NOMBRE_DE_MORCEAUX:
        return None
    return morceaux[index].strip()


def lignes_de_lecon(depot, plage):
    """(les lignes ajoutées, les lignes retirées) par le diff du registre."""
    sortie = _git(depot, "diff", "--unified=0", plage, "--", REGISTRE)
    ajoutees, retirees = [], []
    for ligne in sortie.splitlines():
        for prefix, tas in (("+", ajoutees), ("-", retirees)):
            if ligne.startswith(prefix) and not ligne.startswith(prefix * 3):
                corps = ligne[1:]
                if MOTIF_LIGNE_DE_LECON.match(corps):
                    tas.append(corps)
    return ajoutees, retirees


def verdict_de_la_cellule_verifie_par(ligne):
    """(True, "") quand la cellule passe ; (False, raison) quand elle manque.

    La ligne est une ligne de leçon déjà dépouillée de son `+` ou de son `-`.
    """
    verifie = cellule(ligne, CELLULE_VERIFIE_PAR)
    if verifie is None:
        return False, (
            "ligne de leçon non conforme : le nombre de colonnes ne "
            "correspond pas (pipe non échappé dans une cellule ?)"
        )
    if not verifie:
        return False, "colonne « Vérifié par » vide"
    if verifie.replace("`", "").strip().startswith("non rejoué"):
        reste = verifie.replace("`", "").strip()
        suite = reste[len("non rejoué"):].strip().strip("—").strip()
        if not suite:
            return False, ("« non rejoué » sans son pourquoi : "
                           "la raison, le coût constaté ou l'épreuve suit le tiret")
    return True, ""


def main():
    parseur = argparse.ArgumentParser(
        description="Refuse une PR qui touche un skill sans trace au registre."
    )
    parseur.add_argument("--depot", default=".", help="racine du dépôt git")
    parseur.add_argument(
        "--base",
        required=True,
        help="référence de base du diff, p. ex. origin/main",
    )
    arguments = parseur.parse_args()

    plage = f"{arguments.base}...HEAD"

    touches = fichiers_touches(arguments.depot, plage)
    if not any(chemin.startswith("IA/skills/") for chemin in touches):
        print("Aucun skill touché : sans objet.")
        return 0

    if REGISTRE not in touches:
        print(
            f"Cette PR modifie IA/skills/ sans toucher {REGISTRE}.\n"
            "Toute modification de skill se trace : ajoutez la ligne de la leçon."
        )
        return 1

    ajoutees, retirees = lignes_de_lecon(arguments.depot, plage)
    refus = []

    # Toute ligne retirée doit revenir : une ligne ancienne vidée de sa
    # preuve, ou disparue sans remplacement, échappe au regard si le garde
    # ne lit que les ajouts — exactement la panne que la colonne doit fermer.
    par_lecon = {}
    for ligne in ajoutees:
        lecon = cellule(ligne, 2) or ligne
        par_lecon.setdefault(lecon, []).append(ligne)
    for ligne in retirees:
        lecon = cellule(ligne, 2) or ligne
        if not par_lecon.get(lecon):
            refus.append(
                f"ligne de leçon retirée sans remplacement : « {lecon} » — "
                "une ligne ne se supprime jamais"
            )
    for ligne in ajoutees:
        valide, raison = verdict_de_la_cellule_verifie_par(ligne)
        if not valide:
            refus.append(raison)
    if not ajoutees and retirees:
        for ligne in retirees:
            valide, raison = verdict_de_la_cellule_verifie_par(ligne)
            if not valide:
                refus.append(raison)
    if not ajoutees and not retirees:
        refus.append(
            f"le diff ajoute {REGISTRE} sans y ajouter une seule ligne de leçon "
            "(ligne datée du tableau)"
        )
    if refus:
        for raison in refus:
            print(raison)
        return 1

    print(
        f"{len(ajoutees)} lignes de leçon ajoutées au registre, "
        f"{len(retirees)} remplacées, « Vérifié par » rempli."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
