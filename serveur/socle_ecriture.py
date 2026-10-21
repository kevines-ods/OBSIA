"""Le socle d'écriture du coffre — ce qui est vrai de **tout** acte d'outil.

Un acte (créer un carnet, ranger une note, compléter une note) partage le même
banc : un verrou exclusif posé avant la première ligne, un préalable qui refuse
un coffre qui n'est pas un dépôt de données, un commit qui se reconnaît à sa
marque (``OBSIA-Outil`` / ``OBSIA-Auteur``, §7.4), et une vérification que le
commit porte **exactement** les fichiers annoncés — sinon l'écriture est défaite.

Le banc suppose **git ≥ 2.36** : la reprise s'appuie sur ``git hook run``, apparu
dans cette version (``git --version`` pour le vérifier). Trois objets du dossier
``.git`` ont une vie à part, et le **ménage de reprise** (``_menage_de_reprise``,
appelé quand un verrou périmé se relève) ne retire que le dernier :

- la **garde de reprise** (``.git/obsia-ecriture.garde``) — l'inode stable que
  ``flock`` réserve le temps de la reprise ; elle **ne se supprime jamais**, et
  c'est sa stabilité seule qui rend la reprise atomique ;
- le **journal des incidents** et le **marqueur des remontées**, que l'humain garde
  entiers pour son relevé ;
- l'**index dédié** d'un acte (``.git/obsia-ecriture.index-*``), qu'un acte **tué**
  peut laisser orphelin — retiré, lui, par le ménage de reprise.

Rien ici ne connaît les carnets ni les notes : c'est le socle que les deux
paliers réutilisent. Un refus n'écrit jamais rien ; une écriture qui échoue est
défaite avant que le refus ne remonte.
"""

from __future__ import annotations

import errno
import hashlib
import json
import os
import platform
import secrets
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple

try:                                        # POSIX seulement : la garde de reprise
    import fcntl
except ImportError:                         # hors POSIX, la garde n'existe pas
    fcntl = None

sys.dont_write_bytecode = True
_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import convention_des_notes as CONVENTION   # noqa: E402

try:                                        # importé comme `serveur.socle_ecriture`
    from . import carte_legale as CARTE
    from . import porte_entree as PORTE
except ImportError:                         # importé à plat : le dossier est sur le chemin
    import carte_legale as CARTE            # noqa: E402
    import porte_entree as PORTE            # noqa: E402

#: La racine du dépôt produit : ce fichier vit dans ``serveur/``.
RACINE_PRODUIT = _SCRIPTS.parent

#: Le nom de l'outil, tel qu'il s'inscrit dans la marque du commit (§7.4).
OUTIL = "ecrivain-du-coffre"

#: Les deux lignes de pied par lesquelles un acte d'outil se fait reconnaître
#: (§7.4). ``OBSIA-Outil`` est la marque proprement dite : c'est elle qui
#: distingue un commit d'outil d'un commit écrit à la main par un chef d'équipe.
MARQUE_OUTIL = "OBSIA-Outil"
MARQUE_AUTEUR = "OBSIA-Auteur"

#: Le nom du verrou d'écriture, à la racine du dépôt de données.
VERROU = "obsia-ecriture.lock"

#: Le nom de la **garde de reprise**, dans le dossier ``.git`` : un inode **stable**
#: que ``flock`` réserve le temps de relever un verrou périmé et d'en poser un neuf.
#: Elle ne se retire **jamais** — c'est sa stabilité qui rend la reprise atomique.
GARDE = "obsia-ecriture.garde"

#: Le préfixe de l'**index dédié** d'un acte, dans ``.git`` : un index par processus,
#: si bien que l'acte ne pose jamais ses fichiers dans l'index du coffre (§7.4). Un
#: acte tué entre l'ouverture de cet index et sa fermeture en laisse un **orphelin**,
#: que le **ménage de reprise** retire (``_menage_de_reprise``).
INDEX = "obsia-ecriture.index"

#: Le fichier où **chaque station** garde son identifiant d'écrivain. Il vit **hors du
#: coffre** et **hors de ``.git``** : posé dans le dépôt, il voyagerait avec les clones
#: et deux stations clonées (même ``/etc/machine-id``) se croiraient le même écrivain.
IDENTIFIANT_ECRIVAIN = "ecrivain.id"


class Acte(NamedTuple):
    """La trace d'un acte : la demande, ce qui a été écrit, et le refus s'il y en a un.

    Un acte refusé porte quand même son ``chemin`` — c'est la destination visée —
    mais ni ``apercu``, ni ``copie``, ni ``commit``. Un refus n'écrit rien : sa
    trace est cette valeur, jamais un fichier neuf (``_MAINTENANCE/`` ne reçoit que
    les écritures accomplies).
    """

    demande: str
    chemin: str | None
    apercu: str | None
    copie: str | None
    commit: str | None
    refus: str | None
    #: Les incidents du journal qu'un acte d'avant a laissés **sans que l'agent les
    #: ait encore vus** (§7.4) : l'agent les consigne à son carnet. Vide quand il n'y
    #: a rien de neuf — la valeur par défaut laisse les actes d'avant inchangés.
    incidents: tuple = ()

    @property
    def ecrit(self) -> bool:
        """L'acte a-t-il abouti ?"""
        return self.refus is None

    def trace(self) -> str:
        """La trace de la demande, lisible d'un coup d'œil."""
        lignes = ["Demande : %s" % self.demande,
                  "Chemin  : %s" % (self.chemin or "—")]
        if self.refus is not None:
            lignes.append("Refus   : %s" % self.refus)
        else:
            lignes.append("Copie   : %s" % self.copie)
            lignes.append("Commit  : %s" % self.commit)
        if self.incidents:
            lignes.append("Incidents : %d à consigner au carnet" % len(self.incidents))
        return "\n".join(lignes)


# --------------------------------------------------------------- la marque

def message_d_un_acte(titre: str, auteur: str, outil: str = OUTIL) -> str:
    """Le message de commit d'un acte d'outil (§7.4).

    La première ligne dit le **pourquoi** ; le pied porte la marque par laquelle
    l'acte se fait reconnaître dans l'historique du dépôt de données.
    """
    return "%s\n\n%s: %s\n%s: %s\n" % (titre, MARQUE_OUTIL, outil,
                                       MARQUE_AUTEUR, auteur)


def _valeur_de_marque(message: str, marque: str) -> str | None:
    """La valeur d'une ligne de pied ``<marque>: …``, ou None si elle manque."""
    for ligne in str(message).splitlines():
        tete, separateur, valeur = ligne.partition(":")
        if separateur and tete.strip().lower() == marque.lower():
            return valeur.strip() or None
    return None


def outil_du_commit(message: str) -> str | None:
    """L'outil reconnu à sa marque dans un message de commit.

    C'est ce que le §7.4 appelle « se reconnaît à une marque » : un message sans
    la marque n'est pas un acte d'outil — rend ``None``.
    """
    return _valeur_de_marque(message, MARQUE_OUTIL)


def auteur_du_commit(message: str) -> str | None:
    """L'auteur déclaré par un message d'acte, ou None si le message n'en porte pas."""
    return _valeur_de_marque(message, MARQUE_AUTEUR)


# --------------------------------------------------------------- les textes

def texte_de_la_copie(demande: str, chemin: str, apercu: str) -> str:
    """Le texte de la copie d'aperçu : la demande, le chemin, et l'aperçu exact.

    C'est la trace qu'exige le §7.4 — lisible d'un coup d'œil sur le moment, et
    plus tard par qui n'a que le coffre sous les yeux.
    """
    return ("---\ntype: maintenance\ndescription: %s\n---\n\n"
            "Ce fichier est la copie datée de l'aperçu d'une écriture (§7.4).\n\n"
            "- Demande : %s\n- Chemin : `%s`\n\n"
            "## Aperçu exact\n\n~~~markdown\n%s~~~\n"
            % (demande, demande, chemin, apercu))


# --------------------------------------------------------------- git

def _git(depot, *arguments, environnement=None):
    """Lance ``git`` dans ``depot`` et rend le résultat, sans jamais lever.

    ``environnement`` permet de viser un **index dédié** (``GIT_INDEX_FILE``) sans
    toucher à l'index du coffre — c'est ainsi que l'acte se construit à part, puis
    ne fait bouger la branche qu'en **comparaison-et-échange** (F6).
    """
    return subprocess.run(["git", "-C", str(depot), *arguments],
                          capture_output=True, text=True, check=False,
                          env=environnement)


def _branche_par_defaut(depot) -> str | None:
    """Le nom de la branche par défaut du dépôt, si on peut le nommer.

    On la lit d'abord sur la référence distante ``origin/HEAD``, puis sur la
    configuration ``init.defaultBranch``. Si ni l'une ni l'autre ne la nomme, on
    rend ``None`` — et ce ``None`` **n'autorise rien** : l'appelant refuse l'acte
    (échec fermé). Rien d'autre ne dit la branche par défaut avec certitude : le
    nom de la branche courante n'est pas une preuve, et deviner ``main`` ou
    ``master`` reviendrait à écrire sur une branche que personne n'a déclarée —
    c'est-à-dire à relâcher exactement la garantie du §7.4.
    """
    distante = _git(depot, "symbolic-ref", "--quiet", "--short",
                    "refs/remotes/origin/HEAD")
    if distante.returncode == 0 and distante.stdout.strip():
        return distante.stdout.strip().rsplit("/", 1)[-1]
    locale = _git(depot, "config", "--get", "init.defaultBranch")
    if locale.returncode == 0 and locale.stdout.strip():
        return locale.stdout.strip()
    return None


