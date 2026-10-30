#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vérifie la cohérence du coffre OBSIA. N'écrit rien.

Le contrat pose des règles strictes (§5 frontmatter, §6 nommage) que rien ne
contrôlait : un index a pu affirmer pendant des mois qu'un agent disposait de
skills qu'il ne déclarait pas. Ce script confronte les fichiers entre eux.

Sort 0 si tout est cohérent, 1 sinon. Prévu pour la CI comme pour la main.

CE QU'IL REFUSE
---------------
Chacun de ces cas sort en 1 :

  · un frontmatter invalide, ou un `name` différent du nom de fichier ;
  · une liste écrite en chaîne (`skills: a, b` au lieu de tirets YAML) ;
  · une `description` repliée sur plusieurs lignes physiques ;
  · un agent déclarant un skill ou un MCP qui n'existe pas ;
  · une tâche sans section d'instruction, ou au `quand` non quoté ;
  · un chemin cité ou un lien Markdown qui ne mène nulle part ;
  · un nom de note en double dans le dépôt ;
  · un nom de premier niveau ambigu dans `0-MEMOIRES/` — un projet qui porterait
    `préférences` ou le nom d'un agent, à côté de la mémoire des agents (§6) ;
  · un fichier généré périmé (§11 du contrat) ;
  · un `AGENTS.md` écrit au-delà du plafond total de Codex (32 Kio, fichier
    global compris) : le surplus est laissé de côté, et l'agent perd des
    déclarations entières sans que rien ne le dise ;
  · un `AGENTS.md` engendré qui porterait un chemin absolu de machine : le fichier
    est synchronisé entre des postes où le coffre n'a ni le même chemin ni le même
    nom, et un `/srv/…` y est faux « partout ailleurs » — la racine se désigne par
    son sous-dossier `OBSIA/`, jamais par un chemin ;
  · un noyau du contrat (`IA/system/VAULT-CONTRACT.md`) au-delà de son plafond en
    mots, déclaré à un seul endroit — la table de `CONSTRAINTS.md`, ligne « Noyau
    du contrat », comme le plancher de tests : le noyau est lu **en entier** par
    tout agent au démarrage, donc le laisser grossir se paie à chaque séance, et
    sa taille, son plafond et l'écart s'affichent à chaque passage ;
  · une déclaration sans `module`, ou visant un module inexistant (§13) ;
  · une annexe du contrat (`IA/system/contrat/*.md`, sauf `registre.md`) au
    frontmatter invalide — `kind` autre que `contract`, `schema` non entier,
    `name` ≠ nom du fichier ou hors `NOM_VALIDE`, `description` vide, repliée
    ou poursuivie sur la ligne suivante, module absent ou inexistant (§5, §13) ;
  · un module au frontmatter invalide : `essentiel` non booléen, module non
    essentiel sans `question`, sonde au préfixe inconnu (§13.2) ;
  · un cycle de dépendances entre modules, qui boucle l'installeur ;
  · un chemin cité vers une zone que la publication vide (§13.5) ;
  · après le 2026-12-31, un vestige de la bascule : l'ancien `mémoire/` ou
    `IA/system/session-log/` du dépôt, ou un dossier `-…` à la racine du coffre
    parent (§6, transition).

Ce dernier mérite son mot. `brouillon/`, `.archive/` et
`IA/system/session-log/` ne franchissent pas la frontière du public : un
fichier de `IA/` qui les cite par leur chemin casserait l'export, loin de
l'endroit où la faute a été écrite. Nommer la note suffit. Survivent seuls
leurs `README.md`. La mémoire, elle, vit hors du dépôt (§7.1). `session-log/`
— des notes de séance, donc de la mémoire — la rejoint à la bascule
(`0-MEMOIRES/obsia/session-log/`, gelé). L'ancien `mémoire/` et lui restent
contrôlés le temps de la bascule — avertissement jusqu'au 2026-12-31, puis
erreur (voir §6, transition, et §11) — pour que rien n'y pourrisse avant la
migration, et qu'elle se finisse.

CE QUE LE PROFIL D'INSTALLATION CHANGE
--------------------------------------
Sous `mode: copie` dans `obsia.local.yml` (§13.4), le coffre est amputé : la
cible d'un chemin cité peut appartenir à un module écarté — le contrat cite
`IA/skills/cron/cron.md`, que personne n'est obligé d'installer. Trois
contrôles deviennent alors de simples avertissements : chemin cité, agent
nommé, module qu'aucune déclaration ne rejoint.

