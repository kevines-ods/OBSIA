"""Contrôles de la mémoire du coffre : unicité des noms, carnets, noms de
`0-MEMOIRES/`, dépôt de données.

Extraits de `verifier_coffre.py`, qui reste la porte d'entrée. Chaque contrôle
reçoit un contexte `ctx` — `racine`, `coffre`, `erreur`, `avertir`,
`signaler_memoire`, `signaler_bascule` — construit au moment de l'appel : aucun
état global ici.
"""

import os
import re
import subprocess
from pathlib import Path

from convention_des_notes import (COURRIER, EXPERIENCES, MEMOIRES, PREFERENCES,
                                  STATUTS_CARNET, carnet_a_la_forme,
                                  carnet_du_dossier, liste_des_agents)
from generer_prompt import lire_frontmatter


def verifier_unicite_des_noms(ctx):
    """§6 : les noms de notes doivent être uniques dans tout le coffre parent.

    On ne peut pas voir le coffre parent depuis ici ; on vérifie donc l'unicité
    à l'intérieur d'OBSIA, qui en est la condition nécessaire.
    """
    banals = {"sommaire.md", "README.md"}          # légitimement répétés
    vus: dict[str, list[str]] = {}
    for chemin, sous, fichiers in os.walk(ctx.racine):
        sous[:] = [d for d in sous
                   if not d.startswith(".") and d not in ("scripts", "assets")]
        for f in fichiers:
            if f.endswith(".md") and f not in banals:
                vus.setdefault(f, []).append(
                    str(Path(chemin).joinpath(f).relative_to(ctx.racine)))
    for nom, chemins in sorted(vus.items()):
        if len(chemins) > 1:
            ctx.erreur(nom, "nom de note en double, les rétroliens deviennent ambigus (§6) : %s"
                   % ", ".join(chemins))


# ------------------------------------------------------------------- carnets
# La forme d'un carnet n'a qu'un exemplaire, et il vit dans le moteur partagé :
# c'est lui qui nomme (`nom_de_carnet`), c'est lui qui reconnaît
# (`carnet_a_la_forme`, `carnet_du_dossier`). La date et les statuts se lisent là
# aussi — deux listes de statuts finiraient par diverger.

NOTE_DATEE_A_PLAT = re.compile(r"^\d{4}-\d{2}-\d{2}-.*\.md$")
RESERVES_PROJET = ("carnets", "documents", "code")


def designation(ctx, chemin: Path) -> Path:
    """Chemin affiché : relatif au dépôt produit s'il y est, relatif au coffre
    parent sinon — la mémoire vit là (§7.1), et un rapport doit rester lisible."""
    bases = []
    for base in (ctx.racine, ctx.coffre, ctx.racine.parent):
        if base not in bases:
            bases.append(base)
    for base in bases:
        try:
            return chemin.relative_to(base)
        except ValueError:
            continue
    return chemin


def emplacements_de_projets(ctx):
    """Les dossiers de projets à contrôler, dans l'ordre : le coffre parent
    (`0-PROJETS/`, et son ancien nom `-PROJETS/`), puis l'ancien
    `mémoire/projets` du dépôt tant que la bascule dure (§6, transition).

    Ne rend que ce qui existe : un clone de la CI n'a pas de coffre parent."""
    candidats = [ctx.coffre / "0-PROJETS", ctx.coffre / "-PROJETS",
                 ctx.racine / "mémoire" / "projets"]
    return [c for c in candidats if c.is_dir()]

def verifier_carnets(ctx):
    """§6 : forme des carnets, un seul niveau de chantier, transition.

    - un carnet est `0-PROJETS/<projet>/carnets/AAAA-MM-JJ-<projet>-<sujet>.md`,
      avec `agent:`, `projet:` et `statut:` — trois chaînes non vides, le
      `projet:` égal au nom du dossier, et un `statut:` dans
      `en cours | en attente | clos` ;
    - un chantier est un dossier de plus, avec **ses** `carnets/`, `documents/`
      et son résumé ; ses carnets portent son nom dans `projet:` — jamais de
      vision, jamais de chantier dans un chantier ;
    - les carnets du jour hors chantier restent dans `0-PROJETS/<projet>/carnets/`,
      et s'y nomment du nom du projet ;
    - un sous-dossier dans un `carnets/` est refusé : un carnet est un fichier ;
    - la mémoire vit dans le coffre parent (§7.1) : on la contrôle là où elle
      est — `0-PROJETS/` du coffre parent, son ancien nom `-PROJETS/`, et
      l'ancien `mémoire/projets` du dépôt tant que la bascule dure. Un clone de
      la CI n'a aucun de ces dossiers : il n'y a alors rien à contrôler ;
    - tant que la bascule dure (§11), une note datée à plat et un dossier
      `archives/` (au niveau du projet comme sous `carnets/`) restent tolérés :
      avertissement, jamais erreur — même sur le coffre lui-même, sans quoi la
      migration serait impossible à finir. **Passé le 2026-12-31, la tolérance
      tombe** : les mêmes formes font échouer le contrôle, comme l'ancienne
      mémoire de `verifier_bascule` — une échéance, un seul traitement.
    """
    for projets in emplacements_de_projets(ctx):
        for projet in sorted(projets.iterdir()):
            if not projet.is_dir() or projet.name.startswith("."):
                continue
            parcourir_projet(ctx, projet, projet.name, 0)