def fichiers_du_commit(depot, commit) -> tuple:
    """Les chemins que ce commit porte, triés — la vérité du dépôt, pas la nôtre.

    ``--no-renames`` : sans lui, git rapproche une suppression et un ajout en un
    ``R100 ancien nouveau`` et ``--name-only`` n'en montre que la **destination** —
    un rangement (un déplacement) paraîtrait porter un fichier de moins que les
    deux chemins jugés, et serait défait à tort. En désactivant la détection de
    renommage, un déplacement se lit ``A nouveau`` **et** ``D ancien`` : les deux
    chemins de l'acte sont là.

    ``core.quotePath=false`` : sans lui, git cite les chemins non ASCII
    (``"Id\\303\\251es/…"``), et la comparaison avec les chemins calculés ne
    reconnaîtrait plus l'acte — un dossier accentué ferait échouer toutes les
    écritures.

    ``-z`` : les chemins sont séparés par des octets nuls, ce qui laisse passer un
    nom portant un guillemet ou un retour à la ligne sans re-citation.
    """
    rendu = _git(depot, "-c", "core.quotePath=false",
                 "show", "--name-status", "--format=", "-z", "--no-renames",
                 str(commit))
    if rendu.returncode != 0:
        return ()
    champs = rendu.stdout.split("\0")
    chemins = [champs[i + 1] for i in range(0, len(champs) - 1, 2)
               if champs[i + 1]]
    return tuple(sorted(chemins))


def _blob(depot, objet) -> bytes | None:
    """Les octets d'un objet du dépôt — ``None`` s'il ne se lit pas.

    Lu **hors** de :func:`_git`, en octets et sans décodage : on compare des
    contenus, pas des textes, et un octet changé doit se voir.
    """
    rendu = subprocess.run(["git", "-C", str(depot), "cat-file", "blob", objet],
                           capture_output=True, check=False)
    return rendu.stdout if rendu.returncode == 0 else None


def _contenu_de_l_index(coffre, environnement, chemins) -> dict:
    """Ce que l'index **dédié** porte pour ces chemins — ``None`` quand il est absent.

    C'est exactement ce que ``write-tree`` mettra dans le commit. L'acte s'en sert
    pour **revérifier**, avant de construire l'objet du commit, que l'index porte bien
    ce qu'il a posé : un contenu qui a bougé entre l'ajout et le commit ne devient
    jamais un commit (F-d, §7.4). Les octets, pas le texte — la comparaison est
    exacte.
    """
    listage = _git(coffre, "ls-files", "-s", "-z", "--", *chemins,
                   environnement=environnement)
    portes = {chemin: None for chemin in chemins}
    if listage.returncode != 0:
        return portes
    for enregistrement in listage.stdout.split("\0"):
        if not enregistrement:
            continue
        meta, _, chemin = enregistrement.partition("\t")
        morceaux = meta.split()
        if chemin in portes and len(morceaux) >= 2:
            portes[chemin] = _blob(coffre, morceaux[1])
    return portes


# --------------------------------------------------------------- le verrou

#: Le journal, dans le dossier ``.git`` du dépôt de données, où se consignent les
#: incidents d'écriture — un commit étranger qui a emporté les fichiers de l'acte.
#: Il vit **hors du coffre** : un incident ne salit pas la mémoire.
INCIDENTS = "obsia-ecriture.incidents.log"

#: Le marqueur, dans le même dossier ``.git``, des incidents **déjà remontés** à un
#: agent : le journal ne se vide jamais — c'est ce compteur qui dit ce qui n'a pas
#: encore été rendu, sans quoi chaque acte re-rendrait tout le journal depuis le début.
REMONTES = "obsia-ecriture.incidents.remontes"

#: Le délai, en secondes, pendant lequel un acte attend qu'un verrou **vivant**
#: se rende : le temps qu'un acte en série finisse, jamais assez pour confondre
#: une lenteur avec une panne.
DELAI_VERROU = 10.0
PAS_D_ATTENTE = 0.02

def _machine() -> str:
    """L'identité de **cette machine**, réduite à une empreinte tronquée — jamais son nom.

    Le nom d'un hôte dit une organisation, un réseau, parfois une personne ; §9 ne
    veut **aucun** nom écrit sur le disque. On préfère donc à ``platform.node()`` une
    empreinte **tronquée** de ``/etc/machine-id`` — l'identifiant que la machine se
    donne à son installation : deux machines se distinguent encore (le refus dit
    « second écrivain »), mais aucune ne se nomme. À défaut de ``/etc/machine-id``
    (hors Linux, ou fichier vide), on empreinte le nom d'hôte : le nom ne sort pas
    pour autant, seule son empreinte.

    Ce n'est plus l'identité d'un acte : ``identifiant_d_ecrivain`` tire au hasard un
    identifiant de station, hors du dépôt, et ne se rabat ici que si cet emplacement
    est hors d'atteinte.
    """
    # Le fichier d'identité du système, **composé depuis la racine** : c'est un
    # chemin du système — le même sur toute installation Linux — et non un chemin
    # de machine, que la garde du plancher (§13) refuserait. L'écrire en un seul
    # littéral absolu de deux segments la ferait tomber sur un faux positif.
    fichier = Path("/") / "etc" / "machine-id"
    try:
        source = fichier.read_bytes().strip()
    except OSError:
        source = b""
    if not source:
        source = (platform.node() or "machine-inconnue").encode("utf-8")
    return hashlib.sha256(source).hexdigest()[:12]

#: L'identité de machine n'est plus qu'un **repli** : voir ``identifiant_d_ecrivain``.

def _chemin_de_l_identifiant() -> Path:
    """Où **cette station** garde son identifiant d'écrivain — jamais dans un dépôt.

    ``OBSIA_ECRIVAIN_ID_FICHIER`` l'emporte, pour les tests et les stations partagées ;
    à défaut, ``$XDG_STATE_HOME/obsia/`` puis ``~/.local/state/obsia/`` : un emplacement
    **hors du coffre** et **hors de ``.git``**, deux endroits qui se synchronisent entre
    clones et feraient voyager l'identifiant d'une station à l'autre.
    """
    force = os.environ.get("OBSIA_ECRIVAIN_ID_FICHIER")
    if force:
        return Path(force)
    etat = os.environ.get("XDG_STATE_HOME")
    base = Path(etat) if etat else Path.home() / ".local" / "state"
    return base / "obsia" / IDENTIFIANT_ECRIVAIN

def _lire_l_identifiant(chemin) -> str:
    """L'identifiant déjà gardé à cet emplacement, ou une chaîne vide."""
    try:
        return Path(chemin).read_text(encoding="utf-8").strip()
    except OSError:
        return ""

def _poser_l_identifiant(chemin, valeur) -> bool:
    """Poser ``valeur`` à ``chemin`` en passant par un fichier **temporaire**.

    Le fichier temporaire porte l'identifiant entier avant que le nom définitif
    n'existe : aucun lecteur ne voit donc jamais un fichier d'identité **vide**.
    C'est ce qui permet de **réparer** un fichier vide ou illisible — on le remplace
    par un identifiant frais — plutôt que de retomber, en silence, sur l'empreinte de
    ``/etc/machine-id``.

    La création se fait par ``os.link``, qui **échoue si le nom est pris** : le
    premier arrivé pose son identifiant, les suivants lisent le sien au lieu de le
    remplacer. Sans cette exclusivité, deux actes qui se créent au même instant
    tireraient deux identifiants et se prendraient l'un l'autre pour un « second
    écrivain ». Un identifiant **déjà utilisable** n'est donc jamais écrasé ; un
    fichier vide ou illisible, lui, est réparé par ``os.replace``.

    Tous les systèmes de fichiers ne connaissent pas les liens physiques (FAT, SMB,
    certains montages réseau) : là où ``os.link`` échoue **autrement** que parce que
    le nom est pris, on se replie sur une création **exclusive**
    (``os.O_CREAT | os.O_EXCL``) suivie de l'écriture — on garde ainsi un identifiant
    **tiré**, plutôt que de retomber en silence sur l'empreinte de la machine.

    Rend ``True`` si le fichier porte un identifiant, ``False`` si l'emplacement n'a
    pas pu être tenu (dossier absent et non créable, disque plein, lecture seule).
    """
    chemin = Path(chemin)
    temporaire = None
    try:
        chemin.parent.mkdir(parents=True, exist_ok=True)
        descripteur, nom = tempfile.mkstemp(dir=str(chemin.parent),
                                           prefix=chemin.name + ".", suffix=".tmp")
        temporaire = Path(nom)
        with os.fdopen(descripteur, "w", encoding="utf-8") as flux:
            flux.write(valeur + "\n")
        return _installer_l_identifiant(temporaire, chemin)
    except OSError:
        return False
    finally:
        if temporaire is not None:
            try:
                temporaire.unlink()             # après le lien ou le remplacement, il reste un nom en trop
            except OSError:
                pass