L'intégrité du catalogue se vérifie là où le catalogue est entier — dans le
dépôt de distribution, sans profil, et c'est sous ce régime que tourne la CI.
Le mode « en place » n'est pas amputé : rien n'y est retiré du disque, les
contrôles y restent complets. Le contrôle de taille du fichier `AGENTS.md` ne
s'assouplit jamais non plus : un surplus écarté reste écarté, quelle que soit
l'installation.

CE QU'IL SIGNALE SANS REFUSER
-----------------------------
Un skill qui dit de charger un skill que l'agent le déclarant ne possède pas :
la consigne est alors inapplicable pour cet agent, et la procédure s'arrête là
sans que rien ne le dise. Même chose entre modules (§13.1) : si le skill visé
appartient à un module que celui du skill citant n'entraîne pas, la consigne
tombe dans le vide chez qui n'a installé que le premier.

C'est un **avertissement et non une erreur**, pour deux raisons. La détection
repose sur le verbe employé, donc sur une heuristique, qui se trompe. Et
l'absence peut être **voulue** — une frontière de périmètre plutôt qu'un
oubli ; c'est alors au skill qui renvoie de l'énoncer, et à l'exemption
inscrite ici de porter la raison.

Un `AGENTS.md` qui approche le plafond de consignes de Codex : au-delà de
28 Kio, la marge se réduit avant les 32 Kio où le surplus est laissé de côté —
et c'est alors une erreur. Les 4 Kio de marge servent aussi à couvrir le fichier
global (`~/.codex/AGENTS.md`), que ce script ne voit pas. La taille mesurée est
celle du fichier que l'installeur écrit, marqueur compris, sur le catalogue
entier — profil ignoré, le pire cas, celui sous lequel la CI vérifie, pour ne
pas dépendre d'un `obsia.local.yml` qui n'est pas versionné.

Une **clause datée** du noyau du contrat qui a échu : une date ISO `AAAA-MM-JJ`
est la seule façon d'y écrire une échéance (« se retire au plus tard le
2026-12-31 ») ; passé le jour, l'avertissement dit la ligne et la date, parce
qu'une échéance dépassée laisse croire qu'un régime tient encore. Une date bien
formée mais inexistante (`2028-02-30`, `2026-13-01`) est dite « illisible » : on
avertit, on ne sort pas en traceback devant une faute de frappe.

PORTÉE DU CONTRÔLE DES CHEMINS
------------------------------
Un contrôle qu'on croit plus large qu'il n'est vaut moins que pas de contrôle
du tout. Celui-ci :

  · couvre les chemins **depuis la racine du dépôt** (`IA/…`, `scripts/…`) et
    les chemins **relatifs**, résolus depuis le fichier qui les cite — c'est
    cette seconde forme qui casse quand un skill passe de la forme plate à la
    forme dossier (§6) ;
  · couvre les **scripts appelés dans un bloc de code** (`python3 …`) : c'est
    là que vivent les commandes qu'une tâche exécutera vraiment. Le reste d'un
    bloc de code n'est pas contrôlé — on y écrit des arborescences d'exemple ;
  · **écarte les chemins du coffre parent** (§7 du contrat) : ils désignent des
    dossiers hors du dépôt, que ce script ne peut pas voir.

Il s'arrête à `IA/` et aux documents de la racine, parce que c'est là qu'un
chemin faux **agit** : une instruction de tâche part au déclenchement, un skill
dit d'ouvrir un fichier.

Deux dossiers en sont exemptés, et pour la même raison :

  · la mémoire du coffre parent (§7.1) — elle est **hors du dépôt**, ce script
    ne la voit pas, et c'est un récit où une note ancienne cite légitimement un
    état révolu ;
  · `IA/system/session-log/` l'est aussi, bien qu'il vive sous `IA/` : un log
    dit ce qui a été fait ce jour-là, aux chemins de ce jour-là.

Le §11 du contrat porte la raison de ces deux exemptions ; elle n'est pas
reprise ici.

