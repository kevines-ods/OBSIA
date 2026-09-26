#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lecture du catalogue de modules et du profil d'installation.

Le coffre est un **catalogue** : tout y est déclaré, rien n'oblige à tout
retenir. Un module (`IA/system/modules/<nom>.md`) regroupe des agents, des
skills, des MCP et des tâches qui n'ont de sens qu'ensemble. Le profil
d'installation (`obsia.local.yml`, non versionné) dit lesquels sont retenus
sur *cette* machine.

Sans profil, tout est actif : c'est l'état du dépôt de distribution, et c'est
ce que la CI vérifie. Le §13 du contrat fait foi.

Bibliothèque standard uniquement — le coffre ne doit dépendre d'aucune
installation pour être vérifiable.
"""

import os
import shutil
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generer_prompt import (RACINE_DEFAUT, collecter, fichiers_declaratifs,
                            lire_frontmatter)

NOM_PROFIL = "obsia.local.yml"
SCHEMA = 1

#: Les genres déclaratifs et où ils vivent, dans l'ordre où on les traite.
GENRES = (
    ("agent", "IA/agents"),
    ("skill", "IA/skills"),
    ("mcp", "IA/MCP"),
    ("tâche", "IA/tâches"),
)


#: Gabarits des fichiers propres à l'instance. Ils vivent ici parce que
#: l'installeur (mode copie) et le publieur (miroir public) doivent écrire
#: exactement les mêmes : deux copies divergeraient à la première correction.
GABARIT_PROFIL_UTILISATEUR = """# Profil utilisateur

Faits durables sur la personne qui utilise ce coffre. Cette note évite de
redemander à chaque session ce qui a déjà été dit. Elle n'est pas datée : elle
est **mise à jour sur place** quand un fait change, pas dupliquée.

## Statut
🟡 Vide — à remplir au fil des premières sessions.

---

## Poste de travail

À compléter : distribution, gestionnaire de paquets, environnement de bureau.
Le profil d'installation en contient déjà une partie.

## Rapport au code

À compléter : ce que l'utilisateur attend qu'on lui explique, et ce qu'il sait
déjà.

## Valeurs

À compléter.

## Coffre Obsidian

À compléter si le dépôt est cloné dans un coffre parent (§7 du contrat).

## Infrastructure

À compléter. Jamais d'adresse IP, de nom d'hôte interne ni d'identifiant.

---

## Ce qui n'entre jamais dans cette note

Adresse de courriel, mots de passe, jetons, clés, adresses IP privées, noms
d'hôtes internes.
"""

GABARIT_SESSION_LOG = """# session-log/ — journal des sessions

Une note par séance de travail, nommée `AAAA-MM-JJ.md` : décisions prises,
fichiers modifiés, questions restées ouvertes, et **toute action à effet
externe** — appel de MCP quel que soit son `permission`, correction appliquée à
un système. Les règles sont au §9 de `../VAULT-CONTRACT.md`, qui fait foi.

Ce dossier est vide à l'installation : les logs décrivent le travail d'une
personne sur sa machine, pas le coffre.
"""


def ecrire_gabarits_dinstance(racine: Path) -> None:
    """Pose les fichiers que le contrat exige et que l'instance doit remplir.

    `profil-utilisateur.md` est cité par le §6 : absent, il ferait échouer le
    contrôle des chemins. Vide mais présent, il dit aussi à quoi il sert.
    """
    memoire = racine / "mémoire"
    memoire.mkdir(parents=True, exist_ok=True)
    (memoire / "profil-utilisateur.md").write_text(
        GABARIT_PROFIL_UTILISATEUR, encoding="utf-8")

    log = racine / "IA" / "system" / "session-log"
    log.mkdir(parents=True, exist_ok=True)
    (log / "README.md").write_text(GABARIT_SESSION_LOG, encoding="utf-8")


# ------------------------------------------------------------ YAML minimal

def lire_yaml_simple(texte: str) -> dict:
    """Scalaires et listes à tirets, rien d'autre.

    Même sous-ensemble que le frontmatter du §5, sans les délimiteurs `---`.
    Suffisant pour `obsia.local.yml`, qu'un script écrit et qu'un humain
    relit — pas pour du YAML quelconque, qu'on n'écrit jamais ici.
    """
    donnees: dict = {}
    cle_liste: str | None = None

    for ligne in texte.splitlines():
        nu = ligne.strip()
        if not nu or nu.startswith("#"):
            continue

        if nu.startswith("- ") and cle_liste:
            donnees[cle_liste].append(nu[2:].strip().strip("\"'"))
            continue

        if ":" not in nu:
            continue

        cle, _, valeur = nu.partition(":")
        cle, valeur = cle.strip(), valeur.strip()

        if not valeur:
            donnees[cle] = []
            cle_liste = cle
            continue

        cle_liste = None
        if valeur.lower() in ("true", "false"):
            donnees[cle] = valeur.lower() == "true"
        elif valeur.isdigit():
            donnees[cle] = int(valeur)
        else:
            donnees[cle] = valeur.strip("\"'")

    return donnees


# ------------------------------------------------------------------ modules

def dossier_modules(racine: Path = RACINE_DEFAUT) -> Path:
    return racine / "IA" / "system" / "modules"


def lire_modules(racine: Path = RACINE_DEFAUT) -> list[dict]:
    """Les modules du catalogue, triés : le noyau d'abord, puis par nom."""
    dossier = dossier_modules(racine)
    if not dossier.is_dir():
        return []

    modules = []
    for chemin in sorted(dossier.glob("*.md")):
        fm = lire_frontmatter(chemin)
        if fm and fm.get("kind") == "module":
            fm["_fichier"] = chemin.name
            fm.setdefault("requiert", [])
            fm.setdefault("sondes", [])
            modules.append(fm)

    return sorted(modules, key=lambda m: (not m.get("essentiel"), m["name"]))


