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
from typing import NamedTuple

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

#: Ce qui trahit un coffre vivant du côté de la cible. `synchroniser` efface
#: tout ce que la cible contient hors `.git/` : lui donner un coffre de travail,
#: c'est effacer le travail de quelqu'un.
MARQUES_DE_COFFRE = (".obsidian", "-SAVOIRS", "-PROJETS")

#: Dans `mémoire/`, les seuls fichiers qu'un export légitime contient : le
#: README du dossier, le profil en gabarit que l'installeur y pose, et le
#: sommaire que `regenerate_sommaire.py` réécrit avant la synchronisation. Tout
#: le reste est du travail — un clone du dépôt public n'en a jamais.
#: (Trois noms, trois sources : les élargir, c'est élargir ce qu'on accepte
#: d'effacer. Vérifié en publiant à blanc, puis en republiant sur le résultat.)
MEMOIRE_DE_DISTRIBUTION = ("README.md", "profil-utilisateur.md", "sommaire.md")

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
    # (`OPENAI_API_KEY=…`, `db_password`), et `_` étant un caractère de mot, la
    # limite ne tombait jamais là où il fallait. Un suffixe d'un seul morceau
    # (`password_hash`) est admis pour la même raison — un seul : au-delà,
    # `bearer_token_env_var` désigne le nom d'une variable d'environnement, pas
    # un secret.
    #
    # Le coffre s'écrit en français : `mdp`, `mot de passe`, `jeton`, `clé`
    # disent la même chose que `password` et `token`. Et la valeur, elle, ne se
    # limite pas à l'alphanumérique : un mot de passe a le droit d'avoir des
    # symboles, et des espaces quand il est entre guillemets.
    #
    # Le prix à payer, c'est la ligne de code : `cle = os.environ.get(clé)` lit
    # une variable, elle ne donne aucun secret. D'où les deux garde-fous de la
    # valeur nue — pas de ponctuation de code, et la valeur va jusqu'au bout du
    # mot. Sans quoi la moitié des scripts du coffre se signaleraient.
    ("secret affecté",
     re.compile(
         r"(?i)(?:[\w-]*[_-])?"
         r"(?:password|passwd|api[_-]?key|secret|token|jeton|mdp"
         r"|mot[ _-]de[ _-]passe|cl[ée])(?:[_-][A-Za-z0-9]+)?\b\s*[=:]\s*"
         r"(?:[\"'][^\"']{12,}[\"']|[^\s\"'()\[\]{},]{12,}(?=\s|$))"
         # Une phrase de passe sans guillemets, donc des espaces dans la valeur.
         # Rien, dans sa forme, ne la distingue d'une phrase de prose : c'est sa
         # position qui parle. Mot-clé fort en début de ligne — éventuellement
         # après une puce — et une affectation qui prend toute la ligne. Une
         # phrase comme « … pas un secret : une note du coffre parent la porte »
         # a le même mot-clé, mais au milieu de la ligne, et elle reste muette.
         r"|^[ \t]*(?:[-*+][ \t]+)?"
         r"(?:password|passwd|secret|mdp|mot[ _-]de[ _-]passe)\b\s*[=:]\s*"
         r"\S+(?:\s+\S+)+[ \t]*$")),
    # Une clé secrète AWS n'a pas de préfixe reconnaissable — c'est justement
    # pourquoi elle se recopie nue. Quarante caractères base64, à côté d'un
    # mot-clé qui dit ce qu'ils sont ; l'alternance `[^\n]{0,40}?` laisse la
    # valeur se placer librement sur la ligne. Majuscules obligatoires dans le
    # motif : quarante hexadécimaux minuscules, c'est une empreinte de commit,
    # et le coffre en cite.
    ("clé secrète AWS",
     re.compile(r"(?i)(?:aws|secret)[^\n]{0,40}?"
                r"\b(?=[A-Za-z0-9/+=]*[A-Z])[A-Za-z0-9/+=]{40}\b")),
    # Noms d'hôte internes. La fin ne doit pas être suivie d'un point et d'un
    # mot : sans cela, `obsia.local.yml`, `AGENTS.local.md` et
    # `CLAUDE.local.md` — trois noms de fichiers locaux, jamais des machines —
    # se signaleraient tout seuls.
    ("nom d'hôte interne",
     re.compile(r"\b[\w-]+(?:\.[\w-]+)*"
                r"\.(?:lan|local|internal|home\.arpa|ts\.net)\b(?!\.\w)")),
)

