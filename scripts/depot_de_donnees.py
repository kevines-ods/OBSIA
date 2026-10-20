#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Le dépôt de données du coffre parent (§7.1) — ce que ses crochets appellent.

La mémoire vit hors du dépôt produit, dans un dépôt git à part, à la racine du
coffre parent. Ce script est ce que ses crochets déclenchent. Il ne lit ni
n'écrit rien d'autre que ce dépôt-là et l'état de poussée qui vit dans son
`.git/` (hors version, et donc hors synchronisation).

    python3 scripts/depot_de_donnees.py avant-commit --coffre <coffre> [--produit <dépôt produit>]
    python3 scripts/depot_de_donnees.py apres-commit --coffre <coffre>
    python3 scripts/depot_de_donnees.py apres-rewrite --coffre <coffre>
    python3 scripts/depot_de_donnees.py fraicheur    --coffre <coffre> [--heures 48]

`avant-commit` refuse, dans l'ordre : un commit venu d'une autre machine que
l'écrivain déclaré (« un seul écrivain », §7.1) ; une valeur à forme de secret
que le commit ajoute à la mémoire (`garde_secrets.py`, §7.1) ; puis il contrôle
la mémoire du coffre avec `verifier_coffre.py --coffre <coffre> --carnets`.

**Ce que le crochet relit, et ce qu'il ne relit pas.** Les règles de
`garde_secrets.py` ne se ressemblent pas, et cette asymétrie est une décision,
pas un détail d'implémentation : un secret **nommé** n'est jugé que sur les
lignes que le commit **ajoute**, tandis qu'un **bloc de base64** et un **jeton
isolé** sont relus dans **tout le contenu** de chaque fichier indexé — ils ne
veulent rien dire ligne à ligne. Un secret nommé qu'aucun commit ne touche tient
donc bon, et le retirer est un acte humain, sur la note et dans l'historique.
`tests/test_secrets_a_deux_portes.py` fixe les deux versants ; les changer ici
sans les changer là casse l'un des deux.

`apres-commit` pousse vers `origin` et note l'instant du succès dans
`<coffre>/.git/obsia-derniere-poussee`. Un échec est journalisé, jamais
bloquant : le commit a déjà eu lieu. L'état de poussée — verrou, marque,
journaux — vit dans le dossier git **commun** (`--git-common-dir`), partagé
par tous les worktrees du coffre : deux arbres liés n'y mènent donc qu'une
poussée à eux deux.

**Une seule poussée à la fois.** Un verrou (`<coffre>/.git/obsia-poussee.verrou`)
sérialise les appels : le détenteur attend une fenêtre d'anti-rebond, pousse,
puis recommence tant que la pointe bouge. Une salve — un rebase qui rejoue N
commits et rappelle ce script à chaque commit — se solde donc par une ou deux
poussées **successives**, jamais par N poussées concurrentes. C'est la
concurrence, pas le nombre, qui avait produit les `cannot lock ref` et le
`unable to migrate objects` du 2026-10-14. Un échec du détenteur n'abandonne
plus la salve : il est retenté un nombre borné de fois.

**Pendant une réécriture d'historique, la poussée se suspend d'elle-même.** Un
rebase rejoue ses commits un à un : pousser chacun d'eux serait au mieux
inutile, au pire un `push` non-avance (l'historique réécrit n'avance plus). Le
script détecte l'état `rebase-merge`/`rebase-apply` et suspend ; c'est le
crochet `post-rewrite`, à la fin, qui pousse **une fois** la pointe finale — le
seul moment où la branche est réattachée et stable. Rien à poser de la main de
l'opérateur pour un rebase ; les autres réécritures (`filter-branch`) se
suspendent par `OBSIA_POUSSEE=0` ou la marque `<coffre>/.git/obsia-poussee.suspendue`.
Chaque épisode de suspension — et sa reprise — laisse une ligne datée dans
`<coffre>/.git/obsia-poussee.suspendue.log`, que `fraicheur` relaie : une
poussée suspendue ne disparaît plus sans trace. La fenêtre d'anti-rebond se
règle par `OBSIA_POUSSEE_REBOND` (en secondes, 3 par défaut).

