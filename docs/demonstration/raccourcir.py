#!/usr/bin/env python3
"""Accélère les attentes d'une prise : là où l'écran ne bouge plus.

    raccourcir.py PRISE.mp4 [SORTIE.mp4]

Rien n'est coupé. Chaque plage immobile de plus de SEUIL secondes garde son
début et sa fin à vitesse réelle ; son milieu est accéléré pour tenir en
MILIEU secondes. La dernière plage, celle où l'on lit la réponse, reste
intacte. Sans SORTIE, écrit PRISE-court.mp4 à côté.
"""
import re
import subprocess
import sys
from pathlib import Path

SEUIL = 8.0    # en dessous, une attente se laisse telle quelle
BORD = 1.5     # secondes gardées à vitesse réelle de chaque côté
MILIEU = 2.5   # durée du milieu une fois accéléré


def duree(video):
    sortie = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(video)],
        check=True, capture_output=True, text=True).stdout
    return float(sortie)


def plages_immobiles(video):
    journal = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(video),
         "-vf", "freezedetect=n=0.001:d=3", "-an", "-f", "null", "-"],
        check=True, capture_output=True, text=True).stderr
    debuts = [float(x) for x in re.findall(r"freeze_start: ([0-9.]+)", journal)]
    fins = [float(x) for x in re.findall(r"freeze_end: ([0-9.]+)", journal)]
    # Un début sans fin est la plage finale : zip l'écarte, et c'est voulu.
    return [(d, f) for d, f in zip(debuts, fins) if f - d >= SEUIL]


def main():
    if len(sys.argv) not in (2, 3):
        sys.exit(__doc__)
    prise = Path(sys.argv[1])
    sortie = Path(sys.argv[2]) if len(sys.argv) == 3 else \
        prise.with_name(prise.stem + "-court.mp4")
    total = duree(prise)

    # Découpe la vidéo en morceaux (début, fin, facteur d'accélération).
    morceaux, curseur = [], 0.0
    for debut, fin in plages_immobiles(prise):
        a, b = debut + BORD, fin - BORD
        morceaux.append((curseur, a, 1.0))
        morceaux.append((a, b, (b - a) / MILIEU))
        curseur = b
    morceaux.append((curseur, total, 1.0))
    if len(morceaux) == 1:
        print(f"Aucune attente de plus de {SEUIL:.0f} s : {prise.name} reste tel quel.")
        return

    filtres = []
    for i, (a, b, facteur) in enumerate(morceaux):
        filtres.append(
            f"[0:v]trim=start={a:.3f}:end={b:.3f},setpts=(PTS-STARTPTS)/{facteur:.4f}[v{i}]")
    entrees = "".join(f"[v{i}]" for i in range(len(morceaux)))
    filtres.append(f"{entrees}concat=n={len(morceaux)}:v=1:a=0[v]")
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(prise),
         "-filter_complex", ";".join(filtres), "-map", "[v]",
         "-r", "25", "-pix_fmt", "yuv420p", str(sortie)],
        check=True)
    print(f"{prise.name} : {total:.0f} s → {duree(sortie):.0f} s  ({sortie})")


if __name__ == "__main__":
    main()
