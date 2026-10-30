#!/usr/bin/env python3
"""
Génère le prompt système OBSIA à partir des frontmatters du coffre.

Usage :
    ./generer_prompt.py                          # affiche sur la sortie standard
    ./generer_prompt.py -o prompt-systeme.md     # écrit dans un fichier
    ./generer_prompt.py --mcp                    # affiche aussi la config MCP à faire
    ./generer_prompt.py --sans-profil            # ignore obsia.local.yml (pire cas)
    ./generer_prompt.py --racine /chemin/OBSIA
    ./generer_prompt.py --embarque depanneur-accompagne -o AGENTS-embarque.md
    ./generer_prompt.py --compact assistant      # prompt court, modèle à petit contexte
    ./generer_prompt.py --compact batisseur --phase cadrage

`--embarque` reprend le corps intégral de l'agent, **et** celui de chaque
skill qu'il déclare : un poste sans coffre ne peut charger un skill à la
demande, donc sa méthode doit être inlinée d'avance dans le prompt engendré.

Aucune dépendance externe : le frontmatter est lu par un analyseur minimal,
suffisant pour le format strict défini dans VAULT-CONTRACT.md.
"""

import argparse
import json
import re
import sys
from pathlib import Path

from convention_des_notes import extraire_frontmatter

RACINE_DEFAUT = Path(__file__).resolve().parent.parent

#: Le noyau du coffre : le contrat, seule source des règles. Le prompt engendré
#: n'en garde aucune copie à rafraîchir (§5) — il extrait ce qu'il lui faut au
#: moment de le poser.
NOYAU = Path("IA") / "system" / "VAULT-CONTRACT.md"

#: Le repère du §4 autour de la règle des secrets. Le commentaire HTML est muet :
#: il ne se rend nulle part, et le prompt ne reçoit que ce qui est **entre** les
#: deux. La règle n'existe donc qu'ici, et l'`AGENTS.md` l'obtient sans qu'on la
#: recopie — deux copies finiraient par diverger.
#:
#: Le haut et le bas sont distincts : un motif unique se reconnaîtrait deux fois.
REPERE_SECRETS_DEBUT = re.compile(r"^<!--\s*regle-secrets\s*:\s*debut\s*-->\s*$",
                                  re.MULTILINE)
REPERE_SECRETS_FIN = re.compile(r"^<!--\s*regle-secrets\s*:\s*fin\s*-->\s*$",
                                re.MULTILINE)

#: Le repère du §10 autour de la charte de concision. Même mécanique que la
#: règle des secrets : le prompt l'obtient entre les deux repères, la seule
#: copie vivante reste le noyau (§5). Commentaire HTML seul sur sa ligne, muet.
REPERE_CHARTE_DEBUT = re.compile(r"^<!--\s*charte-concision\s*:\s*debut\s*-->\s*$",
                                 re.MULTILINE)
REPERE_CHARTE_FIN = re.compile(r"^<!--\s*charte-concision\s*:\s*fin\s*-->\s*$",
                               re.MULTILINE)


#: Le repère du §2 autour de la règle d'écriture. Même mécanique que les deux
#: autres : le prompt l'obtient entre les repères, la seule copie vivante
#: reste le noyau (§5). Ce qu'il porte — où écrire, le preview, les générés —
#: n'arrive au prompt compact que par le §2 entier ; le prompt du coffre,
#: lui, ne porte pas le noyau : sans extraction, un agent qui ne l'ouvre pas
#: écrit de toute façon.
REPERE_ECRITURE_DEBUT = re.compile(r"^<!--\s*regle-ecriture\s*:\s*debut\s*-->\s*$",
                                    re.MULTILINE)
REPERE_ECRITURE_FIN = re.compile(r"^<!--\s*regle-ecriture\s*:\s*fin\s*-->\s*$",
                                  re.MULTILINE)


def regle_ecriture(racine: Path = RACINE_DEFAUT) -> str:
    """La règle d'écriture du §2 du contrat, entre ses repères, telle quelle.

    Rend "" quand le coffre n'a pas de noyau — les coffres des tests n'en
    ont pas — ou quand les repères ont disparu. Ce second cas n'est pas
    avalé en silence : un test tient le vrai contrat armé, sinon la règle
    quitterait tous les `AGENTS.md` engendrés sans que rien ne le dise.
    """
    try:
        contrat = (Path(racine) / NOYAU).read_text(encoding="utf-8")
    except OSError:
        return ""
    debut = REPERE_ECRITURE_DEBUT.search(contrat)
    fin = REPERE_ECRITURE_FIN.search(contrat)
    if debut is None or fin is None or fin.start() < debut.end():
        return ""
    return contrat[debut.end():fin.start()].strip("\n")


