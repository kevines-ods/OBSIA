#!/usr/bin/env python3
"""Enregistre une session de terminal en fichier asciinema v2 (.cast).

Usage : enregistrer-demo.py <racine du coffre parent> <sortie.cast>

Lance sous PTY le script session-demo.sh (voisin de ce fichier), horodate
chaque octet sorti et écrit le cast.
"""
import fcntl
import json
import os
import pty
import select
import struct
import sys
import termios
import time

LARGEUR, HAUTEUR = 100, 32


def principal():
    coffre = os.path.abspath(sys.argv[1])
    sortie = sys.argv[2]
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "session-demo.sh")

    cast = open(sortie, "w", buffering=1)
    cast.write(json.dumps({"version": 2, "width": LARGEUR, "height": HAUTEUR}) + "\n")

    pid, fd = pty.fork()
    if pid == 0:
        os.environ["TERM"] = "xterm-256color"
        os.environ["COLUMNS"] = str(LARGEUR)
        os.environ["LINES"] = str(HAUTEUR)
        os.execvp("bash", ["bash", script, coffre])

    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", HAUTEUR, LARGEUR, 0, 0))

    debut = time.time()
    vivant = True
    while vivant:
        r, _, _ = select.select([fd], [], [], 0.05)
        if r:
            try:
                data = os.read(fd, 65536)
            except OSError:
                vivant = False
            if not data:
                vivant = False
            else:
                cast.write(json.dumps(
                    [round(time.time() - debut, 6), "o",
                     data.decode("utf-8", "replace")]) + "\n")
        else:
            p, _ = os.waitpid(pid, os.WNOHANG)
            if p == pid:
                vivant = False

    try:
        os.waitpid(pid, 0)
    except ChildProcessError:
        pass
    cast.close()
    print("cast écrit :", sortie)


if __name__ == "__main__":
    principal()
