#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Évalue le ROUTAGE des skills : le bon skill sort-il devant, et deux
descriptions se marchent-elles dessus ?

`verifier_coffre.py` contrôle la forme : frontmatter valide, chemins qui
mènent quelque part, index à jour. Il ne dit rien de la seule chose qui
décide qu'un skill se charge — sa `description`, unique élément toujours
présent en contexte. Avec plus de trente skills, deux descriptions proches
suffisent à ce que le mauvais réponde, sans qu'aucun contrôle ne bronche.

Deux mesures, toutes deux déterministes et sans réseau :

  · le CLASSEMENT — pour chaque demande de `IA/system/routage-attendu.md`,
    le skill attendu doit figurer dans les premiers rangs ;
  · les COLLISIONS — deux descriptions trop semblables sont signalées.

C'est une approximation lexicale, pas une compréhension. Elle n'attrape pas
la sémantique, mais elle attrape les deux pannes réelles : une description
à laquelle manque le vocabulaire que l'utilisateur emploie, et une
description trop large qui passe devant la bonne.

**Un échec veut dire « corriger la description », pas « corriger le test ».**

Usage :
    python3 scripts/evaluer_routage.py
    python3 scripts/evaluer_routage.py --explique "je veux publier mon site"
    python3 scripts/evaluer_routage.py --seuil-collision 0.7
