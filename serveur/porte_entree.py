#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""La porte d'entrée : juger un texte candidat **avant** tout disque (P2).

Le modèle ne propose pas un chemin — il propose un **sujet** validé et un texte.
La porte calcule elle-même le nom du fichier et sa destination, puis refuse tant
qu'un contrôle n'est pas satisfait :

1. ``aucun chemin ne vient du modèle`` — le sujet ne porte ni ``/``, ni ``..``,
   ni ``.md`` (§6) ; et un nom **fourni** doit être celui que la règle dérive : la
   porte le recalcule depuis la zone et le sujet brut, et refuse tout autre — un
   nom libre serait un chemin choisi par le modèle (§6, §7.4) ;
2. ``zone autorisée`` — la destination appartient à la liste que l'appelant a
   donnée, moins les exclusions structurelles ;
3. ``sujet exploitable`` — le sujet donne un nom de fichier, et ce nom **réel** —
   celui qui s'écrirait, non une forme repliée une seconde fois — tient dans le
   plafond d'octets (§6) ;
4. ``dépôt imbriqué`` — aucune part de la zone n'est un ``code/``, un
   ``node_modules/`` ou un dossier caché (§7.3) ;
5. ``mémoire gelée`` — la destination ne tombe pas dans un chantier clos de
   ``0-MEMOIRES/`` (§6) ;
6. ``zone du contrat`` — le §7.3 ouvre bien cette destination à cet **auteur**,
   pour cette **nature**. Sans auteur — ou sans coffre, pour lire le gel — la
   porte refuse : elle ne devine pas un « tout est ouvert » ;
7. ``nom réservé`` — le nom n'est pas un fichier de dossier (§6) ;
8. ``nom unique`` — le nom n'existe pas déjà dans la zone (§6) ;
9. ``dossier jumeau`` — le dossier de la destination ne se replie pas au même nom
   qu'un dossier voisin : l'aperçu du jour replie le dossier d'origine, et deux
   dossiers jumeaux le partageraient (§6, §7.4) ;
10. ``nom unique dans le coffre`` — un **dépôt** ne sème pas un second porteur du
   même nom ailleurs dans le coffre parent : le §6 vaut sur tout le coffre, pas
   seulement sur la zone qui reçoit la note ;
11. ``compléter juge la note présente`` — l'acte qui complète donne le texte déjà
   écrit de la note : sans lui, « sans en changer le sens » ne se mesure pas (§7.3) ;
12. ``absence de secret`` — aucun secret nommé ni jeton isolé (§7.1) ; il parle
   **avant** la forme, parce qu'un refus de mise en forme devant une clé privée
   corrige des ``---`` et laisse la clé ;
13. ``frontmatter conforme`` — pas de second bloc, pas de champ répété (§5) ;
14. ``listes YAML sur une ligne`` — une liste s'écrit **une entrée par ligne** (§5) ;
15. ``tags du vocabulaire`` — chaque tag vient du registre (§7.5).