Usage :
    python3 scripts/verifier_coffre.py
    python3 scripts/verifier_coffre.py --silencieux   # n'affiche que les erreurs
    python3 scripts/verifier_coffre.py --coffre <chemin> [--carnets]
        # contrôle la mémoire de ce coffre-là en mode strict ; `--carnets`
        # se limite à elle. C'est ce que le pre-commit du dépôt de données
        # du coffre déclenche (§7.1).
"""

import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from generer_prompt import RACINE_DEFAUT, fichiers_declaratifs, lire_frontmatter
from commun import depot_reel, est_un_coffre_parent as _est_un_coffre_parent

#: Les noms de la mémoire du coffre, et « qui est un agent », n'ont **qu'une**
#: définition : le moteur partagé `convention_des_notes`, que l'applicateur du
#: skill emprunte aussi. Deux copies finiraient par diverger sur les noms mêmes
#: qui séparent la mémoire vivante du chantier gelé (§6).
from convention_des_notes import (EXPERIENCES, MEMOIRES, PREFERENCES,
                                  STATUTS_CARNET, carnet_a_la_forme,
                                  carnet_du_dossier, liste_des_agents)
import modules as MOD
import verif_contrat as VCT
import verif_catalogue as VCA
from verif_catalogue import (  # noqa: F401
    AGENT_NOMME,
    CHAMPS_COMMUNS,
    CHAMPS_CONTRAT,
    CHEMIN_CITE,
    CHEMIN_RELATIF,
    COFFRE_PARENT,
    CONSIGNE_SKILL,
    CORPS_ATTENDU,
    EXECUTANTS,
    GABARIT,
    LIEN_MD,
    MODES_TACHE,
    NOM_EXEMPT_CONTRAT,
    NOM_VALIDE,
    PERMISSIONS,
    PREFIXES_SONDE,
    RENVOIS_ADMIS,
    SCRIPT_APPELE,
    TRANSPORTS,
    TYPES_SKILL,
    ZONES_PRIVEES,
    cloture,
    dans_zone_privee,
    ligne_description_brute,
    ligne_frontmatter_brute,
    vise_le_coffre_parent)
import verif_memoire as VM
from verif_memoire import NOTE_DATEE_A_PLAT, RESERVES_PROJET  # noqa: F401
from verif_memoire import _git_dans  # noqa: F401
from verif_contrat import (CLAUSE_DATEE, LIBELLE_PLAFOND_NOYAU, NOYAU,  # noqa: F401
                           TAILLE_FICHIER_AGENTS_AVERTISSEMENT,
                           TAILLE_FICHIER_AGENTS_ERREUR)

RACINE = RACINE_DEFAUT

def _coffre_par_defaut(racine: Path) -> Path:
    """`racine.parent` suffit dans un clone ordinaire, mais vaut le hangar à
    worktrees (`~/obsia-worktrees/`) depuis un worktree lié — même piège que
    documenté dans `publier.depot_reel`, dont on se sert ici pour retrouver le
    clone principal avant de prendre son parent."""
    try:
        return depot_reel(racine).parent
    except (RuntimeError, OSError):
        return racine.parent


#: Racine du coffre parent — là où vit la mémoire (§7.1). Le dépôt produit n'y
#: touche pas : ce n'est plus son coffre, et un dépôt produit n'a pas à échouer
#: parce qu'un carnet du coffre est mal formé (M5). `--coffre` la déplace pour
#: un contrôle explicite, ou depuis le pre-commit du dépôt de données.
COFFRE = _coffre_par_defaut(RACINE)

#: Les constats qui portent sur la **mémoire du coffre** ne sont des erreurs que
#: lorsqu'on vérifie le coffre lui-même. Depuis le dépôt produit, ils
#: avertissent : le produit n'est pas responsable de la mémoire, et un commit du
#: produit ne doit pas être refusé pour elle (§7.1).
MEMOIRE_STRICTE = False


erreurs: list[str] = []
avertissements: list[str] = []


def installation_reduite() -> bool:
    """Ce coffre est-il une installation par copie, donc amputée (§13.4) ?

    Trois contrôles n'ont de sens que sur le catalogue complet : un chemin
    cité, un agent nommé, un module qu'aucune déclaration ne rejoint. Dans une
    installation par copie, la cible d'un chemin peut appartenir à un module
    écarté — le contrat cite `IA/skills/cron/cron.md` que personne n'est obligé
    d'installer. Les y traiter en erreurs ferait échouer toute installation
    partielle, c'est-à-dire exactement ce que le §13 rend légitime.

    L'intégrité du catalogue se vérifie là où le catalogue est entier : dans le
    dépôt de distribution, et c'est ce que fait la CI, qui n'a pas de profil.
    Le mode « en place » n'est pas réduit — rien n'y est retiré du disque — et
    garde donc les contrôles complets.
    """
    import modules as _mod                       # tardif, comme dans generer_prompt
    profil = _mod.lire_profil(RACINE)
    return bool(profil) and profil.get("mode") == "copie"


REDUITE = installation_reduite()


def signaler(chemin, message):
    """Erreur sur un coffre complet, simple avertissement sur une copie réduite."""
    if REDUITE:
        avertir(chemin, message + " — installation réduite, la cible appartient "
                                  "peut-être à un module écarté (§13.4)")
    else:
        erreur(chemin, message)


def erreur(chemin, message):
    erreurs.append("%s : %s" % (chemin, message))


def avertir(chemin, message):
    avertissements.append("%s : %s" % (chemin, message))


def signaler_memoire(chemin, message):
    """Signale un constat de mémoire : erreur dans le coffre, avertissement ici.

    La même faute — un carnet mal nommé, un `archives/` qui traîne — n'a pas le
    même poids selon qui regarde. Dans le coffre c'est une erreur, parce que la
    mémoire est le sujet ; depuis le dépôt produit c'est un avertissement, parce
    qu'un commit du produit n'a pas à porter la mémoire des autres (§7.1).
    """
    if MEMOIRE_STRICTE:
        erreur(chemin, message)
    else:
        avertir(chemin, "(mémoire du coffre) " + message)


#: Tolérance de bascule (§11) : le chantier dont la clôture les retire, et la
#: date écrite au plus tard de laquelle elles doivent avoir disparu. Tant qu'il
#: dure, la mémoire vit sous deux formes à la fois et le contrôle doit rester
#: utilisable : ses tolérances avertissent — même sur le coffre lui-même — et le
#: message porte la date. **Passé cette date, les mêmes formes refusent** : c'est
#: elle qui force la clôture si elle traîne, au lieu d'un avertissement éternel.
BASCULE = "souverainete-des-donnees"
BASCULE_FIN = "2026-12-31"


def signaler_bascule(chemin, message, aujourdhui=None):
    """Une tolérance de bascule (§11) : avertissement, puis erreur après le jour dit.

    Le chantier est nommé et la date de fin écrite. Tant que la bascule dure,
    l'ancienne forme avertit sans interrompre — la mémoire vit sous deux formes,
    et exiger la disparition de celle qu'on migre empêcherait de finir. Passé
    `BASCULE_FIN`, le même vestige fait échouer le contrôle : un avertissement
    éternel ne se lit plus, et une tolérance qu'on ne paie pas ne se retire
    jamais. `aujourdhui` n'existe que pour le test, comme dans
    `bascule_echue`.
    """
    if bascule_echue(aujourdhui):
        erreur(chemin, "bascule non achevée : %s — la tolérance a expiré le %s "
                       "(§11, chantier « %s »)" % (message, BASCULE_FIN, BASCULE))
        return
    avertir(chemin, "%s (tolérance de bascule — chantier « %s », à retirer au plus "
                    "tard le %s, §11)" % (message, BASCULE, BASCULE_FIN))


def bascule_echue(aujourdhui=None) -> bool:
    """La tolérance de bascule est-elle échue (§6, transition) ?

    `aujourdhui` n'existe que pour le test : il permet de se placer après la
    date sans attendre le jour dit.
    """
    if aujourdhui is None:
        aujourdhui = date.today()
    return aujourdhui > date.fromisoformat(BASCULE_FIN)


def est_un_coffre_parent() -> bool:
    """`COFFRE` est-il un coffre parent, ou le dossier qui contient un clone ?

    Sans marqueur, ce n'est pas un coffre : rien à lui demander, et faire
    échouer la CI au motif qu'un dossier `-…` traîne chez un inconnu serait
    abusif. Les marqueurs de `modules.MARQUEURS_COFFRE` incluent les anciens
    noms `-…` : un coffre qui n'a pas fini de migrer reste reconnu.
    """
    return COFFRE.is_dir() and any(
        (COFFRE / marqueur).exists() for marqueur in MOD.MARQUEURS_COFFRE)


def emplacements_anciens():
    """Ce qui devait avoir disparu à la fin de la bascule (§6, transition).

    Dans le dépôt produit : l'ancien `mémoire/`, et `IA/system/session-log/` —
    des notes de séance, donc de la mémoire, qui rejoignent `0-MEMOIRES/obsia/
    session-log/` (gelé) en même temps que lui. Dans le coffre parent : tout
    dossier de premier niveau resté à la forme `-…`. Ne rend que ce qui existe.
    """
    anciens = []
    for ancien in (RACINE / "mémoire", RACINE / "IA" / "system" / "session-log"):
        if ancien.is_dir():
            anciens.append(ancien)
    if est_un_coffre_parent():
        anciens += [entree for entree in sorted(COFFRE.iterdir())
                    if entree.is_dir() and entree.name.startswith("-")]
    return anciens


def verifier_bascule(aujourdhui=None):
    """§6 (transition) : passé le jour dit, l'ancienne forme devient une erreur.

    Tant que la bascule dure, `signaler_bascule` avertit sans interrompre — la
    mémoire vit sous deux formes à la fois, et exiger l'ancienne disparue
    empêcherait de finir la migration. Une tolérance qu'on ne paie pas ne se
    retire pas : au-delà de `BASCULE_FIN`, ce qui reste de l'ancienne forme fait
    échouer le contrôle, et le message dit ce qu'il reste à achever.
    """
    if not bascule_echue(aujourdhui):
        return
    for ancien in emplacements_anciens():
        erreur(designation(ancien),
               "bascule non achevée : `%s` devait avoir disparu au plus tard le "
               "%s (§6, transition — chantier « %s »)"
               % (ancien.name, BASCULE_FIN, BASCULE))


# ------------------------------------------------------------------ frontmatter

# Contrôles du catalogue : leur code vit dans `verif_catalogue.py`.

def _contexte_catalogue():
    """L'état que les contrôles du catalogue lisent, pris au moment de l'appel."""
    return SimpleNamespace(racine=RACINE, coffre=COFFRE, reduite=REDUITE,
                           erreur=erreur, avertir=avertir, signaler=signaler)


def verifier_fichier(chemin: Path, genre: str, champs_requis: tuple = CHAMPS_COMMUNS,
                     emplacement: str | None = None):
    return VCA.verifier_fichier(_contexte_catalogue(), chemin, genre, champs_requis, emplacement)


def verifier_mcp(dossier: Path):
    return VCA.verifier_mcp(_contexte_catalogue(), dossier)


def verifier_taches(dossier: Path, agents: list[dict], *,
                    exclure: frozenset = frozenset()):
    return VCA.verifier_taches(_contexte_catalogue(), dossier, agents, exclure=exclure)


def verifier_taches_coffre(taches_produit: list[dict], agents: list[dict]):
    return VCA.verifier_taches_coffre(_contexte_catalogue(), taches_produit, agents)


def verifier_references(agents, skills):
    return VCA.verifier_references(_contexte_catalogue(), agents, skills)


def verifier_portee_des_renvois(agents, skills):
    return VCA.verifier_portee_des_renvois(_contexte_catalogue(), agents, skills)


def verifier_forme_dossier(dossier: Path, genre: str):
    return VCA.verifier_forme_dossier(_contexte_catalogue(), dossier, genre)


def verifier_agents_nommes(agents):
    return VCA.verifier_agents_nommes(_contexte_catalogue(), agents)


def verifier_chemins_cites():
    return VCA.verifier_chemins_cites(_contexte_catalogue())


def verifier_citations_de_memoire():
    return VCA.verifier_citations_de_memoire(_contexte_catalogue())


def verifier_modules(dossier: Path):
    return VCA.verifier_modules(_contexte_catalogue(), dossier)


def verifier_profil(modules: list[dict]):
    return VCA.verifier_profil(_contexte_catalogue(), modules)


def module_declare(chemin, module, noms: set):
    return VCA.module_declare(_contexte_catalogue(), chemin, module, noms)


def verifier_appartenance(modules, agents, skills, mcp, taches):
    return VCA.verifier_appartenance(_contexte_catalogue(), modules, agents, skills, mcp, taches)


def verifier_annexes_contrat(dossier: Path, modules: list[dict]):
    return VCA.verifier_annexes_contrat(_contexte_catalogue(), dossier, modules)


def verifier_renvois_entre_modules(modules, skills):
    return VCA.verifier_renvois_entre_modules(_contexte_catalogue(), modules, skills)


def verifier_derives():
    return VCA.verifier_derives(_contexte_catalogue())


# Contrôles de la mémoire : leur code vit dans `verif_memoire.py`.

def _contexte():
    """L'état que les contrôles de la mémoire lisent, pris au moment de l'appel :
    les tests remplacent `RACINE`, `COFFRE` ou `date` dans ce module."""
    return SimpleNamespace(racine=RACINE, coffre=COFFRE, erreur=erreur,
                           avertir=avertir, signaler_memoire=signaler_memoire,
                           signaler_bascule=signaler_bascule)


def verifier_unicite_des_noms():
    return VM.verifier_unicite_des_noms(_contexte())


def designation(chemin: Path):
    return VM.designation(_contexte(), chemin)


def emplacements_de_projets():
    return VM.emplacements_de_projets(_contexte())


def verifier_carnets():
    return VM.verifier_carnets(_contexte())


def parcourir_projet(dossier: Path, projet: str, niveau: int):
    return VM.parcourir_projet(_contexte(), dossier, projet, niveau)


def verifier_carnets_dun_projet(dossier: Path, projet: str):
    return VM.verifier_carnets_dun_projet(_contexte(), dossier, projet)


def verifier_carnet(chemin: Path, projet: str):
    return VM.verifier_carnet(_contexte(), chemin, projet)


def noms_d_agents_declares():
    return VM.noms_d_agents_declares(_contexte())


def verifier_noms_de_memoire():
    return VM.verifier_noms_de_memoire(_contexte())


def verifier_depot_de_donnees():
    return VM.verifier_depot_de_donnees(_contexte())


# Contrôles du contrat : leur code vit dans `verif_contrat.py` ; ces relais
# leur passent la racine et les deux compteurs du vérificateur.

def verifier_taille_du_fichier_agents():
    VCT.verifier_taille_du_fichier_agents(RACINE, erreur, avertir)


def plafond_du_noyau(chemin=None):
    return VCT.plafond_du_noyau(RACINE, chemin)


def mots_du_noyau(chemin=None) -> int:
    return VCT.mots_du_noyau(RACINE, chemin)


def verifier_taille_du_noyau():
    return VCT.verifier_taille_du_noyau(RACINE, erreur)


def verifier_regle_des_secrets():
    return VCT.verifier_regle_des_secrets(RACINE, erreur)


def verifier_clauses_datees_du_noyau(aujourdhui=None):
    # Le jour se lit ici : `verifier_dates.py` ne remplace `date` que dans ce module.
    if aujourdhui is None:
        aujourdhui = date.today()
    VCT.verifier_clauses_datees_du_noyau(RACINE, avertir, aujourdhui)


def verifier_chemins_du_prompt():
    VCT.verifier_chemins_du_prompt(RACINE, erreur)


# ----------------------------------------------------------------------- main

AIDE = """\
verifier_coffre.py [--coffre <chemin>] [--carnets] [--silencieux]