def charte_de_concision(racine: Path = RACINE_DEFAUT) -> str:
    """La charte de concision du §10, entre ses repères, telle quelle.

    Une seule copie vivante : le noyau (§5). Rend "" quand le coffre n'a pas
    de noyau — les coffres des tests n'en ont pas — ou quand les repères ont
    disparu ; ce second cas n'est pas avalé en silence : un test tient le
    vrai contrat armé, sinon la charte quitterait tous les `AGENTS.md`
    engendrés sans que rien ne le dise.
    """
    try:
        contrat = (Path(racine) / NOYAU).read_text(encoding="utf-8")
    except OSError:
        return ""
    debut = REPERE_CHARTE_DEBUT.search(contrat)
    fin = REPERE_CHARTE_FIN.search(contrat)
    if debut is None or fin is None or fin.start() < debut.end():
        return ""
    return contrat[debut.end():fin.start()].strip("\n")


def regle_des_secrets(racine: Path = RACINE_DEFAUT) -> str:
    """La règle des secrets du §4 du contrat, entre ses repères, telle quelle.

    Rendue ligne pour ligne, sans remise en forme : c'est ce qui la tient égale
    au contrat, et ce qu'un test vérifie ligne à ligne.

    Rend "" quand le coffre n'a pas de noyau — les coffres des tests n'en ont pas
    — ou quand les repères ont disparu. Ce second cas n'est pas avalé : un test
    tient le vrai contrat pour armé, sinon la règle quitterait tous les
    `AGENTS.md` engendrés sans que rien ne le dise.
    """
    try:
        contrat = (Path(racine) / NOYAU).read_text(encoding="utf-8")
    except OSError:
        return ""
    debut = REPERE_SECRETS_DEBUT.search(contrat)
    fin = REPERE_SECRETS_FIN.search(contrat)
    if debut is None or fin is None or fin.start() < debut.end():
        return ""
    return contrat[debut.end():fin.start()].strip("\n")

#: Ce qui introduit un chemin dans une phrase : le début de la ligne, ou un
#: séparateur. Un `/` collé à autre chose est le plus souvent du texte : `>` d'un
#: espace réservé (``0-PROJETS/<projet>/code/``), lettre d'un chemin relatif
#: (`IA/skills/`), barre d'une adresse (`https://…`).
_INTRODUCTEUR = r"(?:^|(?<=[\s(\[{`'\"=:,]))"

#: Un `/` qui ouvre un chemin ne doit pas être suivi d'un blanc ni d'un `/` : cela
#: écarte le `/` isolé de la prose (« et/ou », « 1/2 ») et le second d'une adresse.
_RACINE = r"/(?![\s/])"

#: Un chemin absolu de machine, sous les trois formes qu'il prend ici : racine
#: POSIX (`/srv`, `/home/moi/coffre/OBSIA`), relatif au foyer (`~/coffre`),
#: lecteur Windows (`C:\coffre`, `C:/coffre`).
#:
#: Le texte engendré ne doit en porter **aucun** : l'AGENTS.md est synchronisé
#: entre des postes où le coffre n'a ni le même chemin ni le même nom, et un
#: chemin de machine y serait faux partout ailleurs. Le repère qui tient partout
#: est le sous-dossier `OBSIA/`, pas un chemin.
#:
#: Un segment à espaces (`/home/moi/Mon coffre/OBSIA`) se reconnaît à son début.
CHEMIN_ABSOLU = re.compile(
    _INTRODUCTEUR + _RACINE                                  # /srv, /home/moi/…
    + r"|" + _INTRODUCTEUR + r"~/(?![\s/])"                  # ~/coffre
    + r"|(?<![\w])[A-Za-z]:[\\/]"                            # C:\coffre, C:/coffre
)


def chemins_absolus(texte: str) -> list[str]:
    """Les lignes du texte qui portent un chemin absolu, dans l'ordre.

    Rend la liste des lignes fautives, pas un booléen : qui constate veut voir
    laquelle, sinon il relit tout le fichier à la main.
    """
    return [ligne for ligne in texte.splitlines() if CHEMIN_ABSOLU.search(ligne)]


# ---------------------------------------------------------------- frontmatter

def lire_frontmatter(chemin: Path) -> dict | None:
    """Extrait le frontmatter YAML d'un fichier Markdown.

    Gère uniquement les formes prévues par le contrat : scalaires et listes
    à tirets. Renvoie None si le fichier n'a pas de frontmatter.
    """
    try:
        texte = chemin.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as err:
        print(f"  ! illisible : {chemin.name} ({err})", file=sys.stderr)
        return None

    return extraire_frontmatter(texte)[0]