def _installer_l_identifiant(temporaire, chemin) -> bool:
    """Publier l'identifiant au nom définitif **sans jamais écraser** un identifiant.

    Le lien physique est le moyen **préféré** : il est exclusif et publie le contenu
    d'un seul geste. Là où il n'existe pas — FAT, SMB, montages sans liens physiques —
    il échoue autrement qu'en « nom déjà pris » (``EPERM``, ``ENOTSUP``, ``ENOSYS``…).
    On se replie alors sur une **réservation exclusive** du nom (``O_CREAT | O_EXCL``,
    mode ``0600``), aussitôt suivie d'un **remplacement atomique** par ``os.replace`` :
    le nom ne porte jamais un identifiant à moitié écrit. La station garde ainsi un
    identifiant tiré, au lieu de retomber en silence sur l'empreinte de la machine. Ce
    qui n'a pas pu être réparé **échoue**, jamais ne contourne.

    *Fenêtre* — entre la réservation et le remplacement, le nom existe **vide**. Un
    lecteur qui le croise peut le lire vide et tenter une réparation, et deux stations
    pourraient alors tirer deux identifiants : c'est le seul écart, borné à ces
    systèmes. ``os`` n'expose **pas** de renommage « sans écrasement » (le ``rename``
    de POSIX écrase ; ``RENAME_NOREPLACE`` n'est pas exposé) et ``os.link`` manque ici
    même : on ne fait pas mieux sans sortir de la bibliothèque standard. Le
    remplacement n'écrase jamais que **notre propre réservation**, posée un instant
    plus tôt — jamais l'identifiant d'autrui.

    Un nom **déjà pris** n'est remplacé que s'il ne porte **pas** d'identifiant
    utilisable (fichier vide ou illisible) : c'est la réparation.
    """
    try:
        os.link(str(temporaire), str(chemin))
        return True
    except FileExistsError:
        pass
    except OSError:
        # Système de fichiers sans liens physiques : on **réserve** le nom
        # exclusivement, puis on publie l'identifiant d'un remplacement atomique. La
        # réservation a réussi, le nom est donc nôtre : on n'écrase jamais l'identifiant
        # d'autrui (voir la *fenêtre* documentée plus haut).
        try:
            reserve = os.open(str(chemin),
                              os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            pass
        except OSError:
            return False
        else:
            os.close(reserve)
            os.replace(str(temporaire), str(chemin))
            return True
    # Le nom est pris : on ne remplace que ce qui ne porte **pas** d'identifiant.
    if not _lire_l_identifiant(chemin):
        os.replace(str(temporaire), str(chemin))
    return True

def _identifiant_d_ecrivain(chemin=None) -> str:
    """L'identifiant d'écrivain de cette station : **aléatoire**, tiré **une fois**.

    ``/etc/machine-id`` est partagé par tout ce qui vit sur un même hôte : deux
    stations clonées d'un même gabarit, ou deux profils d'une même machine, porteraient
    la même empreinte et se croiraient le même écrivain — le refus du « second
    écrivain » (§7.4) ne se déclencherait pas. On préfère donc un identifiant **tiré au
    hasard**, gardé à ``chemin`` (par défaut ``_chemin_de_l_identifiant()``), **hors du
    dépôt** pour ne pas voyager avec les clones.

    Un fichier présent mais **vide ou illisible** est **réparé** — un nouvel identifiant
    y est écrit — et non contourné : retomber en silence sur l'empreinte de la machine
    ramènerait exactement le défaut qu'on répare. Même raison pour la course à la
    première création : l'écriture passe par un temporaire (voir
    ``_poser_l_identifiant``), si bien qu'un second processus ne lit jamais un fichier
    vide — il lit l'identifiant du premier, qui fait foi.

    Si l'emplacement n'a pas pu être tenu (dossier impossible, lecture seule), on se
    rabat sur l'empreinte de la machine (``_machine``) : la station n'échoue pas faute
    d'avoir pu garder son identité. Cette empreinte tronquée n'est jamais un nom
    d'hôte (§9).
    """
    chemin = Path(chemin) if chemin is not None else _chemin_de_l_identifiant()
    garde = _lire_l_identifiant(chemin)
    if garde:
        return garde
    neuf = secrets.token_hex(6)
    if not _poser_l_identifiant(chemin, neuf):
        return _machine()
    # Un autre acte a pu remplacer le fichier depuis notre tirage : ce que le fichier
    # porte fait foi, pour que deux stations finissent sur le même identifiant.
    return _lire_l_identifiant(chemin) or neuf

_IDENTIFIANT_DE_LA_STATION = None

def identifiant_d_ecrivain() -> str:
    """L'identifiant d'écrivain de cette station — calculé **une fois** par processus.

    On le calcule à la demande, et non à l'import : importer le socle ne crée rien sur
    le disque, c'est le premier verrou qui matérialise l'identité de la station.
    """
    global _IDENTIFIANT_DE_LA_STATION
    if _IDENTIFIANT_DE_LA_STATION is None:
        _IDENTIFIANT_DE_LA_STATION = _identifiant_d_ecrivain()
    return _IDENTIFIANT_DE_LA_STATION

#: Le refus **historique** d'un verrou tenu, mot pour mot : un verrou illisible
#: (posé par une autre version, ou à la main) garde ce texte, parce que sa seule
#: vérité est qu'on ne peut **pas** prouver que son porteur est mort.
_MOTIF_VERROU = ("un autre acte écrit peut-être à cet instant — il n'est jamais "
                 "retiré d'office (§7.4)")

def _motif_verrou_pose(detail: str) -> str:
    """Le refus d'un verrou tenu, mis en une phrase que l'appelant peut dire."""
    return "un verrou d'écriture est déjà posé (%s) : %s" % (VERROU, detail)

def _motif_verrou_vide(chemin) -> str:
    """Le refus d'un verrou **vide** — un écrivain vivant peut être en train de le poser.

    Même décision que pour un verrou illisible : on refuse, et on ne retire **rien**
    d'office (§7.4). Mais le motif pousse plus loin, parce qu'un verrou vide n'a
    **aucune identité** à préserver : il nomme le fichier **exact** et le **geste
    humain**. Il ne dit **pas** pourquoi ce fichier est vide : sans liens physiques,
    ``_prendre`` réserve le nom **vide** un court instant avant d'y publier sa fiche,
    donc un écrivain **vivant** peut l'avoir posé à cet instant même. Supprimer le
    fichier pendant que l'écrivain le tient laisserait **deux écrivains** écrire en
    même temps : on vérifie donc qu'aucun écrivain ne tourne avant de le retirer à la
    main, et le socle ne le fait jamais lui-même.
    """
    return ("un verrou d'écriture est déjà posé (%s) : le fichier est vide — soit le "
            "reste d'un écrivain mort, soit la fiche d'un écrivain **vivant** qui est "
            "justement en train de le poser (sans liens physiques, le nom est réservé "
            "vide un court instant avant d'y publier la fiche). Aucune identité n'y est "
            "lisible, donc rien ne prouve que son porteur est mort, et le retirer pendant "
            "que l'écrivain le tient laisserait deux écrivains écrire en même temps. Il "
            "n'est jamais retiré d'office (§7.4). Vérifie qu'aucun écrivain ne tourne, "
            "puis supprime-le à la main." % chemin)

def _naissance(pid):
    """Le marqueur de naissance d'un processus — ce qui le distingue d'un pid recyclé.

    Un pid seul ne dit pas qu'un processus est **le même** : le noyau le recycle, et
    un verrou périmé pourrait sembler vivant parce qu'un processus neuf porte son
    pid. On joint donc au pid deux choses : l'instant de démarrage du processus —
    ``starttime``, en jiffies depuis le démarrage du noyau, 22ᵉ champ de
    ``/proc/<pid>/stat`` — et l'identifiant de démarrage du noyau (``boot_id``).
    Deux processus qui portent le même pid, même après un redémarrage, ne se
    confondent plus.

    Rend ``None`` quand on ne peut pas le lire — pid mort, ``/proc`` absent,
    plateforme sans ``/proc`` : l'appelant ne doit alors **pas** conclure.
    """
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        return None
    proc = Path("/") / "proc"
    try:
        stat = (proc / str(pid) / "stat").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    fin = stat.rfind(")")
    if fin < 0:
        return None
    champs = stat[fin + 1:].split()
    # Après `comm)` viennent l'état (champ 3) puis les suivants ; `starttime`
    # (champ 22) est donc l'index 19 de cette liste. On lit par index, jamais par
    # position : `comm` peut contenir espaces et parenthèses, d'où le `rfind`.
    if len(champs) <= 19:
        return None
    demarrage = champs[19]
    try:
        amorce = (proc / "sys" / "kernel" / "random" / "boot_id"
                  ).read_text(encoding="utf-8").strip()
    except OSError:
        amorce = ""
    return "%s:%s" % (amorce, demarrage)

def _processus_vivant(pid, naiss=None) -> bool:
    """Le processus ``pid`` est-il **encore** celui qui a posé le verrou ?

    ``os.kill(pid, 0)`` ne tue rien : il teste l'existence du processus. Un
    ``PermissionError`` veut dire « vivant, mais pas à moi » — on ne le confond
    **pas** avec un mort : relever le verrou d'un vivant serait l'écraser (§7.4).

    Mais un pid ne suffit pas : le noyau le recycle. Quand ``naiss`` est fourni, on
    vérifie aussi que le marqueur de naissance est le même — un pid recyclé rend
    ``False``, et le verrou est bien **périmé**. Un ``OverflowError`` (pid hors des
    bornes de l'entier du noyau) ou tout autre ``OSError`` disent mort, sans faire
    lever le socle.
    """
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except (OverflowError, ValueError):
        return False                    # un pid hors bornes n'est pas un processus
    except OSError:
        return False
    if naiss is None:
        return True
    marqueur = _naissance(pid)
    if marqueur is None:
        return True                     # on ne peut pas vérifier : on suppose vivant
    return marqueur == naiss

def _marque_de_naissance(pid):
    """L'empreinte courte du marqueur de naissance d'un pid, ou ``None``.

    C'est le **même** marqueur que le verrou (``_naissance`` : amorce de démarrage de
    la machine + ``starttime`` du processus), réduit à une empreinte pour tenir dans un
    nom de fichier. Un pid **recyclé** — le noyau le réattribue à un processus neuf —
    rend une empreinte différente : on ne prend donc **pas** l'index d'un mort pour
    celui d'un vivant.
    """
    naiss = _naissance(pid)
    if naiss is None:
        return None
    return hashlib.sha256(naiss.encode("utf-8")).hexdigest()[:8]

def _nom_de_l_index(pid) -> str:
    """Le nom de l'index dédié d'un acte : ``obsia-ecriture.index-<pid>-<marque>``.

    Le pid ne suffit pas — le noyau le recycle — on y joint donc l'empreinte du
    marqueur de naissance, la même que le verrou porte (point « pid recyclé »). Si le
    marqueur n'a pas pu être lu, on se rabat sur le nom **d'avant**, sans marqueur :
    le ménage saura qu'il ne peut pas juger la naissance.
    """
    marque = _marque_de_naissance(pid)
    return ("%s-%d-%s" % (INDEX, pid, marque) if marque else "%s-%d" % (INDEX, pid))

def _reste_de_l_index(nom: str):
    """Le ``(pid, marque)`` inscrit dans un nom d'index, ou ``None``.

    Les noms d'**avant** ce lot (``obsia-ecriture.index-<pid>``) n'ont pas de marqueur :
    ils rendent ``(pid, None)``, et le ménage les traite comme il le faisait — sur la
    seule existence du pid.
    """
    prefixe = INDEX + "-"
    if not nom.startswith(prefixe):
        return None
    morceaux = nom[len(prefixe):].split("-", 1)
    try:
        pid = int(morceaux[0])
    except ValueError:
        return None
    marque = morceaux[1] if len(morceaux) > 1 and morceaux[1] else None
    return pid, marque

def _index_encore_tenu(pid, marque) -> bool:
    """Cet index a-t-il **encore** son écrivain ? Même pid **et** même naissance.

    Un pid seul ne suffit pas : le noyau le recycle, et l'index d'un acte mort
    semblerait « en usage » parce qu'un processus neuf porte son pid. Sans marqueur
    (nom d'avant), on ne peut pas juger : on suppose l'écrivain vivant, et on ne
    retire rien.
    """
    if not _processus_vivant(pid):
        return False
    if marque is None:
        return True
    return _marque_de_naissance(pid) == marque

def _menage_de_reprise(dossier_git) -> tuple:
    """Le ménage de reprise : retirer ce qu'un écrivain **mort** a laissé d'orphelin.

    Un acte **tué** entre l'ouverture de son index dédié
    (``obsia-ecriture.index-<pid>-<marque>``) et sa fermeture en laisse un orphelin :
    il ne sert plus à personne — l'index du coffre, lui, n'a jamais été touché — et il
    s'accumulerait. On le retire, **mais seulement** quand plus aucun processus ne
    porte ce pid **avec la même naissance** : le noyau recycle les pid, et l'index d'un
    mort ne doit pas survivre au prétexte qu'un processus neuf a hérité de son numéro.
    On ne touche à rien d'autre : **jamais** la garde (dont l'inode porte le
    ``flock``), **jamais** le journal des incidents, **jamais** le marqueur des
    remontées.

    Rend le nom des restes retirés.
    """
    if dossier_git is None:
        return ()
    dossier = Path(dossier_git)
    retires = []
    for reste in sorted(dossier.glob(INDEX + "-*")):
        fiche = _reste_de_l_index(reste.name)
        if fiche is None or _index_encore_tenu(*fiche):
            continue                    # un index en cours d'usage n'est pas un orphelin
        try:
            reste.unlink()
        except OSError:
            continue
        retires.append(reste.name)
    return tuple(retires)

class GardeNonPrise(RuntimeError):
    """La garde de reprise n'a pas pu être prise — contention ou erreur.

    On la lève plutôt que d'attendre sans fin un autre relevé : la reprise **refuse**
    et le dit, sans rien retirer d'office (§7.4). Le drapeau ``contention`` dit
    **pourquoi** : ``True`` quand un autre relevé tient la garde (le motif peut parler
    de verrou déjà posé), ``False`` quand c'est une **erreur** — ouverture impossible,
    verrouillage refusé par le système de fichiers : le motif dit alors l'erreur, et
    **non** qu'un verrou est déjà posé.
    """

    def __init__(self, message, contention=True):
        super().__init__(message)
        self.contention = contention


@contextmanager
def _garde(dossier_git, delai=DELAI_VERROU, dormir=time.sleep, horloge=time.monotonic):
    """Réserve la reprise du verrou périmé, sur un inode **stable** (« flock »).

    Le verrou d'écriture dit **qui** écrit, mais il se crée puis se retire : son
    inode change à chaque acte, et deux reprises qui visaient le **même** verrou
    périmé pouvaient donc le retirer toutes les deux — la seconde retirant, sans le
    savoir, le verrou **neuf** de la première. Les deux se croyaient alors seules et
    écrivaient de front : c'est le double écrivain que le verrou existe pour empêcher
    (§7.4).

    Cette garde-ci, elle, **ne se retire jamais** : c'est son inode stable que
    ``flock`` réserve, en **exclusif**, le temps de lire le verrou, de le relever
    s'il est périmé et d'en poser un neuf — la reprise devient **atomique**, quel que
    soit l'entrelacement des processus.

    La garde se prend en **non bloquant** (``LOCK_EX|LOCK_NB``), dans une boucle
    bornée par ``delai`` : plutôt que de suspendre la reprise indéfiniment derrière un
    autre, elle lève :class:`GardeNonPrise` — l'appelant refuse et le dit.

    Seule une **contention** (``EWOULDBLOCK``/``EAGAIN`` : un autre la tient) fait
    attendre. ``EINTR`` (verrouillage interrompu par un signal) est **réessayé** au
    lieu d'être pris pour un refus. Toute **autre** erreur de verrou — ``ENOLCK`` sur
    un système de fichiers qui ne sait pas verrouiller, par exemple — refuse **tout de
    suite**, en nommant l'erreur : la traiter comme une contention ferait boucler
    jusqu'au délai et rendrait un motif faux. L'ouverture même du fichier de garde est
    dans le ``try`` : son échec donne un refus **motivé**, jamais une ``OSError``
    brute. Hors POSIX, ``fcntl`` manque : la garde laisse passer, et le socle garde
    au moins sa sûreté d'avant.
    """
    chemin = Path(dossier_git) / GARDE
    if fcntl is None:
        yield chemin
        return
    descripteur = None
    pris = False
    try:
        try:
            descripteur = os.open(str(chemin), os.O_CREAT | os.O_RDWR, 0o644)
        except OSError as erreur:
            raise GardeNonPrise(
                "la garde de reprise n'a pas pu être ouverte : %s (%s) — rien n'est "
                "retiré d'office (§7.4)"
                % (errno.errorcode.get(erreur.errno, erreur.errno), erreur),
                contention=False)
        debut = horloge()
        while not pris:
            try:
                fcntl.flock(descripteur, fcntl.LOCK_EX | fcntl.LOCK_NB)
                pris = True
            except OSError as erreur:
                if erreur.errno not in (errno.EWOULDBLOCK, errno.EAGAIN, errno.EINTR):
                    raise GardeNonPrise(
                        "la garde de reprise a échoué : %s (%s) — ce n'est pas une "
                        "contention mais une erreur ; rien n'est retiré d'office (§7.4)"
                        % (errno.errorcode.get(erreur.errno, erreur.errno), erreur),
                        contention=False)
                if horloge() - debut >= delai:
                    raise GardeNonPrise(
                        "la garde de reprise n'a pas pu être prise dans le délai de "
                        "%g s — un autre relevé la tient ; rien n'est retiré d'office "
                        "(§7.4)" % delai)
                if erreur.errno != errno.EINTR:
                    dormir(PAS_D_ATTENTE)         # EINTR : on réessaie aussitôt
        yield chemin
    finally:
        if pris:
            try:
                fcntl.flock(descripteur, fcntl.LOCK_UN)
            except OSError:
                pass
        if descripteur is not None:
            os.close(descripteur)


class Verrou:
    """Le verrou exclusif d'un acte (§7.4) — un seul écrivain à la fois.

    Le verrou se pose dans le dossier ``.git`` **réel** du dépôt de données : sa fiche
    (outil, pid, **identifiant d'écrivain** de la station (§9), heure de pose) est
    écrite dans un fichier **temporaire**, puis publiée sous son nom par ``os.link``,
    qui **échoue si le nom est pris**. Le verrou naît donc **entier ou pas du tout** :
    jamais un nom vide qu'un processus tué laisserait derrière lui — un coffre
    verrouillé à vie.

    Il **nomme son porteur** pour qu'une reprise puisse juger : un verrou tenu par
    un processus **vivant** de la même station fait **attendre** l'acte (les écritures
    passent en série), un verrou tenu par une **autre** station ou un **autre** outil
    dit un **second écrivain** et refuse sans attendre, et un verrou dont le processus
    est **mort** est **périmé** : on le relève, en le nommant, puis on reprend la main.
    """

    def __init__(self, dossier_git, delai=DELAI_VERROU, dormir=time.sleep,
                 horloge=time.monotonic, machine=None, pid=None):
        self.chemin = Path(dossier_git) / VERROU
        self.pris = False
        self._descripteur = None
        self.delai = delai
        self._dormir = dormir
        self._horloge = horloge
        self._machine = identifiant_d_ecrivain() if machine is None else machine
        self._pid = os.getpid() if pid is None else pid
        #: Le refus à dire quand le verrou n'a pas pu être pris.
        self.motif = None
        #: Le porteur du verrou **périmé** relevé, ou ``None``.
        self.perime_leve = None
        #: Ce qu'un acte mort a laissé de non commité, constaté en relevant son verrou.
        self.reste_d_acte = ()
        #: Ce que le ménage de reprise a retiré de ``.git`` (index orphelins, jamais la garde).
        self.menage = ()
        #: Le temps passé à attendre un verrou vivant.
        self.attente = 0.0
        #: Le dernier porteur vivant vu, pour le nommer dans le refus de délai.
        self._porteur_attendu = None

    def _proprietaire(self):
        """Le porteur inscrit dans le verrou, ou ``None`` s'il est illisible."""
        try:
            premiere = self.chemin.read_text(encoding="utf-8").splitlines()[0]
        except (OSError, IndexError):
            return None
        try:
            fiche = json.loads(premiere)
        except ValueError:
            return None
        if not isinstance(fiche, dict) or "pid" not in fiche:
            return None
        return fiche

    def _verrou_vide(self) -> bool:
        """Le fichier existe et, **blancs seuls retirés**, ne porte rien.

        Des blancs seuls — espaces, tabulations, sauts de ligne — comptent comme
        **vide** : ``read_text().strip()`` les efface, le fichier est donc traité
        comme vide, jamais comme « illisible ». Distingue ce **vide** d'un verrou
        simplement **illisible** (octets non décodables) : celui-ci garde le refus
        historique, celui-là peut nommer le fichier et le geste humain, puisqu'aucune
        identité n'y est à préserver. Un verrou vide n'est pas pour autant un reste
        mort : sans liens physiques, ``_prendre`` réserve le nom vide un court instant
        avant d'y publier sa fiche, donc un écrivain vivant peut l'avoir posé.
        """
        try:
            return not self.chemin.read_text(encoding="utf-8").strip()
        except OSError:
            return False

    def _prendre(self) -> bool:
        """Pose le verrou **et son porteur** d'un seul geste ; ``False`` s'il est pris.

        La fiche est écrite dans un fichier **temporaire**, puis publiée sous le nom du
        verrou par ``os.link`` : le lien **échoue si le nom est pris**, si bien que le
        verrou apparaît **entier ou pas du tout** — jamais vide. Un écrivain qui perd la
        course relit la fiche du gagnant (:meth:`_proprietaire`) au lieu de l'écraser.
        C'est ce qui garantit qu'un processus tué entre la création et l'écriture ne
        laisse pas un verrou vide et un coffre verrouillé à vie.

        Là où les liens physiques sont refusés (système de fichiers sans ``link``), le
        nom est **réservé** en ``O_CREAT|O_EXCL`` puis la fiche publiée par
        ``os.replace`` : la fenêtre où le nom existe vide se réduit à cet intervalle,
        mais elle **existe** — ce chemin produit donc lui aussi un verrou vide pendant
        un court instant, et seule la publication immédiate de la fiche le referme. Un
        verrou vide ne porte **aucune** identité : ni lu ni retiré, la reprise refuse
        (§7.4) ; son motif prévient qu'un écrivain vivant peut l'avoir posé
        (:func:`_motif_verrou_vide`).
        """
        fiche = {"outil": OUTIL, "pid": self._pid, "machine": self._machine,
                 "naiss": _naissance(self._pid),
                 "pose": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        contenu = (json.dumps(fiche) + "\n").encode("utf-8")
        temporaire = None
        try:
            descripteur, nom = tempfile.mkstemp(dir=str(self.chemin.parent),
                                                prefix=VERROU + ".", suffix=".tmp")
            temporaire = Path(nom)
            try:
                os.write(descripteur, contenu)
            finally:
                os.close(descripteur)
            try:
                os.link(str(temporaire), str(self.chemin))
            except FileExistsError:
                return False
            except OSError:
                # Pas de liens physiques : on **réserve** le nom exclusivement, puis on
                # publie la fiche d'un remplacement atomique. La réservation a réussi,
                # le nom est donc nôtre — on n'écrase jamais l'identité d'autrui ; seule
                # une fenêtre minuscule montre le nom vide, et sur un tel système le
                # socle n'a pas mieux (le ``rename`` de POSIX écrase, et ``os`` n'expose
                # pas ``RENAME_NOREPLACE``).
                try:
                    reserve = os.open(str(self.chemin),
                                      os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                except FileExistsError:
                    return False
                os.close(reserve)
                os.replace(str(temporaire), str(self.chemin))
        finally:
            if temporaire is not None:
                try:
                    temporaire.unlink()
                except OSError:
                    pass
        self.pris = True
        return True

    def _tenter(self) -> str:
        """Un tour de la reprise — « pris », « attendre », « refus » ou « relever ».

        Le tour se joue **sous la garde** : si elle ne se prend pas dans le délai,
        la reprise **refuse** en le disant (:class:`GardeNonPrise`), plutôt que
        d'attendre sans fin derrière un autre relevé.
        """
        try:
            with _garde(self.chemin.parent, delai=self.delai,
                        dormir=self._dormir, horloge=self._horloge):
                return self._un_tour()
        except GardeNonPrise as refus:
            # Contention : un autre relevé tient la garde — le motif dit « verrou déjà
            # posé ». Erreur (ouverture impossible, verrouillage refusé) : le motif dit
            # l'erreur elle-même, et **ne dit pas** qu'un verrou est déjà posé.
            self.motif = (_motif_verrou_pose(str(refus)) if refus.contention
                          else str(refus))
            return "refus"

    def _un_tour(self) -> str:
        """Le tour lui-même, la garde tenue.

        Tout se lit et s'écrit sous la garde : le verrou, son porteur, sa mort, le
        relevé d'un périmé, la pose d'un neuf. Deux reprises ne se croisent donc
        plus, quel que soit leur entrelacement : celui qui relève un verrou périmé
        pose le sien **dans le même tour de garde**, alors qu'avant il relâchait la
        garde entre les deux et pouvait se faire retirer son verrou neuf.
        """
        if self._prendre():
            return "pris"
        porteur = self._proprietaire()
        if porteur is None:
            # Verrou illisible *ou* **vide**. Ni l'un ni l'autre ne se retire d'office :
            # rien ne prouve que son porteur est mort (§7.4). Un verrou vide n'est **pas**
            # forcément un reste mort : sans liens physiques, ``_prendre`` réserve le nom
            # vide un court instant avant d'y publier sa fiche
            # (:meth:`_prendre`), donc un écrivain **vivant** peut être en train de le
            # poser. Son refus va plus loin — il nomme le fichier exact et le geste
            # humain, et prévient que le retirer pendant que l'écrivain le tient
            # laisserait deux écrivains écrire (:func:`_motif_verrou_vide`) ; un verrou
            # **illisible**, lui, garde le refus historique, mot pour mot.
            self.motif = (_motif_verrou_vide(self.chemin) if self._verrou_vide()
                          else _motif_verrou_pose(_MOTIF_VERROU))
            return "refus"
        if (porteur.get("machine") != self._machine
                or porteur.get("outil") != OUTIL):
            self.motif = _motif_verrou_pose(
                "un **second écrivain** le tient — station `%s`, outil `%s` ; il "
                "n'est jamais écrasé (§7.4)"
                % (porteur.get("machine"), porteur.get("outil")))
            return "refus"
        if _processus_vivant(porteur.get("pid"), porteur.get("naiss")):
            self._porteur_attendu = porteur
            return "attendre"
        # Le porteur est mort : le verrou est **périmé** — on le relève, en le
        # nommant, et on reprend la main (la reprise, §7.4). Ce qu'il a laissé
        # de non commité est **constaté et consigné**, jamais achevé au hasard :
        # on ne devine pas l'intention d'un mort, ce serait un écrasement.
        # Le relevé et la pose qui suit se font **sous cette même garde**.
        self.perime_leve = porteur
        self.reste_d_acte = _reste_d_acte(self.chemin.parent)
        if self.reste_d_acte:
            _consigner(self.chemin.parent,
                       "verrou périmé levé (pid %s, station `%s`) — reste d'acte "
                       "non commité : %s"
                       % (porteur.get("pid"), porteur.get("machine"),
                          " | ".join(self.reste_d_acte)))
        self.menage = _menage_de_reprise(self.chemin.parent)
        if self.menage:
            # Ce qu'on a retiré de ``.git`` est **consigné** : le ménage doit
            # remonter avec les incidents vers l'agent, pas disparaître en silence.
            _consigner(self.chemin.parent,
                       "ménage de reprise (pid %s, station `%s`) — index orphelins "
                       "retirés : %s"
                       % (porteur.get("pid"), porteur.get("machine"),
                          " | ".join(self.menage)))
        try:
            self.chemin.unlink()
        except FileNotFoundError:
            pass
        return "relever"

    def __enter__(self) -> bool:
        debut = self._horloge()
        while True:
            verdict = self._tenter()
            if verdict == "pris":
                return True
            if verdict == "refus":
                return False
            if verdict == "relever":
                continue                    # relevé sous la garde : on retente aussitôt
            self.attente = self._horloge() - debut
            if self.attente >= self.delai:
                porteur = self._porteur_attendu or {}
                self.motif = _motif_verrou_pose(
                    "un **second écrivain** (pid %s, machine `%s`) ne l'a pas rendu "
                    "dans le délai de %g s — jamais écrasé (§7.4)"
                    % (porteur.get("pid"), porteur.get("machine"), self.delai))
                return False
            self._dormir(PAS_D_ATTENTE)

    def __exit__(self, *_details):
        if self.pris:
            # La fiche a été publiée par un lien ou un remplacement : plus aucun
            # descripteur à tenir ouvert, le verrou *est* le fichier sous son nom.
            if self._descripteur is not None:
                try:
                    os.close(self._descripteur)
                except OSError:
                    pass
            try:
                self.chemin.unlink()
            except FileNotFoundError:
                pass
        return False

# --------------------------------------------------- la tête et les empreintes

def tete_de(coffre):
    """La position de tête du dépôt, ou ``None`` quand il n'y en a pas encore."""
    sortie = _git(coffre, "rev-parse", "--verify", "--quiet", "HEAD")
    if sortie.returncode != 0:
        return None
    return sortie.stdout.strip() or None

def empreinte(donnees) -> str:
    """L'empreinte SHA-256 d'un contenu — octets, ou texte encodé d'abord."""
    if isinstance(donnees, str):
        donnees = donnees.encode("utf-8")
    return hashlib.sha256(donnees).hexdigest()

def _reverifier_tete_et_empreintes(coffre, tete_attendue, ecrits):
    """Relit la tête et l'empreinte des fichiers **juste avant** de committer.

    Rend un motif de refus, ou ``None``. ``tete_attendue`` est la position de tête
    au moment où l'acte a lu : si elle a bougé, un **commit concurrent** s'est posé
    pendant l'acte — on refuse, on ne réécrit pas par-dessus. ``ecrits`` associe
    chaque chemin au texte que l'acte vient d'y poser : si le disque en porte un
    autre, un écrivain a touché le fichier entre l'écriture et le commit — même
    refus. C'est **juste avant le commit** que le contrôle a lieu : après, il serait
    trop tard pour ne pas écraser.
    """
    maintenant = tete_de(coffre)
    if maintenant != tete_attendue:
        return ("un commit concurrent est venu pendant l'acte — tête `%s` au lieu de "
                "`%s` ; l'écriture a été défaite, jamais posée par-dessus (§7.4)"
                % (maintenant, tete_attendue))
    for chemin, texte in (ecrits or {}).items():
        fichier = Path(coffre) / chemin
        try:
            sur_le_disque = fichier.read_bytes()
        except OSError:
            return ("le fichier `%s` a disparu pendant l'acte — l'écriture a été "
                    "défaite (§7.4)" % chemin)
        if empreinte(sur_le_disque) != empreinte(texte):
            return ("un autre écrivain a touché `%s` pendant l'acte — l'empreinte ne "
                    "correspond plus ; l'écriture a été défaite (§7.4)" % chemin)
    return None

def _consigner(dossier_git, texte: str) -> None:
    """Écrit une ligne au **journal des incidents** du dépôt, hors du coffre.

    L'incident n'est pas une note : il vit dans le dossier ``.git``, pour qu'une
    trace durable reste à l'humain sans jamais salir la mémoire. Si le journal ne
    s'écrit pas, on ne fait pas échouer l'acte pour autant — l'incident est déjà
    constaté, et c'est le refus qui compte.
    """
    if dossier_git is None:
        return
    ligne = "%s\t%s\n" % (datetime.now(timezone.utc).isoformat(timespec="seconds"), texte)
    try:
        with open(Path(dossier_git) / INCIDENTS, "a", encoding="utf-8") as flux:
            flux.write(ligne)
    except OSError:
        pass

def _consigner_commit_etranger(coffre, tete, portes, attendus) -> None:
    """Consigne un commit qui a emporté les fichiers de l'acte — jamais attribué."""
    _consigner(_dossier_git(coffre),
               "commit étranger\ttete=%s\tporte=%s\tattendu=%s"
               % (tete, ",".join(str(p) for p in portes),
                  ",".join(str(p) for p in attendus)))

def _reste_d_acte(dossier_git) -> tuple:
    """Ce qu'un acte mort a laissé **non commité** dans le coffre, s'il y a lieu.

    On le demande au dépôt lui-même (``git status --porcelain``) : c'est la seule
    vérité disponible quand l'acte n'a pas laissé d'état d'avant. On **constate**,
    on ne devine pas quelle était l'intention du mort — un reste qu'on achèverait
    au hasard serait un écrasement.
    """
    if dossier_git is None:
        return ()
    sortie = _git(Path(dossier_git).parent, "status", "--porcelain")
    if sortie.returncode != 0:
        return ()
    return tuple(ligne for ligne in sortie.stdout.splitlines() if ligne.strip())

def incidents_du_depot(coffre) -> tuple:
    """Les incidents consignés dans le journal du dépôt, de la plus ancienne à la plus récente."""
    dossier = _dossier_git(coffre)
    if dossier is None:
        return ()
    try:
        texte = (dossier / INCIDENTS).read_text(encoding="utf-8")
    except OSError:
        return ()
    return tuple(ligne for ligne in texte.splitlines() if ligne.strip())


def _lignes_deja_remontees(dossier_git, total: int) -> int:
    """Combien de lignes du journal ont déjà été rendues à un agent.

    Un marqueur absent ou illisible vaut zéro : au pire un incident se remonte deux
    fois, jamais zéro fois — on ne cache jamais un incident derrière un fichier abîmé.
    Un marqueur **plus grand que le journal** vaut zéro aussi : le journal a rétréci
    (tronqué, repris), on ne sait plus ce qui a été vu, et on remonte **tout** à
    nouveau plutôt que de laisser passer pour vus des incidents qu'on n'a pas rendus.
    """
    try:
        marque = int((Path(dossier_git) / REMONTES).read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return 0
    if marque > total:
        return 0
    return max(0, marque)


def _marquer_remontes(dossier_git, total: int) -> None:
    """Avance le marqueur des incidents remontés, par un remplacement atomique.

    On écrit à côté puis on renomme : un lecteur ne voit jamais un marqueur à moitié
    écrit, qui ferait re-remonter des incidents pourtant déjà consignés.
    """
    cible = Path(dossier_git) / REMONTES
    temporaire = cible.with_name(".%s.tmp" % cible.name)
    try:
        temporaire.write_text(str(total), encoding="utf-8")
        os.replace(temporaire, cible)
    except OSError:
        try:
            temporaire.unlink()
        except OSError:
            pass


def incidents_non_remontes(coffre) -> tuple:
    """Les incidents du journal qu'aucun acte n'a encore rendus à un agent.

    Le journal **ne se vide jamais** — c'est le marqueur ``REMONTES`` qui retient
    combien de ses lignes ont déjà été remontées. On rend donc ce qui vient après :
    un incident se consigne une fois au carnet, mais reste au journal, pour l'humain.
    """
    lignes = incidents_du_depot(coffre)
    dossier = _dossier_git(coffre)
    if dossier is None or not lignes:
        return ()
    return lignes[_lignes_deja_remontees(dossier, len(lignes)):]


def remonter_les_incidents(coffre) -> tuple:
    """Rend les incidents non encore remontés, **puis** les marque comme remontés.

    C'est « l'acte suivant remonte à l'agent » (§7.4) : l'écrivain l'appelle quand
    l'acte aboutit, sous le verrou — la lecture et l'avance du marqueur ne se croisent
    donc pas. Un incident rendu une fois n'est pas rendu deux fois ; le journal, lui,
    les garde toutes, et rien n'est perdu.
    """
    lignes = incidents_du_depot(coffre)
    dossier = _dossier_git(coffre)
    if dossier is None or not lignes:
        return ()
    deja = _lignes_deja_remontees(dossier, len(lignes))
    neufs = lignes[deja:]
    if neufs:
        _marquer_remontes(dossier, len(lignes))
    return neufs


# --------------------------------------------------------------- l'écriture

def _dire(refus: PORTE.Refus) -> str:
    """Un refus de la porte, mis en une phrase que l'appelant peut lire et dire."""
    return "%s : %s — %s Geste : %s" % (refus.controle, refus.constat,
                                        refus.regle, refus.geste)


def _contexte(coffre, auteur: str, zones: tuple,
              nature: str = CONVENTION.NATURE_CREER,
              notes_du_coffre: tuple = ()) -> PORTE.Contexte:
    """Le contexte de la porte, bâti par la carte légale — jamais deviné.

    Une zone que la carte ne rend pas est une zone que la porte refusera :
    l'écrivain ne se rabat jamais sur un « tout est ouvert ».

    ``nature`` dit le geste jugé (``créer``, ``déposer``, ``compléter``) : c'est
    lui qui ouvre ou ferme la matrice du §7.3. ``notes_du_coffre`` porte les
    chemins des notes du coffre entier, pour le contrôle d'unicité du §6 — un
    rangement refuse un nom déjà pris **ailleurs** que dans la zone visée.
    """
    return PORTE.Contexte(
        zones=tuple(zones),
        noms_presents=CARTE.carte_legale(coffre, tuple(zones), auteur=auteur),
        vocabulaire=CONVENTION.lire_registre(RACINE_PRODUIT),
        auteur=auteur,
        coffre=coffre,
        agents=frozenset(CONVENTION.liste_des_agents(RACINE_PRODUIT)),
        nature=nature,
        notes_du_coffre=tuple(notes_du_coffre),
    )


def _etat_avant(coffre, chemins) -> dict:
    """Le contenu **d'avant** de chaque chemin de l'acte, lu sur le disque.

    Rend un dictionnaire ``chemin -> octets`` — ou ``None`` quand le fichier n'existe
    pas encore. On lit des **octets**, pas un texte : « restauré à l'octet » doit
    être vrai, fins de ligne comprises (une note en CRLF revient en CRLF). C'est cet
    état qui permet de défaire un acte sans rien perdre : un fichier **créé**
    (``None``) se retire, un fichier **modifié, déplacé ou supprimé** se restaure
    tel quel. Sans lui, défaire une complétion effacerait la note au lieu de la
    remettre dans son état antérieur.
    """
    etats = {}
    for chemin in chemins:
        fichier = Path(coffre) / chemin
        etats[chemin] = fichier.read_bytes() if fichier.is_file() else None
    return etats


def _texte(etats_d_un_chemin):
    """Le **texte** d'un état d'avant, pour qui raisonne sur le contenu.

    Le socle garde des octets — c'est ce qui se restaure. La porte, elle, juge un
    texte (frontmatter, corps, tags) : ce passage explicite évite de confondre les
    deux, et ``None`` (fichier absent) reste ``None``.
    """
    return None if etats_d_un_chemin is None else etats_d_un_chemin.decode("utf-8")


def _poser(coffre, chemin: str, donnees: bytes) -> None:
    """Pose ces octets dans ce fichier — **en entier, ou pas du tout**.

    ``Path.write_text`` tronque le fichier visé **puis** encode : si l'encodage
    échoue (un demi-surrogate, par exemple) ou si le disque se remplit en cours de
    route, le fichier reste **vidé** — une note perdue, que ``_defaire`` ne verrait
    même pas, puisqu'il n'aurait pas été appelé. On écrit donc d'abord dans un
    fichier temporaire **du même dossier** (même système de fichiers, donc
    ``os.replace`` est atomique), et on ne met en place qu'un contenu complet.
    Tant que le remplacement n'a pas eu lieu, le fichier visé garde son ancien
    contenu — jamais d'état intermédiaire.
    """
    vise = Path(coffre) / chemin
    vise.parent.mkdir(parents=True, exist_ok=True)
    temporaire = vise.with_name(".%s.obsia-tmp" % vise.name)
    try:
        with open(temporaire, "wb") as flux:
            flux.write(donnees)
            flux.flush()
            os.fsync(flux.fileno())
        os.replace(temporaire, vise)
    except BaseException:
        try:
            temporaire.unlink()
        except OSError:
            pass
        raise


def _ecrire(coffre, chemin: str, texte: str) -> None:
    """Écrit un texte : **encodage d'abord**, puis pose atomique.

    L'encodage précède toute écriture : un texte inencodable lève **avant** que le
    fichier visé soit touché, et celui-ci garde son contenu d'avant, à l'octet près.
    """
    _poser(coffre, chemin, texte.encode("utf-8"))


def _defaire(coffre, etats, poses=None) -> tuple:
    """Défait l'écriture : désindexe l'acte, puis remet chaque chemin en son état d'avant.

    ``etats`` associe chaque chemin aux **octets** qu'il portait **avant** l'acte
    (:func:`_etat_avant`) — ou ``None`` s'il n'existait pas. On distingue alors les
    deux cas, et c'est tout l'enjeu : un fichier **créé** se retire, un fichier
    **modifié, déplacé ou supprimé** se **restaure** à l'octet près — fins de ligne
    comprises, car c'est bien l'octet qu'on a gardé, pas un texte réécrit. Les
    confondre effacerait la note que l'acte voulait compléter — une perte de données,
    pas un refus.

    ``poses`` dit ce que l'acte a **posé** sur chaque chemin — le texte qu'il y a
    écrit, ou ``None`` pour un chemin qu'il a laissé **absent** (la source d'un
    déplacement, par exemple). Le défaire devient alors **conditionnel** : on ne
    restaure un chemin que si son contenu est **encore exactement** ce que l'acte y
    a posé. Un chemin qui porte **autre chose** a été touché par un tiers depuis
    l'écriture ; le défaire n'y touche pas et le **rend** dans la tuple des laissés,
    pour qu'on le dise dans le motif — écraser le travail d'un tiers serait la faute
    même que le verrou existe pour empêcher (§7.4). Sans ``poses`` (appelant
    historique, ou pose inconnue), on restaure sans condition.

    Rend la tuple des chemins **laissés tels quels** — vide quand tout a pu être
    défait.

    On ne touche **pas** à l'index du dépôt. L'acte se construit sur un index
    **dédié** (``GIT_INDEX_FILE``, voir :func:`_committer`) : l'index réel n'a jamais
    porté l'écriture, il n'a donc rien à défaire. Le réinitialiser serait au mieux
    inutile, au pire une **perte** : il effacerait ce qu'un humain y a mis en attente
    pour ces mêmes chemins — la faute que le verrou existe pour empêcher (§7.4).

    Les dossiers que l'acte a créés sont retirés s'ils sont restés vides ; un
    dossier qui porte autre chose est laissé en place, évidemment.
    """
    chemins = tuple(etats)
    laisses = []
    for chemin, avant in etats.items():
        fichier = Path(coffre) / chemin
        try:
            actuel = fichier.read_bytes()
        except OSError:
            actuel = None
        if actuel == avant:
            continue                        # rien n'a été posé : rien à défaire
        if poses is not None:
            texte = poses.get(chemin)
            pose = texte.encode("utf-8") if texte is not None else None
            if actuel != pose:
                laisses.append(chemin)      # un tiers a écrit : on n'y touche pas
                continue
        if avant is None:
            if fichier.is_file():
                fichier.unlink()
        else:
            _poser(coffre, chemin, avant)
    for chemin in chemins:
        dossier = (Path(coffre) / chemin).parent
        while dossier != Path(coffre) and dossier.is_dir():
            try:
                dossier.rmdir()
            except OSError:
                break
            dossier = dossier.parent
    return tuple(laisses)


def _avec_les_laisses(motif: str, laisses) -> str:
    """Complète un motif de refus en nommant les chemins **laissés tels quels**.

    Un chemin laissé est un chemin où **quelqu'un d'autre a écrit** depuis l'acte :
    le défaire ne l'a pas touché, et le motif doit le dire — sans quoi l'humain
    croirait l'acte annulé alors qu'une écriture tierce est restée en place.
    """
    if not laisses:
        return motif
    return ("%s ; laissé tel quel : quelqu'un y a écrit — %s"
            % (motif, ", ".join("`%s`" % chemin for chemin in laisses)))


def _dossier_git(coffre) -> Path | None:
    """Le dossier ``.git`` **réel** du coffre — ``None`` si ce n'en est pas un dépôt.

    On le demande à git plutôt que de le supposer : dans un **worktree lié**,
    ``.git`` est un *fichier* qui désigne le vrai dossier, et le verrou ne peut pas
    se poser à côté d'un fichier.
    """
    sortie = _git(coffre, "rev-parse", "--absolute-git-dir")
    if sortie.returncode != 0:
        return None
    chemin = sortie.stdout.strip()
    return Path(chemin) if chemin else None


def _prealable(coffre) -> tuple:
    """Ce qu'il faut pouvoir dire du dépôt **avant** d'écrire quoi que ce soit.

    Ces refus-là tombent avant la première ligne écrite : un coffre qui n'est pas
    un dépôt de données, une tête détachée, ou une branche qui n'est pas la branche
    par défaut ne méritent pas qu'on écrive puis qu'on défasse. Rend ``(motif du
    refus, dossier .git réel)`` : le motif vaut ``None`` quand l'acte peut
    s'engager, et le dossier sert alors à poser le verrou.
    """
    dossier_git = _dossier_git(coffre)
    if dossier_git is None:
        return ("le coffre n'est pas un dépôt de données : git n'y trouve pas son "
                "dossier `.git` — aucun acte ne peut y être commité", None)
    branche = _git(coffre, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    if branche in ("", "HEAD"):
        return ("tête détachée : l'acte doit se poser sur la branche par défaut du "
                "dépôt de données — revenir sur une branche, puis rejouer l'écriture "
                "(§7.4)", None)
    defaut = _branche_par_defaut(coffre)
    if defaut is None:
        return ("branche par défaut introuvable : ni `origin/HEAD` ni "
                "`init.defaultBranch` ne la nomment, et l'acte se pose sur la branche "
                "par défaut pour qu'un `git revert` le défasse seul (§7.4) — nommer "
                "la branche du coffre (`git symbolic-ref refs/remotes/origin/HEAD "
                "refs/remotes/origin/<branche>`, ou `git config init.defaultBranch "
                "<branche>`), puis rejouer l'écriture", None)
    if branche != defaut:
        return ("branche `%s` au lieu de la branche par défaut `%s` : l'acte se pose sur "
                "la branche par défaut, pour qu'un `git revert` le défasse seul (§7.4)"
                % (branche, defaut), None)
    return None, dossier_git


def _committer(coffre, etats, message: str, lister=None, tete_attendue=None,
               ecrits=None, apres_l_ajout=None, avant_l_echange=None) -> tuple:
    """Ajoute l'acte, le commite, et vérifie qu'il porte exactement ses fichiers.

    ``etats`` associe chaque chemin au contenu qu'il portait **avant** l'acte
    (:func:`_etat_avant`) — ou ``None`` s'il n'existait pas. Ces chemins sont ceux
    que l'acte engage : un déplacement en engage **deux** (la source supprimée et
    la destination créée). L'état d'avant sert à **défaire sans rien perdre** : la
    note complétée reprend son texte, la note déplacée revient dans le vrac, seul
    ce qui a été créé est retiré.

    Rend ``(commit, refus)`` : le commit si l'acte est passé, sinon le refus, et
    dans ce cas l'écriture a été défaite — la branche, elle, n'a jamais bougé :
    c'est l'échange qui la fait avancer, et rien d'autre.

    ``lister`` est la façon de lire ce qu'un commit porte ; par défaut
    :func:`fichiers_du_commit`. On peut la remplacer pour mettre l'épreuve sur le
    contrôle « le commit porte exactement l'acte » sans dépendre de git — le
    contrôle lui-même ne se relâche pas pour autant.

    ``apres_l_ajout`` est une couture d'épreuve du même genre : appelée avec
    ``(coffre, environnement, chemins)`` une fois les fichiers ajoutés à l'index
    dédié, elle ne sert qu'aux épreuves. Le contrôle, lui, ne se relâche pas : on
    revérifie ensuite que l'index porte bien ce que l'acte a posé, et que la branche
    est restée la **branche par défaut** du dépôt de données (§7.4).

    ``avant_l_echange`` est la couture de la fenêtre de ``checkout`` : appelée avec
    ``(coffre, reference)`` après que la branche par défaut a été vérifiée et **juste
    avant** que la référence soit relue et l'échange tenté, elle ne sert qu'aux
    épreuves. Le contrôle tient tout seul : la branche du répertoire de travail est
    **relue** juste avant l'``update-ref``, et l'acte refuse si elle a changé.

    L'acte se construit sur un **index dédié** (``GIT_INDEX_FILE``), à part de
    l'index du coffre, et la branche n'avance que par **comparaison-et-échange**
    (``git update-ref <ref> <nouveau> <attendu>``) : la vérification de la tête et
    le déplacement de la branche ne font plus qu'un seul geste. Un commit qui
    atterrit entre la vérification et l'échange fait échouer celui-ci — l'acte est
    refusé, jamais empilé sur une tête qui n'était pas la sienne (F6, §7.4).

    **Ce qu'un crochet indexe n'entre pas dans le commit** : l'arbre est écrit
    (``write-tree``) **avant** que le crochet ``pre-commit`` ne tourne, et c'est cet
    arbre-là, par son identifiant, que ``commit-tree`` grave. Le crochet ne peut donc
    pas ajouter un fichier à l'index pour le faire entrer dans la pose — le commit
    porte **exactement** ce que l'acte a posé, rien de plus.

    **Un crochet qui réécrit les fichiers sur le disque** va plus loin : il modifie
    les fichiers **après** que l'arbre a été écrit, si bien qu'un acte réussi laisse un
    **disque différent du commit** — la pose gravée reste celle de l'arbre d'avant le
    crochet. L'écart se voit à ``git status`` ; c'est le prix de la garantie, et le
    commit, lui, reste exactement l'acte.
    """
    lire = fichiers_du_commit if lister is None else lister
    chemins = tuple(etats)
    # Ce que l'acte a **posé**, chemin par chemin : le texte écrit, ou ``None`` pour
    # un chemin laissé **absent** (la source d'un déplacement). C'est ce qui rend le
    # défaire conditionnel : un chemin qui ne porte plus la pose de l'acte a été
    # touché par un tiers, et n'est jamais écrasé (§7.4). Sans ``ecrits``, la pose
    # n'est pas connue : le défaire reste inconditionnel, comme avant.
    poses = (None if ecrits is None
             else {chemin: ecrits.get(chemin) for chemin in chemins})

    def rater(motif: str) -> tuple:
        """Défait l'écriture et rend ``(None, motif)`` — un seul chemin pour refuser."""
        return None, _avec_les_laisses(motif, _defaire(coffre, etats, poses))

    # F5 : la tête et les empreintes, relues **juste avant** le commit. Un commit
    # concurrent posé pendant l'acte, ou un fichier touché entre l'écriture et
    # ici, fait refuser l'acte — on n'écrase jamais, et on défait ce qu'on a posé.
    motif = _reverifier_tete_et_empreintes(coffre, tete_attendue, ecrits)
    if motif is not None:
        return rater(motif)

    dossier_git = _dossier_git(coffre)
    if dossier_git is None:
        return rater("le coffre n'est plus un dépôt de données — l'écriture a été "
                     "défaite")
    # F6 : l'acte se construit sur un **index dédié**, jetable, à part de l'index
    # du coffre : on n'y touche pas, et un fichier étranger qui s'y trouvait n'entre
    # jamais dans notre commit. Puis la branche n'avance que par échange.
    index = dossier_git / _nom_de_l_index(os.getpid())
    environnement = dict(os.environ, GIT_INDEX_FILE=str(index))
    try:
        depart = (["read-tree", "--empty"] if tete_attendue is None
                  else ["read-tree", tete_attendue])
        preparation = _git(coffre, *depart, environnement=environnement)
        if preparation.returncode != 0:
            return rater("l'index dédié n'a pas pu être préparé — l'écriture a été "
                         "défaite : %s"
                         % (preparation.stderr or preparation.stdout).strip())
        ajout = _git(coffre, "add", "--", *chemins, environnement=environnement)
        if ajout.returncode != 0:
            return rater("l'ajout des fichiers de l'acte a échoué — l'écriture a été "
                         "défaite : %s" % (ajout.stderr or ajout.stdout).strip())
        if apres_l_ajout is not None:
            apres_l_ajout(coffre, environnement, chemins)
        # F-d : l'index **revérifié** avant de construire l'objet. L'ajout lit le
        # disque ; si un tiers y a écrit entre notre pose et cet instant, l'index
        # porterait son texte, et le commit le graverait sans que rien ne le dise. On
        # relit donc l'index, octet par octet, contre la pose de l'acte.
        if poses is not None:
            portes_index = _contenu_de_l_index(coffre, environnement, chemins)
            for chemin in chemins:
                pose = poses[chemin]
                attendu = None if pose is None else pose.encode("utf-8")
                if portes_index.get(chemin) != attendu:
                    return rater(
                        "l'index ne porte pas ce que l'acte a posé pour `%s` — un "
                        "tiers y a écrit depuis ; l'écriture a été défaite (§7.4)"
                        % chemin)
        arbre = _git(coffre, "write-tree", environnement=environnement)
        if arbre.returncode != 0:
            return rater("l'arbre de l'acte n'a pas pu être écrit — l'écriture a été "
                         "défaite : %s" % (arbre.stderr or arbre.stdout).strip())
        # Le crochet `pre-commit`, comme le lancerait `git commit` — sur l'index
        # dédié, et sans échouer quand le dépôt n'en a pas. L'arbre est **déjà** écrit
        # ci-dessus : ce que le crochet ajouterait à l'index n'entre donc **pas** dans
        # le commit, qui porte exactement la pose de l'acte (rien de plus). Seul le
        # **refus** du crochet arrête l'acte.
        crochet = _git(coffre, "hook", "run", "--ignore-missing", "pre-commit",
                       environnement=environnement)
        if crochet.returncode != 0:
            dit = (crochet.stderr or crochet.stdout).strip() or "sans message"
            return rater("le crochet a refusé le commit — l'écriture a été défaite : %s"
                         % dit)
        arguments = ["commit-tree", arbre.stdout.strip()]
        if tete_attendue is not None:
            arguments += ["-p", tete_attendue]
        arguments += ["-m", message]
        objet = _git(coffre, *arguments)
        if objet.returncode != 0:
            return rater("l'objet du commit n'a pas pu être construit — l'écriture a "
                         "été défaite : %s" % (objet.stderr or objet.stdout).strip())
        nouveau = objet.stdout.strip()
        # Le commit **porte-t-il exactement l'acte** ? Vérifié **avant** de faire
        # bouger la branche : un commit qui n'est pas le nôtre ne devient jamais la tête.
        portes = lire(coffre, nouveau)
        if set(portes) != set(chemins):
            _consigner_commit_etranger(coffre, nouveau, sorted(portes), sorted(chemins))
            return rater("le commit ne porte pas exactement l'acte — attendu %s, porté "
                         "%s ; l'écriture a été défaite (§7.4)"
                         % (sorted(chemins), sorted(portes)))
        reference = _git(coffre, "symbolic-ref", "--quiet", "HEAD").stdout.strip()
        if not reference:
            return rater("l'acte ne s'écrit que sur une branche, pas sur une tête "
                         "détachée (§7.4) : l'écriture a été défaite")
        # F-d : la branche **comparée à la branche par défaut**, juste avant l'échange.
        # Un changement de branche pendant l'acte ferait avancer une référence qui
        # n'est pas celle qu'on croit — on refuse, comme `_prealable` l'a fait au début.
        defaut = _branche_par_defaut(coffre)
        if defaut is None:
            return rater("la branche par défaut du dépôt de données n'est plus "
                         "nommable ; l'écriture a été défaite (§7.4)")
        if reference != "refs/heads/%s" % defaut:
            return rater("la branche a changé pendant l'acte — `%s` au lieu de "
                         "`refs/heads/%s`, la branche par défaut ; l'écriture a été "
                         "défaite (§7.4)" % (reference, defaut))
        if avant_l_echange is not None:
            avant_l_echange(coffre, reference)
        # Fenêtre de `checkout` : la branche du **répertoire de travail** est **relue**
        # juste avant l'échange. Entre la vérification ci-dessus et l'`update-ref`, un
        # `git checkout` peut avoir déplacé HEAD : on ferait alors avancer une référence
        # qui n'est plus celle du répertoire de travail, et l'acte se poserait sur une
        # branche qu'on n'a pas vérifiée. On refuse plutôt que de deviner.
        relu = _git(coffre, "symbolic-ref", "--quiet", "HEAD").stdout.strip()
        if relu != reference:
            return rater("la branche du répertoire de travail a changé pendant l'acte "
                         "— `%s` au lieu de `%s` ; l'écriture a été défaite (§7.4)"
                         % (relu or "tête détachée", reference))
        # Comparaison-et-échange : la référence ne bouge que si elle est **encore**
        # celle qu'on avait vérifiée. Sinon, un commit a atterri dans la fenêtre.
        echange = _git(coffre, "update-ref", reference, nouveau,
                       tete_attendue or ("0" * 40))
        if echange.returncode != 0:
            return rater("un commit concurrent a atterri entre la vérification et le "
                         "commit — la branche n'est plus celle attendue ; l'écriture a "
                         "été défaite (§7.4)")
        # La branche a bougé : on aligne l'index **réel** sur la nouvelle tête, pour
        # ces seuls chemins — l'arbre de travail redevient propre, et `git revert`
        # pourra défaire l'acte d'un seul geste (§7.4).
        _git(coffre, "reset", "--quiet", "--", *chemins)
        return nouveau, None
    finally:
        try:
            index.unlink()
        except OSError:
            pass