"""

import argparse
import math
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from generer_prompt import RACINE_DEFAUT, fichiers_declaratifs, lire_frontmatter

RACINE = RACINE_DEFAUT
ATTENDU = RACINE / "IA" / "system" / "routage-attendu.md"

SEUIL_COLLISION = 0.62      # au-delà, deux descriptions se ressemblent trop
POIDS_DU_NOM = 3            # le nom du skill porte souvent le mot que l'on dit

# Les exemptions vivent ICI, dans le script, jamais dans le frontmatter d'un
# skill : sinon un skill se déclare lui-même dispensé du contrôle, et le
# contrôle ne vaut plus rien. Chaque entrée porte sa raison.
COLLISIONS_ADMISES = {
    frozenset(("diagnostic-linux", "remediation-linux")):
        "paire constater/agir assumée — les descriptions se renvoient l'une à l'autre",
    frozenset(("conteneurs-docker", "traefik")):
        "deux couches du même symptôme, chaque description dit quand prendre l'autre",
}

VIDES = {
    "je", "tu", "il", "elle", "on", "nous", "vous", "ils", "me", "te", "se",
    "un", "une", "des", "le", "la", "les", "de", "du", "dans", "en", "et",
    "ou", "que", "qui", "quoi", "dont", "pour", "avec", "sans", "sur", "sous",
    "par", "ce", "cet", "cette", "ces", "mon", "ma", "mes", "ton", "ta",
    "son", "sa", "ses", "au", "aux", "est", "sont", "ont", "ai", "as", "eu",
    "etre", "avoir", "plus", "moins", "pas", "ne", "ni", "si", "comme",
    "tout", "tous", "toute", "toutes", "mais", "donc", "car", "quand",
    "tres", "bien", "alors", "aussi", "avant", "apres", "chez", "entre",
    "vers", "depuis", "leur", "leurs", "y", "a", "l", "d", "s", "n", "c",
    "j", "m", "t", "qu", "faire", "fait", "veux", "veut", "dois", "doit",
    "peux", "peut", "charger", "skill", "quand", "puis", "ici", "cela",
}

# Suffixes du plus long au plus court : la première coupe qui laisse un
# radical d'au moins quatre lettres gagne.
SUFFIXES = ("ements", "ement", "ations", "ation", "ateurs", "ateur",
            "issons", "issent", "aient", "erait", "eront", "ions",
            "ites", "ite", "eurs", "eur", "euses", "euse", "ives", "ive",
            "irait", "irons", "iront", "ent", "ant",
            "aux", "als", "ers", "er", "ir", "ez", "es", "s", "e")


def sans_accent(texte: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texte)
                   if unicodedata.category(c) != "Mn")


MIN_RADICAL = 3


def radical(mot: str) -> str:
    """Coupe le plus long suffixe qui laisse un radical de trois lettres.

    Trois et non quatre : à quatre, `fige` et `figer` restaient deux jetons
    distincts, et `ecris` ne rejoignait pas `ecrire`. C'est la panne la plus
    fréquente d'un appariement lexical en français, où la conjugaison
    sépare ce que le sens réunit.
    """
    if len(mot) <= 4:
        return mot
    for suffixe in SUFFIXES:
        if mot.endswith(suffixe) and len(mot) - len(suffixe) >= MIN_RADICAL:
            mot = mot[:-len(suffixe)]
            break
    # `déployer` donne `deploy`, `déploie` donne `deploi` : l'alternance
    # -oyer/-oie du français sépare deux formes du même verbe. Ramener un `y`
    # final sur `i` les réunit, comme le fait l'algorithme de Porter.
    return mot[:-1] + "i" if mot.endswith("y") else mot


def jetons(texte: str) -> list[str]:
    nu = sans_accent(texte.lower())
    bruts = re.findall(r"[a-z0-9]+", nu)
    return [radical(m) for m in bruts if m not in VIDES and len(m) > 1]


# ------------------------------------------------------------------ TF-IDF

def construire_index(skills):
    """Renvoie (sacs, idf) — un sac de jetons pondéré par skill."""
    sacs = {}
    for s in skills:
        mots = jetons(s.get("description", ""))
        mots += jetons(s["name"].replace("-", " ")) * POIDS_DU_NOM
        sacs[s["name"]] = Counter(mots)
    total = len(sacs)
    presence = Counter(j for sac in sacs.values() for j in sac)
    idf = {j: math.log(1 + total / (1 + n)) for j, n in presence.items()}
    return sacs, idf


def vecteur(sac, idf):
    return {j: (1 + math.log(n)) * idf.get(j, 0.0) for j, n in sac.items()}


def cosinus(a, b):
    if not a or not b:
        return 0.0
    commun = set(a) & set(b)
    haut = sum(a[j] * b[j] for j in commun)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return haut / (na * nb) if na and nb else 0.0


def classer(demande, sacs, idf):
    """Les skills, du plus au moins pertinent pour la demande."""
    q = vecteur(Counter(jetons(demande)), idf)
    scores = [(nom, cosinus(q, vecteur(sac, idf))) for nom, sac in sacs.items()]
    return sorted(scores, key=lambda t: (-t[1], t[0]))


# ------------------------------------------------- le registre des demandes

LIGNE = re.compile(r"^\|(?!\s*-)(.+)\|\s*$")


def lire_attendu(chemin: Path):
    """Lit le tableau de `routage-attendu.md`.

    Quatre colonnes : demande · skill attendu · rang au plus · ne doit pas
    devancer (`—` si rien).
    """
    if not chemin.is_file():
        return None
    cas = []
    for ligne in chemin.read_text(encoding="utf-8").splitlines():
        m = LIGNE.match(ligne.rstrip())
        if not m:
            continue
        cells = [c.strip() for c in m.group(1).split("|")]
        if len(cells) != 4 or cells[0].lower().startswith("demande"):
            continue
        demande = cells[0].strip("«» ").strip()
        attendu = cells[1].strip("`")
        try:
            rang = int(cells[2])
        except ValueError:
            continue
        rival = cells[3].strip("`")
        cas.append((demande, attendu, rang, None if rival in ("—", "-", "") else rival))
    return cas


# ----------------------------------------------------------------- rapports

def evaluer(cas, sacs, idf):
    echecs = []
    for demande, attendu, rang_max, rival in cas:
        classement = classer(demande, sacs, idf)
        noms = [n for n, _ in classement]
        if attendu not in noms:
            echecs.append((demande, "`%s` n'existe pas dans IA/skills/" % attendu, []))
            continue
        rang = noms.index(attendu) + 1
        tete = ["%s (%.2f)" % (n, s) for n, s in classement[:3]]
        if classement[noms.index(attendu)][1] == 0.0:
            echecs.append((demande, "`%s` ne partage aucun mot avec la demande — "
                           "sa description n'a pas ce vocabulaire" % attendu, tete))
        elif rang > rang_max:
            echecs.append((demande, "`%s` sort au rang %d, attendu %d au plus"
                           % (attendu, rang, rang_max), tete))
        elif rival and rival in noms and noms.index(rival) < noms.index(attendu):
            echecs.append((demande, "`%s` devance `%s`" % (rival, attendu), tete))
    return echecs


def collisions(sacs, idf, seuil):
    trouvees = []
    noms = sorted(sacs)
    for i, a in enumerate(noms):
        for b in noms[i + 1:]:
            score = cosinus(vecteur(sacs[a], idf), vecteur(sacs[b], idf))
            if score < seuil:
                continue
            raison = COLLISIONS_ADMISES.get(frozenset((a, b)))
            trouvees.append((a, b, score, raison))
    return trouvees


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--explique", metavar="DEMANDE",
                    help="affiche le classement pour une demande, et sort")
    ap.add_argument("--seuil-collision", type=float, default=SEUIL_COLLISION)
    opts = ap.parse_args()

    skills = [fm for fm in (lire_frontmatter(p)
                            for p in fichiers_declaratifs(RACINE / "IA" / "skills"))
              if fm and fm.get("name")]
    if not skills:
        print("Aucun skill lisible dans IA/skills/", file=sys.stderr)
        return 2
    sacs, idf = construire_index(skills)

    if opts.explique:
        print("Demande : %s\n" % opts.explique)
        for rang, (nom, score) in enumerate(classer(opts.explique, sacs, idf)[:8], 1):
            marque = "→" if rang == 1 else " "
            print(" %s %d. %-28s %.3f" % (marque, rang, nom, score))
        return 0

    cas = lire_attendu(ATTENDU)
    if cas is None:
        print("Registre absent : IA/system/routage-attendu.md", file=sys.stderr)
        return 2
    if not cas:
        print("Registre vide — aucune demande à évaluer.", file=sys.stderr)
        return 2

    echecs = evaluer(cas, sacs, idf)
    heurts = [(a, b, s) for a, b, s, raison in collisions(sacs, idf, opts.seuil_collision)
              if raison is None]
    admis = [(a, b, s, r) for a, b, s, r in collisions(sacs, idf, opts.seuil_collision)
             if r is not None]

    for a, b, s, r in admis:
        print("  · collision admise : %s ↔ %s (%.2f) — %s" % (a, b, s, r))

    if not echecs and not heurts:
        print("Routage sain : %d demande(s) bien classée(s), %d skill(s), "
              "aucune collision au-delà de %.2f."
              % (len(cas), len(sacs), opts.seuil_collision))
        return 0

    if echecs:
        print("\nRoutage — %d demande(s) mal classée(s) :" % len(echecs),
              file=sys.stderr)
        for demande, motif, tete in echecs:
            print("  ✗ « %s »" % demande, file=sys.stderr)
            print("      %s" % motif, file=sys.stderr)
            if tete:
                print("      en tête : %s" % ", ".join(tete), file=sys.stderr)

    if heurts:
        print("\nCollisions — %d paire(s) de descriptions trop proches :" % len(heurts),
              file=sys.stderr)
        for a, b, s in heurts:
            print("  ✗ %s ↔ %s (%.2f)" % (a, b, s), file=sys.stderr)

    print("\nUn échec ici veut dire : corriger la `description` du skill —", file=sys.stderr)
    print("c'est elle qui décide du déclenchement, pas ce registre.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        # `--explique | head` ferme le tuyau avant la fin : ce n'est pas une
        # erreur du script, et une trace de pile ferait croire le contraire.
        sys.stderr.close()
        sys.exit(0)
