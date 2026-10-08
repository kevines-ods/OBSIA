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

import contextlib
import io
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from generer_prompt import (RACINE_DEFAUT, chemins_absolus,
                            fichiers_declaratifs, lire_frontmatter,
                            prompt_du_coffre)
from installer import contenu_agents
import modules as MOD

RACINE = RACINE_DEFAUT

#: Racine du coffre parent — là où vit la mémoire (§7.1). Le dépôt produit n'y
#: touche pas : ce n'est plus son coffre, et un dépôt produit n'a pas à échouer
#: parce qu'un carnet du coffre est mal formé (M5). `--coffre` la déplace pour
#: un contrôle explicite, ou depuis le pre-commit du dépôt de données.
COFFRE = RACINE.parent

#: Les constats qui portent sur la **mémoire du coffre** ne sont des erreurs que
#: lorsqu'on vérifie le coffre lui-même. Depuis le dépôt produit, ils
#: avertissent : le produit n'est pas responsable de la mémoire, et un commit du
#: produit ne doit pas être refusé pour elle (§7.1).
MEMOIRE_STRICTE = False

CHAMPS_COMMUNS = ("schema", "kind", "name", "description", "read_only")
CHAMPS_CONTRAT = ("schema", "kind", "name", "description")   # ni read_only, ni type
NOM_EXEMPT_CONTRAT = "registre.md"      # l'index du dossier, pas une annexe
NOM_VALIDE = re.compile(r"^[^\W_]+(?:-[^\W_]+)*$", re.UNICODE)   # minuscules-et-tirets, accents admis
TYPES_SKILL = ("core", "outil")

# AGENTS.md est lu par Codex, qui ne retient en tout que 32 Kio de consignes :
# le fichier global (~/.codex/AGENTS.md) et ceux du projet comptent **ensemble**.
# Au-delà, le surplus est laissé de côté — sans erreur, sans avertissement ;
# l'agent perd des agents et des skills entiers sans que rien ne le dise.
# On mesure le pire cas — le catalogue entier, sans profil, comme la CI — et on
# avertit dès 28 Kio : les 4 Kio de marge couvrent un fichier global, et
# laissent le temps de réduire avant que le surplus ne soit écarté.
TAILLE_FICHIER_AGENTS_AVERTISSEMENT = 28 * 1024     # 28 672 o
TAILLE_FICHIER_AGENTS_ERREUR = 32 * 1024            # 32 768 o

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
#: utilisable — ses tolérances avertissent, même sur le coffre lui-même, et le
#: message porte la date : c'est elle qui force la clôture si elle traîne.
BASCULE = "souverainete-des-donnees"
BASCULE_FIN = "2026-12-31"


def signaler_bascule(chemin, message):
    """Une tolérance de bascule (§11) : toujours un avertissement, jamais une erreur.

    Le chantier est nommé et la date de fin écrite : à sa clôture — au plus tard
    le jour dit — la tolérance tombe avec l'ancienne forme qu'elle excusait.
    """
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

def ligne_frontmatter_brute(chemin: Path, cle: str) -> str | None:
    """La ligne `<cle>:` telle qu'écrite dans le frontmatter.

    `lire_frontmatter()` normalise (déquote, convertit) ; certains contrôles
    portent au contraire sur l'écriture littérale — un scalaire replié, des
    guillemets absents.
    """
    dans_fm = False
    prefixe = cle + ":"
    for ligne in chemin.read_text(encoding="utf-8").splitlines():
        if ligne.strip() == "---":
            if dans_fm:
                return None
            dans_fm = True
            continue
        if dans_fm and ligne.startswith(prefixe):
            return ligne
    return None


def ligne_description_brute(chemin: Path) -> str | None:
    """La ligne `description:` telle qu'écrite, pour détecter un scalaire replié."""
    return ligne_frontmatter_brute(chemin, "description")


def verifier_fichier(chemin: Path, genre: str, champs_requis: tuple = CHAMPS_COMMUNS,
                     emplacement: str | None = None) -> dict | None:
    """Frontmatter d'une fiche déclarative — agent, skill ou annexe du contrat.

    `champs_requis` dit quels champs doivent être **présents** : les annexes du
    contrat n'ont ni `read_only` — elles ne s'exécutent pas — ni `type`, réservé
    aux skills. Tout le reste est vérifié dans tous les cas, quel que soit
    l'appelant : `kind` égal au genre, `name` qui suit le nom du fichier et
    `NOM_VALIDE`, `schema` entier, `description` non vide et d'une seule ligne
    physique, `skills` et `mcp` en listes si elles sont là. Un `module` non vide
    est également exigé, hors `champs_requis` : il se vérifie pour toute fiche
    (§13). Réutiliser cette garde vaut mieux que la réécrire — deux copies d'un
    contrôle finissent par diverger.
    """
    fm = lire_frontmatter(chemin)
    rel = chemin.relative_to(RACINE)

    if fm is None:
        erreur(rel, "frontmatter absent ou non fermé")
        return None

    for champ in champs_requis:
        if champ not in fm:
            erreur(rel, "champ obligatoire manquant : `%s` (§5)" % champ)

    if fm.get("kind") != genre:
        erreur(rel, "`kind: %s` alors que le fichier est dans %s (§5)"
               % (fm.get("kind"),
                  emplacement or ("le dossier des %ss" % genre)))

    nom = fm.get("name")
    if nom:
        if nom != chemin.stem:
            erreur(rel, "`name: %s` ≠ nom du fichier `%s` (§5)" % (nom, chemin.stem))
        if not NOM_VALIDE.match(nom):
            erreur(rel, "`name: %s` — attendu : minuscules et tirets, sans espace (§5)" % nom)

    if "read_only" in champs_requis and not isinstance(fm.get("read_only"), bool):
        erreur(rel, "`read_only` doit valoir true ou false (§5)")

    if not isinstance(fm.get("schema"), int):
        erreur(rel, "`schema` doit être un entier (§5)")

    # description : présente, sur une seule ligne physique
    desc = fm.get("description")
    brute = ligne_description_brute(chemin)
    if not desc:
        erreur(rel, "`description` vide ou absente (§5)")
    elif desc.strip() in (">", "|", ">-", "|-"):
        erreur(rel, "`description` est un scalaire replié YAML — non géré par "
                    "lire_frontmatter(), la valeur devient « %s ». Une seule ligne physique."
               % desc.strip())
    elif brute and brute.rstrip().endswith((":", ">", "|")):
        erreur(rel, "`description` semble se poursuivre sur la ligne suivante — "
                    "une seule ligne physique est acceptée")

    if not fm.get("module"):
        erreur(rel, "champ obligatoire manquant : `module` (§13)")

    if genre == "skill" and fm.get("type") not in TYPES_SKILL:
        erreur(rel, "`type: %s` — attendu `core` ou `outil` (§5)" % fm.get("type"))

    for champ in ("skills", "mcp"):
        if champ in fm and not isinstance(fm[champ], list):
            erreur(rel, "`%s` vaut une chaîne, pas une liste — une entrée par ligne "
                        "précédée d'un tiret (§5)" % champ)

    if fm:
        fm["_chemin"] = rel
    return fm


# ---------------------------------------------------------------------- checks

