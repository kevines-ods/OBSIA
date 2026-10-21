#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Le garde anti-secret du pre-commit du dépôt de données (§7.1).

Le 2026-10-04, une note de `_MAINTENANCE/` a porté un mot de passe en clair,
puis un index régénéré l'a recopié. Rien ne l'a arrêté. La liste blanche du §7.1
interdit toute règle par *nom de fichier*, et le motif « secret affecté » de
`publier.py` ne voit qu'une valeur **nommée** : un mot de passe collé seul, sans
le mot « mot de passe », passe au travers.

Ce garde refuse donc, dans ce que le commit **ajoute** au dépôt de données :

  * les valeurs qui répondent aux motifs de **secret** de `publier.BLOQUANTS`,
    importés de là — jamais recopiés (`motifs_secrets`) ;
  * un fichier dont **tout le contenu** est un unique jeton sans espace à forte
    entropie — le cas exact qui a échoué (`jeton_isole`) ;
  * un **bloc** de base64 recopié — le corps d'une clé **sans son en-tête**, au
    moins trois lignes consécutives qui ne sont que du base64 (`bloc_base64`);
    `jeton_isole` refuse tout espace, donc cette forme lui échappait. Deux formes
    publiques en sont exemptées : les **empreintes** (un hexadécimal de 40 ou 64
    est dans l'alphabet du base64 sans en être, cf. `empreinte_de_bloc`) et un
    bloc **encadré** par `-----BEGIN PGP PUBLIC KEY BLOCK-----` ou `-----BEGIN
    CERTIFICATE-----`, la paire complète requise et **aucun délimiteur à
    l'intérieur**. L'exemption n'est pas un mur : un corps **nu** entre deux faux
    délimiteurs publics reste indistinguable d'une vraie clé publique — limite
    assumée, consignée par un test.

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

Rien ne relit la mémoire **déjà écrite**. Aucun contrôle ne parcourt le coffre à
la recherche de secrets : les deux portes voient un contenu au moment où il
arrive — celle du commit, la différence entre `HEAD` et l'index ; celle de
l'entrée, le texte candidat. Un secret **nommé**, sur une ligne qu'un commit ne
touche pas, reste donc en place sans être revu : le retirer est un acte humain,
sur la note et dans l'historique. C'est une décision, pas un oubli. Elle a une
limite, voulue : un **bloc de base64** ou un **jeton isolé** n'ont de sens que
dans le fichier entier, donc ils sont relus dans le contenu complet de chaque
fichier indexé — un bloc déjà écrit est refusé au commit suivant.
`tests/test_secrets_a_deux_portes.py` fixe les deux versants de ce choix.

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

#: Une ligne d'un bloc de base64 recopié. La ligne doit n'être **que** du base64 ;
#: le vrai cas — le corps d'une clé privée — fait des lignes de 64 caractères, et
#: 40 écarte un identifiant court.
LIGNE_BASE64_MIN = 40
#: En deçà de trois lignes consécutives, c'est une citation, pas un bloc recopié.
LIGNES_BLOC_MIN = 3
#: Une ligne qui n'est que du base64 : l'alphabet standard, un remplissage `=`
#: facultatif, au moins `LIGNE_BASE64_MIN` caractères, et rien d'autre. Une ligne
#: qui mêle une phrase et du base64 ne compte pas — « sans autre prose ».
_LIGNE_BASE64 = re.compile(r"\A[A-Za-z0-9+/]{%d,}={0,2}\Z" % LIGNE_BASE64_MIN)

#: Les armures qui rendent un bloc de base64 **public** : une clé PGP publique et
#: un certificat. Elles **seules** exemptent le bloc qu'elles encadrent. La paire
#: complète est requise — un `BEGIN` orphelin n'exempte rien — et **aucun
#: délimiteur ne doit vivre à l'intérieur** : c'est ce qui démasque une armure
#: privée glissée dans un cadre public (détournement prouvé à la relecture de
#: `2c8d91d`). Reste hors de portée, et assumé : un corps **nu** entre deux faux
#: délimiteurs publics, qu'aucune inspection ne distingue d'une vraie clé publique.
_CADRES_PUBLICS = (
    ("-----BEGIN PGP PUBLIC KEY BLOCK-----", "-----END PGP PUBLIC KEY BLOCK-----"),
    ("-----BEGIN CERTIFICATE-----", "-----END CERTIFICATE-----"),
)

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
#: Les longueurs qui, **dans un bloc de base64**, valent une empreinte : le
#: condensat entier seul — SHA-1 (40), SHA-256 (64). Un condensat abrégé (7 à 12)
#: sert à citer un commit dans une phrase ; il n'atteint pas `LIGNE_BASE64_MIN` et
#: n'a donc rien à exempter dans un bloc de trois lignes.
LONGUEURS_EMPREINTE_DE_BLOC = (40, 64)
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


def empreinte_de_bloc(ligne: str) -> bool:
    """La ligne est-elle une empreinte **entière**, donc pas une ligne de clé ?

    Plus étroit qu'`est_empreinte`, exprès : dans un bloc de base64, seules les
    longueurs de condensat complet exemptent — SHA-1 (**40**) et SHA-256 (**64**),
    cf. `LONGUEURS_EMPREINTE_DE_BLOC`. Un condensat abrégé (7 à 12) ne peut pas
    former une ligne de `LIGNE_BASE64_MIN` caractères ; s'il en atteignait la
    longueur, il n'en serait pas moins une empreinte abrégée, qui n'a rien à faire
    au milieu d'un bloc de trois lignes.

    Pas de contexte ici : la ligne se juge seule, sans le mot « sha » ou
    « commit » qui l'entoure dans une phrase.
    """
    return _HEX.match(ligne) is not None and len(ligne) in LONGUEURS_EMPREINTE_DE_BLOC


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

    C'est le cas d'école : la note de `_MAINTENANCE/` du 2026-10-04 ne portait
    qu'une chaîne de 32 caractères, sans le mot « mot de passe ». Aucun motif
    nommé ne la voyait.
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


def _lignes_sous_cadre_public(lignes: list) -> set:
    """Les indices des lignes **à l'intérieur** d'un cadre public fermé.

    Seule une paire `BEGIN`/`END` complète exempte : un en-tête orphelin ne doit
    pas ouvrir un trou où recopier une clé. Les lignes d'armure elles-mêmes ne
    sont pas rendues — elles ne sont pas du base64 et ne comptent pour rien.

    L'exemption **tombe** dès qu'une ligne intérieure est elle-même un délimiteur
    (`-----BEGIN` ou `-----END`) : le corps d'une clé publique ou d'un certificat
    n'en porte aucun, donc un délimiteur là est le signe d'une armure **privée**
    glissée dans un cadre public. C'est le détournement prouvé à la relecture de
    `2c8d91d`.

    Ce qui reste au-dehors du filet, et qu'aucune inspection ne peut trancher :
    un corps de base64 **nu** entre deux **faux** délimiteurs publics est
    indistinguable du corps d'une vraie clé publique. Celui-là passe — c'est le
    refus de l'en-tête privé (`secret_dans_une_ligne`) qui tient le secret.
    """
    interieures = set()
    for debut, fin in _CADRES_PUBLICS:
        ouverte = None
        for i, ligne in enumerate(lignes):
            nue = ligne.strip()
            if ouverte is None:
                if nue == debut:
                    ouverte = i
            elif nue == fin:
                interieur = lignes[ouverte + 1:i]
                if not any(_est_un_delimiteur(l) for l in interieur):
                    interieures.update(range(ouverte + 1, i))
                ouverte = None
    return interieures


def _est_un_delimiteur(ligne: str) -> bool:
    """Vrai si la ligne est une ligne d'armure (`-----BEGIN …` / `-----END …`)."""
    nue = ligne.strip()
    return nue.startswith("-----BEGIN") or nue.startswith("-----END")


def bloc_base64(contenu: str):
    """Rend la première ligne d'un bloc de base64 recopié, ou `None` sinon.

    Une clé recopiée **sans son en-tête** (`-----BEGIN …`) est une suite de
    lignes de base64 : `jeton_isole`, qui refuse tout espace, ne les voit pas.
    C'est ce trou que cette forme ferme. On exige au moins `LIGNES_BLOC_MIN`
    lignes **consécutives** dont chacune n'est que du base64 (au moins
    `LIGNE_BASE64_MIN` caractères) : une seule ligne citée, ou du base64 noyé
    dans la prose, ne suffit pas — la mémoire ordinaire passe.

    Deux formes **publiques** ne sont pas des secrets et ne se refusent pas :

    * les **empreintes** — un hexadécimal de 40 (SHA-1) ou 64 (SHA-256)
      caractères est dans l'alphabet du base64 sans en être, et trois empreintes
      à la suite sont un journal de notes, pas une clé ; c'est `empreinte_de_bloc`
      qui tranche, et **ces deux longueurs seules** ;
    * un bloc **encadré** par `-----BEGIN PGP PUBLIC KEY BLOCK-----` ou
      `-----BEGIN CERTIFICATE-----`, et fermé par la ligne `END` correspondante
      — une clé publique ou un certificat, faits pour être recopiés.

    L'exemption du cadre n'est pas un mur : elle tombe si un délimiteur s'y
    glisse (`_lignes_sous_cadre_public`), ce qui démasque une armure **privée**
    encadrée ; mais un corps **nu** entre deux faux délimiteurs publics reste,
    lui, indistinguable d'une vraie clé publique — **limite assumée**, consignée
    par un test. Le refus d'un secret recopié tient d'abord à son **en-tête**
    privé, que `secret_dans_une_ligne` refuse.
    """
    lignes = contenu.splitlines()
    exemptees = _lignes_sous_cadre_public(lignes)
    suite = 0
    for i, ligne in enumerate(lignes):
        nue = ligne.strip()
        if i in exemptees or empreinte_de_bloc(nue) or not _LIGNE_BASE64.match(nue):
            suite = 0
            continue
        suite += 1
        if suite >= LIGNES_BLOC_MIN:
            return nue
    return None


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


def secret_dans_une_ligne(texte: str):
    """Le premier secret d'une ligne, ou ``None`` — fonction pure.

    Rend ``(étiquette, extrait)``. Sert à ``verifier`` (ligne par ligne d'un
    commit) et à la porte d'entrée du produit, qui juge un texte candidat avant
    qu'il n'existe : la décision est prise des deux côtés par la même copie des
    motifs, sans dupliquer la finesse du cas « secret affecté ».
    """
    for etiquette, motif in motifs_secrets():
        trouve = motif.search(texte)
        if not trouve:
            continue
        if etiquette == "secret affecté":
            brut = _valeur_affectee(trouve.group(0))
            guillemetee = brut.lstrip()[:1] in ("\"", "'")
            if not valeur_a_forme_de_secret(
                    brut, contexte=texte, guillemetee=guillemetee):
                continue
        return (etiquette, trouve.group(0))
    return None


def verifier(coffre) -> int:
    """Rend 0 si ce que le commit ajoute est propre, 1 sinon — et dit quoi.

    Chaque refus nomme le fichier, la ligne et le motif ; la valeur n'est montrée
    que tronquée, pour ne pas la réintroduire là où on la lit. Les motifs sont
    demandés **une fois par commit**, avant tout jugement, même quand rien n'est
    à juger (`motifs_secrets`) : une étiquette disparue doit faire tomber le
    crochet, jamais le laisser muet faute d'avoir été sollicité.
    """
    coffre = Path(coffre)
    if not _est_depot(coffre):
        return 0

    # Un appel inconditionnel : c'est ici qu'une étiquette manquante de
    # `publier.BLOQUANTS` lève. Le remettre sous condition reviendrait à ne
    # plus vérifier la source dès qu'un commit n'ajoute aucune ligne.
    motifs_secrets()

    problemes = []
    for chemin, numero, texte in lignes_ajoutees(coffre):
        trouve = secret_dans_une_ligne(texte)
        if trouve is not None:
            problemes.append((chemin, numero, trouve[0], trouve[1]))
    for chemin in fichiers_indexes(coffre):
        contenu = contenu_indexe(coffre, chemin)
        if contenu is None:
            continue
        jeton = jeton_isole(contenu, contexte=chemin)
        if jeton is not None:
            problemes.append((chemin, None, "valeur isolée à forte entropie", jeton))
            continue
        bloc = bloc_base64(contenu)
        if bloc is not None:
            problemes.append((chemin, None, "bloc de base64 recopié", bloc))

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
