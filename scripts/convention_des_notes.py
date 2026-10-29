#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""La convention des notes du coffre parent, en un seul exemplaire.

Ces règles vivaient en double, et les copies avaient divergé :

- ``IA/skills/traitement-des-notes/scripts/appliquer_convention_parent.py``
  — qui pose ``type`` et ``tags`` sur les notes ;
- ``IA/skills/traitement-des-notes/scripts/indexer_coffre_parent.py``
  — qui écrit les index de ``_MAINTENANCE/`` ;
- ``scripts/regenerate_sommaire.py`` — qui résume un dossier.

Elles vivent ici **une fois**, et les trois appelants les importent. Le
``VAULT-CONTRACT.md`` et le registre des tags restent la source qui fait foi ;
ce module n'est que son exécution en Python.

**Ce qu'elle coûte.** Les appelants doivent avoir localisé le dépôt OBSIA : le
dossier du skill ``traitement-des-notes`` n'est plus autonome, il importe
``scripts/convention_des_notes.py``. L'applicateur et l'indexeur remontent depuis
leur propre chemin pour trouver la racine (et s'arrêtent net si elle manque),
puis ajoutent ``scripts/`` à ``sys.path`` ; ``regenerate_sommaire.py`` y vit
déjà. C'est le prix assumé de la copie unique.

Ce qui est ramassé ici, et ce qui a survécu :

- ``extraire_frontmatter`` : la lecture qui rend la position du corps — celle de
  l'applicateur — survit. La seconde, qui renvoyait un ``dict`` sans position,
  s'y range ; son nettoyage des guillemets de liste est repris au passage (il
  manquait à la première).
- ``est_depot_imbrique``, ``DOSSIERS_HORS_MEMOIRE``, ``dossier_hors_memoire`` :
  la frontière de mémoire. Un dépôt imbriqué n'est jamais parcouru, quel que
  soit son nom ; ``code/`` et ``node_modules/`` sont le filet sous cette règle.
- ``notes_du_dossier`` : un seul parcours des notes d'un dossier. La sélection
  reste à l'appelant (``retenir``) ; l'ordre est garanti par le parcours. Les
  deux appelants cherchent désormais la même chose — des notes (``est_note``) —
  et l'indexeur n'écarte en plus que ses propres index.
- ``est_gele``, ``point_de_depart_ecarte``, ``liste_des_agents`` : la moitié
  vivante de ``0-MEMOIRES/`` contrastée au chantier clos (§6), et le refus de
  viser un sous-dossier hors mémoire. La porte les appelle pour son contrôle de
  mémoire gelée. Elles ne pouvaient plus vivre dans le dossier du skill sans que
  le produit l'importe à l'envers.
- ``lire_registre``, ``vocabulaire_des_tags``, ``tags_inline`` : le vocabulaire
  contrôlé des tags et la lecture des ``#tag`` du corps. ``vocabulaire_des_tags``
  lit le **texte** du registre (fonction pure) ; ``lire_registre`` n'en est que
  le lecteur de fichier.

Bibliothèque standard uniquement ; outil de la machine, pas de CI.
"""

import os
import re
import sys
import unicodedata
from collections import namedtuple
from pathlib import Path

sys.dont_write_bytecode = True

#: Dossiers jamais parcourus par leur nom, en plus de ceux qui commencent par
#: ``.`` : ``node_modules/`` (cache d'outil) et ``code/``, le dépôt Git d'un
#: projet. C'est le filet : la règle de fond est le ``.git``, qui attrape tout
#: dépôt imbriqué quel que soit son nom.
DOSSIERS_HORS_MEMOIRE = frozenset(("node_modules", "code"))

#: Fichiers de dossier, jamais des notes : l'installeur les pose.
FICHIERS_DE_DOSSIER = frozenset(("sommaire.md", "readme.md"))

#: Le registre des tags, seule source du vocabulaire contrôlé du coffre.
REGISTRE_REL = Path("IA") / "system" / "tags-du-coffre-parent.md"

#: La section du registre dont la table fait foi pour les tags. La section des
#: « candidats » ne fait pas foi : ces mots ne sont pas encore validés.
SECTION_VOCABULAIRE = "## Vocabulaire"

#: Forme d'un tag : une lettre (minuscule ou accentuée), puis lettres, chiffres,
#: ``_`` et ``-``. Sert à la fois au registre et aux ``#tag`` du corps.
TAG = re.compile(r"^[a-zà-ÿ][\wà-ÿ-]*$", re.UNICODE)

#: La moitié vivante de ``0-MEMOIRES/`` (§6) : tout le reste y est gelé.
MEMOIRES = "0-MEMOIRES"
PREFERENCES = "préférences"
EXPERIENCES = "expériences"

#: La zone de passage du coffre : previews, actions et registre (§7.3, §7.4).
MAINTENANCE = "_MAINTENANCE"
#: Le vrac : la seule source d'un **classement** (§7.3, §7.7).
VRAC = "0-EN-VRAC"


def est_depot_imbrique(dossier) -> bool:
    """Vrai si ``dossier`` est une racine de dépôt Git (``dossier`` ou fichier ``.git``).

    Le fichier ``.git`` compte : un sous-module ou un arbre de travail le porte à
    la place d'un dossier. On teste l'existence, jamais le type.
    """
    return (Path(dossier) / ".git").exists()


def partie_hors_memoire(partie: str) -> bool:
    """Vrai si cette **part** de chemin met hors mémoire (§7.3).

    Un dossier caché (``.git``, ``.obsidian``), ou un dossier technique
    (``code/``, ``node_modules/``). C'est la seule définition de la règle : la
    carte légale s'en sert pour écarter une zone, l'applicateur pour refuser un
    point de départ, la porte pour refuser un chemin en direct. Deux copies
    finiraient par diverger.
    """
    return partie.startswith(".") or partie in DOSSIERS_HORS_MEMOIRE


def dossier_hors_memoire(dossier) -> bool:
    """Vrai si l'on ne doit ni parcourir ``dossier``, ni descendre dedans.

    Un dossier technique (``code/``, ``node_modules/``), ou tout dossier portant
    un ``.git`` quel que soit son nom : la connaissance d'un autre dépôt n'est
    pas la mémoire du coffre (§7.3).

    Ne s'applique qu'aux dossiers **rencontrés sous** le point de départ : la
    racine du parcours n'est jamais filtrée, sans quoi le coffre — qui est
    lui-même un dépôt — ne serait jamais parcouru.
    """
    chemin = Path(dossier)
    return chemin.name in DOSSIERS_HORS_MEMOIRE or est_depot_imbrique(chemin)


def est_fichier_de_dossier(nom: str) -> bool:
    """Vrai si ``nom`` est un fichier de dossier (``sommaire.md``, ``README.md``)."""
    return nom.lower() in FICHIERS_DE_DOSSIER


def est_note(nom: str) -> bool:
    """Un ``.md`` qui n'est pas un fichier de dossier — la convention par défaut."""
    return nom.lower().endswith(".md") and not est_fichier_de_dossier(nom)


