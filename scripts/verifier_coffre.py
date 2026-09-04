#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vérifie la cohérence du coffre OBSIA. N'écrit rien.

Le contrat pose des règles strictes (§5 frontmatter, §6 nommage) que rien ne
contrôlait : un index a pu affirmer pendant des mois qu'un agent disposait de
skills qu'il ne déclarait pas. Ce script confronte les fichiers entre eux.

Sort 0 si tout est cohérent, 1 sinon. Prévu pour la CI comme pour la main.

Usage :
    python3 scripts/verifier_coffre.py
    python3 scripts/verifier_coffre.py --silencieux   # n'affiche que les erreurs
"""

import os
import re
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from generer_prompt import RACINE_DEFAUT, fichiers_declaratifs, lire_frontmatter

RACINE = RACINE_DEFAUT

CHAMPS_COMMUNS = ("schema", "kind", "name", "description", "read_only")
NOM_VALIDE = re.compile(r"^[^\W_]+(?:-[^\W_]+)*$", re.UNICODE)   # minuscules-et-tirets, accents admis
TYPES_SKILL = ("core", "outil")

erreurs: list[str] = []
avertissements: list[str] = []


def erreur(chemin, message):
    erreurs.append("%s : %s" % (chemin, message))


def avertir(chemin, message):
    avertissements.append("%s : %s" % (chemin, message))


# ------------------------------------------------------------------ frontmatter

def ligne_description_brute(chemin: Path) -> str | None:
    """La ligne `description:` telle qu'écrite, pour détecter un scalaire replié."""
    dans_fm = False
    for ligne in chemin.read_text(encoding="utf-8").splitlines():
        if ligne.strip() == "---":
            if dans_fm:
                return None
            dans_fm = True
            continue
        if dans_fm and ligne.startswith("description:"):
            return ligne
    return None


def verifier_fichier(chemin: Path, genre: str) -> dict | None:
    fm = lire_frontmatter(chemin)
    rel = chemin.relative_to(RACINE)

    if fm is None:
        erreur(rel, "frontmatter absent ou non fermé")
        return None

    for champ in CHAMPS_COMMUNS:
        if champ not in fm:
            erreur(rel, "champ obligatoire manquant : `%s` (§5)" % champ)

    if fm.get("kind") != genre:
        erreur(rel, "`kind: %s` alors que le fichier est dans le dossier des %ss (§5)"
               % (fm.get("kind"), genre))

    nom = fm.get("name")
    if nom:
        if nom != chemin.stem:
            erreur(rel, "`name: %s` ≠ nom du fichier `%s` (§5)" % (nom, chemin.stem))
        if not NOM_VALIDE.match(nom):
            erreur(rel, "`name: %s` — attendu : minuscules et tirets, sans espace (§5)" % nom)

    if not isinstance(fm.get("read_only"), bool):
        erreur(rel, "`read_only` doit valoir true ou false (§5)")

    if not isinstance(fm.get("schema"), int):
        erreur(rel, "`schema` doit être un entier (§5)")

    # description : présente, sur une seule ligne physique
    desc = fm.get("description")
    brute = ligne_description_brute(chemin)
    if not desc:
        erreur(rel, "`description` vide ou absente (§5)")
    elif desc.strip() in (">", "|", ">-", "|-"):
        erreur(rel, "`description` est un scalaire replié YAML — non géré par "
                    "lire_frontmatter(), la valeur devient « %s ». Une seule ligne physique."
               % desc.strip())
    elif brute and brute.rstrip().endswith((":", ">", "|")):
        erreur(rel, "`description` semble se poursuivre sur la ligne suivante — "
                    "une seule ligne physique est acceptée")

    if genre == "skill" and fm.get("type") not in TYPES_SKILL:
        erreur(rel, "`type: %s` — attendu `core` ou `outil` (§5)" % fm.get("type"))

    for champ in ("skills", "mcp"):
        if champ in fm and not isinstance(fm[champ], list):
            erreur(rel, "`%s` vaut une chaîne, pas une liste — une entrée par ligne "
                        "précédée d'un tiret (§5)" % champ)

    if fm:
        fm["_chemin"] = rel
    return fm


# ---------------------------------------------------------------------- checks

TRANSPORTS = ("stdio", "http")
PERMISSIONS = ("normal", "elevated")


