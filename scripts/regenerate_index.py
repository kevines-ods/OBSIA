#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Régénère les index dérivés de `IA/` : `IA/system/agents-index.md`,
`skills-index.md`, `taches-index.md`, `modules-index.md` et `IA/README.md`.

Ces index sont **dérivés** des frontmatters, qui font foi. Les maintenir à
la main les fait diverger sans que rien ne le signale — c'est arrivé, voir
0-MEMOIRES/assistant/expériences/index-maintenus-a-la-main.md.

Les cinq fichiers sont **versionnés** : ils décrivent le catalogue entier,
jamais un coffre réduit à un profil. `obsia.local.yml` (§13) ne les lit ni
ne les filtre ; il ne réduit que ce qui n'est pas versionné — le prompt
système et `AGENTS.md`, produits par `generer_prompt.py` / `installer.py`.

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
          "> ponctuelle. (cf. `VAULT-CONTRACT.md` §5 et `contrat/contrat-frontmatter.md`)",
          "",
          "> Fichier **généré** par `scripts/regenerate_index.py`. La colonne description",
          "> reproduit mot pour mot le champ `description` du frontmatter, qui fait foi :",
          "> c'est le seul élément toujours présent en contexte, il doit suffire à décider",
          "> d'ouvrir le skill sans le lire. Ne pas éditer à la main (§11).",
          ""]
    return "\n".join(L)


def rendre_taches(taches: list[dict]) -> str:
    """Index des tâches planifiées — pendant de `skills-index.md` pour `IA/tâches/`.

    Toujours présent en contexte : c'est par lui qu'un harness neuf apprend
    qu'une tâche existe. Il ne la déclenche pas pour autant (§12).
    """
    L = ["# taches-index.md — Index des tâches planifiées", "",
         "| Tâche | Quand | Fuseau | Mode | Exécutant | Agent | Active | Description |",
         "|---|---|---|---|---|---|---|---|"]
    for t_ in taches:
        L.append("| [%s](../tâches/%s) | `%s` | %s | %s | %s | %s | %s | %s |"
                 % (t_["name"], t_["_fichier"], t_.get("quand", "?"),
                    t_.get("fuseau", "?"), t_.get("mode", "?"),
                    t_.get("exécutant", "?"), t_.get("agent", "—"),
                    "oui" if t_.get("actif") else "non",
                    t_.get("description", "")))
    if not taches:
        L.append("| — | | | | | | | Aucune tâche déclarée. |")
    L += ["",
          "> Le registre `IA/tâches/` **déclare** ; rien ne s'instancie tout seul.",
          "> Une tâche listée ici n'est pas forcément planifiée sur la machine",
          "> courante : charger le skill `cron` pour instancier ou réconcilier",
          "> (cf. `VAULT-CONTRACT.md` §12).",
          "",
          "> `Exécutant` dit qui a le droit de déclencher — et donc qui pas :",
          "> une tâche = **au plus une instance vivante**, tous exécutants",
          "> confondus. Planifier la même chose côté harness *et* côté machine",
          "> la déclenche deux fois.",
          "",
          "> Fichier **généré** par `scripts/regenerate_index.py` depuis les",
          "> frontmatters, qui font foi. Ne pas éditer à la main (§11).",
          ""]
    return "\n".join(L)


def rendre_ia_readme(agents: list[dict], skills: list[dict], mcp: list[dict],
                     taches: list[dict]) -> str:
    """README de `IA/`, dérivé lui aussi des frontmatters.

    Il énumérait ses fichiers à la main : `cloture-de-session` y a manqué
    pendant plusieurs jours sans que rien ne le signale.
    """
    L = ["# /IA/ — Définition des agents, skills, outils et tâches", "",
         "Toutes les définitions d'agents, de compétences (skills), d'outils",
         "structurés (MCP) et de tâches planifiées vivent ici. C'est la partie",
         "déclarative du coffre.", "",
         "Les règles de format sont au §5 du contrat `system/VAULT-CONTRACT.md`,",
         "et le détail des champs dans `system/contrat/contrat-frontmatter.md` ;",
         "les deux font foi et ne sont pas reformulés ici.", "",
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
          "## Tâches planifiées — `IA/tâches/`", "",
          "Le registre fait foi ; timers et planificateurs n'en sont que des",
          "instances reconstructibles (§12). Procédure dans le skill `cron`.", ""]
    if taches:
        for t_ in taches:
            suspendue = "" if t_.get("actif") else "  — **suspendue**"
            L.append("- **%s** (`%s`, %s, mode `%s`, exécutant `%s`) — %s%s"
                     % (t_["name"], t_.get("quand", "?"), t_.get("fuseau", "?"),
                        t_.get("mode", "?"), t_.get("exécutant", "?"),
                        t_.get("description", ""), suspendue))
    else:
        L.append("Aucune tâche déclarée.")
    L += ["",
          "## `IA/system/`", "",
          "- `VAULT-CONTRACT.md` — les règles. Fait foi.",
          "- `agents-index.md`, `skills-index.md`, `taches-index.md`,",
          "  `modules-index.md` — index générés (§11).",
          "- `modules/` — le catalogue de modules installables (§13). Un module",
          "  regroupe ce qui n'a de sens qu'ensemble ; quels modules sont retenus",
          "  ici se lit dans `obsia.local.yml`, s'il existe ; son absence vaut",
          "  catalogue complet.",
          "- `providers.md` — repère pour choisir un modèle. Aucune clé n'y vit.",
          "- `prompt-fondateur.md` — intention d'origine, non normative.",
          "- `session-log/` — archives : on n'y écrit plus, les carnets (§6) le",
          "  remplacent (§9).",
          "",
          "Le registre des tâches planifiées vit à côté, dans `IA/tâches/` (§12) ;",
          "`system/taches-index.md` en est l'index généré.",
          "",
          "> Fichier **généré** par `scripts/regenerate_index.py` depuis les",
          "> frontmatters, qui font foi. Ne pas éditer à la main (§11).",
          ""]
    return "\n".join(L)


