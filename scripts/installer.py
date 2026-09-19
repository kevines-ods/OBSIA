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
from generer_prompt import RACINE_DEFAUT, fichiers_declaratifs, lire_frontmatter

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
           mode: str, cible: Path | None) -> list[Path]:
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
    print("  Profil   : %s" % MOD.chemin_profil(cible or racine))

    if mode == "copie":
        print("  Cible    : %s" % cible)
        print("\n  Seront aussi copiés : %s" % ", ".join(SOCLE))
        print("  Seront créés vides  : %s" % ", ".join(PROPRES_A_LINSTANCE))
    else:
        print("\n  Aucun fichier n'est déplacé ni supprimé. Seuls les fichiers")
        print("  générés seront réduits au profil :")
        print("    IA/system/agents-index.md, skills-index.md, taches-index.md,")
        print("    IA/system/modules-index.md, IA/README.md")
        print("  `git checkout -- IA` les remet au catalogue complet.")

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


def copier(racine: Path, cible: Path, emportes: list[Path]) -> None:
    cible.mkdir(parents=True, exist_ok=True)

    for rel in SOCLE:
        src = racine / rel
        if not src.exists():
            continue
        dst = cible / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)

    for rel in emportes:
        src, dst = racine / rel, cible / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)

    # Le contenu de l'instance ne se copie jamais : il appartient à qui installe.
    for rel in PROPRES_A_LINSTANCE:
        dossier = cible / rel
        if dossier.is_dir():
            for enfant in dossier.iterdir():
                if enfant.name == "README.md":
                    continue
                shutil.rmtree(enfant) if enfant.is_dir() else enfant.unlink()
        dossier.mkdir(parents=True, exist_ok=True)

    MOD.ecrire_gabarits_dinstance(cible)

    skills_presents = {p.stem for p in fichiers_declaratifs(cible / "IA" / "skills")}
    mcp_presents = {p.stem for p in (cible / "IA" / "MCP").glob("*.md")}
    for chemin in fichiers_declaratifs(cible / "IA" / "agents"):
        if reduire_declarations_agent(chemin, skills_presents, mcp_presents):
            print("  ~ déclarations réduites : %s"
                  % chemin.relative_to(cible))

    # Une tâche qui vise un agent absent ne déclencherait rien.
    agents_presents = {p.stem for p in fichiers_declaratifs(cible / "IA" / "agents")}
    for chemin in sorted((cible / "IA" / "tâches").glob("*.md")):
        fm = lire_frontmatter(chemin) or {}
        if fm.get("mode") == "agent" and fm.get("agent") not in agents_presents:
            chemin.unlink()
            print("  − tâche retirée (agent absent) : %s"
                  % chemin.relative_to(cible))


# ---------------------------------------------------------------- régénération

def regenerer(racine: Path) -> int:
    """Relance les générateurs puis le vérificateur, dans le coffre visé."""
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


# ---------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Installe OBSIA en ne retenant que les modules utiles.")
    ap.add_argument("--racine", type=Path, default=RACINE_DEFAUT,
                    help="racine du coffre source (défaut : parent de ce script)")
    ap.add_argument("--sonder", action="store_true",
                    help="affiche la détection et le verdict des sondes, n'écrit rien")
    ap.add_argument("--installer", type=Path, metavar="CIBLE",
                    help="mode copie : n'écrit dans CIBLE que les modules retenus")
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
    if args.tout:
        actifs = {m["name"] for m in modules}
        print("\n  --tout : catalogue complet, le profil sera supprimé.")
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
        print("\n  --rejouer : %d module(s) repris du profil." % len(actifs))
    else:
        actifs = choisir(modules, racine, interactif=sys.stdin.isatty())

    mode = "copie" if args.installer else "en-place"
    cible = args.installer.resolve() if args.installer else None
    emportes = apercu(modules, actifs, racine, mode, cible)

    if not args.appliquer:
        print("\nAperçu seulement. Relancer avec --appliquer pour exécuter.")
        return 0

    # -------------------------------------------------------------- exécution
    titre("Exécution")

    if args.tout:
        chemin = MOD.chemin_profil(racine)
        if chemin.is_file():
            chemin.unlink()
            print("  − %s supprimé — catalogue complet" % MOD.NOM_PROFIL)
    elif mode == "en-place":
        print("  ~ %s" % MOD.ecrire_profil(racine, actifs, systeme, mode,
                                           systeme.get("coffre_parent") or None))
    else:
        if cible.resolve() == racine:
            print("La cible ne peut pas être la source.", file=sys.stderr)
            return 1
        copier(racine, cible, emportes)
        print("  ~ %s" % MOD.ecrire_profil(cible, actifs, systeme, mode,
                                           systeme.get("coffre_parent") or None))

    coffre = cible if mode == "copie" else racine
    code = regenerer(coffre)

    print("\n%s" % ("Installation terminée." if code == 0
                    else "Installation terminée, mais le coffre est incohérent "
                         "— voir ci-dessus."))
    if mode == "copie":
        print("Coffre installé : %s" % coffre)
    print("Prompt système : python3 scripts/generer_prompt.py -o prompt-systeme.md --mcp")
    return code


if __name__ == "__main__":
    sys.exit(main())