`fraicheur` dit si la dernière poussée réussie a moins du seuil d'heures (48 h
par défaut) — c'est la sonde qu'un moniteur push peut brancher — et rappelle,
le cas échéant, depuis quand la poussée est suspendue, qu'une salve s'est
arrêtée au plafond, ou que la dernière poussée a échoué.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import subprocess
import sys
import time
from pathlib import Path

try:
    import fcntl
except ImportError:      # plateforme sans verrou de fichier : on ne sérialise pas
    fcntl = None

sys.path.insert(0, str(Path(__file__).resolve().parent))
import garde_secrets as GS  # noqa: E402
import modules as MOD  # noqa: E402

RACINE_DEFAUT = Path(__file__).resolve().parent.parent
NOM_DISTANT = "origin"
HEURES_FRAICHEUR = 48
FICHIER_DERNIERE_POUSSEE = "obsia-derniere-poussee"
FICHIER_JOURNAL = "obsia-poussee.log"
FICHIER_JOURNAL_SUSPENSION = "obsia-poussee.suspendue.log"
FICHIER_VERROU = "obsia-poussee.verrou"
FICHIER_SUSPENSION = "obsia-poussee.suspendue"
VARIABLE_SUSPENSION = "OBSIA_POUSSEE"
VARIABLE_REBOND = "OBSIA_POUSSEE_REBOND"
FENETRE_REBOND = 3.0     # secondes
TOURS_MAX = 10           # poussées d'affilée au plus pendant une salve
TOURS_ECHEC_MAX = 2      # reprises d'une poussée échouée avant d'abandonner
#: Marqueurs, dans le dossier git du worktree, d'une réécriture d'historique en
#: cours — on ne pousse pas un historique qu'on est en train de réécrire.
MARQUES_DE_REECRITURE = (("rebase-merge", "rebase"), ("rebase-apply", "rebase"))
CODE_SALVE_INACHEVEE = 2  # la salve s'est arrêtée au plafond, pointe non poussée
MARQUEUR_SALVE_INACHEVEE = "salve inachevée"  # écrit au journal, relu par fraicheur


# ------------------------------------------------------------------- lecture

def _git(coffre: Path, *arguments: str, delai: int | None = None) -> subprocess.CompletedProcess:
    """Lance git dans le coffre. Ne lève jamais : rend le résultat, code inclus."""
    return subprocess.run(
        ["git", "-C", str(coffre), *arguments],
        capture_output=True, text=True, timeout=delai,
    )


def dossier_git(coffre: Path) -> Path | None:
    """Le dossier git **du worktree courant**, ou None hors dépôt git.

    C'est lui qui porte l'état propre à cet arbre-ci (`rebase-merge`, index…) :
    la détection d'une réécriture en cours s'y fait donc, et non dans le dossier
    commun.
    """
    resultat = _git(coffre, "rev-parse", "--git-dir")
    if resultat.returncode != 0:
        return None
    chemin = Path(resultat.stdout.strip())
    return chemin if chemin.is_absolute() else coffre / chemin


def dossier_git_commun(coffre: Path) -> Path | None:
    """Le dossier git **commun à tous les worktrees**, ou None hors dépôt git.

    Verrou, marque de suspension, journaux et marque de poussée y vivent : deux
    worktrees liés du même coffre partagent ainsi un seul verrou, donc une seule
    poussée. Sans cela, chaque arbre aurait sa propre marque de suspension — et
    suspendre dans l'un ne suspendrait rien dans l'autre.
    """
    resultat = _git(coffre, "rev-parse", "--git-common-dir")
    if resultat.returncode != 0 or not resultat.stdout.strip():
        return dossier_git(coffre)
    chemin = Path(resultat.stdout.strip())
    return chemin if chemin.is_absolute() else coffre / chemin


