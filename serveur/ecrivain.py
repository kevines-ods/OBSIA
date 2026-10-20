#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L'écrivain des carnets — produire un carnet de bout en bout, à travers la porte.

C'est le premier **geste** du produit. Jusqu'ici, la porte savait juger une
écriture sans l'écrire ; l'écrivain prend un **sujet**, compose le carnet, le fait
passer par la porte de #149 (matrice §7.3, mémoire gelée, unicité, auteur
obligatoire, garde des secrets), l'écrit, en garde une copie d'aperçu datée dans
``_MAINTENANCE/`` (§7.4), puis le commite.

Ce que l'écrivain calcule, et que l'appelant n'a pas à connaître : le chemin, le
nom, la date, le frontmatter. Le modèle dit **quoi** écrire, jamais **où** — le
chemin ne vient pas de lui.

Le banc de **tout** acte — le verrou, le préalable, la marque du commit
(``OBSIA-Outil`` / ``OBSIA-Auteur``), la vérification que le commit porte
exactement ses fichiers, et le contexte de la porte — vit dans
:mod:`serveur.socle_ecriture` : il est partagé avec les gestes des notes
(ranger, compléter) plutôt que recopié. Ce module-ci ne garde que ce qui est
propre au **carnet** : son texte, sa demande, ses zones, ses dossiers, son acte.

**Ce qui restait à poser avant le coffre réel** — et qui l'est depuis. L'écrivain
n'était alors **pas encore déclaré** dans ``IA/MCP/`` : cette fiche — disant qu'il
écrit *pour un modèle local piloté* — est la **condition d'entrée** de l'exception
bornée du §7.4, à poser avant tout usage sur un coffre réel. Elle existe depuis le
**2026-10-09**, et le §7.4 la cite par son chemin.

