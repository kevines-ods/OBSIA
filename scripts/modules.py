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
import socket
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

GABARIT_SESSION_LOG = """# session-log/ — archives

Ce dossier est **archivé** : on n'y écrit plus. Les carnets (§6) le
remplacent comme trace des séances ; les notes antérieures à cette règle
restent lisibles pour l'historique et ne se réécrivent pas — un récit ne se
corrige pas après coup (§11). Les règles sont au §9 de `../VAULT-CONTRACT.md`,
qui fait foi.

Ce dossier est vide à l'installation : les logs décrivent le travail d'une
personne sur sa machine, pas le coffre.
"""


GABARIT_MEMOIRES = """# 0-MEMOIRES/ — deux mémoires, une seule est gelée

Ce dossier en porte deux, et il faut les distinguer :

- **`préférences/` et `<nom-agent>/expériences/`** — la mémoire des agents.
  Elle **vit** : une préférence qui change se corrige sur place, une leçon se
  révise, comme le profil de `0-PERSONNELS/`. `préférences/` est posé par
  l'installation, même vide ; `<nom-agent>/expériences/` naît à la première leçon.
- **`<projet>/<chantier>/`** — les chantiers clos. À la clôture, le **dossier
  entier** du chantier quitte `0-PROJETS/` pour venir ici, tel quel : le résumé
  devient un bilan avec une section « État », les carnets passent
  `statut: clos`, les documents suivent. Ces dossiers-là sont **gelés** : plus
  rien n'y est modifié, jamais, et le durable a été distillé avant vers
  `0-SAVOIRS/`, `0-MEMOIRES/préférences/` ou `0-MEMOIRES/<nom-agent>/expériences/`.
  Rouvrir un chantier le ramène dans `0-PROJETS/`, sans copie laissée derrière.

Un nom de premier niveau ici est donc, et rien d'autre : `préférences`, le nom
d'un agent, ou un projet gelé. **Un projet ne peut s'appeler ni `préférences` ni
le nom d'un agent** — la collision rendrait la mémoire des agents indistinguable
d'un chantier gelé, et le contrôle la refuse.

Les règles sont au §6 de `OBSIA/IA/system/VAULT-CONTRACT.md`, qui fait foi.
"""


def sous_un_lien(depart: Path, chemin: Path) -> Path | None:
    """Le premier maillon de `chemin`, sous `depart`, qui est un lien symbolique.

    Un lien ne se suit ni en lecture ni en écriture : écrire au travers, c'est
    écrire ailleurs que dans le coffre qu'on croit remplir. Les deux scripts
    d'installation s'en servent avant chaque geste.
    """
    courant = depart
    for morceau in chemin.relative_to(depart).parts:
        courant = courant / morceau
        if courant.is_symlink():
            return courant
    return None


def nom_machine() -> str:
    """Le nom de cette machine, tel qu'il s'écrit dans `obsia.local.yml` (§7.1).

    Écrit à l'installation, relu par le pre-commit du dépôt de données : les deux
    passent par ici, sinon le refus « ce n'est pas l'écrivain » tomberait sur la
    machine qui l'est.
    """
    return socket.gethostname() or os.environ.get("HOSTNAME", "")


def designation(chemin: Path, base: Path) -> str:
    """Nomme un chemin pour un humain : relatif à `base` quand il y est, absolu sinon."""
    try:
        return str(chemin.relative_to(base))
    except ValueError:
        return str(chemin)


def ecrire_gabarits_dinstance(racine: Path) -> None:
    """Pose dans le dépôt les fichiers que le contrat exige.

    Reste ici ce qui appartient au produit : le README de `session-log/`, qui
    dit à quoi la zone archivée sert. Le gabarit de profil n'est plus un fichier
    du dépôt — la mémoire est sortie (§7.1) : c'est `ecrire_memoire_du_coffre`
    qui le pose, dans le coffre parent.

    Rien n'est écrasé : une réinstallation ne doit pas emporter le travail de qui
    utilise déjà le coffre. C'est leur absence qui déclenche l'écriture. Rien
    n'est écrit non plus à travers un lien : le gabarit atterrirait ailleurs.
    """
    # La bascule est faite : `session-log/` a quitté le dépôt pour
    # `0-MEMOIRES/obsia/session-log/` (§11). Le recréer ici ferait échouer
    # `verifier_coffre.py` passé le 2026-12-31 : il n'y a plus rien à poser.
    return


