"""Contrôles du contrat : taille du noyau, règle des secrets, clauses datées,
taille et chemins d'AGENTS.md.

Extraits de `verifier_coffre.py`, qui reste la porte d'entrée : il appelle ces
fonctions en leur passant la racine du dépôt et ses deux compteurs, `erreur` et
`avertir`. Aucun état global ici.
"""

import contextlib
import io
import re
from datetime import date
from pathlib import Path

from commun import contenu_agents
from generer_prompt import chemins_absolus, prompt_du_coffre, regle_des_secrets

# AGENTS.md est lu par Codex, qui ne retient en tout que 32 Kio de consignes :
# le fichier global (~/.codex/AGENTS.md) et ceux du projet comptent **ensemble**.
# Au-delà, le surplus est laissé de côté — sans erreur, sans avertissement ;
# l'agent perd des agents et des skills entiers sans que rien ne le dise.
# On mesure le pire cas — le catalogue entier, sans profil, comme la CI — et on
# avertit dès 28 Kio : les 4 Kio de marge couvrent un fichier global, et
# laissent le temps de réduire avant que le surplus ne soit écarté.
TAILLE_FICHIER_AGENTS_AVERTISSEMENT = 28 * 1024     # 28 672 o
TAILLE_FICHIER_AGENTS_ERREUR = 32 * 1024            # 32 768 o

# Le noyau du contrat (`IA/system/VAULT-CONTRACT.md`) est lu **en entier** par
# tout agent au démarrage : c'est un coût payé à chaque séance, pas un détail.
# Son plafond en mots vit dans son **unique** endroit déclaré — la table de
# `CONSTRAINTS.md`, ligne « Noyau du contrat », comme le plancher de tests. La
# mesure est `len(texte.split())`, identique à `wc -w`. Relever le plafond se
# décide dans une PR (§11), jamais en silence.
NOYAU = Path("IA") / "system" / "VAULT-CONTRACT.md"
LIBELLE_PLAFOND_NOYAU = "Noyau du contrat"

# Une échéance datée dans le noyau s'écrit en ISO `AAAA-MM-JJ` — la seule forme
# admise. Passé le jour, le contrôle avertit : une clause périmée laisse croire
# qu'un régime tient encore.
CLAUSE_DATEE = re.compile(r"\d{4}-\d{2}-\d{2}")


def verifier_taille_du_fichier_agents(racine, erreur, avertir):
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
        prompt = prompt_du_coffre(racine, sans_profil=True)
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


def plafond_du_noyau(racine, chemin=None):
    """Le plafond du noyau, lu à son **unique** endroit déclaré : `CONSTRAINTS.md`.

    Le nombre ne vit qu'ici — dans la table, ligne « Noyau du contrat », comme le
    plancher de tests — et nulle part ailleurs : une seconde copie finirait par
    diverger de la première, et c'est celle qu'on croit qui ment. Rend ``None``
    quand le document ou la ligne manquent : c'est à l'appelant de dire si cela
    doit être une erreur.
    """
    chemin = Path(chemin) if chemin else racine / "CONSTRAINTS.md"
    if not chemin.is_file():
        return None
    for ligne in chemin.read_text(encoding="utf-8").splitlines():
        nue = ligne.strip()
        if not nue.startswith("|"):
            continue
        champs = [champ.strip() for champ in nue.strip("|").split("|")]
        if len(champs) < 2 or champs[0] != LIBELLE_PLAFOND_NOYAU:
            continue
        trouve = re.search(r"≤\s*\**\s*(\d[\d\s]*)", nue)
        if trouve:
            return int(re.sub(r"\s", "", trouve.group(1)))
    return None


def mots_du_noyau(racine, chemin=None) -> int:
    """Le nombre de mots du noyau, à la manière de `wc -w`.

    `len(texte.split())` compte les suites de caractères non blancs exactement
    comme `wc -w` : la mesure annoncée est celle qu'on peut rejouer en ligne de
    commande, sans outil du dépôt.
    """
    chemin = Path(chemin) if chemin else racine / NOYAU
    return len(chemin.read_text(encoding="utf-8").split())


