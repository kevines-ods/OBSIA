#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Produit le miroir public d'OBSIA à partir de ce dépôt, qui fait foi.

Ce dépôt-ci est privé : il a porté la mémoire, et il porte encore les logs de
session et le profil d'installation de son propriétaire. La mémoire vit
désormais dans le coffre parent (§7.1), hors du dépôt : le dépôt public est la
**distribution** — le même outil, moins ce qui décrit une personne et une
machine.

Il n'y a pas deux sources de vérité. Ce script en dérive une seconde, et il
refuse de publier ce qu'il ne sait pas relire.

    python3 scripts/publier.py --cible ~/OBSIA-public              # aperçu
    python3 scripts/publier.py --cible ~/OBSIA-public --appliquer  # écrit
    python3 scripts/publier.py --cible ~/OBSIA-public --appliquer --commit

La cible est un clone du dépôt public. Son `.git/` n'est jamais touché : le
script remplace le contenu suivi, montre le diff, et laisse committer — ou
committe lui-même avec `--commit`, sans jamais pousser.

Bibliothèque standard uniquement.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import NamedTuple

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import modules as MOD
from generer_prompt import RACINE_DEFAUT

#: Ce qui décrit une personne ou une machine, et ne franchit jamais la
#: frontière du public. Les README de ces dossiers, eux, passent : ils
#: expliquent à quoi la zone sert. `mémoire` est transitoire : la mémoire vit
#: dans le coffre parent (§7.1) et ce dossier quitte le dépôt à la migration ;
#: tant qu'il est là, la vider est ce qui empêche de la publier par accident.
PRIVE = ("IA/system/session-log", "brouillon", ".archive", "mémoire")

#: Ce qui ne devrait même pas être suivi par Git, mais qu'on écarte quand même :
#: une ceinture coûte moins cher qu'un secret dans un historique public.
JAMAIS = ("obsia.local.yml", "prompt-systeme.md", ".env", "mcp.json", ".mcp.json")

#: Ce qui trahit un coffre vivant du côté de la cible. `synchroniser` efface
#: tout ce que la cible contient hors `.git/` : lui donner un coffre de travail,
#: c'est effacer le travail de quelqu'un. Les deux noms du même dossier y sont —
#: `0-…` depuis la bascule (§7.1), `-…` pour les coffres qui ne l'ont pas finie.
MARQUES_DE_COFFRE = (".obsidian", "_MAINTENANCE", "Mon coffre",
                     "0-SAVOIRS", "0-PROJETS", "0-MEMOIRES", "0-PERSONNELS",
                     "-SAVOIRS", "-PROJETS")

# ------------------------------------------------------------ contrôle de fuite