def ancien_profil_rempli(coffre: Path, produit: Path | None = None) -> Path | None:
    """Un profil d'avant la migration, et **rempli**.

    Deux emplacements possibles, l'un dans le dépôt produit, l'autre dans le
    coffre sous son ancien nom à tiret. Un profil identique au gabarit vide ne
    compte pas : il n'y a rien à préserver. Un lien symbolique est ignoré — on
    ne lit pas au travers (§13).
    """
    candidats = [coffre / "-PERSONNELS/profil-utilisateur.md"]
    if produit is not None:
        candidats.insert(0, produit / "mémoire/profil-utilisateur.md")
    for chemin in candidats:
        if chemin.is_symlink() or not chemin.is_file():
            continue
        try:
            texte = chemin.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return chemin
        if texte.strip() != GABARIT_PROFIL_UTILISATEUR.strip():
            return chemin
    return None


def ecrire_memoire_du_coffre(coffre: Path, produit: Path | None = None) -> list[str]:
    """Prépare la mémoire d'un coffre parent : `0-PERSONNELS/` et `0-MEMOIRES/`.

    Un coffre tiers n'a pas forcément la structure de mémoire du §6 : l'installeur
    la pose — le profil en gabarit, le README qui dit ce que `0-MEMOIRES/` garde,
    et `0-MEMOIRES/préférences/`, où la première préférence viendra se ranger.
    Comme `ecrire_gabarits_dinstance`, **rien n'est écrasé** — une réinstallation
    ne doit pas emporter ce qui a déjà été écrit — et rien ne s'écrit à travers un
    lien symbolique.

    **Jamais de profil vide devant un ancien profil rempli.** Tant que la
    migration n'a pas déplacé le profil d'avant (`mémoire/profil-utilisateur.md`
    dans le dépôt produit, ou `-PERSONNELS/…` dans le coffre), poser un gabarit
    vide à côté le masquerait : le texte rendu n'est plus lu nulle part. On
    préfère refuser et le dire. La liste rendue porte les refus, que l'appelant
    affiche.
    """
    refus = []
    ancien = ancien_profil_rempli(coffre, produit)
    for relatif, gabarit in (("0-PERSONNELS/profil-utilisateur.md",
                              GABARIT_PROFIL_UTILISATEUR),
                             ("0-MEMOIRES/README.md", GABARIT_MEMOIRES)):
        chemin = coffre / relatif
        if chemin.is_file() or sous_un_lien(coffre, chemin) is not None:
            continue
        if relatif.endswith("profil-utilisateur.md") and ancien is not None:
            refus.append(
                "profil non créé : un profil rempli existe déjà en %s. La migration "
                "le déplacera vers 0-PERSONNELS/profil-utilisateur.md ; poser un "
                "gabarit vide ici le masquerait." % designation(ancien, coffre))
            continue
        try:
            chemin.parent.mkdir(parents=True, exist_ok=True)
            chemin.write_text(gabarit, encoding="utf-8")
        except OSError as echec:
            # Un coffre en lecture seule n'est pas une raison d'échouer : on le
            # dit, et l'installeur continue ce qu'il a à faire ailleurs.
            refus.append("non écrit : %s (%s)." % (relatif, echec.strerror or echec))

    # `préférences/` est vide tant que rien n'a été préféré : Git n'en gardera
    # rien, mais l'agent qui écrit sa première préférence le trouve déjà là.
    preferences = coffre / "0-MEMOIRES" / "préférences"
    if not preferences.is_dir() and sous_un_lien(coffre, preferences) is None:
        try:
            preferences.mkdir(parents=True, exist_ok=True)
        except OSError as echec:
            refus.append("non créé : 0-MEMOIRES/préférences/ (%s)."
                         % (echec.strerror or echec))
    return refus


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