def verifier_mcp(dossier: Path) -> list[dict]:
    """Frontmatter des fichiers de IA/MCP/ (§5).

    Format distinct de celui des agents et des skills : pas de `read_only`,
    mais `transport` et `permission`.
    """
    resultats = []
    for chemin in sorted(dossier.glob("*.md")) if dossier.is_dir() else []:
        fm = lire_frontmatter(chemin)
        rel = chemin.relative_to(RACINE)
        if fm is None:
            erreur(rel, "frontmatter absent ou non fermé")
            continue
        for champ in ("schema", "kind", "name", "description", "type",
                      "transport", "permission"):
            if champ not in fm:
                erreur(rel, "champ obligatoire manquant : `%s` (§5)" % champ)
        if fm.get("kind") != "mcp":
            erreur(rel, "`kind: %s` attendu `mcp` (§5)" % fm.get("kind"))
        if fm.get("name") and fm["name"] != chemin.stem:
            erreur(rel, "`name: %s` ≠ nom du fichier `%s` (§5)" % (fm["name"], chemin.stem))
        if fm.get("transport") not in TRANSPORTS:
            erreur(rel, "`transport: %s` — attendu %s (§5)"
                   % (fm.get("transport"), " ou ".join(TRANSPORTS)))
        if fm.get("permission") not in PERMISSIONS:
            erreur(rel, "`permission: %s` — attendu %s (§5)"
                   % (fm.get("permission"), " ou ".join(PERMISSIONS)))
        fm["_chemin"] = rel
        resultats.append(fm)
    return resultats


def verifier_references(agents, skills):
    """Un agent ne déclare que des skills et des MCP qui existent."""
    connus = {s["name"] for s in skills if s.get("name")}
    mcp_connus = {p.stem for p in (RACINE / "IA" / "MCP").glob("*.md")} \
        if (RACINE / "IA" / "MCP").is_dir() else set()

    for a in agents:
        for s in a.get("skills", []):
            if s not in connus:
                erreur(a["_chemin"], "déclare le skill `%s`, qui n'existe pas dans IA/skills/" % s)
        for m in a.get("mcp", []):
            if m not in mcp_connus:
                erreur(a["_chemin"], "déclare le MCP `%s`, qui n'existe pas dans IA/MCP/" % m)

    utilises = {s for a in agents for s in a.get("skills", [])}
    for s in skills:
        if s.get("name") and s["name"] not in utilises:
            avertir(s["_chemin"], "skill déclaré par aucun agent")

    actifs = {m for a in agents for m in a.get("mcp", [])}
    for p in sorted((RACINE / "IA" / "MCP").glob("*.md")) if (RACINE / "IA" / "MCP").is_dir() else []:
        if p.stem not in actifs:
            avertir(p.relative_to(RACINE),
                    "MCP déclaré par aucun agent — inutilisable en l'état (§10.2)")


def verifier_forme_dossier(dossier: Path, genre: str):
    """Un skill en forme dossier doit porter son point d'entrée (§5).

    Vérifie aussi que les fichiers extraits dans `references/` sont bien cités
    depuis le corps : un fichier qu'on ne sait pas exister n'est jamais lu —
    c'est la règle de `createur-de-skill`.
    """
    if not dossier.is_dir():
        return
    for sous in sorted(dossier.iterdir()):
        if not sous.is_dir() or sous.name.startswith("."):
            continue
        entree = sous / (sous.name + ".md")
        rel = sous.relative_to(RACINE)
        if not entree.is_file():
            erreur(rel, "dossier de %s sans point d'entrée `%s.md` (§5). "
                        "Le point d'entrée porte le nom du dossier, pas `SKILL.md`."
                   % (genre, sous.name))
            continue

        corps = entree.read_text(encoding="utf-8")
        for annexe in sorted((sous / "references").glob("**/*")):
            if not annexe.is_file():
                continue
            if annexe.name not in corps:
                avertir(rel, "`references/%s` n'est cité nulle part dans `%s.md` — "
                             "un fichier qu'on ne sait pas exister n'est jamais lu"
                        % (annexe.relative_to(sous / "references").as_posix(), sous.name))


# Formes réelles sous lesquelles un nom d'agent apparaît dans le coffre :
#   l'agent `assistant`   ·   un agent « untel »   ·   agent[untel] --> …
# Le nom capturé doit ressembler à un nom : lettres, chiffres, tirets, espaces.
# Exclure « : » et « | » écarte `read_only: false` et les séparateurs de tableau.
AGENT_NOMME = re.compile(
    r"agents?\s*[«\"`\[]\s*([^\W\d_][\w \-]{1,39}?)\s*[»\"`\]]", re.UNICODE)