def fichiers_declaratifs(dossier: Path) -> list[Path]:
    """Les fichiers de déclaration d'un dossier d'agents ou de skills.

    Deux formes admises (cf. VAULT-CONTRACT.md §5) :
      - `<dossier>/<nom>.md`         — forme plate, par défaut ;
      - `<dossier>/<nom>/<nom>.md`   — forme dossier, quand le skill grossit et
                                       s'accompagne de references/, scripts/…

    Le point d'entrée porte le nom du skill, pas `SKILL.md` : le §5 impose que
    le fichier porte le `name`, et le §6 l'unicité des noms de notes dans le
    coffre parent — une douzaine de `SKILL.md` la violerait.
    """
    if not dossier.is_dir():
        return []
    trouves = list(dossier.glob("*.md"))
    for sous in dossier.iterdir():
        if sous.is_dir() and not sous.name.startswith("."):
            entree = sous / (sous.name + ".md")
            if entree.is_file():
                trouves.append(entree)
    return sorted(trouves, key=lambda p: p.stem)


def collecter(dossier: Path, genre: str) -> list[dict]:
    """Récupère les frontmatters valides d'un dossier, triés par nom."""
    if not dossier.is_dir():
        print(f"  ! dossier absent : {dossier}", file=sys.stderr)
        return []

    resultats = []
    for fichier in fichiers_declaratifs(dossier):
        fm = lire_frontmatter(fichier)
        if not fm:
            print(f"  ! sans frontmatter : {fichier.name}", file=sys.stderr)
            continue
        if fm.get("kind") != genre:
            print(f"  ! kind « {fm.get('kind')} » inattendu : {fichier.name}",
                  file=sys.stderr)
            continue
        if not fm.get("description"):
            print(f"  ! description manquante : {fichier.name}", file=sys.stderr)
        fm["_fichier"] = fichier.relative_to(dossier).as_posix()
        resultats.append(fm)

    return resultats


def filtrer_par_profil(racine: Path, *collections: list[dict]) -> tuple:
    """Ne garde que ce qui appartient à un module retenu par `obsia.local.yml`.

    Sans profil, rien n'est filtré : c'est l'état du dépôt de distribution, et
    celui sous lequel la CI vérifie le coffre (§13). L'import est tardif parce
    que `modules` importe ce fichier — au chargement, il ne serait pas prêt.
    """
    import modules as _mod                       # tardif : cycle d'import assumé

    actifs = _mod.modules_actifs(racine)
    if actifs is None:
        return collections

    def garde(fm: dict) -> bool:
        return fm.get("module", "") in actifs

    return tuple([f for f in collection if garde(f)] for collection in collections)


def reduire_aux_actifs(agents: list[dict], skills: list[dict],
                       mcp_noms: set[str]) -> None:
    """Retire des agents les skills et MCP qu'un profil a écartés.

    Modifie les dictionnaires en mémoire, jamais les fichiers : en mode « en
    place » le catalogue reste intact sur le disque, seul ce qu'on en présente
    se réduit (§13).
    """
    presents = {s["name"] for s in skills}
    for ag in agents:
        if ag.get("skills"):
            ag["skills"] = [s for s in ag["skills"] if s in presents]
        if ag.get("mcp"):
            ag["mcp"] = [m for m in ag["mcp"] if m in mcp_noms]


# --------------------------------------------------------------------- rendu