TRANSPORTS = ("stdio", "http")
PERMISSIONS = ("normal", "elevated")


def verifier_mcp(dossier: Path) -> list[dict]:
    """Frontmatter des fichiers de IA/MCP/ (§5).

    Format distinct de celui des agents et des skills : pas de `read_only`,
    mais `transport` et `permission`.
    """
    resultats = []
    for chemin in sorted(dossier.glob("*.md")) if dossier.is_dir() else []:
        fm = lire_frontmatter(chemin)
        rel = chemin.relative_to(RACINE)
        if fm is None:
            erreur(rel, "frontmatter absent ou non fermé")
            continue
        for champ in ("schema", "kind", "name", "description", "type",
                      "transport", "permission"):
            if champ not in fm:
                erreur(rel, "champ obligatoire manquant : `%s` (§5)" % champ)
        if fm.get("kind") != "mcp":
            erreur(rel, "`kind: %s` attendu `mcp` (§5)" % fm.get("kind"))
        if fm.get("name") and fm["name"] != chemin.stem:
            erreur(rel, "`name: %s` ≠ nom du fichier `%s` (§5)" % (fm["name"], chemin.stem))
        if fm.get("transport") not in TRANSPORTS:
            erreur(rel, "`transport: %s` — attendu %s (§5)"
                   % (fm.get("transport"), " ou ".join(TRANSPORTS)))
        if fm.get("permission") not in PERMISSIONS:
            erreur(rel, "`permission: %s` — attendu %s (§5)"
                   % (fm.get("permission"), " ou ".join(PERMISSIONS)))
        fm["_chemin"] = rel
        resultats.append(fm)
    return resultats


MODES_TACHE = ("agent", "commande")
EXECUTANTS = ("local", "harness")
CORPS_ATTENDU = {"agent": "## Instruction", "commande": "## Commande"}


def verifier_taches(dossier: Path, agents: list[dict]) -> list[dict]:
    """Frontmatter et corps des fichiers de IA/tâches/ (§5, §12).

    Une tâche déclare une intention planifiée. Trois erreurs la rendent
    silencieusement inopérante — d'où trois contrôles :
      · `quand` non quoté : `*/15 * * * *` est une ancre YAML invalide, tout
        lecteur YAML réel refuse le fichier ;
      · corps sans `## Instruction` (ou `## Commande`) : rien à déclencher ;
      · `agent` inconnu : la tâche vise quelqu'un qui n'existe pas (§1).
    """
    resultats = []
    noms_agents = {a["name"] for a in agents if a.get("name")}
    for chemin in sorted(dossier.glob("*.md")) if dossier.is_dir() else []:
        fm = lire_frontmatter(chemin)
        rel = chemin.relative_to(RACINE)
        if fm is None:
            erreur(rel, "frontmatter absent ou non fermé")
            continue

        for champ in ("schema", "kind", "name", "description",
                      "mode", "quand", "fuseau", "exécutant", "actif"):
            if champ not in fm:
                erreur(rel, "champ obligatoire manquant : `%s` (§5)" % champ)

        if fm.get("kind") != "tâche":
            erreur(rel, "`kind: %s` attendu `tâche` (§5)" % fm.get("kind"))
        if fm.get("name") and fm["name"] != chemin.stem:
            erreur(rel, "`name: %s` ≠ nom du fichier `%s` (§5)" % (fm["name"], chemin.stem))
        if fm.get("name") and not NOM_VALIDE.match(fm["name"]):
            erreur(rel, "`name: %s` — attendu : minuscules et tirets, sans espace (§5)"
                   % fm["name"])
        if not isinstance(fm.get("schema"), int):
            erreur(rel, "`schema` doit être un entier (§5)")
        if not isinstance(fm.get("actif"), bool):
            erreur(rel, "`actif` doit valoir true ou false (§5)")
        if not fm.get("description"):
            erreur(rel, "`description` vide ou absente (§5)")

        mode = fm.get("mode")
        if mode not in MODES_TACHE:
            erreur(rel, "`mode: %s` — attendu %s (§5)" % (mode, " ou ".join(MODES_TACHE)))

        # `quand` : cron à 5 champs, écrit entre guillemets
        brute = ligne_frontmatter_brute(chemin, "quand")
        if brute:
            valeur = brute.partition(":")[2].strip()
            if not (valeur.startswith(('"', "'")) and valeur.endswith(('"', "'"))):
                erreur(rel, "`quand` doit être écrit entre guillemets (§5) — sans eux, "
                            "une expression comme */15 * * * * est une ancre YAML invalide")
        quand = fm.get("quand")
        if isinstance(quand, str) and len(quand.split()) != 5:
            erreur(rel, "`quand: %s` — attendu cron à 5 champs "
                        "(minute heure jour-du-mois mois jour-de-semaine) (§5)" % quand)
        elif isinstance(quand, int):
            erreur(rel, "`quand` doit être une chaîne entre guillemets, pas un nombre (§5)")

        executant = fm.get("exécutant")
        if executant not in EXECUTANTS:
            erreur(rel, "`exécutant: %s` — attendu %s (§5). Sans lui, la "
                        "réconciliation ne sait pas où la tâche doit tourner et "
                        "peut créer un doublon (§12)."
                   % (executant, " ou ".join(EXECUTANTS)))
        elif executant == "harness" and mode == "commande":
            avertir(rel, "`mode: commande` avec `exécutant: harness` — un "
                         "planificateur distant n'atteint pas les fichiers de la "
                         "machine. Vérifier que ce harness tourne bien en local.")

        fuseau = fm.get("fuseau")
        if isinstance(fuseau, str) and "/" not in fuseau and fuseau != "UTC":
            avertir(rel, "`fuseau: %s` — attendu un identifiant IANA (`Europe/Paris`) "
                         "ou `UTC`" % fuseau)

        if mode == "agent":
            vise = fm.get("agent")
            if not vise:
                erreur(rel, "`mode: agent` sans champ `agent` (§5)")
            elif vise not in noms_agents:
                erreur(rel, "vise l'agent `%s`, qui n'a pas de fichier dans "
                            "IA/agents/ (§1)" % vise)
        elif mode == "commande" and fm.get("agent"):
            avertir(rel, "`mode: commande` avec un champ `agent` — ignoré au "
                         "déclenchement, à retirer")

        attendu = CORPS_ATTENDU.get(mode)
        if attendu and attendu not in chemin.read_text(encoding="utf-8"):
            erreur(rel, "corps sans section `%s` — la tâche ne déclenche rien (§5)"
                   % attendu)

        if not fm.get("module"):
            erreur(rel, "champ obligatoire manquant : `module` (§13)")

        fm["_chemin"] = rel
        resultats.append(fm)
    return resultats