def verifier_taille_du_noyau(racine, erreur):
    """Le noyau du contrat tient sous son plafond, et on le dit à chaque passage.

    Le noyau est lu **en entier** par tout agent au démarrage : sa taille est un
    coût payé à chaque séance, pas un détail. Le plafond vit dans son unique
    endroit déclaré (`CONSTRAINTS.md`, ligne « Noyau du contrat ») ; le relever
    se décide dans une PR (§11), jamais en silence. La mesure est celle de
    `wc -w` ; l'écart est la marge restante avant le plafond.

    Rend la ligne à afficher — taille, plafond, écart — ou ``None`` s'il n'y a
    pas de noyau à mesurer : un clone sans noyau, ou un dossier de mémoire, n'a
    rien à dire ici (le second n'a pas non plus de `CONSTRAINTS.md`).
    """
    chemin_noyau = racine / NOYAU
    chemin_plafond = racine / "CONSTRAINTS.md"
    if not chemin_noyau.is_file() or not chemin_plafond.is_file():
        return None

    mots = mots_du_noyau(racine, chemin_noyau)
    plafond = plafond_du_noyau(racine, chemin_plafond)
    if plafond is None:
        erreur("CONSTRAINTS.md",
               "le plafond du noyau du contrat n'est pas déclaré : la table doit "
               "porter une ligne « %s » avec un nombre de mots (`≤ N mots`) — "
               "sans elle, le noyau peut grossir sans que rien ne le dise"
               % LIBELLE_PLAFOND_NOYAU)
        return "Noyau du contrat : %d mots, plafond non déclaré." % mots

    if mots > plafond:
        erreur("IA/system/VAULT-CONTRACT.md",
               "le noyau pèse %d mots, %d au-dessus du plafond de %d : le noyau "
               "est lu en entier à chaque séance — le ramener sous le plafond, "
               "ou relever le plafond dans une PR (§11), jamais en silence"
               % (mots, mots - plafond, plafond))
    return ("Noyau du contrat : %d mots sur %d (marge %d)."
            % (mots, plafond, plafond - mots))


def verifier_regle_des_secrets(racine, erreur):
    """Le bloc de la règle des secrets (§4) est là, entre ses repères.

    `generer_prompt.regle_des_secrets` rend ``""`` quand les repères
    `regle-secrets` disparaissent du noyau : le prompt engendré — et donc
    l'`AGENTS.md` lu par l'agent — perdent alors la règle **en silence**, alors
    qu'elle est la seule porte qui protège les secrets (§4, §5). Le générateur a
    beau être tenu par un test, ce test vit dans le dépôt produit ; ce contrôle-ci
    le dit depuis le coffre, là où l'amendement du §4 atterrit.

    Rend la ligne à afficher, ou ``None`` s'il n'y a pas de noyau à lire : un
    clone sans contrat n'a rien à dire ici.
    """
    chemin_noyau = racine / NOYAU
    if not chemin_noyau.is_file():
        return None

    bloc = regle_des_secrets(racine)
    if not bloc.strip():
        erreur("IA/system/VAULT-CONTRACT.md",
               "le bloc de la règle des secrets (§4, repères `regle-secrets`) est "
               "vide ou introuvable : le prompt engendré — et l'`AGENTS.md` lu par "
               "l'agent — perdent la règle en silence ; rétablir le bloc entre ses "
               "repères (§4, §5)")
        return "Règle des secrets : bloc vide ou introuvable."

    return ("Règle des secrets : %d caractères, entre ses repères."
            % len(bloc))


def verifier_clauses_datees_du_noyau(racine, avertir, aujourdhui=None):
    """Une clause datée du noyau ne survit pas à sa date.

    Forme reconnue : une date ISO `AAAA-MM-JJ` écrite dans le noyau — la seule
    admise pour y dater une échéance (« se retire au plus tard le 2026-12-31 »).
    Passé le jour, l'avertissement dit la ligne et la date : une échéance
    dépassée laisse croire qu'un régime tient encore, et le contrat doit être
    nettoyé ou la clause redatée. Un avertissement suffit — toutes les dates du
    noyau ne sont pas des échéances, et la relecture humaine tranche.

    Une date **bien formée mais inexistante** (`2028-02-30`, `2026-13-01`) est
    dite « illisible » : `date.fromisoformat` lèverait une `ValueError`, qui
    sortirait le vérificateur en traceback et refuserait un coffre cohérent pour
    une faute de frappe. On avertit, on ne s'arrête pas.

    `aujourdhui` n'existe que pour le test.
    """
    chemin = racine / NOYAU
    if not chemin.is_file():
        return
    if aujourdhui is None:
        aujourdhui = date.today()
    for numero, ligne in enumerate(chemin.read_text(encoding="utf-8").splitlines(), 1):
        for trouve in CLAUSE_DATEE.finditer(ligne):
            ecrite = trouve.group(0)
            try:
                echeance = date.fromisoformat(ecrite)
            except ValueError:
                avertir("IA/system/VAULT-CONTRACT.md",
                        "date illisible, ligne %d : « %s » a la forme d'une date "
                        "sans en être une — la corriger, ou l'écrire autrement "
                        "si ce n'est pas une échéance" % (numero, ecrite))
                continue
            if echeance >= aujourdhui:
                continue
            avertir("IA/system/VAULT-CONTRACT.md",
                    "clause datée périmée, ligne %d : la date %s est passée — "
                    "retirer la clause ou la redater, une échéance dépassée "
                    "laisse croire qu'un régime tient encore"
                    % (numero, ecrite))


def verifier_chemins_du_prompt(racine, erreur):
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
        prompt = prompt_du_coffre(racine, sans_profil=True)
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
