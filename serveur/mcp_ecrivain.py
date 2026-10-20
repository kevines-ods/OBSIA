#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Serveur MCP « ecrivain-du-coffre » — l'écrivain exposé à un harnais pilotant
un modèle local.

Le modèle **propose un geste** — poser un carnet, ranger une note, compléter une
note, lire l'inventaire des notes. La porte d'entrée le juge, le socle d'écriture
l'accomplit et le commit, ou le refuse **avec son motif**. Le modèle dit **quoi**
(auteur, projet, sujet, corps, source, zone…), **jamais où** : il ne nomme ni le
coffre, ni un dossier, ni un nom de fichier — c'est ``OBSIA_COFFRE`` qui désigne
le coffre, et l'écrivain calcule seul la destination.

Le coffre visé est celui que désigne ``OBSIA_COFFRE``. S'il est vide, ou s'il ne
désigne pas un dépôt de données, l'écrivain **refuse** : il ne se rabat jamais
sur un autre coffre (*fail-closed*).

Transport : **stdio**, JSON-RPC 2.0 délimité par des fins de ligne. Aucune
dépendance hors de la bibliothèque standard (§11), aucun accès réseau.

Variables d'environnement — les valeurs réelles vivent dans la configuration du
harnais, jamais dans le dépôt (§13) :

    ``OBSIA_COFFRE``   chemin du coffre de travail. **Aucun défaut** : sans
                       elle, l'écrivain refuse d'écrire.