def _fin_du_frontmatter(texte: str) -> int:
    """Index de la première ligne après le bloc, ou ``-1`` s'il n'y en a pas.

    Une seule copie de la règle de délimitation : ``frontmatter_brut`` et
    ``extraire_frontmatter`` la partagent, sans quoi l'un verrait un bloc là où
    l'autre n'en voit pas.
    """
    if not texte.startswith("---"):
        return -1
    return texte.find("\n---", 3)


def frontmatter_brut(texte: str):
    """Le texte du bloc de frontmatter, sans ses ``---``, ou ``None``.

    ``None`` couvre les deux cas : pas de frontmatter, ou bloc jamais refermé.
    """
    fin = _fin_du_frontmatter(texte)
    return None if fin == -1 else texte[3:fin]


def cles_repetees(texte: str) -> list:
    """Clés de frontmatter écrites plusieurs fois, dans l'ordre rencontré (§5).

    ``extraire_frontmatter`` garde la dernière valeur sans le dire ; cette
    fonction le dit, pour que la porte d'entrée refuse une note qui répète un
    champ au lieu de laisser la dernière valeur gagner en silence.
    """
    bloc = frontmatter_brut(texte)
    if bloc is None:
        return []
    vues: set = set()
    repetees: list = []
    for ligne in bloc.splitlines():
        nu = ligne.strip()
        if not nu or nu.startswith("#") or nu.startswith("- ") or ":" not in nu:
            continue
        cle = nu.split(":", 1)[0].strip()
        if cle in vues and cle not in repetees:
            repetees.append(cle)
        vues.add(cle)
    return repetees


def listes_en_ligne(texte: str) -> list:
    """Clés de frontmatter dont la valeur est une liste écrite **sur une ligne** (§5).

    Le contrat veut une entrée par ligne : ``tags: [docker, réseau]`` est refusé,
    ``tags:`` suivi d'une puce ``- docker`` est la forme attendue. Sans ce
    contrôle, la valeur serait lue comme le scalaire ``[docker, réseau]`` — un
    « tag » que le vocabulaire ne connaît pas — et le refus parlerait des tags au
    lieu de la forme de la liste.
    """
    bloc = frontmatter_brut(texte)
    if bloc is None:
        return []
    trouvees: list = []
    for ligne in bloc.splitlines():
        nu = ligne.strip()
        if not nu or nu.startswith(("#", "-")) or ":" not in nu:
            continue
        cle, _, valeur = nu.partition(":")
        if valeur.strip().startswith("["):
            trouvees.append(cle.strip())
    return trouvees


def extraire_frontmatter(texte: str) -> tuple:
    """Frontmatter YAML minimal (scalaires et listes à tirets).

    Renvoie ``(dict, fin)`` où ``fin`` est l'index de la première ligne après le
    bloc, ou ``(None, 0)`` si le fichier ne commence pas par un frontmatter.

    Les scalaires reçoivent leur type : ``true``/``false`` deviennent des
    booléens, un entier reste un entier. Les guillemets qui entourent une valeur
    ou une puce de liste sont retirés.
    """
    fin = _fin_du_frontmatter(texte)
    if fin == -1:
        return None, 0
    donnees: dict = {}
    cle_liste = None
    for ligne in texte[3:fin].splitlines():
        nu = ligne.strip()
        if not nu or nu.startswith("#"):
            continue
        if nu.startswith("- ") and cle_liste:
            donnees[cle_liste].append(nu[2:].strip().strip("'\""))
            continue
        if ":" not in nu:
            continue
        cle, _, valeur = nu.partition(":")
        cle = cle.strip()
        valeur = valeur.strip()
        if not valeur:
            donnees[cle] = []
            cle_liste = cle
            continue
        cle_liste = None
        if valeur.lower() in ("true", "false"):
            donnees[cle] = valeur.lower() == "true"
        elif valeur.isdigit():
            donnees[cle] = int(valeur)
        else:
            donnees[cle] = valeur.strip("\"'")
    # `fin` pointe sur le « --- » de clôture : passer après cette ligne.
    retour = texte.find("\n", fin + 1)
    return donnees, (retour + 1 if retour != -1 else len(texte))


