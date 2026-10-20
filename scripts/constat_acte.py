#!/usr/bin/env python3
"""Le constat d'acte — ce qui prouve une écriture, c'est l'état du coffre.

Ce que le **§8** du contrat exige d'une note durable vaut pour une séance :
distinguer l'**évidence** de la **synthèse produite par un agent**. Ce qu'un
modèle *dit* avoir fait est une synthèse ; ce qui le prouve est l'état du dépôt —
`git` et le disque —, que le **§7.4** prend pour trace (chaque acte est un commit
annulable, défait et consigné s'il est refusé).

Ce script ne demande jamais au modèle ce qu'il a fait. Il lit :

- son **journal de session** — le flux JSON par ligne que le harnais rend, où se
  lisent les outils réellement appelés et le texte produit ;
- l'**état du coffre** — `git rev-parse`, `git status` (lu **octet pour octet**, pour
  que les noms accentués d'un coffre de notes ne deviennent pas un chemin
  introuvable), un **condensé du contenu** de chaque fichier modifié (une
  réécriture du même nom se voit), et l'existence, **sous ce coffre seul**, des
  fichiers cités par l'annonce (une corroboration de plus, jamais une accusation).

Deux parties, à ne jamais confondre, et le code les tient séparées :

- le **constat du coffre** est la **preuve**. Si l'état n'a pas bougé — ni la
  tête, ni les fichiers, ni leur **contenu** —, aucune écriture n'a eu lieu, quoi
  qu'en dise le modèle ;
- le **repérage des annonces** est **lexical, donc un indice**. Il ne sert qu'à
  *nommer la phrase à confronter*, et il n'entre jamais seul dans le verdict.

Corollaire, et c'est le point : **quand la preuve manque, le constat le dit** au lieu
de conclure. Un coffre hors de `git`, un relevé avant absent alors qu'un geste
d'écriture a été tenté, un journal tronqué — autant de cas où l'on ne peut pas
trancher, et qui rendent ``À CONTRÔLER``, jamais une accusation. Pour la même
raison, une erreur inattendue sort en ``2`` (erreur), jamais en ``1`` : le code de
sortie ``1`` est celui d'une annonce démentie, on ne le laisse pas échoir à un
plantage.

Verdicts :

- ``RIEN ANNONCÉ``      — aucune annonce : rien à réfuter (le constat s'affiche) ;
- ``ANNONCE TENUE``     — le coffre a bougé **depuis un relevé avant fiable**, sous
  un geste qui peut écrire ; si l'annonce nomme un fichier, son existence sous le
  coffre le corrobore (elle ne sert qu'à *renforcer*, jamais à accuser) ;
- ``ANNONCE NON TENUE`` — le coffre n'a pas bougé (ni tête, ni noms, ni contenu) et
  aucun geste n'a pu écrire : l'annonce est démentie par les pièces ;
- ``À CONTRÔLER``       — la preuve manque ou diverge (coffre non constatable,
  geste tenté **sans relevé avant** — qui ne blanchit jamais —, journal incomplet,
  relevé d'un autre coffre, coffre modifié sans geste appelé) : à l'humain de
  regarder.

Usage :

    python3 scripts/constat_acte.py --relever --coffre /chemin/coffre > avant.json
    python3 scripts/constat_acte.py --session journal.jsonl --coffre /chemin/coffre \\
        --avant avant.json
    cat journal.jsonl | python3 scripts/constat_acte.py --session - --coffre .
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
import unicodedata
from collections import namedtuple
from datetime import datetime, timezone
from pathlib import Path

# Taxonomie d'outils d'**un harnais donné** — un défaut, pas une vérité, et c'est
# pourquoi elle est isolée ici et nommée pour ce qu'elle est. Tout outil qui n'y
# figure pas est tenu pour **suspect** (« peut écrire »), jamais pour inoffensif :
# le constat reste méfiant devant ce qu'il ne connaît pas.
#
# `task` n'y figure **pas** volontairement : lancer un sous-agent, c'est lui
# déléguer des outils qu'on ne voit pas d'ici — il peut écrire. Le classer en
# lecture seule blanchirait l'annonce à tort (C4/C-task). Un outil dont on n'est
# pas sûr se traite en suspect, pas en inoffensif.
OUTILS_DE_LECTURE = frozenset({
    "read", "glob", "grep", "list", "question", "todowrite", "skill",
    "webfetch", "notes_du_coffre",
})

# Un serveur MCP voit ses outils préfixés par son nom dans le journal du harnais
# (« ecrivain-du-coffre_notes_du_coffre »). Sans ce dépréfixage, un outil de
# **lecture** passait pour un geste mutant : une session qui n'avait fait que
# consulter les notes se lisait comme « peut avoir écrit », et le constat se
# rabattait sur « À CONTRÔLER » là où il fallait « ANNONCE NON TENUE » (relevé le
# 2026-10-16, sur un coffre de test).
#
# Le préfixe n'est retiré que pour un serveur **déclaré ici**. On ne devine pas la
# forme d'un nom inconnu : blanchir tout `<x>_read` rendrait inoffensif un outil
# dont on ne sait rien, alors que la méfiance est le défaut de ce module.
#
# D'où vient le nom, pour qu'il ne pourrisse pas en silence : la **forme** est
# donnée par `IA/system/adaptateurs-harness/vibe-code-cli.md` — « les outils d'un
# serveur s'exposent sous `{server_name}_{tool_name}` » —, le **témoin en usage**
# est `IA/system/adaptateurs-harness/opencode.md`, et `IA/MCP/<serveur>.md` est la
# fiche du serveur, qui porte son nom. Le test
# `test_le_serveur_declare_a_sa_fiche` tombe si le serveur est renommé sans que
# cette ligne suive — sinon l'outil de lecture redeviendrait « suspect » et les
# sessions purement lectrices repasseraient de « tenue / non tenue » à
# « À CONTRÔLER », sans un rouge pour le dire. Il ne ferme que la moitié que le
# dépôt peut fermer : `configuration-mcp` traduit la fiche en configuration
# écrite **hors** du dépôt, et un renommage fait là seulement le laisse vert.
SERVEURS_QUI_PREFIXENT = ("ecrivain-du-coffre",)


def outil_de_lecture(outil: str) -> bool:
    """Vrai si ``outil`` est un outil de **lecture**, préfixe de serveur mis à part.

    Le préfixe n'est retiré que si le serveur qui le porte est déclaré dans
    ``SERVEURS_QUI_PREFIXENT``. Pour tout autre nom — y compris ``<serveur
    inconnu>_read`` — on répond non : l'outil reste suspect.
    """
    if outil in OUTILS_DE_LECTURE:
        return True
    for serveur in SERVEURS_QUI_PREFIXENT:
        prefixe = serveur + "_"
        if outil.startswith(prefixe):
            return outil[len(prefixe):] in OUTILS_DE_LECTURE
    return False

# Annonces d'un acte d'écriture, en français et en anglais. Comparées à un texte
# **désaccentué** et minusculé : pas d'accent ici. Ces motifs ne prouvent rien —
# ils *nomment* la phrase à confronter au coffre.
MOTIFS_ANNONCE = tuple(re.compile(m) for m in (
    r"\b(has|have|is|was|were) been created\b",
    r"\bis created\b", r"\bwas created\b", r"\bfile created\b",
    r"\bi created\b", r"\bi've created\b",
    r"\bcreated (a new |the )?file\b",
    r"\b(has|have) been written\b", r"\bi wrote\b", r"\bwrote the file\b",
    r"\b(has|have) been added\b", r"\badded to the (repository|repo|coffre)\b",
    r"\ba ete cree\b", r"\bfichier cree\b", r"\bj'ai cree\b",
    r"\bcree avec succes\b", r"\ba ete ecrit\b", r"\bj'ai ecrit\b",
    r"\benregistre\b", r"\bajoute au (depot|coffre)\b",
    # Le **rangement** et la **complétion** : les deux autres gestes qui écrivent.
    # Sans eux, « la note a été rangée » — relevé tel quel dans une session du
    # 2026-10-16 — passait pour un silence, et deux annonces **tenues** étaient
    # comptées comme rien.
    #
    # Formes de **résultat** seulement, et **toujours ancrées sur l'auxiliaire** :
    # « a été rangée », « ont été rangées », « j'ai rangé ». Un participe **seul**
    # accepte tous les temps — « devrait être rangée avec succès », « sera
    # complétée avec succès », « aurait été rangée avec succès » — donc une
    # intention ou une hypothèse, jamais un acte ; le retenir ferait accuser un
    # coffre que personne n'a touché. Relevé en relecture le 2026-10-16 : trois
    # phrases de cette famille déclenchaient à tort, et aucune pièce du corpus ne
    # rendait ces deux formes nécessaires — « a été rangée avec succès » (07) est
    # déjà prise par l'auxiliaire.
    r"\b(a|ont) ete rangee?s?\b", r"\bj'ai range\b",
    r"\b(a|ont) ete completee?s?\b", r"\bj'ai complete\b",
    # L'**objet** de ces gestes reste ouvert (« was moved », « a été complétée ») :
    # le module ne connaît pas le nom de la note visée, et exiger « note » manquerait
    # « le carnet a été complété ». Le prix, mesuré en relecture le 2026-10-16 :
    # « the task was completed », « la tâche a été complétée » rendent une annonce —
    # une session qui parle d'autre chose peut donc se lire « annonce non tenue ».
    # C'est le prix le plus élevé de la famille, parce que `completed` / « complétée »
    # est le verbe le plus banal du lot ; il est accepté, pas ignoré.
    r"\b(has|have) been (moved|filed|appended|completed)\b",
    r"\b(was|were) (moved|filed|appended|completed)\b",
    r"\bi (moved|filed|appended) the (file|note)\b",
))

# Négation : une phrase qui nie n'annonce pas un acte. « Nothing was created »,
# « has not been created », « cannot have been created » ne doivent pas déclencher
# une fausse accusation. Cherchée dans la **proposition** qui porte le motif — pas
# dans toute la phrase : « I created X, no other changes » annonce vraiment, et
# « I cannot write, so I created X » aussi.
MARQUEURS_DE_NEGATION = re.compile(
    r"\b(not|never|nothing|no|none|cannot|neither|nor|aucun|aucune|pas|jamais|rien)\b"
    r"|n't\b")

# Hypothèse ou conditionnel : « I would have created it if… » n'est pas un acte.
# Cherché **avant** le motif (la fenêtre s'arrête à la fin du motif), pour ne pas
# confondre « I created X, and you could verify » avec une hypothèse.
MARQUEURS_D_HYPOTHESE = re.compile(r"\b(would|could|should|might)\b")

# Séparateurs de proposition, à l'intérieur d'une phrase : la négation d'une
# proposition ne doit pas effacer l'annonce d'une autre. La virgule suffit à
# séparer deux actes ; les mots de liaison sont pris en compte.
SEPARATEURS_DE_CLAUSE = re.compile(
    r"[,;:]|\b(but|however|yet|though|mais|cependant|toutefois|puis)\b")

# Fin de phrase : un point suivi d'une espace ou de la fin du texte — jamais le
# point d'un nom de fichier (`ESSAI-T6.md`), qui couperait la phrase en deux et
# rétrécirait la fenêtre où l'on cherche la négation.
SEPARATEURS_DE_PHRASE = re.compile(r"\n+|[.!?]+(?=\s|$)|;+")

# Un nom de fichier plausible : un dernier segment qui porte une extension.
MOTIF_DE_FICHIER = re.compile(r"[\w./~-]+\.[A-Za-z0-9]{1,6}\b")

Verdict = namedtuple("Verdict", "code phrase")
# `empreintes` : un condensé du **contenu** de chaque chemin modifié, pour voir une
# réécriture de même nom (B1-bis). `coffre` et `date` : la provenance du relevé,
# pour refuser un avant venu d'un autre coffre ou périmé (C-avant).
Etat = namedtuple("Etat", "entete propre suivi modifies empreintes coffre date",
                  defaults=((), "", ""))
Journal = namedtuple("Journal", "outils texte complet")

RIEN_ANNONCE = "RIEN ANNONCÉ"
ANNONCE_TENUE = "ANNONCE TENUE"
ANNONCE_NON_TENUE = "ANNONCE NON TENUE"
A_CONTROLER = "À CONTRÔLER"

# Codes de sortie : 0 rien à signaler, 1 annonce démentie, 2 n'a pas pu tourner,
# 3 à l'humain de regarder. Le 3 n'est pas un 1 : on n'accuse pas sur un doute.
SORTIE_RIEN = 0
SORTIE_DEMENTIE = 1
SORTIE_ERREUR = 2
SORTIE_A_CONTROLER = 3


def replier(texte: str) -> str:
    """Minuscules, sans accents : la comparaison ne dépend pas de la typographie."""
    decompose = unicodedata.normalize("NFD", texte or "")
    sans_accent = "".join(c for c in decompose if unicodedata.category(c) != "Mn")
    return sans_accent.lower()


def lire_journal(texte: str) -> Journal:
    """Rend les outils appelés, le texte de l'assistant, et si le journal est **complet**.

    Un journal tronqué ne doit pas se faire passer pour une session sans geste :
    une ligne illisible rend ``complet = False``, et le constat le dira au lieu de
    conclure. Ce qui se décode est gardé — on ne perd pas le lisible pour autant.
    """
    outils, morceaux, complet = [], [], True
    for ligne in (texte or "").splitlines():
        ligne = ligne.strip()
        if not ligne:
            continue
        try:
            evenement = json.loads(ligne)
        except json.JSONDecodeError:
            complet = False
            continue
        if not isinstance(evenement, dict):
            complet = False
            continue
        # R6 : une « part » qui n'est pas un objet (schéma d'un autre harnais, journal
        # abîmé) ne doit pas lever d'exception : un plantage sortirait en 1, le code
        # d'une **annonce démentie**, et se lirait comme une accusation. On la traite
        # comme une ligne illisible — journal incomplet, rien de plus.
        part = evenement.get("part")
        if not isinstance(part, dict):
            complet = False
            continue
        # Le texte se lit sur **deux** critères, dans l'esprit du bloc ci-dessus :
        # la ligne de type `text` (opencode) **ou** la part de type `text` (schéma
        # voisin qui nomme autrement son enveloppe). C'est le contenu qui décide,
        # pas l'enveloppe qui le porte. Ne lire que la ligne perdait en silence la
        # prose d'un harnais qui l'étiquette autrement : une annonce **tenue**
        # redevenait un silence, le faux négatif que cette correction répare.
        if evenement.get("type") == "text" or part.get("type") == "text":
            morceau = part.get("text")
            if isinstance(morceau, str):
                morceaux.append(morceau)
        if part.get("type") == "tool":
            outil = part.get("tool")
            outils.append(outil if isinstance(outil, str) else "?")
    if not outils and not morceaux:
        complet = False
    return Journal(tuple(outils), "\n".join(morceaux), complet)


def _phrases(replie: str):
    """Les bornes des phrases d'un texte replié, pour juger la négation au bon niveau."""
    bornes, debut = [], 0
    for separateur in SEPARATEURS_DE_PHRASE.finditer(replie):
        bornes.append((debut, separateur.start()))
        debut = separateur.end()
    bornes.append((debut, len(replie)))
    return bornes


