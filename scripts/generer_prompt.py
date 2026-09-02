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


def collecter(dossier: Path, genre: str) -> list[dict]:
    """Récupère les frontmatters valides d'un dossier, triés par nom."""
    if not dossier.is_dir():
        print(f"  ! dossier absent : {dossier}", file=sys.stderr)
        return []

    resultats = []
    for fichier in sorted(dossier.glob("*.md")):
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
        fm["_fichier"] = fichier.name
        resultats.append(fm)

    return resultats


# --------------------------------------------------------------------- rendu

def construire_prompt(racine: Path, agents: list[dict], skills: list[dict]) -> str:
    lignes: list[str] = []
    a = lignes.append

    a("Tu opères sur le coffre OBSIA.")
    a(f"Racine du coffre : {racine}")
    a("")

    a("## Règles permanentes")
    a("")
    a("Ces règles s'appliquent en toute circonstance, sans avoir à les relire.")
    a("")
    a("- Le coffre est en LECTURE SEULE pour tout agent read_only: true.")
    a("- Un agent read_only: false écrit SANS patch, en direct, uniquement dans :")
    a("  brouillon/, mémoire/<nom de l'agent>/, et IA/skills/ (si le skill")
    a("  createur-de-skill est déclaré). Tout le reste du coffre passe par un")
    a("  patch Git soumis à revue humaine.")
    a("- Aucune suppression sans archivage préalable dans .archive/, même en")
    a("  écriture directe.")
    a("- Toute action touchant plusieurs fichiers exige un aperçu affiché avant")
    a("  exécution, listant les chemins concernés.")
    a("- Les fichiers sommaire.md ne sont jamais édités à la main : ils sont")
    a("  régénérés par scripts/regenerate_sommaire.py")
    a("- Toute exécution de code se fait en bac à sable.")
    a("- Ne jamais recopier dans une note : mot de passe, jeton, clé, adresse IP")
    a("  privée, nom d'hôte interne. Le dépôt est public.")
    a("- Un agent et un skill sont deux choses distinctes : un agent décide et")
    a("  utilise des skills ; un skill décrit une manière de faire.")
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

    a("## Méthode")
    a("")
    a("1. Identifie dans les listes ci-dessus le ou les skills pertinents pour")
    a("   la demande.")
    a("2. Lis leur fichier : IA/skills/<nom>.md — et seulement ceux-là.")
    a("3. Applique la procédure qu'ils décrivent.")
    a("4. Cite les chemins des fichiers utilisés.")
    a("")
    a("Ne charge pas de fichier « pour voir ». Si aucun skill ne correspond,")
    a("réponds directement en le signalant.")
    a("")
    a("Un skill marqué [lecture seule] n'exécute aucune commande modifiant")
    a("l'état du système. S'il conclut à une action, énonce-la sans la faire.")

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

    if not agents and not skills:
        print("Aucun agent ni skill trouvé. Vérifie --racine.", file=sys.stderr)
        return 1

    prompt = construire_prompt(racine, agents, skills)

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