def modules_inconnus(modules: list[dict], retenus) -> set[str]:
    """Les noms cités qui ne sont pas au catalogue."""
    return set(retenus) - {m["name"] for m in modules if m.get("name")}


def signaler_modules_inconnus(modules: list[dict], retenus,
                              source: str = NOM_PROFIL) -> set[str]:
    """Signale sur stderr les noms cités absents du catalogue (§13).

    Un nom inconnu ne désigne rien : la sélection reste ce qu'elle est, et ce
    n'est pas une erreur — un profil peut citer un module qu'une version
    ultérieure apportera. Mais faute de ce signal, un profil fautif reste
    muet, et rien ne dit pourquoi le coffre installé est plus maigre que
    prévu. Le catalogue connu est rappelé pour qu'on puisse corriger sans
    relire l'index.
    """
    inconnus = modules_inconnus(modules, retenus)
    if inconnus:
        connus = sorted(m["name"] for m in modules if m.get("name"))
        print("Modules inconnus dans %s : %s — sans effet (catalogue : %s)"
              % (source, ", ".join(sorted(inconnus)), ", ".join(connus)),
              file=sys.stderr)
    return inconnus


def modules_actifs(racine: Path = RACINE_DEFAUT) -> set[str] | None:
    """Les modules retenus, ou None quand tout l'est (absence de profil)."""
    profil = lire_profil(racine)
    if profil is None:
        return None
    modules = lire_modules(racine)
    signaler_modules_inconnus(modules, profil.get("modules", []))
    return resoudre_dependances(modules, profil.get("modules", []))


def ecrire_profil(racine: Path, actifs, systeme: dict, mode: str,
                  coffre_parent: str | None = None,
                  coffre_distant: str | None = None) -> Path:
    """Écrit `obsia.local.yml`. Non versionné : il décrit cette machine-ci.

    `coffre_distant`, quand il est déjà déclaré, est repris tel quel : le
    réinstaller ne doit pas l'effacer (§7.1)."""
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
    machine = nom_machine()
    if machine:
        # L'écrivain du dépôt de données du coffre (§7.1). L'installeur l'écrit
        # ici, sur la machine concernée et hors de tout dépôt versionné : c'est
        # ce qui autorise son pre-commit, et rien d'autre.
        L.append("ecrivain: %s" % machine)
    L += [""]
    if coffre_distant:
        L.append("coffre_distant: %s" % coffre_distant)
    else:
        L += [
            "# Décommenter pour faire pousser le dépôt de données du coffre vers un",
            "# distant (§7.1) ; l'installeur l'enregistre alors comme `origin`, et ne",
            "# pousse jamais lui-même.",
            "# coffre_distant: ssh://nas/volume/coffre.git",
        ]
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

#: Ce qui trahit un coffre — un coffre de travail, ou la cible d'une publication.
#: Source **unique** : `publier.py` et `verifier_coffre.py` l'importent, si bien
#: qu'un marqueur oublié ici ne l'est plus nulle part. Les deux noms du même
#: dossier y sont — `0-…` depuis la bascule (§7.1), `-…` pour les coffres qui ne
#: l'ont pas finie ; ces derniers disparaissent à la fin de la migration du
#: chantier `souverainete-des-donnees`. `.obsidian` et `_MAINTENANCE` sont
#: l'entourage du coffre, `Mon coffre` en est le nom d'écriture (§7.1).
MARQUEURS_COFFRE = (".obsidian", "_MAINTENANCE", "Mon coffre",
                    "0-SAVOIRS", "0-EN-VRAC", "0-DOCUMENTS", "0-PROJETS",
                    "0-MEMOIRES", "0-PERSONNELS",
                    "-SAVOIRS", "-EN-VRAC", "-DOCUMENTS", "-PROJETS",
                    "-PERSONNELS")


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