def rendre_modules(modules: list[dict], contenu: dict[str, int]) -> str:
    """Index du catalogue de modules — ce qui existe, et ce que chacun apporte.

    Toujours présent en contexte : c'est par lui qu'on sait qu'un module
    écarté *existe*, et donc qu'on peut le retenir plus tard. Un catalogue
    dont on ignore les entrées absentes n'est pas un catalogue, c'est une
    liste (§13).

    Le catalogue est montré **entier** : ce fichier est versionné, donc il ne
    dépend pas de la machine. Il n'a pas de colonne « retenu ici » — avec un
    profil, elle vaudrait « oui » partout et ne dirait rien ; sans profil, tout
    est retenu. Quels modules le sont se lit dans `obsia.local.yml`, s'il existe.
    """
    L = ["# modules-index.md — Index des modules installables", "",
         "| Module | Essentiel | Déclarations | Sondes | Requiert | Description |",
         "|---|---|---|---|---|---|"]
    for m in modules:
        nom = m["name"]
        L.append("| [%s](modules/%s) | %s | %d | %s | %s | %s |" % (
            nom, m["_fichier"],
            "oui" if m.get("essentiel") else "non",
            contenu.get(nom, 0),
            ", ".join("`%s`" % s for s in m.get("sondes", [])) or "—",
            ", ".join(m.get("requiert", [])) or "—",
            m.get("description", "")))
    L += ["",
          "> Ce fichier montre le **catalogue complet** : versionné, il ne dépend",
          "> pas de la machine, et ne se réduit jamais au profil. Quels modules",
          "> sont retenus *ici* se lit dans `obsia.local.yml`, s'il existe ; son",
          "> absence vaut catalogue complet (cf. `VAULT-CONTRACT.md` §13 et",
          "> `contrat/contrat-distribution.md`).",
          "",
          "> Retenir un module écarté, ou en écarter un autre :",
          "> `python3 scripts/installer.py --appliquer`. L'installeur sonde la",
          "> machine, propose, et n'écrit qu'avec `--appliquer`.",
          "",
          "> Fichier **généré** par `scripts/regenerate_index.py` depuis les",
          "> frontmatters, qui font foi. Ne pas éditer à la main (§11).",
          ""]
    return "\n".join(L)


def lire_modules_locaux(racine) -> list[dict]:
    """Frontmatters de IA/system/modules/, noyau d'abord puis par nom (§13)."""
    resultats = []
    dossier = racine / "IA" / "system" / "modules"
    for chemin in sorted(dossier.glob("*.md")) if dossier.is_dir() else []:
        fm = lire_frontmatter(chemin)
        if fm and fm.get("kind") == "module":
            fm["_fichier"] = chemin.name
            fm.setdefault("requiert", [])
            fm.setdefault("sondes", [])
            resultats.append(fm)
    return sorted(resultats, key=lambda m: (not m.get("essentiel"), m["name"]))


def lire_taches(dossier) -> list[dict]:
    """Frontmatters de IA/tâches/, triés par nom. Format décrit au §5."""
    resultats = []
    for chemin in sorted(dossier.glob("*.md")) if dossier.is_dir() else []:
        fm = lire_frontmatter(chemin)
        if fm and fm.get("kind") == "tâche":
            fm["_fichier"] = chemin.name
            resultats.append(fm)
    return resultats


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
    mcp = lire_mcp(RACINE / "IA" / "MCP")
    taches = lire_taches(RACINE / "IA" / "tâches")
    modules = lire_modules_locaux(RACINE)

    # Le catalogue entier alimente les compteurs : les index montrent tout ce
    # que le coffre déclare, sans jamais le réduire au profil (§13).
    contenu: dict[str, int] = {}
    for fm in agents + skills + mcp + taches:
        if fm.get("module"):
            contenu[fm["module"]] = contenu.get(fm["module"], 0) + 1

    if not agents or not skills:
        print("Aucun agent ou aucun skill collecté — index non régénéré.", file=sys.stderr)
        return 1

    attendus = {
        RACINE / "IA" / "system" / "agents-index.md": rendre_agents(agents),
        RACINE / "IA" / "system" / "skills-index.md": rendre_skills(agents, skills),
        RACINE / "IA" / "system" / "taches-index.md": rendre_taches(taches),
        RACINE / "IA" / "system" / "modules-index.md": rendre_modules(modules, contenu),
        RACINE / "IA" / "README.md": rendre_ia_readme(agents, skills, mcp, taches),
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
