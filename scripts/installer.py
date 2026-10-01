#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Installeur d'OBSIA — ne retient que les modules qui correspondent à la machine.

Le coffre est un catalogue : tout y est déclaré, rien n'oblige à tout retenir.
Cet installeur sonde la machine, montre ce qu'il a trouvé, demande confirmation,
et écrit le profil `obsia.local.yml`. Le §13 du contrat fait foi.

Deux modes, et la différence tient en une phrase :

    en place   les fichiers restent tous là ; seuls les fichiers générés
               (index, IA/README.md, prompt système) sont réduits au profil.
               Réversible d'une commande.
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
import os
import shutil
import subprocess
import sys
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
SOCLE = ("CLAUDE.md", "README.md", "HISTORIQUE.md", "LICENSE", ".gitignore",
         "scripts", ".githooks", ".github",
         "IA/system", "IA/MCP/mcp.example.json")

#: Dossiers recréés vides dans la cible — le contenu appartient à l'instance,
#: jamais à la distribution (§13).
PROPRES_A_LINSTANCE = ("mémoire", "brouillon", "IA/system/session-log")


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
        print("\n  Aucun fichier n'est déplacé ni supprimé. Seuls les fichiers")
        print("  générés seront réduits au profil :")
        print("    IA/system/agents-index.md, skills-index.md, taches-index.md,")
        print("    IA/system/modules-index.md, IA/README.md")
        print("  `git checkout -- IA` les remet au catalogue complet.")

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

#: Les deux dossiers que la régénération écrit : `regenerate_sommaire.py` pose
#: les `sommaire.md` dans `mémoire/`, `regenerate_index.py` les index dans
#: `IA/system/`. Un lien n'importe où sous l'une de ces deux racines ferait
#: écrire — et lire — hors du coffre visé.
DOSSIERS_REGENERES = ("IA", "mémoire")


def premier_lien(racine: Path) -> Path | None:
    """Le premier lien symbolique sous `IA/` ou `mémoire/`, ou None.

    Tout l'arbre est parcouru, pas seulement les deux racines : un
    `IA/system` déplacé ailleurs, un `mémoire/sommaire.md` partagé font écrire
    les générateurs hors du coffre visé aussi sûrement qu'un `IA/` entier.
    `os.walk` ne descend pas dans les liens qu'il croise (`followlinks` est
    faux) : c'est à chaque niveau qu'on teste les noms, dossiers et fichiers.
    """
    for relatif in DOSSIERS_REGENERES:
        depart = racine / relatif
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


def regenerer(racine: Path) -> int:
    """Relance les générateurs puis le vérificateur, dans le coffre visé.

    Un lien symbolique, où qu'il soit sous `IA/` ou `mémoire/`, arrête tout
    net : les générateurs écriraient hors du coffre visé — les `sommaire.md`
    dans la `mémoire/` liée, les index dans l'`IA/` lié — et le vérificateur
    lirait des fichiers qui ne sont pas au coffre. On le dit, on saute, et le
    code de retour reste bon : rien n'est cassé, seulement rien de régénéré.
    """
    lien = premier_lien(racine)
    if lien is not None:
        print("  ! %s : un lien symbolique de la cible serait traversé par la "
              "régénération ; index et sommaires laissés en l'état."
              % lien.relative_to(racine), file=sys.stderr)
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
        chemin.write_text("%s\n\n%s\n" % (MARQUEUR_AGENTS, prompt),
                          encoding="utf-8")
    except OSError as souci:
        print("  ! %s : écriture impossible (%s) ; laissé de côté."
              % (chemin, souci.strerror or souci), file=sys.stderr)
        return "sauté"
    print("  ~ AGENTS.md %s : %s" % (etat, chemin))
    return etat


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
        print("  ~ %s" % MOD.ecrire_profil(coffre, actifs, systeme, mode,
                                           systeme.get("coffre_parent") or None))

    code = regenerer(coffre)

    # Après `regenerer` : le prompt embarque l'index, il doit lire l'index à jour.
    # Sur le coffre effectif, donc en place comme en copie.
    ecrire_agents(coffre)

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
