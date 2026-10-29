#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Applique les registres `IA/tâches/` et, s'il existe, celui du coffre parent
(`Mon coffre/0-PROJETS/tâches-planifiées/`) aux timers systemd utilisateur.

Les deux registres font foi, ensemble (VAULT-CONTRACT.md §12) ; ce script en tire les instances
locales et rapporte les écarts. Il ne touche QUE les unités préfixées
`obsia-` : ce que l'utilisateur a planifié par ailleurs ne le regarde pas.

Par défaut il n'écrit rien et affiche le tableau des écarts — c'est le preview
qu'impose le §2 avant toute action multi-fichiers. `--appliquer` exécute.

Contrairement aux scripts de `scripts/`, celui-ci **dépend d'un exécutant**
(systemd utilisateur). C'est assumé : il vit dans le skill qui s'en sert, pas
dans l'outillage du coffre, qui doit rester vérifiable sans rien installer.

Usage :
    python3 IA/skills/cron/scripts/appliquer_taches.py             # aperçu
    python3 IA/skills/cron/scripts/appliquer_taches.py --appliquer
    python3 IA/skills/cron/scripts/appliquer_taches.py --tache NOM [--appliquer]
    python3 IA/skills/cron/scripts/appliquer_taches.py --config    # gabarit
"""

import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.dont_write_bytecode = True
RACINE = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(RACINE / "scripts"))

from generer_prompt import lire_frontmatter          # noqa: E402  (après sys.path)
from modules import MARQUEURS_COFFRE                 # noqa: E402  (même liste que l'installeur)


def _est_un_coffre_parent(chemin: Path) -> bool:
    try:
        noms = set(os.listdir(chemin))
    except OSError:
        return False
    return bool(noms & set(MARQUEURS_COFFRE))


def _coffre_parent(racine: Path) -> Path:
    """Le coffre parent, même lancé depuis un worktree lié.

    `racine.parent` suffit dans un clone ordinaire, mais vaut le hangar à
    worktrees (`~/obsia-worktrees/`) depuis un worktree lié — même piège que
    documenté dans `scripts/publier.depot_reel`. On retrouve d'abord le clone
    principal via le dossier git commun à tous les worktrees, puis son parent.
    """
    try:
        res = subprocess.run(["git", "-C", str(racine), "rev-parse", "--git-common-dir"],
                             capture_output=True, text=True, check=True)
        commun = Path(res.stdout.strip())
        if not commun.is_absolute():
            commun = racine / commun
        return commun.resolve().parent.parent
    except (subprocess.CalledProcessError, OSError):
        return racine.parent


TACHES = RACINE / "IA" / "tâches"
#: Registre privé, dans le coffre parent — tâches propres à cette installation :
#: une machine précise du parc de l'utilisateur, ou son mainteneur (§12 du
#: contrat).
COFFRE_PARENT = _coffre_parent(RACINE)
TACHES_COFFRE = COFFRE_PARENT / "0-PROJETS" / "tâches-planifiées"
UNITES = Path.home() / ".config" / "systemd" / "user"
ENVELOPPES = Path.home() / ".local" / "share" / "obsia" / "taches"
ARCHIVE = Path.home() / ".local" / "share" / "obsia" / "archive"
CONFIG = Path.home() / ".config" / "obsia" / "appliquer.conf"

GABARIT_CONFIG = """\
# Configuration locale de appliquer_taches.py — NON versionnée, à dessein :
# elle nomme un harness — le §3 le permet hors du produit, tant qu'aucun nom ni
# comportement de harness n'y conditionne le fonctionnement.