def essentiels(modules: list[dict]) -> set[str]:
    return {m["name"] for m in modules if m.get("essentiel")}


def resoudre_dependances(modules: list[dict], retenus) -> set[str]:
    """Ferme la sélection sur `requiert`, et y ajoute toujours les essentiels.

    Un module retenu dont une dépendance manque produirait un coffre qui
    référence des fichiers absents. Plutôt que de refuser, on complète : c'est
    ce que « requiert » veut dire.
    """
    par_nom = {m["name"]: m for m in modules}
    resolu = set(retenus) | essentiels(modules)

    change = True
    while change:
        change = False
        for nom in list(resolu):
            for besoin in par_nom.get(nom, {}).get("requiert", []):
                if besoin not in resolu and besoin in par_nom:
                    resolu.add(besoin)
                    change = True

    return resolu


# ------------------------------------------------------------- appartenance

def appartenance(racine: Path = RACINE_DEFAUT) -> dict[tuple[str, str], str]:
    """(genre, nom) → module déclaré, pour tout le catalogue."""
    carte = {}
    for genre, sous in GENRES:
        for fm in collecter(racine / sous, genre):
            if fm.get("module"):
                carte[(genre, fm["name"])] = fm["module"]
    return carte


def fichiers_du_module(racine: Path, nom_module: str) -> list[Path]:
    """Tous les fichiers déclaratifs d'un module, chemins relatifs à la racine.

    Pour un skill en forme dossier, c'est le dossier entier qui appartient au
    module : `references/`, `scripts/` et `assets/` ne se séparent pas de leur
    point d'entrée.
    """
    trouves = []
    for _genre, sous in GENRES:
        dossier = racine / sous
        for chemin in fichiers_declaratifs(dossier):
            fm = lire_frontmatter(chemin)
            if not fm or fm.get("module") != nom_module:
                continue
            # forme dossier : le dossier entier, pas seulement le point d'entrée
            cible = chemin.parent if chemin.parent != dossier else chemin
            trouves.append(cible.relative_to(racine))
    return sorted(set(trouves))


# -------------------------------------------------------------------- profil

def chemin_profil(racine: Path = RACINE_DEFAUT) -> Path:
    return racine / NOM_PROFIL


def lire_profil(racine: Path = RACINE_DEFAUT) -> dict | None:
    """Le profil d'installation, ou None s'il n'y en a pas.

    Pas de profil = catalogue complet. C'est l'état du dépôt de distribution,
    et l'état sous lequel la CI vérifie le coffre.
    """
    chemin = chemin_profil(racine)
    if not chemin.is_file():
        return None
    profil = lire_yaml_simple(chemin.read_text(encoding="utf-8"))
    profil.setdefault("modules", [])
    return profil


def modules_actifs(racine: Path = RACINE_DEFAUT) -> set[str] | None:
    """Les modules retenus, ou None quand tout l'est (absence de profil)."""
    profil = lire_profil(racine)
    if profil is None:
        return None
    return resoudre_dependances(lire_modules(racine), profil.get("modules", []))