def verifier_agents_nommes(agents):
    """§1 : seul un agent qui a son fichier dans IA/agents/ peut être nommé.

    Nommer un agent avant qu'il existe le fait exister dans les têtes — c'est
    ainsi qu'un agent fantôme s'est installé dans ce coffre pendant des mois.
    """
    declares = {a["name"] for a in agents if a.get("name")}
    for chemin in sorted(RACINE.rglob("*.md")):
        if any(part.startswith(".") for part in chemin.relative_to(RACINE).parts):
            continue
        rel = chemin.relative_to(RACINE)
        try:
            texte = chemin.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for cite in {m.group(1) for m in AGENT_NOMME.finditer(texte)}:
            if cite in declares:
                continue
            # contre-exemples de nommage de dossier : ne désignent personne
            if re.fullmatch(r"agents?\s*\d+", cite) or cite.startswith(("nom-", "<")):
                continue
            erreur(rel, "nomme l'agent `%s`, qui n'a pas de fichier dans "
                        "IA/agents/ (§1 : seul un agent existant peut être nommé)" % cite)


def verifier_unicite_des_noms():
    """§6 : les noms de notes doivent être uniques dans tout le coffre parent.

    On ne peut pas voir le coffre parent depuis ici ; on vérifie donc l'unicité
    à l'intérieur d'OBSIA, qui en est la condition nécessaire.
    """
    banals = {"sommaire.md", "README.md"}          # légitimement répétés
    vus: dict[str, list[str]] = {}
    for chemin, sous, fichiers in os.walk(RACINE):
        sous[:] = [d for d in sous
                   if not d.startswith(".") and d not in ("scripts", "assets")]
        for f in fichiers:
            if f.endswith(".md") and f not in banals:
                vus.setdefault(f, []).append(
                    str(Path(chemin).joinpath(f).relative_to(RACINE)))
    for nom, chemins in sorted(vus.items()):
        if len(chemins) > 1:
            erreur(nom, "nom de note en double, les rétroliens deviennent ambigus (§6) : %s"
                   % ", ".join(chemins))


def verifier_derives():
    """Index et sommaires doivent être à jour vis-à-vis de leurs sources."""
    for script, quoi in (("regenerate_index.py", "index"),
                         ("regenerate_sommaire.py", "sommaires")):
        res = subprocess.run([sys.executable, str(SCRIPTS / script), "--verifier"],
                             capture_output=True, text=True, cwd=str(RACINE))
        if res.returncode != 0:
            detail = (res.stderr or res.stdout).strip().replace("\n", " / ")
            erreur("scripts/%s" % script, "%s périmés — %s" % (quoi, detail))


# ----------------------------------------------------------------------- main

def main() -> int:
    silencieux = "--silencieux" in sys.argv

    dossier_agents = RACINE / "IA" / "agents"
    dossier_skills = RACINE / "IA" / "skills"

    agents = [fm for fm in (verifier_fichier(p, "agent")
                            for p in fichiers_declaratifs(dossier_agents)) if fm]
    skills = [fm for fm in (verifier_fichier(p, "skill")
                            for p in fichiers_declaratifs(dossier_skills)) if fm]

    verifier_forme_dossier(dossier_agents, "agent")
    verifier_forme_dossier(dossier_skills, "skill")

    if not agents:
        erreur("IA/agents/", "aucun agent valide trouvé")
    if not skills:
        erreur("IA/skills/", "aucun skill valide trouvé")

    verifier_mcp(RACINE / "IA" / "MCP")
    verifier_references(agents, skills)
    verifier_agents_nommes(agents)
    verifier_unicite_des_noms()
    verifier_derives()

    if avertissements and not silencieux:
        print("Avertissements (%d) :" % len(avertissements))
        for a in avertissements:
            print("  · %s" % a)

    if erreurs:
        print("\nCoffre incohérent — %d erreur(s) :" % len(erreurs), file=sys.stderr)
        for e in erreurs:
            print("  ✗ %s" % e, file=sys.stderr)
        print("\nLes numéros de § renvoient à IA/system/VAULT-CONTRACT.md.", file=sys.stderr)
        return 1

    if not silencieux:
        print("Coffre cohérent : %d agent(s), %d skill(s), index et sommaires à jour."
              % (len(agents), len(skills)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