def construire_prompt(agents: list[dict], skills: list[dict],
                      taches: list[dict] | None = None, regle: str = "",
                      charter: str = "", ecriture: str = "") -> str:
    lignes: list[str] = []
    a = lignes.append

    # §7.1 : deux racines distinctes — le coffre, où vit la mémoire, et le dépôt
    # OBSIA, où vivent les agents, les skills et le contrat. Les nommer toutes les
    # deux : un en-tête qui donnait le dépôt pour « racine du coffre » a fait
    # écrire un `0-SAVOIRS/` dans le dépôt de code, sous Goose et DeepSeek Harness.
    #
    # Les nommer sans aucun chemin absolu : l'AGENTS.md est synchronisé
    # (Syncthing) entre des postes où le coffre n'a ni le même chemin ni le même
    # nom. Un chemin de machine y serait faux partout ailleurs. D'où la `racine`
    # absente de cette fonction : le texte ne dépend que des déclarations — et de
    # la règle des secrets, reçue toute faite, qui ne porte pas de chemin non
    # plus (`regle_des_secrets` la lit dans le noyau, §4).
    #
    # Pas « le dossier qui contient ce fichier » pour autant : relecture faite, le
    # texte se pose ailleurs qu'à la racine du coffre — une copie annexée par un
    # harness qui n'a pas de fichier à lire (`.pi/APPEND_SYSTEM.md`, espace de
    # travail OpenClaw). Là, « ce fichier » désignerait le dossier d'accueil de la
    # copie. Le repère qui tient partout est le **sous-dossier `OBSIA/`**, que
    # seule la racine du coffre porte, et c'est là aussi que l'AGENTS.md est
    # engendré (`installer.chemin_agents`).
    a("Tu opères sur le coffre OBSIA.")
    a("Coffre (la mémoire) : le dossier qui contient le sous-dossier OBSIA/ — "
      "celui de l'AGENTS.md d'OBSIA.")
    a("Dépôt OBSIA (agents, skills, contrat) : son sous-dossier OBSIA/.")
    a("La mémoire s'écrit dans le coffre, jamais dans le dépôt OBSIA.")
    a("")

    # §4 : la règle des secrets se pose ici, en tête et hors de l'index, près de
    # l'en-tête des deux racines. Constat de la phase 2 (trois harness, deux
    # modèles, cinq cellules) : le test « secret » échouait partout — la règle est
    # au contrat, mais aucun agent n'ouvre le contrat pour ce cas. Elle vient du
    # contrat (`regle_des_secrets`), elle n'est pas écrite ici : une information
    # vit à un seul endroit (§5).
    # §2 et §7.3 : la règle d'écriture se pose avant les autres — un agent
    # qui n'ouvre jamais le noyau écrit de toute façon, et c'est sur les
    # emplacements qu'une séance dévoyée fait le plus de dégâts (constat au
    # coffre : un journal posé dans un projet, sans le contrat relu).
    if ecriture:
        a("## Écriture dans le coffre (§2, §7.3)")
        a("")
        a(ecriture)
        a("")

    if regle:
        a("## Secrets (§4)")
        a("")
        a(regle)
        a("")

    # §10 : la charte de concision se pose au même endroit, extraite du noyau
    # plutôt que recopiée — le constat de la phase 2 vaut pour elle aussi, et
    # la verbosité coûte à chaque réponse, pas une fois par séance.
    if charter:
        a("## Concision (§10)")
        a("")
        a(charter)
        a("")

    if agents:
        a("## Agents disponibles")
        a("")
        for ag in agents:
            marque = " [lecture seule]" if ag.get("read_only") else ""
            desc = ag.get("description", "(sans description)")
            a(f"- **{ag['name']}**{marque} — {desc}")
            details = []
            if ag.get("skills"):
                details.append("skills : " + ", ".join(ag["skills"]))
            if ag.get("mcp"):
                details.append("MCP : " + ", ".join(ag["mcp"]))
            if details:
                a(f"  ({' ; '.join(details)})")
        a("")

    if skills:
        a("## Skills disponibles")
        a("")
        a("Un skill se lit dans `IA/skills/` du dépôt, jamais dans le dossier")
        a("de skills du harness ; il ne se recopie ni ne se lie ailleurs.")
        a("Ici, la première phrase seulement : le quand et le quand-pas se lisent")
        a("dans le frontmatter du skill avant de l'ouvrir.")
        a("")
        from regenerate_index import premiere_phrase   # import tardif : regenerate_index importe ce module
        for sk in skills:
            marque = " [lecture seule]" if sk.get("read_only") else ""
            desc = premiere_phrase(sk.get("description", "(sans description)"))
            a(f"- **{sk['name']}**{marque} — {desc}")
        a("")

    if taches:
        a("## Tâches planifiées déclarées")
        a("")
        a("Registre : IA/tâches/ — il fait foi pour les tâches génériques. Un")
        a("second registre, privé et non publié, vit dans le coffre parent pour")
        a("les tâches propres à cette installation — une machine du parc de")
        a("l'utilisateur, ou son mainteneur ; les deux")
        a("comptent ensemble pour l'invariant ci-dessous (§12). Les timers ou")
        a("planificateurs qui les déclenchent ne sont que des instances")
        a("reconstructibles. Une tâche = au plus UNE instance vivante, tous")
        a("registres confondus : `exécutant` dit qui a le droit de la")
        a("déclencher, donc qui pas.")
        a("")
        for ta in taches:
            etat = "" if ta.get("actif") else " [suspendue]"
            a(f"- **{ta['name']}**{etat} — {ta.get('description', '(sans description)')}")
            a(f"  ({ta.get('quand', '?')}, {ta.get('fuseau', '?')}, "
              f"mode {ta.get('mode', '?')}, exécutant {ta.get('exécutant', '?')})")
        a("")

    a("## Méthode")
    a("")
    a("Lis en entier le noyau `IA/system/VAULT-CONTRACT.md` avant toute action.")
    a("Il fait foi sur toutes les règles (écriture, suppression, preview, sandbox,")
    a("secrets, frontmatter) ET sur la méthode à suivre pour toute demande (son")
    a("§10 : choix de l'agent, choix des skills/MCP, écriture en mémoire, citation")
    a("des chemins). Une annexe de `IA/system/contrat/` ne se lit qu'avant l'acte")
    a("que lui assigne le tableau du préambule du noyau. Ne déduis rien de ces")
    a("sujets d'une autre source, y compris de ce prompt — les listes ci-dessus")
    a("ne sont que l'index paresseux que le §10 te demande d'utiliser.")
    a("")
    a("0. Au démarrage, cherche tes carnets `statut: en cours` — dans l'arbre principal")
    a("   **et dans chaque worktree lié** — rapproche-les de l'état réel (§6) et propose")
    a("   de reprendre. Pendant la bascule, cherche aussi aux anciens emplacements")
    a("   (§6). Un agent `read_only: true` n'a pas de carnet : il saute cette étape.")

    return "\n".join(lignes)


