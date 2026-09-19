#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Produit le miroir public d'OBSIA à partir de ce dépôt, qui fait foi.

Ce dépôt-ci est privé : il porte la mémoire, les logs de session et le profil
d'installation de son propriétaire. Le dépôt public est la **distribution** :
le même coffre, moins ce qui décrit une personne et une machine.

Il n'y a pas deux sources de vérité. Ce script en dérive une seconde, et il
refuse de publier ce qu'il ne sait pas relire.

    python3 scripts/publier.py --cible ~/OBSIA-public              # aperçu
    python3 scripts/publier.py --cible ~/OBSIA-public --appliquer  # écrit
    python3 scripts/publier.py --cible ~/OBSIA-public --appliquer --commit

La cible est un clone du dépôt public. Son `.git/` n'est jamais touché : le
script remplace le contenu suivi, montre le diff, et laisse committer — ou
committe lui-même avec `--commit`, sans jamais pousser.

Bibliothèque standard uniquement.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import modules as MOD
from generer_prompt import RACINE_DEFAUT

#: Ce qui décrit une personne ou une machine, et ne franchit jamais la
#: frontière du public. Les README de ces dossiers, eux, passent : ils
#: expliquent à quoi la zone sert.
PRIVE = ("mémoire", "IA/system/session-log", "brouillon", ".archive")

#: Ce qui ne devrait même pas être suivi par Git, mais qu'on écarte quand même :
#: une ceinture coûte moins cher qu'un secret dans un historique public.
JAMAIS = ("obsia.local.yml", "prompt-systeme.md", ".env", "mcp.json", ".mcp.json")

# ------------------------------------------------------------ contrôle de fuite

