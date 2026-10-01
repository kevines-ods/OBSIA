#!/usr/bin/env python3
"""Rafraîchit le clone OBSIA depuis GitHub — un receveur, à sens unique.

Le coffre est versionné par git, mais `OBSIA/` est **exclu de Syncthing** (un
`.git` synchronisé se corrompt) : sur une machine autre que celle où l'on
travaille, le clone ne se rafraîchit donc que si quelque chose le rafraîchit.
C'est ce script, appelé par un minuteur systemd utilisateur.

Trois principes, dans cet ordre :

  · **Un seul sens.** GitHub → ici. Il ne pousse rien, ne rebase rien, ne
    force rien. La seule écriture sur le dépôt est un `merge --ff-only`.
  · **Il ne détruit jamais.** Arbre modifié : il s'arrête. Histoires
    divergentes : il s'arrête. Aucune commande destructive n'existe ici.
  · **Il ne fait rien quand il n'y a rien à faire.** À jour, il n'écrit pas
    un octet : pas de fichier réécrit, pas de commit vide, pas de réseau
    inutile (la machine se présente d'abord).

Il ne régénère rien, et c'est délibéré. Les index sont suivis par git — la CI
exige qu'ils soient à jour — donc ils arrivent avec le commit. Les sommaires de
`mémoire/` ne sont plus versionnés : le crochet `post-merge`, s'il est activé
sur le poste, les refait après le `merge --ff-only`.
`AGENTS.md`, lui, vit au-dessus du dépôt et arrive par Syncthing. Lancer
`installer.py` ici n'ajouterait rien et ferait un **second écrivain** sur un
fichier partagé entre les machines : exactement ce qu'il faut éviter.

Un seul poste est concerné, et son nom n'est pas dans ce dépôt : il vient de la
configuration locale d'installation (`~/.config/obsia/maj_obsia.conf`), lue à
l'exécution sur le modèle de la clé `commande_agent` (voir
`IA/skills/cron/scripts/appliquer_taches.py`). Ailleurs, la garde de `decider()`
renvoie « poste non concerné » et rien n'est lu ni contacté. Sans cette
configuration, le script sort dès le départ sans rien faire, comme sur un poste
inattendu : un dépôt publié ne nomme jamais l'infrastructure qu'il sert.
`--config` imprime le gabarit du fichier à poser sur le poste.

Codes de sortie — un minuteur qui échoue en silence ne sert à rien :

  0  rien à faire, ou mise à jour franchie et contrôles verts
  1  git n'a pas répondu, ou le chemin n'est pas un dépôt
  2  l'arbre de travail porte des modifications locales (anomalie)
  3  les histoires ont divergé : avancement rapide impossible
  4  contrôles rouges après la mise à jour
  5  le distant est resté injoignable après les essais
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

BRANCHE = "main"
RACINE = Path(__file__).resolve().parent.parent

ESSAIS_RESEAU = 3          # au démarrage, le réseau n'est pas toujours monté
ATTENTE_RESEAU = 20        # secondes entre deux essais
FUSEAU = "%Y-%m-%d %H:%M:%S"

CONFIG = Path(os.path.expanduser("~/.config/obsia/maj_obsia.conf"))

GABARIT_CONFIG = """\
# Configuration locale de maj_obsia.py — NON versionnée, à dessein : elle nomme
# une machine de l'infrastructure, ce que le dépôt ne fait jamais (§9).

