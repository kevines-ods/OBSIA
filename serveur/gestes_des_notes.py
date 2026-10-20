#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Les gestes des notes — ranger une note du vrac, compléter une note sur place.

Deux gestes, un même banc (le verrou, le préalable, le commit d'acte, le contexte
de la porte — voir :mod:`serveur.socle_ecriture`, partagé avec l'écrivain des
carnets) :

- **ranger** déplace une note **du vrac seul** vers une zone autorisée. Elle ne se
  réécrit pas — on ne range pas une note en la changeant —, elle garde son nom
  exact, et le registre ``_MAINTENANCE/notes_remplies.md`` s'ajoute dans le
  **même** commit : le rangement et sa trace ne se séparent jamais (§7.3, §7.4).
- **compléter** remplit une note **sur place**, en **ajoutant** : le corps ne fait
  que croître à la fin, le frontmatter ne perd ni ne change aucune clé, ``tags`` ne
  fait que croître — **sauf** retirer un tag hors vocabulaire, seul retrait permis
  (§7.5) —, et tout tag ajouté vient du vocabulaire contrôlé. La complétion est
  **ouverte au vrac, aux savoirs et au registre** de maintenance, et — c'est la tenue
  au fil de l'eau d'une note que l'agent tient sur place (§7.3) — aux **carnets** d'un
  projet ou d'un chantier. Un résumé, une vision, des préférences ou une expérience
  viendront plus tard. Jamais dans ``0-DOCUMENTS`` / ``0-PERSONNELS`` / les autres
  dossiers de ``0-PROJETS`` : on n'y modifie pas une note existante.

**Un déplacement, deux chemins jugés.** Ranger juge la source **et** la
destination : la source doit être une note présente sous ``0-EN-VRAC/``, et le nom
fourni doit être exactement celui du fichier visé. L'unicité du §6 se vérifie sur
**tout le coffre parent**, pas seulement dans la zone d'arrivée — un homonyme
ailleurs interdit le rangement.