def parcourir_projet(ctx, dossier: Path, projet: str, niveau: int):
    """`niveau` 0 pour un projet, 1 pour un de ses chantiers ; au-delà, refus (§6).

    Au niveau 0, `carnets/` porte les carnets du jour écrits hors chantier. Au
    niveau 1, le dossier est un **chantier** : il a ses propres `carnets/`, ses
    `documents/`, son résumé, et rien de plus — pas de vision, et pas un
    chantier dans un chantier.
    """
    for entree in sorted(dossier.iterdir()):
        if entree.name in ("sommaire.md", "README.md"):
            continue
        if entree.is_file():
            if NOTE_DATEE_A_PLAT.match(entree.name):
                ctx.signaler_bascule(designation(ctx, entree),
                        "ancienne forme : note datée à plat, à migrer vers "
                        "`carnets/` (§6)")
            continue
        if entree.name == "carnets":
            verifier_carnets_dun_projet(ctx, entree, projet)
        elif entree.name == "archives":
            ctx.signaler_bascule(designation(ctx, entree),
                    "`archives/` n'existe plus : un chantier clos part, dossier "
                    "entier, dans `0-MEMOIRES/` (§6)")
        elif entree.name in RESERVES_PROJET:
            continue
        elif niveau >= 1:
            ctx.erreur(designation(ctx, entree),
                   "chantier imbriqué — un chantier ne contient pas de chantier (§6)")
        else:
            parcourir_projet(ctx, entree, entree.name, 1)

def verifier_carnets_dun_projet(ctx, dossier: Path, projet: str):
    for carnet in sorted(dossier.iterdir()):
        if carnet.name in ("sommaire.md", "README.md"):
            continue
        if carnet.is_dir():
            if carnet.name == "archives":
                ctx.signaler_bascule(designation(ctx, carnet),
                        "`carnets/archives/` n'existe plus : un chantier clos "
                        "part dans `0-MEMOIRES/` (§6)")
            else:
                ctx.erreur(designation(ctx, carnet),
                       "sous-dossier dans `carnets/` — un carnet est un fichier (§6)")
            continue
        if carnet.is_file() and carnet.name.endswith(".md"):
            verifier_carnet(ctx, carnet, projet)

def verifier_carnet(ctx, chemin: Path, projet: str):
    rel = designation(ctx, chemin)
    if not carnet_a_la_forme(chemin.name):
        ctx.signaler_memoire(rel, "carnet mal nommé — attendu "
                              "`AAAA-MM-JJ-<projet>-<sujet>.md` (§6)")
    elif not carnet_du_dossier(chemin.name, projet):
        ctx.signaler_memoire(rel, "carnet mal nommé : `<projet>` ne correspond pas au "
                              "dossier `%s` (§6)" % projet)
    fm = lire_frontmatter(chemin)
    if fm is None:
        ctx.signaler_memoire(rel, "carnet sans frontmatter fermé (§6)")
        return
    for champ in ("agent", "projet", "statut"):
        valeur = fm.get(champ)
        if not isinstance(valeur, str) or not valeur.strip():
            ctx.signaler_memoire(rel, "carnet `%s:` vide ou absent (§6)" % champ)
    statut = fm.get("statut")
    if isinstance(statut, str) and statut.strip() and statut not in STATUTS_CARNET:
        ctx.signaler_memoire(rel, "carnet `statut: %s` — attendu `en cours`, "
                              "`en attente` ou `clos` (§6)" % statut)
    projet_fm = fm.get("projet")
    if isinstance(projet_fm, str) and projet_fm.strip() and projet_fm != projet:
        ctx.signaler_memoire(rel, "carnet `projet: %s` ne correspond pas au dossier "
                              "`%s` (§6)" % (projet_fm, projet))