"""

import json
import os
import sys
from pathlib import Path

# Un serveur ne doit rien laisser derrière lui : ni fichier compilé, ni trace.
sys.dont_write_bytecode = True

_ICI = Path(__file__).resolve().parent
_SOMME = (str(_ICI), str(_ICI.parent / "scripts"))
for _chemin in _SOMME:
    if _chemin not in sys.path:
        sys.path.insert(0, _chemin)

try:                                          # importé comme `serveur.mcp_ecrivain`
    from . import ecrivain as ECRIVAIN
    from . import gestes_des_notes as NOTES
except ImportError:                           # lancé à plat depuis son dossier
    import ecrivain as ECRIVAIN               # noqa: E402
    import gestes_des_notes as NOTES          # noqa: E402

import convention_des_notes as CONVENTION    # noqa: E402

NOM = "ecrivain-du-coffre"
VERSION = "1.0.0"
PROTOCOLE = "2025-06-18"

#: Le refus *fail-closed* : sans coffre désigné, on n'écrit nulle part.
SANS_COFFRE = ("Aucun coffre n'est désigné : la variable d'environnement "
               "OBSIA_COFFRE est vide ou absente. L'écrivain refuse d'écrire — "
               "il ne se rabat jamais sur un autre coffre.")

#: Les autres refus de coffre. Aucun ne recopie le chemin : une réponse part au
#: modèle, et le chemin d'une machine n'a rien à y faire (§13). Le chemin part au
#: **journal local**, lui seul (voir :func:`_journal`).
COFFRE_RELATIF = ("Le coffre doit être désigné par un **chemin absolu** : celui qui "
                  "est posé n'en est pas un. L'écrivain refuse d'écrire — un chemin "
                  "relatif dépendrait du dossier d'où le serveur a été lancé.")
COFFRE_INTROUVABLE = ("Le coffre désigné n'existe pas, ou l'écrivain ne peut pas le "
                      "lire. Il refuse d'écrire, plutôt que d'écrire ailleurs.")
COFFRE_DETOURNE = ("Le chemin du coffre passe par un **lien** : il désigne autre "
                   "chose que ce qu'il écrit. L'écrivain refuse d'écrire là où il "
                   "ne croit pas écrire — lui donner le chemin réel du coffre.")

#: Ce qu'une panne interne dit au modèle — le détail reste au journal local.
PANNE = "écriture impossible : le serveur a rencontré une panne interne"


class ParametreInvalide(Exception):
    """Un paramètre n'a pas le type que le schéma de l'outil annonce."""


# ------------------------------------------------------------------ le coffre

def _coffre() -> str:
    """Le coffre désigné par ``OBSIA_COFFRE`` — jamais un défaut."""
    return (os.environ.get("OBSIA_COFFRE") or "").strip()


def _journal(detail: str) -> None:
    """Le journal **local** du serveur : la sortie d'erreur, jamais la réponse.

    Ce qui s'y écrit ne part pas au modèle. C'est là que vont les détails qu'une
    réponse ne doit pas porter — le chemin d'une machine, le texte d'une
    exception : la sortie d'erreur ne sert qu'à qui exploite le serveur.
    """
    sys.stderr.write("ecrivain-du-coffre : %s\n" % detail)
    sys.stderr.flush()


def _passe_par_un_lien(chemin: Path) -> bool:
    """Vrai si un composant du chemin est un lien symbolique.

    On juge **composant par composant**, non en comparant le chemin écrit au
    chemin résolu : un `..` ou une barre de trop sont la même route (résoudre les
    efface), tandis qu'un lien, lui, mène réellement ailleurs. Un `..` posé après
    un lien changerait la cible : le composant lien est justement ce qu'on refuse.
    """
    courant = Path(chemin.anchor)
    for partie in chemin.parts[1:]:
        courant = courant / partie
        try:
            if courant.is_symlink():
                return True
        except OSError:
            return True                     # on ne peut pas juger : on refuse
    return False


def _coffre_ou_refus():
    """Le coffre à servir, ou le refus *fail-closed* s'il n'est pas désigné.

    Le coffre doit être désigné par un **chemin absolu**, et ce chemin ne doit
    passer par **aucun lien symbolique** : un lien mènerait ailleurs que là où
    l'on croit écrire. Un `..` ou une barre de trop, eux, restent la même route :
    on les accepte et l'on rend le chemin **réel** du coffre.
    """
    coffre = _coffre()
    if not coffre:
        return None, (SANS_COFFRE, True)
    chemin = Path(coffre)
    if not chemin.is_absolute():
        _journal("OBSIA_COFFRE n'est pas un chemin absolu : %r" % coffre)
        return None, (COFFRE_RELATIF, True)
    try:
        resolu = chemin.resolve(strict=True)
    except OSError as panne:
        _journal("OBSIA_COFFRE est introuvable : %s" % panne)
        return None, (COFFRE_INTROUVABLE, True)
    if _passe_par_un_lien(chemin):
        _journal("OBSIA_COFFRE passe par un lien : %r mène à %r" % (coffre, str(resolu)))
        return None, (COFFRE_DETOURNE, True)
    return str(resolu), None


def _texte(args: dict, nom: str, defaut: str = "") -> str:
    """Le paramètre `nom`, qui doit être une chaîne — sinon ``-32602``.

    Le schéma annonce des chaînes : un nombre, une liste ou un objet là où une
    chaîne est attendue n'est pas une demande qu'on juge, c'est une demande mal
    formée. On la rejette sans la traduire en douce.
    """
    valeur = args.get(nom)
    if valeur is None:
        return defaut
    if not isinstance(valeur, str):
        raise ParametreInvalide("le paramètre « %s » doit être une chaîne de "
                                "caractères" % nom)
    return valeur


def _mot(args: dict, nom: str) -> str:
    """Un paramètre qui **nomme** quelque chose : une chaîne, élaguée."""
    return _texte(args, nom).strip()


def _rendre(acte) -> tuple:
    """La trace d'un acte et son état d'erreur.

    Un acte refusé porte son motif dans ``trace()`` et vaut une erreur pour
    l'appelant : rien n'a été écrit.
    """
    return acte.trace(), (not acte.ecrit)


# ---------------------------------------------------------------- les gestes

def ecrire_un_carnet(args: dict) -> tuple:
    """Poser un carnet de chantier — la porte et le socle font le reste."""
    coffre, refus = _coffre_ou_refus()
    if refus is not None:
        return refus
    corps = _texte(args, "corps")               # -32602 si ce n'est pas une chaîne
    sujet = _mot(args, "sujet")
    if not sujet:
        return "Demande invalide : un carnet sans sujet n'a pas de nom.", True
    statut = _mot(args, "statut") or CONVENTION.STATUT_EN_COURS
    if statut not in CONVENTION.STATUTS_CARNET:
        return ("Demande invalide : « %s » n'est pas un statut de carnet (%s)."
                % (statut, ", ".join(CONVENTION.STATUTS_CARNET))), True
    acte = ECRIVAIN.ecrire_un_carnet(
        coffre,
        auteur=_mot(args, "auteur"),
        projet=_mot(args, "projet"),
        chantier=_mot(args, "chantier") or None,
        sujet=sujet,
        corps=corps,
        statut=statut,
        date=_mot(args, "date") or None,
    )
    return _rendre(acte)


def completer_une_note(args: dict) -> tuple:
    """Tenir une note sur place, au fil de l'eau."""
    coffre, refus = _coffre_ou_refus()
    if refus is not None:
        return refus
    texte = _texte(args, "texte")               # -32602 si ce n'est pas une chaîne
    source = _mot(args, "source")
    if not source:
        return "Demande invalide : quelle note compléter ?", True
    acte = NOTES.completer_une_note(
        coffre,
        auteur=_mot(args, "auteur"),
        source=source,
        texte=texte,
        date=_mot(args, "date") or None,
    )
    return _rendre(acte)