#: Ce qui bloque la publication. Chaque motif vise une **valeur**, jamais le
#: mot qui la nomme : le contrat parle de jetons et de mots de passe à longueur
#: de page, et il doit pouvoir continuer.
BLOQUANTS = (
    ("adresse de courriel",
     re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]{2,}\b")),
    ("adresse IP privée",
     re.compile(r"\b(?:10\.\d{1,3}|192\.168|172\.(?:1[6-9]|2\d|3[01]))"
                r"\.\d{1,3}\.\d{1,3}\b")),
    ("clé privée",
     re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("jeton d'API",
     re.compile(r"\b(?:ghp|gho|ghs|ghu|github_pat|sk-ant|sk-proj|sk-live|AKIA)"
                r"[-_A-Za-z0-9]{10,}")),
    # Pas de `\b` en tête : un préfixe colle presque toujours au nom réel
    # (`OPENAI_API_KEY=…`, `db_password`), et `_` étant un caractère de mot, la
    # limite ne tombait jamais là où il fallait. Un suffixe d'un seul morceau
    # (`password_hash`) est admis pour la même raison — un seul : au-delà,
    # `bearer_token_env_var` désigne le nom d'une variable d'environnement, pas
    # un secret.
    #
    # Le coffre s'écrit en français : `mdp`, `mot de passe`, `jeton`, `clé`
    # disent la même chose que `password` et `token`. Et la valeur, elle, ne se
    # limite pas à l'alphanumérique : un mot de passe a le droit d'avoir des
    # symboles, et des espaces quand il est entre guillemets.
    #
    # Le prix à payer, c'est la ligne de code : `cle = os.environ.get(clé)` lit
    # une variable, elle ne donne aucun secret. D'où les deux garde-fous de la
    # valeur nue — pas de ponctuation de code, et la valeur va jusqu'au bout du
    # mot. Sans quoi la moitié des scripts du coffre se signaleraient.
    ("secret affecté",
     re.compile(
         r"(?i)(?:[\w-]*[_-])?"
         r"(?:password|passwd|api[_-]?key|secret|token|jeton|mdp"
         r"|mot[ _-]de[ _-]passe|cl[ée])(?:[_-][A-Za-z0-9]+)?\b\s*[=:]\s*"
         r"(?:[\"'][^\"']{12,}[\"']|[^\s\"'()\[\]{},]{12,}(?=\s|$))"
         # Une phrase de passe sans guillemets, donc des espaces dans la valeur.
         # Rien, dans sa forme, ne la distingue d'une phrase de prose : c'est sa
         # position qui parle. Mot-clé fort en début de ligne — éventuellement
         # après une puce — et une affectation qui prend toute la ligne. Une
         # phrase comme « … pas un secret : une note du coffre parent la porte »
         # a le même mot-clé, mais au milieu de la ligne, et elle reste muette.
         r"|^[ \t]*(?:[-*+][ \t]+)?"
         r"(?:password|passwd|secret|mdp|mot[ _-]de[ _-]passe)\b\s*[=:]\s*"
         r"\S+(?:\s+\S+)+[ \t]*$")),
    # Une clé secrète AWS n'a pas de préfixe reconnaissable — c'est justement
    # pourquoi elle se recopie nue. Quarante caractères base64, à côté d'un
    # mot-clé qui dit ce qu'ils sont ; l'alternance `[^\n]{0,40}?` laisse la
    # valeur se placer librement sur la ligne. Majuscules obligatoires dans le
    # motif : quarante hexadécimaux minuscules, c'est une empreinte de commit,
    # et le coffre en cite.
    ("clé secrète AWS",
     re.compile(r"(?i)(?:aws|secret)[^\n]{0,40}?"
                r"\b(?=[A-Za-z0-9/+=]*[A-Z])[A-Za-z0-9/+=]{40}\b")),
    # Noms d'hôte internes. La fin ne doit pas être suivie d'un point et d'un
    # mot : sans cela, `obsia.local.yml`, `AGENTS.local.md` et
    # `CLAUDE.local.md` — trois noms de fichiers locaux, jamais des machines —
    # se signaleraient tout seuls.
    ("nom d'hôte interne",
     re.compile(r"\b[\w-]+(?:\.[\w-]+)*"
                r"\.(?:lan|local|internal|home\.arpa|ts\.net)\b(?!\.\w)")),
)

#: Boîtes génériques et domaines réservés : ils désignent un projet, pas une
#: personne. Le domaine se compare **en entier** — `exemple.fr.attaquant.net`
#: n'est pas `exemple.fr`, et rien n'empêche d'enregistrer le second.
BOITES_ADMISES = ("noreply", "utilisateur")
DOMAINES_ADMIS = ("exemple.fr",)

#: Domaines que la RFC 2606 réserve à la documentation. Personne ne peut les
#: enregistrer : une adresse qui les porte ne désigne aucun correspondant réel.
#: Un sous-domaine d'un domaine réservé l'est aussi — `mail.example.com`.
DOMAINES_RESERVES = ("example.com", "example.net", "example.org")
#: Domaines de premier niveau que la RFC 6761 réserve de la même façon. Le
#: suffixe se compare **avec son point**, sans quoi on admettrait
#: `quelqu'un@mon-test` par simple terminaison de chaîne.
TLD_RESERVES = (".test", ".example", ".invalid")

#: Les étiquettes qu'un `--forcer` ne publie jamais — les valeurs à forme
#: reconnaissable. Une clé privée ne se révoque pas — elle se remplace. Un jeton
#: connu se révoque, mais seulement avant d'avoir servi : publié, il est déjà
#: trop tard. Les autres catégories — une adresse, un nom d'hôte, un mot de
#: passe à changer — se rattrapent.
#:
#: Un *nom interdit* n'en fait pas partie : ce n'est pas une forme
#: reconnaissable, c'est une liste personnelle qui frappe des mots. Il est
#: signalé en avertissement, pas bloqué — un avertissement n'a pas besoin de
#: converger, un faux positif se corrige à la main sans perdre la publication.
#:
#: Le **chemin de la machine qui publie** en fait partie sans être une valeur :
#: rien ne le révoque, et le publier nomme une arborescence privée (§13). Le
#: corriger n'est pas un jugement à porter, c'est une évidence : sa place n'est
#: pas dans l'export, donc il n'y a rien à forcer.
SANS_FORCAGE = ("clé privée", "jeton d'API",
                "chemin du coffre", "chemin du dépôt")

#: La liste locale des noms interdits — noms d'hôtes, nom du dépôt privé, tout
#: ce qui désigne l'infrastructure sans avoir de forme reconnaissable. Elle vit
#: hors du dépôt, à dessein : la versionner publierait précisément ce qu'elle
#: protège. Un nom par ligne, `#` pour commenter. `OBSIA_NOMS_INTERDITS` en
#: désigne une autre.
#:
#: Un nom de cette liste **avertit**, il ne refuse pas : la liste doit retenir
#: des identités, mais elle frappe des mots — un mot banal peut s'y trouver, et
#: un avertissement n'a pas besoin de converger. Le contrôle signale chaque
#: occurrence, ligne par ligne, puis laisse publier. Liste absente ou vide =
#: aucun nom contrôlé.
NOMS_INTERDITS = Path(os.environ.get(
    "OBSIA_NOMS_INTERDITS", os.path.expanduser("~/.config/obsia/noms-interdits")))

#: En dessous, un nom attrape des mots ordinaires : `ia` signalerait `IA/` dans
#: chaque fichier. Un tel nom est ignoré, et le rapport le dit.
LONGUEUR_MINIMALE_NOM = 4

#: Ce qui n'est pas relu, par extension : un fichier binaire. `.svg` n'y est
#: plus — c'est du texte, et le sauter laissait passer ce qu'il contient.
BINAIRES = (".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".woff",
            ".woff2", ".ico")


def courriel_admis(adresse: str) -> bool:
    """Vrai pour une adresse de projet : boîte générique, ou domaine réservé.

    Un vrai domaine reste bloqué : seul ce que la RFC 2606/6761 réserve à la
    documentation est admis, parce que rien ne peut y être enregistré. Le
    réservé couvre ses sous-domaines, dans les deux formes — `mail.example.com`
    comme `mail.exemple.test`.
    """
    boite, _, domaine = adresse.partition("@")
    if boite.lower() in BOITES_ADMISES:
        return True
    domaine = domaine.lower()
    if domaine in DOMAINES_ADMIS or domaine.endswith(TLD_RESERVES):
        return True
    return any(domaine == reserve or domaine.endswith("." + reserve)
               for reserve in DOMAINES_RESERVES)


#: Une option qui reçoit un **chemin** de fichier de mot de passe, pas le mot de
#: passe lui-même : `--password-file=/chemin/vers/motdepasse.txt`, ou la même
#: forme séparée par une espace. Le nom de l'option le dit — `file`, `fichier`,
#: `path` — et il commence par un tiret : c'est une option de commande, pas une
#: variable qui porterait le secret. La documentation conseille cette forme ;
#: sans l'exception, toute fiche qui la montre se signale comme une fuite, et un
#: contrôle qui crie à tort finit par être forcé sans être lu.
MOTIF_OPTION_DE_FICHIER = re.compile(
    r"(?i)^--?[\w-]*(?:file|fichier|path)[\w-]*$")


def option_de_fichier(extrait: str) -> bool:
    """`--password-file=…` désigne un fichier, pas un mot de passe."""
    nom = re.split(r"[=:]|\s", extrait.strip(), maxsplit=1)[0]
    return bool(MOTIF_OPTION_DE_FICHIER.match(nom))


def charger_noms_interdits(chemin: Path = None) -> tuple[list, list]:
    """Rend (noms retenus, noms écartés car trop courts). Sans fichier : rien."""
    chemin = chemin or NOMS_INTERDITS
    try:
        lignes = chemin.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return [], []
    retenus, courts = [], []
    for ligne in lignes:
        nom = ligne.split("#", 1)[0].strip()
        if not nom:
            continue
        (retenus if len(nom) >= LONGUEUR_MINIMALE_NOM else courts).append(nom)
    return retenus, courts


def motif_des_noms(noms) -> "re.Pattern | None":
    """Un nom entier, sans tenir compte de la casse : `poste-1` ne se trouve pas
    dans `poste-12`, ni `atelier` dans `ateliers`."""
    if not noms:
        return None
    alternance = "|".join(re.escape(nom) for nom in sorted(noms, key=len, reverse=True))
    return re.compile(r"(?i)(?<![\w-])(?:%s)(?![\w-])" % alternance)


#: Les échappements d'un littéral collent un mot devant le chemin : dans un test,
#: le chemin s'écrit `"…\n/home/moi/coffre\n…"`, et le `/` y suit alors un
#: `n`. Le motif aurait beau jeu d'écarter les sous-chaînes : ce chemin-là est
#: bel et bien dans le fichier, et c'est lui qu'on cherche. On desserre avant de
#: chercher.
ECHAPPEMENTS = re.compile(r"\\[nrtvfb'\"\\]")


def desserrer(ligne: str) -> str:
    """Remplace un échappement de littéral par une espace, pour la recherche."""
    return ECHAPPEMENTS.sub(" ", ligne)


#: Les deux schémas dont le chemin n'est pas une arborescence locale.
SCHEMES_WEB = ("http://", "https://")


def dans_une_url_web(ligne: str, position: int) -> bool:
    """Vrai si le chemin qui commence à `position` est celui d'une URL http(s).

    `https://exemple.fr/srv/…` porte un chemin d'URL, pas un chemin de fichier :
    l'égalité avec la racine de la machine serait une coïncidence, et refuser une
    URL écrite à la main n'apprendrait rien à personne. Le silence vaut par
    **occurrence**, pas par ligne : une seconde plus loin, hors de l'URL, le
    chemin est de nouveau regardé — et c'est souvent celle-là qui fuit.

    `file://` n'est pas dans la liste, et c'est voulu : une URL de fichier
    désigne bien une arborescence locale — c'est même la forme la plus probable
    d'une fuite recopiée depuis un navigateur.
    """
    avant = ligne[:position]
    debut = max(avant.rfind(schema) for schema in SCHEMES_WEB)
    if debut < 0:
        return False
    return not re.search(r"\s", avant[debut:])


def formes_du_chemin(chemin: Path, maison: Path) -> list:
    """Les écritures équivalentes d'un chemin : absolue, et `~/…` sous le home.

    Un dossier de premier niveau ne désigne personne. `/srv`, `/opt`, `/mnt` :
    une installation y tient avec le dépôt posé directement dedans, et le motif
    `/srv` se signalerait dans la moitié des textes qui parlent d'un serveur ou
    d'un montage. Un contrôle qui crie à tort est un contrôle qu'on force sans le
    lire : plutôt que de crier, on se taît.

    Le home est un paramètre, pas `Path.home()` : les deux formes dépendent de la
    machine, et un test doit pouvoir les poser à la main.
    """
    if len(chemin.parts) <= 2:          # `/` et `/srv` : rien à reconnaître
        return []
    formes = [str(chemin).rstrip("/")]
    if chemin != maison and maison in chemin.parents:
        relatif = chemin.relative_to(maison).as_posix()
        if relatif:                     # le home lui-même ne fait pas `~`
            formes.append("~/" + relatif)
    return formes


def motifs_de_machine(source: Path, maison: Path = None) -> list:
    """Les chemins absolus de la machine qui publie : le dépôt, et son coffre.

    Un chemin de machine dans un fichier exporté nomme une arborescence privée —
    et il est faux partout ailleurs (§13). Les motifs de `BLOQUANTS` ne peuvent
    pas le reconnaître : il dépend de la machine. D'où ce second motif, construit
    à partir de la source, et **vide** quand on ne la lui donne pas : le contrôle
    ne doit pas dépendre de la machine qui le lance, sans quoi un test passerait
    ici et échouerait là.

    Le chemin se compare **entier** : `/home/moi/coffre-notes` n'est pas le coffre,
    et `/home/moi/coffre/OBSIA-tests` n'est pas le dépôt. Il se compare aussi
    **sans regarder ce qui le précède** : `file://`, `//…`, `…/backup/…` sont des
    façons de l'écrire, pas des raisons de le laisser passer. Le coffre parent
    vient en second, et la comparaison s'arrête à la première : une ligne qui
    porte le dépôt porte aussi son préfixe, et le rapport doit dire lequel des
    deux c'est.
    """
    racine = Path(source).resolve()
    maison = Path(maison) if maison is not None else Path.home()
    motifs = []
    for etiquette, chemin in (("chemin du dépôt", racine),
                              ("chemin du coffre", racine.parent)):
        formes = formes_du_chemin(chemin, maison)
        if not formes:
            continue
        motif = re.compile(r"(?:%s)(?![\w-])"
                           % "|".join(re.escape(forme) for forme in formes))
        motifs.append((etiquette, motif))
    return motifs


class Controle(NamedTuple):
    """Ce que le contrôle a vu — et ce qu'il n'a pas pu relire.

    Les deux vont ensemble : « aucune trouvaille » sur cent fichiers dont
    quatre-vingts illisibles ne veut rien dire. Un fichier non relu n'est pas
    un fichier propre, c'est un fichier dont on ne sait rien.
    """

    #: (chemin, ligne, étiquette, extrait) par trouvaille bloquante — ce que
    #: `--forcer` ne franchit pas (forme reconnaissable : clé, jeton).
    trouvailles: list
    #: (chemin, raison) par fichier sauté : binaire, non UTF-8, illisible.
    non_relus: list
    #: Nombre de fichiers effectivement relus.
    relus: int
    #: (chemin, ligne, étiquette, extrait) par avertissement — un nom de la
    #: liste locale, signalé sans bloquer ; `--forcer` ne sert pas, il passe.
    avertissements: list


def _balayer(lignes, chemin, trouvailles, avertissements, motif_noms=None,
             motifs_machine=()) -> None:
    """Passe des lignes au crible des motifs, et verse ce qu'il y voit.

    Partagé par `controler_fuites` (un arbre de fichiers) et `controler_texte`
    (le titre et la description d'une pull request) : la règle qui décide ce qui
    fuit ne doit exister qu'une fois. `chemin` est ce qui s'imprime à gauche de
    `:ligne` — un chemin relatif, ou le nom de la source textuelle.

    `motifs_machine` est vide par défaut : ces motifs-là dépendent de la machine
    (`motifs_de_machine`), et le contrôle de texte libre n'a pas à les recevoir.
    """
    for numero, ligne in enumerate(lignes, 1):
        for etiquette, motif in BLOQUANTS:
            trouve = motif.search(ligne)
            if not trouve:
                continue
            extrait = trouve.group(0)
            if etiquette == "adresse de courriel" and courriel_admis(extrait):
                continue
            if etiquette == "secret affecté" and option_de_fichier(extrait):
                continue
            trouvailles.append((chemin, numero, etiquette, ligne.strip()[:110]))
        if motifs_machine:
            # Desserrée une fois, et cherchée telle quelle : la position rendue
            # sert à regarder ce qui précède, et ne doit pas se décaler.
            # Chaque occurrence est jugée : une première dans le chemin d'une URL
            # muette ne doit pas blanchir la seconde, écrite en `file://`.
            desseree = desserrer(ligne)
            for etiquette, motif in motifs_machine:
                if all(dans_une_url_web(desseree, trouve.start())
                       for trouve in motif.finditer(desseree)):
                    continue
                trouvailles.append((chemin, numero, etiquette, ligne.strip()[:110]))
                break
        if motif_noms:
            trouve = motif_noms.search(ligne)
            if trouve:
                avertissements.append(
                    (chemin, numero, "nom interdit", ligne.strip()[:110]))


def controler_texte(texte: str, noms_interdits=(), etiquette="texte") -> Controle:
    """Relit un texte libre — le titre et la description d'une pull request.

    Le contrôle d'arbre ne voit que des fichiers versionnés ; or le titre d'une
    PR paraît sur le dépôt public *avant* son contenu, et il y reste. D'où ce
    second point d'entrée, qui applique exactement les mêmes motifs au texte
    fourni. `relus` compte la source, pas ses lignes : un texte vide n'en est
    pas une, et « aucune trouvaille » doit alors ne rien dire.
    """
    trouvailles, avertissements = [], []
    _balayer(texte.splitlines(), etiquette, trouvailles, avertissements,
             motif_des_noms(noms_interdits))
    return Controle(trouvailles, [], 1 if texte.strip() else 0, avertissements)


def depot_reel(source: Path) -> Path:
    """Le clone principal du dépôt, même quand on lance depuis un worktree.

    Les motifs de machine nomment le coffre **de cette machine** : c'est le clone
    principal qu'il faut lire, pas le dossier d'où l'on parle. Un worktree vit
    ailleurs — `~/obsia-worktrees/<nom-agent>-<sujet>` — et son dossier parent
    n'est pas le coffre : c'est un hangar à worktrees, dont le nom se lit dans la
    documentation du dépôt. Prendre ce parent pour le coffre ferait signaler
    cette documentation à chaque aperçu lancé depuis un worktree, et la
    publication y resterait bloquée — un chemin de machine ne se force pas.
    """
    commun = Path(git(source, "rev-parse", "--git-common-dir").strip())
    if not commun.is_absolute():
        commun = source / commun
    return commun.resolve().parent


def controler_fuites(racine: Path, noms_interdits=(), machine: Path = None,
                     maison: Path = None) -> Controle:
    """Relit tout l'arbre exporté, et dit aussi ce qu'il n'a pas pu relire.

    `noms_interdits` vient de la liste locale (`charger_noms_interdits`) ; par
    défaut vide, pour que le contrôle ne dépende pas de la machine qui le lance.

    `machine` est la racine du dépôt **de la machine qui publie** — le clone
    principal, que `depot_reel` retrouve même depuis un worktree : le contrôle en
    déduit ses deux chemins absolus — le dépôt, et son parent, le coffre — et
    refuse de les publier (§13). Absent, ces deux chemins ne sont pas contrôlés,
    par la même règle que `noms_interdits` : un contrôle qui dépendrait de la
    machine qui le lance passerait ici et échouerait là.

    `maison` est le home de cette machine, et ne sert qu'à une chose : reconnaître
    la forme `~/…` du même chemin. Absent, `Path.home()` — ce qui suffit à la
    publication, mais rendrait un test dépendant du poste, d'où le paramètre.
    """
    trouvailles, avertissements, non_relus, relus = [], [], [], 0
    motif_noms = motif_des_noms(noms_interdits)
    motifs_machine = motifs_de_machine(machine, maison) if machine else ()
    for chemin in sorted(racine.rglob("*")):
        if not chemin.is_file() or chemin.is_symlink():
            continue
        rel = chemin.relative_to(racine)
        if rel.parts and rel.parts[0] == ".git":
            continue
        if chemin.suffix.lower() in BINAIRES:
            non_relus.append((str(rel), "extension binaire"))
            continue
        try:
            texte = chemin.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            non_relus.append((str(rel), "non UTF-8"))
            continue
        except OSError:
            non_relus.append((str(rel), "illisible"))
            continue
        relus += 1
        _balayer(texte.splitlines(), str(rel), trouvailles, avertissements,
                 motif_noms, motifs_machine)
    return Controle(trouvailles, non_relus, relus, avertissements)


# --------------------------------------------------------------------- export

def git(racine: Path, *args: str) -> str:
    res = subprocess.run(["git", *args], cwd=str(racine),
                         capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError((res.stderr or res.stdout).strip())
    return res.stdout


URL_CLONE = re.compile(r"(git clone https://github\.com/)[\w.-]+/[\w.-]+")


def reecrire_url_de_clone(vers: Path, depot: str) -> list[str]:
    """Fait pointer les commandes `git clone` de la doc vers le dépôt public.

    Le README du dépôt privé annonce l'adresse du dépôt privé : recopiée telle
    quelle, elle donnerait à un lecteur du public une commande qui échoue en
    404, sans lui dire pourquoi.
    """
    touches = []
    for chemin in sorted(vers.rglob("*.md")):
        if ".git" in chemin.parts:
            continue
        texte = chemin.read_text(encoding="utf-8")
        neuf = URL_CLONE.sub(r"\g<1>" + depot, texte)
        if neuf != texte:
            chemin.write_text(neuf, encoding="utf-8")
            touches.append(str(chemin.relative_to(vers)))
    return touches


def exporter(source: Path, vers: Path) -> None:
    """Copie l'arbre suivi par Git à HEAD, puis retire ce qui est privé.

    `git archive` plutôt qu'une copie du répertoire : ce qui n'est pas suivi
    n'a pas été relu, et ce qui n'a pas été relu ne se publie pas.
    """
    archive = vers.parent / "obsia-export.tar"
    with archive.open("wb") as sortie:
        res = subprocess.run(["git", "archive", "HEAD"], cwd=str(source),
                             stdout=sortie, stderr=subprocess.PIPE, text=False)
    if res.returncode != 0:
        raise RuntimeError(res.stderr.decode("utf-8", "replace").strip())

    vers.mkdir(parents=True, exist_ok=True)
    shutil.unpack_archive(str(archive), str(vers), format="tar")
    archive.unlink()

    for rel in PRIVE:
        dossier = vers / rel
        if not dossier.is_dir():
            continue
        for enfant in sorted(dossier.rglob("*")):
            if enfant.is_file() and enfant.name != "README.md":
                enfant.unlink()
        for enfant in sorted(dossier.rglob("*"), reverse=True):
            if enfant.is_dir() and not any(enfant.iterdir()):
                enfant.rmdir()

    for rel in JAMAIS:
        for trouve in vers.rglob(rel):
            trouve.unlink()

    MOD.ecrire_gabarits_dinstance(vers)


def regenerer_et_verifier(racine: Path) -> int:
    # Les index seulement : les sommaires décrivent la mémoire du coffre parent
    # (§7.1), et la distribution n'en porte aucune — il n'y a rien à résumer.
    for script in ("regenerate_index.py",):
        res = subprocess.run([sys.executable, str(racine / "scripts" / script)],
                             cwd=str(racine), capture_output=True, text=True)
        if res.returncode != 0:
            print((res.stderr or res.stdout).strip(), file=sys.stderr)
            return res.returncode
    res = subprocess.run([sys.executable, str(racine / "scripts" / "verifier_coffre.py")],
                         cwd=str(racine), capture_output=True, text=True)
    print("  " + (res.stdout or "").strip().replace("\n", "\n  "))
    if res.returncode != 0:
        print((res.stderr or "").strip(), file=sys.stderr)
    return res.returncode


def synchroniser(export: Path, cible: Path) -> None:
    """Remplace le contenu suivi de la cible. Son `.git/` n'est jamais touché."""
    for enfant in sorted(cible.iterdir()):
        if enfant.name == ".git":
            continue
        if enfant.is_symlink():
            # Un lien se défait lui-même : le rmtree d'un dossier lié s'arrête
            # sur le lien et laisse la cible à moitié vidée.
            enfant.unlink()
        elif enfant.is_dir():
            shutil.rmtree(enfant)
        else:
            enfant.unlink()
    for enfant in sorted(export.iterdir()):
        destination = cible / enfant.name
        if enfant.is_dir():
            shutil.copytree(enfant, destination)
        else:
            shutil.copy2(enfant, destination)


# ------------------------------------------------------------------ la cible

#: Ce qu'un miroir d'OBSIA porte et que rien d'autre ne porte. Les marques de
#: coffre disent ce qu'il ne faut pas écraser ; celle-ci dit ce qu'on a le droit
#: d'écraser, et c'est la seule reconnaissance possible d'une publication.
MARQUE_DE_MIROIR = Path("IA") / "system" / "VAULT-CONTRACT.md"


def cible_vierge(cible: Path) -> bool:
    """Vrai si la cible n'a rien à perdre : un dépôt, et rien que son `.git/`.

    Pas « un dossier vide » : sans `.git/`, ce n'est pas un dépôt vierge mais
    un dossier inconnu, que `synchroniser` remplirait sans jamais savoir ce
    qu'il a effacé.
    """
    if not (cible / ".git").exists():
        return False
    return all(enfant.name == ".git" for enfant in cible.iterdir())


#: Les trois écritures d'une même origine distante — `git@hôte:p/dépôt`,
#: `ssh://git@hôte/p/dépôt`, `https://hôte/p/dépôt` — ramenées à leurs morceaux.
MOTIF_ORIGINE = re.compile(
    r"^(?:[a-z+]+://)?(?:(?P<utilisateur>[^@/]+)@)?"
    r"(?P<hote>[^:/]+)[:/](?P<chemin>[^/].*?)/?$", re.IGNORECASE)


def url_origine(depot: Path) -> str:
    """L'identité d'`origin`, ramenée à `hôte/chemin` — ou "" s'il n'y en a pas.

    Deux `origin` qui désignent le même dépôt doivent se comparer égaux : sans
    cela, le refus de publier sur un clone du privé se contourne en clonant en
    ssh ce qu'on a écrit en https. On jette donc ce qui ne désigne pas le
    dépôt — protocole, utilisateur, `.git` final, barre finale — et la casse.
    """
    try:
        url = git(depot, "remote", "get-url", "origin").strip()
    except RuntimeError:
        return ""
    encontre = MOTIF_ORIGINE.match(url)
    if encontre is None:
        # Un chemin local, par exemple : on ne sait pas le ramener à un dépôt.
        return url.rstrip("/").lower()
    chemin = re.sub(r"\.git$", "", encontre.group("chemin"))
    return ("%s/%s" % (encontre.group("hote"), chemin)).lower()


def raison_de_refus(source: Path, cible: Path) -> str | None:
    """Pourquoi refuser de synchroniser cette cible — ou None si c'est sûr.

    `synchroniser` efface le contenu suivi de la cible avant d'y verser
    l'export. Se tromper de cible, c'est effacer un coffre de travail ou un
    clone du dépôt privé, sans retour possible. On refuse donc avant d'exporter.
    """
    if cible == source:
        return "la cible est la source"
    if cible in source.parents:
        return "la cible contient la source"
    if source in cible.parents:
        return "la source contient la cible"
    for marque in MARQUES_DE_COFFRE:
        if (cible / marque).exists():
            return "la cible porte la marque d'un coffre : %s" % marque
    origine = url_origine(cible)
    if origine and origine == url_origine(source):
        return "la cible a la même origine que la source : %s" % origine
    if not (cible / MARQUE_DE_MIROIR).is_file() and not cible_vierge(cible):
        return ("la cible n'est ni un miroir d'OBSIA — %s — ni un dépôt vierge, "
                "c'est-à-dire un dépôt qui n'a rien que son `.git/` : y publier "
                "effacerait autre chose que notre publication"
                % MARQUE_DE_MIROIR)
    return None


def chemins_a_supprimer(cible: Path) -> list[str]:
    """Les entrées de la cible que `synchroniser` effacerait, `.git/` excepté."""
    supprimes = []
    for enfant in sorted(cible.iterdir()):
        if enfant.name == ".git":
            continue
        if enfant.is_symlink():
            supprimes.append("%s (lien symbolique)" % enfant.name)
        elif enfant.is_dir():
            supprimes.append("%s/" % enfant.name)
        else:
            supprimes.append(enfant.name)
    return supprimes


# ----------------------------------------------------------------------- main

def controler_le_texte(forcer: bool = False) -> int:
    """Le mode `--controler-texte` : lit l'entrée standard et juge.

    Sert à la vérification CI : le titre et la description d'une pull request
    paraissent sur le dépôt public avant que `publier.py` n'ait vu un seul
    fichier de l'export, et le contrôle d'arbre ne les lit donc jamais. Le même
    sens de `--forcer` s'applique — une clé privée se remplace, un jeton connu se
    révoque, aucun des deux ne se force. Les chemins de la machine, eux, ne
    peuvent pas se signaler ici : aucune racine n'est donnée, donc aucun chemin
    n'est connu de ce mode.
    """
    texte = sys.stdin.read()
    noms, _ = charger_noms_interdits()
    etiquette = "titre ou description de PR"
    controle = controler_texte(texte, noms, etiquette)
    for _, numero, trouvaille, ligne in controle.trouvailles:
        print("  ✗ %s:%d  [%s]" % (etiquette, numero, trouvaille))
        print("      %s" % ligne)
    for _, numero, avertissement, ligne in controle.avertissements:
        print("  ⚠ %s:%d  [%s]" % (etiquette, numero, avertissement))
        print("      %s" % ligne)
    if not controle.trouvailles:
        print("  Aucune trouvaille dans le %s." % etiquette)
        return 0
    if not forcer:
        print("  Corriger le texte de la PR, ou passer --forcer si c'est un "
              "faux positif.", file=sys.stderr)
        return 1
    interdites = sorted({t[2] for t in controle.trouvailles} & set(SANS_FORCAGE))
    if interdites:
        print("  --forcer ne s'applique pas ici : %s." % ", ".join(interdites),
              file=sys.stderr)
        return 1
    print("  --forcer : texte accepté malgré %d trouvaille(s)."
          % len(controle.trouvailles))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Produit le miroir public d'OBSIA depuis ce dépôt privé.")
    ap.add_argument("--racine", type=Path, default=RACINE_DEFAUT)
    ap.add_argument("--cible", type=Path,
                    help="clone local du dépôt public (requis hors "
                         "--controler-texte)")
    ap.add_argument("--controler-texte", action="store_true",
                    help="relit l'entrée standard — titre et description d'une "
                         "pull request — et refuse ce qui y fuit, sans lire "
                         "aucun arbre : ni --cible ni --racine ne servent")
    ap.add_argument("--appliquer", action="store_true",
                    help="écrit dans la cible ; sans lui, aperçu seulement")
    ap.add_argument("--commit", action="store_true",
                    help="committe dans la cible après écriture. Ne pousse jamais.")
    ap.add_argument("--depot-public", metavar="OWNER/NOM",
                    help="réécrit les `git clone https://github.com/…` de la "
                         "documentation vers ce dépôt")
    ap.add_argument("--forcer", action="store_true",
                    help="publie malgré les trouvailles du contrôle de fuite — "
                         "sauf une clé privée, un jeton connu, ou un chemin de "
                         "la machine : ceux-là ne se forcent pas")
    ap.add_argument("--autoriser-modifications", action="store_true",
                    help="publie depuis un arbre de travail sale (HEAD reste la source)")
    args = ap.parse_args()

    if args.controler_texte:
        return controler_le_texte(args.forcer)
    if args.cible is None:
        ap.error("--cible est requis (sauf avec --controler-texte)")

    source = args.racine.resolve()
    cible = args.cible.expanduser().resolve()

    if not (cible / ".git").is_dir():
        print("La cible n'est pas un clone Git : %s" % cible, file=sys.stderr)
        print("Cloner d'abord le dépôt public à cet emplacement.", file=sys.stderr)
        return 1
    refus = raison_de_refus(source, cible)
    if refus is not None:
        print("Publication refusée : %s." % refus, file=sys.stderr)
        print("  Source : %s" % source, file=sys.stderr)
        print("  Cible  : %s" % cible, file=sys.stderr)
        print("  `synchroniser` efface tout le contenu suivi de la cible : "
              "donner un clone du dépôt public.", file=sys.stderr)
        return 1

    sale = git(source, "status", "--porcelain").strip()
    if sale and not args.autoriser_modifications:
        print("Arbre de travail modifié — `git archive HEAD` ne publierait pas "
              "ces changements :", file=sys.stderr)
        print(sale, file=sys.stderr)
        print("\nCommitter d'abord, ou passer --autoriser-modifications.",
              file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory(prefix="obsia-publier-") as tmp:
        export = Path(tmp) / "export"
        forcees: list[str] = []
        print("Export de HEAD (%s)…" % git(source, "rev-parse", "--short", "HEAD").strip())
        exporter(source, export)

        if args.depot_public:
            touches = reecrire_url_de_clone(export, args.depot_public)
            print("  URL de clone → %s  (%d fichier(s))"
                  % (args.depot_public, len(touches)))

        print("\nCohérence du coffre exporté")
        print("───────────────────────────")
        code = regenerer_et_verifier(export)
        if code != 0:
            print("\nL'export est incohérent — rien n'est publié.", file=sys.stderr)
            return code

        # Après la régénération, et pas avant : elle réécrit les index et les
        # sommaires, et c'est cet export-là qui partira. Contrôler avant
        # reviendrait à relire un état qui n'existe plus.
        print("\nContrôle de fuite")
        print("─────────────────")
        noms, courts = charger_noms_interdits()
        if courts:
            print("  Noms interdits ignorés, trop courts (< %d caractères) : %d."
                  % (LONGUEUR_MINIMALE_NOM, len(courts)))
        print("  Liste locale des noms interdits : %s"
              % ("%d nom(s)" % len(noms) if noms else "absente ou vide — "
                 "noms d'hôtes nus non contrôlés (%s)" % NOMS_INTERDITS))
        controle = controler_fuites(export, noms, depot_reel(source))
        if controle.avertissements:
            for rel, numero, etiquette, ligne in controle.avertissements:
                print("  ⚠ %s:%d  [%s]" % (rel, numero, etiquette))
                print("      %s" % ligne)
            print("  %d nom(s) interdit(s) signalé(s) — avertissement, pas un refus."
                  % len(controle.avertissements))
            print("  La liste retient des identités mais frappe des mots : un faux "
                  "positif se corrige à la main, sans perdre la publication.")
        if controle.trouvailles:
            for rel, numero, etiquette, ligne in controle.trouvailles:
                print("  ✗ %s:%d  [%s]" % (rel, numero, etiquette))
                print("      %s" % ligne)

        # Le total se dit toujours — avertissement comme refus : « aucune
        # trouvaille » sur des fichiers qu'on n'a pas ouverts ne vaut que si le
        # nombre de fichiers sautés est sous les yeux.
        if not controle.trouvailles and not controle.avertissements:
            print("  Aucune trouvaille sur %d fichier(s) relu(s) — %d non relu(s)."
                  % (controle.relus, len(controle.non_relus)))
        else:
            print("  %d trouvaille(s) bloquante(s), %d avertissement(s) — "
                  "%d fichier(s) relu(s), %d non relu(s)."
                  % (len(controle.trouvailles), len(controle.avertissements),
                     controle.relus, len(controle.non_relus)))
        for rel, raison in controle.non_relus:
            print("      - %s (%s)" % (rel, raison))

        if controle.trouvailles:
            posees = [trouvaille[2] for trouvaille in controle.trouvailles]
            signalees = sorted(set(posees))
            interdites = sorted(set(posees) & set(SANS_FORCAGE))
            if interdites:
                print("  --forcer ne s'applique pas ici : %s."
                      % ", ".join(interdites), file=sys.stderr)
                print("  Une clé privée se remplace, un jeton connu se révoque, un "
                      "chemin de machine se retire — avant de publier, pas après.",
                      file=sys.stderr)
                return 1
            if not args.forcer:
                print("  Corriger la source, ou passer --forcer si c'est un "
                      "faux positif.", file=sys.stderr)
                return 1
            forcees = signalees
            print("  --forcer : publication malgré tout — %s."
                  % ", ".join(forcees))

        fichiers = sorted(p.relative_to(export) for p in export.rglob("*") if p.is_file())
        print("\nAperçu")
        print("──────")
        print("  Source  : %s" % source)
        print("  Cible   : %s" % cible)
        print("  Fichiers publiés : %d" % len(fichiers))
        print("  Vidés de leur contenu : %s" % ", ".join(PRIVE))
        print("  Jamais publiés        : %s" % ", ".join(JAMAIS))

        supprimes = chemins_a_supprimer(cible)
        print("  Entrées effacées dans la cible : %d" % len(supprimes))
        for chemin in supprimes:
            print("      - %s" % chemin)

        if not args.appliquer:
            print("\nAperçu seulement. Relancer avec --appliquer pour écrire "
                  "dans la cible.")
            return 0

        synchroniser(export, cible)

    print("\nÉcrit dans %s" % cible)
    diff = git(cible, "status", "--porcelain").strip()
    print("  %d entrée(s) au statut Git" % len(diff.splitlines()) if diff
          else "  Aucun changement — le public était déjà à jour.")

    if args.commit and diff:
        # La dérogation se relit là où elle compte : une publication forcée qui
        # ne le dit nulle part est indiscernable d'une publication propre, et
        # c'est ainsi qu'une fuite passe pour un oubli de contrôle.
        message = ("Synchronisation depuis le dépôt privé (%s)"
                   % git(source, "rev-parse", "--short", "HEAD").strip())
        if forcees:
            message += ("\n\nPublié malgré le contrôle de fuite (--forcer) :\n"
                        + "\n".join("- %s" % etiquette for etiquette in forcees))
        if controle.avertissements:
            # Le nombre, et rien d'autre : un avertissement peut tenir au nom
            # d'un fichier (`inventaire-nas-maison.md`), et `chemin:ligne` le
            # ferait entrer dans le message public. Le détail — fichier et ligne
            # — reste dans le rapport local, imprimé plus haut.
            message += ("\n\nPublié avec %d avertissement(s) de nom interdit, "
                        "relus avant publication." % len(controle.avertissements))
        git(cible, "add", "-A")
        git(cible, "commit", "-m", message)
        print("  Committé. La poussée reste à faire à la main — par une branche :")
        print("  la règle de main exige la vérification CI avant qu'un commit y arrive,")
        print("  une poussée directe est refusée.")
        print("    git -C %s push origin HEAD:refs/heads/publication/AAAA-MM-JJ" % cible)
        print("    puis pull request, vérification verte, fusion.")
    elif diff:
        print("  À relire puis committer : git -C %s diff --cached" % cible)

    return 0


if __name__ == "__main__":
    sys.exit(main())