def verifier_references(agents, skills):
    """Un agent ne déclare que des skills et des MCP qui existent."""
    connus = {s["name"] for s in skills if s.get("name")}
    mcp_connus = {p.stem for p in (RACINE / "IA" / "MCP").glob("*.md")} \
        if (RACINE / "IA" / "MCP").is_dir() else set()

    for a in agents:
        for s in a.get("skills", []):
            if s not in connus:
                erreur(a["_chemin"], "déclare le skill `%s`, qui n'existe pas dans IA/skills/" % s)
        for m in a.get("mcp", []):
            if m not in mcp_connus:
                erreur(a["_chemin"], "déclare le MCP `%s`, qui n'existe pas dans IA/MCP/" % m)

    utilises = {s for a in agents for s in a.get("skills", [])}
    for s in skills:
        if s.get("name") and s["name"] not in utilises:
            avertir(s["_chemin"], "skill déclaré par aucun agent")

    actifs = {m for a in agents for m in a.get("mcp", [])}
    for p in sorted((RACINE / "IA" / "MCP").glob("*.md")) if (RACINE / "IA" / "MCP").is_dir() else []:
        if p.stem not in actifs:
            avertir(p.relative_to(RACINE),
                    "MCP déclaré par aucun agent — inutilisable en l'état (§10.2)")


# « charger X », « relève de X » : une consigne, pas une simple mention.
# Insensible à la casse : une consigne s'écrit aussi bien en tête de phrase
# (« Charger `x`. ») qu'en cours de ligne, et le verbe y garde son sens.
CONSIGNE_SKILL = re.compile(r"(?:charger|c'est|relève de)\s+`([^\W_][\w-]{2,39})`",
                            re.IGNORECASE)

# Frontières assumées : le skill visé est volontairement hors de portée de cet
# agent, et le skill qui renvoie vers lui l'énonce. Les exemptions vivent ici,
# dans le vérificateur, jamais dans le frontmatter du fichier contrôlé : un
# fichier qui se déclare lui-même dispensé annule le contrôle.
RENVOIS_ADMIS = {
    ("diagnostic-linux", "remediation-linux", "batisseur"):
        "constater n'implique pas le droit de corriger la machine ; "
        "diagnostic-linux énonce la frontière et rend la main",
}


def verifier_portee_des_renvois(agents, skills):
    """Un skill renvoie-t-il vers un skill hors de portée de son agent ?

    Le §10.2 fait choisir PARMI les skills déclarés par l'agent. Un skill qui
    dit « charger `X` » alors que l'agent qui le déclare n'a pas `X` donne une
    consigne inapplicable : la procédure s'arrête là sans que rien ne le dise.

    Avertissement et non erreur : la détection repose sur le verbe employé,
    donc sur une heuristique. Et l'absence peut être **voulue** — une
    frontière de périmètre plutôt qu'un oubli ; c'est alors au skill de
    l'énoncer.
    """
    connus = {s["name"]: s for s in skills if s.get("name")}
    for nom, fm in connus.items():
        proprios = [a for a in agents if nom in a.get("skills", [])]
        if not proprios:
            continue
        chemin = RACINE / fm["_chemin"]
        try:
            texte = chemin.read_text(encoding="utf-8")
        except OSError:
            continue
        vises = {m.group(1) for m in CONSIGNE_SKILL.finditer(texte)} & set(connus)
        for vise in sorted(vises - {nom}):
            hors = [a["name"] for a in proprios if vise not in a.get("skills", [])]
            hors = [h for h in hors
                    if (nom, vise, h) not in RENVOIS_ADMIS]
            if hors:
                avertir(fm["_chemin"],
                        "dit de charger `%s`, que %s ne déclare pas — consigne "
                        "inapplicable pour lui, ou frontière à énoncer (§10.2)"
                        % (vise, " et ".join("`%s`" % h for h in hors)))


def verifier_forme_dossier(dossier: Path, genre: str):
    """Un skill en forme dossier doit porter son point d'entrée (§5).

    Vérifie aussi que les fichiers extraits dans `references/` sont bien cités
    depuis le corps : un fichier qu'on ne sait pas exister n'est jamais lu —
    c'est la règle de `createur-de-skill`.
    """
    if not dossier.is_dir():
        return
    for sous in sorted(dossier.iterdir()):
        if not sous.is_dir() or sous.name.startswith("."):
            continue
        entree = sous / (sous.name + ".md")
        rel = sous.relative_to(RACINE)
        if not entree.is_file():
            erreur(rel, "dossier de %s sans point d'entrée `%s.md` (§5). "
                        "Le point d'entrée porte le nom du dossier, pas `SKILL.md`."
                   % (genre, sous.name))
            continue

        corps = entree.read_text(encoding="utf-8")
        for annexe in sorted((sous / "references").glob("**/*")):
            if not annexe.is_file():
                continue
            if annexe.name not in corps:
                avertir(rel, "`references/%s` n'est cité nulle part dans `%s.md` — "
                             "un fichier qu'on ne sait pas exister n'est jamais lu"
                        % (annexe.relative_to(sous / "references").as_posix(), sous.name))


# Formes réelles sous lesquelles un nom d'agent apparaît dans le coffre :
#   l'agent `assistant`   ·   un agent « untel »   ·   agent[untel] --> …
# Le nom capturé doit ressembler à un nom : lettres, chiffres, tirets, espaces.
# Exclure « : » et « | » écarte `read_only: false` et les séparateurs de tableau.
AGENT_NOMME = re.compile(
    r"agents?\s*[«\"`\[]\s*([^\W\d_][\w \-]{1,39}?)\s*[»\"`\]]", re.UNICODE)


def verifier_agents_nommes(agents):
    """§1 : seul un agent qui a son fichier dans IA/agents/ peut être nommé.

    Nommer un agent avant qu'il existe le fait exister dans les têtes — c'est
    ainsi qu'un agent fantôme s'est installé dans ce coffre pendant des mois.
    """
    declares = {a["name"] for a in agents if a.get("name")}
    for chemin in sorted(RACINE.rglob("*.md")):
        if any(part.startswith(".") for part in chemin.relative_to(RACINE).parts):
            continue
        rel = chemin.relative_to(RACINE)
        try:
            texte = chemin.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for cite in {m.group(1) for m in AGENT_NOMME.finditer(texte)}:
            if cite in declares:
                continue
            # contre-exemples de nommage de dossier : ne désignent personne
            if re.fullmatch(r"agents?\s*\d+", cite) or cite.startswith(("nom-", "<")):
                continue
            signaler(rel, "nomme l'agent `%s`, qui n'a pas de fichier dans "
                          "IA/agents/ (§1 : seul un agent existant peut être nommé)" % cite)


# Un chemin cité entre accents graves, ou une cible de lien Markdown.
# La mémoire est sortie du dépôt (§7.1) : elle ne s'y cite plus — sauf l'ancien
# `mémoire/`, resté le temps de la bascule, dont les chemins cités restent donc
# contrôlés. Cette ligne disparaît avec le dossier, à la fin de la migration du
# chantier `souverainete-des-donnees`.
CHEMIN_CITE = re.compile(
    r"`((?:IA|scripts|brouillon|mémoire)/[^`\s]+\.(?:md|py|json|yml|sh))`")