def ranger_une_note(args: dict) -> tuple:
    """Classer une note brute du vrac dans la zone que la porte autorise."""
    coffre, refus = _coffre_ou_refus()
    if refus is not None:
        return refus
    source = _mot(args, "source")
    zone = _mot(args, "zone")
    if not source or not zone:
        return "Demande invalide : il faut une note de départ et une zone d'arrivée.", True
    acte = NOTES.ranger_une_note(
        coffre,
        auteur=_mot(args, "auteur"),
        source=source,
        zone=zone,
        date=_mot(args, "date") or None,
    )
    return _rendre(acte)


def notes_du_coffre(args: dict) -> tuple:
    """Lire l'inventaire des notes du coffre, sans rien écrire."""
    coffre, refus = _coffre_ou_refus()
    if refus is not None:
        return refus
    try:
        noms = NOTES.notes_du_coffre(coffre)
    except NOTES.CoffreInjoignable as motif:
        return str(motif), True
    if not noms:
        return "Le coffre ne contient aucune note.", False
    return "\n".join(str(nom) for nom in noms), False


# ----------------------------------------------------------------- les outils

OUTILS = [
    {
        "name": "ecrire_un_carnet",
        "description": (
            "Poser un carnet dans le coffre, à partir de son sujet. L'écrivain "
            "calcule seul le nom du fichier, la date et le dossier : dire quoi, "
            "jamais où. La porte juge la demande et refuse avec son motif."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "auteur": {"type": "string",
                           "description": "Qui signe l'acte — le nom de l'agent."},
                "projet": {"type": "string",
                           "description": "Nom du projet : un seul nom, sans barre oblique."},
                "chantier": {"type": "string",
                             "description": "Nom du chantier quand le carnet en relève. Facultatif."},
                "sujet": {"type": "string",
                          "description": "Sujet du carnet ; sert à calculer son nom de fichier."},
                "corps": {"type": "string",
                          "description": "Le texte du carnet."},
                "statut": {"type": "string",
                           "enum": list(CONVENTION.STATUTS_CARNET),
                           "description": "Statut du carnet. Défaut : « en cours »."},
                "date": {"type": "string",
                         "description": "Date de l'acte en AAAA-MM-JJ. Défaut : aujourd'hui."},
            },
            "required": ["auteur", "projet", "sujet", "corps"],
        },
    },
    {
        "name": "ranger_une_note",
        "description": (
            "Classer une note brute du vrac dans une zone autorisée du coffre. "
            "La porte vérifie la provenance, la destination et le nom, et refuse "
            "avec son motif. Dire quoi, jamais où."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "auteur": {"type": "string",
                           "description": "Qui signe l'acte — le nom de l'agent."},
                "source": {"type": "string",
                           "description": "Nom de la note à ranger, tel qu'il apparaît dans l'inventaire."},
                "zone": {"type": "string",
                         "description": "Zone d'arrivée, par son nom — la porte juge si elle l'accepte."},
                "date": {"type": "string",
                         "description": "Date de l'acte en AAAA-MM-JJ. Défaut : aujourd'hui."},
            },
            "required": ["auteur", "source", "zone"],
        },
    },
    {
        "name": "completer_une_note",
        "description": (
            "Ajouter du texte à la fin d'une note tenue à la main et l'inscrire au "
            "registre des notes traitées. La note d'origine n'est pas réécrite. "
            "Dire quoi, jamais où."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "auteur": {"type": "string",
                           "description": "Qui signe l'acte — le nom de l'agent."},
                "source": {"type": "string",
                           "description": "Nom de la note à compléter, tel qu'il apparaît dans l'inventaire."},
                "texte": {"type": "string",
                          "description": "Le texte à ajouter à la note."},
                "date": {"type": "string",
                         "description": "Date de l'acte en AAAA-MM-JJ. Défaut : aujourd'hui."},
            },
            "required": ["auteur", "source", "texte"],
        },
    },
    {
        "name": "notes_du_coffre",
        "description": (
            "Lire l'inventaire des notes du coffre, sans doublon — leur nom relatif, "
            "tel que le porte le coffre. Matière pour repérer un doublon avant "
            "d'écrire ou de ranger. Ne modifie rien."
        ),
        "inputSchema": {"type": "object", "properties": {}},
    },
]

