#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Installeur d'OBSIA — ne retient que les modules qui correspondent à la machine.

Le coffre est un catalogue : tout y est déclaré, rien n'oblige à tout retenir.
Cet installeur sonde la machine, montre ce qu'il a trouvé, demande confirmation,
et écrit le profil `obsia.local.yml`. Le §13 du contrat fait foi.

Deux modes, et la différence tient en une phrase :

    en place   les fichiers restent tous là ; le prompt système et l'`AGENTS.md`
               qui l'accompagne sont réduits au profil. Les index, eux, sont
               versionnés : ils restent au catalogue complet. Réversible d'une
               commande.
    copie      seuls les fichiers retenus atterrissent dans le coffre cible,
               et les déclarations d'agents y sont réduites pour rester
               cohérentes. Le coffre obtenu est réellement minimal.

Usage :
    python3 scripts/installer.py --sonder             # ce que la machine dit, n'écrit rien
    python3 scripts/installer.py                      # aperçu en place (n'écrit rien)
    python3 scripts/installer.py --appliquer          # exécute en place
    python3 scripts/installer.py --installer ~/coffre/OBSIA --appliquer
    python3 scripts/installer.py --rejouer --appliquer      # rejoue obsia.local.yml
    python3 scripts/installer.py --tout --appliquer         # revient au catalogue complet
    python3 scripts/installer.py --modules noyau,revue --appliquer

Rien n'est écrit sans `--appliquer` : l'aperçu du §2 n'est pas décoratif.
Aucun accès réseau, aucune commande système modifiante (§4).
"""

import argparse
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import modules as MOD
from generer_prompt import (RACINE_DEFAUT, fichiers_declaratifs, lire_frontmatter,
                            prompt_du_coffre)

#: Ce qu'une installation par copie emporte quoi qu'il arrive : les règles, les
#: scripts, la licence. Un coffre sans son contrat n'est pas un coffre réduit,
#: c'est un tas de fichiers.
SOCLE = ("CLAUDE.md", "README.md", "README.fr.md", "DEMARRAGE.md",
         "GETTING-STARTED.md", "HISTORIQUE.md", "LICENSE", ".gitignore",
         "scripts", ".githooks", ".github",
         "IA/system", "IA/MCP/mcp.example.json")

#: Dossiers recréés vides dans la cible — le contenu appartient à l'instance,
#: jamais à la distribution (§13). La mémoire n'y figure plus : elle vit dans le
#: coffre parent (§7.1), et c'est `MOD.ecrire_memoire_du_coffre` qui la pose.
PROPRES_A_LINSTANCE = ("brouillon", "IA/system/session-log")


# --------------------------------------------------------------- présentation

def titre(texte: str) -> None:
    print("\n%s\n%s" % (texte, "─" * len(texte)))


def etat_sonde(resultat: bool | None) -> str:
    return {True: "détecté", False: "absent", None: "indécidable"}[resultat]


def afficher_systeme(systeme: dict) -> None:
    titre("Ce que la machine dit d'elle-même")
    lignes = [
        ("Distribution", systeme["nom_distribution"]),
        ("Gestionnaire de paquets", systeme["gestionnaire_paquets"] or "aucun reconnu"),
        ("Conteneurs", systeme["conteneurs"] or "aucun"),
        ("Init", systeme["init"] or "non systemd"),
        ("Coffre Obsidian parent", systeme["coffre_parent"] or "aucun détecté"),
    ]
    for cle, valeur in lignes:
        print("  %-26s %s" % (cle + " :", valeur))
    print("\n  Aucune de ces informations ne quitte la machine : elles servent à")
    print("  choisir les modules, et sont recopiées dans obsia.local.yml, qui")
    print("  n'est pas versionné.")


# ------------------------------------------------------------------ sélection

def demander(question: str, defaut: bool) -> bool:
    """Question fermée. Hors terminal, le défaut s'applique sans bloquer."""
    invite = "%s [%s] " % (question, "O/n" if defaut else "o/N")
    if not sys.stdin.isatty():
        print("%s%s  (pas de terminal — défaut appliqué)"
              % (invite, "o" if defaut else "n"))
        return defaut
    while True:
        try:
            reponse = input(invite).strip().lower()
        except EOFError:
            print()
            return defaut
        if not reponse:
            return defaut
        if reponse in ("o", "oui", "y", "yes"):
            return True
        if reponse in ("n", "non", "no"):
            return False
        print("  Répondre o ou n.")


def choisir(modules: list[dict], racine: Path, interactif: bool) -> set[str]:
    """Sonde chaque module, propose un défaut, et laisse trancher l'utilisateur.

    La sonde ne décide jamais seule : elle ne sait pas distinguer « docker est
    installé » de « je veux gérer des conteneurs ». Elle ne fait que proposer.
    """
    titre("Modules")
    retenus = set(MOD.essentiels(modules))

    for m in modules:
        nom = m["name"]
        if m.get("essentiel"):
            print("\n  ● %s — essentiel, toujours installé" % nom)
            print("    %s" % m.get("description", ""))
            continue

        resultat = MOD.sonder(m, racine)
        defaut = resultat is not False        # indécidable → proposé, pas imposé

        print("\n  ○ %s" % nom)
        print("    %s" % m.get("description", ""))
        print("    sonde : %s%s" % (
            etat_sonde(resultat),
            "" if not m.get("sondes") else " (%s)" % ", ".join(m["sondes"])))
        if m.get("requiert"):
            print("    requiert : %s" % ", ".join(m["requiert"]))

        question = "    %s" % m.get("question", "Retenir ce module ?")
        if interactif:
            if demander(question, defaut):
                retenus.add(nom)
        else:
            print("%s → %s  (non interactif)" % (question, "oui" if defaut else "non"))
            if defaut:
                retenus.add(nom)

    return MOD.resoudre_dependances(modules, retenus)


# -------------------------------------------------------------------- aperçu