def corps(texte: str) -> str:
    """Le texte situé après le frontmatter, s'il y en a un."""
    return texte[extraire_frontmatter(texte)[1]:]


def notes_du_dossier(dossier, *, retenir=None) -> list:
    """Notes ``.md`` sous ``dossier``, en profondeur mais hors dossiers techniques.

    L'élagage se fait **avant** de descendre :

    - tout composant commençant par un point, un ``node_modules/`` ou un ``code/`` ;
    - **tout dossier contenant un ``.git``**, c'est-à-dire un dépôt imbriqué,
      quel que soit son nom.

    Le ``dossier`` de départ n'est pas filtré : le coffre peut être lui-même un
    dépôt, seule la descente s'arrête aux dépôts *imbriqués*. ``os.walk`` ne suit
    pas les liens symboliques, aucune boucle n'est possible.

    ``retenir`` resserre la sélection des fichiers ; par défaut, la convention
    (``est_note``, donc les fichiers de dossier sont écartés). Le résultat est
    trié par chemin relatif, du plus court au plus long, pour que deux
    exécutions sur le même dossier rendent la même liste.
    """
    if retenir is None:
        retenir = est_note
    notes: list = []
    for racine, dossiers, fichiers in os.walk(dossier):
        dossiers[:] = [d for d in dossiers
                       if not d.startswith(".")
                       and d not in DOSSIERS_HORS_MEMOIRE
                       and not est_depot_imbrique(Path(racine) / d)]
        for nom in fichiers:
            if retenir(nom):
                notes.append(Path(racine) / nom)
    return sorted(notes, key=lambda p: Path(p).relative_to(dossier).as_posix())


# --------------------------------------------------------------- la mémoire
# `0-MEMOIRES/` porte deux mémoires, et une seule est gelée (§6). Ces règles
# vivent ici pour la **tranche qui écrit** : la carte s'en sert pour écarter un
# chantier clos, et la porte la relit dans le contrôle « mémoire gelée » (P3).
# Un seul exemplaire, appelé des deux côtés.

def liste_des_agents(racine_depot) -> set:
    """Noms des agents, lus dans ``IA/agents/`` — la mémoire vivante d'un agent.

    ``0-MEMOIRES/<nom>/expériences/`` n'est vivant que si ``<nom>`` est un agent :
    sans cette liste, un dossier ``expériences/`` sous un projet passerait pour de
    la mémoire vivante, et la note serait écrite dans un chantier clos (§6). Un
    dossier ``IA/agents/`` absent rend l'ensemble vide : rien n'est vivant, et qui
    refuse d'écrire plutôt que de se tromper a raison.

    « Qui est un agent » n'a **qu'une** définition : ``fichiers_declaratifs``, qui
    voit les deux formes de déclaration (§5) — ``IA/agents/<nom>.md`` et
    ``IA/agents/<nom>/<nom>.md``. S'en tenir aux seuls fichiers plats ferait
    passer le ``expériences/`` d'un agent déclaré en dossier pour un chantier clos.
    """
    from generer_prompt import fichiers_declaratifs      # tardif : une seule règle
    try:
        dossier = Path(racine_depot) / "IA" / "agents"
        return {p.stem for p in fichiers_declaratifs(dossier)}
    except OSError:
        return set()


def est_gele(chemin, coffre, agents: set) -> bool:
    """Vrai si ``chemin`` tombe dans un chantier gelé de ``0-MEMOIRES/``.

    ``0-MEMOIRES/`` porte deux mémoires, et une seule est gelée (§6) : les
    préférences et les expériences **d'un agent** se corrigent sur place, un
    chantier clos jamais. On le constate par le chemin, sans lire la note : sous
    ``0-MEMOIRES/``, seuls ``préférences/`` et ``<agent>/expériences/`` sont
    vivants, ``<agent>`` devant figurer dans ``agents`` (les fichiers de
    ``IA/agents/``). Tout ce qui est plus profond est un chantier — donc gelé, y
    compris ce qui ne devrait pas exister (mieux vaut refuser d'écrire que de se
    tromper).
    """
    try:
        parts = Path(chemin).resolve().relative_to(Path(coffre).resolve()).parts
    except ValueError:
        return False                      # hors du coffre : rien à geler
    if not parts or parts[0] != MEMOIRES:
        return False                      # pas la mémoire des chantiers
    if len(parts) == 1 or len(parts) == 2:
        return False                      # `0-MEMOIRES/`, `0-MEMOIRES/<projet>/`
    if parts[1] == PREFERENCES:
        return False                      # `0-MEMOIRES/préférences/…` : vivant
    if parts[1] in agents and parts[2] == EXPERIENCES:
        return False                      # `0-MEMOIRES/<agent>/expériences/…` : vivant
    return True                           # tout le reste : chantier gelé


def point_de_depart_ecarte(dossier, coffre) -> bool:
    """Le point de départ est-il hors mémoire (dépôt imbriqué, ``code/``, ``.``…) ?

    La racine du coffre est dispensée : le coffre est lui-même un dépôt Git, et
    le ``--dossier=.`` doit rester possible. Mais viser un sous-dossier que
    ``notes_du_dossier`` n'aurait jamais atteint — ``<projet>/code/``, un dossier
    sous un ``.git`` — ouvrirait un dépôt à un frontmatter : on refuse.
    """
    try:
        parts = Path(dossier).resolve().relative_to(Path(coffre).resolve()).parts
    except ValueError:
        return False                      # hors du coffre : cas « introuvable »
    courant = Path(coffre).resolve()
    for partie in parts:
        if partie_hors_memoire(partie):
            return True
        courant = courant / partie
        if est_depot_imbrique(courant):
            return True
    return False