# Nom du poste où cette tâche a un sens. Ailleurs — et sans ce fichier — le
# script sort sans rien faire.
machine_cible =
"""

# Verdicts de `decider()` — des chaînes, pour que le journal se lise.
AVANCER = "avancer"
A_JOUR = "a-jour"
ARBRE_SALE = "arbre-sale"
DIVERGENT = "divergent"
AILLEURS = "ailleurs"

# Codes de sortie, par verdict.
TOUT_VA_BIEN = 0
CODE_ECHEC = 1
CODE_ARBRE_SALE = 2
CODE_DIVERGENT = 3
CODE_CONTROLE_ROUGE = 4
CODE_RESEAU = 5

CODES = {
    AILLEURS: TOUT_VA_BIEN,
    A_JOUR: TOUT_VA_BIEN,
    AVANCER: TOUT_VA_BIEN,
    ARBRE_SALE: CODE_ARBRE_SALE,
    DIVERGENT: CODE_DIVERGENT,
}

PREFIXE = "[maj-obsia]"


def git(*arguments, racine=RACINE):
    """Lance git et rend (code, sortie) — sans jamais pouvoir réclamer une saisie.

    `GIT_TERMINAL_PROMPT=0` est ce qui empêche un dépôt privé mal identifié de
    faire patienter le minuteur indéfiniment : sans identifiants, git échoue
    tout de suite, et l'échec est lisible dans le journal.
    """
    environnement = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    acheve = subprocess.run(
        ["git", "-C", str(racine), *arguments],
        capture_output=True, text=True, env=environnement)
    sortie = acheve.stdout.strip() or acheve.stderr.strip()
    return acheve.returncode, sortie


def charge_machine():
    """Rend le nom du poste que cette tâche concerne, ou None.

    Le nom réel de la machine reste dans l'inventaire, sous
    `-PERSONNELS/Homelab/` : il n'a rien à faire dans un dépôt publié. Il est
    donc lu à l'exécution dans un fichier plat, hors dépôt, sur le modèle de la
    clé `commande_agent` (voir `IA/skills/cron/scripts/appliquer_taches.py`).
    Sans fichier, ou sans la clé `machine_cible`, on rend None — et l'appelant
    sort sans rien faire, comme sur un poste inattendu.
    """
    if not CONFIG.is_file():
        return None
    for ligne in CONFIG.read_text(encoding="utf-8").splitlines():
        nu = ligne.strip()
        if not nu or nu.startswith("#") or "=" not in nu:
            continue
        cle, _, valeur = nu.partition("=")
        if cle.strip() == "machine_cible":
            return valeur.strip() or None
    return None


def decider(machine, arbre_sale, local, distant, est_ancetre, attendue):
    """Le verdict et son explication, à partir des seuls faits.

    Rien n'est lancé ici : `est_ancetre` est une fonction, appelée seulement
    si elle sert. L'ordre des questions est le fond de la chose.

      1. **Le poste**, avant tout le reste. Ailleurs, aucune question de
         dépôt n'est posée : on ne lit pas même le dépôt.
      2. **L'arbre modifié**, avant « à jour ». Un arbre sale mais à jour
         sortirait autrement en silence, et l'anomalie — quelqu'un a écrit
         dans le clone d'un poste qui ne doit jamais écrire — ne serait jamais
         signalée.
      3. **À jour**, qui n'a besoin d'aucune information de dépôt.
      4. **La divergence**, avant l'avancement. Un `--ff-only` échouerait de
         toute façon ; le nommer donne un journal lisible au lieu d'une erreur
         de git à déchiffrer.
    """
    if machine != attendue:
        return AILLEURS, ("poste « %s » ≠ « %s » : poste non concerné"
                          % (machine, attendue))
    if arbre_sale:
        return ARBRE_SALE, ("l'arbre de travail porte des modifications "
                            "locales — un poste receveur ne doit jamais en avoir")
    if local == distant:
        return A_JOUR, "déjà au commit distant %s" % local[:8]
    if not est_ancetre():
        return DIVERGENT, ("« %s » ne descend pas de l'état local : avancement "
                           "rapide impossible, et il n'y aura pas de rebase"
                           % BRANCHE)
    return AVANCER, "en retard : avancement rapide possible vers %s" % distant[:8]


def rafraichir(racine):
    """`fetch` avec trois essais. Rend None si c'est passé, sinon le message."""
    message = ""
    for essai in range(1, ESSAIS_RESEAU + 1):
        code, sortie = git("fetch", "--prune", "origin", racine=racine)
        if code == 0:
            return None
        message = sortie
        if essai < ESSAIS_RESEAU:
            time.sleep(ATTENTE_RESEAU)
    return message


def controles(racine):
    """Rejoue les contrôles en lecture seule de la CI, dans cet ordre.

    Rouge, on s'arrête **sans revenir en arrière** : ce poste doit refléter
    GitHub, pas s'en écarter. Un retour arrière créerait une divergence, qui
    est précisément ce que ce script est fait d'éviter. Le journal dit ce qui
    a échoué ; c'est au serveur principal que la réparation se décide.

    Rend None si tout est vert, sinon (libellé, dernière ligne de la sortie).
    """
    environnement = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    for commande, libelle in (
            (["python3", "scripts/verifier_coffre.py"], "cohérence du coffre"),
            (["python3", "-m", "unittest", "discover", "-s", "tests"],
             "tests unitaires")):
        acheve = subprocess.run(commande, cwd=str(racine), capture_output=True,
                                text=True, env=environnement)
        if acheve.returncode != 0:
            lignes = (acheve.stderr.strip() or acheve.stdout.strip()).splitlines()
            return libelle, lignes[-1] if lignes else "échec sans message"
    return None


def analyser_arguments(argv):
    analyseur = argparse.ArgumentParser(
        description="Rafraîchit le clone OBSIA depuis GitHub, sur le poste "
                    "receveur.")
    analyseur.add_argument(
        "--verifier", action="store_true",
        help="montre le verdict sans toucher à l'arbre de travail. Le fetch, "
             "lui, a bien lieu : sans lui on ne peut pas savoir si le clone "
             "est en retard")
    analyseur.add_argument(
        "--forcer", action="store_true",
        help="passer outre la garde de poste — jamais la garde d'arbre sale")
    analyseur.add_argument(
        "--racine", type=Path, default=RACINE,
        help="le clone à rafraîchir (défaut : celui de ce script)")
    analyseur.add_argument(
        "--config", action="store_true",
        help="affiche le gabarit de la configuration locale à poser sur le "
             "poste, et sort. Le nom du poste ne se met jamais dans le dépôt")
    return analyseur.parse_args(argv)