def apercu(modules: list[dict], actifs: set[str], racine: Path,
           mode: str, cible: Path | None, tout: bool = False) -> list[Path]:
    """Affiche ce qui serait retenu et ce qui serait écarté. N'écrit rien (§2)."""
    titre("Aperçu — rien n'est écrit sans --appliquer")

    emportes: list[Path] = []
    for m in modules:
        nom = m["name"]
        fichiers = MOD.fichiers_du_module(racine, nom)
        marque = "✓" if nom in actifs else "·"
        print("  %s %-18s %d fichier(s)" % (marque, nom, len(fichiers)))
        for f in fichiers:
            print("      %s %s" % (marque, f))
        if nom in actifs:
            emportes += fichiers

    ecartes = [m["name"] for m in modules if m["name"] not in actifs]
    print("\n  Retenus  : %s" % ", ".join(sorted(actifs)))
    print("  Écartés  : %s" % (", ".join(ecartes) or "aucun"))
    profil = ("aucun — catalogue complet" if tout
              else str(MOD.chemin_profil(cible or racine)))
    print("  Profil   : %s" % profil)

    if mode == "copie":
        print("  Cible    : %s" % cible)
        print("\n  Seront aussi copiés : %s" % ", ".join(SOCLE))
        print("  À l'instance — créés s'ils manquent, jamais vidés :")
        for rel in PROPRES_A_LINSTANCE:
            deja = contenu_dinstance(cible / rel)
            print("      %-9s: %s" % ("conservé" if deja else "créé", rel))
    else:
        print("\n  Aucun fichier n'est déplacé ni supprimé. Le profil ne réduit")
        print("  que ce qui n'est pas versionné : l'AGENTS.md voisin du coffre,")
        print("  et le prompt système si vous en produisez un.")
        print("  Les index versionnés (agents, skills, taches, modules et")
        print("  IA/README.md) restent au catalogue complet — c'est ce que la CI")
        print("  et le contrôle d'avant-commit vérifient.")

    # La mémoire vit à côté du dépôt, dans le coffre parent (§7.1).
    coffre_parent = (cible if mode == "copie" else racine).parent
    print("\n  Mémoire du coffre parent : %s" % coffre_parent)
    if parent_est_le_dossier_personnel(cible if mode == "copie" else racine):
        print("  ! le coffre parent est votre dossier personnel : --appliquer")
        print("    refusera d'installer. Placez OBSIA dans un dossier de coffre")
        print("    dédié (DEMARRAGE.md, étape 1).")
    for rel in ("0-PERSONNELS/profil-utilisateur.md", "0-MEMOIRES/README.md",
                "0-MEMOIRES/préférences/"):
        chemin = coffre_parent / rel
        print("      %-9s: %s" % ("conservé" if chemin.exists() else "créé", rel))
    if est_un_coffre_parent(coffre_parent):
        for rel, mot in ((".gitignore", "conservé"),
                         (".githooks/pre-commit", "rafraîchi"),
                         (".githooks/post-commit", "rafraîchi")):
            chemin = coffre_parent / rel
            print("      %-9s: %s" % (mot if chemin.is_file() else "posé", rel))
        print("      dépôt de données : %s"
              % ("déjà initialisé" if (coffre_parent / ".git").is_dir()
                 else "à initialiser (git init)"))

    coffre = cible if mode == "copie" else racine
    etat = etat_agents(coffre)
    print("\n  AGENTS.md : %s — %s" % (etat, chemin_agents(coffre)))
    if etat == "sauté":
        print("    (%s.)" % raison_du_saut(coffre))
    elif etat == "régénéré":
        print("    (porte le marqueur OBSIA : sera réécrit au profil courant)")

    return emportes


# -------------------------------------------------------------- mode « copie »

def reduire_declarations_agent(chemin: Path, skills_presents: set[str],
                               mcp_presents: set[str]) -> bool:
    """Retire d'un agent les skills et MCP que la cible n'a pas reçus.

    Uniquement en mode copie : là, les fichiers sont réellement absents, et un
    agent qui les déclarerait ferait échouer le vérificateur de la cible. En
    mode « en place » rien n'est réécrit — les fichiers sont toujours là.
    """
    lignes = chemin.read_text(encoding="utf-8").split("\n")
    if lignes[0] != "---":
        return False
    fin = next((i for i, l in enumerate(lignes[1:], 1) if l == "---"), None)
    if fin is None:
        return False

    presents = {"skills": skills_presents, "mcp": mcp_presents}
    garde, section, modifie = [], None, False

    for i, ligne in enumerate(lignes):
        if 0 < i < fin:
            nu = ligne.strip()
            if nu.rstrip(":") in presents and nu.endswith(":"):
                section = nu.rstrip(":")
                garde.append(ligne)
                continue
            if section and nu.startswith("- "):
                if nu[2:].strip() not in presents[section]:
                    modifie = True
                    continue
                garde.append(ligne)
                continue
            if section and garde and garde[-1].strip() == section + ":":
                garde.pop()          # la liste est vide : la clé ne reste pas seule
            section = None
        garde.append(ligne)

    if modifie:
        chemin.write_text("\n".join(garde), encoding="utf-8")
    return modifie


def contenu_dinstance(dossier: Path) -> bool:
    """Vrai si le dossier porte du travail de l'instance, pas que son README."""
    return dossier.is_dir() and any(e.name != "README.md"
                                    for e in dossier.iterdir())