# Commande qui lance un agent avec une instruction.
# `{instruction}` est remplacé par le chemin du fichier contenant l'instruction
# complète. Sans ce marqueur, le fichier est fourni sur l'entrée standard.
commande_agent =
"""

JOURS = ("Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat")


# ------------------------------------------------------------------- registre

def corps_section(chemin: Path, titre: str) -> str:
    """Le contenu d'une section `## <titre>`, jusqu'au titre suivant."""
    texte = chemin.read_text(encoding="utf-8")
    debut = re.search(r"^## +%s *$" % re.escape(titre), texte, re.M)
    if not debut:
        return ""
    reste = texte[debut.end():]
    suite = re.search(r"^## ", reste, re.M)
    return (reste[:suite.start()] if suite else reste).strip()


def lire_registre() -> list[dict]:
    """Les deux registres (§12) — `IA/tâches/` puis le registre privé du coffre.

    Un nom présent aux deux est un doublon de déclaration : `main()` le
    refuse avant d'écrire quoi que ce soit, plutôt que de laisser le second
    silencieusement écraser le premier.

    Si le coffre parent existe mais n'a pas ce registre, c'est signalé sur
    `stderr` plutôt que silencieusement ignoré — sans quoi une tâche propre à
    cette installation, déplacée là et jamais relue, disparaîtrait sans que
    personne ne le remarque.
    """
    if not TACHES_COFFRE.is_dir() and _est_un_coffre_parent(COFFRE_PARENT):
        print("Avertissement : coffre parent trouvé (%s), mais aucun registre "
              "`0-PROJETS/tâches-planifiées/` — aucune tâche propre à cette "
              "installation ne sera lue." % COFFRE_PARENT, file=sys.stderr)
    taches = []
    vus: dict[str, Path] = {}
    doublons = []
    for dossier in (TACHES, TACHES_COFFRE):
        for chemin in sorted(dossier.glob("*.md")) if dossier.is_dir() else []:
            fm = lire_frontmatter(chemin)
            if not fm or fm.get("kind") != "tâche":
                continue
            nom = fm.get("name")
            if nom in vus:
                doublons.append((nom, vus[nom], chemin))
                continue
            vus[nom] = chemin
            fm["_chemin"] = chemin
            titre = "Instruction" if fm.get("mode") == "agent" else "Commande"
            fm["_corps"] = corps_section(chemin, titre)
            taches.append(fm)
    if doublons:
        raise ValueError("\n".join(
            "%s : déclarée aux deux registres (%s et %s)" % (n, a, b)
            for n, a, b in doublons))
    return taches


# ------------------------------------------------------------- cron → systemd

def _champ(valeur: str, base_pas: str) -> str:
    """Traduit un champ cron en son équivalent systemd."""
    if valeur.startswith("*/"):
        return "%s/%s" % (base_pas, valeur[2:])
    return valeur


def cron_vers_oncalendar(quand: str) -> str | None:
    """`0 9 * * 1` → `Mon *-*-* 09:00:00`. None si la forme n'est pas gérée."""
    champs = quand.split()
    if len(champs) != 5:
        return None
    minute, heure, jour, mois, semaine = champs

    if not all(re.fullmatch(r"[\d*/,\-]+", c) for c in champs):
        return None

    mn = _champ(minute, "0")
    hr = _champ(heure, "0")
    if mn.isdigit():
        mn = "%02d" % int(mn)
    if hr.isdigit():
        hr = "%02d" % int(hr)

    # systemd normalise `*-*-1` en `*-*-01` : produire d'emblée sa forme
    # normale évite de croire à un écart au moment de comparer.
    jour = "%02d" % int(jour) if jour.isdigit() else jour
    mois = "%02d" % int(mois) if mois.isdigit() else mois

    prefixe = ""
    if semaine != "*":
        noms = []
        for morceau in semaine.split(","):
            if "-" in morceau:
                a, b = morceau.split("-", 1)
                if not (a.isdigit() and b.isdigit()):
                    return None
                noms.append("%s..%s" % (JOURS[int(a) % 7], JOURS[int(b) % 7]))
            elif morceau.isdigit():
                noms.append(JOURS[int(morceau) % 7])
            else:
                return None
        prefixe = ",".join(noms) + " "

    return "%s*-%s-%s %s:%s:00" % (prefixe, mois, jour, hr, mn)