# --------------------------------------------------------- dépôt de données

def _git_dans(chemin: Path, *arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(chemin), *arguments],
                          capture_output=True, text=True)


# ------------------------------------------------------- noms de 0-MEMOIRES

def noms_d_agents_declares(ctx) -> set:
    """Le nom de chaque agent déclaré : sous `0-MEMOIRES/`, il est réservé (§6).

    « Qui est un agent » n'a **qu'une** définition : `liste_des_agents` du moteur
    partagé, qui voit les deux formes de déclaration (§5) — un agent déclaré en
    dossier compte autant qu'un agent déclaré d'un fichier plat.
    """
    return set(liste_des_agents(ctx.racine))


def verifier_noms_de_memoire(ctx):
    """§6 : dans `0-MEMOIRES/`, la mémoire vivante et la mémoire gelée ne se confondent pas.

    Le dossier porte la mémoire des agents — `préférences/` et
    `<nom-agent>/expériences/`, vivantes, plus les messages à plat de `courrier/`
    — **et** les chantiers clos, gelés.
    Un projet qui s'appellerait `préférences`, `courrier` ou porterait le nom d'un
    agent rendrait les deux indistinguables : c'est une erreur de nommage, pas un
    détail de rangement.

    Faute de lire une intention, la règle se contrôle par la **forme** :
    `préférences/` et `courrier/` ne contiennent que des notes, la mémoire d'un
    agent n'a qu'un `expériences/` de notes, et tout autre dossier est un projet
    gelé — donc il
    porte au moins un chantier. Le contrôle ne tourne que sur le coffre parent
    (§7.1) : un clone de la CI n'a pas de `0-MEMOIRES/`.
    """
    racine_memoires = ctx.coffre / MEMOIRES
    if not racine_memoires.is_dir():
        return
    reserves = {PREFERENCES} | noms_d_agents_declares(ctx)
    for entree in sorted(racine_memoires.iterdir()):
        if entree.name.startswith("."):
            continue
        if not entree.is_dir():
            if entree.name not in ("README.md", "sommaire.md"):
                ctx.signaler_memoire(entree, "`%s/` n'accueille que des dossiers : "
                                         "`%s/`, la mémoire d'un agent, ou un projet gelé (§6)"
                                 % (MEMOIRES, PREFERENCES))
            continue
        if entree.name == PREFERENCES:
            for intrus in sorted(entree.iterdir()):
                if intrus.is_dir():
                    ctx.signaler_memoire(intrus, "`%s/%s/` est la mémoire des agents : elle ne contient "
                                             "que des notes `<sujet>.md`. Un projet ne peut pas porter "
                                             "ce nom (§6)" % (MEMOIRES, PREFERENCES))
            continue
        if entree.name == COURRIER:
            for intrus in sorted(entree.iterdir()):
                if intrus.is_dir():
                    ctx.signaler_memoire(intrus, "`%s/%s/` ne contient que des notes `<sujet>.md` : "
                                             "un chantier ne vit pas dans le courrier. Un projet ne peut "
                                             "pas porter ce nom (§6)" % (MEMOIRES, COURRIER))
            continue
        if entree.name in reserves:
            lecons = entree / EXPERIENCES
            if not lecons.is_dir():
                ctx.signaler_memoire(entree, "`%s/%s/` est l'espace mémoire de cet agent : il ne contient "
                                         "que `%s/`. Un projet ne peut pas porter le nom d'un agent (§6)"
                                 % (MEMOIRES, entree.name, EXPERIENCES))
            elif [e for e in sorted(lecons.iterdir()) if e.is_dir()]:
                ctx.signaler_memoire(lecons, "`%s/` ne contient que des notes `<sujet>.md` (§6)"
                                 % EXPERIENCES)
            continue
        if not [e for e in sorted(entree.iterdir())
                if e.is_dir() and not e.name.startswith(".")]:
            ctx.signaler_memoire(entree, "projet gelé sans chantier : sous `%s/`, un projet est "
                                     "`<projet>/<chantier>/` (§6)" % MEMOIRES)


# --------------------------------------------------------- dépôt de données