# Un chemin relatif cité — `../system/VAULT-CONTRACT.md`. C'est la forme
# employée partout dans le coffre, et celle qui casse quand un skill passe de
# la forme plate à la forme dossier (§6) : elle se résout depuis le fichier
# qui la cite, pas depuis la racine.
CHEMIN_RELATIF = re.compile(r"`(\.\.?/[^`\s]+\.(?:md|py|json|yml|sh))`")
# Un script réellement appelé dans un bloc de code. Le reste d'un bloc n'est
# pas contrôlé — on y écrit des arborescences d'exemple — mais une commande,
# elle, s'exécute : c'est ce que l'instruction d'une tâche fera au
# déclenchement.
SCRIPT_APPELE = re.compile(r"(?:python3?|bash|sh)\s+([\w./\-]+\.(?:py|sh))")
LIEN_MD = re.compile(r"\]\(([^)]+)\)")
GABARIT = re.compile(r"[<>*…{]|AAAA|MM-JJ")          # chemins d'exemple, pas des cibles

# Dossiers du coffre parent (§7.1) : hors du dépôt, donc invisibles d'ici.
# Un chemin qui les vise n'est pas cassé, il désigne autre chose. Source unique :
# `modules.MARQUEURS_COFFRE`, partagée avec `publier.py`.
COFFRE_PARENT = MOD.MARQUEURS_COFFRE


def vise_le_coffre_parent(chemin: str) -> bool:
    """Le chemin désigne-t-il un dossier du coffre parent plutôt que le dépôt ?"""
    segments = [s for s in chemin.split("/") if s not in ("", ".", "..")]
    return bool(segments) and segments[0] in COFFRE_PARENT


def verifier_chemins_cites():
    """Un chemin cité dans `IA/` ou à la racine doit exister.

    Déplacer un skill en forme dossier laisse derrière lui des chemins qui ne
    mènent plus nulle part — dont, une fois, celui que l'instruction d'une
    tâche demandait d'ouvrir au déclenchement. Rien ne le signalait.

    Le contrôle s'arrête à `IA/` et aux documents de la racine : là, un chemin
    faux **agit**. La mémoire est hors du dépôt (§7.1) : ses chemins n'y sont
    plus cités, et un récit y cite de toute façon légitimement un état révolu
    ou reproduit un extrait d'index.

    `IA/system/session-log/` est écarté pour la même raison, bien qu'il vive
    sous `IA/` : un log dit ce qui a été fait ce jour-là, aux chemins de ce
    jour-là. Le corriger après un déplacement lui ferait annoncer la création
    d'un fichier à un endroit qui n'existait pas encore — on falsifierait le
    récit pour faire taire le contrôle. Un log n'agit jamais : personne ne
    l'ouvre pour exécuter ce qu'il décrit.

    Trois formes sont contrôlées, parce que trois formes cassent :

      · le chemin depuis la racine du dépôt — `IA/skills/x.md` ;
      · le chemin **relatif**, résolu depuis le fichier qui le cite — c'est
        celui qui casse quand un skill change de forme (§6), et il est resté
        des mois hors du filet ;
      · le **script appelé dans un bloc de code** — le reste d'un bloc est
        illustratif, mais une commande s'exécute.

    Les chemins du coffre parent (§7.1) sont écartés : ils désignent des
    dossiers hors du dépôt, que ce script ne peut pas voir.
    """
    cibles = list((RACINE / "IA").rglob("*.md")) + list(RACINE.glob("*.md"))
    for chemin in sorted(cibles):
        rel = chemin.relative_to(RACINE)
        if any(part.startswith(".") for part in rel.parts):
            continue
        if rel.parts[:3] == ("IA", "system", "session-log"):
            continue
        texte = chemin.read_text(encoding="utf-8")
        hors_code = re.sub(r"```.*?```", "", texte, flags=re.S)

        for cite in sorted({m.group(1) for m in CHEMIN_CITE.finditer(hors_code)}):
            if GABARIT.search(cite) or (RACINE / cite).exists():
                continue
            signaler(rel, "cite le chemin `%s`, qui n'existe pas" % cite)

        # chemins relatifs : résolus depuis le fichier qui les cite
        for cite in sorted({m.group(1) for m in CHEMIN_RELATIF.finditer(hors_code)}):
            if GABARIT.search(cite) or vise_le_coffre_parent(cite):
                continue
            if (chemin.parent / cite).exists():
                continue
            signaler(rel, "cite le chemin relatif `%s`, qui ne mène nulle part "
                        "depuis ce fichier (§6)" % cite)

        # scripts appelés dans un bloc de code : eux s'exécutent
        for bloc in re.findall(r"```.*?```", texte, flags=re.S):
            for script in sorted({m.group(1) for m in SCRIPT_APPELE.finditer(bloc)}):
                if GABARIT.search(script) or vise_le_coffre_parent(script):
                    continue
                depuis_racine = (RACINE / script).exists()
                depuis_fichier = (chemin.parent / script).exists()
                if depuis_racine or depuis_fichier:
                    continue
                signaler(rel, "appelle le script `%s` dans un bloc de code, "
                            "et ce fichier n'existe pas (§11)" % script)

        for m in LIEN_MD.finditer(hors_code):
            cible = m.group(1).split("#")[0].strip()
            if (not cible or "://" in cible or cible.startswith("mailto:")
                    or GABARIT.search(cible)):
                continue
            if not (chemin.parent / cible).exists():
                signaler(rel, "lien Markdown cassé : `%s`" % cible)


#: Ce que `publier.py` vide au passage vers le public (§13.5). Un fichier
#: publié qui cite un chemin d'ici mènerait nulle part dans la distribution.
#: La mémoire est sortie du dépôt (§7.1) : elle n'est plus citée — sauf l'ancien
#: `mémoire/`, resté le temps de la bascule, qui reste donc dans la liste des
#: zones qu'un fichier publié ne cite pas. Ces deux lignes disparaissent avec le
#: dossier, à la fin de la migration du chantier `souverainete-des-donnees`.
ZONES_PRIVEES = ("brouillon", ".archive", "IA/system/session-log", "mémoire")


def dans_zone_privee(chemin: str) -> bool:
    return any(chemin == zone or chemin.startswith(zone + "/")
               for zone in ZONES_PRIVEES)


def verifier_citations_de_memoire():
    """§13.5 : un fichier publié ne cite pas un chemin qui ne sera pas publié.

    `publier.py` vide `brouillon/`, `.archive/` et `IA/system/session-log/` au
    passage vers le public. Un chemin qui les vise depuis `IA/` ou depuis la
    racine mène donc nulle part dans la distribution — et l'export échoue, loin
    de l'endroit où la faute a été écrite. Autant la voir ici.

    Ce n'est pas une interdiction de *renvoyer* à une note privée : la nommer
    suffit, et c'est déjà la règle du §7.5 pour les rétroliens — un lien par
    nom survit aux déplacements, un lien par chemin casse.
    """
    for chemin in sorted(RACINE.rglob("*.md")):
        rel = chemin.relative_to(RACINE)
        if any(part.startswith(".") for part in rel.parts):
            continue
        if len(rel.parts) > 1 and rel.parts[0] != "IA":
            continue                      # même portée que le contrôle des chemins
        if rel.parts[:3] == ("IA", "system", "session-log"):
            continue                      # un log dit les chemins de son jour (§11)
        try:
            texte = chemin.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for cite in sorted({m.group(1) for m in CHEMIN_CITE.finditer(texte)}):
            if GABARIT.search(cite):      # chemin d'exemple, pas une cible
                continue
            if not dans_zone_privee(cite):
                continue
            if cite.endswith("/README.md"):
                continue
            erreur(rel, "cite le chemin `%s`, qui ne sera pas publié : cette "
                        "zone est vidée à la publication. Nommer la note "
                        "suffit (§13.5)." % cite)