#: Boîtes génériques et domaines réservés : ils désignent un projet, pas une
#: personne. Le domaine se compare **en entier** — `exemple.fr.attaquant.net`
#: n'est pas `exemple.fr`, et rien n'empêche d'enregistrer le second.
BOITES_ADMISES = ("noreply", "utilisateur")
DOMAINES_ADMIS = ("example.com", "exemple.fr")

#: Les deux étiquettes qu'un `--forcer` ne publie pas. Une clé privée ne se
#: révoque pas — elle se remplace. Un jeton connu se révoque, mais seulement
#: avant d'avoir servi : publié, il est déjà trop tard. Les autres catégories
#: — une adresse, un nom d'hôte, un mot de passe à changer — se rattrapent.
SANS_FORCAGE = ("clé privée", "jeton d'API")

#: Ce qui n'est pas relu, par extension : un fichier binaire. `.svg` n'y est
#: plus — c'est du texte, et le sauter laissait passer ce qu'il contient.
BINAIRES = (".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".woff",
            ".woff2", ".ico")


def courriel_admis(adresse: str) -> bool:
    """Vrai pour une adresse de projet : boîte générique, ou domaine réservé."""
    boite, _, domaine = adresse.partition("@")
    if boite.lower() in BOITES_ADMISES:
        return True
    return domaine.lower() in DOMAINES_ADMIS


class Controle(NamedTuple):
    """Ce que le contrôle a vu — et ce qu'il n'a pas pu relire.

    Les deux vont ensemble : « aucune trouvaille » sur cent fichiers dont
    quatre-vingts illisibles ne veut rien dire. Un fichier non relu n'est pas
    un fichier propre, c'est un fichier dont on ne sait rien.
    """

    #: (chemin, ligne, étiquette, extrait) par trouvaille.
    trouvailles: list
    #: (chemin, raison) par fichier sauté : binaire, non UTF-8, illisible.
    non_relus: list
    #: Nombre de fichiers effectivement relus.
    relus: int


def controler_fuites(racine: Path) -> Controle:
    """Relit tout l'arbre exporté, et dit aussi ce qu'il n'a pas pu relire."""
    trouvailles, non_relus, relus = [], [], 0
    for chemin in sorted(racine.rglob("*")):
        if not chemin.is_file() or chemin.is_symlink():
            continue
        rel = chemin.relative_to(racine)
        if rel.parts and rel.parts[0] == ".git":
            continue
        if chemin.suffix.lower() in BINAIRES:
            non_relus.append((str(rel), "extension binaire"))
            continue
        try:
            texte = chemin.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            non_relus.append((str(rel), "non UTF-8"))
            continue
        except OSError:
            non_relus.append((str(rel), "illisible"))
            continue
        relus += 1
        for numero, ligne in enumerate(texte.splitlines(), 1):
            for etiquette, motif in BLOQUANTS:
                trouve = motif.search(ligne)
                if not trouve:
                    continue
                extrait = trouve.group(0)
                if etiquette == "adresse de courriel" and courriel_admis(extrait):
                    continue
                trouvailles.append((str(rel), numero, etiquette, ligne.strip()[:110]))
    return Controle(trouvailles, non_relus, relus)


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
        if enfant.is_symlink():
            # Un lien se défait lui-même : le rmtree d'un dossier lié s'arrête
            # sur le lien et laisse la cible à moitié vidée.
            enfant.unlink()
        elif enfant.is_dir():
            shutil.rmtree(enfant)
        else:
            enfant.unlink()
    for enfant in sorted(export.iterdir()):
        destination = cible / enfant.name
        if enfant.is_dir():
            shutil.copytree(enfant, destination)
        else:
            shutil.copy2(enfant, destination)


# ------------------------------------------------------------------ la cible

def travail_dans_memoire(memoire: Path) -> bool:
    """Vrai si `mémoire/` porte autre chose que le gabarit de distribution."""
    for enfant in memoire.rglob("*"):
        if enfant.is_dir() or enfant.name not in MEMOIRE_DE_DISTRIBUTION:
            return True
    return False


#: Ce qu'un miroir d'OBSIA porte et que rien d'autre ne porte. Les marques de
#: coffre disent ce qu'il ne faut pas écraser ; celle-ci dit ce qu'on a le droit
#: d'écraser, et c'est la seule reconnaissance possible d'une publication.
MARQUE_DE_MIROIR = Path("IA") / "system" / "VAULT-CONTRACT.md"