def copier_arbre(src: Path, dst: Path, cible: Path, refus: list[str]) -> None:
    """Copie `src` vers `dst`, sans jamais toucher aux zones de l'instance.

    Ce qui est à l'instance se crée (voir `copier`) : le copier, ce serait
    emporter le travail d'ailleurs, et l'écraser, l'effacer. Un lien
    symbolique non plus ne se traverse pas : `refus` garde la trace de ce qui
    n'a pas été copié pour cette raison.
    """
    relatif = dst.relative_to(cible)
    for zone in PROPRES_A_LINSTANCE:
        if relatif == Path(zone) or Path(zone) in relatif.parents:
            return
    lien = MOD.sous_un_lien(cible, dst)
    if lien is not None:
        refus.append("%s (à travers le lien %s)"
                     % (relatif, lien.relative_to(cible)))
        return
    if src.is_dir():
        dst.mkdir(parents=True, exist_ok=True)
        for enfant in sorted(src.iterdir()):
            copier_arbre(enfant, dst / enfant.name, cible, refus)
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def reduire_a_la_cible(cible: Path) -> None:
    """Retire de la cible les déclarations qu'elle ne peut pas honorer."""
    skills_presents = {p.stem
                       for p in fichiers_declaratifs(cible / "IA" / "skills")}
    mcp_presents = {p.stem for p in (cible / "IA" / "MCP").glob("*.md")}
    for chemin in fichiers_declaratifs(cible / "IA" / "agents"):
        if reduire_declarations_agent(chemin, skills_presents, mcp_presents):
            print("  ~ déclarations réduites : %s"
                  % chemin.relative_to(cible))

    # Une tâche qui vise un agent absent ne déclencherait rien.
    agents_presents = {p.stem
                       for p in fichiers_declaratifs(cible / "IA" / "agents")}
    for chemin in sorted((cible / "IA" / "tâches").glob("*.md")):
        fm = lire_frontmatter(chemin) or {}
        if fm.get("mode") == "agent" and fm.get("agent") not in agents_presents:
            chemin.unlink()
            print("  − tâche retirée (agent absent) : %s"
                  % chemin.relative_to(cible))


def avertir_du_lien(rel: Path) -> None:
    """Le dire, quand un lien de la cible empêche un geste dans `rel`."""
    print("  ! %s : un lien symbolique de la cible aurait été traversé ; "
          "laissé de côté." % rel, file=sys.stderr)


def copier(racine: Path, cible: Path, emportes: list[Path]) -> None:
    cible.mkdir(parents=True, exist_ok=True)

    refus: list[str] = []
    for rel in SOCLE:
        if (racine / rel).exists():
            copier_arbre(racine / rel, cible / rel, cible, refus)

    for rel in emportes:
        if (racine / rel).exists():
            copier_arbre(racine / rel, cible / rel, cible, refus)

    if refus:
        print("  ! %d entrée(s) non copiée(s) : un lien symbolique de la cible "
              "aurait été traversé." % len(refus), file=sys.stderr)
        for ligne in sorted(refus):
            print("      %s" % ligne, file=sys.stderr)

    # Ce qui appartient à l'instance ne se copie pas et ne se vide pas : on le
    # crée s'il manque, avec son README, et on laisse son contenu en paix.
    for rel in PROPRES_A_LINSTANCE:
        dossier = cible / rel
        if MOD.sous_un_lien(cible, dossier) is not None:
            avertir_du_lien(Path(rel))
            continue
        if contenu_dinstance(dossier):
            print("  ~ %s conservé : il a déjà un contenu, il est à l'instance."
                  % rel)
            continue
        dossier.mkdir(parents=True, exist_ok=True)
        lireme = racine / rel / "README.md"
        if lireme.is_file():
            shutil.copy2(lireme, dossier / "README.md")

    MOD.ecrire_gabarits_dinstance(cible)

    # Lire un dossier lié, c'est lire ailleurs ; y réécrire, c'est écrire
    # ailleurs. Les deux se refusent ensemble.
    sous_ia = [sous for sous in ("IA", "IA/agents", "IA/skills", "IA/MCP",
                                 "IA/tâches")
               if MOD.sous_un_lien(cible, cible / sous) is not None]
    if sous_ia:
        avertir_du_lien(Path(sous_ia[0]))
    else:
        reduire_a_la_cible(cible)


# ---------------------------------------------------------------- régénération

#: Ce que la régénération écrit : `regenerate_index.py` pose les index dans
#: `IA/system/`, `regenerate_sommaire.py` les `sommaire.md` dans la mémoire du
#: coffre parent (§7.1). Un lien n'importe où sous l'une de ces racines ferait
#: écrire — et lire — hors du coffre visé.
DOSSIER_INDEX = "IA"
#: Les deux noms d'un dossier de mémoire : `0-…` depuis la bascule, `-…` pour
#: les coffres qui ne l'ont pas finie (§7.1).
PREFIXES_DE_MEMOIRE = ("0-", "-")


def dossiers_a_regenerer(racine: Path) -> list[Path]:
    """`IA/` dans le dépôt, plus la mémoire du coffre parent quand il est là."""
    cibles = [racine / DOSSIER_INDEX]
    parent = racine.parent
    if parent.is_dir():
        cibles += [parent / nom for nom in sorted(os.listdir(parent))
                   if nom.startswith(PREFIXES_DE_MEMOIRE) and not nom.startswith(".")
                   and (parent / nom).is_dir()]
    return cibles


def premier_lien(racine: Path) -> Path | None:
    """Le premier lien symbolique sous `IA/` ou dans la mémoire, ou None.

    Tout l'arbre est parcouru, pas seulement les racines : un `IA/system`
    déplacé ailleurs, un `sommaire.md` partagé dans une mémoire liée font écrire
    les générateurs hors du coffre visé aussi sûrement qu'un `IA/` entier.
    `os.walk` ne descend pas dans les liens qu'il croise (`followlinks` est
    faux) : c'est à chaque niveau qu'on teste les noms, dossiers et fichiers.
    """
    for depart in dossiers_a_regenerer(racine):
        if depart.is_symlink():
            return depart
        if not depart.is_dir():
            continue
        for chemin, dossiers, fichiers in os.walk(depart):
            for nom in dossiers + fichiers:
                candidat = Path(chemin) / nom
                if candidat.is_symlink():
                    return candidat
    return None


