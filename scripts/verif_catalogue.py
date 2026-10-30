"""Contrôles du catalogue : agents, skills, MCP, tâches, modules, profil,
renvois, chemins cités et fichiers générés.

Extraits de `verifier_coffre.py`, qui reste la porte d'entrée. Les contrôles
qui lisent l'état du vérificateur reçoivent un contexte `ctx` — `racine`,
`coffre`, `reduite`, `erreur`, `avertir`, `signaler` — construit au moment de
l'appel ; les autres sont des fonctions pures. Aucun état global ici.
"""

import re
import subprocess
import sys
from pathlib import Path

import modules as MOD
from commun import est_un_coffre_parent as _est_un_coffre_parent
from generer_prompt import lire_frontmatter

SCRIPTS = Path(__file__).resolve().parent

CHAMPS_COMMUNS = ("schema", "kind", "name", "description", "read_only")
CHAMPS_CONTRAT = ("schema", "kind", "name", "description")   # ni read_only, ni type
NOM_EXEMPT_CONTRAT = "registre.md"      # l'index du dossier, pas une annexe
NOM_VALIDE = re.compile(r"^[^\W_]+(?:-[^\W_]+)*$", re.UNICODE)   # minuscules-et-tirets, accents admis
TYPES_SKILL = ("core", "outil")


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


