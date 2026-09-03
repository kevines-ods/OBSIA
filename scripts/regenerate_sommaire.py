#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Régénère les sommaire.md du dossier mémoire/ depuis le contenu des notes.

Un sommaire.md est la couche de résumé d'un dossier : il doit permettre de
décider si une note mérite d'être ouverte, SANS l'ouvrir. Il porte donc, pour
chaque entrée, un statut et un résumé extraits de la note elle-même — jamais
saisis à la main (cf. VAULT-CONTRACT.md §2).

Rien n'est inventé ni résumé par un modèle : tout est prélevé dans les notes.
Un dossier parent reprend les chiffres de ses enfants, de bas en haut.

À exécuter AVANT tout commit, pour garder un diff Git fiable.

Usage :
    python3 scripts/regenerate_sommaire.py
    python3 scripts/regenerate_sommaire.py --verifier   # n'écrit rien, sort 1 si périmé
"""

import os
import re
import sys

RACINE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
MEMOIRE = "mémoire"

LARGEUR_RESUME = 120          # caractères, coupés sur un mot
DATE = re.compile(r"^(\d{4}-\d{2}-\d{2})")

# Sections où chercher un résumé, par ordre de préférence. Au-delà, on prend
# la première section venue.
SECTIONS_PREFEREES = ("statut", "objectif", "résumé", "resume", "synthèse ia", "synthese ia")


# ------------------------------------------------------------------ extraction

def est_prose(ligne: str) -> bool:
    """Vrai si la ligne peut servir de résumé.

    Écarte titres, tableaux, clôtures de bloc, filets, et dessins ASCII —
    plusieurs notes du coffre commencent par un schéma en caractères de
    encadrement, qui ne résume rien.
    """
    nu = ligne.strip()
    if not nu or nu.startswith(("#", "|", "```", "---", "===", ">")):
        return False
    if nu.lstrip("─│┌┐└┘├┤┬┴┼╭╮╰╯ ") == "":
        return False
    return len(re.findall(r"[^\W\d_]", nu)) >= 3      # au moins 3 lettres


def nettoyer(ligne: str) -> str:
    """Retire la décoration Markdown qui n'apporte rien dans une cellule."""
    nu = ligne.strip()
    nu = re.sub(r"^[-*+]\s+", "", nu)                 # puce de liste
    nu = re.sub(r"^\d+\.\s+", "", nu)                 # puce numérotée
    nu = re.sub(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", r"\1", nu)   # rétrolien
    nu = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", nu)  # lien Markdown
    nu = re.sub(r"\*\*|__", "", nu)                    # gras : ne survit pas à la coupe
    nu = nu.replace("|", "\\|")                       # ne pas casser le tableau
    return nu.strip()


def tronquer(texte: str, largeur: int = LARGEUR_RESUME) -> str:
    if len(texte) <= largeur:
        return texte
    coupe = texte[:largeur].rsplit(" ", 1)[0].rstrip(" ,;:—-")
    if coupe.count("`") % 2:          # ne pas laisser un ` ouvert par la coupe
        coupe += "`"
    return coupe + "…"


def decouper_sections(lignes):
    """Renvoie (préambule, [(titre_minuscule, [lignes]), …]).

    Le contenu des blocs de code est écarté d'emblée : il n'y a jamais de
    résumé à y prendre.
    """
    preambule, sections = [], []
    courante, dans_code = None, False

    for ligne in lignes:
        if ligne.strip().startswith("```"):
            dans_code = not dans_code
            continue
        if dans_code:
            continue
        if ligne.startswith("## "):
            courante = (ligne[3:].strip().lower(), [])
            sections.append(courante)
        elif ligne.startswith("# "):
            continue                                  # le H1 est traité à part
        elif courante is None:
            preambule.append(ligne)
        else:
            courante[1].append(ligne)

    return preambule, sections


def lire_note(chemin: str) -> dict:
    """Extrait d'une note son titre, sa date, son statut et son résumé."""
    nom = os.path.basename(chemin)
    try:
        lignes = open(chemin, encoding="utf-8").read().splitlines()
    except (OSError, UnicodeDecodeError) as err:
        print("  ! illisible : %s (%s)" % (nom, err), file=sys.stderr)
        return {"nom": nom, "date": "", "titre": nom, "statut": "—", "resume": "—"}

    m = DATE.match(nom)
    date = m.group(1) if m else ""

    titre = nom
    for ligne in lignes:
        if ligne.startswith("# "):
            titre = re.sub(r"^\d{4}-\d{2}-\d{2}\s*[—–-]\s*", "", ligne[2:].strip())
            break

    preambule, sections = decouper_sections(lignes)
    par_titre = dict(sections)

    statut = "—"
    for ligne in par_titre.get("statut", []):
        if est_prose(ligne):
            statut = tronquer(nettoyer(ligne), 60)
            break

    # Résumé : le préambule d'abord — c'est le chapeau de la note quand il
    # existe — puis les sections préférées, puis la première section utile.
    vus = {"statut"} if statut != "—" else set()
    candidats = [preambule]
    candidats += [par_titre[t] for t in SECTIONS_PREFEREES if t in par_titre and t not in vus]
    candidats += [corps for titre_s, corps in sections if titre_s not in vus]

    resume = "—"
    for corps in candidats:
        prose = [nettoyer(l) for l in corps if est_prose(l)]
        if prose:
            resume = tronquer(" ".join(prose))
            break

    return {"nom": nom, "date": date, "titre": titre, "statut": statut, "resume": resume}


# -------------------------------------------------------------------- collecte

def notes_de(dossier: str):
    return sorted(f for f in os.listdir(dossier)
                  if f.endswith(".md") and f != "sommaire.md"
                  and os.path.isfile(os.path.join(dossier, f)))


def sous_dossiers_de(dossier: str):
    return sorted(d for d in os.listdir(dossier)
                  if not d.startswith(".") and os.path.isdir(os.path.join(dossier, d)))


def agreger(dossier: str, cumul: dict) -> dict:
    """Chiffres d'un dossier, enfants compris. `cumul` porte les résultats déjà
    calculés pour les sous-dossiers — d'où le parcours de bas en haut."""
    total = len(notes_de(dossier))
    dates = [n["date"] for n in (cumul[dossier]["notes"] if dossier in cumul else []) if n["date"]]
    recente = cumul[dossier]["recente"] if dossier in cumul else None

    for sd in sous_dossiers_de(dossier):
        chemin = os.path.join(dossier, sd)
        if chemin in cumul:
            total += cumul[chemin]["total"]
            dates += cumul[chemin]["dates"]
            autre = cumul[chemin]["recente"]
            if autre and (recente is None or autre["date"] > recente["date"]):
                recente = autre

    return {"total": total, "dates": sorted(dates), "recente": recente}


def phrase_couverture(infos: dict, nb_dossiers: int) -> str:
    """Ligne factuelle en tête de sommaire : ce que le dossier couvre.

    Volontairement descriptive et non sémantique — elle est dérivée, donc
    exacte. Aucun modèle n'intervient.
    """
    if not infos["total"]:
        return "Aucune note." if not nb_dossiers else "%d sous-dossier%s, aucune note." % (
            nb_dossiers, "s" if nb_dossiers > 1 else "")

    morceaux = []
    if nb_dossiers:
        morceaux.append("%d sous-dossier%s" % (nb_dossiers, "s" if nb_dossiers > 1 else ""))
    morceaux.append("%d note%s" % (infos["total"], "s" if infos["total"] > 1 else ""))

    phrase = ", ".join(morceaux)
    dates = infos["dates"]
    if dates:
        phrase += (", du %s au %s" % (dates[0], dates[-1])) if dates[0] != dates[-1] \
                  else (", le %s" % dates[0])
    return phrase + "."


# ---------------------------------------------------------------------- rendu

def rendre(dossier: str, cumul: dict) -> str:
    rel = os.path.relpath(dossier, RACINE)
    nom = os.path.basename(dossier)
    dossiers = sous_dossiers_de(dossier)
    notes = cumul[dossier]["notes"]

    L = ["# Sommaire — %s" % nom, ""]
    L += ["> Généré par `scripts/regenerate_sommaire.py` depuis le contenu des notes.",
          "> Ne pas éditer à la main (cf. `VAULT-CONTRACT.md` §2).", ""]
    L += [phrase_couverture(agreger(dossier, cumul), len(dossiers)), ""]

    if dossiers:
        L += ["## Sous-dossiers", "",
              "| Dossier | Notes | Plus récente |", "|---|---|---|"]
        for d in dossiers:
            infos = cumul.get(os.path.join(dossier, d))
            if not infos:
                L.append("| [%s](%s/) | — | — |" % (d, d))
                continue
            r = infos["recente"]
            derniere = "%s — %s" % (r["date"], r["titre"]) if r and r["date"] else \
                       (r["titre"] if r else "—")
            L.append("| [%s](%s/) | %d | %s |" % (d, d, infos["total"], derniere))
        L.append("")

    if notes:
        L += ["## Notes", "", "| Note | Statut | Résumé |", "|---|---|---|"]
        for n in notes:
            L.append("| [%s](%s) | %s | %s |" % (n["titre"], n["nom"], n["statut"], n["resume"]))
        L.append("")

    L += ["> Chemin dans le coffre : `%s/`" % rel, ""]
    return "\n".join(L)


# ----------------------------------------------------------------------- main

def main() -> int:
    verifier = "--verifier" in sys.argv
    racine_memoire = os.path.join(RACINE, MEMOIRE)
    if not os.path.isdir(racine_memoire):
        print("Dossier introuvable : %s" % racine_memoire, file=sys.stderr)
        return 1

    # Bas vers le haut : un parent lit les chiffres déjà calculés de ses enfants.
    dossiers = []
    for chemin, sous, _ in os.walk(racine_memoire):
        sous[:] = [d for d in sous if not d.startswith(".")]
        dossiers.append(chemin)
    dossiers.sort(key=lambda p: p.count(os.sep), reverse=True)

    cumul = {}
    for chemin in dossiers:
        notes = [lire_note(os.path.join(chemin, f)) for f in notes_de(chemin)]
        datees = [n for n in notes if n["date"]]
        cumul[chemin] = {"notes": notes,
                         "recente": max(datees, key=lambda n: n["date"]) if datees else None}
        cumul[chemin].update(agreger(chemin, cumul))

    perimes, ecrits = [], 0
    for chemin in sorted(dossiers):
        if not (cumul[chemin]["notes"] or sous_dossiers_de(chemin)):
            continue                                   # dossier vide : pas de sommaire
        cible = os.path.join(chemin, "sommaire.md")
        neuf = rendre(chemin, cumul)
        ancien = open(cible, encoding="utf-8").read() if os.path.isfile(cible) else None
        if ancien == neuf:
            continue
        rel = os.path.relpath(cible, RACINE)
        if verifier:
            perimes.append(rel)
            continue
        open(cible, "w", encoding="utf-8").write(neuf)
        print("  %s %s" % ("~" if ancien is not None else "+", rel))
        ecrits += 1

    if verifier:
        if perimes:
            print("Sommaires périmés (%d) :" % len(perimes), file=sys.stderr)
            for p in perimes:
                print("  - %s" % p, file=sys.stderr)
            print("Lancer : python3 scripts/regenerate_sommaire.py", file=sys.stderr)
            return 1
        print("Sommaires à jour.")
        return 0

    print("Fait. (%d sommaire.md écrits)" % ecrits)
    return 0


if __name__ == "__main__":
    sys.exit(main())