def verifier_unicite_des_noms():
    """§6 : les noms de notes doivent être uniques dans tout le coffre parent.

    On ne peut pas voir le coffre parent depuis ici ; on vérifie donc l'unicité
    à l'intérieur d'OBSIA, qui en est la condition nécessaire.
    """
    banals = {"sommaire.md", "README.md"}          # légitimement répétés
    vus: dict[str, list[str]] = {}
    for chemin, sous, fichiers in os.walk(RACINE):
        sous[:] = [d for d in sous
                   if not d.startswith(".") and d not in ("scripts", "assets")]
        for f in fichiers:
            if f.endswith(".md") and f not in banals:
                vus.setdefault(f, []).append(
                    str(Path(chemin).joinpath(f).relative_to(RACINE)))
    for nom, chemins in sorted(vus.items()):
        if len(chemins) > 1:
            erreur(nom, "nom de note en double, les rétroliens deviennent ambigus (§6) : %s"
                   % ", ".join(chemins))


# ------------------------------------------------------------------- carnets

DATE_CARNET = re.compile(r"^\d{4}-\d{2}-\d{2}-")
NOTE_DATEE_A_PLAT = re.compile(r"^\d{4}-\d{2}-\d{2}-.*\.md$")
STATUTS_CARNET = ("en cours", "en attente", "clos")
RESERVES_PROJET = ("carnets", "documents", "code")


def designation(chemin: Path) -> Path:
    """Chemin affiché : relatif au dépôt produit s'il y est, relatif au coffre
    parent sinon — la mémoire vit là (§7.1), et un rapport doit rester lisible."""
    bases = []
    for base in (RACINE, COFFRE, RACINE.parent):
        if base not in bases:
            bases.append(base)
    for base in bases:
        try:
            return chemin.relative_to(base)
        except ValueError:
            continue
    return chemin


def emplacements_de_projets():
    """Les dossiers de projets à contrôler, dans l'ordre : le coffre parent
    (`0-PROJETS/`, et son ancien nom `-PROJETS/`), puis l'ancien
    `mémoire/projets` du dépôt tant que la bascule dure (§6, transition).

    Ne rend que ce qui existe : un clone de la CI n'a pas de coffre parent."""
    candidats = [COFFRE / "0-PROJETS", COFFRE / "-PROJETS",
                 RACINE / "mémoire" / "projets"]
    return [c for c in candidats if c.is_dir()]

def verifier_carnets():
    """§6 : forme des carnets, un seul niveau de chantier, transition.

    - un carnet est `0-PROJETS/<projet>/carnets/AAAA-MM-JJ-<projet>-<sujet>.md`,
      avec `agent:`, `projet:` et `statut:` — trois chaînes non vides, le
      `projet:` égal au nom du dossier, et un `statut:` dans
      `en cours | en attente | clos` ;
    - un chantier est un dossier de plus, avec **ses** `carnets/`, `documents/`
      et son résumé ; ses carnets portent son nom dans `projet:` — jamais de
      vision, jamais de chantier dans un chantier ;
    - les carnets du jour hors chantier restent dans `0-PROJETS/<projet>/carnets/`,
      et s'y nomment du nom du projet ;
    - un sous-dossier dans un `carnets/` est refusé : un carnet est un fichier ;
    - la mémoire vit dans le coffre parent (§7.1) : on la contrôle là où elle
      est — `0-PROJETS/` du coffre parent, son ancien nom `-PROJETS/`, et
      l'ancien `mémoire/projets` du dépôt tant que la bascule dure. Un clone de
      la CI n'a aucun de ces dossiers : il n'y a alors rien à contrôler ;
    - tant que la bascule dure (§11), une note datée à plat et un dossier
      `archives/` (au niveau du projet comme sous `carnets/`) restent tolérés :
      avertissement, jamais erreur — même sur le coffre lui-même, sans quoi la
      migration serait impossible à finir.
    """
    for projets in emplacements_de_projets():
        for projet in sorted(projets.iterdir()):
            if not projet.is_dir() or projet.name.startswith("."):
                continue
            parcourir_projet(projet, projet.name, 0)

def parcourir_projet(dossier: Path, projet: str, niveau: int):
    """`niveau` 0 pour un projet, 1 pour un de ses chantiers ; au-delà, refus (§6).

    Au niveau 0, `carnets/` porte les carnets du jour écrits hors chantier. Au
    niveau 1, le dossier est un **chantier** : il a ses propres `carnets/`, ses
    `documents/`, son résumé, et rien de plus — pas de vision, et pas un
    chantier dans un chantier.
    """
    for entree in sorted(dossier.iterdir()):
        if entree.name in ("sommaire.md", "README.md"):
            continue
        if entree.is_file():
            if NOTE_DATEE_A_PLAT.match(entree.name):
                signaler_bascule(designation(entree),
                        "ancienne forme : note datée à plat, à migrer vers "
                        "`carnets/` (§6)")
            continue
        if entree.name == "carnets":
            verifier_carnets_dun_projet(entree, projet)
        elif entree.name == "archives":
            signaler_bascule(designation(entree),
                    "`archives/` n'existe plus : un chantier clos part, dossier "
                    "entier, dans `0-MEMOIRES/` (§6)")
        elif entree.name in RESERVES_PROJET:
            continue
        elif niveau >= 1:
            erreur(designation(entree),
                   "chantier imbriqué — un chantier ne contient pas de chantier (§6)")
        else:
            parcourir_projet(entree, entree.name, 1)

def verifier_carnets_dun_projet(dossier: Path, projet: str):
    for carnet in sorted(dossier.iterdir()):
        if carnet.name in ("sommaire.md", "README.md"):
            continue
        if carnet.is_dir():
            if carnet.name == "archives":
                signaler_bascule(designation(carnet),
                        "`carnets/archives/` n'existe plus : un chantier clos "
                        "part dans `0-MEMOIRES/` (§6)")
            else:
                erreur(designation(carnet),
                       "sous-dossier dans `carnets/` — un carnet est un fichier (§6)")
            continue
        if carnet.is_file() and carnet.name.endswith(".md"):
            verifier_carnet(carnet, projet)

def verifier_carnet(chemin: Path, projet: str):
    rel = designation(chemin)
    if not DATE_CARNET.match(chemin.name):
        signaler_memoire(rel, "carnet mal nommé — attendu "
                              "`AAAA-MM-JJ-<projet>-<sujet>.md` (§6)")
    elif not chemin.name.startswith(chemin.name[:11] + projet + "-"):
        signaler_memoire(rel, "carnet mal nommé : `<projet>` ne correspond pas au "
                              "dossier `%s` (§6)" % projet)
    fm = lire_frontmatter(chemin)
    if fm is None:
        signaler_memoire(rel, "carnet sans frontmatter fermé (§6)")
        return
    for champ in ("agent", "projet", "statut"):
        valeur = fm.get(champ)
        if not isinstance(valeur, str) or not valeur.strip():
            signaler_memoire(rel, "carnet `%s:` vide ou absent (§6)" % champ)
    statut = fm.get("statut")
    if isinstance(statut, str) and statut.strip() and statut not in STATUTS_CARNET:
        signaler_memoire(rel, "carnet `statut: %s` — attendu `en cours`, "
                              "`en attente` ou `clos` (§6)" % statut)
    projet_fm = fm.get("projet")
    if isinstance(projet_fm, str) and projet_fm.strip() and projet_fm != projet:
        signaler_memoire(rel, "carnet `projet: %s` ne correspond pas au dossier "
                              "`%s` (§6)" % (projet_fm, projet))


