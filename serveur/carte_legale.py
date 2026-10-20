#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""La carte légale : **la carte des destinations**, pas la carte de ce qu'on peut
lire (P2).

La carte est en **lecture seule**, et elle ne dit **qu'une chose : les
destinations où le modèle peut écrire**. Elle ne dit jamais ce que le modèle a le
droit de lire — la lecture du coffre reste ouverte (§7.2) ; elle sert seulement à
écrire sans se tromper.

Les zones lui viennent de l'appelant, **jamais du modèle** : elle rend **les
zones données par l'appelant, moins les exclusions structurelles**, puis les
confronte au §7.3 (la matrice zone × auteur × nature d'écriture). Trois familles
sont écartées :

- une zone sous un dépôt imbriqué (`code/`, un dossier caché, un dépôt Git) ;
- une zone **absolue** : un chemin absolu sortirait du coffre, les zones sont
  relatives (§13) ;
- une zone qui tombe dans un **chantier gelé** de la mémoire du coffre : on ne
  rouvre pas un chantier clos (§6).

Elle juge la **forme** d'une zone, puis son **appartenance à la matrice** : une
zone que le contrat n'ouvre pas à cet auteur est refusée, même fournie par
l'appelant. Elle ne devine jamais l'auteur : sans auteur déclaré, elle n'ouvre
**rien** — un silence ne vaut pas permission (§7.3). La matrice elle-même vit
dans le moteur partagé (`scripts/convention_des_notes.py`), un seul exemplaire
pour les deux.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True
_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import convention_des_notes as CONVENTION   # noqa: E402

#: Le dépôt produit, qui déclare ses agents : c'est **lui** qui dit quel nom de
#: la mémoire du coffre est encore vivant, et non le coffre lui-même.
RACINE_PRODUIT = Path(__file__).resolve().parent.parent


def _parties(zone: str) -> list:
    return [p for p in zone.split("/") if p not in ("", ".")]


def _absolue(zone: str) -> bool:
    """Un chemin absolu sortirait du coffre : les zones sont relatives (§13)."""
    return (zone.startswith(("/", "\\", "~"))
            or (len(zone) > 1 and zone[1] == ":"))


def parties_hors_memoire(zone: str) -> list:
    """Les parts de la zone qui la mettent hors mémoire (`code/`, `.git`…).

    La règle elle-même vit dans le moteur partagé, une seule fois
    (``partie_hors_memoire``) ; la carte l'applique sans lire le disque, et la
    porte s'en sert pour écarter une zone qu'on lui donnerait en direct.
    """
    return [p for p in _parties(zone) if CONVENTION.partie_hors_memoire(p)]


def zone_legale(coffre, zone: str, agents=None, auteur=None) -> bool:
    """La zone est-elle une destination légale, hors de tout dépôt imbriqué ?

    Écartée si elle est absolue, si une part est `code/`, `node_modules/` ou un
    dossier caché, si un sous-dossier abrite un `.git` (dépôt imbriqué, §7.3), si
    elle tombe dans un chantier gelé de la mémoire du coffre (§6), ou si la
    matrice du §7.3 ne la nomme pas — `_MAINTENANCE/` comprise, désormais.

    Elle juge la **forme** — relative, hors dépôt imbriqué, hors mémoire gelée —
    et **l'appartenance au §7.3**. ``auteur`` est obligatoire : écrire sans dire
    qui écrit n'est pas jugeable au §7.3, et une carte sans auteur serait un
    « tout est ouvert » silencieux. Auteur absent vaut refus, sous le motif
    unique du moteur (``MOTIF_AUTEUR_ABSENT``) — la porte juge de même.

    ``agents`` vient du dépôt produit ; à défaut on le lit. Un dépôt sans
    ``IA/agents/`` rend l'ensemble vide, donc tout ``expériences/`` inconnu est
    pris pour gelé : mieux vaut refuser d'écrire que rouvrir un chantier clos.
    """
    if _absolue(zone):
        return False
    if not CONVENTION.zone_autorisee(zone, auteur)[0]:
        return False
    if parties_hors_memoire(zone):
        return False
    courant = Path(coffre)
    for partie in _parties(zone):
        courant = courant / partie
        if CONVENTION.est_depot_imbrique(courant):
            return False
    if agents is None:
        agents = CONVENTION.liste_des_agents(RACINE_PRODUIT)
    return not CONVENTION.est_gele(Path(coffre) / zone, coffre, agents)


def contenu_existant(coffre, zone: str) -> tuple:
    """Chemins **relatifs à la zone** des notes déjà présentes, triés.

    Un chemin relatif, pas un simple nom : une note peut vivre dans un
    sous-dossier de la zone. Le refus « nom unique » ne porte que sur le **même
    dossier de destination** — la carte montre donc où vit la note, et un
    homonyme rangé plus bas ne fait pas croire qu'il occupe la racine. Les
    fichiers de dossier (`sommaire.md`, `README.md`) n'y figurent pas : ce ne sont
    pas des notes (`notes_du_dossier` les écarte déjà). Une zone absolue ne liste
    rien : elle sortirait du coffre.
    """
    if _absolue(zone):
        return ()
    dossier = Path(coffre) / zone
    return tuple(sorted(p.relative_to(dossier).as_posix()
                        for p in CONVENTION.notes_du_dossier(dossier)))


def carte_legale(coffre, zones, auteur=None) -> dict:
    """Pour chaque zone autorisée, légale et ouverte à ``auteur``, ses notes déjà là.

    L'``auteur`` est **obligatoire** : une zone interdite, absolue, sous un dépôt
    imbriqué, dans un chantier gelé, ou hors de la matrice du §7.3 est **écartée**
    de la carte, pas donnée vide — ce qui n'est pas une destination ne se montre
    pas (§7.3, §6). Sans auteur, rien n'est montré. Les chemins sont **relatifs à
    la zone**, pour que le refus « nom unique » compare des notes du même dossier.
    """
    agents = CONVENTION.liste_des_agents(RACINE_PRODUIT)
    carte: dict = {}
    for zone in zones:
        if not zone_legale(coffre, zone, agents, auteur):
            continue
        carte[zone] = contenu_existant(coffre, zone)
    return carte
