#!/usr/bin/env python3
"""Retire les worktrees d'agent dont le travail est fusionné — et rien d'autre.

Un worktree ne sert qu'à son chantier, de l'ouverture à la fusion de sa pull
request (`IA/system/travail-en-parallele.md`). Une fois fusionné, il n'est plus
un travail : il encombre `git worktree list`, qui sert justement à savoir qui
travaille sur quoi. Le 2026-11-22, deux dépôts en portaient 60, dont 55 fusionnés
et oubliés : la règle « on retire le sien à la fin » ne suffit pas.

Ce script fait le geste pour **tous** les agents. Un worktree ne part que si
**tout** ceci est vrai :

  · sa branche est celle d'un agent (`<nom-agent>/<sujet>`, `<nom-agent>` ayant
    sa fiche dans `IA/agents/`) — ni une tête détachée (publication, rebase ou
    bisect en cours), ni la branche de quelqu'un d'autre ;
  · elle porte **un travail à elle** : son reflog contient au moins un commit
    (ou un `cherry-pick`, un `revert`).
    Un worktree neuf, ouvert sur `origin/main` et encore vide, descend lui aussi
    de la branche par défaut — sans ce critère, il passerait pour fusionné ;
  · elle **descend de la branche par défaut distante** : le travail y est ;
  · il est **propre** : aucune modification, aucun fichier non suivi, aucun
    fichier ignoré hors des caches qui se refont (`__pycache__`) — `git worktree
    remove` emporterait un `.env` ou un venv ignorés ;
  · il **n'est pas verrouillé**, et rien n'y a bougé depuis une heure.

Sinon il reste, avec sa raison. Puis sa branche locale part par `git update-ref
-d`, **seulement si elle pointe encore sur la tête jugée fusionnée** : le travail
est dans la branche par défaut distante, rien ne se perd, et la branche ne
reste pas orpheline parce que le `main` local serait en retard (ce que `git
branch -d` exigerait).

Une fusion par *squash* ou *rebase* n'est pas vue (la tête ne descend pas de la
branche par défaut) : le worktree reste. Les dépôts d'OBSIA fusionnent par
commit de fusion.

  · **Aperçu par défaut.** Sans `--appliquer`, il liste et n'écrit rien —
    `git --no-optional-locks status` ne prend pas l'index d'un agent qui commite.
  · **Il ne force jamais.** `git worktree remove` sans `--force` ; un refus de
    git est dit, avec ce que git a répondu.
  · **Pas de réseau.** Il juge contre `origin/<défaut>` tel qu'il est ; un
    `git fetch --prune origin` d'abord, si l'on veut juger à jour.
  · **Rien d'autre.** Pas de `git worktree prune` : un dossier disparu (disque
    démonté) est signalé, pas effacé.

Il signale aussi, sans y toucher, un worktree rangé hors de la racine commune
(`~/obsia-worktrees/`) : c'est là seulement qu'une interface ouvre l'écriture à
un agent, et un dossier sous `/tmp` se vide au redémarrage.

Usage, depuis le dépôt produit (les autres dépôts en argument) :
  python3 scripts/ranger_worktrees.py [DEPOT ...]            # aperçu
  python3 scripts/ranger_worktrees.py [DEPOT ...] --appliquer

Sans DEPOT, le dépôt qui porte ce script. Codes de sortie : 0 tout va bien,
1 un dépôt illisible ou un refus de git.
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
RACINE_COMMUNE = Path(os.path.expanduser("~/obsia-worktrees"))
CALME = 3600                     # secondes sans activité avant de juger
CACHES = ("__pycache__/", ".pytest_cache/", ".ruff_cache/",
          ".mypy_cache/")         # fichiers ignorés qui se refont
#: Les entrées de reflog qui créent un commit sur la branche. `merge`, `pull` ou
#: `rebase` n'y sont pas : ils peuvent avancer une branche neuve sans travail.
GESTES_QUI_COMMITENT = ("commit", "cherry-pick", "revert")

RETIRER = "retirer"
GARDER = "garder"


def git(depot, *args):
    """Lance git dans `depot` sans verrou facultatif ; rend (code, sortie, erreur)."""
    r = subprocess.run(["git", "--no-optional-locks", "-C", str(depot), *args],
                       capture_output=True, text=True)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def noms_d_agents(racine=RACINE):
    """Les agents qui ont leur fiche dans `IA/agents/`."""
    return {p.stem for p in (Path(racine) / "IA" / "agents").glob("*.md")}


def lire_worktrees(sortie_porcelaine):
    """Les worktrees de `git worktree list --porcelain`, le principal compris.

    Chacun : {"chemin", "tete", "branche" (None si détachée), "principal",
    "verrouille"}.
    """
    liste, courant = [], None
    for ligne in sortie_porcelaine.splitlines():
        if ligne.startswith("worktree "):
            courant = {"chemin": ligne[len("worktree "):], "tete": "",
                       "branche": None, "principal": not liste,
                       "verrouille": False}
            liste.append(courant)
        elif courant is None:
            continue
        elif ligne.startswith("HEAD "):
            courant["tete"] = ligne[len("HEAD "):]
        elif ligne.startswith("branch refs/heads/"):
            courant["branche"] = ligne[len("branch refs/heads/"):]
        elif ligne == "locked" or ligne.startswith("locked "):
            courant["verrouille"] = True
    return liste


def fichiers_bloquants(statut_porcelaine):
    """Les lignes de `status --porcelain --ignored` qui interdisent le retrait :
    tout, sauf les caches ignorés qui se refont."""
    bloquants = []
    for ligne in statut_porcelaine.splitlines():
        chemin = ligne[3:]
        if ligne.startswith("!! ") and any(c in chemin or chemin.endswith(c.rstrip("/"))
                                           for c in CACHES):
            continue
        if ligne.strip():
            bloquants.append(ligne)
    return bloquants


def classer(faits):
    """(verdict, raison) — la décision seule, sans aucune commande.

    `faits` : principal, present, verrouille, agent (la branche est-elle d'un
    agent connu), travail (un commit à elle), fusionne, propre, calme.
    """
    ordre = (
        ("principal", True, "arbre principal"),
        ("present", False, "dossier disparu — signalé, pas effacé"),
        ("verrouille", True, "verrouillé"),
        ("agent", False, "pas une branche d'agent (tête détachée ou autre)"),
        ("travail", False, "aucun commit à elle : worktree neuf, ou création inconnue"),
        ("fusionne", False, "pas encore dans la branche par défaut"),
        ("propre", False, "modifications ou fichiers non suivis ou ignorés"),
        ("calme", False, "activité dans l'heure"),
    )
    for cle, mauvais, raison in ordre:
        if bool(faits.get(cle)) is mauvais:
            return GARDER, raison
    return RETIRER, "fusionné et propre"


def hors_racine(chemin, racine=RACINE_COMMUNE):
    """Vrai si le worktree n'est pas rangé directement sous la racine commune."""
    return Path(chemin).resolve().parent != Path(racine).resolve()