def nom_du_distant(coffre: Path) -> str | None:
    """L'URL du distant `origin`, ou None s'il n'est pas configuré."""
    resultat = _git(coffre, "remote", "get-url", NOM_DISTANT)
    if resultat.returncode != 0:
        return None
    return resultat.stdout.strip() or None


def branche_courante(coffre: Path, git: Path | None = None) -> str:
    """La branche de tête, même quand HEAD est détaché.

    Pendant un rebase, `rev-parse --abbrev-ref HEAD` rend « HEAD » : la branche
    réellement réécrite n'est alors lisible que dans l'état du rebase. On la
    relit là plutôt que de pousser vers une ref « HEAD », que le distant ne
    saurait résoudre — c'est ce qui avait produit 29 entrées `branche=HEAD` sur
    37 dans le journal du 2026-10-14.
    """
    resultat = _git(coffre, "rev-parse", "--abbrev-ref", "HEAD")
    nom = resultat.stdout.strip() if resultat.returncode == 0 else ""
    if nom and nom != "HEAD":
        return nom
    dossier = git if git is not None else dossier_git(coffre)
    if dossier is not None:
        for marque, _ in MARQUES_DE_REECRITURE:
            try:
                ref = (dossier / marque / "head-name").read_text(encoding="utf-8").strip()
            except OSError:
                continue
            if ref.startswith("refs/heads/"):
                return ref[len("refs/heads/"):]
    return nom or "HEAD"


def reecriture_en_cours(git: Path | None) -> str | None:
    """Pourquoi une réécriture d'historique est en cours, ou None.

    Le dossier git **du worktree** est attendu : c'est là que git pose
    `rebase-merge` (rebase moderne) ou `rebase-apply` (git am / rebase ancien).
    """
    if git is None:
        return None
    for marque, nom in MARQUES_DE_REECRITURE:
        if (git / marque).exists():
            return "%s en cours" % nom
    return None


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


# ------------------------------------------------------ poussée sérialisée

def fenetre_de_rebond() -> float:
    """La fenêtre d'anti-rebond en secondes, réglable par l'environnement."""
    brut = os.environ.get(VARIABLE_REBOND)
    try:
        valeur = FENETRE_REBOND if brut is None else float(brut)
    except ValueError:
        return FENETRE_REBOND
    return valeur if valeur >= 0 else FENETRE_REBOND


def raison_de_suspendre(git: Path | None) -> str | None:
    """Pourquoi ne pas pousser maintenant, ou None.

    Deux interrupteurs explicites : la variable d'environnement `OBSIA_POUSSEE`
    à « 0 » (posée p. ex. sur toute la durée d'un `filter-branch`), ou la marque
    `obsia-poussee.suspendue` dans le dossier git commun. Ils complètent la
    suspension automatique pendant un rebase, que `reecriture_en_cours` détecte.
    """
    valeur = (os.environ.get(VARIABLE_SUSPENSION) or "").strip().lower()
    if valeur in {"0", "non", "false", "off"}:
        return "%s=%s" % (VARIABLE_SUSPENSION, valeur)
    if git is not None and (git / FICHIER_SUSPENSION).is_file():
        return "marque %s" % FICHIER_SUSPENSION
    return None