def est_un_depot(racine):
    """Un clone, ou un worktree lié — les deux ne se présentent pas pareil.

    Dans un clone, `.git` est un répertoire. Dans un worktree lié — `git
    worktree add`, dont ce dépôt se sert pour travailler à plusieurs sans se
    disputer l'arbre de travail — `.git` est un **fichier** qui pointe vers le
    dépôt principal. Tester `is_dir()` refuse donc un worktree lié ; `.exists()`
    couvre les deux, et c'est ce qu'on veut savoir : y a-t-il un dépôt ici ?
    """
    return (racine / ".git").exists()


def main(argv=None):
    options = analyser_arguments(argv)
    racine = options.racine

    if options.config:
        print(GABARIT_CONFIG, end="")
        return TOUT_VA_BIEN

    if not est_un_depot(racine):
        print("%s %s n'est pas un dépôt git" % (PREFIXE, racine))
        return CODE_ECHEC

    machine = os.uname().nodename
    # Le nom du poste attendu vient de la configuration locale, hors dépôt :
    # il n'est jamais écrit ici (voir `charge_machine`). `--forcer` s'en passe
    # — c'est le seul moyen de lancer la tâche à la main sur un poste neuf,
    # avant que la configuration n'y soit posée.
    if options.forcer:
        attendue = machine
    else:
        attendue = charge_machine()
        if attendue is None:
            print("%s %s introuvable ou sans clé `machine_cible` : rien à faire "
                  "(poste non configuré — voir --config)"
                  % (PREFIXE, CONFIG))
            return TOUT_VA_BIEN

    concerne = machine == attendue

    # Ailleurs, on ne lit ni le dépôt ni le réseau : la garde de `decider()`
    # tranchera, et elle seule. Les faits restés vides ne sont jamais lus.
    arbre_sale = False
    local = distant = ""
    if concerne:
        code, sortie = git("status", "--porcelain", racine=racine)
        if code != 0:
            print("%s git status a échoué : %s" % (PREFIXE, sortie))
            return CODE_ECHEC
        arbre_sale = bool(sortie)

        if arbre_sale:
            print("%s arbre modifié :\n%s" % (PREFIXE, sortie))

        echec = rafraichir(racine)
        if echec is not None:
            print("%s distant injoignable après %d essais : %s"
                  % (PREFIXE, ESSAIS_RESEAU, echec))
            return CODE_RESEAU

        code, local = git("rev-parse", "HEAD", racine=racine)
        if code != 0:
            print("%s HEAD illisible : %s" % (PREFIXE, local))
            return CODE_ECHEC
        code, distant = git("rev-parse", "origin/%s" % BRANCHE, racine=racine)
        if code != 0:
            print("%s origin/%s illisible : %s" % (PREFIXE, BRANCHE, distant))
            return CODE_ECHEC

    def est_ancetre():
        code, _ = git("merge-base", "--is-ancestor", local, distant,
                      racine=racine)
        # Tout ce qui n'est pas un « oui » franc vaut « non » : mieux vaut
        # s'arrêter sur une erreur que d'avancer sur un doute.
        return code == 0

    verdict, explication = decider(machine, arbre_sale, local, distant,
                                   est_ancetre, attendue)
    print("%s %s — %s" % (PREFIXE, verdict, explication))

    if verdict != AVANCER:
        return CODES[verdict]

    if options.verifier:
        print("%s --verifier : rien n'a été écrit" % PREFIXE)
        return TOUT_VA_BIEN

    # Le commit distant, et non la référence : entre l'instant où elle a été
    # lue et celui-ci, un autre fetch aurait pu la déplacer.
    debut = time.time()
    code, sortie = git("merge", "--ff-only", distant, racine=racine)
    if code != 0:
        print("%s l'avancement rapide a échoué : %s" % (PREFIXE, sortie))
        return CODE_DIVERGENT

    _, arrivees = git("log", "--oneline", "--no-decorate",
                      "%s..%s" % (local, distant), racine=racine)
    lignes = arrivees.splitlines()
    print("%s %s → %s en %.1f s, %d commit(s) :"
          % (PREFIXE, local[:8], distant[:8], time.time() - debut, len(lignes)))
    for ligne in lignes[:10]:
        print("%s   %s" % (PREFIXE, ligne))

    rouge = controles(racine)
    if rouge is not None:
        libelle, message = rouge
        print("%s contrôle rouge — %s : %s" % (PREFIXE, libelle, message))
        return CODE_CONTROLE_ROUGE

    print("%s contrôles verts" % PREFIXE)
    return TOUT_VA_BIEN


if __name__ == "__main__":
    sys.exit(main())
