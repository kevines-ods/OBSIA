#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Le garde anti-secret du pre-commit du dépôt de données (§7.1).

Le 2026-10-04, un mot de passe est entré en clair dans la mémoire du coffre
(`_MAINTENANCE/opencode.md`), puis a été recopié par un index régénéré. Rien ne
l'a arrêté. La liste blanche du §7.1 interdit toute règle par *nom de fichier*,
et le motif « secret affecté » de `publier.py` ne voit qu'une valeur **nommée** :
un mot de passe collé seul, sans le mot « mot de passe », passe au travers.

Ce garde refuse donc, dans ce que le commit **ajoute** au dépôt de données :

  * les valeurs qui répondent aux motifs de **secret** de `publier.BLOQUANTS`,
    importés de là — jamais recopiés (`motifs_secrets`) ;
  * un fichier dont **tout le contenu** est un unique jeton sans espace à forte
    entropie — le cas exact qui a échoué (`jeton_isole`).

Trois règles évitent de refuser la mémoire ordinaire :

  * pour « secret affecté », la valeur doit **avoir forme de secret** : un
    gabarit en tête (`yourpassword`, `change-root-password`, `mot-de-passe`), un
    chemin en tête (`/`, `~/`, `./`, `../`) et une prose **non guillemetée** ne
    sont pas des secrets ; une phrase **entre guillemets** en est un, sauf si
    c'est une ligne de commande — il faut alors **à la fois** une espace et un
    marqueur shell (`;`, `|`, accent grave, `$(`), car la ponctuation ordinaire
    (`&`, `$` seul, parenthèses) vit dans la prose
    (`valeur_a_forme_de_secret`) ;
  * cette règle de forme ne vaut que pour « secret affecté » : les autres motifs
    de `publier` portent déjà la forme de leur secret ;
  * une **empreinte** citée n'est pas un secret : hexadécimal d'une longueur de
    condensat connue (7-12, 40, 64), ou hexadécimal quelconque à côté d'un mot
    qui dit « sha » ou « commit » (`est_empreinte`).

Il ne reprend pas les autres motifs du contrôle de fuite — courriel, adresse IP
privée, nom d'hôte interne : ceux-là gardent la frontière *vers le public*, alors
que la mémoire privée du coffre les porte légitimement. Confondre les deux ferait
refuser la mémoire au nom de la publication.

Tout se lit en octets : un fichier qui n'est pas de l'UTF-8 — binaire ou Latin-1
— ne doit pas faire tomber le crochet.