def verifier_depot_de_donnees(ctx):
    """§7.1 : la liste blanche du coffre est le gabarit, et `OBSIA/` n'y est pas suivi.

    Le `.gitignore` du coffre parent n'est pas écrit à la main : c'est le gabarit
    `IA/system/depot-de-donnees/gitignore-coffre`, posé par l'installeur et jamais
    écrasé. Un écart veut dire que quelqu'un a retouché la liste blanche sur la
    machine — la prochaine installation ne le verra pas, et `OBSIA/` peut se
    retrouver versionné dans la mémoire sans que personne ne s'en aperçoive.

    Ne s'exécute que sur un coffre parent désigné (`--coffre`) : un clone de la
    CI n'en a pas.
    """
    gabarit = ctx.racine / "IA" / "system" / "depot-de-donnees" / "gitignore-coffre"
    if not gabarit.is_file():
        ctx.erreur(designation(ctx, gabarit),
               "gabarit de la liste blanche du coffre absent (§7.1)")
        return
    gitignore = ctx.coffre / ".gitignore"
    if not gitignore.is_file():
        ctx.signaler_memoire(Path(".gitignore"),
                         "le coffre parent n'a pas de liste blanche : le dépôt de "
                         "données n'est pas initialisé — l'installeur la pose (§7.1)")
        return
    try:
        ecrit = gitignore.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        ctx.signaler_memoire(Path(".gitignore"), "liste blanche illisible (§7.1)")
        return
    if ecrit != gabarit.read_text(encoding="utf-8"):
        ctx.signaler_memoire(Path(".gitignore"),
                         "diffère du gabarit `IA/system/depot-de-donnees/gitignore-coffre` "
                         "— la liste blanche est le gabarit, sans retouche (§7.1)")
    if _git_dans(ctx.coffre, "rev-parse", "--git-dir").returncode != 0:
        return
    suivis = [ligne for ligne in
              _git_dans(ctx.coffre, "ls-files", "--", ctx.racine.name).stdout.splitlines()
              if ligne.strip()]
    if suivis:
        ctx.signaler_memoire(Path(suivis[0]),
                         "le dépôt produit est suivi par le dépôt de données du "
                         "coffre — `%s/` n'entre jamais dans la mémoire (§7.1)"
                         % ctx.racine.name)


# ------------------------------------------------------------ ce qui traîne

#: Copie de conflit d'un outil de synchronisation (`x.sync-conflict-…-ABCD.md`).
#: Ce n'est pas un résidu : c'est une **note concurrente** de la vraie, qui
#: porte souvent la version d'avant.
COPIE_DE_CONFLIT = re.compile(r"\.sync[-.]conflict", re.IGNORECASE)

#: Résidus d'exécution ou d'édition. Refusés à la racine seulement : dans
#: `_MAINTENANCE/`, un journal est quelquefois voulu.
RESIDU = re.compile(r"\.(log|bak|tmp|orig|rej|swp|swo)$|~$|\.backup"
                    r"|^\.DS_Store$", re.IGNORECASE)


def verifier_fichiers_etrangers(ctx):
    """§7.4 : ni copie de conflit, ni résidu au ras du coffre.

    La synchronisation travaille sur le dossier, pas sur l'historique : un
    `llama.log`, une sauvegarde d'éditeur ou une copie de conflit voyage vers
    tous les postes même quand git l'ignore — le coffre se salit ailleurs sans
    que rien ne le dise.

    Une copie de conflit est plus grave qu'un résidu : deux postes ont écrit la
    même note, et l'agent peut lire, citer ou indexer la copie à la place de
    l'original. Elle est refusée partout.

    Ne s'exécute que sur un coffre parent désigné (`--coffre`) : un clone de la
    CI n'en a pas. Les dossiers cachés (`.git`, `.worktrees`) sont sautés — un
    arbre de travail n'est pas la mémoire.
    """
    if ctx.coffre is None:
        return
    coffre = Path(ctx.coffre)
    for chemin, sous, fichiers in os.walk(coffre):
        sous[:] = [d for d in sous if not d.startswith(".")]
        for nom in sorted(fichiers):
            relatif = Path(chemin).joinpath(nom).relative_to(coffre)
            if COPIE_DE_CONFLIT.search(nom):
                ctx.signaler_memoire(
                    relatif,
                    "copie de conflit de synchronisation : c'est une note "
                    "concurrente de la vraie — la comparer, garder la bonne, "
                    "retirer la copie (§7.4)")
            elif Path(chemin) == coffre and RESIDU.search(nom):
                ctx.signaler_memoire(
                    relatif,
                    "résidu à la racine du coffre : il voyage vers les autres "
                    "postes alors que git l'ignore — le ranger dans "
                    "`_MAINTENANCE/` ou hors du coffre (§7.4)")