def verifier_fichier(ctx, chemin: Path, genre: str, champs_requis: tuple = CHAMPS_COMMUNS,
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
    rel = chemin.relative_to(ctx.racine)

    if fm is None:
        ctx.erreur(rel, "frontmatter absent ou non fermé")
        return None

    for champ in champs_requis:
        if champ not in fm:
            ctx.erreur(rel, "champ obligatoire manquant : `%s` (§5)" % champ)

    if fm.get("kind") != genre:
        ctx.erreur(rel, "`kind: %s` alors que le fichier est dans %s (§5)"
               % (fm.get("kind"),
                  emplacement or ("le dossier des %ss" % genre)))

    nom = fm.get("name")
    if nom:
        if nom != chemin.stem:
            ctx.erreur(rel, "`name: %s` ≠ nom du fichier `%s` (§5)" % (nom, chemin.stem))
        if not NOM_VALIDE.match(nom):
            ctx.erreur(rel, "`name: %s` — attendu : minuscules et tirets, sans espace (§5)" % nom)

    if "read_only" in champs_requis and not isinstance(fm.get("read_only"), bool):
        ctx.erreur(rel, "`read_only` doit valoir true ou false (§5)")

    if not isinstance(fm.get("schema"), int):
        ctx.erreur(rel, "`schema` doit être un entier (§5)")

    # description : présente, sur une seule ligne physique
    desc = fm.get("description")
    brute = ligne_description_brute(chemin)
    if not desc:
        ctx.erreur(rel, "`description` vide ou absente (§5)")
    elif desc.strip() in (">", "|", ">-", "|-"):
        ctx.erreur(rel, "`description` est un scalaire replié YAML — non géré par "
                    "lire_frontmatter(), la valeur devient « %s ». Une seule ligne physique."
               % desc.strip())
    elif brute and brute.rstrip().endswith((":", ">", "|")):
        ctx.erreur(rel, "`description` semble se poursuivre sur la ligne suivante — "
                    "une seule ligne physique est acceptée")

    if not fm.get("module"):
        ctx.erreur(rel, "champ obligatoire manquant : `module` (§13)")

    if genre == "skill" and fm.get("type") not in TYPES_SKILL:
        ctx.erreur(rel, "`type: %s` — attendu `core` ou `outil` (§5)" % fm.get("type"))

    for champ in ("skills", "mcp"):
        if champ in fm and not isinstance(fm[champ], list):
            ctx.erreur(rel, "`%s` vaut une chaîne, pas une liste — une entrée par ligne "
                        "précédée d'un tiret (§5)" % champ)

    if fm:
        fm["_chemin"] = rel
    return fm


# ---------------------------------------------------------------------- checks

TRANSPORTS = ("stdio", "http")
PERMISSIONS = ("normal", "elevated")


def verifier_mcp(ctx, dossier: Path) -> list[dict]:
    """Frontmatter des fichiers de IA/MCP/ (§5).

    Format distinct de celui des agents et des skills : pas de `read_only`,
    mais `transport` et `permission`.
    """
    resultats = []
    for chemin in sorted(dossier.glob("*.md")) if dossier.is_dir() else []:
        fm = lire_frontmatter(chemin)
        rel = chemin.relative_to(ctx.racine)
        if fm is None:
            ctx.erreur(rel, "frontmatter absent ou non fermé")
            continue
        for champ in ("schema", "kind", "name", "description", "type",
                      "transport", "permission"):
            if champ not in fm:
                ctx.erreur(rel, "champ obligatoire manquant : `%s` (§5)" % champ)
        if fm.get("kind") != "mcp":
            ctx.erreur(rel, "`kind: %s` attendu `mcp` (§5)" % fm.get("kind"))
        if fm.get("name") and fm["name"] != chemin.stem:
            ctx.erreur(rel, "`name: %s` ≠ nom du fichier `%s` (§5)" % (fm["name"], chemin.stem))
        if fm.get("transport") not in TRANSPORTS:
            ctx.erreur(rel, "`transport: %s` — attendu %s (§5)"
                   % (fm.get("transport"), " ou ".join(TRANSPORTS)))
        if fm.get("permission") not in PERMISSIONS:
            ctx.erreur(rel, "`permission: %s` — attendu %s (§5)"
                   % (fm.get("permission"), " ou ".join(PERMISSIONS)))
        fm["_chemin"] = rel
        resultats.append(fm)
    return resultats


MODES_TACHE = ("agent", "commande")
EXECUTANTS = ("local", "harness")
CORPS_ATTENDU = {"agent": "## Instruction", "commande": "## Commande"}


def verifier_taches(ctx, dossier: Path, agents: list[dict], *,
                    exclure: frozenset = frozenset()) -> list[dict]:
    """Frontmatter et corps des fichiers d'un registre de tâches (§5, §12).

    Sert aux deux registres : `IA/tâches/` et le registre privé du coffre
    (`verifier_taches_coffre`) — `module` reste obligatoire dans les deux
    (§5), mais seul celui du dépôt produit est confronté au catalogue
    installable (`verifier_appartenance`, §13) : le registre privé n'en fait
    pas partie.

    `exclure` nomme des fichiers à ignorer — vide pour `IA/tâches/`, qui n'en
    porte jamais ; `verifier_taches_coffre` y pose `sommaire.md` quand il
    porte la marque d'un fichier généré, pour ce seul appel. La décision
    reste chez l'appelant : cette fonction ne connaît rien de la mémoire du
    coffre ni des fichiers que `scripts/regenerate_sommaire.py`,
    `regenerate_index.py` ou `installer.py` écrivent (§11).

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
        if chemin.name in exclure:
            continue
        fm = lire_frontmatter(chemin)
        try:
            rel = chemin.relative_to(ctx.racine)
        except ValueError:
            rel = chemin.relative_to(ctx.coffre) if ctx.coffre.is_dir() else chemin
        if fm is None:
            ctx.erreur(rel, "frontmatter absent ou non fermé")
            continue

        for champ in ("schema", "kind", "name", "description",
                      "mode", "quand", "fuseau", "exécutant", "actif"):
            if champ not in fm:
                ctx.erreur(rel, "champ obligatoire manquant : `%s` (§5)" % champ)

        if fm.get("kind") != "tâche":
            ctx.erreur(rel, "`kind: %s` attendu `tâche` (§5)" % fm.get("kind"))
        if fm.get("name") and fm["name"] != chemin.stem:
            ctx.erreur(rel, "`name: %s` ≠ nom du fichier `%s` (§5)" % (fm["name"], chemin.stem))
        if fm.get("name") and not NOM_VALIDE.match(fm["name"]):
            ctx.erreur(rel, "`name: %s` — attendu : minuscules et tirets, sans espace (§5)"
                   % fm["name"])
        if not isinstance(fm.get("schema"), int):
            ctx.erreur(rel, "`schema` doit être un entier (§5)")
        if not isinstance(fm.get("actif"), bool):
            ctx.erreur(rel, "`actif` doit valoir true ou false (§5)")
        if not fm.get("description"):
            ctx.erreur(rel, "`description` vide ou absente (§5)")

        mode = fm.get("mode")
        if mode not in MODES_TACHE:
            ctx.erreur(rel, "`mode: %s` — attendu %s (§5)" % (mode, " ou ".join(MODES_TACHE)))

        # `quand` : cron à 5 champs, écrit entre guillemets
        brute = ligne_frontmatter_brute(chemin, "quand")
        if brute:
            valeur = brute.partition(":")[2].strip()
            if not (valeur.startswith(('"', "'")) and valeur.endswith(('"', "'"))):
                ctx.erreur(rel, "`quand` doit être écrit entre guillemets (§5) — sans eux, "
                            "une expression comme */15 * * * * est une ancre YAML invalide")
        quand = fm.get("quand")
        if isinstance(quand, str) and len(quand.split()) != 5:
            ctx.erreur(rel, "`quand: %s` — attendu cron à 5 champs "
                        "(minute heure jour-du-mois mois jour-de-semaine) (§5)" % quand)
        elif isinstance(quand, int):
            ctx.erreur(rel, "`quand` doit être une chaîne entre guillemets, pas un nombre (§5)")

        executant = fm.get("exécutant")
        if executant not in EXECUTANTS:
            ctx.erreur(rel, "`exécutant: %s` — attendu %s (§5). Sans lui, la "
                        "réconciliation ne sait pas où la tâche doit tourner et "
                        "peut créer un doublon (§12)."
                   % (executant, " ou ".join(EXECUTANTS)))
        elif executant == "harness" and mode == "commande":
            ctx.avertir(rel, "`mode: commande` avec `exécutant: harness` — un "
                         "planificateur distant n'atteint pas les fichiers de la "
                         "machine. Vérifier que ce harness tourne bien en local.")

        fuseau = fm.get("fuseau")
        if isinstance(fuseau, str) and "/" not in fuseau and fuseau != "UTC":
            ctx.avertir(rel, "`fuseau: %s` — attendu un identifiant IANA (`Europe/Paris`) "
                         "ou `UTC`" % fuseau)

        if mode == "agent":
            vise = fm.get("agent")
            if not vise:
                ctx.erreur(rel, "`mode: agent` sans champ `agent` (§5)")
            elif vise not in noms_agents:
                ctx.erreur(rel, "vise l'agent `%s`, qui n'a pas de fichier dans "
                            "IA/agents/ (§1)" % vise)
        elif mode == "commande" and fm.get("agent"):
            ctx.avertir(rel, "`mode: commande` avec un champ `agent` — ignoré au "
                         "déclenchement, à retirer")

        attendu = CORPS_ATTENDU.get(mode)
        if attendu and attendu not in chemin.read_text(encoding="utf-8"):
            ctx.erreur(rel, "corps sans section `%s` — la tâche ne déclenche rien (§5)"
                   % attendu)

        if not fm.get("module"):
            ctx.erreur(rel, "champ obligatoire manquant : `module` (§5)")

        fm["_chemin"] = rel
        resultats.append(fm)
    return resultats


def verifier_taches_coffre(ctx, taches_produit: list[dict], agents: list[dict]) -> list[dict]:
    """Registre privé du coffre (`Mon coffre/0-PROJETS/tâches-planifiées/`,
    §12) — tâches propres à cette installation. Mêmes règles que
    `verifier_taches`, `module` compris (§5) — mais sans le confronter au
    catalogue : ce registre ne fait pas partie des modules installables du
    dépôt produit (§13), aussi n'est-il jamais passé à `verifier_appartenance`.
    Rend silencieusement une liste vide si le coffre parent n'a pas ce dossier
    (CI, clone sans coffre) — avec un avertissement si le coffre, lui, existe.

    Un nom déclaré aux deux registres est un doublon (§12) : l'invariant d'une
    seule instance vivante ne tient pas si la même tâche existe deux fois.
    """
    dossier = ctx.coffre / "0-PROJETS" / "tâches-planifiées"
    if not dossier.is_dir():
        if _est_un_coffre_parent(ctx.coffre):
            ctx.avertir(ctx.coffre, "coffre parent trouvé, mais aucun registre "
                            "`0-PROJETS/tâches-planifiées/` — aucune tâche liée "
                            "au parc n'est lue (§12)")
        return []

    # Ce dossier vit sous `0-PROJETS/` : `regenerate_sommaire.py` y pose un
    # `sommaire.md` sans frontmatter comme à tout projet (§11). On ne
    # l'exempte que s'il porte bien sa marque de fichier généré — un fichier
    # nommé ainsi mais sans cette marque reste jugé comme une tâche, et donc
    # refusé pour de bonnes raisons.
    MARQUE_SOMMAIRE = "Généré par `scripts/regenerate_sommaire.py`"
    sommaire = dossier / "sommaire.md"
    exclure = frozenset({"sommaire.md"}) if (
        sommaire.is_file() and MARQUE_SOMMAIRE in sommaire.read_text(encoding="utf-8")
    ) else frozenset()

    resultats = verifier_taches(ctx, dossier, agents, exclure=exclure)
    noms_produit = {t["name"] for t in taches_produit if t.get("name")}
    for t in resultats:
        if t.get("name") in noms_produit:
            ctx.erreur(t["_chemin"], "nom `%s` déclaré aussi dans IA/tâches/ — un "
                                 "même nom ne vit pas aux deux registres (§12)"
                   % t["name"])
    return resultats


def verifier_references(ctx, agents, skills):
    """Un agent ne déclare que des skills et des MCP qui existent."""
    connus = {s["name"] for s in skills if s.get("name")}
    mcp_connus = {p.stem for p in (ctx.racine / "IA" / "MCP").glob("*.md")} \
        if (ctx.racine / "IA" / "MCP").is_dir() else set()

    for a in agents:
        for s in a.get("skills", []):
            if s not in connus:
                ctx.erreur(a["_chemin"], "déclare le skill `%s`, qui n'existe pas dans IA/skills/" % s)
        for m in a.get("mcp", []):
            if m not in mcp_connus:
                ctx.erreur(a["_chemin"], "déclare le MCP `%s`, qui n'existe pas dans IA/MCP/" % m)

    utilises = {s for a in agents for s in a.get("skills", [])}
    for s in skills:
        if s.get("name") and s["name"] not in utilises:
            ctx.avertir(s["_chemin"], "skill déclaré par aucun agent")

    actifs = {m for a in agents for m in a.get("mcp", [])}
    for p in sorted((ctx.racine / "IA" / "MCP").glob("*.md")) if (ctx.racine / "IA" / "MCP").is_dir() else []:
        if p.stem not in actifs:
            ctx.avertir(p.relative_to(ctx.racine),
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


def verifier_portee_des_renvois(ctx, agents, skills):
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
        chemin = ctx.racine / fm["_chemin"]
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
                ctx.avertir(fm["_chemin"],
                        "dit de charger `%s`, que %s ne déclare pas — consigne "
                        "inapplicable pour lui, ou frontière à énoncer (§10.2)"
                        % (vise, " et ".join("`%s`" % h for h in hors)))


def verifier_forme_dossier(ctx, dossier: Path, genre: str):
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
        rel = sous.relative_to(ctx.racine)
        if not entree.is_file():
            ctx.erreur(rel, "dossier de %s sans point d'entrée `%s.md` (§5). "
                        "Le point d'entrée porte le nom du dossier, pas `SKILL.md`."
                   % (genre, sous.name))
            continue

        corps = entree.read_text(encoding="utf-8")
        for annexe in sorted((sous / "references").glob("**/*")):
            if not annexe.is_file():
                continue
            if annexe.name not in corps:
                ctx.avertir(rel, "`references/%s` n'est cité nulle part dans `%s.md` — "
                             "un fichier qu'on ne sait pas exister n'est jamais lu"
                        % (annexe.relative_to(sous / "references").as_posix(), sous.name))


# Formes réelles sous lesquelles un nom d'agent apparaît dans le coffre :
#   l'agent `assistant`   ·   un agent « untel »   ·   agent[untel] --> …
# Le nom capturé doit ressembler à un nom : lettres, chiffres, tirets, espaces.
# Exclure « : » et « | » écarte `read_only: false` et les séparateurs de tableau.
AGENT_NOMME = re.compile(
    r"agents?\s*[«\"`\[]\s*([^\W\d_][\w \-]{1,39}?)\s*[»\"`\]]", re.UNICODE)


def verifier_agents_nommes(ctx, agents):
    """§1 : seul un agent qui a son fichier dans IA/agents/ peut être nommé.

    Nommer un agent avant qu'il existe le fait exister dans les têtes — c'est
    ainsi qu'un agent fantôme s'est installé dans ce coffre pendant des mois.
    """
    declares = {a["name"] for a in agents if a.get("name")}
    for chemin in sorted(ctx.racine.rglob("*.md")):
        if any(part.startswith(".") for part in chemin.relative_to(ctx.racine).parts):
            continue
        rel = chemin.relative_to(ctx.racine)
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
            ctx.signaler(rel, "nomme l'agent `%s`, qui n'a pas de fichier dans "
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


def verifier_chemins_cites(ctx):
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
    cibles = list((ctx.racine / "IA").rglob("*.md")) + list(ctx.racine.glob("*.md"))
    for chemin in sorted(cibles):
        rel = chemin.relative_to(ctx.racine)
        if any(part.startswith(".") for part in rel.parts):
            continue
        if rel.parts[:3] == ("IA", "system", "session-log"):
            continue
        texte = chemin.read_text(encoding="utf-8")
        hors_code = re.sub(r"```.*?```", "", texte, flags=re.S)

        for cite in sorted({m.group(1) for m in CHEMIN_CITE.finditer(hors_code)}):
            if GABARIT.search(cite) or (ctx.racine / cite).exists():
                continue
            ctx.signaler(rel, "cite le chemin `%s`, qui n'existe pas" % cite)

        # chemins relatifs : résolus depuis le fichier qui les cite
        for cite in sorted({m.group(1) for m in CHEMIN_RELATIF.finditer(hors_code)}):
            if GABARIT.search(cite) or vise_le_coffre_parent(cite):
                continue
            if (chemin.parent / cite).exists():
                continue
            ctx.signaler(rel, "cite le chemin relatif `%s`, qui ne mène nulle part "
                        "depuis ce fichier (§6)" % cite)

        # scripts appelés dans un bloc de code : eux s'exécutent
        for bloc in re.findall(r"```.*?```", texte, flags=re.S):
            for script in sorted({m.group(1) for m in SCRIPT_APPELE.finditer(bloc)}):
                if GABARIT.search(script) or vise_le_coffre_parent(script):
                    continue
                depuis_racine = (ctx.racine / script).exists()
                depuis_fichier = (chemin.parent / script).exists()
                if depuis_racine or depuis_fichier:
                    continue
                ctx.signaler(rel, "appelle le script `%s` dans un bloc de code, "
                            "et ce fichier n'existe pas (§11)" % script)

        for m in LIEN_MD.finditer(hors_code):
            cible = m.group(1).split("#")[0].strip()
            if (not cible or "://" in cible or cible.startswith("mailto:")
                    or GABARIT.search(cible)):
                continue
            if not (chemin.parent / cible).exists():
                ctx.signaler(rel, "lien Markdown cassé : `%s`" % cible)


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


def verifier_citations_de_memoire(ctx):
    """§13.5 : un fichier publié ne cite pas un chemin qui ne sera pas publié.

    `publier.py` vide `brouillon/`, `.archive/` et `IA/system/session-log/` au
    passage vers le public. Un chemin qui les vise depuis `IA/` ou depuis la
    racine mène donc nulle part dans la distribution — et l'export échoue, loin
    de l'endroit où la faute a été écrite. Autant la voir ici.

    Ce n'est pas une interdiction de *renvoyer* à une note privée : la nommer
    suffit, et c'est déjà la règle du §7.5 pour les rétroliens — un lien par
    nom survit aux déplacements, un lien par chemin casse.
    """
    for chemin in sorted(ctx.racine.rglob("*.md")):
        rel = chemin.relative_to(ctx.racine)
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
            ctx.erreur(rel, "cite le chemin `%s`, qui ne sera pas publié : cette "
                        "zone est vidée à la publication. Nommer la note "
                        "suffit (§13.5)." % cite)


PREFIXES_SONDE = ("commande", "fichier", "distribution", "parent")


def verifier_modules(ctx, dossier: Path) -> list[dict]:
    """§13 : le catalogue de modules — frontmatter, sondes, dépendances.

    Un module mal formé ne casse rien tant qu'on installe tout ; il casse
    l'installation partielle, c'est-à-dire précisément le cas qu'on ne teste
    jamais avant de le vivre.
    """
    modules: list[dict] = []
    if not dossier.is_dir():
        ctx.erreur("IA/system/modules/", "catalogue de modules absent (§13)")
        return modules

    for chemin in sorted(dossier.glob("*.md")):
        fm = lire_frontmatter(chemin)
        rel = chemin.relative_to(ctx.racine)
        if fm is None:
            ctx.erreur(rel, "frontmatter absent ou non fermé")
            continue
        if fm.get("kind") != "module":
            ctx.erreur(rel, "`kind: %s` alors que le fichier est dans IA/system/modules/ (§13)"
                   % fm.get("kind"))
            continue

        nom = fm.get("name")
        if nom != chemin.stem:
            ctx.erreur(rel, "`name: %s` ≠ nom du fichier `%s` (§5)" % (nom, chemin.stem))
        if nom and not NOM_VALIDE.match(nom):
            ctx.erreur(rel, "`name: %s` — attendu : minuscules et tirets, sans espace (§5)" % nom)
        if not isinstance(fm.get("schema"), int):
            ctx.erreur(rel, "`schema` doit être un entier (§5)")
        if not fm.get("description"):
            ctx.erreur(rel, "`description` vide ou absente (§5)")
        if not isinstance(fm.get("essentiel"), bool):
            ctx.erreur(rel, "`essentiel` doit valoir true ou false (§13)")

        for champ in ("requiert", "sondes"):
            if champ in fm and not isinstance(fm[champ], list):
                ctx.erreur(rel, "`%s` doit être une liste à tirets, pas « %s » (§5)"
                       % (champ, fm[champ]))

        if not fm.get("essentiel") and not fm.get("question"):
            ctx.erreur(rel, "module non essentiel sans `question` — l'installeur "
                        "n'aurait rien à demander (§13)")

        for sonde in fm.get("sondes", []) if isinstance(fm.get("sondes"), list) else []:
            prefixe = sonde.split(":", 1)[0]
            if prefixe not in PREFIXES_SONDE:
                ctx.erreur(rel, "sonde `%s` — préfixe inconnu, attendu %s (§13)"
                       % (sonde, " | ".join(PREFIXES_SONDE)))
            elif ":" not in sonde or not sonde.split(":", 1)[1].strip():
                ctx.erreur(rel, "sonde `%s` — valeur vide (§13)" % sonde)

        fm["_chemin"] = rel
        fm.setdefault("requiert", [])
        fm.setdefault("sondes", [])
        modules.append(fm)

    noms = {m.get("name") for m in modules}
    if "noyau" not in noms:
        ctx.erreur("IA/system/modules/", "aucun module `noyau` — le socle doit exister (§13)")

    for m in modules:
        for besoin in m["requiert"] if isinstance(m["requiert"], list) else []:
            if besoin not in noms:
                ctx.erreur(m["_chemin"], "`requiert: %s` — module inexistant (§13)" % besoin)

    # Un cycle de dépendances boucle la résolution de l'installeur.
    par_nom = {m["name"]: m for m in modules if m.get("name")}
    for depart in sorted(par_nom):
        vus, pile = set(), [depart]
        while pile:
            courant = pile.pop()
            for besoin in par_nom.get(courant, {}).get("requiert", []):
                if besoin == depart:
                    ctx.erreur(par_nom[depart]["_chemin"],
                           "cycle de dépendances entre modules : %s → … → %s (§13)"
                           % (depart, depart))
                    pile = []
                    break
                if besoin not in vus:
                    vus.add(besoin)
                    pile.append(besoin)

    return modules


def verifier_profil(ctx, modules: list[dict]) -> None:
    """§13 : le profil ne doit citer que des modules du catalogue.

    Avertissement et non erreur. Sans profil — le cas de la CI — il n'y a rien
    à dire. Avec un profil fautif, le coffre n'est pas incohérent : il est plus
    maigre que voulu, et c'est justement ce qu'on ne comprend pas quand on le
    découvre après l'installation.
    """
    import modules as _mod                       # tardif, comme dans generer_prompt

    profil = _mod.lire_profil(ctx.racine)
    if profil is None:
        return

    for nom in sorted(_mod.modules_inconnus(modules, profil.get("modules", []))):
        ctx.avertir(_mod.NOM_PROFIL,
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


def module_declare(ctx, chemin, module, noms: set) -> bool:
    """Le `module` d'une déclaration existe-t-il dans le catalogue (§13) ?"""
    if not module:
        ctx.erreur(chemin, "ne déclare aucun `module` — inclassable à "
                       "l'installation (§13)")
        return False
    if module not in noms:
        ctx.erreur(chemin, "`module: %s` — module inexistant dans "
                       "IA/system/modules/ (§13)" % module)
        return False
    return True


def verifier_appartenance(ctx, modules, agents, skills, mcp, taches):
    """§13 : tout ce qui se déclare appartient à un module du catalogue."""
    noms = {m.get("name") for m in modules}
    peuples = set()

    for fm in list(agents) + list(skills) + list(mcp) + list(taches):
        chemin = fm.get("_chemin", fm.get("name", "?"))
        if module_declare(ctx, chemin, fm.get("module"), noms):
            peuples.add(fm["module"])

    if ctx.reduite:
        return              # ici, un module sans déclaration est un module écarté
    for m in modules:
        if m.get("name") not in peuples:
            ctx.avertir(m["_chemin"], "module qu'aucun agent, skill, MCP ou tâche "
                                  "ne rejoint — il n'installerait rien (§13)")


def verifier_annexes_contrat(ctx, dossier: Path, modules: list[dict]) -> list[dict]:
    """Les annexes du noyau, `IA/system/contrat/*.md` (§5, §13).

    Une annexe est un document déclaratif : elle se définit **par son dossier**,
    pas par son nom. Tout `*.md` de `IA/system/contrat/` est donc contrôlé comme
    une annexe, à une seule exception, `registre.md`, nommée ici : c'est l'index
    du dossier, sans frontmatter. Définir l'annexe par le préfixe `contrat-`
    laisserait une annexe renommée sortir du filet sans que rien ne le dise.

    Le frontmatter est vérifié par `verifier_fichier(ctx)`, appelé avec
    `CHAMPS_CONTRAT = (schema, kind, name, description)` : une annexe n'a ni
    `read_only` — elle ne s'exécute pas — ni `type`, réservé aux skills. Le
    contrôle exige en plus un `module` non vide (comme pour toute fiche), et
    `module_declare(ctx)` vérifie que ce module existe au catalogue.

    Les chemins qu'une annexe cite sont, eux, déjà contrôlés par
    `verifier_chemins_cites(ctx)` : tout `IA/**/*.md` y passe, le dossier compris,
    et les chemins **relatifs** sont résolus depuis le fichier qui les cite —
    `../VAULT-CONTRACT.md` depuis ici mène bien à `IA/system/VAULT-CONTRACT.md`.
    Aucune cible de ce dossier n'échappe au filet.

    Une annexe ne peuple pas son module : une déclaration dit à quoi elle
    appartient, elle n'installe rien. Seuls agents, skills, MCP et tâches
    comptent comme occupants (§13), sans quoi une annexe suffirait à faire
    passer un module vide pour un module habité.
    """
    if not dossier.is_dir():
        ctx.avertir(dossier.relative_to(ctx.racine),
                "dossier des annexes du contrat absent — aucune annexe contrôlée "
                "(§5, §13)")
        return []
    noms = {m.get("name") for m in modules}
    annexes: list[dict] = []
    for chemin in sorted(dossier.glob("*.md")):
        if chemin.name == NOM_EXEMPT_CONTRAT:
            continue
        fm = verifier_fichier(ctx, chemin, "contract", CHAMPS_CONTRAT,
                              "le dossier des annexes du contrat")
        if fm is None:
            continue
        module_declare(ctx, fm["_chemin"], fm.get("module"), noms)
        annexes.append(fm)
    return annexes


def verifier_renvois_entre_modules(ctx, modules, skills):
    """Un skill renvoie-t-il vers un skill qu'une installation partielle n'aura pas ?

    Pendant du contrôle de portée par agent (§10.2), mais au niveau du
    catalogue : si `A` dit « charger `B` » et que le module de `B` n'est pas
    entraîné par celui de `A`, la consigne tombe dans le vide chez qui n'a
    installé que le premier. Avertissement, pas erreur : la détection repose
    sur le verbe, et la frontière peut être voulue.
    """
    if ctx.reduite:
        return              # le contrôle porte sur le catalogue, pas sur une copie
    par_nom = {s["name"]: s for s in skills if s.get("name")}
    for nom, fm in par_nom.items():
        mien = fm.get("module")
        if not mien:
            continue
        entraines = cloture(modules, mien)
        try:
            texte = (ctx.racine / fm["_chemin"]).read_text(encoding="utf-8")
        except OSError:
            continue
        vises = {m.group(1) for m in CONSIGNE_SKILL.finditer(texte)} & set(par_nom)
        for vise in sorted(vises - {nom}):
            sien = par_nom[vise].get("module")
            if sien and sien not in entraines:
                ctx.avertir(fm["_chemin"],
                        "dit de charger `%s`, du module `%s` que `%s` n'entraîne "
                        "pas — consigne absente d'une installation partielle (§13)"
                        % (vise, sien, mien))


def verifier_derives(ctx):
    """Les index doivent être à jour vis-à-vis de leurs sources.

    Les sommaires de `mémoire/` n'en font plus partie : ils ne sont pas
    versionnés (§11), donc un clone neuf — celui de la CI — n'en a pas, et
    les exiger reviendrait à refuser tout clone propre.

    `--racine` dit quel coffre juger : sans lui, le générateur indexe la racine
    du produit, c'est-à-dire la machine, quel que soit le `--coffre` reçu. Un
    contrôle qui juge un autre coffre que celui qu'on lui donne ne prouve rien ;
    c'est pourtant ce qu'il faisait, et aucun test ne pouvait le voir.
    """
    for script, quoi in (("regenerate_index.py", "index"),):
        res = subprocess.run([sys.executable, str(SCRIPTS / script),
                              "--racine", str(ctx.racine), "--verifier"],
                             capture_output=True, text=True, cwd=str(ctx.racine))
        if res.returncode != 0:
            detail = (res.stderr or res.stdout).strip().replace("\n", " / ")
            ctx.erreur("scripts/%s" % script, "%s périmés — %s" % (quoi, detail))