def calendrier_valide(expression: str) -> bool:
    """Fait valider l'expression par systemd lui-même, quand il est là."""
    if not shutil.which("systemd-analyze"):
        return True
    res = subprocess.run(["systemd-analyze", "calendar", expression],
                         capture_output=True, text=True)
    return res.returncode == 0


# ------------------------------------------------------------------- instances

def instances_locales() -> dict[str, dict]:
    """Les unités `obsia-*.timer` posées sur cette machine, lues sur disque.

    On lit les fichiers plutôt que d'interroger systemd : le diagnostic reste
    possible là où le bus n'est pas joignable (conteneur, session sans dbus).
    """
    trouvees = {}
    for timer in sorted(UNITES.glob("obsia-*.timer")) if UNITES.is_dir() else []:
        nom = timer.stem[len("obsia-"):]
        texte = timer.read_text(encoding="utf-8")
        m = re.search(r"^OnCalendar=(.+)$", texte, re.M)
        trouvees[nom] = {
            "timer": timer,
            "service": UNITES / ("obsia-%s.service" % nom),
            "oncalendar": m.group(1).strip() if m else "",
        }
    return trouvees


# --------------------------------------------------------------------- écarts

def ecarts(registre: list[dict], locales: dict[str, dict]) -> list[tuple]:
    """(nom, verdict, explication, geste) — verdict en majuscules si action."""
    lignes = []
    vus = set()

    for t in registre:
        nom = t["name"]
        vus.add(nom)
        ici = locales.get(nom)
        attendu = cron_vers_oncalendar(t.get("quand", ""))

        if t.get("exécutant") == "harness":
            if ici:
                lignes.append((nom, "DOUBLON",
                               "déclarée chez le harness, mais un timer local existe",
                               "retirer le timer local"))
            else:
                lignes.append((nom, "harness",
                               "déclarée chez le harness", "vérifier de son côté"))
            continue

        if not t.get("actif"):
            if ici:
                lignes.append((nom, "À RETIRER", "suspendue au registre",
                               "désactiver et archiver le timer"))
            else:
                lignes.append((nom, "suspendue", "suspendue, non instanciée", "rien"))
            continue

        if not ici:
            lignes.append((nom, "À CRÉER", "déclarée, aucune instance",
                           "poser le service et le timer"))
        elif attendu and ici["oncalendar"] != attendu:
            lignes.append((nom, "À CORRIGER",
                           "horaire divergent (%s ≠ %s)" % (ici["oncalendar"], attendu),
                           "réécrire le timer"))
        else:
            lignes.append((nom, "à jour", "instance conforme", "rien"))

    for nom in sorted(set(locales) - vus):
        lignes.append((nom, "ORPHELINE", "instance sans tâche au registre",
                       "déclarer la tâche, ou retirer l'instance à la main"))
    return lignes


# ------------------------------------------------------------------ écriture

def lire_config() -> dict:
    reglages = {}
    if CONFIG.is_file():
        for ligne in CONFIG.read_text(encoding="utf-8").splitlines():
            nu = ligne.strip()
            if not nu or nu.startswith("#") or "=" not in nu:
                continue
            cle, _, valeur = nu.partition("=")
            reglages[cle.strip()] = valeur.strip()
    return reglages