def activer_crochets(coffre: Path) -> None:
    """Active `core.hooksPath` sur le dépôt, une fois par clone (§11).

    Le contrat demande de le faire à la main ; l'installeur le fait pour qui
    l'oublie, parce qu'un crochet non activé laisse passer ce que les gardes
    refusent. On ne l'impose pas et on n'échoue jamais pour ça : sans dépôt git
    sur place, ou sans `git`, on le dit et on continue.
    """
    if not (coffre / ".git").exists():
        return
    try:
        res = subprocess.run(["git", "-C", str(coffre), "config",
                              "core.hooksPath", ".githooks"],
                             capture_output=True, text=True)
    except OSError as souci:
        print("  ! core.hooksPath non posé (%s)." % souci, file=sys.stderr)
        return
    if res.returncode == 0:
        print("  ~ core.hooksPath = .githooks")
    else:
        print("  ! core.hooksPath non posé : %s"
              % (res.stderr or "").strip(), file=sys.stderr)


def designation(chemin: Path, base: Path) -> Path:
    """Chemin affiché : relatif au dépôt s'il y est, au coffre parent sinon.

    La mémoire vit à côté du dépôt (§7.1) : un lien trouvé peut être hors de
    lui, et `relative_to` lèverait une exception au lieu de le nommer.
    """
    for depart in (base, base.parent):
        try:
            return chemin.relative_to(depart)
        except ValueError:
            continue
    return chemin


def regenerer(racine: Path) -> int:
    """Relance les générateurs puis le vérificateur, dans le coffre visé.

    Un lien symbolique, où qu'il soit sous `IA/` ou dans la mémoire, arrête tout
    net : les générateurs écriraient hors du coffre visé — les `sommaire.md`
    dans une mémoire liée, les index dans l'`IA/` lié — et le vérificateur
    lirait des fichiers qui ne sont pas au coffre. On le dit, on saute, et le
    code de retour reste bon : rien n'est cassé, seulement rien de régénéré.
    """
    lien = premier_lien(racine)
    if lien is not None:
        print("  ! %s : un lien symbolique de la cible serait traversé par la "
              "régénération ; index et sommaires laissés en l'état."
              % designation(lien, racine), file=sys.stderr)
        return 0

    for script in ("regenerate_sommaire.py", "regenerate_index.py"):
        chemin = racine / "scripts" / script
        if not chemin.is_file():
            continue
        res = subprocess.run([sys.executable, str(chemin)],
                             cwd=str(racine), capture_output=True, text=True)
        print("  · %s → %s" % (script, "ok" if res.returncode == 0 else "échec"))
        if res.returncode != 0:
            print((res.stderr or res.stdout).strip())
            return res.returncode

    verif = racine / "scripts" / "verifier_coffre.py"
    if not verif.is_file():
        return 0
    res = subprocess.run([sys.executable, str(verif)],
                         cwd=str(racine), capture_output=True, text=True)
    print((res.stdout or "").strip())
    if res.returncode != 0:
        print((res.stderr or "").strip(), file=sys.stderr)
    return res.returncode


# ------------------------------------------------------------------ AGENTS.md

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


def chemin_agents(coffre: Path) -> Path:
    """AGENTS.md se pose **à côté** du coffre, jamais dedans.

    Les harness lisent le fichier de consignes du dépôt dans lequel ils
    s'ouvrent — une fiche par harness dans `IA/system/adaptateurs-harness/` — et
    ce dépôt n'est pas le coffre : OBSIA est un catalogue qu'on lit, pas un
    projet qu'on construit. Le poser dehors a un second effet, voulu :
    `publier.py` n'exporte que les fichiers suivis du dépôt (`git archive HEAD`)
    — un fichier hors dépôt ne peut pas s'y glisser, et n'est de toute façon pas
    versionné.
    """
    return coffre.parent / "AGENTS.md"


def tete_agents(chemin: Path) -> str:
    """Le début du fichier, sans BOM ni blancs : de quoi juger le marqueur."""
    return chemin.read_text(encoding="utf-8").lstrip("\ufeff").lstrip()


def porte_le_marqueur(chemin: Path) -> bool:
    """Ce fichier commence-t-il par un libellé OBSIA connu ?"""
    return tete_agents(chemin).startswith(MARQUEURS_AGENTS)


def etat_agents(coffre: Path) -> str:
    """« créé », « régénéré » ou « sauté » — décidé avant d'écrire quoi que ce soit.

    « sauté » couvre tout ce qui n'est pas à nous : un lien symbolique, qui
    appartient à qui l'a posé ; autre chose qu'un fichier ; un fichier étranger,
    ou illisible. Dans le doute on s'abstient — jamais on n'écrase.
    """
    chemin = chemin_agents(coffre)
    if chemin.is_symlink():
        return "sauté"              # un lien ne se réécrit pas, même marqué
    if not chemin.exists():
        return "créé"
    if not chemin.is_file():
        return "sauté"              # dossier, socket… : pas notre affaire
    try:
        marque = porte_le_marqueur(chemin)
    except OSError:
        return "sauté"              # illisible : à nous de ne pas insister
    return "régénéré" if marque else "sauté"


def raison_du_saut(coffre: Path) -> str:
    """Pourquoi ce fichier n'est pas touché, dit de façon actionnable.

    La phrase commence après le chemin, et dit quoi faire : sans cela,
    l'avertissement laisserait devant un fichier inchangé sans issue.
    """
    chemin = chemin_agents(coffre)
    if chemin.is_symlink():
        return ("est un lien symbolique ; supprimez-le pour qu'un fichier à nous "
                "puisse être régénéré")
    if not chemin.is_file():
        return ("n'est pas un fichier ; déplacez-le ou supprimez-le pour "
                "qu'installer.py puisse écrire à sa place")
    try:
        tete_agents(chemin)
    except OSError as souci:
        return "est illisible (%s) ; laissé intact" % (souci.strerror or souci)
    return ("ne porte pas le marqueur OBSIA ; supprimez-le ou ajoutez le marqueur "
            "en tête pour qu'il soit régénéré")