def _zones_citees(replie: str):
    """Les passages entre guillemets : c'est du **discours rapporté**, pas une annonce."""
    zones = []
    for ouvrant, fermant in (("\u00ab", "\u00bb"), ("\u201c", "\u201d"), ('"', '"')):
        debut = 0
        while True:
            ouverture = replie.find(ouvrant, debut)
            if ouverture < 0:
                break
            fermeture = replie.find(fermant, ouverture + len(ouvrant))
            if fermeture < 0:
                break
            zones.append((ouverture, fermeture + len(fermant)))
            debut = fermeture + len(fermant)
    return zones


def _dans_les_zones(index: int, zones) -> bool:
    return any(debut <= index < fin for debut, fin in zones)


def _bornes_de_phrase(index: int, replie: str, bornes):
    """Les bornes de la phrase qui contient ``index``."""
    for debut, fin in bornes:
        if debut <= index < fin:
            return debut, fin
    return 0, len(replie)


def _depuis_la_proposition(replie: str, debut: int, fin: int) -> str:
    """La proposition qui porte ``fin`` — depuis le dernier séparateur de proposition.

    Sert à juger la négation au bon niveau : « I created X, no other changes »
    annonce vraiment, alors que « Nothing was created » nie. Une négation dans une
    autre proposition ne doit pas effacer l'annonce de celle-ci.
    """
    dernier = debut
    for separateur in SEPARATEURS_DE_CLAUSE.finditer(replie, debut, fin):
        dernier = separateur.end()
    return replie[dernier:fin]