def construire_config_mcp(agents: list[dict]) -> tuple[str, list[str]]:
    """Squelette de configuration MCP + liste des serveurs référencés."""
    serveurs = sorted({m for ag in agents for m in ag.get("mcp", [])})
    config = {
        "mcpServers": {
            nom: {
                "command": "À COMPLÉTER",
                "args": [],
                "env": {},
            }
            for nom in serveurs
        }
    }
    return json.dumps(config, indent=2, ensure_ascii=False), serveurs


# ------------------------------------------------------- fabrique du prompt

def declarations_reduites(racine: Path = RACINE_DEFAUT,
                          sans_profil: bool = False) -> tuple:
    """Les déclarations du coffre, réduites à son profil.

    Le point de passage unique : l'index d'un agent ne doit pas dépendre de
    qui l'a demandé. `main()` s'en sert pour la sortie standard, `installer.py`
    pour AGENTS.md.

    `sans_profil=True` saute `filtrer_par_profil` et rend le catalogue entier :
    le prompt d'un coffre sans profil, donc la taille la plus grande qu'il
    puisse prendre. C'est le régime de la CI, que `verifier_coffre.py` mesure
    pour alerter avant le plafond de consignes de Codex. La réduction aux
    déclarations actives, elle, reste appliquée : c'est une correction de
    cohérence, pas un effet de profil.
    """
    agents = collecter(racine / "IA" / "agents", "agent")
    skills = collecter(racine / "IA" / "skills", "skill")
    taches = collecter(racine / "IA" / "tâches", "tâche")
    mcp = collecter(racine / "IA" / "MCP", "mcp")

    if not sans_profil:
        agents, skills, taches, mcp = filtrer_par_profil(racine, agents, skills,
                                                         taches, mcp)
    reduire_aux_actifs(agents, skills, {m["name"] for m in mcp})
    return agents, skills, taches, mcp


def prompt_du_coffre(racine: Path = RACINE_DEFAUT,
                     sans_profil: bool = False) -> str | None:
    """Le prompt système du coffre, ou None si le coffre ne déclare rien.

    None n'est pas une erreur du coffre : c'est un profil qui ne retient rien
    d'utile, et l'appelant décide quoi en dire.

    `sans_profil=True` mesure le catalogue entier, profil ignoré — le pire cas
    de taille, celui sous lequel la CI vérifie (voir `declarations_reduites`).
    """
    agents, skills, taches, _ = declarations_reduites(racine,
                                                      sans_profil=sans_profil)
    if not agents and not skills:
        return None
    return construire_prompt(agents, skills, taches, regle_des_secrets(racine),
                             charter=charte_de_concision(racine),
                             ecriture=regle_ecriture(racine))


# ------------------------------------------------------------- mode embarqué

def corps_declaratif(chemin: Path) -> str | None:
    """Le corps Markdown d'un fichier déclaratif, frontmatter ôté.

    Rend None si le fichier ne se lit pas ou n'a pas de frontmatter : sans
    frontmatter ce n'est pas une déclaration, et le mode embarqué n'a rien
    à engendrer à partir d'elle.
    """
    if not lire_frontmatter(chemin):
        return None
    try:
        texte = chemin.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    fin = texte.find("\n---", 3)
    if fin == -1:
        return None
    return texte[fin + 4:].strip("\n")


