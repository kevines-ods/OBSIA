#!/usr/bin/env python3
"""
Génère le prompt système OBSIA à partir des frontmatters du coffre.

Usage :
    ./generer_prompt.py                          # affiche sur la sortie standard
    ./generer_prompt.py -o prompt-systeme.md     # écrit dans un fichier
    ./generer_prompt.py --mcp                    # affiche aussi la config MCP à faire
    ./generer_prompt.py --racine /chemin/OBSIA

Aucune dépendance externe : le frontmatter est lu par un analyseur minimal,
suffisant pour le format strict défini dans VAULT-CONTRACT.md.
"""

import argparse
import json
import sys
from pathlib import Path

RACINE_DEFAUT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------- frontmatter

def lire_frontmatter(chemin: Path) -> dict | None:
    """Extrait le frontmatter YAML d'un fichier Markdown.

    Gère uniquement les formes prévues par le contrat : scalaires et listes
    à tirets. Renvoie None si le fichier n'a pas de frontmatter.
    """
    try:
        texte = chemin.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as err:
        print(f"  ! illisible : {chemin.name} ({err})", file=sys.stderr)
        return None

    if not texte.startswith("---"):
        return None

    fin = texte.find("\n---", 3)
    if fin == -1:
        return None

    donnees: dict = {}
    cle_liste: str | None = None

    for ligne in texte[3:fin].splitlines():
        nu = ligne.strip()
        if not nu or nu.startswith("#"):
            continue

        # élément de liste
        if nu.startswith("- ") and cle_liste:
            donnees[cle_liste].append(nu[2:].strip())
            continue

        if ":" not in nu:
            continue

        cle, _, valeur = nu.partition(":")
        cle = cle.strip()
        valeur = valeur.strip()

        if not valeur:                      # une liste commence à la ligne suivante
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


def fichiers_declaratifs(dossier: Path) -> list[Path]:
    """Les fichiers de déclaration d'un dossier d'agents ou de skills.

    Deux formes admises (cf. VAULT-CONTRACT.md §5) :
      - `<dossier>/<nom>.md`         — forme plate, par défaut ;
      - `<dossier>/<nom>/<nom>.md`   — forme dossier, quand le skill grossit et
                                       s'accompagne de references/, scripts/…

    Le point d'entrée porte le nom du skill, pas `SKILL.md` : le §5 impose que
    le fichier porte le `name`, et le §6 l'unicité des noms de notes dans le
    coffre parent — une douzaine de `SKILL.md` la violerait.
    """
    if not dossier.is_dir():
        return []
    trouves = list(dossier.glob("*.md"))
    for sous in dossier.iterdir():
        if sous.is_dir() and not sous.name.startswith("."):
            entree = sous / (sous.name + ".md")
            if entree.is_file():
                trouves.append(entree)
    return sorted(trouves, key=lambda p: p.stem)


def collecter(dossier: Path, genre: str) -> list[dict]:
    """Récupère les frontmatters valides d'un dossier, triés par nom."""
    if not dossier.is_dir():
        print(f"  ! dossier absent : {dossier}", file=sys.stderr)
        return []

    resultats = []
    for fichier in fichiers_declaratifs(dossier):
        fm = lire_frontmatter(fichier)
        if not fm:
            print(f"  ! sans frontmatter : {fichier.name}", file=sys.stderr)
            continue
        if fm.get("kind") != genre:
            print(f"  ! kind « {fm.get('kind')} » inattendu : {fichier.name}",
                  file=sys.stderr)
            continue
        if not fm.get("description"):
            print(f"  ! description manquante : {fichier.name}", file=sys.stderr)
        fm["_fichier"] = fichier.relative_to(dossier).as_posix()
        resultats.append(fm)

    return resultats


# --------------------------------------------------------------------- rendu