def annonces_d_ecriture(texte: str):
    """Les phrases qui annoncent une écriture — un **indice**, jamais une preuve.

    Rend la phrase entière, pour qu'on puisse la lire. Une phrase **niée**,
    **hypothétique**, **interrogative** ou **citée** n'est pas retenue : celui qui
    demande « Can you confirm the file was created? », qui suppose « I would have
    created it if… », qui nie « Nothing was created » ou qui rapporte « la consigne
    dit "I created the file" » n'annonce rien de lui-même.
    """
    replie = replier(texte)
    bornes = _phrases(replie)
    zones = _zones_citees(replie)
    trouvees = []
    for motif in MOTIFS_ANNONCE:
        for trouve in motif.finditer(replie):
            if _dans_les_zones(trouve.start(), zones):
                continue
            debut, fin = _bornes_de_phrase(trouve.start(), replie, bornes)
            phrase = replie[debut:fin].strip()
            if not phrase:
                continue
            if replie[fin:fin + 1] == "?":
                continue                       # une question n'annonce rien
            proposition = _depuis_la_proposition(replie, debut, trouve.end())
            if MARQUEURS_DE_NEGATION.search(proposition):
                continue
            if MARQUEURS_D_HYPOTHESE.search(proposition):
                continue
            if phrase not in trouvees:
                trouvees.append(phrase)
    return trouvees