def ecrire_agents(coffre: Path) -> str:
    """Écrit AGENTS.md pour ce coffre et son profil, ou explique pourquoi non.

    Le contenu est exactement celui du prompt système : même fabrication, donc
    même index, même méthode. Ce qui change, c'est où il atterrit et ce qu'il
    porte en tête — le marqueur qui autorise la réécriture suivante.

    Rien ici ne doit faire tomber l'installation : un fichier étranger, un
    dossier à sa place, un lien, un parent en lecture seule, on le dit, on
    passe, et le code de retour ne bouge pas.
    """
    chemin = chemin_agents(coffre)
    etat = etat_agents(coffre)
    if etat == "sauté":
        print("  ! %s %s." % (chemin, raison_du_saut(coffre)), file=sys.stderr)
        return etat

    prompt = prompt_du_coffre(coffre)
    if prompt is None:
        print("  ! %s : rien à écrire, ce profil ne retient aucun agent." % chemin,
              file=sys.stderr)
        return etat

    try:
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(contenu_agents(prompt), encoding="utf-8")
    except OSError as souci:
        print("  ! %s : écriture impossible (%s) ; laissé de côté."
              % (chemin, souci.strerror or souci), file=sys.stderr)
        return "sauté"
    print("  ~ AGENTS.md %s : %s" % (etat, chemin))
    return etat


# Entrée des « Fichiers exclus » d'Obsidian : le `code/` de tout projet. Forme
# regex entre barres obliques — la seule qui ait un sens sur le chemin complet
# `0-PROJETS/<projet>/code/<…>`. Le joker au milieu d'un chemin
# (`0-PROJETS/*/code`, essayé d'abord) n'est documenté nulle part, et la doc
# officielle d'Obsidian décrit l'effet du réglage sans en donner la syntaxe.
MOTIF_CODE_OBSIDIAN = "/^0-PROJETS\\/[^\\/]+\\/code\\//"
# Motif écrit par la première version, retiré à la réinstallation.
MOTIF_CODE_OBSIDIAN_ANCIEN = "0-PROJETS/*/code"


def exclure_code_d_obsidian(coffre: Path) -> None:
    """Exclut le `code/` des projets de l'index d'Obsidian, si le coffre parent
    en est un.

    Le dépôt git de chaque projet ne doit ni paraître dans la recherche, le
    graphe ou les mentions non liées, ni peser dans le sélecteur rapide et les
    suggestions de liens (§7.3) — c'est ce que promet le réglage « Fichiers
    exclus » (aide officielle Obsidian). Obsidian le range dans
    `.obsidian/app.json`, clé `userIgnoreFilters`. On ne crée rien sans coffre
    Obsidian, on ne touche à rien si le parent ne porte pas de `0-PROJETS/` (il
    n'y a alors rien à exclure), on ne suit jamais un lien symbolique, et une
    configuration illisible ou d'un format inattendu est laissée telle quelle :
    un réglage d'éditeur ne doit pas faire tomber l'installation.

    **Ce que la documentation officielle ne dit pas** : si l'ancre `^` du motif
    correspond bien au chemin qu'Obsidian compare — la syntaxe du réglage n'est
    documentée nulle part. L'appariement reste donc à confirmer à la main, une
    fois, sur un coffre réel, par la recette affichée après l'ajout et reprise
    dans `installation-et-publication.md` ; la même réserve est écrite au §7.3.

    L'écriture est **idempotente** : le motif n'est ajouté qu'une fois, et
    l'ancien motif à joker est retiré s'il traîne — les autres entrées de
    l'utilisateur ne sont pas touchées. Si rien ne change, le fichier n'est pas
    réécrit. L'écriture passe par un fichier temporaire puis `os.replace`, pour
    qu'une interruption ne laisse jamais un `app.json` tronqué ; le fichier naît
    en `0600` (un réglage d'éditeur n'a rien à faire sous les yeux du voisin) et
    garde son mode s'il existait déjà.
    """
    parent = coffre.parent
    projets = parent / "0-PROJETS"
    if not projets.is_dir():
        projets = parent / "-PROJETS"           # coffre d'avant la bascule (§7.1)
    dossier = parent / ".obsidian"
    if not dossier.is_dir():
        return
    if not projets.is_dir():
        print("pas de 0-PROJETS/ : exclusion Obsidian non posée, relancer "
              "l'installeur après le premier projet.")
        return
    config = dossier / "app.json"
    if MOD.sous_un_lien(parent, config) is not None:
        print("  ! %s : lien symbolique sur le chemin, Fichiers exclus non "
              "modifiés." % config, file=sys.stderr)
        return
    if config.is_file():
        try:
            donnees = json.loads(config.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            print("  ! %s : configuration illisible, Fichiers exclus non "
                  "modifiés." % config, file=sys.stderr)
            return
        if not isinstance(donnees, dict):
            print("  ! %s : format inattendu, Fichiers exclus non modifiés."
                  % config, file=sys.stderr)
            return
    else:
        donnees = {}
    filtres_initiaux = donnees.get("userIgnoreFilters")
    if filtres_initiaux is None:
        filtres_initiaux = []
    elif not isinstance(filtres_initiaux, list):
        print("  ! %s : `userIgnoreFilters` n'est pas une liste, Fichiers "
              "exclus non modifiés." % config, file=sys.stderr)
        return
    filtres = [f for f in filtres_initiaux if f != MOTIF_CODE_OBSIDIAN_ANCIEN]
    if MOTIF_CODE_OBSIDIAN not in filtres:
        filtres.append(MOTIF_CODE_OBSIDIAN)
    if filtres == filtres_initiaux:
        return
    donnees["userIgnoreFilters"] = filtres
    contenu = json.dumps(donnees, ensure_ascii=False, indent=2) + "\n"
    temporaire = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=dossier,
                                         prefix=".app.json.", suffix=".tmp",
                                         delete=False) as flux:
            temporaire = Path(flux.name)
            flux.write(contenu)
        # Le temporaire naît en 0600 ; on garde le mode du fichier qu'on remplace.
        if config.is_file():
            os.chmod(temporaire, stat.S_IMODE(os.stat(config).st_mode))
        os.replace(temporaire, config)
    except OSError as souci:
        if temporaire is not None:
            try:
                temporaire.unlink()
            except OSError:
                pass
        print("  ! %s : écriture impossible (%s), Fichiers exclus non modifiés."
              % (config, souci.strerror or souci), file=sys.stderr)
        return
    print("  + Fichiers exclus d'Obsidian : `%s` dans %s."
          % (MOTIF_CODE_OBSIDIAN, config))
    print("    Vérification manuelle à faire une fois : poser un fichier sous")
    print("    `0-PROJETS/<projet>/code/`, puis chercher son nom dans Obsidian ;")
    print("    s'il n'apparaît ni dans la recherche, ni dans le graphe, ni dans")
    print("    les suggestions de liens, le motif agit comme voulu.")