# -------------------------------------------------------- la matrice du §7.3
# Le §7.3 ouvre l'écriture **directe** sur une poignée de zones, et la referme
# partout ailleurs. Cette matrice (zone × auteur × nature) en est l'unique
# exemplaire : la carte, la porte et leurs tests la lisent ici, personne ne la
# réécrit. Les noms sont ceux du **contrat** (§7.1/§7.3), pas d'un coffre
# particulier — un « 0-EN-VRAC » reste un « 0-EN-VRAC » d'un coffre à l'autre.

AUTEUR_UTILISATEUR = "utilisateur"      # le propriétaire du coffre
AUTEUR_VISIONNAIRE = "visionnaire"      # le seul à écrire une note « — vision »
AUTEUR_TOUS = "*"                       # l'utilisateur, ou n'importe quel agent
#: Marqueur : l'auteur ouvert n'est autre que le nom d'agent porté par le chemin
#: (`0-MEMOIRES/<agent>/expériences/`), résolu par `zone_autorisee`.
AUTEUR_PROPRE = "<agent du chemin>"
#: Marqueur : l'auteur ouvert est l'agent que le champ ``auteur:`` de la note
#: nomme (`0-PERSONNELS/<note de référence>`). La matrice ne lit pas le
#: frontmatter : c'est `zone_autorisee` qui reçoit le texte — l'existant comme le
#: proposé — et y résout ce nom.
AUTEUR_DE_LA_NOTE = "<auteur de la note>"

NATURE_CREER = "créer"          # poser une note neuve
NATURE_COMPLETER = "compléter"  # remplir une note déposée, sans en changer le sens
NATURE_DEPOSER = "déposer"      # ranger une note déjà classée venue d'0-EN-VRAC/
NATURE_CORRIGER = "corriger"    # corriger une note tenue sur place

#: Un cran de la matrice : qui écrit, de quelle nature, et le mot pour le dire.
Regle = namedtuple("Regle", "auteurs natures libelle")

_TOUS = frozenset((AUTEUR_TOUS,))
_VISIONNAIRE = frozenset((AUTEUR_VISIONNAIRE,))
_PROPRE_AGENT = frozenset((AUTEUR_PROPRE,))
#: Ranger une note déjà classée, venue d'`0-EN-VRAC/`.
_DEPOSER = frozenset((NATURE_DEPOSER,))
#: Remplir une note déposée, sans en changer le sens ni la déplacer.
_COMPLETER = frozenset((NATURE_COMPLETER, NATURE_CORRIGER))
#: Les savoirs : on y complète une note déposée, et le **classement** d'une note
#: venue d'`0-EN-VRAC/` peut y déposer — jamais y créer une note neuve (§7.3).
_SAVOIRS = _COMPLETER | _DEPOSER
#: Une note qu'un agent tient sur place : il la pose, la remplit, la corrige.
_TENUE_SUR_PLACE = frozenset((NATURE_CREER, NATURE_COMPLETER, NATURE_CORRIGER))
#: L'`0-EN-VRAC/` : remplir, tagger, relier, et préparer le classement.
_VRAC = frozenset((NATURE_COMPLETER, NATURE_CORRIGER, NATURE_DEPOSER))

#: Les têtes de zone du §7.1 que la matrice reconnaît. Le reste est refusé.
ZONES_DU_CONTRAT = frozenset(("0-EN-VRAC", "0-SAVOIRS", "0-DOCUMENTS",
                              "0-PERSONNELS", "0-PROJETS", MEMOIRES,
                              MAINTENANCE))

#: La matrice du §7.3, tête par tête : ce que le contrat ouvre à qui, et de
#: quelle nature. Les têtes à sous-règles (`0-PROJETS/`, `0-PERSONNELS/`,
#: `0-MEMOIRES/`, `0-SAVOIRS/`) lisent d'abord cette table, puis `regle_de_zone`
#: en résout le cas fin — un carnet, une `— vision`, un `profil-utilisateur`.
#: `0-MEMOIRES/` n'y figure pas : seule sa moitié vivante est ouverte, résolue
#: plus bas.
MATRICE_MEMOIRE = {
    "0-EN-VRAC": Regle(_TOUS, _VRAC, "le vrac"),
    "0-SAVOIRS": Regle(_TOUS, _SAVOIRS, "les savoirs"),
    "0-DOCUMENTS": Regle(_TOUS, _DEPOSER, "les documents"),
    # `0-PERSONNELS/` porte aussi la **note de référence d'un agent**, tenue sur
    # place (§7.3) : `regle_de_zone` la distingue par la profondeur et rend une règle
    # à part, dont l'auteur se lit dans le champ `auteur:` — la matrice ne lit pas le
    # frontmatter, mais `zone_autorisee` reçoit le texte et le résout. La tête seule
    # s'en tient au **dépôt** d'une note classée, ouvert à tous.
    "0-PERSONNELS": Regle(_TOUS, _DEPOSER, "les personnels"),
    # Les `carnets/` et la note ` — résumé` d'un projet sont ouverts à **tout
    # agent**, comme la **tête** `0-PERSONNELS/` : le chemin ne nomme pas de
    # propriétaire, et la matrice ne lit pas le champ `auteur:` — faute de quoi il
    # faudrait le lire.
    "0-PROJETS": Regle(_TOUS, _DEPOSER, "un projet"),
    # `_MAINTENANCE/` : previews, actions et registre `notes_remplies.md` — la
    # zone de passage du §7.4, que la matrice doit ouvrir (§7.3).
    MAINTENANCE: Regle(_TOUS, _TENUE_SUR_PLACE, "la maintenance du coffre"),
}