def ecrire_profil(racine: Path, actifs, systeme: dict, mode: str,
                  coffre_parent: str | None = None) -> Path:
    """Écrit `obsia.local.yml`. Non versionné : il décrit cette machine-ci."""
    modules = lire_modules(racine)
    ordre = [m["name"] for m in modules if m["name"] in actifs]

    L = [
        "# obsia.local.yml — profil d'installation OBSIA.",
        "#",
        "# Écrit par scripts/installer.py, relisible et modifiable à la main.",
        "# NON VERSIONNÉ : il décrit cette machine, pas le coffre (§13).",
        "# Le rejouer après modification : python3 scripts/installer.py --rejouer",
        "",
        "schema: %d" % SCHEMA,
        "mode: %s" % mode,
    ]
    if coffre_parent:
        L.append("coffre_parent: %s" % coffre_parent)
    for cle in ("distribution", "gestionnaire_paquets", "conteneurs", "init"):
        if systeme.get(cle):
            L.append("%s: %s" % (cle, systeme[cle]))
    L += ["", "modules:"]
    L += ["  - %s" % nom for nom in ordre]
    L.append("")

    chemin = chemin_profil(racine)
    chemin.write_text("\n".join(L), encoding="utf-8")
    return chemin


# -------------------------------------------------------------------- sondes

def _os_release() -> dict:
    donnees = {}
    chemin = Path("/etc/os-release")
    if not chemin.is_file():
        return donnees
    for ligne in chemin.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" in ligne:
            cle, _, valeur = ligne.partition("=")
            donnees[cle.strip()] = valeur.strip().strip("\"'")
    return donnees


def evaluer_sonde(sonde: str, racine: Path) -> bool:
    """Évalue une sonde déclarative. Ne lit que le système, n'écrit jamais.

    Quatre formes, et pas une de plus — une sonde qui exécuterait du code
    arbitraire ferait d'un fichier du catalogue un vecteur d'exécution :

        commande:<nom>      le binaire est dans le PATH
        fichier:<chemin>    le chemin existe (`~` développé)
        distribution:<id>   ID ou ID_LIKE de /etc/os-release
        parent:<nom>        le dossier existe à côté du dépôt (coffre parent)

    Aucune n'ouvre le réseau : l'installeur ne doit rien émettre.
    """
    genre, _, valeur = sonde.partition(":")
    valeur = valeur.strip()

    if genre == "commande":
        return shutil.which(valeur) is not None
    if genre == "fichier":
        return Path(valeur).expanduser().exists()
    if genre == "distribution":
        rel = _os_release()
        ids = [rel.get("ID", "")] + rel.get("ID_LIKE", "").split()
        return valeur in [i for i in ids if i]
    if genre == "parent":
        return (racine.parent / valeur).exists()

    return False


def sonder(module: dict, racine: Path) -> bool | None:
    """True / False si le module a des sondes, None s'il n'en déclare aucune.

    None n'est pas « non » : c'est « la machine ne peut pas répondre ». La
    distinction compte, parce que l'installeur propose un défaut différent
    dans les deux cas.
    """
    sondes = module.get("sondes") or []
    if not sondes:
        return None
    return any(evaluer_sonde(s, racine) for s in sondes)


GESTIONNAIRES = (("pacman", "pacman"), ("apt", "apt"), ("dnf", "dnf"),
                 ("zypper", "zypper"), ("apk", "apk"), ("emerge", "portage"))

MARQUEURS_COFFRE = (".obsidian", "-SAVOIRS", "-EN-VRAC", "-PROJETS")


def detecter_systeme(racine: Path = RACINE_DEFAUT) -> dict:
    """Ce que la machine dit d'elle-même. Lecture seule, sans réseau."""
    rel = _os_release()
    systeme = {
        "distribution": rel.get("ID") or "inconnue",
        "nom_distribution": rel.get("PRETTY_NAME") or rel.get("NAME") or "inconnue",
        "gestionnaire_paquets": next(
            (nom for binaire, nom in GESTIONNAIRES if shutil.which(binaire)), ""),
        "conteneurs": next(
            (b for b in ("docker", "podman") if shutil.which(b)), ""),
        "init": "systemd" if Path("/run/systemd/system").is_dir() else "",
        "coffre_parent": "",
    }

    parent = racine.parent
    if any((parent / m).exists() for m in MARQUEURS_COFFRE):
        systeme["coffre_parent"] = parent.name

    return systeme