def dernier_etat_de_suspension(git: Path | None) -> tuple[str, str, str] | None:
    """(horodatage, état, détail) de la dernière ligne du journal de suspension.

    L'état vaut « suspendue » ou « reprise ». C'est la dernière ligne qui fait
    foi : `fraicheur` en tire le « suspendu depuis … ».
    """
    if git is None:
        return None
    try:
        lignes = (git / FICHIER_JOURNAL_SUSPENSION).read_text(
            encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    for ligne in reversed(lignes):
        if not ligne.strip():
            continue
        morceaux = ligne.split("  ", 2)
        if len(morceaux) < 2:
            return None
        return morceaux[0], morceaux[1], morceaux[2] if len(morceaux) > 2 else ""
    return None


def noter_etat_de_suspension(git: Path | None, etat: str, detail: str = "") -> None:
    """Écrit une ligne d'état de suspension — seulement si elle est nouvelle.

    Un rebase rappelle `post-commit` à chaque commit rejoué : on veut **une**
    ligne pour l'épisode, pas N. On ne répète donc pas l'état déjà en dernière
    ligne du journal.
    """
    if git is None:
        return
    dernier = dernier_etat_de_suspension(git)
    if etat == "reprise" and dernier is None:
        return      # aucune suspension à clore : rien à dire, pas de fichier à créer
    if dernier is not None and (dernier[1], dernier[2]) == (etat, detail):
        return
    ligne = "%s  %s" % (dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                        etat)
    if detail:
        ligne += "  " + detail
    try:
        with (git / FICHIER_JOURNAL_SUSPENSION).open("a", encoding="utf-8") as journal:
            journal.write(ligne + "\n")
    except OSError:
        pass


def tenter_verrou(git: Path):
    """Le fichier de verrou, tenu, ou None si un autre le tient déjà.

    `flock` porte sur le descripteur : le verrou tombe quand le fichier rendu
    est refermé. Sans `fcntl`, on rend le fichier sans verrou — on ne sérialise
    pas les poussées, mais on continue de pousser.
    """
    fichier = (git / FICHIER_VERROU).open("a", encoding="utf-8")
    if fcntl is None:
        return fichier
    try:
        fcntl.flock(fichier.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        fichier.close()
        return None
    return fichier


def pointe_du_coffre(coffre: Path) -> str:
    """Le commit de tête du coffre, ou une chaîne vide si on ne peut pas le lire."""
    resultat = _git(coffre, "rev-parse", "HEAD")
    return resultat.stdout.strip() if resultat.returncode == 0 else ""


def pousser_vers_le_distant(coffre: Path, git: Path | None, branche: str) -> int:
    """Pousse `branche` vers l'origine, note le succès, journalise l'échec."""
    try:
        resultat = _git(coffre, "push", NOM_DISTANT, branche, delai=120)
    except subprocess.TimeoutExpired:
        resultat = None
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
    print("  ! poussée vers %s échouée (journalisé dans %s) : %s"
          % (NOM_DISTANT, (git / FICHIER_JOURNAL) if git is not None else FICHIER_JOURNAL,
             detail), file=sys.stderr)
    return 1


def pousser_avec_reprise(coffre: Path, git: Path | None, branche: str) -> int:
    """Pousse, et retente un nombre borné de fois si le distant a hoqueté.

    Sans cette reprise, l'échec du détenteur du verrou laissait **toute** la
    salve en local : les autres crochets avaient déjà rendu la main (verrou
    tenu), et personne ne repoussait avant le commit suivant. Un hoquet du
    réseau ne doit pas coûter une salve entière.
    """
    code = pousser_vers_le_distant(coffre, git, branche)
    for _ in range(TOURS_ECHEC_MAX):
        if code == 0:
            break
        time.sleep(fenetre_de_rebond())
        code = pousser_vers_le_distant(coffre, git, branche)
    return code


def pousser_par_salve(coffre: Path, git: Path, branche: str) -> int:
    """Anti-rebond, puis poussée répétée tant que la pointe bouge.

    Un rebase rejoue ses commits un à un, et chacun rappelle ce script. La
    fenêtre d'anti-rebond laisse d'abord la salve retomber : on pousse ainsi
    une pointe déjà stable, une fois plutôt que N. Si la pointe a bougé pendant
    la poussée, la salve n'était pas finie et on repart pour un tour — c'est ce
    qui rattrape un commit arrivé pendant la poussée précédente.

    Le plafond de tours n'est pas un succès : s'il est atteint alors que la
    pointe bougeait encore, on le journalise et on rend `CODE_SALVE_INACHEVEE`,
    pour ne pas confondre « tout est parti » et « on s'est arrêté en chemin ».
    """
    time.sleep(fenetre_de_rebond())
    for _ in range(TOURS_MAX):
        avant = pointe_du_coffre(coffre)
        code = pousser_avec_reprise(coffre, git, branche)
        if code != 0:
            return code
        if not avant or pointe_du_coffre(coffre) == avant:
            return 0
    try:
        with (git / FICHIER_JOURNAL).open("a", encoding="utf-8") as journal:
            journal.write("%s  %s  %s (plafond de %d tours)\n"
                          % (dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                             branche, MARQUEUR_SALVE_INACHEVEE, TOURS_MAX))
    except OSError:
        pass
    print("  ! salve inachevée après %d tours : la pointe bougeait encore, toute "
          "la poussée n'est pas passée." % TOURS_MAX, file=sys.stderr)
    return CODE_SALVE_INACHEVEE


# ---------------------------------------------------------------- apres-commit

def apres_commit(coffre: Path, reecriture_finie: bool = False) -> int:
    """Pousse vers `origin`, note le succès, journalise l'échec. Jamais bloquant.

    Une seule poussée à la fois : le verrou, pris sur le dossier git **commun**,
    sérialise les appels — deux worktrees du coffre n'en mènent donc qu'un à eux
    deux —, et le détenteur anti-rebonde. Une salve ne lance plus N poussées
    concurrentes, mais des poussées successives.

    Une réécriture d'historique en cours suspend d'office la poussée, et l'état
    est journalisé (`fraicheur` le relaie). `reecriture_finie=True`, posé par le
    crochet `post-rewrite`, dit que la réécriture est terminée : on pousse alors
    la pointe finale, une fois.
    """
    if nom_du_distant(coffre) is None:
        return 0
    git = dossier_git_commun(coffre)
    suspendu = raison_de_suspendre(git)
    if suspendu is None and not reecriture_finie:
        suspendu = reecriture_en_cours(dossier_git(coffre))
    if suspendu is not None:
        noter_etat_de_suspension(git, "suspendue", suspendu)
        print("Poussée suspendue (%s) : la pointe du coffre reste locale." % suspendu)
        return 0
    noter_etat_de_suspension(git, "reprise")
    branche = branche_courante(coffre)
    if git is None or fcntl is None:
        return pousser_avec_reprise(coffre, git, branche)
    verrou = tenter_verrou(git)
    if verrou is None:
        # Une autre poussée tient le verrou : elle pousse la *pointe* de la
        # branche, donc la nôtre y est comprise, et elle recommence tant que la
        # pointe bouge. Il n'y a rien à faire ici.
        return 0
    try:
        return pousser_par_salve(coffre, git, branche)
    finally:
        verrou.close()


# ------------------------------------------------------------------ fraicheur

def rappeler_la_suspension(coffre: Path, git: Path) -> None:
    """Rappelle, sur la sortie d'erreur, depuis quand la poussée est suspendue.

    Sans cela, une marque laissée en place arrêtait la poussée **sans trace** :
    on ne s'en apercevait que le seuil de fraîcheur franchi, sans savoir
    pourquoi. On croise l'interrupteur vivant avec la dernière ligne du journal.
    """
    suspendu = raison_de_suspendre(git) or reecriture_en_cours(dossier_git(coffre))
    if suspendu is None:
        return
    dernier = dernier_etat_de_suspension(git)
    depuis = ""
    if dernier is not None and dernier[1] == "suspendue" and dernier[2] == suspendu:
        depuis = " depuis %s" % dernier[0]
    print("Poussée suspendue%s (%s) : la mémoire du coffre ne part pas tant que "
          "l'interrupteur reste posé." % (depuis, suspendu), file=sys.stderr)


def lire_le_journal(git: Path) -> list[tuple[dt.datetime, str]]:
    """Les lignes horodatées du journal des poussées, dans l'ordre d'écriture."""
    try:
        lignes = (git / FICHIER_JOURNAL).read_text(
            encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    entrees = []
    for ligne in lignes:
        if not ligne.strip():
            continue
        try:
            quand = dt.datetime.fromisoformat(ligne.split("  ", 1)[0])
        except ValueError:
            continue
        if quand.tzinfo is None:
            quand = quand.replace(tzinfo=dt.timezone.utc)
        entrees.append((quand, ligne))
    return entrees


def rappeler_le_journal(git: Path, depuis: dt.datetime) -> None:
    """Rappelle ce que le journal dit depuis la dernière poussée réussie.

    Un « à jour » tairait deux choses qui laissent des commits en local : une
    salve arrêtée au plafond, et un échec de poussée. On les cherche sur **tout**
    le journal à partir de la marque, pas seulement sur sa dernière ligne — un
    échec peut être écrit après la ligne de plafond et la masquer.

    La marque est comprise (`>=`) : la ligne de plafond est écrite aussitôt après
    la poussée réussie qui a posé la marque, et les deux horodatages sont à la
    seconde — ils sont donc égaux dans la quasi-totalité des cas. Un `>` strict
    laisserait la salve inachevée sans écho. Raviver une vieille ligne de plafond
    est impossible : la salve suivante attend la fenêtre d'anti-rebond avant sa
    première poussée, donc toute poussée réussie ultérieure porte un horodatage
    strictement plus grand.
    """
    apres = [(quand, ligne) for quand, ligne in lire_le_journal(git) if quand >= depuis]
    if not apres:
        return
    plafond = [entree for entree in apres if MARQUEUR_SALVE_INACHEVEE in entree[1]]
    if plafond:
        print("Poussée arrêtée au plafond le %s : toute la salve n'est peut-être pas "
              "partie (elle repartira au prochain commit)."
              % plafond[-1][0].isoformat(timespec="seconds"), file=sys.stderr)
    echecs = [entree for entree in apres if MARQUEUR_SALVE_INACHEVEE not in entree[1]]
    if echecs:
        print("Dernière poussée échouée le %s : le journal en dit le détail."
              % echecs[-1][0].isoformat(timespec="seconds"), file=sys.stderr)


def fraicheur(coffre: Path, heures: int = HEURES_FRAICHEUR) -> int:
    """Dit si la dernière poussée réussie a moins de `heures`.

    Relaie aussi, sur la sortie d'erreur, ce que la dernière poussée réussie n'a
    pas couvert : une suspension en cours (§ C1), une salve arrêtée au plafond,
    une poussée échouée — pour qu'un « à jour » ne taise pas des commits restés
    en local.
    """
    if nom_du_distant(coffre) is None:
        print("Aucun distant configuré pour le dépôt de données du coffre : "
              "rien à surveiller (§7.1).")
        return 0
    git = dossier_git_commun(coffre)
    if git is None:
        print("Le coffre n'est pas un dépôt git : aucune poussée à vérifier.",
              file=sys.stderr)
        return 1
    rappeler_la_suspension(coffre, git)
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
    rappeler_le_journal(git, quand)
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
                           choices=["avant-commit", "apres-commit", "apres-rewrite",
                                    "fraicheur"])
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
    if args.commande == "apres-rewrite":
        # Tiré par le crochet `post-rewrite`, à la fin d'un rebase : la réécriture
        # est terminée, on pousse la pointe finale. (`post-rewrite` tire aussi sur
        # un amend, mais le crochet sort avant — `post-commit` a déjà poussé.)
        return apres_commit(coffre, reecriture_finie=True)
    return fraicheur(coffre, args.heures)


if __name__ == "__main__":
    sys.exit(main())