def construire_prompt(racine: Path, agents: list[dict], skills: list[dict],
                      taches: list[dict] | None = None) -> str:
    lignes: list[str] = []
    a = lignes.append

    a("Tu opères sur le coffre OBSIA.")
    a(f"Racine du coffre : {racine}")
    a("")

    if agents:
        a("## Agents disponibles")
        a("")
        for ag in agents:
            desc = ag.get("description", "(sans description)")
            a(f"- **{ag['name']}** — {desc}")
            details = []
            if ag.get("skills"):
                details.append("skills : " + ", ".join(ag["skills"]))
            if ag.get("mcp"):
                details.append("MCP : " + ", ".join(ag["mcp"]))
            if details:
                a(f"  ({' ; '.join(details)})")
        a("")

    if skills:
        a("## Skills disponibles")
        a("")
        for sk in skills:
            marque = " [lecture seule]" if sk.get("read_only") else ""
            desc = sk.get("description", "(sans description)")
            a(f"- **{sk['name']}**{marque} — {desc}")
        a("")

    if taches:
        a("## Tâches planifiées déclarées")
        a("")
        a("Registre : IA/tâches/ — il fait foi. Les timers ou planificateurs qui")
        a("les déclenchent ne sont que des instances reconstructibles (§12).")
        a("Une tâche = au plus UNE instance vivante : `exécutant` dit qui a le")
        a("droit de la déclencher, donc qui pas.")
        a("")
        for ta in taches:
            etat = "" if ta.get("actif") else " [suspendue]"
            a(f"- **{ta['name']}**{etat} — {ta.get('description', '(sans description)')}")
            a(f"  ({ta.get('quand', '?')}, {ta.get('fuseau', '?')}, "
              f"mode {ta.get('mode', '?')}, exécutant {ta.get('exécutant', '?')})")
        a("")

    a("## Méthode")
    a("")
    a("Lis IA/system/VAULT-CONTRACT.md en entier avant toute action. Il fait foi")
    a("sur toutes les règles (écriture, suppression, preview, sandbox, secrets,")
    a("frontmatter) ET sur la méthode à suivre pour toute demande (son §10 :")
    a("choix de l'agent, choix des skills/MCP, écriture en mémoire, citation des")
    a("chemins). Ne déduis rien de ces sujets d'une autre source, y compris de")
    a("ce prompt — les listes ci-dessus ne sont que l'index paresseux que le §10")
    a("te demande d'utiliser.")

    return "\n".join(lignes)


def construire_config_mcp(agents: list[dict]) -> tuple[str, list[str]]:
    """Squelette de configuration MCP + liste des serveurs référencés."""
    serveurs = sorted({m for ag in agents for m in ag.get("mcp", [])})
    config = {
        "mcpServers": {
            nom: {
                "command": "À COMPLÉTER",
                "args": [],
                "env": {},
            }
            for nom in serveurs
        }
    }
    return json.dumps(config, indent=2, ensure_ascii=False), serveurs


# ---------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description="Génère le prompt système OBSIA.")
    ap.add_argument("--racine", type=Path, default=RACINE_DEFAUT,
                    help="racine du coffre (défaut : parent de ce script)")
    ap.add_argument("-o", "--sortie", type=Path,
                    help="fichier de sortie (défaut : sortie standard)")
    ap.add_argument("--mcp", action="store_true",
                    help="affiche aussi la configuration MCP à faire côté harness")
    args = ap.parse_args()

    racine = args.racine.resolve()
    if not racine.is_dir():
        print(f"Racine introuvable : {racine}", file=sys.stderr)
        return 1

    agents = collecter(racine / "IA" / "agents", "agent")
    skills = collecter(racine / "IA" / "skills", "skill")
    taches = collecter(racine / "IA" / "tâches", "tâche")

    if not agents and not skills:
        print("Aucun agent ni skill trouvé. Vérifie --racine.", file=sys.stderr)
        return 1

    prompt = construire_prompt(racine, agents, skills, taches)

    if args.sortie:
        args.sortie.write_text(prompt + "\n", encoding="utf-8")
        print(f"Écrit : {args.sortie}", file=sys.stderr)
    else:
        print(prompt)

    print(f"\n{len(agents)} agent(s), {len(skills)} skill(s).", file=sys.stderr)

    if args.mcp:
        config, serveurs = construire_config_mcp(agents)
        if serveurs:
            print("\n--- À configurer dans le harness ---", file=sys.stderr)
            print("Serveurs MCP référencés par les agents :", file=sys.stderr)
            for nom in serveurs:
                print(f"  - {nom}", file=sys.stderr)
            print("\nSquelette de configuration :", file=sys.stderr)
            print(config, file=sys.stderr)
        else:
            print("\nAucun MCP référencé par les agents.", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