# ---------------------------------------------------- dépôt de données du coffre

#: Les gabarits du dépôt de données du coffre (§7.1), versionnés dans le
#: produit : la liste blanche et les deux crochets.
GABARITS_DEPOT = Path("IA") / "system" / "depot-de-donnees"
#: Où le dépôt de données range ses crochets. Même nom que ceux du produit.
CROCHETS_DEPOT = ".githooks"


def parent_est_le_dossier_personnel(produit: Path) -> bool:
    """Vrai si le dossier qui contient `produit` est le dossier personnel.

    Ce n'est jamais un coffre : y poser la mémoire, puis un `git init` au
    passage suivant (les dossiers posés devenant des marqueurs), convertirait
    tout le dossier personnel en dépôt de données.
    """
    try:
        parent = produit.resolve().parent
        # `HOME` vide fait rendre `/` à `Path.home()` : la base des comptes
        # donne alors le vrai dossier personnel.
        candidats = {Path.home().resolve()}
        try:
            import pwd
            candidats.add(Path(pwd.getpwuid(os.getuid()).pw_dir).resolve())
        except (ImportError, KeyError, AttributeError):
            pass
        candidats.discard(Path("/"))
        return parent in candidats
    except (OSError, RuntimeError):
        return False


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


def _git(chemin: Path, *arguments: str) -> subprocess.CompletedProcess | None:
    """git dans `chemin`, sans jamais lever : None si git n'est pas là."""
    try:
        return subprocess.run(["git", "-C", str(chemin), *arguments],
                              capture_output=True, text=True)
    except OSError:
        return None


def ecrire_liste_blanche_depot(coffre: Path, racine: Path) -> None:
    """Pose `<coffre>/.gitignore` depuis le gabarit — sans jamais l'écraser (§7.1).

    La liste blanche dit ce que le dépôt de données suit : les zones de mémoire,
    rien d'autre. Elle est le gabarit à la lettre, et `verifier_coffre.py
    --coffre` le vérifie. La retoucher sur la machine ferait entrer `OBSIA/` —
    ou pire — dans l'histoire de la mémoire, sans que personne ne le voie.
    """
    gabarit = racine / GABARITS_DEPOT / "gitignore-coffre"
    if not gabarit.is_file():
        return
    cible = coffre / ".gitignore"
    if MOD.sous_un_lien(coffre, cible) is not None:
        avertir_du_lien(Path(".gitignore"))
        return
    attendu = gabarit.read_text(encoding="utf-8")
    if cible.is_file():
        if cible.read_text(encoding="utf-8") != attendu:
            print("  ! .gitignore du coffre : il diffère du gabarit "
                  "`IA/system/depot-de-donnees/gitignore-coffre` et reste tel "
                  "quel (§7.1).", file=sys.stderr)
        return
    cible.write_text(attendu, encoding="utf-8")
    print("  + .gitignore — liste blanche du dépôt de données du coffre (§7.1)")


def initialiser_depot_de_donnees(coffre: Path) -> None:
    """`git init` du dépôt de données s'il manque. Ne pousse jamais (§7.1)."""
    if (coffre / ".git").exists():
        return
    dedans = _git(coffre, "rev-parse", "--show-toplevel")
    if dedans is not None and dedans.returncode == 0:
        # Le coffre est un sous-dossier d'un autre dépôt : y faire naître un
        # dépôt imbriqué cacherait la mémoire et rendrait le parent instable.
        print("  ! le coffre est déjà dans le dépôt git %s ; dépôt de données "
              "laissé non initialisé (§7.1)." % dedans.stdout.strip(), file=sys.stderr)
        return
    resultat = _git(coffre, "init", "--quiet")
    if resultat is None or resultat.returncode != 0:
        print("  ! dépôt de données non initialisé : %s"
              % ((resultat.stderr or "").strip() if resultat else "git introuvable"),
              file=sys.stderr)
        return
    print("  + dépôt de données du coffre initialisé (git init, §7.1)")


def enregistrer_distant(coffre: Path, distant: str | None) -> None:
    """Pose `origin` quand le profil déclare `coffre_distant` (§7.1). Ne pousse pas.

    L'installeur enregistre l'adresse et s'arrête là : c'est le post-commit du
    dépôt de données qui poussera, et pas entre deux commits.
    """
    if not distant or not (coffre / ".git").exists():
        return
    actuel = _git(coffre, "remote", "get-url", "origin")
    if actuel is not None and actuel.returncode == 0:
        if actuel.stdout.strip() != distant:
            print("  ! origin déjà posé sur %s ; `coffre_distant` (%s) non appliqué."
                  % (actuel.stdout.strip(), distant), file=sys.stderr)
        return
    resultat = _git(coffre, "remote", "add", "origin", distant)
    if resultat is not None and resultat.returncode == 0:
        print("  + origin = %s — le dépôt de données poussera là (§7.1)" % distant)
    else:
        print("  ! origin non posé : %s"
              % ((resultat.stderr or "").strip() if resultat else "git introuvable"),
              file=sys.stderr)