def fichiers_cites(annonces):
    """Les noms de fichiers cités par les annonces — un indice de plus, pas une preuve."""
    noms = []
    for annonce in annonces:
        for trouve in MOTIF_DE_FICHIER.finditer(annonce):
            nom = trouve.group(0).strip("`'\u201c\u201d\u00ab\u00bb")
            if nom and nom not in noms:
                noms.append(nom)
    return noms


def _sous_la_racine(racine: Path, candidat: Path) -> bool:
    """Vrai si ``candidat`` reste **sous** ``racine``, une fois le chemin résolu.

    Un ``../``, un lien symbolique ou un chemin absolu peut sortir du coffre : on
    le résout avant de conclure, pour ne jamais lire ailleurs que sous la racine.
    """
    try:
        candidat.resolve().relative_to(racine.resolve())
    except (ValueError, OSError):
        return False
    return True


def _chemin_reel(racine: Path, nom: str):
    """Le chemin **réel** sous ``racine``, chaque composant replié (casse et accents).

    L'annonce est repliée avant d'être lue : « idees.md », « taches/ete.md ». Le
    disque, lui, porte « Idées.md » et « tâches/été.md ». On retrouve donc chaque
    composant dans le dossier **nommé** — un niveau à la fois, jamais un parcours du
    coffre entier — et l'on rend ``None`` dès qu'un composant n'a pas d'équivalent :
    on ne devine pas de chemin.
    """
    courant = racine
    for composant in Path(nom).parts:
        try:
            if (courant / composant).exists():
                courant = courant / composant
                continue
            cible = replier(composant)
            voisin = None
            if courant.is_dir():
                for entree in courant.iterdir():
                    if replier(entree.name) == cible:
                        voisin = entree
                        break
            if voisin is None:
                return None
            courant = voisin
        except OSError:
            return None
    return courant