def _segments(chemin) -> tuple:
    """Les segments d'un chemin de note, débarrassés du bruit (``.``, ``#…``)."""
    brut = str(chemin).split("#", 1)[0].strip().strip("/")
    return tuple(p for p in brut.split("/") if p not in ("", "."))


def _note_de_dossier(projet: str, genre: str):
    """Les deux écritures de la note de dossier d'un projet.

    Le coffre écrit ``<projet> — vision.md`` ; une porte qui dérive le nom d'un
    sujet écrit ``<projet>-vision.md``. Les deux désignent la même note ; aucune
    autre note ne porte ce nom, le projet le préfixe.
    """
    return ("%s — %s.md" % (projet, genre), "%s-%s.md" % (projet, genre))


def tige_de_nom(texte: str) -> str:
    """La tige d'un nom : minuscules, sans accent, ponctuation repliée en tirets.

    C'est **la** façon dont le coffre replie un mot en nom de fichier — ``Modèles
    locaux`` y vit sous ``modeles-locaux``, ``créée`` sous ``creee``. La
    comparaison d'identité (:func:`nom_comparable`) et le nommage d'un carnet
    (:func:`nom_de_carnet`) s'en servent tous les deux : une seconde règle,
    divergente, rouvrirait la porte au doublon.
    """
    decompose = unicodedata.normalize("NFKD", str(texte))
    sans_accent = "".join(c for c in decompose if not unicodedata.combining(c))
    return re.sub(r"[^0-9a-z]+", "-", sans_accent.lower()).strip("-")


def nom_comparable(nom: str) -> str:
    """Un nom de note réduit à sa forme comparable — la clé d'identité d'une note.

    Le §7.3 juge des **noms réels** : un dossier ``Homelab`` et une porte qui en
    dérive ``homelab`` désignent le même projet. Une capitale, une espace, un
    accent, un tiret ne doivent donc pas suffire à sortir une note de sa règle —
    sinon la vision échapperait au visionnaire, ou lui serait refusée.

    C'est **la** clé de comparaison de tout ce qui nomme une note : la matrice s'en
    sert pour reconnaître un `` — vision`` ou un `` — résumé``, et la porte pour
    juger l'unicité (``Homelab — vision.md`` et ``homelab-vision.md`` sont la même
    note). Deux clés différentes rouvriraient la porte au doublon.
    """
    tige = str(nom)
    if tige.lower().endswith(".md"):
        tige = tige[:-3]
    return tige_de_nom(tige)


def _est_note_de_dossier(nom: str, projet: str, genre: str) -> bool:
    """``nom`` est-il celui de la note ``genre`` du projet ``projet`` ?

    La comparaison passe par la forme comparable : ``Homelab — vision.md`` et
    ``homelab-vision.md`` rendent la **même** règle, une seule fois — sans quoi
    la même note aurait deux règles, et un doublon pourrait passer entre elles.
    """
    voulus = {nom_comparable(e) for e in _note_de_dossier(projet, genre)}
    return nom_comparable(nom) in voulus


# ------------------------------------------------------- le nom d'un carnet
# Le §6 fixe la forme d'un carnet, et cette forme n'a qu'**un** exemplaire : la
# tranche qui écrit s'en sert pour nommer, la vérification du coffre pour
# reconnaître. La recopier d'un côté ferait diverger les deux.

#: La forme d'une date d'acte (§6) : ``AAAA-MM-JJ``, et rien d'autre. Le §6 fixe
#: cette forme comme il fixe celle d'un nom de carnet, et elle n'a qu'**un**
#: exemplaire : les trois gestes de l'écrivain s'en servent pour juger la date
#: qu'on leur donne (carnet, rangement, complétion). Ancrée aux deux bouts :
#: ``$`` laisserait passer un saut de ligne final, et une date qui traîne une
#: ligne de trop n'est pas une date.
DATE_ISO = re.compile(r"\A\d{4}-\d{2}-\d{2}\Z")

#: Un nom de carnet s'ouvre sur sa date : c'est ce qui le distingue d'une note
#: ordinaire, les carnets étant les seules notes datées (§6).
DATE_D_UN_CARNET = re.compile(r"^\d{4}-\d{2}-\d{2}-")

#: Les trois états d'un carnet (§6). Rien d'autre ne s'écrit dans ``statut:``.
STATUTS_CARNET = ("en cours", "en attente", "clos")
STATUT_EN_COURS = STATUTS_CARNET[0]

#: Ce qui joint, dans le nom d'un aperçu, le dossier d'origine et le nom de la note.
#: Un tiret ne suffirait pas : le repli d'un nom en tige produit des tirets, et
#: ``0-SAVOIRS/reseau-note.md`` se confondrait avec ``0-SAVOIRS/Réseau/note.md``.
#: Deux tirets ne peuvent pas venir d'une tige (:func:`tige_de_nom` ramène toute
#: suite de ponctuation à un seul ``-``) : la jointure se relit sans ambiguïté.
SEPARATEUR_D_APERCU = "--"