**Rien ne se perd.** L'état d'avant de chaque chemin est lu **après** la pose du
verrou (jamais avant : une autre écriture pourrait l'avoir changé entre-temps) et
confié au commit d'acte. Un refus n'écrit rien ; un acte qui échoue en chemin est
**défait** : ce qui a été créé se retire, ce qui a été modifié, déplacé ou supprimé
se restaure à l'octet près — la note complétée reprend son texte, la note rangée
revient dans le vrac, l'aperçu du jour retrouve ses sections d'avant.

**Un seul aperçu par note, par dossier d'origine et par jour** (§7.4) : le nom de la
note **tel quel**, précédé de son dossier d'origine replié en tige et de la date —
``_MAINTENANCE/<date>-apercu-<dossier>--<nom>``, deux tirets entre le dossier et le
nom pour que ``0-SAVOIRS/reseau-note.md`` ne se confonde pas avec
``0-SAVOIRS/Réseau/note.md`` ; un carnet, lui, garde son nom entier, date comprise,
sans redoubler son dossier (:func:`convention_des_notes.nom_de_l_apercu`). Le nom est
recalculé par le moteur, donc infalsifiable. Le premier acte du jour sur cette note
**depuis ce dossier** le **crée** ; les actes suivants du même jour, lus au même
dossier, y **ajoutent** une section (geste, chemin, aperçu exact), sans jamais le
réécrire. Une note qui **change de dossier** le même jour change donc d'aperçu : son
dossier d'origine fait partie de son identité — le prix de la distinction de deux
homonymes de deux dossiers, que replier seul ne saurait rendre. C'est le chemin normal
du traitement — *remplir, puis classer*, tous deux lus au vrac — et l'unicité du §6 ne
s'y oppose pas : ajouter à l'aperçu du jour n'est pas créer un homonyme, alors qu'une
seconde copie du même nom reste refusée.
"""

from __future__ import annotations

import datetime
import sys
from pathlib import Path

sys.dont_write_bytecode = True
_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import convention_des_notes as CONVENTION   # noqa: E402

try:                                        # importé comme `serveur.gestes_des_notes`
    from . import porte_entree as PORTE
    from .socle_ecriture import (Acte, VERROU, Verrou, _committer, _contexte,
                                 _defaire, _dire, _ecrire, _etat_avant, _prealable,
                                 _texte, fichiers_du_commit, message_d_un_acte,
                                 remonter_les_incidents, tete_de, texte_de_la_copie)
except ImportError:                         # importé à plat : le dossier est sur le chemin
    import porte_entree as PORTE            # noqa: E402
    from socle_ecriture import (Acte, VERROU, Verrou, _committer, _contexte,
                                _defaire, _dire, _ecrire, _etat_avant, _prealable,
                                _texte, fichiers_du_commit, message_d_un_acte,
                                remonter_les_incidents, tete_de, texte_de_la_copie)

#: Le registre du §7.4 : la liste des notes traitées, ajoutée en fin, jamais réécrite.
REGISTRE = "notes_remplies.md"

#: Le chemin du registre, relatif à la racine du coffre.
REGISTRE_RELATIF = CONVENTION.MAINTENANCE + "/" + REGISTRE

#: Les **têtes de zone** ouvertes à la complétion (§7.3) : le vrac et les savoirs.
#: La règle de zone du contrat se lit sur le premier segment (``seg[0]``) : tout
#: sous-dossier d'une tête ouverte est donc ouvert, et une note rangée dans
#: ``0-SAVOIRS/Réseau/`` reste complétable. Le registre de maintenance s'y ajoute,
#: nommément — et les carnets, dont l'agent tient la note sur place, s'ouvrent par le
#: **genre de zone** (voir ``GENRES_TENUS_AU_FIL_DE_L_EAU``).
ZONES_OUVERTES_A_LA_COMPLETION = (CONVENTION.VRAC, "0-SAVOIRS")

#: La marque propre à chaque geste (§7.4) : l'historique dit **quel** geste a écrit,
#: non seulement qu'un outil l'a fait. L'écrivain des carnets garde la sienne.
OUTIL_RANGER = "ranger-une-note"
OUTIL_COMPLETER = "completer-une-note"


def _le_jour(date) -> str:
    """La date de l'acte : celle qu'on rejoue, ou le jour même."""
    return str(date) if date else datetime.date.today().isoformat()


class CoffreInjoignable(Exception):
    """Le coffre désigné n'est pas un dépôt de données : la lecture est refusée."""


def _refus_de_la_source(coffre, source):
    """La source est-elle une note **du coffre** ? — jugé **sans rien lire**.

    ``coffre / source`` suit la source **où elle mène** : une source absolue, ou
    qui remonte par ``..``, fait sortir du coffre. La lire avant de la juger
    ouvrirait alors un fichier qui n'est pas une note, et le refus dirait, par sa
    seule forme, si ce fichier existe — un **oracle d'existence** sur tout le
    disque. On juge donc la source **avant toute lecture** : relative, propre, et
    résolue sous la racine du coffre. Le motif ne dépend ni du contenu, ni de
    l'existence du fichier visé : c'est le même, toujours.

    Rend le motif du refus, ou ``None`` si la source est saine.
    """
    if not isinstance(source, str) or not source.strip():
        return ("la source n'est pas nommée : dire le nom de la note à traiter, tel "
                "qu'il apparaît dans l'inventaire des notes")
    if source.startswith("/") or "\\" in source or source[1:2] == ":":
        return ("la source `%s` n'est pas un chemin relatif au coffre : une note se "
                "désigne par son chemin **dans** le coffre, jamais par un chemin "
                "absolu ni par un chemin de machine" % source)
    if any(morceau in ("", ".", "..") for morceau in source.split("/")):
        return ("la source `%s` sort du coffre : une note se désigne par son chemin "
                "dans le coffre, sans `.` ni `..`" % source)
    racine = Path(coffre).resolve()
    chemin = (racine / source).resolve()
    if racine not in chemin.parents:
        return ("la source `%s` sort du coffre : une note se désigne par son chemin "
                "dans le coffre" % source)
    return None


def _refus_de_la_date(date):
    """La date est-elle de la forme du §6 ? — le même jugement que pour un carnet."""
    if date is not None and not CONVENTION.DATE_ISO.match(str(date)):
        return ("date `%s` mal formée (§6) — attendue sous la forme AAAA-MM-JJ"
                % date)
    return None


def _titre(verbe: str, nom: str) -> str:
    """Le titre d'un acte de note — le verbe, puis le nom sans son extension."""
    return "%s : %s" % (verbe, nom[:-3] if nom.endswith(".md") else nom)


def notes_du_coffre(coffre) -> tuple:
    """Tous les chemins de notes du coffre parent, relatifs à sa racine.

    C'est la matière du contrôle d'unicité du §6 — un nom de note reste unique
    dans **tout** le coffre, pas seulement là où on l'écrit. On s'en tient aux
    têtes de zone que le contrat reconnaît (§7.1) : un fichier ``.md`` hors zone
    n'est pas une note du coffre et ne doit pas interdire un rangement légitime.

    Le coffre doit **être un dépôt de données** : hors d'un dépôt, il n'y a pas de
    coffre à lire, et l'écrivain refuse plutôt que d'énumérer un dossier
    quelconque. Le refus est levé en :class:`CoffreInjoignable` — un inventaire
    n'est pas un acte, il n'a pas de trace où porter son motif.
    """
    motif, _ = _prealable(coffre)
    if motif is not None:
        raise CoffreInjoignable(motif)
    racine = Path(coffre)
    vues = []
    for zone in sorted(CONVENTION.ZONES_DU_CONTRAT):
        dossier = racine / zone
        if dossier.is_dir():
            for note in CONVENTION.notes_du_dossier(dossier):
                vues.append(note.relative_to(racine).as_posix())
    return tuple(sorted(vues))


def _ligne_du_registre(chemin: str, avant: str) -> str:
    """Ce qu'on ajoute au registre pour inscrire une note rangée.

    Le registre est un journal : une note traitée, une ligne. On **ajoute** — le
    reste du fichier n'est jamais réécrit —, et on coupe la ligne si le registre
    ne se terminait pas par un retour.
    """
    debut = "" if (not avant or avant.endswith("\n")) else "\n"
    return "%s%s\n" % (debut, chemin)


def _dossier_de_la_source(source: str) -> str:
    """Le **dossier d'origine** d'une note : le dossier de sa source, sans son nom.

    C'est lui qui entre dans le nom de l'aperçu du jour (§7.4) : deux notes homonymes
    de deux dossiers ne se disputent donc plus un même aperçu. On prend le dossier de
    la **source**, non la zone visée, pour qu'un remplissage dans le vrac suivi d'un
    rangement le même jour garde le même aperçu — l'origine du rangement est le vrac.
    """
    return str(source).rsplit("/", 1)[0] if "/" in str(source) else ""


def _chemin_de_l_apercu(date: str, nom: str, dossier: str = "") -> str:
    """Le chemin, dans la maintenance, de la copie d'aperçu d'une note (§7.4)."""
    return PORTE.destination(CONVENTION.MAINTENANCE,
                             CONVENTION.nom_de_l_apercu(date, nom, dossier))


#: Les genres dont la **tenue au fil de l'eau** reste à venir (§7.3). Ils se nomment
#: par le libellé de la règle de zone du contrat, pour que le refus dise *ce qui*
#: attend et non seulement *où* : un résumé, une vision, des préférences, une
#: expérience se complètent au fil de leur propre geste, et ce geste viendra plus
#: tard. `compléter` n'y touche pas — même là où la matrice l'ouvrirait, car le sens
#: d'une note vivante se réécrit à chaque ligne.
GENRES_TENUS_A_PART = frozenset((
    "un résumé de projet", "un résumé de chantier",
    "une note « — vision »",
    "les préférences", "les expériences d'un agent",
))

#: Les genres ouverts à la **tenue au fil de l'eau** (§7.3, phase 5) : les carnets,
#: que le contrat reconnaît comme des notes que l'agent **tient sur place** au même
#: titre que son `` — résumé`` ou sa `` — vision``. On peut donc y ajouter une étape
#: par ``compléter``, sous les mêmes garanties qu'ailleurs (ajout en fin seulement,
#: frontmatter intact, tags du vocabulaire).
GENRES_TENUS_AU_FIL_DE_L_EAU = frozenset((
    "un carnet de projet", "un carnet de chantier",
))


def _tete_de_zone(zone: str) -> str:
    """La **tête** de zone d'une zone — ce que la matrice §7.3 juge.

    La règle de zone se lit sur le premier segment seul (``regle_de_zone``,
    ``seg[0]``) : ``0-SAVOIRS/Réseau`` est une bouche de ``0-SAVOIRS``. Comparer la
    zone **entière** à la tête fermait la complétion à tout sous-dossier qu'un
    rangement venait d'ouvrir — ``0-SAVOIRS/Réseau/`` accepté au rangement, refusé à
    la complétion.
    """
    return zone.split("/", 1)[0]


def _libelle_de_zone(zone: str, nom: str):
    """Le libellé de la règle de zone du contrat, ou ``None`` hors zone reconnue."""
    regle = CONVENTION.regle_de_zone(PORTE.destination(zone, nom))
    return regle.libelle if regle is not None else None


def _genre_tenu_a_part(zone: str, nom: str):
    """Le genre de note que `compléter` ne touche pas encore, ou ``None`` (§7.3).

    On lit le genre dans la **règle de zone** du contrat plutôt que de deviner par
    le nom : une note du vrac peut porter une date, ou s'appeler « … — vision »,
    sans être pour autant un carnet ou une vision de projet.
    """
    libelle = _libelle_de_zone(zone, nom)
    if libelle is not None and libelle in GENRES_TENUS_A_PART:
        return libelle
    return None


def _section_du_jour(geste: str, date: str, chemin: str, apercu: str) -> str:
    """La section qu'un nouvel acte ajoute à l'aperçu du jour (§7.4).

    On **ajoute** au fichier du jour : le geste, le chemin visé et l'aperçu exact de
    ce qui a été écrit. Rien n'est réécrit — une section par acte, dans l'ordre où
    les actes sont venus.
    """
    return ("\n## %s — %s\n\n- Geste : %s\n- Chemin : `%s`\n\n"
            "### Aperçu exact\n\n~~~markdown\n%s~~~\n"
            % (geste, date, geste, chemin, apercu))


def _apercu_du_jour(contexte, *, date: str, nom: str, dossier: str, copie: str,
                    avant_copie, demande: str, geste: str, chemin: str, texte: str):
    """Le texte de l'aperçu du jour, son candidat et le contexte pour le juger.

    Un **seul** aperçu par note, **par dossier d'origine** et par jour (§7.4) : le
    premier acte du jour lu à ce dossier le **crée** — la copie datée entière, comme en
    P3 —, et tout acte suivant du même jour, lu au même dossier, l'**ajoute** en fin,
    section par section. Ajouter à l'aperçu du jour n'est pas créer un homonyme :
    l'unicité du §6 reste entière pour tout autre nom. L'aperçu ajouté se **restaure**
    à l'octet si l'acte échoue, puisque c'est l'état d'avant qui repart avec l'acte (F1).

    ``dossier`` est le dossier **d'origine** de la note (celui de sa source) : il
    entre dans le nom de l'aperçu, pour que deux notes homonymes de deux dossiers ne
    se le disputent pas — donc une note qui change de dossier le même jour reçoit un
    **second** aperçu, le dossier d'origine faisant partie de son identité.

    Un aperçu du jour **vide** — un reste laissé en début de journée — n'est pas
    « un texte d'avant » à quoi ajouter, mais n'**bloque** pas la journée : l'acte
    l'**achève** en y remettant la copie du jour entière, sous la même nature que
    l'ajout (le fichier existe, il n'est pas une création).
    """
    nom_de_l_apercu = CONVENTION.nom_de_l_apercu(date, nom, dossier)
    if avant_copie is None:
        texte_copie = texte_de_la_copie(demande, chemin, texte)
        candidat = PORTE.Candidat(CONVENTION.MAINTENANCE, nom, texte_copie,
                                  nom=nom_de_l_apercu, dossier=dossier)
        return texte_copie, candidat, contexte._replace(
            nature=CONVENTION.NATURE_CREER)
    if not avant_copie:
        # L'aperçu du jour existe mais ne porte rien : l'acte le **remplit** avec la
        # copie du jour, entière. Le fichier est là, donc ce n'est pas une création —
        # mais il n'y a rien à quoi ajouter, donc rien à mesurer : `avant=""`.
        texte_copie = texte_de_la_copie(demande, chemin, texte)
        candidat = PORTE.Candidat(CONVENTION.MAINTENANCE, nom, texte_copie,
                                  nom=nom_de_l_apercu, source=copie, avant="",
                                  dossier=dossier)
        return texte_copie, candidat, contexte._replace(
            nature=CONVENTION.NATURE_COMPLETER)
    texte_copie = avant_copie + _section_du_jour(geste, date, chemin, texte)
    candidat = PORTE.Candidat(CONVENTION.MAINTENANCE, nom, texte_copie,
                              nom=nom_de_l_apercu, source=copie,
                              avant=avant_copie, dossier=dossier)
    return texte_copie, candidat, contexte._replace(
        nature=CONVENTION.NATURE_COMPLETER)


def completer_une_note(coffre, *, auteur: str, source: str, texte: str,
                       date=None) -> Acte:
    """Compléter une note **présente**, sur place, en n'ajoutant qu'à la fin (§7.3).

    ``texte`` est le contenu **entier** après complétion : la porte le compare à ce
    qui est sur le disque et refuse tout ce qui ne serait pas un ajout en fin de
    corps, un frontmatter amputé d'une clé, ou un tag ajouté hors vocabulaire. Rien
    ne s'écrit si le geste est refusé, et la note est relue **après** la pose du
    verrou : c'est ce texte-là, à l'octet près, qui sera restauré si l'acte échoue.
    """
    coffre = Path(coffre)
    auteur = str(auteur).strip()
    date = _le_jour(date)
    source = str(source)
    demande = "compléter la note `%s` (auteur `%s`, le %s)" % (source, auteur, date)

    def refuse(motif, chemin=None):
        return Acte(demande=demande, chemin=chemin, apercu=None, copie=None,
                    commit=None, refus=motif)

    # La source est jugée **avant toute lecture** : hors du coffre, la lire dirait
    # si un fichier qui n'est pas une note existe (oracle d'existence).
    motif = _refus_de_la_source(coffre, source)
    if motif is not None:
        return refuse(motif)
    motif = _refus_de_la_date(date)
    if motif is not None:
        return refuse(motif)

    nom = source.rsplit("/", 1)[-1]
    zone = source.rpartition("/")[0]
    chemin = PORTE.destination(zone, nom)
    dossier = _dossier_de_la_source(source)
    copie = _chemin_de_l_apercu(date, nom, dossier)

    genre = _genre_tenu_a_part(zone, nom)
    if genre is not None:
        return refuse("compléter n'est pas encore ouvert à %s : sa tenue au fil de "
                      "l'eau viendra plus tard, et `compléter` n'y touche pas en P4 "
                      "(§7.3)" % genre, chemin)

    if (_tete_de_zone(zone) not in ZONES_OUVERTES_A_LA_COMPLETION
            and source != REGISTRE_RELATIF
            and _libelle_de_zone(zone, nom) not in GENRES_TENUS_AU_FIL_DE_L_EAU):
        return refuse("compléter n'est pas encore ouvert à la zone `%s` : la complétion "
                      "se limite au vrac, aux savoirs, au registre de maintenance et à "
                      "la tenue au fil de l'eau des carnets (§7.3)" % zone, chemin)

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
        # F4 : on lit l'état d'avant **après** le verrou — sous la protection de
        # l'acte, et pas sur une observation peut-être périmée.
        etats = _etat_avant(coffre, (chemin, copie))
        avant = _texte(etats[chemin])
        if avant is None:
            return refuse("la note visée `%s` n'est pas là : `compléter` reprend une note "
                          "présente — il n'en crée pas" % source, chemin)
        contexte = _contexte(coffre, auteur, (zone, CONVENTION.MAINTENANCE),
                             nature=CONVENTION.NATURE_COMPLETER,
                             notes_du_coffre=notes_du_coffre(coffre))
        candidat = PORTE.Candidat(zone, nom, texte, nom=nom, source=source,
                                  avant=avant)
        verdict = PORTE.juger(candidat, contexte)
        if verdict.refus is not None:
            return refuse(_dire(verdict.refus), chemin)
        if verdict.destination != chemin:
            return refuse("la porte range l'acte ailleurs qu'au chemin calculé (`%s` au "
                          "lieu de `%s`) : l'écriture s'arrête là"
                          % (verdict.destination, chemin), chemin)
        # Un seul aperçu par note, par dossier d'origine et par jour : on le crée, ou
        # on y ajoute (§7.4). Ici le dossier est celui de la source, donc celui de la
        # note elle-même — un acte lu ailleurs aurait un autre aperçu.
        copie_texte, candidat_copie, contexte_copie = _apercu_du_jour(
            contexte, date=date, nom=nom, dossier=dossier, copie=copie,
            avant_copie=_texte(etats[copie]),
            demande=demande, geste="Compléter", chemin=chemin, texte=texte)
        verdict_copie = PORTE.juger(candidat_copie, contexte_copie)
        if verdict_copie.refus is not None:
            return refuse(_dire(verdict_copie.refus), copie)

        try:
            # La note **sur place** (même chemin), puis l'aperçu du jour : les deux
            # d'un coup, en entier ou pas du tout.
            _ecrire(coffre, chemin, texte)
            _ecrire(coffre, copie, copie_texte)
        except Exception as panne:
            # On attrape **tout**, pas seulement l'OSError : un texte inencodable
            # lève avant même d'avoir touché le fichier, et un fichier à moitié écrit
            # est justement ce qu'on refuse. On défait, et on dit le refus.
            _defaire(coffre, etats, {chemin: texte, copie: copie_texte})
            return refuse("l'écriture a échoué — la note a été remise dans son état "
                          "d'avant : %s" % panne, chemin)

        commit, motif = _committer(coffre, etats,
                                   message_d_un_acte(_titre("Compléter", nom), auteur,
                                                     outil=OUTIL_COMPLETER),
                                   lister=fichiers_du_commit,
                                   tete_attendue=tete,
                                   ecrits={chemin: texte, copie: copie_texte})
        if motif is not None:
            return refuse(motif, chemin)

        # L'acte suivant remonte à l'agent les incidents qu'il n'a pas encore vus
        # (constat 7), sous le verrou : lecture et avance du marqueur ne se croisent pas.
        incidents = remonter_les_incidents(coffre)

    return Acte(demande=demande, chemin=chemin, apercu=texte, copie=copie,
                commit=commit, refus=None, incidents=incidents)


def ranger_une_note(coffre, *, auteur: str, source: str, zone: str,
                    date=None) -> Acte:
    """Ranger une note **du vrac seul** vers ``zone`` — sans la réécrire (§7.3).

    La note garde son nom exact ; un nom déjà pris, même ailleurs dans le coffre,
    fait refuser le rangement (§6). Le registre ``notes_remplies.md`` est complété
    en ajout seul et voyage dans le **même** commit que le déplacement (§7.4).

    Un refus n'écrit rien. Si le commit échoue, le déplacement est défait : la note
    est remise dans le vrac et le registre rendu à son état d'avant — tous deux lus
    **après** la pose du verrou.
    """
    coffre = Path(coffre)
    auteur = str(auteur).strip()
    date = _le_jour(date)
    source = str(source)
    zone = str(zone)
    demande = ("ranger la note `%s` vers `%s` (auteur `%s`, le %s)"
               % (source, zone, auteur, date))

    def refuse(motif, chemin=None):
        return Acte(demande=demande, chemin=chemin, apercu=None, copie=None,
                    commit=None, refus=motif)

    # La source est jugée **avant toute lecture** : hors du coffre, la lire dirait
    # si un fichier qui n'est pas une note existe (oracle d'existence).
    motif = _refus_de_la_source(coffre, source)
    if motif is not None:
        return refuse(motif)
    motif = _refus_de_la_date(date)
    if motif is not None:
        return refuse(motif)

    nom = source.rsplit("/", 1)[-1]
    destination = PORTE.destination(zone, nom)
    registre = PORTE.destination(CONVENTION.MAINTENANCE, REGISTRE)
    dossier = _dossier_de_la_source(source)
    copie = _chemin_de_l_apercu(date, nom, dossier)

    impossible, dossier_git = _prealable(coffre)
    if impossible is not None:
        return refuse(impossible, destination)

    verrou = Verrou(dossier_git)
    with verrou as pris:
        if not pris:
            return refuse(verrou.motif, destination)

        # F5 : la tête du dépôt, prise **sous** le verrou — c'est à elle qu'on
        # comparera, juste avant le commit, pour voir venir un commit concurrent.
        tete = tete_de(coffre)
        # F4 : l'état d'avant de **chaque** chemin jugé, lu sous le verrou.
        etats = _etat_avant(coffre, (source, destination, registre, copie))
        contenu = _texte(etats[source])
        if contenu is None:
            return refuse("la note visée `%s` n'est pas là : `ranger` déplace une note "
                          "présente — il n'en crée pas" % source, destination)
        avant_registre = _texte(etats[registre])
        if avant_registre is None:
            return refuse("le registre `%s` est absent : le rangement s'inscrit dans le "
                          "registre (§7.4) — le rétablir avant de ranger" % registre,
                          destination)
        apres_registre = avant_registre + _ligne_du_registre(destination, avant_registre)

        # Un seul contexte, mais des natures **par candidat** : le contrat ne juge pas
        # de la même façon un dépôt, une complétion et une création (la copie d'aperçu).
        # On ne relâche rien — on donne à chaque candidat la nature de son geste.
        contexte = _contexte(coffre, auteur,
                             (CONVENTION.VRAC, zone, CONVENTION.MAINTENANCE),
                             nature=CONVENTION.NATURE_DEPOSER,
                             notes_du_coffre=notes_du_coffre(coffre))
        # La note (déposer) : le nom est celui du fichier visé, la source est jugée.
        candidat = PORTE.Candidat(zone, nom, contenu, nom=nom, source=source)
        verdict = PORTE.juger(candidat, contexte)
        if verdict.refus is not None:
            return refuse(_dire(verdict.refus), destination)
        if verdict.destination != destination:
            return refuse("la porte range l'acte ailleurs qu'au chemin calculé (`%s` au "
                          "lieu de `%s`) : l'écriture s'arrête là"
                          % (verdict.destination, destination), destination)
        # Le registre (compléter, ajout seul).
        verdict_registre = PORTE.juger(
            PORTE.Candidat(CONVENTION.MAINTENANCE, REGISTRE, apres_registre,
                           nom=REGISTRE, source=registre,
                           avant=avant_registre),
            contexte._replace(nature=CONVENTION.NATURE_COMPLETER))
        if verdict_registre.refus is not None:
            return refuse(_dire(verdict_registre.refus), registre)
        # La copie d'aperçu : créée si c'est le premier acte du jour sur la note **lu
        # au vrac**, ajoutée sinon — un seul aperçu par note, par dossier d'origine et
        # par jour (§7.4). Le rangement garde le dossier du vrac, sa source : remplir
        # puis classer le même jour laisse donc un seul aperçu.
        copie_texte, candidat_copie, contexte_copie = _apercu_du_jour(
            contexte, date=date, nom=nom, dossier=dossier, copie=copie,
            avant_copie=_texte(etats[copie]),
            demande=demande, geste="Ranger", chemin=destination, texte=contenu)
        verdict_copie = PORTE.juger(candidat_copie, contexte_copie)
        if verdict_copie.refus is not None:
            return refuse(_dire(verdict_copie.refus), copie)

        try:
            # Le dépôt, puis la suppression de la source, puis le registre et
            # l'aperçu : chaque fichier est posé **d'un coup**, et rien n'est
            # tronqué en chemin — un déplacement qui échoue à mi-chemin défait tout.
            _ecrire(coffre, destination, contenu)
            (coffre / source).unlink()
            _ecrire(coffre, registre, apres_registre)
            _ecrire(coffre, copie, copie_texte)
        except Exception as panne:
            # On attrape **tout**, pas seulement l'OSError : un texte inencodable
            # lève avant même d'avoir touché le fichier, et un fichier à moitié écrit
            # est justement ce qu'on refuse. On défait, et on dit le refus.
            _defaire(coffre, etats, {destination: contenu, source: None,
                                     registre: apres_registre, copie: copie_texte})
            return refuse("l'écriture a échoué — le déplacement a été défait : %s"
                          % panne, destination)

        # On commite **les deux chemins** du déplacement (la suppression et l'ajout)
        # avec le registre et la copie : le commit porte exactement l'acte.
        commit, motif = _committer(coffre, etats,
                                   message_d_un_acte(_titre("Ranger", nom), auteur,
                                                     outil=OUTIL_RANGER),
                                   lister=fichiers_du_commit,
                                   tete_attendue=tete,
                                   ecrits={destination: contenu, registre: apres_registre,
                                           copie: copie_texte})
        if motif is not None:
            return refuse(motif, destination)

        # L'acte suivant remonte à l'agent les incidents qu'il n'a pas encore vus
        # (constat 7), sous le verrou : lecture et avance du marqueur ne se croisent pas.
        incidents = remonter_les_incidents(coffre)

    return Acte(demande=demande, chemin=destination, apercu=contenu, copie=copie,
                commit=commit, refus=None, incidents=incidents)