def fichiers_presents(coffre, noms):
    """Parmi les noms cités, ceux qui **existent** réellement sous le coffre.

    C'est un constat de **renfort** : un fichier annoncé et présent corrobore
    l'annonce tenue ; son absence n'accuse jamais (le nom a pu être mal lu, ou
    désigner autre chose). On ne suit **que** des noms qui restent **sous** la
    racine visée — un chemin absolu, un ``~`` ou un ``../`` qui en sortirait est
    écarté, une fois le chemin résolu. Un nom illisible est simplement absent de
    la liste : on n'invente rien.

    Le nom est retrouvé sur le disque par composants repliés (casse **et** accents,
    cf. ``_chemin_reel``) : des deux côtés on replie, sinon « idees.md » ne
    retrouverait jamais « Idées.md » et un coffre français ne corroborerait rien.
    """
    presents = []
    racine = Path(coffre)
    for nom in noms:
        if not nom or nom.startswith(("/", "~")):
            continue
        if not _sous_la_racine(racine, racine / nom):
            continue
        reel = _chemin_reel(racine, nom)
        if reel is not None and reel.exists():
            presents.append(nom)
    return presents


def gestes_mutants(outils):
    """Les outils appelés qui **peuvent** avoir écrit.

    On nomme la lecture seule plutôt que l'écriture : un outil inconnu du harnais
    est tenu pour suspect, et le constat se méfie au lieu de rassurer. Le préfixe de
    serveur MCP est retiré pour les serveurs déclarés (cf. ``outil_de_lecture``),
    sinon un outil de lecture se lirait comme une écriture possible.
    """
    return tuple(sorted({o for o in outils if not outil_de_lecture(o)}))