def nom_de_carnet(date: str, dossier: str, sujet: str) -> str:
    """Le nom d'un carnet (§6) : ``AAAA-MM-JJ-<dossier>-<sujet>.md``.

    ``dossier`` est le nom du dossier qui porte les ``carnets/`` — le chantier,
    ou le projet pour une séance hors chantier. Il est pris **tel quel** : la
    vérification du coffre compare le nom du carnet au dossier réel, pas au
    sujet, et deux dossiers qui ne diffèrent que par une capitale sont deux
    dossiers. Le **sujet**, lui, se replie en tige (:func:`tige_de_nom`), comme
    tout nom du coffre.
    """
    return "%s-%s-%s.md" % (date, dossier, tige_de_nom(sujet))


def carnet_a_la_forme(nom: str) -> bool:
    """Ce nom a-t-il la forme d'un carnet — une date, puis un dossier, puis un sujet ?"""
    return DATE_D_UN_CARNET.match(str(nom)) is not None


def carnet_du_dossier(nom: str, dossier: str) -> bool:
    """Ce nom de carnet porte-t-il bien le dossier qui le range (§6) ?

    Le dossier est comparé tel quel, une fois la date retirée : ``AA`` et ``Aa``
    sont deux dossiers, et un carnet rangé dans l'un ne vaut pas pour l'autre.
    """
    tige = str(nom)
    return carnet_a_la_forme(tige) and tige.startswith(tige[:11] + dossier + "-")


def nom_de_l_apercu(date: str, nom: str, dossier: str = "") -> str:
    """Le nom de la copie d'aperçu du jour (§7.4) — le dossier d'origine compris.

    L'aperçu du jour s'indexe sur le **nom** de la note, mais deux notes homonymes de
    deux dossiers différents se le disputeraient : le **dossier d'origine** entre donc
    dans le nom, replié en tige. Un **carnet** se reconnaît à deux signes : son nom
    porte une date (§6), et son dossier est un ``carnets/``. Son nom entier — date
    comprise — suit la date de l'acte : la date du carnet n'est **pas** retirée, car
    deux carnets du même sujet ouverts à deux dates (``2026-10-08-obsia-bilan.md`` et
    ``2026-10-09-obsia-bilan.md``) se disputeraient sinon l'aperçu du jour. Son dossier,
    lui, n'est pas répété : son nom le porte déjà. C'est la **seule** forme de l'aperçu
    d'un carnet — la même, qu'on le crée (``écrire_un_carnet``) ou qu'on le complète le
    même jour.

    Le dossier retenu est celui de la **source**, non la zone visée : remplir une note
    du vrac puis la ranger le même jour garde donc le même aperçu — le dossier d'origine
    du rangement est bien le vrac. Mais l'aperçu reste solidaire de ce dossier
    d'origine : une note remplie dans le vrac, rangée dans un savoirs, puis complétée
    là le même jour reçoit **deux** aperçus — le dossier d'origine fait partie du nom.
    Hors de là, une note datée est une note ordinaire, et garde son dossier.

    Le dossier et le nom sont joints par :data:`SEPARATEUR_D_APERCU`, et non par un
    simple tiret : ``0-SAVOIRS/reseau-note.md`` — dossier ``0-SAVOIRS``, puis un nom
    qui porte un tiret — et ``0-SAVOIRS/Réseau/note.md`` — dossier plus profond, puis
    un nom nu — donnaient la même suite ``0-savoirs-reseau-note``, et se disputaient
    un seul aperçu. Le séparateur ``--`` ne peut pas venir d'une tige, qui ramène
    toute suite de ponctuation à un seul ``-`` : le premier ``--`` du nom marque donc
    la jointure, et le couple (dossier, nom) s'y relit sans ambiguïté.

    C'est le **moteur** qui le calcule, non l'écrivain, parce que la porte recalcule ce
    nom pour tout candidat qui en apporte un : la copie et la note restent nouées.
    """
    tige = str(nom)
    if carnet_a_la_forme(tige) and _segments(dossier)[-1:] == ("carnets",):
        return "%s-apercu-%s" % (date, tige)
    replie = tige_de_nom(dossier) if dossier else ""
    return "%s-apercu-%s%s" % (date, replie + SEPARATEUR_D_APERCU if replie else "", tige)


def _regle_du_projet(seg: tuple):
    """Les crans nommés du dossier d'un projet, ou ``None``.

    Le dossier d'un projet porte sa note de suivi, sa ``— vision``, ses
    ``carnets/``, ses ``documents/``, et **un seul niveau** de chantiers — chacun
    avec ses ``carnets/``, ses ``documents/`` et son ``<chantier> — résumé.md``
    (§7.3, annexe du coffre parent).
    """
    projet = seg[1]
    if len(seg) < 3:
        return None
    if seg[2] == "carnets":
        return Regle(_TOUS, _TENUE_SUR_PLACE, "un carnet de projet")
    if seg[2] == "documents":
        return Regle(_TOUS, _DEPOSER, "les documents d'un projet")
    if len(seg) == 3:
        if _est_note_de_dossier(seg[2], projet, "vision"):
            return Regle(_VISIONNAIRE, _TENUE_SUR_PLACE, "une note « — vision »")
        if _est_note_de_dossier(seg[2], projet, "résumé"):
            return Regle(_TOUS, _TENUE_SUR_PLACE, "un résumé de projet")
        return None
    chantier = seg[2]
    if seg[3] == "carnets":
        return Regle(_TOUS, _TENUE_SUR_PLACE, "un carnet de chantier")
    if seg[3] == "documents":
        return Regle(_TOUS, _DEPOSER, "les documents d'un chantier")
    if len(seg) == 4 and _est_note_de_dossier(seg[3], chantier, "résumé"):
        return Regle(_TOUS, _TENUE_SUR_PLACE, "un résumé de chantier")
    return None


