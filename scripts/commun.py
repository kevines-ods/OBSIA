"""Fonctions partagées entre l'installeur, la publication et le vérificateur.

`verifier_coffre.py` en a besoin sans dépendre d'`installer.py` ni de
`publier.py` : une modification de l'un ne doit pas casser l'autre. Ce module
n'importe que `modules`, jamais un des trois scripts.
"""

import os
import subprocess
from pathlib import Path

import modules as MOD


def _git_sortie(racine: Path, *args: str) -> str:
    res = subprocess.run(["git", *args], cwd=str(racine),
                         capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError((res.stderr or res.stdout).strip())
    return res.stdout


#: Les débuts de marqueur qu'on reconnaît comme nôtres. Le premier est le libellé
#: courant ; un fichier posé par une version antérieure porte le même début suivi
#: d'une autre fin, et reste donc à nous. Changer de marqueur un jour, c'est
#: ajouter ici le nouveau libellé, puis l'écrire ci-dessous : les installations
#: déjà faites ne se retrouvent pas orphelines pour autant.
MARQUEURS_AGENTS = (
    "<!-- généré par OBSIA/scripts/installer.py",
)

#: La ligne réellement écrite en tête du fichier. Sans elle, le fichier est celui
#: de quelqu'un d'autre : on n'y touche pas, même sous --appliquer.
MARQUEUR_AGENTS = ("%s — ne pas éditer, relancer installer.py --appliquer -->"
                   % MARQUEURS_AGENTS[0])


def contenu_agents(prompt: str) -> str:
    """Le texte exact d'AGENTS.md : le marqueur, une ligne vide, le prompt.

    Nommé et réutilisé plutôt que recomposé ailleurs : c'est **ce texte-là** que
    le harness lit, et `verifier_coffre.py` doit en mesurer les octets, marqueur
    compris. Mesurer le prompt seul laisserait passer un fichier déjà au-delà du
    plafond de Codex.
    """
    return "%s\n\n%s\n" % (MARQUEUR_AGENTS, prompt)


def est_un_coffre_parent(chemin: Path) -> bool:
    """Vrai si `chemin` porte un marqueur de coffre (§7.1) — `.obsidian/`,
    `_MAINTENANCE/`, une zone `0-…` ou son ancien nom `-…`.

    La mémoire s'installe là, et nulle part ailleurs : un clone de
    développement n'a pas de coffre parent autour de lui, et l'installeur ne
    doit pas y faire naître un dépôt git.
    """
    try:
        noms = set(os.listdir(chemin))
    except OSError:
        return False
    return bool(noms & set(MOD.MARQUEURS_COFFRE))


def depot_reel(source: Path) -> Path:
    """Le clone principal du dépôt, même quand on lance depuis un worktree.

    Les motifs de machine nomment le coffre **de cette machine** : c'est le clone
    principal qu'il faut lire, pas le dossier d'où l'on parle. Un worktree vit
    ailleurs — `~/obsia-worktrees/<nom-agent>-<sujet>` — et son dossier parent
    n'est pas le coffre : c'est un hangar à worktrees, dont le nom se lit dans la
    documentation du dépôt. Prendre ce parent pour le coffre ferait signaler
    cette documentation à chaque aperçu lancé depuis un worktree, et la
    publication y resterait bloquée — un chemin de machine ne se force pas.
    """
    commun = Path(_git_sortie(source, "rev-parse", "--git-common-dir").strip())
    if not commun.is_absolute():
        commun = source / commun
    return commun.resolve().parent
