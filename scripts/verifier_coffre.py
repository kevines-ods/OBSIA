#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vérifie la cohérence du coffre OBSIA. N'écrit rien.

Le contrat pose des règles strictes (§5 frontmatter, §6 nommage) que rien ne
contrôlait : un index a pu affirmer pendant des mois qu'un agent disposait de
skills qu'il ne déclarait pas. Ce script confronte les fichiers entre eux.

Sort 0 si tout est cohérent, 1 sinon. Prévu pour la CI comme pour la main.

Usage :
    python3 scripts/verifier_coffre.py
    python3 scripts/verifier_coffre.py --silencieux   # n'affiche que les erreurs
"""

import os
import re
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from generer_prompt import RACINE_DEFAUT, fichiers_declaratifs, lire_frontmatter

RACINE = RACINE_DEFAUT

CHAMPS_COMMUNS = ("schema", "kind", "name", "description", "read_only")
NOM_VALIDE = re.compile(r"^[^\W_]+(?:-[^\W_]+)*$", re.UNICODE)   # minuscules-et-tirets, accents admis
TYPES_SKILL = ("core", "outil")

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


def verifier_fichier(chemin: Path, genre: str) -> dict | None:
    fm = lire_frontmatter(chemin)
    rel = chemin.relative_to(RACINE)

    if fm is None:
        erreur(rel, "frontmatter absent ou non fermé")
        return None

    for champ in CHAMPS_COMMUNS:
        if champ not in fm:
            erreur(rel, "champ obligatoire manquant : `%s` (§5)" % champ)

    if fm.get("kind") != genre:
        erreur(rel, "`kind: %s` alors que le fichier est dans le dossier des %ss (§5)"
               % (fm.get("kind"), genre))

    nom = fm.get("name")
    if nom:
        if nom != chemin.stem:
            erreur(rel, "`name: %s` ≠ nom du fichier `%s` (§5)" % (nom, chemin.stem))
        if not NOM_VALIDE.match(nom):
            erreur(rel, "`name: %s` — attendu : minuscules et tirets, sans espace (§5)" % nom)

    if not isinstance(fm.get("read_only"), bool):
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
CONSIGNE_SKILL = re.compile(r"(?:charger|c'est|relève de)\s+`([^\W_][\w-]{2,39})`")

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
CHEMIN_CITE = re.compile(
    r"`((?:IA|scripts|mémoire|brouillon)/[^`\s]+\.(?:md|py|json|yml|sh))`")
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
# Un chemin qui les vise n'est pas cassé, il désigne autre chose.
COFFRE_PARENT = ("-SAVOIRS", "-PROJETS", "-DOCUMENTS", "-PERSONNELS",
                 "-EN-VRAC", "_maintenance", "Mon coffre")


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
    faux **agit**. `mémoire/` est un récit, où une note ancienne cite
    légitimement un état révolu ou reproduit un extrait d'index.

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


def verifier_appartenance(modules, agents, skills, mcp, taches):
    """§13 : tout ce qui se déclare appartient à un module du catalogue."""
    noms = {m.get("name") for m in modules}
    peuples = set()

    for fm in list(agents) + list(skills) + list(mcp) + list(taches):
        chemin = fm.get("_chemin", fm.get("name", "?"))
        module = fm.get("module")
        if not module:
            erreur(chemin, "ne déclare aucun `module` — inclassable à "
                           "l'installation (§13)")
        elif module not in noms:
            erreur(chemin, "`module: %s` — module inexistant dans "
                           "IA/system/modules/ (§13)" % module)
        else:
            peuples.add(module)

    if REDUITE:
        return              # ici, un module sans déclaration est un module écarté
    for m in modules:
        if m.get("name") not in peuples:
            avertir(m["_chemin"], "module qu'aucun agent, skill, MCP ou tâche "
                                  "ne rejoint — il n'installerait rien (§13)")


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
    """Index et sommaires doivent être à jour vis-à-vis de leurs sources."""
    for script, quoi in (("regenerate_index.py", "index"),
                         ("regenerate_sommaire.py", "sommaires")):
        res = subprocess.run([sys.executable, str(SCRIPTS / script), "--verifier"],
                             capture_output=True, text=True, cwd=str(RACINE))
        if res.returncode != 0:
            detail = (res.stderr or res.stdout).strip().replace("\n", " / ")
            erreur("scripts/%s" % script, "%s périmés — %s" % (quoi, detail))


# ----------------------------------------------------------------------- main

def main() -> int:
    silencieux = "--silencieux" in sys.argv

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
    verifier_appartenance(modules, agents, skills, mcp, taches)
    verifier_renvois_entre_modules(modules, skills)
    verifier_references(agents, skills)
    verifier_portee_des_renvois(agents, skills)
    verifier_agents_nommes(agents)
    verifier_chemins_cites()
    verifier_unicite_des_noms()
    verifier_derives()

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
              "%d tâche(s), index et sommaires à jour.%s"
              % (len(modules), len(agents), len(skills), len(taches), regime))
    return 0


if __name__ == "__main__":
    sys.exit(main())