def branche_par_defaut(depot):
    code, sortie, _ = git(depot, "symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    return sortie if code == 0 and sortie else "origin/main"


def a_un_commit(depot, branche):
    """Le reflog de la branche montre-t-il au moins un commit fait sur elle ?"""
    code, sortie, _ = git(depot, "reflog", "show", "--format=%gs", f"refs/heads/{branche}")
    return code == 0 and any(l.startswith(GESTES_QUI_COMMITENT) for l in sortie.splitlines())


def calme(chemin, maintenant=None):
    """Rien n'a bougé dans le worktree (index, HEAD) depuis `CALME` secondes."""
    code, gitdir, _ = git(chemin, "rev-parse", "--absolute-git-dir")
    if code != 0:
        return False
    instants = [os.path.getmtime(p) for p in (Path(gitdir) / "index", Path(gitdir) / "HEAD")
                if p.exists()]
    maintenant = time.time() if maintenant is None else maintenant
    return bool(instants) and maintenant - max(instants) > CALME


def faits_de(depot, w, defaut, agents):
    """Ce que `classer` doit savoir d'un worktree — les seules commandes."""
    faits = {"principal": w["principal"], "verrouille": w["verrouille"],
             "present": os.path.isdir(w["chemin"])}
    if w["principal"] or not faits["present"]:
        return faits
    branche = w["branche"] or ""
    faits["agent"] = "/" in branche and branche.split("/", 1)[0] in agents
    if not faits["agent"]:
        return faits
    faits["travail"] = a_un_commit(depot, branche)
    faits["fusionne"] = git(depot, "merge-base", "--is-ancestor", w["tete"], defaut)[0] == 0
    code, statut, _ = git(w["chemin"], "status", "--porcelain", "--ignored")
    faits["propre"] = code == 0 and not fichiers_bloquants(statut)
    faits["calme"] = calme(w["chemin"])
    return faits


def examiner(depot, agents):
    """[(worktree, verdict, raison)] pour un dépôt, ou None s'il est illisible."""
    code, sortie, _ = git(depot, "worktree", "list", "--porcelain")
    if code != 0:
        return None
    defaut = branche_par_defaut(depot)
    return [(w, *classer(faits_de(depot, w, defaut, agents)))
            for w in lire_worktrees(sortie)]


def main(argv=None, agents=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("depots", nargs="*", default=[str(RACINE)])
    p.add_argument("--appliquer", action="store_true",
                   help="retirer pour de bon ; sans lui, aperçu seul")
    args = p.parse_args(argv)
    agents = noms_d_agents() if agents is None else agents

    echec = False
    for depot in args.depots:
        resultats = examiner(depot, agents)
        if resultats is None:
            print(f"{depot} : pas un dépôt git lisible")
            echec = True
            continue
        a_retirer = [w for w, v, _ in resultats if v == RETIRER]
        print(f"{depot} : {len(resultats) - 1} worktree(s) lié(s), "
              f"{len(a_retirer)} à retirer")
        for w, verdict, raison in resultats:
            if w["principal"]:
                continue
            marque = "−" if verdict == RETIRER else "="
            print(f"  {marque} {w['chemin']}  [{w['branche'] or '(détaché)'}]  {raison}")
            if hors_racine(w["chemin"]):
                print(f"      hors de {RACINE_COMMUNE}/")
        if not args.appliquer:
            continue
        for w in a_retirer:
            code, _, erreur = git(depot, "worktree", "remove", w["chemin"])
            if code != 0:
                print(f"  ! git garde {w['chemin']} : {erreur}")
                echec = True
                continue
            print(f"  retiré {w['chemin']}")
            # La branche part si elle pointe toujours sur la tête jugée
            # fusionnée — sinon git refuse, et c'est dit.
            code, _, erreur = git(depot, "update-ref", "-d",
                                  f"refs/heads/{w['branche']}", w["tete"])
            if code != 0:
                print(f"  ! branche {w['branche']} gardée : {erreur}")
                echec = True
    if not args.appliquer:
        print("Aperçu seul : rien n'a été retiré (--appliquer pour le faire).")
    return 1 if echec else 0


if __name__ == "__main__":
    sys.exit(main())