# --------------------------------------------------------- dépôt de données

def _git_dans(chemin: Path, *arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(chemin), *arguments],
                          capture_output=True, text=True)


# ------------------------------------------------------- noms de 0-MEMOIRES

MEMOIRES = "0-MEMOIRES"
PREFERENCES = "préférences"
LECONS = "expériences"


def noms_d_agents_declares() -> set:
    """Le nom de chaque agent déclaré : sous `0-MEMOIRES/`, il est réservé (§6)."""
    dossier = RACINE / "IA" / "agents"
    if not dossier.is_dir():
        return set()
    return {chemin.stem for chemin in fichiers_declaratifs(dossier)}


def verifier_noms_de_memoire():
    """§6 : dans `0-MEMOIRES/`, deux mémoires ne se confondent pas.

    Le dossier porte la mémoire des agents — `préférences/`, vivante, et
    `<nom-agent>/expériences/`, vivante aussi — **et** les chantiers clos, gelés.
    Un projet qui s'appellerait `préférences` ou porterait le nom d'un agent
    rendrait les deux indistinguables : c'est une erreur de nommage, pas un
    détail de rangement.

    Faute de lire une intention, la règle se contrôle par la **forme** :
    `préférences/` ne contient que des notes, la mémoire d'un agent n'a qu'un
    `expériences/` de notes, et tout autre dossier est un projet gelé — donc il
    porte au moins un chantier. Le contrôle ne tourne que sur le coffre parent
    (§7.1) : un clone de la CI n'a pas de `0-MEMOIRES/`.
    """
    racine_memoires = COFFRE / MEMOIRES
    if not racine_memoires.is_dir():
        return
    reserves = {PREFERENCES} | noms_d_agents_declares()
    for entree in sorted(racine_memoires.iterdir()):
        if entree.name.startswith("."):
            continue
        if not entree.is_dir():
            if entree.name not in ("README.md", "sommaire.md"):
                signaler_memoire(entree, "`%s/` n'accueille que des dossiers : "
                                         "`%s/`, la mémoire d'un agent, ou un projet gelé (§6)"
                                 % (MEMOIRES, PREFERENCES))
            continue
        if entree.name == PREFERENCES:
            for intrus in sorted(entree.iterdir()):
                if intrus.is_dir():
                    signaler_memoire(intrus, "`%s/%s/` est la mémoire des agents : elle ne contient "
                                             "que des notes `<sujet>.md`. Un projet ne peut pas porter "
                                             "ce nom (§6)" % (MEMOIRES, PREFERENCES))
            continue
        if entree.name in reserves:
            lecons = entree / LECONS
            if not lecons.is_dir():
                signaler_memoire(entree, "`%s/%s/` est l'espace mémoire de cet agent : il ne contient "
                                         "que `%s/`. Un projet ne peut pas porter le nom d'un agent (§6)"
                                 % (MEMOIRES, entree.name, LECONS))
            elif [e for e in sorted(lecons.iterdir()) if e.is_dir()]:
                signaler_memoire(lecons, "`%s/` ne contient que des notes `<sujet>.md` (§6)"
                                 % LECONS)
            continue
        if not [e for e in sorted(entree.iterdir())
                if e.is_dir() and not e.name.startswith(".")]:
            signaler_memoire(entree, "projet gelé sans chantier : sous `%s/`, un projet est "
                                     "`<projet>/<chantier>/` (§6)" % MEMOIRES)


# --------------------------------------------------------- dépôt de données

def verifier_depot_de_donnees():
    """§7.1 : la liste blanche du coffre est le gabarit, et `OBSIA/` n'y est pas suivi.

    Le `.gitignore` du coffre parent n'est pas écrit à la main : c'est le gabarit
    `IA/system/depot-de-donnees/gitignore-coffre`, posé par l'installeur et jamais
    écrasé. Un écart veut dire que quelqu'un a retouché la liste blanche sur la
    machine — la prochaine installation ne le verra pas, et `OBSIA/` peut se
    retrouver versionné dans la mémoire sans que personne ne s'en aperçoive.

    Ne s'exécute que sur un coffre parent désigné (`--coffre`) : un clone de la
    CI n'en a pas.
    """
    gabarit = RACINE / "IA" / "system" / "depot-de-donnees" / "gitignore-coffre"
    if not gabarit.is_file():
        erreur(designation(gabarit),
               "gabarit de la liste blanche du coffre absent (§7.1)")
        return
    gitignore = COFFRE / ".gitignore"
    if not gitignore.is_file():
        signaler_memoire(Path(".gitignore"),
                         "le coffre parent n'a pas de liste blanche : le dépôt de "
                         "données n'est pas initialisé — l'installeur la pose (§7.1)")
        return
    try:
        ecrit = gitignore.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        signaler_memoire(Path(".gitignore"), "liste blanche illisible (§7.1)")
        return
    if ecrit != gabarit.read_text(encoding="utf-8"):
        signaler_memoire(Path(".gitignore"),
                         "diffère du gabarit `IA/system/depot-de-donnees/gitignore-coffre` "
                         "— la liste blanche est le gabarit, sans retouche (§7.1)")
    if _git_dans(COFFRE, "rev-parse", "--git-dir").returncode != 0:
        return
    suivis = [ligne for ligne in
              _git_dans(COFFRE, "ls-files", "--", RACINE.name).stdout.splitlines()
              if ligne.strip()]
    if suivis:
        signaler_memoire(Path(suivis[0]),
                         "le dépôt produit est suivi par le dépôt de données du "
                         "coffre — `%s/` n'entre jamais dans la mémoire (§7.1)"
                         % RACINE.name)


PREFIXES_SONDE = ("commande", "fichier", "distribution", "parent")