def ecrire_enveloppe(t: dict, config: dict) -> Path | None:
    """Le script réellement lancé par le service. None si rien n'est lançable."""
    ENVELOPPES.mkdir(parents=True, exist_ok=True)
    nom = t["name"]
    enveloppe = ENVELOPPES / ("obsia-%s.sh" % nom)

    if t.get("mode") == "commande":
        corps = t["_corps"]
        # le corps est de la prose : on n'exécute que les blocs ```bash / ```sh
        blocs = re.findall(r"```(?:bash|sh)?\n(.*?)```", corps, re.S)
        commande = "\n".join(b.strip() for b in blocs) or corps
        contenu = "#!/bin/sh\nset -eu\ncd %s\n%s\n" % (shell_quote(str(RACINE)), commande)
    else:
        modele = config.get("commande_agent", "")
        if not modele:
            return None
        instruction = ENVELOPPES / ("obsia-%s.instruction.txt" % nom)
        instruction.write_text(t["_corps"] + "\n", encoding="utf-8")
        if "{instruction}" in modele:
            appel = modele.replace("{instruction}", shell_quote(str(instruction)))
        else:
            appel = "%s < %s" % (modele, shell_quote(str(instruction)))
        contenu = "#!/bin/sh\nset -eu\ncd %s\n%s\n" % (shell_quote(str(RACINE)), appel)

    enveloppe.write_text(contenu, encoding="utf-8")
    enveloppe.chmod(0o755)
    return enveloppe


def shell_quote(valeur: str) -> str:
    return "'" + valeur.replace("'", "'\\''") + "'"


def poser(t: dict, config: dict) -> tuple[bool, str]:
    """Écrit service + timer. Renvoie (succès, compte rendu d'une ligne)."""
    nom = t["name"]
    oncalendar = cron_vers_oncalendar(t.get("quand", ""))
    if not oncalendar:
        return False, "%s : `quand: %s` non convertible en OnCalendar — ignorée" % (
            nom, t.get("quand"))
    if not calendrier_valide(oncalendar):
        return False, "%s : systemd refuse « %s » — ignorée" % (nom, oncalendar)

    enveloppe = ecrire_enveloppe(t, config)
    if enveloppe is None:
        return False, ("%s : `mode: agent` sans `commande_agent` configurée — "
                       "ignorée (voir --config)" % nom)

    UNITES.mkdir(parents=True, exist_ok=True)
    (UNITES / ("obsia-%s.service" % nom)).write_text(
        "[Unit]\nDescription=OBSIA — %s\n\n"
        "[Service]\nType=oneshot\nExecStart=%s\n" % (t.get("description", nom), enveloppe),
        encoding="utf-8")
    (UNITES / ("obsia-%s.timer" % nom)).write_text(
        "[Unit]\nDescription=OBSIA — déclenche %s\n\n"
        "[Timer]\nOnCalendar=%s\nPersistent=true\n\n"
        "[Install]\nWantedBy=timers.target\n" % (nom, oncalendar),
        encoding="utf-8")
    return True, "%s : posée (%s, fuseau %s)" % (nom, oncalendar, t.get("fuseau", "?"))


def retirer(nom: str, locale: dict) -> str:
    """Désactive puis archive — hors du dépôt, qui est public."""
    systemctl("disable", "--now", "obsia-%s.timer" % nom)
    dossier = ARCHIVE / ("%s-%s" % (date.today().isoformat(), nom))
    dossier.mkdir(parents=True, exist_ok=True)
    for chemin in (locale["timer"], locale["service"]):
        if chemin.is_file():
            shutil.move(str(chemin), str(dossier / chemin.name))
    return "%s : retirée, archivée dans %s" % (nom, dossier)


def systemctl(*args) -> bool:
    if not shutil.which("systemctl"):
        return False
    res = subprocess.run(["systemctl", "--user", *args], capture_output=True, text=True)
    return res.returncode == 0


# ----------------------------------------------------------------------- main

def afficher(lignes: list[tuple]) -> int:
    if not lignes:
        print("Registre vide et aucune instance `obsia-*`. Rien à faire.")
        return 0
    largeur = max(len(l[0]) for l in lignes)
    a_faire = 0
    for nom, verdict, explication, geste in lignes:
        marque = "→" if verdict.isupper() else " "
        if verdict.isupper():
            a_faire += 1
        print("%s %-*s  %-11s %s" % (marque, largeur, nom, verdict, explication))
        if verdict.isupper():
            print("%s%-*s  %-11s %s" % ("  ", largeur, "", "", "geste : " + geste))
    return a_faire