def prompt_embarque(racine: Path = RACINE_DEFAUT,
                    nom_agent: str = "") -> str | None:
    """Le prompt autonome d'un agent, pour un poste sans coffre.

    Le déploiement embarqué — un harness posé sur une machine qui ne porte
    ni le dépôt OBSIA ni le coffre parent — ne peut pas suivre la méthode du
    §10 : pas de noyau à lire, pas d'index à consulter, pas de skills sur le
    disque. Le prompt porte donc tout ce dont l'agent dispose : un en-tête
    qui dit où il opère, la règle des secrets (même repère que partout,
    `regle_des_secrets`), le **corps intégral** du fichier de l'agent, et le
    corps de chaque skill qu'il déclare (`skills:` du frontmatter) — sur une
    machine sans coffre, un skill ne se charge pas à la demande : son corps
    doit être inliné d'avance, ou la méthode qu'il porte n'existe nulle part
    sur le poste.

    Le contexte propre au poste — qui le tient, sous quel nom lui parler,
    où vit le carnet — vit dans l'AGENTS.md du carnet, côté coffre parent :
    jamais dans ce prompt, jamais dans le dépôt (§7.3.1).

    Rend None si l'agent n'existe pas ou ne se lit pas : l'appelant décide
    quoi en dire.
    """
    chemin = Path(racine) / "IA" / "agents" / f"{nom_agent}.md"
    corps = corps_declaratif(chemin)
    if corps is None:
        return None
    fm_agent = lire_frontmatter(chemin) or {}

    lignes: list[str] = []
    a = lignes.append

    # Même raison d'être que l'en-tête du prompt du coffre, adapté au poste :
    # il n'y a ni deux racines ni sous-dossier OBSIA/ à nommer — juste une
    # session dont le dossier de travail est le carnet, et rien d'autre à
    # lire sur la machine.
    a("Tu opères sur un poste distant, sans accès au coffre OBSIA : ni son")
    a("dépôt, ni le coffre qui porte la mémoire, ne sont sur cette machine.")
    a("Les règles qui suivent font foi. Le dossier de travail de ta session")
    a("est le carnet du chantier : c'est ta seule écriture durable, et son")
    a("propriétaire y lit à distance ce qui s'y est écrit.")
    a("")

    regle = regle_des_secrets(racine)
    if regle:
        a("## Secrets")
        a("")
        a(regle)
        a("")

    a(corps)

    for nom_skill in fm_agent.get("skills") or []:
        chemin_skill = Path(racine) / "IA" / "skills" / f"{nom_skill}.md"
        if not chemin_skill.is_file():
            chemin_skill = Path(racine) / "IA" / "skills" / nom_skill / f"{nom_skill}.md"
        corps_skill = corps_declaratif(chemin_skill)
        if corps_skill is None:
            print(f"  ! skill déclaré mais introuvable, non inliné : {nom_skill}",
                  file=sys.stderr)
            continue
        a("")
        a("---")
        a("")
        a(corps_skill)

    return "\n".join(lignes)


# --------------------------------------------------------------- mode compact

#: Le plafond du prompt compact, en caractères : ce qu'un modèle local de 8 000
#: jetons garde de place pour la conversation une fois le prompt posé.
PLAFOND_COMPACT = 8000

#: La section du noyau que le prompt compact reprend telle quelle : qui écrit
#: où, le patch, le preview. Bornée par son titre et le suivant, pour ne garder
#: aucune copie à rafraîchir (§5).
SECTION_ECRITURE = re.compile(r"^## 2\. .*?(?=^##)", re.MULTILINE | re.DOTALL)


class NoyauIncomplet(ValueError):
    """Un noyau présent auquel manque une règle grave que le prompt compact porte."""


def section_ecriture(racine: Path = RACINE_DEFAUT) -> str:
    """Le §2 du noyau sans ses sous-sections, ou "" s'il n'y a pas de noyau.

    Un noyau présent sans §2 lève `NoyauIncomplet` : rendre "" ferait sortir
    la règle d'écriture du prompt sans que rien ne le dise.
    """
    try:
        contrat = (Path(racine) / NOYAU).read_text(encoding="utf-8")
    except OSError:
        return ""
    m = SECTION_ECRITURE.search(contrat)
    if m is None:
        raise NoyauIncomplet("le §2 (écriture) est introuvable dans le noyau")
    return m.group(0).strip("\n")


#: Les balises de phase d'une fiche d'agent (`contrat-frontmatter`) : un
#: commentaire HTML seul sur sa ligne, muet dans Obsidian.
BALISE_PHASE = re.compile(r"^<!--\s*phase\s*:\s*([a-z0-9-]+)\s*-->\s*$")
FIN_DE_PHASE = "fin"
SKILL_CITE = re.compile(r"`([a-z0-9-]+)`")


class BalisageInvalide(ValueError):
    """Une fiche dont les balises de phase ne s'ouvrent et ne se ferment pas."""


def decouper_en_phases(corps: str) -> tuple[str, dict[str, str]]:
    """(socle, {phase: section}) d'un corps de fiche, balises ôtées.

    Hors balises, c'est le socle : il entre dans tout prompt compact. Une
    phase ne s'imbrique pas, se ferme avant la suivante et ne se répète pas.
    """
    socle: list[str] = []
    phases: dict[str, list[str]] = {}
    ouverte = None
    for n, ligne in enumerate(corps.splitlines(), 1):
        m = BALISE_PHASE.match(ligne.strip())
        if not m:
            (phases[ouverte] if ouverte else socle).append(ligne)
            continue
        nom = m.group(1)
        if nom == FIN_DE_PHASE:
            if ouverte is None:
                raise BalisageInvalide(f"ligne {n} : fin de phase sans ouverture")
            ouverte = None
        elif ouverte is not None:
            raise BalisageInvalide(f"ligne {n} : phase « {nom} » ouverte dans « {ouverte} »")
        elif nom in phases:
            raise BalisageInvalide(f"ligne {n} : phase « {nom} » déjà définie")
        else:
            ouverte = nom
            phases[nom] = []
    if ouverte is not None:
        raise BalisageInvalide(f"phase « {ouverte} » jamais fermée")
    net = lambda L: re.sub(r"\n{3,}", "\n\n", "\n".join(L)).strip("\n")
    return net(socle), {k: net(v) for k, v in phases.items()}