Sans argument, contrôle le dépôt produit (index, agents, skills, modules,
citations) et, s'il existe, la mémoire du coffre parent — signalée sans
interrompre. Avec `--coffre <chemin>`, la mémoire de ce coffre-là est contrôlée
en mode strict (ses écarts deviennent des erreurs) ; `--carnets` se limite à
elle. C'est ce que le pre-commit du dépôt de données déclenche (§7.1).
"""


def analyser_arguments(argv: list[str]) -> dict:
    """`--coffre <chemin>`, `--carnets`, `--silencieux` — tout le reste est refusé."""
    options = {"coffre": None, "carnets": False, "silencieux": False}
    reste = []
    index = 0
    while index < len(argv):
        argument = argv[index]
        if argument == "--coffre":
            if index + 1 >= len(argv):
                raise ValueError("`--coffre` attend un chemin")
            options["coffre"] = argv[index + 1]
            index += 2
            continue
        if argument == "--carnets":
            options["carnets"] = True
        elif argument == "--silencieux":
            options["silencieux"] = True
        else:
            reste.append(argument)
        index += 1
    if reste:
        raise ValueError("argument inconnu : %s" % " ".join(reste))
    return options


def main(argv=None) -> int:
    global COFFRE, MEMOIRE_STRICTE
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        options = analyser_arguments(argv)
    except ValueError as echec:
        print("verifier_coffre.py : %s\n\n%s" % (echec, AIDE), file=sys.stderr)
        return 2

    silencieux = options["silencieux"]
    if options["coffre"]:
        COFFRE = Path(options["coffre"]).resolve()
        MEMOIRE_STRICTE = True

    if options["carnets"]:
        verifier_carnets()
        verifier_noms_de_memoire()
        verifier_depot_de_donnees()
        verifier_bascule()
        if avertissements and not silencieux:
            print("Avertissements (%d) :" % len(avertissements))
            for a in avertissements:
                print("  · %s" % a)
        if erreurs:
            print("\nMémoire du coffre incohérente — %d erreur(s) :" % len(erreurs),
                  file=sys.stderr)
            for e in erreurs:
                print("  ✗ %s" % e, file=sys.stderr)
            print("\nLes numéros de § renvoient à IA/system/VAULT-CONTRACT.md.",
                  file=sys.stderr)
            return 1
        if not silencieux:
            print("Mémoire du coffre cohérente.")
        return 0

    dossier_agents = RACINE / "IA" / "agents"
    dossier_skills = RACINE / "IA" / "skills"

    agents = [fm for fm in (verifier_fichier(p, "agent")
                            for p in fichiers_declaratifs(dossier_agents)) if fm]
    skills = [fm for fm in (verifier_fichier(p, "skill")
                            for p in fichiers_declaratifs(dossier_skills)) if fm]

    verifier_forme_dossier(dossier_agents, "agent")
    verifier_forme_dossier(dossier_skills, "skill")

    if not agents:
        erreur("IA/agents/", "aucun agent valide trouvé")
    if not skills:
        erreur("IA/skills/", "aucun skill valide trouvé")

    mcp = verifier_mcp(RACINE / "IA" / "MCP")
    taches = verifier_taches(RACINE / "IA" / "tâches", agents)
    verifier_taches_coffre(taches, agents)
    modules = verifier_modules(RACINE / "IA" / "system" / "modules")
    verifier_annexes_contrat(RACINE / "IA" / "system" / "contrat", modules)
    verifier_profil(modules)
    verifier_appartenance(modules, agents, skills, mcp, taches)
    verifier_renvois_entre_modules(modules, skills)
    verifier_references(agents, skills)
    verifier_portee_des_renvois(agents, skills)
    verifier_agents_nommes(agents)
    verifier_chemins_cites()
    verifier_citations_de_memoire()
    verifier_unicite_des_noms()
    verifier_carnets()
    verifier_noms_de_memoire()
    verifier_bascule()
    if options["coffre"]:
        verifier_depot_de_donnees()
    verifier_derives()
    verifier_taille_du_fichier_agents()
    verifier_chemins_du_prompt()
    ligne_du_noyau = verifier_taille_du_noyau()
    verifier_clauses_datees_du_noyau()
    ligne_des_secrets = verifier_regle_des_secrets()
    if ligne_du_noyau and not silencieux:
        print(ligne_du_noyau)
    if ligne_des_secrets and not silencieux:
        print(ligne_des_secrets)

    if avertissements and not silencieux:
        print("Avertissements (%d) :" % len(avertissements))
        for a in avertissements:
            print("  · %s" % a)

    if erreurs:
        print("\nCoffre incohérent — %d erreur(s) :" % len(erreurs), file=sys.stderr)
        for e in erreurs:
            print("  ✗ %s" % e, file=sys.stderr)
        print("\nLes numéros de § renvoient à IA/system/VAULT-CONTRACT.md.", file=sys.stderr)
        return 1

    if not silencieux:
        regime = " (installation réduite — contrôles du catalogue assouplis, §13.4)" \
            if REDUITE else ""
        print("Coffre cohérent : %d module(s), %d agent(s), %d skill(s), "
              "%d tâche(s), index à jour.%s"
              % (len(modules), len(agents), len(skills), len(taches), regime))
    return 0


if __name__ == "__main__":
    sys.exit(main())
