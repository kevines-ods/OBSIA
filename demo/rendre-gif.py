#!/usr/bin/env python3
"""Rend un fichier asciinema v2 (.cast) en GIF animé."""
import json
import sys

import pyte
from PIL import Image, ImageDraw, ImageFont

import os
POLICE = os.environ.get("POLICE", "/tmp/jetbrains-mono.ttf")
TAILLE = 15
LARGEUR_CELL, HAUTEUR_CELL = 9, 18
FPS = 12.5

PALETTE = {
    "black": "#45475a", "red": "#f38ba8", "green": "#a6e3a1", "yellow": "#f9e2af",
    "blue": "#89b4fa", "magenta": "#f5c2e7", "cyan": "#94e2d5", "white": "#bac2de",
    "brightblack": "#585b70", "brightred": "#eb7892", "brightgreen": "#94df8f",
    "brightyellow": "#eec87f", "brightblue": "#74a7f0", "brightmagenta": "#eab3dc",
    "brightcyan": "#86d7ca", "brightwhite": "#ffffff",
    "default": "#cdd6f4",
}
FOND = "#1e1e2e"


def couleur(v, defaut):
    if not v or v == "default":
        return defaut
    if v in PALETTE:
        return PALETTE[v]
    if len(v) == 6:
        return "#" + v
    return defaut


def principal():
    cast, sortie = sys.argv[1], sys.argv[2]
    lignes = open(cast).read().splitlines()
    entete = json.loads(lignes[0])
    cols, rows = entete["width"], entete["height"]
    evenements = [json.loads(l) for l in lignes[1:]]

    ecran = pyte.Screen(cols, rows)
    flux = pyte.ByteStream(ecran)

    police = ImageFont.truetype(POLICE, TAILLE)
    largeur, hauteur = cols * LARGEUR_CELL, rows * HAUTEUR_CELL
    pas = 1.0 / FPS

    images, durees = [], []
    tampon_prec = None
    t_image = 0.0
    t_derniere = 0.0

    def capture(t):
        nonlocal tampon_prec, t_image, t_derniere
        tampon = [[(ecran.buffer[y][x].data or " ",
                    ecran.buffer[y][x].fg,
                    ecran.buffer[y][x].bg,
                    ecran.buffer[y][x].bold,
                    ecran.buffer[y][x].reverse)
                   for x in range(cols)] for y in range(rows)]
        t_image = t
        if tampon == tampon_prec:
            return
        tampon_prec = tampon
        img = Image.new("RGB", (largeur, hauteur), FOND)
        dessin = ImageDraw.Draw(img)
        for y, ligne in enumerate(tampon):
            for x, (ch, fg, bg, gras, inverse) in enumerate(ligne):
                fond_cell = couleur(bg, FOND)
                if fond_cell != FOND:
                    dessin.rectangle(
                        [x * LARGEUR_CELL, y * HAUTEUR_CELL,
                         (x + 1) * LARGEUR_CELL, (y + 1) * HAUTEUR_CELL],
                        fill=fond_cell)
                if ch == " ":
                    continue
                if inverse:
                    dessin.rectangle(
                        [x * LARGEUR_CELL, y * HAUTEUR_CELL,
                         (x + 1) * LARGEUR_CELL, (y + 1) * HAUTEUR_CELL],
                        fill=couleur(fg, PALETTE["default"]))
                    couleur_txt = couleur(bg, FOND)
                else:
                    couleur_txt = couleur(fg, PALETTE["default"])
                    if gras and couleur_txt == PALETTE["default"]:
                        couleur_txt = "#ffffff"
                dessin.text(
                    (x * LARGEUR_CELL, y * HAUTEUR_CELL + 1), ch,
                    font=police, fill=couleur_txt)
        images.append(img)
        durees.append(max(t - t_derniere, pas))
        t_derniere = t

    for t, typ, data in evenements:
        if typ != "o":
            continue
        while t_image + pas <= t:
            capture(t_image + pas)
        flux.feed(data.encode("utf-8", "replace"))

    fin = (evenements[-1][0] + 2.0) if evenements else 2.0
    while t_image + pas <= fin:
        capture(t_image + pas)

    if images:
        durees[-1] = max(durees[-1], 2.0)
        images[0].save(
            sortie, save_all=True, append_images=images[1:],
            duration=[d * 1000 for d in durees], loop=0,
            optimize=True, disposal=2)
        print(f"GIF écrit : {sortie} — {len(images)} images, {sum(durees):.1f}s")


if __name__ == "__main__":
    principal()