#: Ce qui bloque la publication. Chaque motif vise une **valeur**, jamais le
#: mot qui la nomme : le contrat parle de jetons et de mots de passe à longueur
#: de page, et il doit pouvoir continuer.
BLOQUANTS = (
    ("adresse de courriel",
     re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]{2,}\b")),
    ("adresse IP privée",
     re.compile(r"\b(?:10\.\d{1,3}|192\.168|172\.(?:1[6-9]|2\d|3[01]))"
                r"\.\d{1,3}\.\d{1,3}\b")),
    ("clé privée",
     re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("jeton d'API",
     re.compile(r"\b(?:ghp|gho|ghs|ghu|github_pat|sk-ant|sk-proj|sk-live|AKIA)"
                r"[-_A-Za-z0-9]{10,}")),
    # Pas de `\b` en tête : un préfixe colle presque toujours au nom réel
    # (`OPENAI_API_KEY=…`), et `_` étant un caractère de mot, la limite ne
    # tombait jamais là où il fallait.
    ("secret affecté",
     re.compile(r"(?i)(?:password|passwd|api[_-]?key|secret|token)\b\s*[=:]\s*"
                r"[\"']?[A-Za-z0-9_\-./+]{12,}")),
)

#: Adresses de courriel qui ne sont pas des fuites : elles désignent un projet,
#: pas une personne. Une liste explicite, parce qu'une exception implicite est
#: une exception qu'on oublie d'avoir prise.
COURRIELS_ADMIS = ("noreply@", "example.com", "exemple.fr", "utilisateur@")

BINAIRES = (".png", ".jpg", ".jpeg", ".gif", ".pdf", ".svg", ".zip", ".woff",
            ".woff2", ".ico")


def controler_fuites(racine: Path) -> list[tuple[str, int, str, str]]:
    """Relit tout l'arbre exporté. Rend la liste des trouvailles bloquantes."""
    trouvailles = []
    for chemin in sorted(racine.rglob("*")):
        if not chemin.is_file() or chemin.suffix.lower() in BINAIRES:
            continue
        rel = chemin.relative_to(racine)
        if rel.parts and rel.parts[0] == ".git":
            continue
        try:
            texte = chemin.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for numero, ligne in enumerate(texte.splitlines(), 1):
            for etiquette, motif in BLOQUANTS:
                trouve = motif.search(ligne)
                if not trouve:
                    continue
                extrait = trouve.group(0)
                if etiquette == "adresse de courriel" and \
                        any(a in extrait for a in COURRIELS_ADMIS):
                    continue
                trouvailles.append((str(rel), numero, etiquette, ligne.strip()[:110]))
    return trouvailles


# --------------------------------------------------------------------- export

def git(racine: Path, *args: str) -> str:
    res = subprocess.run(["git", *args], cwd=str(racine),
                         capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError((res.stderr or res.stdout).strip())
    return res.stdout


URL_CLONE = re.compile(r"(git clone https://github\.com/)[\w.-]+/[\w.-]+")


def reecrire_url_de_clone(vers: Path, depot: str) -> list[str]:
    """Fait pointer les commandes `git clone` de la doc vers le dépôt public.

    Le README du dépôt privé annonce l'adresse du dépôt privé : recopiée telle
    quelle, elle donnerait à un lecteur du public une commande qui échoue en
    404, sans lui dire pourquoi.
    """
    touches = []
    for chemin in sorted(vers.rglob("*.md")):
        if ".git" in chemin.parts:
            continue
        texte = chemin.read_text(encoding="utf-8")
        neuf = URL_CLONE.sub(r"\g<1>" + depot, texte)
        if neuf != texte:
            chemin.write_text(neuf, encoding="utf-8")
            touches.append(str(chemin.relative_to(vers)))
    return touches


def exporter(source: Path, vers: Path) -> None:
    """Copie l'arbre suivi par Git à HEAD, puis retire ce qui est privé.

    `git archive` plutôt qu'une copie du répertoire : ce qui n'est pas suivi
    n'a pas été relu, et ce qui n'a pas été relu ne se publie pas.
    """
    archive = vers.parent / "obsia-export.tar"
    with archive.open("wb") as sortie:
        res = subprocess.run(["git", "archive", "HEAD"], cwd=str(source),
                             stdout=sortie, stderr=subprocess.PIPE, text=False)
    if res.returncode != 0:
        raise RuntimeError(res.stderr.decode("utf-8", "replace").strip())

    vers.mkdir(parents=True, exist_ok=True)
    shutil.unpack_archive(str(archive), str(vers), format="tar")
    archive.unlink()

    for rel in PRIVE:
        dossier = vers / rel
        if not dossier.is_dir():
            continue
        for enfant in sorted(dossier.rglob("*")):
            if enfant.is_file() and enfant.name != "README.md":
                enfant.unlink()
        for enfant in sorted(dossier.rglob("*"), reverse=True):
            if enfant.is_dir() and not any(enfant.iterdir()):
                enfant.rmdir()

    for rel in JAMAIS:
        for trouve in vers.rglob(rel):
            trouve.unlink()

    MOD.ecrire_gabarits_dinstance(vers)


def regenerer_et_verifier(racine: Path) -> int:
    for script in ("regenerate_sommaire.py", "regenerate_index.py"):
        res = subprocess.run([sys.executable, str(racine / "scripts" / script)],
                             cwd=str(racine), capture_output=True, text=True)
        if res.returncode != 0:
            print((res.stderr or res.stdout).strip(), file=sys.stderr)
            return res.returncode
    res = subprocess.run([sys.executable, str(racine / "scripts" / "verifier_coffre.py")],
                         cwd=str(racine), capture_output=True, text=True)
    print("  " + (res.stdout or "").strip().replace("\n", "\n  "))
    if res.returncode != 0:
        print((res.stderr or "").strip(), file=sys.stderr)
    return res.returncode


def synchroniser(export: Path, cible: Path) -> None:
    """Remplace le contenu suivi de la cible. Son `.git/` n'est jamais touché."""
    for enfant in sorted(cible.iterdir()):
        if enfant.name == ".git":
            continue
        shutil.rmtree(enfant) if enfant.is_dir() else enfant.unlink()
    for enfant in sorted(export.iterdir()):
        destination = cible / enfant.name
        if enfant.is_dir():
            shutil.copytree(enfant, destination)
        else:
            shutil.copy2(enfant, destination)


# ----------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Produit le miroir public d'OBSIA depuis ce dépôt privé.")
    ap.add_argument("--racine", type=Path, default=RACINE_DEFAUT)
    ap.add_argument("--cible", type=Path, required=True,
                    help="clone local du dépôt public")
    ap.add_argument("--appliquer", action="store_true",
                    help="écrit dans la cible ; sans lui, aperçu seulement")
    ap.add_argument("--commit", action="store_true",
                    help="committe dans la cible après écriture. Ne pousse jamais.")
    ap.add_argument("--depot-public", metavar="OWNER/NOM",
                    help="réécrit les `git clone https://github.com/…` de la "
                         "documentation vers ce dépôt")
    ap.add_argument("--forcer", action="store_true",
                    help="publie malgré les trouvailles du contrôle de fuite")
    ap.add_argument("--autoriser-modifications", action="store_true",
                    help="publie depuis un arbre de travail sale (HEAD reste la source)")
    args = ap.parse_args()

    source = args.racine.resolve()
    cible = args.cible.expanduser().resolve()

    if not (cible / ".git").is_dir():
        print("La cible n'est pas un clone Git : %s" % cible, file=sys.stderr)
        print("Cloner d'abord le dépôt public à cet emplacement.", file=sys.stderr)
        return 1
    if cible == source:
        print("La cible ne peut pas être la source.", file=sys.stderr)
        return 1

    sale = git(source, "status", "--porcelain").strip()
    if sale and not args.autoriser_modifications:
        print("Arbre de travail modifié — `git archive HEAD` ne publierait pas "
              "ces changements :", file=sys.stderr)
        print(sale, file=sys.stderr)
        print("\nCommitter d'abord, ou passer --autoriser-modifications.",
              file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory(prefix="obsia-publier-") as tmp:
        export = Path(tmp) / "export"
        print("Export de HEAD (%s)…" % git(source, "rev-parse", "--short", "HEAD").strip())
        exporter(source, export)

        if args.depot_public:
            touches = reecrire_url_de_clone(export, args.depot_public)
            print("  URL de clone → %s  (%d fichier(s))"
                  % (args.depot_public, len(touches)))

        print("\nContrôle de fuite")
        print("─────────────────")
        trouvailles = controler_fuites(export)
        if trouvailles:
            for rel, numero, etiquette, ligne in trouvailles:
                print("  ✗ %s:%d  [%s]" % (rel, numero, etiquette))
                print("      %s" % ligne)
            print("\n  %d trouvaille(s). Rien n'est publié." % len(trouvailles))
            if not args.forcer:
                print("  Corriger la source, ou passer --forcer si c'est un "
                      "faux positif.", file=sys.stderr)
                return 1
            print("  --forcer : publication malgré tout.")
        else:
            print("  Aucune trouvaille.")

        print("\nCohérence du coffre exporté")
        print("───────────────────────────")
        code = regenerer_et_verifier(export)
        if code != 0:
            print("\nL'export est incohérent — rien n'est publié.", file=sys.stderr)
            return code

        fichiers = sorted(p.relative_to(export) for p in export.rglob("*") if p.is_file())
        print("\nAperçu")
        print("──────")
        print("  Source  : %s" % source)
        print("  Cible   : %s" % cible)
        print("  Fichiers publiés : %d" % len(fichiers))
        print("  Vidés de leur contenu : %s" % ", ".join(PRIVE))
        print("  Jamais publiés        : %s" % ", ".join(JAMAIS))

        if not args.appliquer:
            print("\nAperçu seulement. Relancer avec --appliquer pour écrire "
                  "dans la cible.")
            return 0

        synchroniser(export, cible)

    print("\nÉcrit dans %s" % cible)
    diff = git(cible, "status", "--porcelain").strip()
    print("  %d entrée(s) au statut Git" % len(diff.splitlines()) if diff
          else "  Aucun changement — le public était déjà à jour.")

    if args.commit and diff:
        git(cible, "add", "-A")
        git(cible, "commit", "-m",
            "Synchronisation depuis le dépôt privé (%s)"
            % git(source, "rev-parse", "--short", "HEAD").strip())
        print("  Committé. La poussée reste à faire à la main : git push")
    elif diff:
        print("  À relire puis committer : git -C %s diff --cached" % cible)

    return 0


if __name__ == "__main__":
    sys.exit(main())