def skills_par_phase(declares: list[str], socle: str,
                     phases: dict[str, str]) -> dict[str, list[str]]:
    """Les skills déclarés, rangés sous la première phase qui les cite.

    Un skill cité dans le socle, ou nulle part, est commun à toutes.
    """
    rang: dict[str, str] = {}
    cites_au_socle = set(SKILL_CITE.findall(socle))
    for phase, texte in phases.items():
        for nom in SKILL_CITE.findall(texte):
            rang.setdefault(nom, phase)
    groupes: dict[str, list[str]] = {"communs": []}
    groupes.update({p: [] for p in phases})
    for nom in declares:
        cle = "communs" if nom in cites_au_socle else rang.get(nom, "communs")
        groupes[cle].append(nom)
    return {k: v for k, v in groupes.items() if v}


def prompt_compact(racine: Path = RACINE_DEFAUT, nom_agent: str = "",
                   phase: str | None = None) -> str | None:
    """Le prompt court d'un agent, pour un modèle à petit contexte.

    Distinct du mode embarqué : le coffre est là, l'agent lit à la demande.
    Le prompt porte les seules règles graves du noyau — l'écriture et le
    preview (§2), les secrets (§4) —, le **socle** de la fiche, la section de
    la phase demandée s'il y en a une, et les skills **par nom seul**, groupés
    par phase : leur description se lit dans `skills-index.md`.

    Rend None si l'agent n'existe pas ou ne se lit pas. Lève
    `BalisageInvalide` sur une fiche mal balisée, `KeyError` sur une phase
    inconnue, `NoyauIncomplet` si le noyau existe sans l'une des deux règles.
    Ne tronque jamais : l'appelant compare à `PLAFOND_COMPACT` et refuse.
    """
    chemin = Path(racine) / "IA" / "agents" / f"{nom_agent}.md"
    corps = corps_declaratif(chemin)
    fm = lire_frontmatter(chemin) if corps is not None else None
    if corps is None or not fm:
        return None
    socle, phases = decouper_en_phases(corps)
    if phase is not None and phase not in phases:
        raise KeyError(phase)
    connus = {s["name"] for s in collecter(Path(racine) / "IA" / "skills", "skill")}
    declares = [n for n in fm.get("skills", []) if n in connus]

    lignes: list[str] = []
    a = lignes.append
    a("Tu es l'agent OBSIA `%s`. Ces règles font foi ; pour un acte qu'elles"
      % nom_agent)
    a("ne couvrent pas, lire `IA/system/VAULT-CONTRACT.md`.")
    a("")
    ecriture = section_ecriture(racine)
    if ecriture:
        a(ecriture)
        a("")
    regle = regle_des_secrets(racine)
    if not regle and (Path(racine) / NOYAU).is_file():
        raise NoyauIncomplet("la règle des secrets (§4) a perdu ses repères")
    if regle:
        a("## Secrets")
        a("")
        a(regle)
        a("")
    a(socle)
    if phases:
        a("")
        if phase is None:
            a("## Phases de cette fiche — aucune chargée")
            a("")
            a("Avant d'agir, relis dans `IA/agents/%s.md` la section de la phase qui"
              % nom_agent)
            a("s'applique : %s." % ", ".join("`%s`" % p for p in phases))
        else:
            a("## Phase chargée : `%s`" % phase)
            a("")
            a(phases[phase])
    if declares:
        a("")
        a("## Tes skills — `IA/skills/<nom>.md`, à lire avant d'en appliquer un")
        a("")
        # Phase chargée : ses skills et les communs seulement ; ceux des
        # autres phases se lisent avec elles, dans la fiche.
        for groupe, noms in skills_par_phase(declares, socle, phases).items():
            if phase is None or groupe in ("communs", phase):
                a("- %s : %s" % (groupe, ", ".join("`%s`" % n for n in noms)))
    return "\n".join(lignes)