def regle_de_zone(chemin):
    """Le cran du §7.3 qui gouverne ``chemin``, ou ``None`` si la zone est close.

    ``chemin`` est une **destination** : une zone, à laquelle peut s'ajouter le
    nom de la note — c'est ce nom qui distingue une ``— vision`` d'un
    ``— résumé``, tous deux posés dans le dossier d'un même projet.
    """
    seg = _segments(chemin)
    if not seg:
        return None
    tete = seg[0]
    if tete == "0-PERSONNELS" and len(seg) >= 2 and seg[1].startswith("profil-utilisateur"):
        return Regle(_TOUS, _COMPLETER, "le profil de l'utilisateur")
    if tete == "0-PERSONNELS" and len(seg) >= 2:
        # La **note de référence** d'un agent : celui que son champ `auteur:` nomme
        # la pose, la remplit, la corrige — sur place, jamais ailleurs. Le **dépôt**
        # d'une note déjà classée y reste ouvert à tous : c'est la **nature** qui
        # sépare les deux, et `zone_autorisee` qui lit le champ, la matrice ne lisant
        # pas le frontmatter.
        return Regle(frozenset((AUTEUR_TOUS, AUTEUR_DE_LA_NOTE)),
                     _TENUE_SUR_PLACE | _DEPOSER,
                     "la note de référence d'un agent")
    if tete == "0-PROJETS":
        if len(seg) < 2:
            return None                      # `0-PROJETS/` seul n'accueille rien
        if seg[1] == "tâches-planifiées":
            # Pas un projet : le registre privé des tâches propres à cette
            # installation (§12 du contrat). Un fichier par tâche, à plat —
            # pas de chantier, pas de `carnets/`.
            if len(seg) == 3 and seg[2].endswith(".md"):
                return Regle(_TOUS, _TENUE_SUR_PLACE, "une tâche planifiée du coffre")
            return None
        regle = _regle_du_projet(seg)
        if regle is not None:
            return regle
        # Tout le reste du dossier d'un projet : une note qui ne porte ni
        # `carnets/`, ni ` — résumé`, ni ` — vision` n'est pas à l'agent — elle
        # ne s'y range que par le dépôt d'une note classée (§7.3).
        return MATRICE_MEMOIRE["0-PROJETS"]
    if tete == MEMOIRES:
        if len(seg) >= 2 and seg[1] == PREFERENCES:
            return Regle(_TOUS, _TENUE_SUR_PLACE, "les préférences")
        if len(seg) >= 3 and seg[2] == EXPERIENCES:
            return Regle(_PROPRE_AGENT, _TENUE_SUR_PLACE, "les expériences d'un agent")
        return None                          # un chantier : gelé (§6)
    return MATRICE_MEMOIRE.get(tete)         # `_MAINTENANCE/`, tout autre : rien


def auteur_du_chemin(chemin, regle=None):
    """Le nom d'agent que le chemin impose de lui-même, ou ``None``.

    Seules ``0-MEMOIRES/<agent>/expériences/`` portent une contrainte *propre* :
    le seul agent qui y écrive est celui dont le dossier porte le nom.
    """
    if regle is None:
        regle = regle_de_zone(chemin)
    if regle is None or AUTEUR_PROPRE not in regle.auteurs:
        return None
    seg = _segments(chemin)
    return seg[1] if len(seg) >= 2 else None


def auteur_de_la_note(texte) -> str:
    """Le nom d'agent que le champ ``auteur:`` d'une note nomme, ou ``""``.

    La **note de référence** de ``0-PERSONNELS/`` ne dit son agent ni par son
    chemin — il ne porte qu'un titre — ni par son auteur d'acte : elle le dit par
    son frontmatter. Un nom manquant ne fait pas retomber la matrice sur un « tout
    est ouvert », il la **ferme** (échec fermé).

    Un champ ``auteur:`` **répété** ferme aussi la note : ``extraire_frontmatter``
    ne garderait que la dernière ligne, sans le dire, et un agent pourrait se
    donner la note d'un autre en laissant sa ligne écraser la sienne — la note
    dirait deux auteurs, donc aucun (échec fermé). C'est la même règle que
    ``cles_repetees``, appliquée ici au seul champ qui décide de l'ouverture.
    """
    if not texte:
        return ""
    if "auteur" in cles_repetees(texte):
        return ""
    champs, _ = extraire_frontmatter(texte)
    return str((champs or {}).get("auteur", "") or "").strip()


#: Le motif **unique** du refus quand l'auteur n'est pas déclaré. La carte et la
#: porte le partagent : écrire sans dire qui écrit n'est pas jugeable au §7.3, et
#: un refus se dit d'une seule façon, où qu'on le lise.
MOTIF_AUTEUR_ABSENT = ("aucun auteur n'est déclaré : le §7.3 ne se lit pas sans "
                       "savoir qui écrit")


def auteur_declare(auteur) -> bool:
    """L'auteur est-il assez nommé pour juger le §7.3 ?

    Ni vide, ni blanc, ni ``None`` : un auteur non déclaré ne fait pas retomber
    la matrice sur un « tout est ouvert » — il la **ferme** (échec fermé).
    """
    return bool(auteur and str(auteur).strip())