def verifier_modules(dossier: Path) -> list[dict]:
    """§13 : le catalogue de modules — frontmatter, sondes, dépendances.

    Un module mal formé ne casse rien tant qu'on installe tout ; il casse
    l'installation partielle, c'est-à-dire précisément le cas qu'on ne teste
    jamais avant de le vivre.
    """
    modules: list[dict] = []
    if not dossier.is_dir():
        erreur("IA/system/modules/", "catalogue de modules absent (§13)")
        return modules

    for chemin in sorted(dossier.glob("*.md")):
        fm = lire_frontmatter(chemin)
        rel = chemin.relative_to(RACINE)
        if fm is None:
            erreur(rel, "frontmatter absent ou non fermé")
            continue
        if fm.get("kind") != "module":
            erreur(rel, "`kind: %s` alors que le fichier est dans IA/system/modules/ (§13)"
                   % fm.get("kind"))
            continue

        nom = fm.get("name")
        if nom != chemin.stem:
            erreur(rel, "`name: %s` ≠ nom du fichier `%s` (§5)" % (nom, chemin.stem))
        if nom and not NOM_VALIDE.match(nom):
            erreur(rel, "`name: %s` — attendu : minuscules et tirets, sans espace (§5)" % nom)
        if not isinstance(fm.get("schema"), int):
            erreur(rel, "`schema` doit être un entier (§5)")
        if not fm.get("description"):
            erreur(rel, "`description` vide ou absente (§5)")
        if not isinstance(fm.get("essentiel"), bool):
            erreur(rel, "`essentiel` doit valoir true ou false (§13)")

        for champ in ("requiert", "sondes"):
            if champ in fm and not isinstance(fm[champ], list):
                erreur(rel, "`%s` doit être une liste à tirets, pas « %s » (§5)"
                       % (champ, fm[champ]))

        if not fm.get("essentiel") and not fm.get("question"):
            erreur(rel, "module non essentiel sans `question` — l'installeur "
                        "n'aurait rien à demander (§13)")

        for sonde in fm.get("sondes", []) if isinstance(fm.get("sondes"), list) else []:
            prefixe = sonde.split(":", 1)[0]
            if prefixe not in PREFIXES_SONDE:
                erreur(rel, "sonde `%s` — préfixe inconnu, attendu %s (§13)"
                       % (sonde, " | ".join(PREFIXES_SONDE)))
            elif ":" not in sonde or not sonde.split(":", 1)[1].strip():
                erreur(rel, "sonde `%s` — valeur vide (§13)" % sonde)

        fm["_chemin"] = rel
        fm.setdefault("requiert", [])
        fm.setdefault("sondes", [])
        modules.append(fm)

    noms = {m.get("name") for m in modules}
    if "noyau" not in noms:
        erreur("IA/system/modules/", "aucun module `noyau` — le socle doit exister (§13)")

    for m in modules:
        for besoin in m["requiert"] if isinstance(m["requiert"], list) else []:
            if besoin not in noms:
                erreur(m["_chemin"], "`requiert: %s` — module inexistant (§13)" % besoin)

    # Un cycle de dépendances boucle la résolution de l'installeur.
    par_nom = {m["name"]: m for m in modules if m.get("name")}
    for depart in sorted(par_nom):
        vus, pile = set(), [depart]
        while pile:
            courant = pile.pop()
            for besoin in par_nom.get(courant, {}).get("requiert", []):
                if besoin == depart:
                    erreur(par_nom[depart]["_chemin"],
                           "cycle de dépendances entre modules : %s → … → %s (§13)"
                           % (depart, depart))
                    pile = []
                    break
                if besoin not in vus:
                    vus.add(besoin)
                    pile.append(besoin)

    return modules


def verifier_profil(modules: list[dict]) -> None:
    """§13 : le profil ne doit citer que des modules du catalogue.

    Avertissement et non erreur. Sans profil — le cas de la CI — il n'y a rien
    à dire. Avec un profil fautif, le coffre n'est pas incohérent : il est plus
    maigre que voulu, et c'est justement ce qu'on ne comprend pas quand on le
    découvre après l'installation.
    """
    import modules as _mod                       # tardif, comme dans generer_prompt

    profil = _mod.lire_profil(RACINE)
    if profil is None:
        return

    for nom in sorted(_mod.modules_inconnus(modules, profil.get("modules", []))):
        avertir(_mod.NOM_PROFIL,
                "`%s` ne correspond à aucun module du catalogue — sans effet, "
                "le coffre sera plus maigre que prévu (§13)" % nom)


def cloture(modules: list[dict], nom: str) -> set[str]:
    """Le module et tout ce qu'il entraîne, essentiels compris."""
    par_nom = {m["name"]: m for m in modules if m.get("name")}
    resolu = {nom} | {m["name"] for m in modules if m.get("essentiel")}
    pile = list(resolu)
    while pile:
        for besoin in par_nom.get(pile.pop(), {}).get("requiert", []):
            if besoin not in resolu:
                resolu.add(besoin)
                pile.append(besoin)
    return resolu


def module_declare(chemin, module, noms: set) -> bool:
    """Le `module` d'une déclaration existe-t-il dans le catalogue (§13) ?"""
    if not module:
        erreur(chemin, "ne déclare aucun `module` — inclassable à "
                       "l'installation (§13)")
        return False
    if module not in noms:
        erreur(chemin, "`module: %s` — module inexistant dans "
                       "IA/system/modules/ (§13)" % module)
        return False
    return True


def verifier_appartenance(modules, agents, skills, mcp, taches):
    """§13 : tout ce qui se déclare appartient à un module du catalogue."""
    noms = {m.get("name") for m in modules}
    peuples = set()

    for fm in list(agents) + list(skills) + list(mcp) + list(taches):
        chemin = fm.get("_chemin", fm.get("name", "?"))
        if module_declare(chemin, fm.get("module"), noms):
            peuples.add(fm["module"])

    if REDUITE:
        return              # ici, un module sans déclaration est un module écarté
    for m in modules:
        if m.get("name") not in peuples:
            avertir(m["_chemin"], "module qu'aucun agent, skill, MCP ou tâche "
                                  "ne rejoint — il n'installerait rien (§13)")


def verifier_annexes_contrat(dossier: Path, modules: list[dict]) -> list[dict]:
    """Les annexes du noyau, `IA/system/contrat/*.md` (§5, §13).

    Une annexe est un document déclaratif : elle se définit **par son dossier**,
    pas par son nom. Tout `*.md` de `IA/system/contrat/` est donc contrôlé comme
    une annexe, à une seule exception, `registre.md`, nommée ici : c'est l'index
    du dossier, sans frontmatter. Définir l'annexe par le préfixe `contrat-`
    laisserait une annexe renommée sortir du filet sans que rien ne le dise.

    Le frontmatter est vérifié par `verifier_fichier()`, appelé avec
    `CHAMPS_CONTRAT = (schema, kind, name, description)` : une annexe n'a ni
    `read_only` — elle ne s'exécute pas — ni `type`, réservé aux skills. Le
    contrôle exige en plus un `module` non vide (comme pour toute fiche), et
    `module_declare()` vérifie que ce module existe au catalogue.

    Les chemins qu'une annexe cite sont, eux, déjà contrôlés par
    `verifier_chemins_cites()` : tout `IA/**/*.md` y passe, le dossier compris,
    et les chemins **relatifs** sont résolus depuis le fichier qui les cite —
    `../VAULT-CONTRACT.md` depuis ici mène bien à `IA/system/VAULT-CONTRACT.md`.
    Aucune cible de ce dossier n'échappe au filet.

    Une annexe ne peuple pas son module : une déclaration dit à quoi elle
    appartient, elle n'installe rien. Seuls agents, skills, MCP et tâches
    comptent comme occupants (§13), sans quoi une annexe suffirait à faire
    passer un module vide pour un module habité.
    """
    if not dossier.is_dir():
        avertir(dossier.relative_to(RACINE),
                "dossier des annexes du contrat absent — aucune annexe contrôlée "
                "(§5, §13)")
        return []
    noms = {m.get("name") for m in modules}
    annexes: list[dict] = []
    for chemin in sorted(dossier.glob("*.md")):
        if chemin.name == NOM_EXEMPT_CONTRAT:
            continue
        fm = verifier_fichier(chemin, "contract", CHAMPS_CONTRAT,
                              "le dossier des annexes du contrat")
        if fm is None:
            continue
        module_declare(fm["_chemin"], fm.get("module"), noms)
        annexes.append(fm)
    return annexes