def cible_vierge(cible: Path) -> bool:
    """Vrai si la cible n'a rien à perdre : un dépôt, et rien que son `.git/`.

    Pas « un dossier vide » : sans `.git/`, ce n'est pas un dépôt vierge mais
    un dossier inconnu, que `synchroniser` remplirait sans jamais savoir ce
    qu'il a effacé.
    """
    if not (cible / ".git").exists():
        return False
    return all(enfant.name == ".git" for enfant in cible.iterdir())


#: Les trois écritures d'une même origine distante — `git@hôte:p/dépôt`,
#: `ssh://git@hôte/p/dépôt`, `https://hôte/p/dépôt` — ramenées à leurs morceaux.
MOTIF_ORIGINE = re.compile(
    r"^(?:[a-z+]+://)?(?:(?P<utilisateur>[^@/]+)@)?"
    r"(?P<hote>[^:/]+)[:/](?P<chemin>[^/].*?)/?$", re.IGNORECASE)


def url_origine(depot: Path) -> str:
    """L'identité d'`origin`, ramenée à `hôte/chemin` — ou "" s'il n'y en a pas.

    Deux `origin` qui désignent le même dépôt doivent se comparer égaux : sans
    cela, le refus de publier sur un clone du privé se contourne en clonant en
    ssh ce qu'on a écrit en https. On jette donc ce qui ne désigne pas le
    dépôt — protocole, utilisateur, `.git` final, barre finale — et la casse.
    """
    try:
        url = git(depot, "remote", "get-url", "origin").strip()
    except RuntimeError:
        return ""
    encontre = MOTIF_ORIGINE.match(url)
    if encontre is None:
        # Un chemin local, par exemple : on ne sait pas le ramener à un dépôt.
        return url.rstrip("/").lower()
    chemin = re.sub(r"\.git$", "", encontre.group("chemin"))
    return ("%s/%s" % (encontre.group("hote"), chemin)).lower()


def raison_de_refus(source: Path, cible: Path) -> str | None:
    """Pourquoi refuser de synchroniser cette cible — ou None si c'est sûr.

    `synchroniser` efface le contenu suivi de la cible avant d'y verser
    l'export. Se tromper de cible, c'est effacer un coffre de travail ou un
    clone du dépôt privé, sans retour possible. On refuse donc avant d'exporter.
    """
    if cible == source:
        return "la cible est la source"
    if cible in source.parents:
        return "la cible contient la source"
    if source in cible.parents:
        return "la source contient la cible"
    for marque in MARQUES_DE_COFFRE:
        if (cible / marque).exists():
            return "la cible porte la marque d'un coffre : %s" % marque
    memoire = cible / "mémoire"
    if memoire.is_dir() and travail_dans_memoire(memoire):
        return "la cible a une mémoire remplie : %s" % memoire
    origine = url_origine(cible)
    if origine and origine == url_origine(source):
        return "la cible a la même origine que la source : %s" % origine
    if not (cible / MARQUE_DE_MIROIR).is_file() and not cible_vierge(cible):
        return ("la cible n'est ni un miroir d'OBSIA — %s — ni un dépôt vierge, "
                "c'est-à-dire un dépôt qui n'a rien que son `.git/` : y publier "
                "effacerait autre chose que notre publication"
                % MARQUE_DE_MIROIR)
    return None