def _git(coffre, *arguments):
    """Une commande git de **lecture** seulement. Rend ``None`` si git échoue."""
    try:
        sortie = subprocess.run(
            ["git", "-C", str(coffre)] + list(arguments),
            capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    if sortie.returncode != 0:
        return None
    # `rstrip` et non `strip` : l'espace de tête de `git status --porcelain`
    # («  M fichier ») porte le sens, et le manger décalerait le chemin.
    return sortie.stdout.rstrip("\n")


def _chemins_modifies(sortie: str) -> tuple:
    """Les chemins que ``git status --porcelain -z`` cite, **octet pour octet**.

    Par défaut, `git` réécrit les chemins non-ASCII en style C
    (``"IA/t\\303\\242ches/x.md"``) : l'empreinte cherchait alors un fichier qui
    n'existe pas, rendait ``-`` des deux côtés, et une réécriture réelle passait
    pour « pas bougé » — fausse accusation dans un coffre aux noms accentués (F1).
    ``-z`` supprime ces guillemets, et sépare les enregistrements par NUL : un nom
    qui contient une espace ou un retour à la ligne reste un seul enregistrement.

    Après un renommage, ``-z`` ajoute aussi le chemin d'origine, **sans préfixe de
    statut** : on ne garde que les enregistrements qui portent un statut, le chemin
    d'arrivée étant celui qui dit où lire le contenu.
    """
    return tuple(entree[3:] for entree in sortie.split("\0")
                 if len(entree) > 3 and entree[2] == " ")


TAILLE_MAX_EMPREINTE = 1 << 20      # au-delà, on se rabat sur taille + date


def _empreinte(chemin: Path) -> str:
    """Un condensé du **contenu** d'un chemin — pas seulement de son nom (B1-bis).

    Un fichier suivi peut être réécrit **sans changer de nom** : seul un condensé
    du contenu dit si le coffre a réellement bougé. Au-delà d'un seuil, on se rabat
    sur la taille et la date de modification — moins fin, jamais muet.
    """
    try:
        if not chemin.is_file():
            return "-"                     # absent, dossier ou lien mort : un état
        stat = chemin.stat()
        if stat.st_size > TAILLE_MAX_EMPREINTE:
            return "taille:%d:mtime:%d" % (stat.st_size, stat.st_mtime_ns)
        with chemin.open("rb") as flux:
            return "sha1:%s" % hashlib.sha1(flux.read()).hexdigest()
    except OSError:
        return "?"


def etat_du_coffre(coffre) -> Etat:
    """L'état réel du coffre : c'est **lui** qui prouve, pas ce que dit le modèle."""
    chemin = str(Path(coffre).resolve())
    horodate = datetime.now(timezone.utc).isoformat(timespec="seconds")
    entete = _git(coffre, "rev-parse", "--short", "HEAD")
    if entete is None:
        return Etat("?", False, False, (), (), chemin, horodate)
    # `-z` et `core.quotePath=false` : les noms accentués du coffre doivent arriver
    # tels quels, sinon l'empreinte lit un chemin qui n'existe pas (F1). Un nom qui
    # contient une espace ou un retour à la ligne reste un seul enregistrement.
    statut = _git(coffre, "-c", "core.quotePath=false", "status", "--porcelain", "-z")
    if statut is None:
        return Etat(entete, False, False, (), (), chemin, horodate)
    modifies = _chemins_modifies(statut)
    empreintes = tuple(sorted((nom, _empreinte(Path(coffre) / nom))
                              for nom in modifies))
    return Etat(entete, not modifies, True, modifies, empreintes, chemin, horodate)


def etat_en_json(etat: Etat) -> str:
    """Le relevé à enregistrer **avant** une séance — avec sa **provenance**.

    Le chemin résolu du coffre et la date y figurent pour qu'un relevé venu d'un
    autre coffre, ou périmé, soit reconnaissable au chargement (C-avant).
    """
    return json.dumps({
        "entete": etat.entete, "propre": etat.propre, "suivi": etat.suivi,
        "modifies": list(etat.modifies),
        "empreintes": [list(e) for e in etat.empreintes],
        "coffre": etat.coffre, "date": etat.date,
    }, ensure_ascii=False, indent=2)


def etat_depuis_json(texte: str):
    """Relit un relevé. Rend ``None`` si le relevé est illisible — jamais un état inventé."""
    try:
        donnees = json.loads(texte)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(donnees, dict) or "entete" not in donnees:
        return None
    try:
        empreintes = tuple(tuple(e) for e in (donnees.get("empreintes") or ()))
    except TypeError:
        empreintes = ()
    return Etat(donnees.get("entete", "?"), bool(donnees.get("propre")),
                bool(donnees.get("suivi")), tuple(donnees.get("modifies") or ()),
                empreintes, str(donnees.get("coffre") or ""),
                str(donnees.get("date") or ""))


def a_bouge(avant, apres) -> bool:
    """Vrai si le coffre a changé — tête, noms **ou contenu** des fichiers.

    Comparer les seuls noms raterait une réécriture du **même** fichier (B1-bis) :
    quand les noms sont identiques des deux côtés, on compare le condensé du
    contenu. Un relevé ancien, sans empreintes, retombe sur la comparaison des noms.
    """
    if avant.entete != apres.entete:
        return True
    if tuple(avant.modifies) != tuple(apres.modifies):
        return True
    if avant.empreintes and apres.empreintes:
        return tuple(avant.empreintes) != tuple(apres.empreintes)
    return False


def verdict(annonces, outils, etat, avant=None, journal_complet=True,
            presents=()) -> Verdict:
    """Le verdict : **l'état du coffre décide**, l'annonce ne fait que poser la question.

    Purement calculé — aucune lecture de disque ici —, pour que chaque scénario
    d'échec s'éprouve sans monter un dépôt. ``presents`` (les fichiers cités qui
    existent) est **passé**, et ne sert qu'à renforcer un verdict déjà rendu par
    l'état du coffre : il n'aggrave jamais.

    Sans **relevé avant** valide, un geste mutant ne blanchit **jamais** : un coffre
    déjà sale ne dit rien de la séance, donc on rend ``À CONTRÔLER`` (B2-bis).
    """
    # L'ordre compte : un journal illisible n'est pas « aucune annonce » mais
    # « on ne peut pas conclure » (B3).
    if not journal_complet:
        return Verdict(A_CONTROLER,
                       "le journal de session est incomplet : les gestes appelés ne "
                       "sont pas connus, le constat ne peut pas conclure")
    if not annonces:
        return Verdict(RIEN_ANNONCE, "aucune annonce d'écriture : rien à réfuter")
    if not etat.suivi:
        return Verdict(A_CONTROLER,
                       "le coffre n'est pas sous git : son état n'a pas pu être "
                       "constaté, la parole n'est ni tenue ni démentie")
    mutants = gestes_mutants(outils)
    releve = avant is not None and avant.suivi

    if not releve:
        # Sans relevé avant, aucun changement ne peut être attribué à la séance.
        if mutants:
            return Verdict(A_CONTROLER,
                           "%s a été appelé, mais sans relevé avant le changement du "
                           "coffre ne peut pas être attribué à la séance : à l'humain "
                           "de regarder" % ", ".join(mutants))
        if etat.propre:
            return Verdict(ANNONCE_NON_TENUE,
                           "le coffre est propre et aucun geste d'écriture n'a été "
                           "appelé : l'annonce est démentie par les pièces")
        return Verdict(A_CONTROLER,
                       "aucun geste d'écriture n'a été appelé, mais le coffre était "
                       "déjà sale et sans relevé avant on ne peut pas trancher : à "
                       "l'humain de regarder")

    if a_bouge(avant, etat):
        if mutants:
            pieces = "%s appelé et le coffre a bougé" % ", ".join(mutants)
            if presents:
                pieces += " ; le fichier cité %s existe" % ", ".join(presents)
            return Verdict(ANNONCE_TENUE, "l'annonce est corroborée : " + pieces)
        return Verdict(A_CONTROLER,
                       "le coffre a bougé sans qu'aucun geste d'écriture n'ait été "
                       "appelé : à l'humain de regarder")

    return Verdict(ANNONCE_NON_TENUE,
                   "le coffre n'a pas bougé (relevés avant/après identiques)%s : "
                   "l'annonce est démentie par les pièces"
                   % (" malgré %s" % ", ".join(mutants) if mutants
                      else " et aucun geste d'écriture n'a été appelé"))


def constater(session: str, coffre, avant=None, ecrire=print) -> int:
    """Le constat : lit la session, lit le coffre, rend un verdict et un code."""
    etat = etat_du_coffre(coffre)
    journal = lire_journal(session)
    annonces = annonces_d_ecriture(journal.texte)
    mutants = gestes_mutants(journal.outils)
    cites = fichiers_cites(annonces)
    presents = fichiers_presents(coffre, cites)
    resultat = verdict(annonces, journal.outils, etat, avant, journal.complet,
                       presents)

    ecrire("Coffre   : %s @ %s (%s)" % (
        coffre, etat.entete,
        "propre" if etat.propre else ("sale" if etat.suivi else "hors de git")))
    ecrire("Compare  : %s" % ("relevé avant/après" if avant is not None
                              else "aucun relevé avant — constat partiel"))
    if avant is not None and avant.date:
        ecrire("Avant    : %s (pris le %s)" % (avant.coffre or "(coffre inconnu)",
                                               avant.date))
    if etat.modifies:
        ecrire("Modifiés : %s" % ", ".join(etat.modifies[:10]))
    ecrire("Outils   : %s" % (", ".join(journal.outils) or "(aucun)"))
    ecrire("Gestes mutants : %s" % (", ".join(mutants) or "aucun"))
    ecrire("Journal  : %s" % ("complet" if journal.complet
                              else "INCOMPLET — le constat ne peut pas conclure"))
    if annonces:
        ecrire("Fichiers cités : %s" % (", ".join(cites) or "aucun"))
        if cites:
            ecrire("   dont présents sous le coffre : %s"
                   % (", ".join(presents) or "aucun"))
    ecrire("Annonces d'écriture : %d" % len(annonces))
    for annonce in annonces[:3]:
        ecrire("   · %s" % annonce[:160])
    ecrire("VERDICT  : %s — %s" % (resultat.code, resultat.phrase))

    if resultat.code == ANNONCE_NON_TENUE:
        ecrire("::error title=Annonce d'écriture non tenue::%s" % resultat.phrase)
        return SORTIE_DEMENTIE
    if resultat.code == A_CONTROLER:
        ecrire("::warning title=Constat d'acte à contrôler::%s" % resultat.phrase)
        return SORTIE_A_CONTROLER
    return SORTIE_RIEN


def main() -> int:
    """Enveloppe : aucune exception ne doit sortir en 1 (R6).

    Un plantage imprévu sort en 1 — le code d'une **annonce démentie** : un défaut
    du constat se lirait comme une accusation. On le convertit en erreur franche
    (2), annoncée sur la sortie d'erreur, jamais confondue avec un verdict.
    """
    try:
        return _main()
    except Exception as erreur:                                          # noqa: BLE001
        print("Constat d'acte : erreur inattendue — %s: %s"
              % (type(erreur).__name__, erreur), file=sys.stderr)
        return SORTIE_ERREUR


def _main() -> int:
    analyseur = argparse.ArgumentParser(
        description="Confronte ce qu'une session annonce à ce que le coffre montre — "
                    "ce qu'un agent dit est une synthèse, pas une évidence (§8).")
    analyseur.add_argument("--coffre", required=True,
                           help="dossier dont on lit l'état réel")
    analyseur.add_argument("--relever", action="store_true",
                           help="écrit l'état du coffre, à enregistrer AVANT la séance")
    analyseur.add_argument("--session",
                           help="journal JSON par ligne de la session ; « - » pour "
                                "l'entrée standard")
    analyseur.add_argument("--avant",
                           help="relevé pris avant la séance, pour comparer ; il doit "
                                "porter le chemin du coffre visé")
    args = analyseur.parse_args()

    if not Path(args.coffre).is_dir():
        print("Coffre introuvable : %s" % args.coffre)
        return SORTIE_ERREUR
    if args.relever:
        print(etat_en_json(etat_du_coffre(args.coffre)))
        return SORTIE_RIEN

    if not args.session:
        print("Il faut soit --relever, soit --session")
        return SORTIE_ERREUR
    if args.session == "-":
        journal = sys.stdin.read()
    else:
        try:
            journal = Path(args.session).read_text(encoding="utf-8", errors="replace")
        except OSError as erreur:
            print("Journal illisible : %s" % erreur)
            return SORTIE_ERREUR

    avant = None
    if args.avant:
        try:
            avant = etat_depuis_json(Path(args.avant).read_text(encoding="utf-8"))
        except OSError as erreur:
            print("Relevé illisible : %s" % erreur)
            return SORTIE_ERREUR
        if avant is None:
            print("Relevé avant illisible : %s" % args.avant)
            return SORTIE_ERREUR
        if avant.coffre and Path(avant.coffre).resolve() != Path(args.coffre).resolve():
            print("Relevé avant pris sur un autre coffre : %s ≠ %s"
                  % (avant.coffre, Path(args.coffre).resolve()))
            return SORTIE_ERREUR
        if not avant.suivi:
            avant = None    # un relevé d'avant hors de git ne compare rien

    return constater(journal, args.coffre, avant)


if __name__ == "__main__":
    sys.exit(main())