def poser_crochets_depot(coffre: Path, produit: Path) -> None:
    """Pose et active les crochets du dépôt de données (§7.1).

    `@PRODUIT@` devient le nom du dossier du produit à la racine du coffre : les
    crochets rappellent alors les scripts du produit, qui savent où ils sont.
    Les crochets sont rafraîchis à chaque installation — eux n'appartiennent pas
    à l'instance, contrairement à la liste blanche.
    """
    if not (coffre / ".git").exists():
        return
    dossier = coffre / CROCHETS_DEPOT
    if MOD.sous_un_lien(coffre, dossier) is not None:
        avertir_du_lien(Path(CROCHETS_DEPOT))
        return
    poses = []
    for nom in ("pre-commit", "post-commit"):
        gabarit = produit / GABARITS_DEPOT / nom
        if not gabarit.is_file():
            continue
        cible = dossier / nom
        if MOD.sous_un_lien(coffre, cible) is not None:
            avertir_du_lien(Path(CROCHETS_DEPOT) / nom)
            continue
        dossier.mkdir(parents=True, exist_ok=True)
        cible.write_text(gabarit.read_text(encoding="utf-8").replace("@PRODUIT@", produit.name),
                         encoding="utf-8")
        cible.chmod(0o755)
        poses.append(nom)
    if not poses:
        return
    resultat = _git(coffre, "config", "core.hooksPath", CROCHETS_DEPOT)
    actives = resultat is not None and resultat.returncode == 0
    print("  + crochets du dépôt de données : %s%s"
          % (", ".join(poses),
             " (core.hooksPath=%s)" % CROCHETS_DEPOT if actives else
             " — core.hooksPath non posé"))


def preparer_memoire_du_coffre(produit: Path) -> None:
    """Pose la mémoire du coffre parent : `0-PERSONNELS/` et `0-MEMOIRES/` (§7.1).

    `0-PERSONNELS/` reçoit le profil, `0-MEMOIRES/` son README : il explique les
    deux mémoires qu'il porte — celle des agents, vivante, et les chantiers
    clos, gelés. `0-MEMOIRES/préférences/` est posé même vide (§6) ;
    `<nom-agent>/expériences/` naît à la première leçon.

    Rien n'y est écrasé : un profil rempli fait refuser la pose du gabarit, et
    le refus est dit. La migration le déplacera.
    """
    for refus in MOD.ecrire_memoire_du_coffre(produit.parent, produit):
        print("  ! %s" % refus, file=sys.stderr)


def preparer_depot_de_donnees(produit: Path, racine: Path) -> None:
    """Outille le dépôt de données du coffre parent (§7.1).

    Le coffre parent est le dossier qui contient le produit. Rien n'est outillé
    s'il ne porte aucun marqueur de coffre — un clone de développement, un
    dossier de travail : il n'y a pas de mémoire à ranger.
    """
    coffre = produit.parent
    if not est_un_coffre_parent(coffre):
        print("  · pas de coffre parent reconnu autour de %s : dépôt de données "
              "laissé de côté (§7.1)." % produit.name)
        return
    ecrire_liste_blanche_depot(coffre, racine)
    initialiser_depot_de_donnees(coffre)
    enregistrer_distant(coffre, (MOD.lire_profil(produit) or {}).get("coffre_distant"))
    poser_crochets_depot(coffre, produit)