Bibliothèque standard uniquement.
"""

from __future__ import annotations

import argparse
import math
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import publier as PUB  # noqa: E402

#: Les étiquettes de `publier.BLOQUANTS` qui visent une **valeur de secret**.
#: Les autres motifs du contrôle de fuite décrivent la frontière publique et ne
#: se refusent pas dans la mémoire privée (`adresse de courriel`, `adresse IP
#: privée`, `nom d'hôte interne`).
MOTIFS_SECRETS = ("clé privée", "jeton d'API", "secret affecté", "clé secrète AWS")

#: Bornes du jeton isolé. Le vrai cas faisait 32 caractères ; le plancher de 20
#: écarte un mot, une date ou un identifiant court.
LONGUEUR_MIN = 20
LONGUEUR_MAX = 200
#: En deçà, un unique mot (une seule famille de caractères) n'est pas un secret.
CLASSES_MIN = 2
#: Shannon, bits par caractère. Un mot français tourne autour de 3 ; un secret
#: tiré au hasard au-dessus de 4.
ENTROPIE_MIN = 3.5

#: Ce qui suit une affectation. Le mot-clé de `publier` ne porte ni `=` ni `:`,
#: donc le premier séparateur d'une correspondance est celui de l'affectation.
_SEPARATEUR = re.compile(r"[=:]\s*")

#: La valeur **entière** est un gabarit : elle nomme ce qu'il faudrait mettre.
_GABARIT_ENTIER = re.compile(
    r"(?i)\A(?:password|passwd|passphrase|pwd|mdp|secret|token|jeton|cl[ée]"
    r"|mot[ _-]?de[ _-]?passe|motdepasse|changeme|change[ _-]?me|changez[ _-]?moi"
    r"|placeholder|example|exemple|todo|fixme|dummy|sample|mod[eè]le|value|valeur"
    r"|x+|\.\.\.)\Z")
#: La valeur **commence** par un marqueur de gabarit. Le jugement porte sur la
#: tête, jamais sur la valeur entière : `Tr0ub4dor&3Change` est un mot de passe
#: qui *contient* « change », pas un gabarit.
_GABARIT_PREFIXE = re.compile(
    r"(?i)\A(?:"
    r"(?:your|my|mon|ma|ton|ta|votre|notre)[ _-]?"
    r"(?:password|passwd|passphrase|mdp|secret|token|jeton|cl[ée]"
    r"|mot[ _-]?de[ _-]?passe)"
    r"|change|changer|changez|to[ _-]?change|[àa][ _-]?changer"
    r"|placeholder|example|exemple|todo|fixme|dummy|sample"
    r"|mot[ _-]?de[ _-]?passe|motdepasse"
    r")")
#: Ce qui trahit une ligne de commande recopiée : un séparateur de commande
#: (`;`, `|`), un accent grave ou une substitution `$(`. La ponctuation seule —
#: `&`, `$`, parenthèses, accolades, chevrons — ne suffit pas : elle vit dans la
#: prose, et l'exempter laissait passer `Tr0ub4dor&3Change`.
_MARQUEUR_SHELL = re.compile(r"[;|`]|\$\(")

#: Un hexadécimal, une empreinte candidate.
_HEX = re.compile(r"\A[0-9a-fA-F]{7,64}\Z")
#: Les longueurs d'un condensat réel : git abrégé (7 à 12), sha1 (40), sha256
#: (64). Un hexadécimal hors de ces longueurs est un secret possible — les
#: seize octets de `openssl rand -hex 16` font trente-deux caractères.
_LONGUEURS_EMPREINTE = frozenset({7, 8, 9, 10, 11, 12, 40, 64})
#: Un mot qui dit qu'un hexadécimal est une empreinte, pas un secret.
_MOTS_EMPREINTE = re.compile(r"(?i)\b(?:sha(?:-?\d+)?|commit|empreinte|fingerprint)\b")
#: Un identifiant d'objet : un UUID n'est pas un secret.
_UUID = re.compile(
    r"\A[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\Z")
#: Une note qui n'est qu'une adresse n'est pas un secret. Le domaine doit porter
#: un point : `utilisateur@localhost` n'est pas une adresse.
_ADRESSE = re.compile(r"\A[^@\s]+@[^@\s]+\.[^@\s]+\Z")


def motifs_secrets() -> tuple:
    """Les motifs de secret, pris à la source unique qu'est `publier.BLOQUANTS`.

    Une étiquette disparue de `BLOQUANTS` fait échouer ici plutôt que de laisser
    un garde muet : un contrôle qui ne contrôle rien vaut moins que pas de
    contrôle, puisqu'il rassure à tort.
    """
    par_etiquette = {etiquette: motif for etiquette, motif in PUB.BLOQUANTS}
    manquantes = [e for e in MOTIFS_SECRETS if e not in par_etiquette]
    if manquantes:
        raise RuntimeError(
            "publier.BLOQUANTS ne porte plus : %s" % ", ".join(manquantes))
    return tuple((etiquette, par_etiquette[etiquette]) for etiquette in MOTIFS_SECRETS)


# -------------------------------------------------------- forme d'une valeur

def est_empreinte(texte: str, contexte: str = "") -> bool:
    """Le texte est-il une empreinte, donc pas un secret ?

    Un hexadécimal à une longueur de condensat (7-12, 40, 64), un hexadécimal
    quelconque à côté d'un mot qui dit « sha » ou « commit », ou un UUID.
    """
    if _UUID.match(texte):
        return True
    if not _HEX.match(texte):
        return False
    if len(texte) in _LONGUEURS_EMPREINTE:
        return True
    return bool(_MOTS_EMPREINTE.search(contexte))


def valeur_a_forme_de_secret(valeur: str, contexte: str = "",
                             guillemetee: bool = False) -> bool:
    """La valeur d'un « secret affecté » a-t-elle vraiment forme de secret ?

    Trois formes que le coffre porte légitimement ne sont **pas** des secrets :

      * un gabarit, jugé **en tête** — `mot-de-passe`, `yourpassword`,
        `change-root-password` : une valeur qui *contient* « change » ou
        « exemple » plus loin reste un secret (`Tr0ub4dor&3Change`) ;
      * un chemin, jugé **en tête** — `/`, `~/`, `./`, `../` : un `/` au milieu
        ne fait pas un chemin (`8f3/Qz2!Lm91Rt4W8y`) ;
      * une prose **non guillemetée** : c'est la règle du motif importé, dont le
        commentaire ancre la phrase non citée au début de la ligne.

    Une phrase **entre guillemets** est, elle, un secret : c'est ce que dit le
    même commentaire. Seule exception, la plus étroite possible : une valeur
    guillemetée n'est une ligne de commande recopiée que si elle porte **à la
    fois** une espace et un marqueur shell (`;`, `|`, accent grave, `$(`) — le
    coffre en écrit, et la refuser serait refuser sa mémoire, mais la ponctuation
    ordinaire (`&`, `$` seul, parenthèses) ne suffit pas à l'exempter.
    """
    nu = valeur.strip().strip("\"'").strip()
    if not nu:
        return False
    if (guillemetee and _MARQUEUR_SHELL.search(nu)
            and any(c.isspace() for c in nu)):
        return False
    # La décoration Markdown colle au chemin (`**`/root/x.pw`**`) : on la retire
    # avant de juger la tête, jamais avant de juger le reste.
    tete = nu.lstrip("*_` ")
    if tete.startswith(("/", "~/", "./", "../")):
        return False
    if _GABARIT_PREFIXE.match(nu) or _GABARIT_ENTIER.match(nu):
        return False
    if est_empreinte(nu, contexte):
        return False
    if any(c.isspace() for c in nu):
        return guillemetee
    return True


def _valeur_affectee(correspondance: str) -> str:
    """La valeur qui suit l'affectation d'une correspondance de « secret affecté ».

    Rendue **sans être détourée** : l'appelant a besoin de voir les guillemets et
    les espaces pour décider si la valeur est citée (`verifier`).
    """
    separateur = _SEPARATEUR.search(correspondance)
    if not separateur:
        return ""
    return correspondance[separateur.end():]


# ---------------------------------------------------------------- jeton isolé

def entropie(texte: str) -> float:
    """Entropie de Shannon du texte, en bits par caractère."""
    if not texte:
        return 0.0
    total = len(texte)
    return -sum((n / total) * math.log2(n / total)
                for n in Counter(texte).values())


def classes(texte: str) -> int:
    """Familles de caractères présentes : minuscule, majuscule, chiffre, autre."""
    return sum((
        any(c.islower() for c in texte),
        any(c.isupper() for c in texte),
        any(c.isdigit() for c in texte),
        any(not c.isalnum() for c in texte),
    ))


def jeton_isole(contenu: str, contexte: str = ""):
    """Rend le jeton si tout `contenu` en est un seul, sans espace et à forte
    entropie ; `None` sinon.

    C'est le cas d'école : `opencode.md` ne portait qu'une chaîne de 32
    caractères, sans le mot « mot de passe ». Aucun motif nommé ne la voyait.
    Les empreintes (condensat, identifiant de commit), les adresses et les URL
    sont écartées : un fichier qui n'est que cela n'est pas un secret.
    """
    nu = contenu.strip()
    if not (LONGUEUR_MIN <= len(nu) <= LONGUEUR_MAX):
        return None
    if any(c.isspace() for c in nu):
        return None
    if est_empreinte(nu, contexte) or _ADRESSE.match(nu) or "://" in nu:
        return None
    if classes(nu) < CLASSES_MIN:
        return None
    if entropie(nu) < ENTROPIE_MIN:
        return None
    return nu


# ---------------------------------------------------------------- lecture git

def _git(coffre: Path, *arguments: str) -> subprocess.CompletedProcess:
    """Lance git dans le coffre, en **octets**. Ne lève jamais.

    On ne décode pas ici : un fichier peut n'être ni de l'UTF-8 ni du texte, et
    le crochet ne doit pas tomber pour un binaire. Le décodage est remis à
    l'appelant, qui sait ce qu'il attend.
    """
    try:
        return subprocess.run(
            ["git", "-C", str(coffre), *arguments],
            capture_output=True, timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return subprocess.CompletedProcess([], 1, b"", b"")


def lignes_ajoutees(coffre: Path) -> list:
    """Les lignes que ce commit **ajoute**, numérotées dans leur fichier.

    On lit l'index (`--cached`) : c'est ce que le commit emporte, pas l'arbre de
    travail. `--unified=0` supprime le contexte — seules les lignes ajoutées
    paraissent. Le diff se décode avec `replace` : une ligne mal encodée ne doit
    pas lever, et l'ASCII d'un secret reste lisible.
    """
    resultat = _git(coffre, "-c", "core.quotePath=false", "diff", "--cached",
                    "--unified=0", "--no-color", "--diff-filter=ACMR")
    if resultat.returncode != 0:
        return []
    texte = resultat.stdout.decode("utf-8", "replace")
    ajoutees = []
    chemin, numero, dans_hunk = None, 0, False
    for ligne in texte.splitlines():
        if ligne.startswith("diff --git "):
            chemin, dans_hunk = None, False
        elif ligne.startswith("+++ ") and not dans_hunk:
            chemin = ligne[4:]
            chemin = chemin[2:] if chemin.startswith("b/") else chemin
        elif ligne.startswith("@@"):
            dans_hunk = True
            trouve = re.search(r"\+(\d+)", ligne)
            numero = int(trouve.group(1)) if trouve else 1
        elif dans_hunk and ligne.startswith("+"):
            ajoutees.append((chemin, numero, ligne[1:]))
            numero += 1
        elif dans_hunk and ligne.startswith(" "):
            numero += 1
    return [t for t in ajoutees if t[0] is not None]


def contenu_indexe(coffre: Path, chemin: str):
    """Le contenu **indexé** du fichier, ou `None` s'il est binaire ou absent.

    Le binaire se reconnaît à son octet nul **avant** tout décodage ; le reste
    se décode avec `replace`, pour ne pas lever sur un encodage inattendu.
    """
    resultat = _git(coffre, "show", ":%s" % chemin)
    if resultat.returncode != 0:
        return None
    brut = resultat.stdout
    if b"\x00" in brut:
        return None
    return brut.decode("utf-8", "replace")


def fichiers_indexes(coffre: Path) -> list:
    """Les fichiers que ce commit ajoute, copie, modifie ou renomme."""
    resultat = _git(coffre, "-c", "core.quotePath=false", "diff", "--cached",
                    "--name-only", "--diff-filter=ACMR", "-z")
    if resultat.returncode != 0:
        return []
    return [nom.decode("utf-8", "replace")
            for nom in resultat.stdout.split(b"\0") if nom]


def _est_depot(coffre: Path) -> bool:
    return _git(coffre, "rev-parse", "--git-dir").returncode == 0


# ------------------------------------------------------------------- verdict

def _apercu(valeur: str) -> str:
    """Un aperçu qui ne recopie pas le secret dans le journal du terminal."""
    if len(valeur) < 8:
        return "moins de huit caractères"
    return "%s… (%d caractères)" % (valeur[:4], len(valeur))


def verifier(coffre) -> int:
    """Rend 0 si ce que le commit ajoute est propre, 1 sinon — et dit quoi.

    Chaque refus nomme le fichier, la ligne et le motif ; la valeur n'est montrée
    que tronquée, pour ne pas la réintroduire là où on la lit.
    """
    coffre = Path(coffre)
    if not _est_depot(coffre):
        return 0
    motifs = motifs_secrets()  # la source doit porter ses étiquettes, toujours

    problemes = []
    for chemin, numero, texte in lignes_ajoutees(coffre):
        for etiquette, motif in motifs:
            trouve = motif.search(texte)
            if not trouve:
                continue
            if etiquette == "secret affecté":
                brut = _valeur_affectee(trouve.group(0))
                guillemetee = brut.lstrip()[:1] in ("\"", "'")
                if not valeur_a_forme_de_secret(
                        brut, contexte=texte, guillemetee=guillemetee):
                    continue
            problemes.append((chemin, numero, etiquette, trouve.group(0)))
    for chemin in fichiers_indexes(coffre):
        contenu = contenu_indexe(coffre, chemin)
        if contenu is None:
            continue
        jeton = jeton_isole(contenu, contexte=chemin)
        if jeton is not None:
            problemes.append((chemin, None, "valeur isolée à forte entropie", jeton))

    if not problemes:
        return 0
    print("Refusé : ce commit ajoute une valeur à forme de secret à la mémoire "
          "du coffre.", file=sys.stderr)
    for chemin, numero, etiquette, extrait in problemes:
        lieu = "%s:%d" % (chemin, numero) if numero else chemin
        print("  %s — %s : « %s »" % (lieu, etiquette, _apercu(extrait)),
              file=sys.stderr)
    print("Une valeur à forme de secret ne se commite pas (§7.1). Reformulez la "
          "note, ou retirez la valeur de l'index.", file=sys.stderr)
    return 1


def main(argv=None) -> int:
    analyseur = argparse.ArgumentParser(
        description="Refuse les valeurs à forme de secret ajoutées au dépôt de données.")
    analyseur.add_argument("--coffre", default=".", help="racine du coffre parent")
    arguments = analyseur.parse_args(argv)
    return verifier(Path(arguments.coffre).resolve())


if __name__ == "__main__":
    sys.exit(main())