def tache_demandee(argv: list[str]) -> tuple[bool, str | None]:
    """(présente, nom) pour `--tache NOM` ou `--tache=NOM`.

    Présente sans nom — `--tache` en dernier, ou suivi d'une autre option —
    rend (True, None) : l'appelant refuse plutôt que de tout poser. Répétée,
    elle lève `ValueError` : une seule tâche à la fois, jamais la dernière
    nommée en silence.
    """
    if sum(a == "--tache" or a.startswith("--tache=") for a in argv) > 1:
        raise ValueError("--tache ne se répète pas")
    for i, arg in enumerate(argv):
        if arg.startswith("--tache="):
            return True, arg.split("=", 1)[1] or None
        if arg == "--tache":
            suite = argv[i + 1] if i + 1 < len(argv) else ""
            return True, (suite if suite and not suite.startswith("-") else None)
    return False, None


def main() -> int:
    if "--config" in sys.argv:
        print("# Gabarit à écrire dans %s\n" % CONFIG)
        print(GABARIT_CONFIG)
        return 0

    appliquer = "--appliquer" in sys.argv
    try:
        registre = lire_registre()
    except ValueError as exc:
        print("Doublon de déclaration — rien n'a été écrit :\n%s" % exc)
        return 2
    locales = instances_locales()
    lignes = ecarts(registre, locales)

    # `--tache NOM` : une seule tâche, posée, corrigée ou retirée — une tâche
    # réservée à une autre machine ne se pose plus avec le reste.
    try:
        filtre, nom_vise = tache_demandee(sys.argv[1:])
    except ValueError:
        print("--tache ne se donne qu'une fois : une seule tâche par passage. "
              "Rien n'a été écrit.")
        return 2
    if filtre:
        if nom_vise is None:
            print("--tache attend un nom de tâche du registre.")
            return 2
        lignes = [l for l in lignes if l[0] == nom_vise]
        if not lignes:
            print("Tâche inconnue : %s — ni au registre `IA/tâches/`, ni au "
                  "registre du coffre, ni parmi les instances `obsia-*`. "
                  "Rien n'a été écrit." % nom_vise)
            return 2

    print("Registre : %d tâche(s) · instances locales `obsia-*` : %d\n"
          % (len(registre), len(locales)))
    a_faire = afficher(lignes)

    if not appliquer:
        print("\nAperçu seulement — rien n'a été écrit (§2). "
              "Relancer avec --appliquer pour exécuter." if a_faire
              else "\nRien à faire.")
        return 0

    if not a_faire:
        print("\nRien à faire.")
        return 0

    print("\nApplication :")
    par_nom = {t["name"]: t for t in registre}
    config = lire_config()
    posees, touche = [], False
    for nom, verdict, _, _ in lignes:
        if verdict in ("À CRÉER", "À CORRIGER"):
            ok, compte_rendu = poser(par_nom[nom], config)
            print("  " + compte_rendu)
            if ok:
                posees.append(nom)
                touche = True
        elif verdict in ("À RETIRER", "DOUBLON"):
            print("  " + retirer(nom, locales[nom]))
            touche = True
        elif verdict == "ORPHELINE":
            print("  %s : laissée en place — une instance sans intention connue "
                  "ne se supprime pas en aveugle" % nom)

    if not touche:
        print("\nRien n'a été écrit : aucune action n'a abouti.")
        return 1

    if systemctl("daemon-reload"):
        for nom in posees:
            systemctl("enable", "--now", "obsia-%s.timer" % nom)
        print("\nsystemd rechargé, %d timer(s) activé(s)." % len(posees))
    else:
        rappel = "    systemctl --user daemon-reload"
        if posees:
            rappel += "".join("\n    systemctl --user enable --now obsia-%s.timer" % n
                              for n in posees)
        print("\nsystemd injoignable depuis ici. Les changements sont sur "
              "disque ; à faire sur la machine :\n" + rappel)
    print("Agent appelant : consigner ces actions au carnet — du chantier ou du jour, à défaut le journal de `_MAINTENANCE/` — (§9).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
