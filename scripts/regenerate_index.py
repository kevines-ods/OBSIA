#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Régénère IA/system/agents-index.md et IA/system/skills-index.md.

Les deux index sont **dérivés** des frontmatters, qui font foi. Les maintenir à
la main les fait diverger sans que rien ne le signale — c'est arrivé, voir
mémoire/assistant/expériences/index-maintenus-a-la-main.md.

Usage :
    python3 scripts/regenerate_index.py
    python3 scripts/regenerate_index.py --verifier   # n'écrit rien, sort 1 si périmé
"""

import os
import sys

sys.dont_write_bytecode = True                    # pas de __pycache__ dans le coffre
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generer_prompt import (RACINE_DEFAUT, collecter,   # même lecteur que le prompt
                            lire_frontmatter)

RACINE = RACINE_DEFAUT


def rendre_agents(agents: list[dict]) -> str:
    L = ["# agents-index.md — Index des agents", "",
         "| Agent | Rôle | Skills | MCP | Lecture seule |", "|---|---|---|---|---|"]
    for a in agents:
        L.append("| [%s](../agents/%s) | %s | %s | %s | %s |" % (
            a["name"], a["_fichier"], a.get("description", ""),
            ", ".join(a.get("skills", [])) or "—",
            ", ".join(a.get("mcp", [])) or "—",
            "oui" if a.get("read_only") else "non"))
    L += ["",
          "> Règle (cf. `VAULT-CONTRACT.md` §6) : un agent = un fichier dans `IA/agents/`,",
          "> nommé au `name` du frontmatter. Un skill n'est jamais un agent.",
          "",
          "> Fichier **généré** par `scripts/regenerate_index.py` depuis les frontmatters,",
          "> qui font foi. Ne pas éditer à la main (cf. `VAULT-CONTRACT.md` §11).",
          ""]
    return "\n".join(L)


def rendre_skills(agents: list[dict], skills: list[dict]) -> str:
    L = ["# skills-index.md — Index des skills", "",
         "| Skill | Type | Description — quoi, quand, quand pas | Utilisé par |",
         "|---|---|---|---|"]
    for s in skills:
        par = ", ".join(a["name"] for a in agents if s["name"] in a.get("skills", [])) or "—"
        L.append("| [%s](../skills/%s) | %s | %s | %s |"
                 % (s["name"], s["_fichier"], s.get("type", "?"),
                    s.get("description", ""), par))
    L += ["",
          "> `core` = indispensable au fonctionnement du coffre ; `outil` = compétence",
          "> ponctuelle. (cf. `VAULT-CONTRACT.md` §5)",
          "",
          "> Fichier **généré** par `scripts/regenerate_index.py`. La colonne description",
          "> reproduit mot pour mot le champ `description` du frontmatter, qui fait foi :",
          "> c'est le seul élément toujours présent en contexte, il doit suffire à décider",
          "> d'ouvrir le skill sans le lire. Ne pas éditer à la main (§11).",
          ""]
    return "\n".join(L)


def rendre_ia_readme(agents: list[dict], skills: list[dict], mcp: list[dict]) -> str:
    """README de `IA/`, dérivé lui aussi des frontmatters.

    Il énumérait ses fichiers à la main : `cloture-de-session` y a manqué
    pendant plusieurs jours sans que rien ne le signale.
    """
    L = ["# /IA/ — Définition des agents, skills et outils", "",
         "Toutes les définitions d'agents, de compétences (skills) et d'outils",
         "structurés (MCP) vivent ici. C'est la partie déclarative du coffre.", "",
         "Les règles de format sont au §5 de `system/VAULT-CONTRACT.md`, qui fait foi",
         "et n'est pas reformulé ici.", "",
         "## Agents — `IA/agents/`", ""]
    for a in agents:
        L.append("- **%s** — %s" % (a["name"], a.get("description", "")))
    L += ["", "## Skills — `IA/skills/`", ""]
    for s in skills:
        L.append("- **%s** (`%s`) — %s"
                 % (s["name"], s.get("type", "?"), s.get("description", "")))
    L += ["", "## MCP — `IA/MCP/`", ""]
    for m in mcp:
        L.append("- **%s** (`%s`, permission `%s`) — %s"
                 % (m["name"], m.get("transport", "?"), m.get("permission", "?"),
                    m.get("description", "")))
    L += ["",
          "Gabarit de configuration à compléter côté harness : `MCP/mcp.example.json`.",
          "",
          "## `IA/system/`", "",
          "- `VAULT-CONTRACT.md` — les règles. Fait foi.",
          "- `agents-index.md`, `skills-index.md` — index générés (§11).",
          "- `providers.md` — repère pour choisir un modèle. Aucune clé n'y vit.",
          "- `prompt-fondateur.md` — intention d'origine, non normative.",
          "- `session-log/` — une note par session de travail (§9).",
          "",
          "> Fichier **généré** par `scripts/regenerate_index.py` depuis les",
          "> frontmatters, qui font foi. Ne pas éditer à la main (§11).",
          ""]
    return "\n".join(L)


def lire_mcp(dossier) -> list[dict]:
    """Frontmatters de IA/MCP/, triés par nom. Format décrit au §5."""
    resultats = []
    for chemin in sorted(dossier.glob("*.md")) if dossier.is_dir() else []:
        fm = lire_frontmatter(chemin)
        if fm and fm.get("kind") == "mcp":
            fm["_fichier"] = chemin.name
            resultats.append(fm)
    return resultats


def main() -> int:
    verifier = "--verifier" in sys.argv

    agents = collecter(RACINE / "IA" / "agents", "agent")
    skills = collecter(RACINE / "IA" / "skills", "skill")
    if not agents or not skills:
        print("Aucun agent ou aucun skill collecté — index non régénéré.", file=sys.stderr)
        return 1

    mcp = lire_mcp(RACINE / "IA" / "MCP")

    attendus = {
        RACINE / "IA" / "system" / "agents-index.md": rendre_agents(agents),
        RACINE / "IA" / "system" / "skills-index.md": rendre_skills(agents, skills),
        RACINE / "IA" / "README.md": rendre_ia_readme(agents, skills, mcp),
    }

    perimes, ecrits = [], 0
    for chemin, neuf in attendus.items():
        ancien = chemin.read_text(encoding="utf-8") if chemin.is_file() else None
        if ancien == neuf:
            continue
        rel = chemin.relative_to(RACINE)
        if verifier:
            perimes.append(str(rel))
            continue
        chemin.write_text(neuf, encoding="utf-8")
        print("  ~ %s" % rel)
        ecrits += 1

    if verifier:
        if perimes:
            print("Index périmés (%d) :" % len(perimes), file=sys.stderr)
            for p in perimes:
                print("  - %s" % p, file=sys.stderr)
            print("Lancer : python3 scripts/regenerate_index.py", file=sys.stderr)
            return 1
        print("Index à jour.")
        return 0

    print("Fait. (%d index écrits — %d agent(s), %d skill(s))" % (ecrits, len(agents), len(skills)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