**Ce que la phase 5 a posé.** L'écrivain **revérifie** désormais ``HEAD`` et
l'empreinte des fichiers écrits **juste avant** de committer : un commit concurrent,
ou un fichier touché en chemin, fait **refuser** l'acte — jamais écraser. Un
**verrou périmé**, dont le porteur est mort, est **relevé** à la reprise ; un verrou
tenu par un vivant fait **attendre** l'acte, et un **second écrivain** (autre hôte,
autre outil) est signalé. La **tenue au fil de l'eau** d'un carnet existant passe par
``compléter`` (voir :mod:`serveur.gestes_des_notes`) ; l'écrivain, lui, **crée** des
carnets.
"""

from __future__ import annotations

import datetime
import sys
import unicodedata
from pathlib import Path
from typing import NamedTuple

sys.dont_write_bytecode = True
_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import convention_des_notes as CONVENTION   # noqa: E402

try:                                        # importé comme `serveur.ecrivain`
    from . import porte_entree as PORTE
    from .socle_ecriture import (Acte, MARQUE_AUTEUR, MARQUE_OUTIL, OUTIL,
                                 RACINE_PRODUIT, VERROU, Verrou, _committer,
                                 _contexte, _defaire, _dire, _ecrire, _etat_avant,
                                 _prealable, auteur_du_commit, fichiers_du_commit,
                                 message_d_un_acte, outil_du_commit,
                                 remonter_les_incidents, tete_de,
                                 texte_de_la_copie)
except ImportError:                         # importé à plat : le dossier est sur le chemin
    import porte_entree as PORTE            # noqa: E402
    from socle_ecriture import (Acte, MARQUE_AUTEUR, MARQUE_OUTIL, OUTIL,
                                RACINE_PRODUIT, VERROU, Verrou, _committer,
                                _contexte, _defaire, _dire, _ecrire, _etat_avant,
                                _prealable, auteur_du_commit, fichiers_du_commit,
                                message_d_un_acte, outil_du_commit,
                                remonter_les_incidents, tete_de,
                                texte_de_la_copie)

#: La forme d'une date acceptée par le §6 — définie une seule fois, dans la
#: convention, pour que les trois gestes de l'écrivain jugent la même.
DATE_ISO = CONVENTION.DATE_ISO

# Ré-export : le socle et la porte sont le vocabulaire commun des appelants de
# l'écrivain. Les noms ci-dessus (et `Acte`, `Verrou`, `PORTE`) sont ceux que les
# tests de #149 et l'appelant lisent sur `serveur.ecrivain` — on ne les renomme pas.
__all__ = ["Acte", "Verrou", "PORTE", "OUTIL", "VERROU", "RACINE_PRODUIT",
           "message_d_un_acte", "outil_du_commit", "auteur_du_commit",
           "fichiers_du_commit", "texte_de_la_copie", "texte_du_carnet",
           "ecrire_un_carnet"]


def texte_du_carnet(auteur: str, dossier: str, statut: str, date: str,
                    corps: str) -> str:
    """Le texte exact d'un carnet (§5, §6) : son frontmatter, puis son corps.

    C'est **l'aperçu** : ce que la copie conserve et ce que le fichier contient,
    au même octet près.
    """
    frontmatter = ["---",
                   "agent: %s" % auteur,
                   "projet: %s" % dossier,
                   "statut: %s" % statut,
                   "date: %s" % date,
                   "---", ""]
    return "\n".join(frontmatter) + str(corps).strip("\n") + "\n"


def _demande(auteur: str, projet: str, chantier, sujet, date, statut) -> str:
    """La demande, en une phrase — ce que la trace met sous les yeux."""
    ou = ("chantier `%s` du projet `%s`" % (chantier, projet) if chantier
          else "projet `%s`" % projet)
    return ("créer un carnet pour %s — sujet « %s », statut `%s`, le %s, "
            "par l'auteur `%s`" % (ou, sujet, statut, date, auteur))


def _zones_du_carnet(projet: str, chantier) -> str:
    """La zone du carnet (§6) : les ``carnets/`` du chantier, ou du projet."""
    if chantier:
        return "0-PROJETS/%s/%s/carnets" % (projet, chantier)
    return "0-PROJETS/%s/carnets" % projet


def _dossier_jumeau(coffre, parent: str, demande: str):
    """Le dossier qui porte le même nom normalisé sous une autre orthographe.

    ``nom_comparable`` range ``Homelab`` et ``homelab`` sous la même clé : deux
    dossiers ainsi nommés seraient deux dossiers que plus rien ne relierait, et le
    carnet irait sous l'un quand on le chercherait sous l'autre. On en rend le nom
    réel, ou ``None``.
    """
    racine = Path(coffre) / parent
    if not racine.is_dir():
        return None
    cle = CONVENTION.nom_comparable(demande)
    for entree in sorted(racine.iterdir()):
        if (entree.is_dir() and entree.name != demande
                and CONVENTION.nom_comparable(entree.name) == cle):
            return entree.name
    return None


def _motif_de_dossier(coffre, parent: str, demande: str):
    """Le motif de refus d'un nom de dossier de projet ou de chantier, ou ``None``.

    Le dossier est pris **tel quel** : la règle de nommage ne le replie pas — c'est
    le sujet qui se replie — et le contrôle du coffre compare au nom réellement
    présent sur le disque. Une même demande doit donc désigner le même dossier des
    deux côtés. Il reste un **nom**, jamais un chemin. Et s'il existe déjà un
    dossier qui se compare au même nom sous une autre orthographe, on refuse plutôt
    que d'en semer un jumeau.
    """
    if (not demande or demande.strip() != demande or demande in (".", "..")
            or any(caractere in demande for caractere in ("/", "\\", "\0"))):
        return ("nom de dossier `%s` mal formé : un dossier de projet ou de chantier "
                "est un seul nom — ni séparateur, ni remontée `..`" % demande)
    # `Cc` (contrôle) **et** `Cf` (format) : une largeur nulle, un BOM ou une marque
    # d'orientation ne se voient pas — `Home<ZWSP>lab` serait un dossier
    # visuellement jumeau de `Homelab`, sans que rien ne le distingue à l'œil.
    controle = next((c for c in demande
                     if unicodedata.category(c) in ("Cc", "Cf")), None)
    if controle is not None:
        lisible = "".join("?" if unicodedata.category(c) in ("Cc", "Cf") else c
                          for c in demande)
        return ("nom de dossier `%s` mal formé : un nom de dossier ne porte aucun "
                "caractère de contrôle ni invisible — ni retour à la ligne, ni "
                "tabulation, ni largeur nulle, ni marque d'orientation (trouvé %r)"
                % (lisible, controle))
    jumeau = _dossier_jumeau(coffre, parent, demande)
    if jumeau is not None:
        return ("dossier jumeau : `%s/%s/` existe déjà et se compare au même nom que "
                "`%s` — écrire sous l'orthographe du dossier existant (`%s`) plutôt "
                "que d'en semer un second" % (parent, jumeau, demande, jumeau))
    return None


def ecrire_un_carnet(coffre, *, auteur: str, projet: str, chantier=None,
                     sujet: str, corps: str,
                     statut: str = CONVENTION.STATUT_EN_COURS,
                     date=None) -> Acte:
    """Créer un carnet à partir d'un **sujet**, à travers la porte, en un seul acte.

    L'appelant dit *quoi* (le projet, le chantier, le sujet, le corps) ; l'outil
    calcule *où* et *comment* — nom, date, frontmatter. ``date`` n'existe que pour
    rejouer un jour précis ; par défaut, c'est aujourd'hui.

    Le projet et le chantier sont des **noms de dossier**, pas des chemins : ils
    sont pris tels quels, et refusés s'ils portent un séparateur ou s'il existe
    déjà un dossier qui se compare au même nom sous une autre orthographe.

    Rend un :class:`Acte`. Un refus n'écrit rien : il est **rendu**, jamais
    consigné dans un fichier neuf — et si une écriture échoue en chemin, ce qui
    avait été écrit est défait avant que le refus ne remonte.
    """
    coffre = Path(coffre)
    auteur = str(auteur).strip()
    date = str(date) if date else datetime.date.today().isoformat()
    dossier = chantier or projet
    demande = _demande(auteur, projet, chantier, sujet, date, statut)

    def refuse(motif, chemin=None):
        return Acte(demande=demande, chemin=chemin, apercu=None, copie=None,
                    commit=None, refus=motif)

    if statut not in CONVENTION.STATUTS_CARNET:
        return refuse("statut `%s` inconnu (§6) — attendu l'un de : %s"
                      % (statut, ", ".join(CONVENTION.STATUTS_CARNET)))
    if not DATE_ISO.match(date):
        return refuse("date `%s` mal formée (§6) — attendue sous la forme AAAA-MM-JJ"
                      % date)
    motif = _motif_de_dossier(coffre, "0-PROJETS", projet)
    if motif is None and chantier:
        motif = _motif_de_dossier(coffre, "0-PROJETS/%s" % projet, chantier)
    if motif is not None:
        return refuse(motif)

    nom = CONVENTION.nom_de_carnet(date, dossier, sujet)
    zone = _zones_du_carnet(projet, chantier)
    chemin = PORTE.destination(zone, nom)
    copie = PORTE.destination(CONVENTION.MAINTENANCE,
                              CONVENTION.nom_de_l_apercu(date, nom, zone))
    apercu = texte_du_carnet(auteur, dossier, statut, date, corps)

    impossible, dossier_git = _prealable(coffre)
    if impossible is not None:
        return refuse(impossible, chemin)

    verrou = Verrou(dossier_git)
    with verrou as pris:
        if not pris:
            return refuse(verrou.motif, chemin)

        # F5 : la tête du dépôt, prise **sous** le verrou — c'est à elle qu'on
        # comparera, juste avant le commit, pour voir venir un commit concurrent.
        tete = tete_de(coffre)
        contexte = _contexte(coffre, auteur, (zone, CONVENTION.MAINTENANCE))
        copie_texte = texte_de_la_copie(demande, chemin, apercu)
        # Le nom du carnet est **déjà calculé** par la règle du §6, et son dossier
        # garde l'orthographe réelle : la porte le juge tel quel — mais elle le
        # **recalcule** depuis la zone et le sujet brut, et refuse tout nom qui
        # diffère : le nom d'un acte n'est jamais libre. Pour l'aperçu, la matière
        # brute est le nom du carnet lui-même, et son dossier d'origine est la zone du
        # carnet : `nom_de_l_apercu` en garde le nom entier, date comprise (une
        # **seule** forme, la même que pour `compléter`) et ne redouble pas le dossier —
        # la copie reste ainsi nouée au carnet qu'elle accompagne.
        jugements = ((PORTE.Candidat(zone, sujet, apercu, nom), chemin),
                     (PORTE.Candidat(CONVENTION.MAINTENANCE, nom, copie_texte,
                                     nom=CONVENTION.nom_de_l_apercu(date, nom, zone),
                                     dossier=zone), copie))
        for candidat, vise in jugements:
            verdict = PORTE.juger(candidat, contexte)
            if verdict.refus is not None:
                return refuse(_dire(verdict.refus), vise)
            if verdict.destination != vise:
                return refuse("la porte range l'acte ailleurs qu'au chemin calculé "
                              "(`%s` au lieu de `%s`) : l'écriture s'arrête là"
                              % (verdict.destination, vise), vise)

        # L'état d'avant : un carnet et sa copie **créés** (rien avant). S'ils
        # existaient déjà, la porte les aurait refusés (unicité §6).
        etats = _etat_avant(coffre, (chemin, copie))
        try:
            for relatif, texte in ((chemin, apercu), (copie, copie_texte)):
                _ecrire(coffre, relatif, texte)
        except Exception as panne:
            # On attrape **tout**, pas seulement l'OSError : un texte inencodable
            # lève avant même que le fichier soit touché, et un fichier à moitié
            # écrit est exactement ce qu'on refuse. Dans tous les cas, on défait et
            # on dit le refus — un acte qui échoue ne laisse rien derrière lui.
            _defaire(coffre, etats, {chemin: apercu, copie: copie_texte})
            return refuse("l'écriture a échoué — ce qui avait été écrit a été défait : %s"
                          % panne, chemin)

        commit, motif = _committer(coffre, etats,
                                   message_d_un_acte("Carnet : %s" % nom[:-3], auteur),
                                   lister=fichiers_du_commit,
                                   tete_attendue=tete,
                                   ecrits={chemin: apercu, copie: copie_texte})
        if motif is not None:
            return refuse(motif, chemin)

        # L'acte suivant rend à l'agent ce que les actes d'avant ont consigné sans
        # qu'il le voie encore (constat 7) : les incidents non remontés, à consigner
        # au carnet. Sous le verrou — la lecture et l'avance du marqueur ne se croisent pas.
        incidents = remonter_les_incidents(coffre)

    return Acte(demande=demande, chemin=chemin, apercu=apercu, copie=copie,
                commit=commit, refus=None, incidents=incidents)