# ---------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description="Génère le prompt système OBSIA.")
    ap.add_argument("--racine", type=Path, default=RACINE_DEFAUT,
                    help="racine du coffre (défaut : parent de ce script)")
    ap.add_argument("-o", "--sortie", type=Path,
                    help="fichier de sortie (défaut : sortie standard)")
    ap.add_argument("--mcp", action="store_true",
                    help="affiche aussi la configuration MCP à faire côté harness")
    ap.add_argument("--sans-profil", action="store_true",
                    help="ignore obsia.local.yml : le catalogue entier, le pire "
                         "cas que mesure verifier_coffre.py et la CI")
    ap.add_argument("--embarque", metavar="AGENT",
                    help="engendre le prompt autonome de cet agent pour un "
                         "poste sans coffre, au lieu du prompt du coffre")
    ap.add_argument("--compact", metavar="AGENT",
                    help="engendre le prompt court de cet agent (règles graves, "
                         "fiche, skills en une ligne), plafonné à %d caractères"
                         % PLAFOND_COMPACT)
    ap.add_argument("--phase", metavar="PHASE",
                    help="avec --compact : charge aussi cette section balisée "
                         "de la fiche")
    args = ap.parse_args()

    racine = args.racine.resolve()
    if not racine.is_dir():
        print(f"Racine introuvable : {racine}", file=sys.stderr)
        return 1

    if args.compact and args.embarque:
        print("--compact et --embarque s'excluent : un seul prompt à la fois.",
              file=sys.stderr)
        return 1

    if args.compact:
        try:
            prompt = prompt_compact(racine, args.compact, args.phase)
        except NoyauIncomplet as e:
            print(f"Noyau incomplet, aucun prompt compact : {e}", file=sys.stderr)
            return 1
        except BalisageInvalide as e:
            print(f"Balisage de phase invalide dans IA/agents/{args.compact}.md : "
                  f"{e}", file=sys.stderr)
            return 1
        except KeyError:
            print(f"Phase inconnue pour {args.compact} : {args.phase}",
                  file=sys.stderr)
            return 1
        if prompt is None:
            print(f"Agent introuvable ou illisible : {args.compact}",
                  file=sys.stderr)
            return 1
        # Tronquer ferait perdre une règle sans le dire : on refuse, et c'est
        # la fiche de l'agent qui s'allège.
        if len(prompt) > PLAFOND_COMPACT:
            print(f"Prompt compact trop long : {len(prompt)} caractères pour "
                  f"un plafond de {PLAFOND_COMPACT}. Alléger le socle de "
                  f"IA/agents/{args.compact}.md, ou en baliser une phase "
                  f"(contrat-frontmatter).", file=sys.stderr)
            return 1
        if args.sortie:
            args.sortie.write_text(prompt + "\n", encoding="utf-8")
            print(f"Écrit : {args.sortie}", file=sys.stderr)
        else:
            print(prompt)
        print(f"\n{len(prompt)} caractères.", file=sys.stderr)
        return 0

    if args.phase:
        print("--phase ne vaut qu'avec --compact.", file=sys.stderr)
        return 1

    if args.embarque:
        prompt = prompt_embarque(racine, args.embarque)
        if prompt is None:
            print(f"Agent introuvable ou illisible : {args.embarque}",
                  file=sys.stderr)
            return 1
        # Le prompt embarqué voyage vers d'autres machines : un chemin absolu
        # y serait faux partout, comme dans l'AGENTS.md du coffre. La garde
        # est ici, à l'engendrement : c'est le seul endroit qui voit tous les
        # prompts embarqués passer.
        fautifs = chemins_absolus(prompt)
        if fautifs:
            print("Un chemin absolu de machine a contaminé le prompt "
                  "embarqué :", file=sys.stderr)
            for ligne in fautifs:
                print(f"  · {ligne}", file=sys.stderr)
            return 1
        if args.sortie:
            args.sortie.write_text(prompt + "\n", encoding="utf-8")
            print(f"Écrit : {args.sortie}", file=sys.stderr)
        else:
            print(prompt)
        return 0

    agents, skills, taches, _ = declarations_reduites(racine,
                                                      sans_profil=args.sans_profil)
    if not agents and not skills:
        print("Aucun agent ni skill trouvé. Vérifie --racine.", file=sys.stderr)
        return 1

    prompt = construire_prompt(agents, skills, taches, regle_des_secrets(racine),
                               charter=charte_de_concision(racine),
                               ecriture=regle_ecriture(racine))
    if args.sortie:
        args.sortie.write_text(prompt + "\n", encoding="utf-8")
        print(f"Écrit : {args.sortie}", file=sys.stderr)
    else:
        print(prompt)

    print(f"\n{len(agents)} agent(s), {len(skills)} skill(s).", file=sys.stderr)

    if args.mcp:
        config, serveurs = construire_config_mcp(agents)
        if serveurs:
            print("\n--- À configurer dans le harness ---", file=sys.stderr)
            print("Serveurs MCP référencés par les agents :", file=sys.stderr)
            for nom in serveurs:
                print(f"  - {nom}", file=sys.stderr)
            print("\nSquelette de configuration :", file=sys.stderr)
            print(config, file=sys.stderr)
        else:
            print("\nAucun MCP référencé par les agents.", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