Un acte peut aussi partir d'une note **déjà présente** (``source``) : ``ranger`` la
déplace d'``0-EN-VRAC/`` vers sa zone, ``compléter`` la reprend **sur place**. Le
nom n'est alors plus dérivé d'un sujet — c'est celui du fichier présent — et la
porte refuse tout autre nom que le sien. Les **deux** chemins sont jugés : la
source (``la note visée n'est pas là``, ``le vrac seul est une source``, ``le
geste et le chemin s'accordent``), puis la destination. Compléter n'ajoute qu'à la
fin du corps (``compléter n'ajoute qu'à la fin``) et son frontmatter ne perd ni ne
change aucune clé (``compléter garde le frontmatter``) — la note **présente** doit
être donnée pour que ça se mesure (``compléter juge la note présente``). Le
registre des notes traitées se complète de même (§7.4).

Tout refus **guide** : il nomme le contrôle, dit le constat, cite la règle et
donne le geste suivant. Un refus n'est jamais une simple référence.

**Rien ne s'écrit.** La porte est pure : elle prend un candidat et un contexte,
elle rend un verdict. Les règles, elles, ne sont pas recopiées — elles viennent
du moteur partagé (``convention_des_notes``) et de ``garde_secrets``.
"""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path
from typing import Container, Mapping, NamedTuple

sys.dont_write_bytecode = True
_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import convention_des_notes as CONVENTION   # noqa: E402
import garde_secrets as SECRETS             # noqa: E402

try:                                        # importé comme `serveur.porte_entree`
    from . import carte_legale as CARTE
except ImportError:                         # importé à plat : le dossier est sur le chemin
    import carte_legale as CARTE            # noqa: E402

#: La règle citée par chaque refus : le contrat où elle est écrite.
CONTRAT = "VAULT-CONTRACT.md"

#: Ce qui sépare les mots d'un sujet : tout ce qui n'est pas une lettre.
_SEPARATEURS = re.compile(r"[^0-9a-zà-ÿ]+")

#: Les systèmes de fichiers limitent un nom à 255 octets ; on laisse la marge
#: qu'exige un suffixe éventuel. Un nom au-delà échouerait à l'écriture : la
#: porte le refuse avant le disque, plutôt que de laisser l'erreur tomber après.
NOM_MAX_OCTETS = 200


class Refus(NamedTuple):
    """Pourquoi un candidat est refusé, et par où repasser."""

    controle: str        # quel contrôle a refusé
    constat: str         # ce qui cloche, en une phrase
    regle: str           # la règle, citée
    geste: str           # le geste suivant attendu


class Candidat(NamedTuple):
    """Ce que le modèle propose : une zone nommée, un sujet, un texte.

    ``sujet`` est toujours la **matière brute** dont le nom se dérive : le titre en
    mots pour une note ordinaire et pour un carnet, le nom du carnet lui-même pour
    la copie d'aperçu (§7.4, dont :func:`nom_de_l_apercu` dérive).

    ``dossier`` ne sert qu'à l'aperçu : c'est le **dossier d'origine** de la note
    (celui de sa ``source``), qui entre dans le nom de l'aperçu du jour pour que deux
    notes homonymes de deux dossiers ne se le disputent pas. Il est vide pour tout
    autre acte.

    ``nom`` est là pour un acte dont le **nom vient du moteur** et non du sujet : le
    carnet du §6 (``AAAA-MM-JJ-dossier-sujet.md``, dont le dossier garde
    l'orthographe réelle du coffre) et l'aperçu daté qui l'accompagne. La porte
    **recalcule** alors le nom que la règle dérive de la zone, du sujet et du dossier
    d'origine, et **refuse** celui qui diffère : un nom fourni n'est jamais libre —
    sinon ce serait un chemin choisi par le modèle. Vide, c'est le sujet qui donne le
    nom, comme pour une note ordinaire.

    ``source`` nomme le chemin, **relatif au coffre**, d'une note déjà présente :
    ``ranger`` en déplace une d'``0-EN-VRAC/``, ``compléter`` reprend la sienne
    **sur place** (§7.4). Le nom reste alors celui du fichier — ``nom`` doit être
    exactement le sien, et la porte refuse un autre nom. ``avant`` porte le texte
    que la note portait **déjà** : ``None`` — le défaut — dit « pas donné », et la
    porte refuse, parce que « compléter ne réécrit pas le sens » ne se mesure pas
    (§7.3) ; ``""`` dit « la note portait un texte **vide** », et cela se mesure.
    """

    zone: str
    sujet: str
    texte: str
    nom: str = ""
    source: str = ""             # le chemin relatif d'une note déjà là (§7.4) ; vide = création
    avant: str | None = None     # le texte déjà écrit de la note qu'on complète (§7.3)
    dossier: str = ""            # le dossier d'origine, pour l'aperçu du §7.4 ; vide ailleurs


class Contexte(NamedTuple):
    """Ce que le serveur sait déjà : les zones autorisées, leur contenu, le
    vocabulaire contrôlé, qui écrit, ce qu'il fait, et de quel coffre il s'agit.
    Bâti par la carte légale, jamais par le modèle.

    ``auteur`` et ``coffre`` sont **obligatoires**, et leur absence **refuse** :
    écrire sans dire qui écrit n'est pas jugeable au §7.3, et sans coffre le §6
    ne se lit pas — la porte ne devine pas un « tout est ouvert ». ``nature``
    dit ce que l'acte est (``créer``, ``compléter``, ``déposer``, ``corriger``) :
    une note **neuve** dans une zone qui n'ouvre que le dépôt est refusée, et un
    dépôt dans une zone qui ne se complète pas l'est aussi. L'absence de
    ``nature`` ne dispense pas de la juger : c'est ``créer``, l'acte le plus
    étroit, qui vaut alors.

    ``agents`` sert au seul §6 : un agent non déclaré n'est pas vivant. Enfin
    ``notes_du_coffre`` est l'inventaire des notes du coffre, chemins **relatifs
    à sa racine** : c'est ce qui permet de juger l'unicité du §6 sur tout le
    coffre, et non sur une seule zone.
    """

    zones: tuple                 # les zones autorisées, dans l'ordre
    noms_presents: Mapping       # zone -> chemins relatifs des notes déjà là
    vocabulaire: Container       # les tags du vocabulaire contrôlé
    auteur: str = ""             # qui écrit (§7.3) : "utilisateur", un agent ; vide = refusé
    coffre: object = None        # la racine du coffre, pour juger la mémoire gelée (§6) ; None = refusé
    agents: frozenset = frozenset()  # les agents déclarés, pour la mémoire vivante (§6)
    nature: str = ""             # ce que l'acte est (§7.3) ; vide = `créer`, l'acte le plus étroit
    notes_du_coffre: tuple = ()  # les chemins de toutes les notes du coffre, relatifs à sa racine


class Verdict(NamedTuple):
    """La destination calculée si tout va bien, sinon le refus."""

    destination: str | None
    refus: Refus | None

    @property
    def accepte(self) -> bool:
        return self.refus is None


# ------------------------------------------------------------------ le nom

def nom_de_note(sujet: str):
    """Le nom de fichier d'une note, dérivé du sujet — ou ``None``.

    ``Ma note sur Docker`` → ``ma-note-sur-docker.md``. Le nom dit le sujet (§6),
    il vient de la porte et non du modèle : le modèle n'a pas le droit de
    proposer un chemin.

    Le sujet passe d'abord par **NFKC** : les caractères de compatibilité
    (ligature ``ﬁ``, chiffre cerclé ``①``, ``½``, ``㎏``, pleine chasse) se
    replient en leur équivalent ordinaire au lieu d'être comptés pour des
    séparateurs et **perdus**. Sans ce repli, ``ﬁchier`` se rognait en
    ``chier.md`` et la clé du nom écrit cessait d'être la clé du sujet — la note
    devenait introuvable par sa propre clé
    (``tests/test_nommage_du_coffre.py``). NFKC **recompose** les accents : ``é``
    reste ``é``, le nom de note reste lisible, et la fabrication garde son
    écart assumé avec :func:`convention.tige_de_nom`, qui replie, lui.
    """
    base = _SEPARATEURS.sub(
        "-", unicodedata.normalize("NFKC", sujet).strip().lower()).strip("-")
    if not base:
        return None
    return base + ".md"


def destination(zone: str, nom: str) -> str:
    """Le chemin relatif de la note, construit par la porte (jamais par le modèle)."""
    return "/".join((zone.strip("/"), nom))


def _porte_un_chemin(sujet: str) -> bool:
    """Le sujet cherche-t-il à passer un chemin plutôt qu'un titre ?

    ``/`` et ``\\`` suffisent à repérer un chemin ; ``..`` seul et les dossiers
    cachés sont pris par le point initial. Un titre qui contient des points de
    suspension (« Points de suspension… ») reste donc un titre.
    """
    if "/" in sujet or "\\" in sujet:
        return True
    if sujet.startswith("."):
        return True
    return sujet.lower().endswith((".md", ".markdown"))


# --------------------------------------------------------------- les refus

def _lisible(texte: str) -> str:
    """Un texte de refus, sans caractère de contrôle qui casserait la trace.

    Un nom fourni peut porter un ``\\n`` ou une tabulation : le citer tel quel
    ferait d'une phrase de refus deux lignes, et la trace ne se lirait plus.
    """
    return "".join(c if c.isprintable() else "?" for c in texte)


def _refus_chemin(sujet: str):
    if _porte_un_chemin(sujet):
        return Refus(
            "aucun chemin ne vient du modèle",
            "le sujet porte un chemin (`%s`)" % sujet,
            CONTRAT + " §6",
            "donner un titre en mots : le nom et la destination sont calculés "
            "par la porte, à partir de la zone choisie dans la carte")
    return None


def _refus_zone(zone: str, contexte: Contexte):
    """La zone appartient-elle à la liste que l'appelant a donnée ?

    Le contrôle porte sur **cette liste** — les zones que la carte a retenues
    pour cet auteur, moins les exclusions structurelles. C'est le cran le plus
    grossier, et il ne dit rien du §7.3 : l'appartenance au contrat se juge plus
    fin, une fois le nom connu (``_refus_matrice``), parce qu'un `` — vision`` et
    un `` — résumé`` du même dossier ne se distinguent que par leur nom.
    """
    if zone not in contexte.zones:
        return Refus(
            "zone autorisée",
            "`%s` n'est pas une des zones autorisées" % zone,
            CONTRAT + " §7.3",
            "choisir une destination parmi celles de la carte légale")
    return None


def _refus_sujet(sujet: str):
    if nom_de_note(sujet) is None:
        return Refus(
            "sujet exploitable",
            "le sujet `%s` ne donne aucun nom de note" % sujet,
            CONTRAT + " §6",
            "donner un titre en mots, qui dise le sujet de la note")
    return None


def _refus_longueur(nom: str):
    """Le nom **réel** tient-il dans le plafond d'octets ? (§6)

    On mesure le nom qui s'écrirait, jamais une forme repliée une seconde fois :
    replier un accent ou une capitale le raccourcit, et un nom trop long passerait
    alors par la porte sans que rien ne l'arrête.
    """
    octets = len(nom.encode("utf-8"))
    if octets <= NOM_MAX_OCTETS:
        return None
    return Refus(
        "sujet exploitable",
        "le nom `%s` ferait %d octets (maximum %d)"
        % (_lisible(nom), octets, NOM_MAX_OCTETS),
        CONTRAT + " §6",
        "raccourcir le titre : un nom trop long ne s'écrirait pas")


def _refus_imbrique(zone: str):
    """Un ``code/``, un dossier caché : la règle de la carte, une seule fois."""
    parts = CARTE.parties_hors_memoire(zone)
    if parts:
        return Refus(
            "dépôt imbriqué",
            "`%s` passe par `%s`, hors mémoire" % (zone, parts[0]),
            CONTRAT + " §7.3",
            "choisir une zone de la carte : un `code/`, un dossier caché ou "
            "un dépôt imbriqué ne reçoit pas de note")
    return None


def _dossier_du_carnet(zone: str):
    """Le dossier d'un ``…/carnets`` — celui que **la zone** nomme, pas l'appelant.

    ``0-PROJETS/obsia/carnets`` → ``obsia`` ; ``0-PROJETS/obsia/<chantier>/carnets``
    → ``<chantier>``. C'est la zone qui dit l'orthographe du dossier — le coffre
    peut porter ``Homelab`` — et c'est d'elle que la porte recalcule le nom d'un
    carnet quand un candidat en apporte un. Rend ``None`` hors d'un ``carnets/`` :
    là, la zone ne dérive aucun nom.
    """
    parts = [p for p in zone.strip("/").split("/") if p]
    if len(parts) >= 2 and parts[-1] == "carnets":
        return parts[-2]
    return None


def _refus_nom_simple(nom: str):
    """Le nom fourni est-il un **nom de fichier nu**, et non un chemin ? (§6)

    Un nom d'acte ne porte ni barre oblique, ni remontée, ni blanc de bord, ni
    point initial : sinon ce ne serait plus un nom posé dans une zone, mais un
    chemin choisi — et le §6 n'aurait plus de porte.
    """
    if not nom.endswith(".md"):
        return Refus(
            "aucun chemin ne vient du modèle",
            "le nom fourni `%s` ne se termine pas par `.md`" % _lisible(nom),
            CONTRAT + " §6",
            "apporter le nom exact que la règle dérive, ou laisser le sujet donner "
            "le nom")
    if (nom.strip() != nom or nom.startswith(".")
            or any(c in nom for c in ("/", "\\"))):
        return Refus(
            "aucun chemin ne vient du modèle",
            "le nom fourni `%s` n'est pas un simple nom de fichier" % _lisible(nom),
            CONTRAT + " §6",
            "apporter un nom nu : la destination est calculée par la porte")
    return None


def _refus_nom_fourni(candidat: Candidat):
    """Le nom que le candidat apporte est-il **celui que la règle dérive** ?

    Un acte peut apporter un nom déjà calculé — le carnet du §6, la copie d'aperçu
    d'un carnet, ou celle d'une note ordinaire (§7.4) — mais jamais un nom *libre* :
    la porte le recalcule depuis la zone et le sujet brut, et refuse s'il diffère.
    Sans ce recalcul, un nom fourni serait un chemin que le modèle choisit, et le
    §6 n'aurait plus de porte.
    """
    refus = _refus_nom_simple(candidat.nom)
    if refus is not None:
        return refus
    nom = candidat.nom
    date = nom[:10]
    dossier = _dossier_du_carnet(candidat.zone)
    if dossier is not None:
        # Avant de recalculer : le nom doit être **daté** (`AAAA-MM-JJ-`). Sans cela
        # dix caractères de bruit tiendraient lieu de date — `!@#$%^&*()-obsia-bilan.md`
        # se recalculerait à l'identique, et la vérification du coffre ne verrait
        # plus un carnet.
        if not CONVENTION.carnet_a_la_forme(nom):
            return Refus(
                "aucun chemin ne vient du modèle",
                "le nom fourni `%s` ne commence pas par une date de carnet "
                "(`AAAA-MM-JJ-`)" % _lisible(nom),
                CONTRAT + " §6",
                "nommer le carnet par sa date réelle, ou laisser la porte le calculer")
        attendu = CONVENTION.nom_de_carnet(date, dossier, candidat.sujet)
    elif candidat.zone == CONVENTION.MAINTENANCE:
        # Le nom d'un aperçu de la maintenance commence par une **date**
        # (`AAAA-MM-JJ-`) : sans cela, dix caractères de bruit tiendraient lieu de
        # date et la vérification du coffre ne reconnaîtrait plus l'aperçu (§6).
        if not CONVENTION.carnet_a_la_forme(nom):
            return Refus(
                "aucun chemin ne vient du modèle",
                "le nom fourni `%s` ne commence pas par une date (`AAAA-MM-JJ-`)"
                % _lisible(nom),
                CONTRAT + " §7.4",
                "faire dériver l'aperçu par la règle du moteur : la date du jour en "
                "tête")
        # Une **seule** forme : la règle du moteur, calculée du sujet *et* du dossier
        # d'origine. Un carnet y garde son nom entier, date comprise ; une note
        # ordinaire y met son dossier d'origine devant son nom tel quel. Le dossier
        # vient avec le candidat, donc il se recalcule comme le reste : un aperçu qui
        # s'attribue le dossier d'un autre est forgé.
        if _refus_nom_simple(candidat.sujet) is not None:
            return Refus(
                "aucun chemin ne vient du modèle",
                "l'aperçu `%s` ne dérive pas d'une note" % _lisible(nom),
                CONTRAT + " §7.4",
                "faire dériver l'aperçu du nom exact de la note, dossier d'origine "
                "compris")
        attendus = [CONVENTION.nom_de_l_apercu(date, candidat.sujet, candidat.dossier)]
        if nom not in attendus:
            return Refus(
                "aucun chemin ne vient du modèle",
                "le nom fourni `%s` n'est pas celui que la règle dérive (%s)"
                % (_lisible(nom),
                   " ni ".join("`%s`" % _lisible(un) for un in attendus)),
                CONTRAT + " §7.4",
                "apporter le nom exact que la règle dérive de la zone et du sujet")
        return None
    else:
        return Refus(
            "aucun chemin ne vient du modèle",
            "un nom fourni (`%s`) n'est accepté que pour un carnet ou son aperçu"
            % _lisible(nom),
            CONTRAT + " §6",
            "laisser le sujet donner le nom : hors d'un `carnets/` ou de `%s/`, le "
            "nom n'est pas libre" % CONVENTION.MAINTENANCE)
    if nom != attendu:
        return Refus(
            "aucun chemin ne vient du modèle",
            "le nom fourni `%s` n'est pas celui que la règle dérive (`%s`)"
            % (_lisible(nom), _lisible(attendu)),
            CONTRAT + " §6",
            "apporter le nom exact que la règle dérive de la zone et du sujet")
    return None


def _refus_matrice(zone: str, nom: str, candidat: Candidat, contexte: Contexte):
    """Le §7.3 ouvre-t-il cette destination à l'auteur, pour cette nature ?

    La porte refuse une zone hors matrice, même fournie par l'appelant, et
    surtout un auteur que la règle ne nomme pas — une note « — vision » au
    visionnaire, les ``expériences/`` à l'agent dont le dossier porte le nom, et la
    **note de référence** de ``0-PERSONNELS/`` à l'agent que son champ ``auteur:``
    nomme. Ce dernier ne se lit pas dans le chemin : la porte passe donc au moteur
    le texte **proposé** et le texte **déjà écrit**, pour qu'il exige le même nom
    dans les deux. La **nature** compte autant que l'auteur : une note neuve dans
    une zone qui n'ouvre que le dépôt est refusée.

    Sans ``auteur``, il n'y a pas d'auteur à juger — et ce n'est pas un « tout
    est ouvert » : la porte **refuse** (échec fermé), sous le motif unique du
    moteur.
    """
    chemin = destination(zone, nom)
    if not CONVENTION.auteur_declare(contexte.auteur):
        return Refus(
            "zone du contrat",
            CONVENTION.MOTIF_AUTEUR_ABSENT,
            CONTRAT + " §7.3",
            "déclarer l'auteur qui écrit — l'utilisateur, ou un agent nommé "
            "dans la carte")
    ouvert, motif = CONVENTION.zone_autorisee(
        chemin, contexte.auteur,
        contexte.nature or CONVENTION.NATURE_CREER,
        note=candidat.texte, avant=candidat.avant)
    if ouvert:
        return None
    return Refus(
        "zone du contrat",
        "%s : %s" % (chemin, motif),
        CONTRAT + " §7.3",
        "écrire dans une zone que le §7.3 ouvre à cet auteur, ou confier "
        "l'écriture à celui que la zone nomme")


def _refus_gele(zone: str, nom: str, contexte: Contexte):
    """La destination tombe-t-elle dans une mémoire gelée du coffre ?

    La règle vient du moteur partagé : un chantier clos de ``0-MEMOIRES/`` ne
    s'écrit plus (§6), quand les préférences et les ``expériences/`` d'un agent
    restent vivantes.

    Sans ``coffre``, le §6 ne se lit pas — et l'ignorance n'ouvre pas : la porte
    **refuse** (échec fermé), plutôt que de laisser écrire dans un chantier clos
    faute d'avoir regardé.
    """
    chemin = destination(zone, nom)
    if contexte.coffre is None:
        return Refus(
            "mémoire gelée",
            "le coffre n'est pas déclaré : le §6 ne peut pas être lu",
            CONTRAT + " §6",
            "déclarer la racine du coffre, sans quoi un chantier clos ne peut "
            "pas être distingué d'un chantier vivant")
    if not CONVENTION.est_gele(Path(contexte.coffre) / chemin,
                               Path(contexte.coffre), set(contexte.agents)):
        return None
    return Refus(
        "mémoire gelée",
        "%s tombe dans un chantier clos de %s/" % (chemin, CONVENTION.MEMOIRES),
        CONTRAT + " §6",
        "un chantier clos ne s'écrit plus : viser les préférences, ou les "
        "expériences de l'agent qui écrit")


def _refus_reserve(nom: str):
    if CONVENTION.est_fichier_de_dossier(nom):
        return Refus(
            "nom réservé",
            "`%s` est un fichier de dossier, pas une note" % nom,
            CONTRAT + " §6",
            "choisir un titre qui ne soit pas un fichier de dossier")
    return None


def _refus_unique(nom: str, candidat: Candidat, contexte: Contexte):
    """Un homonyme occupe-t-il **le dossier de destination** lui-même ?

    ``noms_presents`` porte des chemins **relatifs à la zone**, ``nom`` est un nom
    de fichier nu : la comparaison les retient donc séparément — **le dossier doit
    être le même à l'identique**, seul le nom de fichier passe par la forme
    comparable. Sans cela, ``nom_comparable`` aplatissant *aussi* la barre oblique,
    un ``sous/docker.md`` prendrait le titre « sous docker » de la racine, et le
    refus renverrait vers un sous-dossier où rien ne se ressemble.

    Le côté fichier se compare sur la clé du moteur partagé (``nom_comparable``) :
    le sujet dérive un kebab (``homelab-vision.md``) quand la note présente s'appelle
    peut-être ``Homelab — vision.md`` — les comparer au caractère près laisserait
    passer un doublon en silence. Et c'est la note **réellement présente** qu'on
    cite, pas le nom qu'on s'apprêtait à écrire.

    Ce contrôle ne vaut que pour une note **neuve**. Quand l'acte part d'une note
    déjà présente (``source``) pour la reprendre, la cible **est** cette note : sa
    présence est attestée par sa source, et la lire comme un homonyme interdirait
    tout simplement de compléter quoi que ce soit.
    """
    if candidat.source and (contexte.nature or CONVENTION.NATURE_CREER) in (
            CONVENTION.NATURE_COMPLETER, CONVENTION.NATURE_CORRIGER):
        return None
    zone = candidat.zone
    dossier, _, fichier = nom.rpartition("/")
    cle = CONVENTION.nom_comparable(fichier)

    def meme_dossier(chemin: str) -> bool:
        dossier_present, _, fichier_present = chemin.rpartition("/")
        return (dossier_present == dossier
                and CONVENTION.nom_comparable(fichier_present) == cle)

    homonyme = next((p for p in contexte.noms_presents.get(zone, ())
                     if meme_dossier(p)), None)
    if homonyme is not None:
        return Refus(
            "nom unique",
            "`%s` existe déjà dans `%s`" % (homonyme, zone),
            CONTRAT + " §6",
            "donner un autre titre, ou compléter `%s` au lieu d'en créer une "
            "seconde" % destination(zone, homonyme))
    return None


def _refus_frontmatter(texte: str):
    bloc = CONVENTION.frontmatter_brut(texte)
    if texte.startswith("---") and bloc is None:
        return Refus(
            "frontmatter conforme",
            "le frontmatter s'ouvre sans jamais se refermer",
            CONTRAT + " §5",
            "fermer le bloc par une ligne `---` avant le corps")
    repetees = CONVENTION.cles_repetees(texte)
    if repetees:
        return Refus(
            "frontmatter conforme",
            "le champ `%s` est écrit deux fois" % repetees[0],
            CONTRAT + " §5",
            "ne garder qu'une valeur par champ : la dernière gagnerait en silence")
    if CONVENTION.corps(texte).lstrip().startswith("---"):
        return Refus(
            "frontmatter conforme",
            "un second bloc de frontmatter s'ouvre dans le corps",
            CONTRAT + " §5",
            "un seul frontmatter en tête de note ; le corps ne commence pas par `---`")
    return None


def _refus_liste_en_ligne(texte: str):
    """Le contrat veut **une entrée par ligne**, pas une liste écrite sur une ligne.

    ``tags: [docker, réseau]`` passerait sinon pour un unique tag ``[docker,
    réseau]``, absent du vocabulaire : le refus parlerait du vocabulaire au lieu
    de la forme de la liste, et enverrait le modèle corriger le mauvais point.
    """
    cles = CONVENTION.listes_en_ligne(texte)
    if cles:
        return Refus(
            "listes YAML sur une ligne",
            "le champ `%s` porte une liste écrite sur une ligne" % cles[0],
            CONTRAT + " §5",
            "réécrire le champ en une entrée par ligne : une valeur par ligne, "
            "précédée d'un `- `")
    return None


def _tags_du_texte(texte: str) -> list:
    """Les tags d'un candidat : ceux du frontmatter et ceux du corps."""
    tags: list = []
    meta, _ = CONVENTION.extraire_frontmatter(texte)
    if isinstance(meta, dict):
        brut = meta.get("tags") or meta.get("tag")
        if isinstance(brut, (list, tuple)):
            tags.extend(str(t) for t in brut)
        elif brut:
            tags.append(str(brut))
    tags.extend(CONVENTION.tags_inline(CONVENTION.corps(texte)))
    return tags


def _refus_tags(texte: str, contexte: Contexte):
    hors = [t for t in _tags_du_texte(texte) if t not in contexte.vocabulaire]
    if hors:
        return Refus(
            "tags du vocabulaire",
            "le tag `%s` n'est pas au vocabulaire contrôlé" % hors[0],
            CONTRAT + " §7.5",
            "choisir un tag du registre, ou le proposer dans la section des "
            "candidats avant de s'en servir")
    return None


def _refus_secret(texte: str):
    for ligne in texte.splitlines():
        trouve = SECRETS.secret_dans_une_ligne(ligne)
        if trouve is not None:
            return Refus(
                "absence de secret",
                "un secret (%s) est écrit dans la note" % trouve[0],
                CONTRAT + " §7.1",
                "retirer la valeur : un secret ne rentre pas dans le coffre, il "
                "se désigne par son nom ou son emplacement")
    # Le jeton et le bloc se jugent sur le **corps**, hors frontmatter : jugés
    # sur la note entière — que son frontmatter rend espacée — ils ne se
    # déclenchaient jamais dans le passage de l'écrivain (relecture de #167).
    if SECRETS.jeton_isole(CONVENTION.corps(texte)) is not None:
        return Refus(
            "absence de secret",
            "le corps de la note a la forme d'un jeton",
            CONTRAT + " §7.1",
            "écrire une note en mots : un jeton seul n'est pas une note")
    if SECRETS.bloc_base64(CONVENTION.corps(texte)) is not None:
        return Refus(
            "absence de secret",
            "le corps de la note est un bloc de base64 recopié",
            CONTRAT + " §7.1",
            "retirer la valeur : un secret ne rentre pas dans le coffre, il "
            "se désigne par son nom ou son emplacement")
    return None


# ----------------------------------------------------------------- le verdict

def _chemins_du_coffre(contexte: Contexte) -> set:
    """Les chemins des notes du coffre, **relatifs à sa racine** (§6).

    Deux sources se complètent : l'inventaire que l'appelant donne
    (``notes_du_coffre``, qui voit tout le coffre) et les zones que la porte
    connaît déjà (``noms_presents``). L'union sert à juger l'unicité là où elle
    vaut vraiment — sur tout le coffre — et à vérifier qu'une ``source`` existe.
    """
    chemins = set(contexte.notes_du_coffre)
    for zone, presents in contexte.noms_presents.items():
        for chemin in presents:
            chemins.add(destination(zone, chemin))
    return chemins


def _refus_de_la_source(candidat: Candidat, contexte: Contexte):
    """Le chemin **source** qu'apporte l'acte est-il celui qu'il dit ? (§7.4)

    Un acte peut partir d'une note **déjà présente** : ``ranger`` en déplace une
    d'``0-EN-VRAC/``, ``compléter`` reprend la sienne **sur place**. Alors le nom
    n'est plus dérivé d'un sujet — c'est celui du fichier — et la porte refuse tout
    autre nom que le sien : le §6 reste une porte, même quand l'acte cite un chemin.

    Le gel et la matrice s'appliquent **des deux côtés** : la source comme la
    destination.
    """
    refus = _refus_nom_simple(candidat.nom)
    if refus is not None:
        return refus
    source = candidat.source.strip("/")
    morceaux = source.split("/")
    if (source != candidat.source or not source or source.startswith(".")
            or any(m in ("", ".", "..") for m in morceaux)):
        return Refus(
            "aucun chemin ne vient du modèle",
            "la source `%s` n'est pas un chemin de note" % _lisible(candidat.source),
            CONTRAT + " §6",
            "nommer la note par son chemin dans le coffre, sans remontée ni blanc")
    if morceaux[-1] != candidat.nom:
        return Refus(
            "aucun chemin ne vient du modèle",
            "le nom fourni `%s` n'est pas celui de la note à la source (`%s`)"
            % (_lisible(candidat.nom), _lisible(morceaux[-1])),
            CONTRAT + " §6",
            "apporter le nom exact de la note présente au chemin source")
    if source not in _chemins_du_coffre(contexte):
        return Refus(
            "la note visée n'est pas là",
            "aucune note au chemin source `%s`" % _lisible(source),
            CONTRAT + " §7.4",
            "viser une note réellement présente dans le coffre")
    nature = contexte.nature or CONVENTION.NATURE_CREER
    if nature == CONVENTION.NATURE_DEPOSER:
        if not source.startswith(CONVENTION.VRAC + "/"):
            return Refus(
                "le vrac seul est une source",
                "un rangement ne part que d'`%s/` (`%s`)"
                % (CONVENTION.VRAC, _lisible(source)),
                CONTRAT + " §7.3",
                "classer la note depuis `%s/` : c'est de là que vient le classement"
                % CONVENTION.VRAC)
        if destination(candidat.zone, candidat.nom) == source:
            return Refus(
                "le geste et le chemin s'accordent",
                "ranger déplace la note : la destination est la source (`%s`)"
                % _lisible(source),
                CONTRAT + " §7.4",
                "donner une zone de classement, pas celle d'où la note vient")
    elif nature in (CONVENTION.NATURE_COMPLETER, CONVENTION.NATURE_CORRIGER):
        if destination(candidat.zone, candidat.nom) != source:
            return Refus(
                "le geste et le chemin s'accordent",
                "compléter ne déplace pas : la destination (`%s`) n'est pas la "
                "source (`%s`)"
                % (destination(candidat.zone, candidat.nom), _lisible(source)),
                CONTRAT + " §7.3",
                "compléter la note là où elle est, sans la déplacer")
    if contexte.coffre is None:
        return Refus(
            "mémoire gelée",
            "le coffre n'est pas déclaré : le §6 ne peut pas être lu",
            CONTRAT + " §6",
            "déclarer la racine du coffre, sans quoi un chantier clos ne peut pas "
            "être distingué d'un chantier vivant")
    if CONVENTION.est_gele(Path(contexte.coffre) / source,
                           Path(contexte.coffre), set(contexte.agents)):
        return Refus(
            "mémoire gelée",
            "%s tombe dans un chantier clos de %s/"
            % (_lisible(source), CONVENTION.MEMOIRES),
            CONTRAT + " §6",
            "un chantier clos ne s'écrit plus : viser les préférences, ou les "
            "expériences de l'agent qui écrit")
    ouvert, motif = CONVENTION.zone_autorisee(source, contexte.auteur, nature,
                                              note=candidat.texte,
                                              avant=candidat.avant)
    if not ouvert:
        return Refus(
            "zone du contrat",
            "`%s` : %s" % (_lisible(source), motif),
            CONTRAT + " §7.3",
            "écrire d'abord la note dans une zone que la matrice ouvre à cet auteur")
    return None


def _ensemble(valeur) -> set:
    """Une valeur de frontmatter lue comme un **ensemble de chaînes**.

    ``tags`` s'écrit une entrée par ligne, mais la note d'avant peut porter sa
    liste sur une seule ligne, ou un tag isolé : on ramène tout à un ensemble pour
    comparer des tags, pas des formes.
    """
    if isinstance(valeur, (list, tuple, set)):
        return {str(v) for v in valeur}
    return {str(valeur)} if valeur not in (None, "") else set()


def _frontmatter_et_corps(texte: str):
    """Le frontmatter lu, et le corps **à partir de son premier octet**.

    ``extraire_frontmatter`` rend ``(champs, fin)`` : ``fin`` est l'indice où le
    corps commence, frontmatter absent ou non. On s'en sert tel quel, sans replier
    le texte : la comparaison « compléter » se fait à l'octet.
    """
    champs, fin = CONVENTION.extraire_frontmatter(texte)
    return champs, texte[fin:]


def _refus_sujet_du_geste(candidat: Candidat, contexte: Contexte):
    """Compléter a-t-il **ajouté** à la note, sans en changer le sens ? (§7.3)

    La règle est mécanique, jamais une lecture du sens : on compare des octets.
    Le corps nouveau **commence par** le corps ancien — on n'ajoute qu'à la fin —
    et le frontmatter ne perd ni ne modifie aucune clé : il en gagne, et ``tags``
    ne fait que croître. Sans le texte déjà écrit de la note, la règle ne se mesure
    pas, et la porte refuse (échec fermé) plutôt que de croire sur parole.

    Deux natures visent une note **présente** : ``compléter`` et ``corriger``. Le
    texte d'avant est exigé des deux — c'est sur lui que se lit la garde du champ
    ``auteur:`` d'une note de référence (§7.3). Les règles de l'ajout, en revanche,
    ne valent que pour ``compléter`` : ``corriger`` remplace le texte, il ne
    l'allonge pas.

    « Pas donné » se dit ``avant=None`` — jamais ``avant=""``. Une note dont le texte
    est **vide** a bien un texte d'avant : ``""``, que la règle mesure (un corps vide
    est le préfixe de tout corps). C'est ce qui permet d'**achever** un aperçu vide
    laissé en début de journée, sans faire passer un acte qui n'apporte rien pour un
    acte qui complète.
    """
    if (not candidat.source
            or (contexte.nature or CONVENTION.NATURE_CREER)
            not in (CONVENTION.NATURE_COMPLETER, CONVENTION.NATURE_CORRIGER)):
        return None
    if candidat.avant is None:
        # Les deux gestes qui visent une note **présente** — `compléter` et
        # `corriger` — la jugent sur le texte qu'elle porte déjà : sans lui, la
        # garde du champ `auteur:` (§7.3) n'aurait rien à lire.
        nature = contexte.nature or CONVENTION.NATURE_CREER
        if nature == CONVENTION.NATURE_COMPLETER:
            return Refus(
                "compléter juge la note présente",
                "le texte déjà écrit de la note n'est pas donné : la complétion ne se "
                "mesure pas",
                CONTRAT + " §7.3",
                "apporter le texte que la note porte déjà, pour que l'ajout se compare")
        return Refus(
            "corriger juge la note présente",
            "le texte déjà écrit de la note n'est pas donné : la correction ne se "
            "mesure pas, et la garde du champ `auteur:` n'aurait rien à lire",
            CONTRAT + " §7.3",
            "apporter le texte que la note porte déjà, pour que l'acte se compare")
    if (contexte.nature or CONVENTION.NATURE_CREER) == CONVENTION.NATURE_CORRIGER:
        # `corriger` remplace le texte au lieu d'y ajouter : les règles de l'ajout
        # — corps allongé, frontmatter qui ne fait que croître — ne le jugent pas,
        # sinon aucune correction ne passerait. Ce qui suit ne vaut que pour
        # `compléter`.
        return None
    champs_avant, corps_avant = _frontmatter_et_corps(candidat.avant)
    champs_apres, corps_apres = _frontmatter_et_corps(candidat.texte)
    if not corps_apres.startswith(corps_avant):
        return Refus(
            "compléter n'ajoute qu'à la fin",
            "le corps de la note est réécrit, au lieu d'être allongé",
            CONTRAT + " §7.3",
            "laisser le corps intact et n'ajouter qu'à sa fin — ou corriger la note "
            "autrement, sans la compléter")
    if not champs_avant:
        return None
    if not champs_apres:
        return Refus(
            "compléter garde le frontmatter",
            "le frontmatter de la note a disparu",
            CONTRAT + " §7.3",
            "garder le frontmatter et l'enrichir, sans le retirer")
    for cle, valeur in champs_avant.items():
        if cle not in champs_apres:
            return Refus(
                "compléter garde le frontmatter",
                "la clé `%s` du frontmatter a disparu" % cle,
                CONTRAT + " §7.3",
                "garder chaque clé du frontmatter et n'en ajouter que d'autres")
        if str(cle).lower() in ("tags", "tag"):
            perdus = _ensemble(valeur) - _ensemble(champs_apres[cle])
            if perdus:
                # §7.5 : un tag peut sortir s'il est **hors** du vocabulaire
                # contrôlé — compléter nettoie alors une note brute. Retirer un tag
                # du vocabulaire, lui, reste refusé : toute autre perte l'est aussi.
                du_vocabulaire = sorted(t for t in perdus if t in contexte.vocabulaire)
                if du_vocabulaire:
                    return Refus(
                        "compléter garde le frontmatter",
                        "la liste `tags` a perdu le tag `%s`, qui est du vocabulaire "
                        ": compléter n'en fait que croître" % du_vocabulaire[0],
                        CONTRAT + " §7.5",
                        "garder chaque tag du vocabulaire et n'en ajouter que "
                        "d'autres ; seul un tag hors vocabulaire peut être retiré "
                        "pour ranger la note")
        elif champs_apres[cle] != valeur:
            return Refus(
                "compléter garde le frontmatter",
                "la clé `%s` du frontmatter a changé" % cle,
                CONTRAT + " §7.3",
                "garder la valeur de chaque clé, et n'ajouter que des clés neuves")
    return None


def _refus_homonyme_du_coffre(nom: str, candidat: Candidat, contexte: Contexte):
    """Un homonyme porte-t-il ce nom **ailleurs dans le coffre** ? (§6)

    L'unicité d'un dépôt vaut sur **tout** le coffre parent, pas seulement sur la
    zone qui le reçoit : la note déplacée, elle, n'est pas un doublon d'elle-même,
    d'où l'exclusion de sa ``source``.
    """
    if (not candidat.source
            or (contexte.nature or CONVENTION.NATURE_CREER) != CONVENTION.NATURE_DEPOSER):
        return None
    cle = CONVENTION.nom_comparable(nom)
    source = candidat.source.strip("/")
    for chemin in sorted(_chemins_du_coffre(contexte)):
        if chemin == source:
            continue
        if CONVENTION.nom_comparable(chemin.rsplit("/", 1)[-1]) == cle:
            return Refus(
                "nom unique dans le coffre",
                "`%s` porte déjà ce nom" % chemin,
                CONTRAT + " §6",
                "renommer la note avant de la ranger : un nom de note est unique "
                "dans tout le coffre parent")
    return None


def _refus_dossier_jumeau(zone: str, contexte: Contexte):
    """Le dossier visé a-t-il un **jumeau** sous son parent ? (§6, §7.4)

    L'aperçu du jour replie le dossier d'origine en tige : ``Réseau`` et ``reseau``
    y tombent sur le **même** nom, et deux notes de deux dossiers se disputeraient
    l'aperçu. On refuse donc de semer un second dossier quand un voisin se replie
    au même nom — la règle qu'``ecrivain`` tient déjà pour les dossiers de projet et
    de chantier, portée ici sur le dossier d'une note.

    Sans coffre déclaré, il n'y a pas d'arbre : rien à comparer, rien à confondre.
    Le contrôle laisse donc passer — à la différence de la mémoire gelée, qui, elle,
    ferme quand elle ne peut pas lire.
    """
    if not contexte.coffre:
        return None
    parent, _, dossier = zone.strip("/").rpartition("/")
    if not parent or not dossier:
        return None
    racine = Path(contexte.coffre) / parent
    if not racine.is_dir():
        return None
    cle = CONVENTION.nom_comparable(dossier)
    for entree in sorted(racine.iterdir()):
        if (entree.is_dir() and entree.name != dossier
                and CONVENTION.nom_comparable(entree.name) == cle):
            return Refus(
                "dossier jumeau",
                "`%s/%s/` se replie au même nom que le dossier `%s`"
                % (parent, entree.name, dossier),
                CONTRAT + " §6",
                "ranger sous `%s/` plutôt que d'en semer un second, qui "
                "partagerait l'aperçu du jour" % (parent + "/" + entree.name))
    return None


def juger(candidat: Candidat, contexte: Contexte) -> Verdict:
    """Juge un candidat sans rien écrire, et rend un verdict guidé.

    L'ordre des contrôles va du plus grossier au plus fin : un chemin glissé dans
    la matière du nom se voit avant qu'on cherche un nom, une zone inconnue avant
    qu'on interroge son contenu. L'ordre dit aussi **ce que le refus doit dire**
    quand deux portes se ferment : le secret passe avant la forme, parce qu'un
    refus de mise en forme devant une clé privée corrige la mise en forme et
    laisse la clé.

    Le nom vient du sujet — sauf quand le candidat apporte un nom **déjà calculé**
    (§6 : le carnet, dont le dossier garde son orthographe ; §7.4 : son aperçu),
    ou quand l'acte part d'une note **déjà présente** (``source`` : le nom est
    celui du fichier). Dans les deux cas il n'est pas pris sur parole : la porte le
    **recalcule** — depuis la zone et le sujet brut, ou depuis le chemin source —
    et refuse tout nom qui diffère. Replier un nom, ou en forger un, écrirait sinon
    sous un nom que la vérification du coffre ne reconnaîtrait pas. Le plafond
    d'octets se mesure alors sur le nom **réel**, celui qui s'écrirait.
    """
    if candidat.source:
        refus = _refus_de_la_source(candidat, contexte)
        if refus is not None:
            return Verdict(None, refus)
    elif candidat.nom:
        refus = _refus_nom_fourni(candidat)
        if refus is not None:
            return Verdict(None, refus)
    else:
        refus = _refus_chemin(candidat.sujet)
        if refus is not None:
            return Verdict(None, refus)

    for refus in (_refus_zone(candidat.zone, contexte),
                  _refus_sujet(candidat.sujet),
                  _refus_imbrique(candidat.zone)):
        if refus is not None:
            return Verdict(None, refus)

    nom = candidat.nom or nom_de_note(candidat.sujet)
    for refus in (_refus_longueur(nom),
                  _refus_gele(candidat.zone, nom, contexte),
                  _refus_matrice(candidat.zone, nom, candidat, contexte),
                  _refus_reserve(nom),
                  _refus_unique(nom, candidat, contexte),
                  _refus_dossier_jumeau(candidat.zone, contexte),
                  _refus_homonyme_du_coffre(nom, candidat, contexte),
                  _refus_sujet_du_geste(candidat, contexte),
                  # Le secret passe **juste avant** la forme. Une note qui recopie
                  # une clé privée dans un corps qui s'ouvre par `---` ferme deux
                  # portes à la fois ; c'est le secret qui doit répondre. Un
                  # « second bloc de frontmatter s'ouvre dans le corps » envoie
                  # réécrire des tirets : on repasse, et la clé reste.
                  _refus_secret(candidat.texte),
                  _refus_frontmatter(candidat.texte),
                  _refus_liste_en_ligne(candidat.texte),
                  _refus_tags(candidat.texte, contexte)):
        if refus is not None:
            return Verdict(None, refus)

    return Verdict(destination(candidat.zone, nom), None)