def zone_autorisee(chemin, auteur, nature=None, note=None, avant=None):
    """Le §7.3 ouvre-t-il ``auteur`` à écrire dans ``chemin``, de cette ``nature`` ?

    Rend ``(autorisé, motif)``. Le motif explique le refus, jamais le silence :
    un auteur non déclaré, une zone close, un auteur que la règle ne nomme pas,
    une nature qu'elle n'ouvre pas. Un auteur est ``AUTEUR_TOUS`` quand la zone
    est ouverte à n'importe qui — l'utilisateur, comme un agent.

    ``note`` et ``avant`` ne servent qu'à la **note de référence** de
    ``0-PERSONNELS/``, dont l'agent se lit dans le frontmatter, non dans le chemin :
    ``note`` est le texte **proposé**, ``avant`` celui que la note porte **déjà**
    (``None`` quand elle n'existe pas encore — une création). L'agent doit être
    nommé par ``auteur:`` **dans les deux** : la note ne change pas de main, et
    l'on ne s'empare pas de celle d'un autre. Le **dépôt** d'une note classée n'y
    dépend pas de ce champ — c'est la nature, non l'auteur, qui l'ouvre à tous.
    """
    if not auteur_declare(auteur):
        return (False, MOTIF_AUTEUR_ABSENT)
    regle = regle_de_zone(chemin)
    if regle is None:
        seg = _segments(chemin)
        if seg and seg[0] == MEMOIRES:
            return (False, "%s/%s est un chantier gelé : un chantier clos ne "
                           "s'écrit plus (§6)" % (MEMOIRES, seg[1] if len(seg) > 1 else ""))
        return (False, "%s n'est pas une zone que le §7.3 ouvre à l'écriture" % chemin)
    # La note de référence : sur place, c'est le champ `auteur:` qui décide, et le
    # dépôt d'une note classée n'en dépend pas.
    if AUTEUR_DE_LA_NOTE in regle.auteurs and nature in _TENUE_SUR_PLACE:
        if str(auteur) != auteur_de_la_note(note) or (
                avant is not None and str(auteur) != auteur_de_la_note(avant)):
            return (False, "le §7.3 réserve %s à l'agent que son champ `auteur:` "
                           "nomme — dans la note comme dans le texte proposé —, pas "
                           "à « %s »" % (regle.libelle, auteur))
    autorises = set(regle.auteurs)
    autorises.discard(AUTEUR_PROPRE)
    autorises.discard(AUTEUR_DE_LA_NOTE)
    propre = auteur_du_chemin(chemin, regle)
    if propre is not None:
        autorises.add(propre)
    if AUTEUR_TOUS not in autorises and auteur not in autorises:
        return (False, "le §7.3 réserve %s à %s, pas à « %s »" % (
            regle.libelle, " ou ".join(sorted(autorises)), auteur))
    if nature is not None and nature not in regle.natures:
        return (False, "dans %s, le §7.3 n'ouvre que %s — pas « %s »" % (
            regle.libelle, " ou ".join(sorted(regle.natures)), nature))
    return (True, "")


# ----------------------------------------------------- le vocabulaire des tags

def vocabulaire_des_tags(texte: str) -> set:
    """Tags du vocabulaire contrôlé, lus dans le **texte** du registre.

    Même règle que ``lire_registre``, mais sur un texte déjà lu : la porte
    d'entrée juge le registre sans y toucher, et l'applicateur peut offrir un
    vocabulaire de secours. Seule la table de la section « Vocabulaire » fait foi
    (cf. ``lire_registre``).
    """
    connus: set = set()
    dans_section = False
    for ligne in texte.splitlines():
        if ligne.startswith("## "):
            dans_section = ligne.startswith(SECTION_VOCABULAIRE)
            continue
        if not dans_section or not ligne.startswith("| "):
            continue
        for m in re.finditer(r"`([^`]+)`", ligne):
            if TAG.match(m.group(1)):
                connus.add(m.group(1))
    return connus


def lire_registre(racine) -> set:
    """Tags du vocabulaire contrôlé, pris dans le registre versionné.

    Seule la table de la section « Vocabulaire » fait foi. Lire *toutes* les
    lignes de tableau du fichier ramassait aussi la table « Type d'une note » :
    ``concept``, ``revue``, ``projet`` et ``note`` passaient alors pour des tags,
    et une note taguée ``#projet`` était déclarée conforme. La section des
    **candidats** est écartée pour la raison inverse : ces mots ne sont pas encore
    validés.
    """
    try:
        texte = (Path(racine) / REGISTRE_REL).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return set()
    return vocabulaire_des_tags(texte)


def tags_inline(texte: str) -> list:
    """Tags ``#tag`` du corps, hors blocs de code, titres et cibles de lien.

    Un tag n'est reconnu que précédé d'une **espace** (comme le veut Obsidian) :
    le ``#`` d'une ancre de lien (``[Sources](#sources)``) suit une parenthèse,
    celui d'un fragment d'URL (``…/page#section``) suit un mot — ni l'un ni
    l'autre n'est un tag. Un ``#`` en début de ligne n'en est pas un non plus :
    c'est un titre, écarté juste en dessous (la branche « début de ligne » d'un
    ancien motif était donc morte ; elle a été retirée, b1 de la relecture).

    Conséquence assumée : un tag collé à une ponctuation — ``(#docker)``,
    ``a,#docker`` — n'est plus vu (b2 de la relecture). Obsidian non plus ne le
    reconnaît pas ; ces formes se réécrivent avec une espace devant ``#``.
    """
    hors_blocs = re.sub(r"```.*?```", "", texte, flags=re.S)
    trouves: list = []
    for ligne in hors_blocs.splitlines():
        if ligne.lstrip().startswith("#"):
            continue                       # titre Markdown, pas un tag
        for m in re.finditer(r"(?<=\s)#([^\s#]+)", ligne):
            tag = m.group(1).rstrip(".,;:!?)('\"").lstrip("(['\"")
            if TAG.match(tag) and tag not in trouves:
                trouves.append(tag)
    return trouves