GESTES = {outil["name"]: globals()[outil["name"]] for outil in OUTILS}


# ------------------------------------------------------------- le protocole

def repondre(id_, resultat=None, erreur=None) -> None:
    """Écrit une réponse JSON-RPC sur la sortie standard, une ligne, un objet."""
    charge = {"jsonrpc": "2.0", "id": id_}
    if erreur is not None:
        charge["error"] = erreur
    else:
        charge["result"] = resultat
    sys.stdout.write(json.dumps(charge, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _id_du_message(message) -> object:
    """L'``id`` d'un message, quel qu'il soit — jamais une exception.

    Un message reçu n'est pas forcément un objet JSON-RPC : ``null``, un nombre,
    une chaîne, une liste sont du JSON valide. On ne peut donc pas leur demander
    leur ``id`` : on le lit si l'on peut, et sinon il n'y en a pas.
    """
    if isinstance(message, dict):
        return message.get("id")
    return None


def _parametres(message: dict, nom: str) -> dict:
    """Les ``params`` d'un message, ou ``{}`` — ce n'est pas forcément un objet."""
    params = message.get("params")
    return params if isinstance(params, dict) else {}


def traiter(message) -> None:
    """Répond à une requête ; ignore les notifications (sans ``id``)."""
    if not isinstance(message, dict):
        repondre(_id_du_message(message),
                 erreur={"code": -32600,
                         "message": "Requête invalide : un objet JSON-RPC est attendu"})
        return
    methode = message.get("method")
    id_ = message.get("id")
    if id_ is None:
        return
    if methode == "initialize":
        params = _parametres(message, "params")
        repondre(id_, {
            "protocolVersion": params.get("protocolVersion") or PROTOCOLE,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": NOM, "version": VERSION},
        })
    elif methode == "ping":
        repondre(id_, {})
    elif methode == "tools/list":
        repondre(id_, {"tools": OUTILS})
    elif methode == "tools/call":
        params = _parametres(message, "params")
        nom = params.get("name")
        geste = GESTES.get(nom)
        if geste is None:
            repondre(id_, erreur={"code": -32602,
                                  "message": "Outil inconnu : %s" % nom})
            return
        arguments = params.get("arguments")
        if arguments is None:
            arguments = {}
        if not isinstance(arguments, dict):
            repondre(id_, erreur={"code": -32602,
                                  "message": "`arguments` doit être un objet"})
            return
        try:
            texte, en_erreur = geste(arguments)
        except ParametreInvalide as faute:
            repondre(id_, erreur={"code": -32602, "message": str(faute)})
            return
        repondre(id_, {"content": [{"type": "text", "text": texte}],
                       "isError": en_erreur})
    else:
        repondre(id_, erreur={"code": -32601,
                              "message": "Méthode inconnue : %s" % methode})


def main() -> int:
    """La boucle stdio : une ligne, un message, une réponse.

    On lit des **octets** et on décode ligne à ligne : une suite d'octets qui
    n'est pas de l'UTF-8 ne doit pas tuer le serveur. Et rien, dans la boucle, ne
    s'appuie sur ce que le message *devrait* être : un message mal formé reçoit
    une erreur, et le suivant est traité comme si de rien n'était.
    """
    for brut in sys.stdin.buffer:
        try:
            ligne = brut.decode("utf-8").strip()
        except UnicodeDecodeError as panne:
            _journal("ligne illisible : %s" % panne)
            repondre(None, erreur={"code": -32700,
                                   "message": "Ligne illisible : UTF-8 invalide"})
            continue
        if not ligne:
            continue
        try:
            message = json.loads(ligne)
        except ValueError as panne:
            _journal("JSON invalide : %s" % panne)
            repondre(None, erreur={"code": -32700, "message": "JSON invalide"})
            continue
        try:
            traiter(message)
        except Exception as panne:      # aucune panne n'arrête le serveur
            # Le détail peut porter le chemin d'une machine : il reste au journal
            # local, la réponse au modèle n'en dit rien (§13).
            _journal("panne interne : %s: %s" % (type(panne).__name__, panne))
            repondre(_id_du_message(message),
                     erreur={"code": -32603, "message": PANNE})
    return 0


if __name__ == "__main__":
    sys.exit(main())