def chemins_a_supprimer(cible: Path) -> list[str]:
    """Les entrées de la cible que `synchroniser` effacerait, `.git/` excepté."""
    supprimes = []
    for enfant in sorted(cible.iterdir()):
        if enfant.name == ".git":
            continue
        if enfant.is_symlink():
            supprimes.append("%s (lien symbolique)" % enfant.name)
        elif enfant.is_dir():
            supprimes.append("%s/" % enfant.name)
        else:
            supprimes.append(enfant.name)
    return supprimes


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
                    help="publie malgré les trouvailles du contrôle de fuite — "
                         "sauf une clé privée ou un jeton connu, qui ne se "
                         "forcent pas")
    ap.add_argument("--autoriser-modifications", action="store_true",
                    help="publie depuis un arbre de travail sale (HEAD reste la source)")
    args = ap.parse_args()

    source = args.racine.resolve()
    cible = args.cible.expanduser().resolve()

    if not (cible / ".git").is_dir():
        print("La cible n'est pas un clone Git : %s" % cible, file=sys.stderr)
        print("Cloner d'abord le dépôt public à cet emplacement.", file=sys.stderr)
        return 1
    refus = raison_de_refus(source, cible)
    if refus is not None:
        print("Publication refusée : %s." % refus, file=sys.stderr)
        print("  Source : %s" % source, file=sys.stderr)
        print("  Cible  : %s" % cible, file=sys.stderr)
        print("  `synchroniser` efface tout le contenu suivi de la cible : "
              "donner un clone du dépôt public.", file=sys.stderr)
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
        forcees: list[str] = []
        print("Export de HEAD (%s)…" % git(source, "rev-parse", "--short", "HEAD").strip())
        exporter(source, export)

        if args.depot_public:
            touches = reecrire_url_de_clone(export, args.depot_public)
            print("  URL de clone → %s  (%d fichier(s))"
                  % (args.depot_public, len(touches)))

        print("\nCohérence du coffre exporté")
        print("───────────────────────────")
        code = regenerer_et_verifier(export)
        if code != 0:
            print("\nL'export est incohérent — rien n'est publié.", file=sys.stderr)
            return code

        # Après la régénération, et pas avant : elle réécrit les index et les
        # sommaires, et c'est cet export-là qui partira. Contrôler avant
        # reviendrait à relire un état qui n'existe plus.
        print("\nContrôle de fuite")
        print("─────────────────")
        controle = controler_fuites(export)
        if controle.trouvailles:
            for rel, numero, etiquette, ligne in controle.trouvailles:
                print("  ✗ %s:%d  [%s]" % (rel, numero, etiquette))
                print("      %s" % ligne)
            print("\n  %d trouvaille(s) sur %d fichier(s) relu(s)."
                  % (len(controle.trouvailles), controle.relus))
            posees = [trouvaille[2] for trouvaille in controle.trouvailles]
            signalees = sorted(set(posees))
            interdites = sorted(set(posees) & set(SANS_FORCAGE))
            if interdites:
                print("  --forcer ne s'applique pas ici : %s."
                      % ", ".join(interdites), file=sys.stderr)
                print("  Une clé privée se remplace, un jeton connu se révoque — "
                      "avant de publier, pas après.", file=sys.stderr)
                return 1
            if not args.forcer:
                print("  Corriger la source, ou passer --forcer si c'est un "
                      "faux positif.", file=sys.stderr)
                return 1
            forcees = signalees
            print("  --forcer : publication malgré tout — %s."
                  % ", ".join(forcees))
        else:
            print("  Aucune trouvaille sur %d fichier(s) relu(s) — %d non relu(s)."
                  % (controle.relus, len(controle.non_relus)))
        for rel, raison in controle.non_relus:
            print("      - %s (%s)" % (rel, raison))

        fichiers = sorted(p.relative_to(export) for p in export.rglob("*") if p.is_file())
        print("\nAperçu")
        print("──────")
        print("  Source  : %s" % source)
        print("  Cible   : %s" % cible)
        print("  Fichiers publiés : %d" % len(fichiers))
        print("  Vidés de leur contenu : %s" % ", ".join(PRIVE))
        print("  Jamais publiés        : %s" % ", ".join(JAMAIS))

        supprimes = chemins_a_supprimer(cible)
        print("  Entrées effacées dans la cible : %d" % len(supprimes))
        for chemin in supprimes:
            print("      - %s" % chemin)

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
        # La dérogation se relit là où elle compte : une publication forcée qui
        # ne le dit nulle part est indiscernable d'une publication propre, et
        # c'est ainsi qu'une fuite passe pour un oubli de contrôle.
        message = ("Synchronisation depuis le dépôt privé (%s)"
                   % git(source, "rev-parse", "--short", "HEAD").strip())
        if forcees:
            message += ("\n\nPublié malgré le contrôle de fuite (--forcer) :\n"
                        + "\n".join("- %s" % etiquette for etiquette in forcees))
        git(cible, "add", "-A")
        git(cible, "commit", "-m", message)
        print("  Committé. La poussée reste à faire à la main — par une branche :")
        print("  la règle de main exige la vérification CI avant qu'un commit y arrive,")
        print("  une poussée directe est refusée.")
        print("    git -C %s push origin HEAD:refs/heads/publication/AAAA-MM-JJ" % cible)
        print("    puis pull request, vérification verte, fusion.")
    elif diff:
        print("  À relire puis committer : git -C %s diff --cached" % cible)

    return 0


if __name__ == "__main__":
    sys.exit(main())