# ---------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Installe OBSIA en ne retenant que les modules utiles.")
    ap.add_argument("--racine", type=Path, default=RACINE_DEFAUT,
                    help="racine du coffre source (défaut : parent de ce script)")
    ap.add_argument("--sonder", action="store_true",
                    help="affiche la détection et le verdict des sondes, n'écrit rien")
    ap.add_argument("--installer", type=Path, metavar="CIBLE",
                    help="mode copie : n'écrit dans CIBLE que les modules "
                         "retenus ; l'AGENTS.md, lui, va dans CIBLE/.. — un cran "
                         "au-dessus de la cible, là où Codex le lit")
    ap.add_argument("--modules", metavar="a,b,c",
                    help="sélection explicite, sans question")
    ap.add_argument("--rejouer", action="store_true",
                    help="reprend la sélection d'obsia.local.yml")
    ap.add_argument("--tout", action="store_true",
                    help="retient tout le catalogue et supprime le profil")
    ap.add_argument("--appliquer", action="store_true",
                    help="exécute ; sans lui, l'installeur n'affiche qu'un aperçu")
    args = ap.parse_args()

    racine = args.racine.resolve()
    modules = MOD.lire_modules(racine)
    if not modules:
        print("Aucun module dans %s — catalogue introuvable."
              % MOD.dossier_modules(racine), file=sys.stderr)
        return 1

    systeme = MOD.detecter_systeme(racine)
    afficher_systeme(systeme)

    if args.sonder:
        titre("Verdict des sondes")
        for m in modules:
            print("  %-18s %s" % (m["name"],
                                  "essentiel" if m.get("essentiel")
                                  else etat_sonde(MOD.sonder(m, racine))))
        print("\nRien n'a été écrit. Pour installer : "
              "python3 scripts/installer.py --appliquer")
        return 0

    # ------------------------------------------------------------- sélection
    mode = "copie" if args.installer else "en-place"
    cible = args.installer.resolve() if args.installer else None

    # Refus franc, avant les questions et avant toute écriture : le dossier
    # personnel n'est jamais un coffre. Y poser `AGENTS.md`, le profil ou la
    # mémoire le ferait lire par tout harness lancé depuis là, et un second
    # passage y ferait un `git init`. L'aperçu, lui, se contente d'avertir.
    if args.appliquer and parent_est_le_dossier_personnel(
            cible if mode == "copie" else racine):
        if mode == "copie":
            conseil = ("Visez une cible dans un dossier de coffre, par exemple :\n"
                       "  --installer ~/\"Mon coffre\"/OBSIA")
        else:
            conseil = ("Créez un dossier de coffre et placez-y OBSIA, par exemple :\n"
                       "  mkdir -p ~/\"Mon coffre\" && mv %s ~/\"Mon coffre\"/"
                       % racine)
        print("Refusé : le dossier qui contiendrait OBSIA est votre dossier "
              "personnel, et ce n'est pas un coffre. Rien n'a été écrit.\n"
              "%s\n(DEMARRAGE.md, étape 1)." % conseil, file=sys.stderr)
        return 1

    if args.tout:
        actifs = {m["name"] for m in modules}
        # En copie, le profil dont on parle est celui de la cible : la source,
        # elle, n'est que lue.
        ou = " de la cible" if mode == "copie" else ""
        print("\n  --tout : catalogue complet, le profil%s sera supprimé." % ou)
    elif args.modules:
        demandes = {n.strip() for n in args.modules.split(",") if n.strip()}
        inconnus = demandes - {m["name"] for m in modules}
        if inconnus:
            print("Modules inconnus : %s" % ", ".join(sorted(inconnus)), file=sys.stderr)
            return 1
        actifs = MOD.resoudre_dependances(modules, demandes)
    elif args.rejouer:
        profil = MOD.lire_profil(racine)
        if profil is None:
            print("Aucun profil à rejouer (%s absent)." % MOD.NOM_PROFIL, file=sys.stderr)
            return 1
        actifs = MOD.resoudre_dependances(modules, profil.get("modules", []))
        # Le profil est modifiable à la main : un nom qui ne correspond à rien
        # doit se voir, sinon le coffre installé est plus maigre que prévu
        # sans que rien ne le dise. Sans effet sur la sélection, et non fatal.
        MOD.signaler_modules_inconnus(modules, profil.get("modules", []))
        print("\n  --rejouer : %d module(s) repris du profil." % len(actifs))
    else:
        actifs = choisir(modules, racine, interactif=sys.stdin.isatty())

    mode = "copie" if args.installer else "en-place"
    cible = args.installer.resolve() if args.installer else None
    emportes = apercu(modules, actifs, racine, mode, cible, args.tout)

    if not args.appliquer:
        print("\nAperçu seulement. Relancer avec --appliquer pour exécuter.")
        return 0

    # -------------------------------------------------------------- exécution
    titre("Exécution")

    if mode == "copie":
        if cible.resolve() == racine:
            print("La cible ne peut pas être la source.", file=sys.stderr)
            return 1
        copier(racine, cible, emportes)

    # `--tout` vaut « catalogue complet » dans les deux modes : le profil
    # disparaît, puisque c'est lui qui dit « ce coffre est réduit ». La copie,
    # elle, ne se saute pas pour autant — sans quoi `--tout --installer CIBLE`
    # annonçait le catalogue entier et laissait la cible vide.
    #
    # Et le profil qu'on écrit ou qu'on supprime est toujours celui du coffre
    # effectif : en copie, c'est celui de la cible. `--installer` lit la source,
    # il ne la modifie pas — sinon ce n'est plus une copie, et le coffre source
    # perdrait son mode sans que rien ne l'ait annoncé.
    coffre = cible if mode == "copie" else racine
    if args.tout:
        chemin = MOD.chemin_profil(coffre)
        if chemin.is_file():
            chemin.unlink()
            print("  − %s supprimé — catalogue complet" % MOD.NOM_PROFIL)
    else:
        # `coffre_distant` est lu avant d'écrire : le réinstaller ne doit pas
        # effacer l'adresse que l'utilisateur a décommentée à la main (§7.1).
        ancien = MOD.lire_profil(coffre) or {}
        print("  ~ %s" % MOD.ecrire_profil(coffre, actifs, systeme, mode,
                                           systeme.get("coffre_parent") or None,
                                           coffre_distant=ancien.get("coffre_distant")))

    code = regenerer(coffre)

    # Les gardes du dépôt ne servent que si git les voit : on active le crochet
    # une fois par clone, ici, plutôt que de compter sur la mémoire de l'agent.
    activer_crochets(coffre)

    # Après `regenerer` : `ecrire_agents` refait le prompt depuis les frontmatters
    # filtrés par le profil — il n'embarque pas l'index. L'`AGENTS.md` est donc
    # écrit après coup, une fois index et sommaires à jour.
    # Sur le coffre effectif, donc en place comme en copie.
    ecrire_agents(coffre)

    # Le dépôt de données du coffre parent, puis la mémoire qu'il suivra (§7.1).
    # Dans cet ordre : le coffre est reconnu tel qu'il est, avant que
    # `0-PERSONNELS/` et `0-MEMOIRES/` n'apparaissent sous lui. Rien n'est écrasé
    # — la liste blanche surtout pas.
    preparer_depot_de_donnees(coffre, racine)
    preparer_memoire_du_coffre(coffre)

    # Les dépôts git des projets n'ont pas leur place dans l'index d'Obsidian.
    exclure_code_d_obsidian(coffre)

    if code != 0:
        print("\nInstallation terminée, mais le coffre est incohérent "
              "— voir ci-dessus.")
    elif premier_lien(coffre) is not None:
        # Rien n'est cassé : la régénération a seulement été sautée. Le dire
        # ici, sinon la seule trace serait l'avertissement plus haut, et la
        # dernière ligne ferait croire à des index et des sommaires refaits.
        print("\nInstallation terminée, sans régénération ni vérification : "
              "un lien symbolique de la cible aurait été traversé.")
    else:
        print("\nInstallation terminée.")
    if mode == "copie":
        print("Coffre installé : %s" % coffre)
    print("Prompt système : python3 scripts/generer_prompt.py -o prompt-systeme.md --mcp")
    return code


if __name__ == "__main__":
    sys.exit(main())