def verifier_renvois_entre_modules(modules, skills):
    """Un skill renvoie-t-il vers un skill qu'une installation partielle n'aura pas ?

    Pendant du contrôle de portée par agent (§10.2), mais au niveau du
    catalogue : si `A` dit « charger `B` » et que le module de `B` n'est pas
    entraîné par celui de `A`, la consigne tombe dans le vide chez qui n'a
    installé que le premier. Avertissement, pas erreur : la détection repose
    sur le verbe, et la frontière peut être voulue.
    """
    if REDUITE:
        return              # le contrôle porte sur le catalogue, pas sur une copie
    par_nom = {s["name"]: s for s in skills if s.get("name")}
    for nom, fm in par_nom.items():
        mien = fm.get("module")
        if not mien:
            continue
        entraines = cloture(modules, mien)
        try:
            texte = (RACINE / fm["_chemin"]).read_text(encoding="utf-8")
        except OSError:
            continue
        vises = {m.group(1) for m in CONSIGNE_SKILL.finditer(texte)} & set(par_nom)
        for vise in sorted(vises - {nom}):
            sien = par_nom[vise].get("module")
            if sien and sien not in entraines:
                avertir(fm["_chemin"],
                        "dit de charger `%s`, du module `%s` que `%s` n'entraîne "
                        "pas — consigne absente d'une installation partielle (§13)"
                        % (vise, sien, mien))


def verifier_derives():
    """Les index doivent être à jour vis-à-vis de leurs sources.

    Les sommaires de `mémoire/` n'en font plus partie : ils ne sont pas
    versionnés (§11), donc un clone neuf — celui de la CI — n'en a pas, et
    les exiger reviendrait à refuser tout clone propre.
    """
    for script, quoi in (("regenerate_index.py", "index"),):
        res = subprocess.run([sys.executable, str(SCRIPTS / script), "--verifier"],
                             capture_output=True, text=True, cwd=str(RACINE))
        if res.returncode != 0:
            detail = (res.stderr or res.stdout).strip().replace("\n", " / ")
            erreur("scripts/%s" % script, "%s périmés — %s" % (quoi, detail))


def verifier_taille_du_fichier_agents():
    """Le fichier AGENTS.md doit rester loin du plafond de consignes de Codex.

    Codex ne retient en tout que 32 Kio de consignes — le fichier global
    (~/.codex/AGENTS.md) et ceux du projet comptent ensemble. Au-delà, le
    surplus est laissé de côté, sans erreur ni avertissement : l'agent perd des
    agents et des skills entiers sans que rien ne le dise.

    On mesure le pire cas — le catalogue entier, profil ignoré, comme la CI —
    avec la même fonction que l'installeur (`prompt_du_coffre(sans_profil=True)`,
    pour ne pas dépendre d'un `obsia.local.yml` qui n'est pas versionné). Et on
    mesure ce que l'installeur écrit vraiment, marqueur compris : le prompt seul
    laisserait passer un fichier déjà au-delà. Un avertissement dès 28 Kio laisse
    le temps de réduire et couvre le fichier global ; au-delà de 32 Kio c'est
    une erreur, parce que la perte est réelle et muette.

    Ce contrôle ne s'assouplit pas sous `mode: copie` : un surplus écarté reste
    écarté, quelle que soit l'installation.
    """
    # `collecter` commente bruyamment ce qu'il écarte — dossier absent, frontmatter
    # illisible, description vide. Le vérificateur le dit déjà fichier par fichier,
    # mieux et au bon endroit : on tait ce bavardage le temps de la mesure. Il est
    # surtout gênant sous `mode: copie`, où un dossier amputé est normal.
    with contextlib.redirect_stderr(io.StringIO()):
        prompt = prompt_du_coffre(RACINE, sans_profil=True)
    if prompt is None:
        return                                   # coffre vide : rien à mesurer
    taille = len(contenu_agents(prompt).encode("utf-8"))

    if taille > TAILLE_FICHIER_AGENTS_ERREUR:
        erreur("AGENTS.md",
               "le fichier écrit (catalogue entier, sans profil, marqueur "
               "compris) pèse %d o, au-delà du plafond total de Codex "
               "(%d o, 32 Kio) : le surplus est laissé de côté et l'agent perd "
               "des déclarations entières sans que rien ne le dise — réduire "
               "le catalogue avant d'y arriver"
               % (taille, TAILLE_FICHIER_AGENTS_ERREUR))
    elif taille > TAILLE_FICHIER_AGENTS_AVERTISSEMENT:
        avertir("AGENTS.md",
                "le fichier écrit (catalogue entier, sans profil, marqueur "
                "compris) pèse %d o ; au-delà de %d o (28 Kio) la marge se "
                "réduit avant le plafond total de Codex (%d o, 32 Kio), que le "
                "fichier global partage — réduire le catalogue avant d'y arriver"
                % (taille,
                   TAILLE_FICHIER_AGENTS_AVERTISSEMENT, TAILLE_FICHIER_AGENTS_ERREUR))


def verifier_chemins_du_prompt():
    """Le prompt engendré ne doit porter aucun chemin absolu de machine.

    L'`AGENTS.md` est synchronisé (Syncthing) entre des postes où le coffre n'a ni
    le même chemin ni le même nom : un `/srv/…` écrit ici est faux là-bas, et rien
    ne le dit — l'agent cherche un dossier qui n'existe pas. Le fichier posé est
    engendré du catalogue : un chemin peut donc entrer par la description d'un
    agent, d'un skill ou d'une tâche, et pas seulement par l'en-tête. On contrôle
    le prompt réel du catalogue, celui que la CI engendre et que l'installeur
    écrit, marqueur compris.

    Le motif vient du générateur (`generer_prompt.chemins_absolus`) : c'est lui qui
    promet ce texte, et deux copies du motif finiraient par diverger.
    """
    with contextlib.redirect_stderr(io.StringIO()):
        prompt = prompt_du_coffre(RACINE, sans_profil=True)
    if prompt is None:
        return                                   # coffre vide : rien à contrôler
    fautives = chemins_absolus(contenu_agents(prompt))
    if not fautives:
        return
    montre = " | ".join(ligne.strip()[:120] for ligne in fautives[:5])
    suite = "" if len(fautives) <= 5 else " (+%d autre(s))" % (len(fautives) - 5)
    erreur("AGENTS.md",
           "le prompt engendré porte %d chemin(s) absolu(s) de machine%s : %s — "
           "le fichier est synchronisé entre des postes où le coffre n'a ni le "
           "même chemin ni le même nom ; désigner la racine par son sous-dossier "
           "OBSIA/, ou par le dossier qui le contient"
           % (len(fautives), suite, montre))


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
