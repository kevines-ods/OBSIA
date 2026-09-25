#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Serveur MCP « modele-local » — délégation de tâches simples à un modèle local.

L'agent principal rédige une consigne auto-suffisante et y joint le seul
contenu utile ; le modèle local rend du texte. Il ne voit ni le contrat du
coffre, ni la conversation, ni aucun fichier, et n'a aucun outil : il ne peut
rien écrire. L'agent principal relit le résultat et reste seul à écrire.
Règles d'usage : fiche `IA/MCP/modele-local.md` et skill `delegation-locale`.

Transport : stdio, JSON-RPC 2.0 délimité par des fins de ligne.
Aucune dépendance hors de la bibliothèque standard (§11).

Variables d'environnement — les valeurs réelles vivent dans la configuration
du harness, jamais dans le dépôt (§13.5) :
    OBSIA_LOCAL_URL      point d'accès compatible OpenAI
                         (défaut : http://127.0.0.1:8080/v1, llama-server nu)
    OBSIA_LOCAL_MODEL    nom du modèle ; obligatoire derrière une passerelle
                         multi-modèles (llama-swap, Ollama), inutile devant un
                         llama-server seul (défaut : vide, champ non envoyé)
    OBSIA_LOCAL_TIMEOUT  délai maximal d'un appel, en secondes (défaut : 600)
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request

URL = os.environ.get("OBSIA_LOCAL_URL", "http://127.0.0.1:8080/v1").rstrip("/")
MODELE = os.environ.get("OBSIA_LOCAL_MODEL", "").strip()
NOM_AFFICHE = MODELE or "local"
DELAI = int(os.environ.get("OBSIA_LOCAL_TIMEOUT", "600"))
MAX_TOKENS_PLAFOND = 4096

#: Court à dessein : chaque token de prompt coûte ~40 ms de lecture sur ce
#: nœud CPU, et le modèle n'a pas à connaître le coffre.
PROMPT_SYSTEME = (
    "Tu exécutes une tâche simple et précise qu'on te confie. "
    "Suis la consigne à la lettre. Réponds uniquement avec le résultat "
    "demandé, sans préambule ni commentaire. Si la consigne est impossible "
    "ou ambiguë, réponds exactement : IMPOSSIBLE: <raison en une phrase>."
)

OUTIL = {
    "name": "deleguer",
    "description": (
        "Confie une tâche simple et délimitée au modèle local "
        + NOM_AFFICHE
        + " (résumer, reformuler, traduire, extraire en JSON, proposer des "
        "tags dans une liste fournie, trier, premier jet). Le modèle ne voit "
        "QUE la consigne et le contenu transmis : pas de fichiers, pas "
        "d'outils, pas de contexte. La consigne doit donc être "
        "auto-suffisante. Souvent lent (CPU) : transmettre le strict "
        "nécessaire. Toujours relire le résultat."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "consigne": {
                "type": "string",
                "description": "Instruction complète et auto-suffisante : quoi faire, contraintes, forme de la sortie.",
            },
            "contenu": {
                "type": "string",
                "description": "Matière à traiter (texte d'une note, liste…). Facultatif.",
            },
            "format": {
                "type": "string",
                "enum": ["texte", "json"],
                "description": "« json » force une sortie JSON valide. Défaut : texte.",
            },
            "max_tokens": {
                "type": "integer",
                "minimum": 1,
                "maximum": MAX_TOKENS_PLAFOND,
                "description": "Longueur maximale de la réponse. Défaut : 512.",
            },
            "reflexion": {
                "type": "boolean",
                "description": "Active le raisonnement du modèle : bien plus lent, rarement utile pour une tâche simple. Défaut : false.",
            },
        },
        "required": ["consigne"],
    },
}


def appeler_modele(args: dict) -> tuple[str, bool]:
    """Renvoie (texte pour l'agent, est_une_erreur)."""
    consigne = (args.get("consigne") or "").strip()
    if not consigne:
        return "Consigne vide : rien à déléguer.", True
    contenu = args.get("contenu") or ""
    fmt = args.get("format", "texte")
    max_tokens = max(1, min(int(args.get("max_tokens") or 512), MAX_TOKENS_PLAFOND))
    reflexion = bool(args.get("reflexion", False))

    message = "Consigne :\n" + consigne
    if contenu:
        message += "\n\nContenu :\n" + contenu
    if fmt == "json":
        message += "\n\nRéponds uniquement par un objet JSON valide."

    corps = {
        "temperature": 0.2,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": PROMPT_SYSTEME},
            {"role": "user", "content": message},
        ],
        "chat_template_kwargs": {"enable_thinking": reflexion},
    }
    if MODELE:
        corps["model"] = MODELE
    if fmt == "json":
        corps["response_format"] = {"type": "json_object"}

    requete = urllib.request.Request(
        URL + "/chat/completions",
        data=json.dumps(corps).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    debut = time.monotonic()
    try:
        with urllib.request.urlopen(requete, timeout=DELAI) as rep:
            reponse = json.load(rep)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:500]
        return "Erreur HTTP %s du modèle local : %s" % (e.code, detail), True
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return "Modèle local injoignable ou trop lent (%s) : %s" % (URL, e), True
    duree = time.monotonic() - debut

    choix = reponse["choices"][0]
    texte = (choix["message"].get("content") or "").strip()
    usage = reponse.get("usage", {})
    notes = [
        "%s — %.1f s, %s tokens lus, %s produits"
        % (NOM_AFFICHE, duree, usage.get("prompt_tokens", "?"), usage.get("completion_tokens", "?"))
    ]
    if choix.get("finish_reason") == "length":
        notes.append("ATTENTION : réponse tronquée (max_tokens atteint).")
    if not texte:
        notes.append("ATTENTION : réponse vide (budget épuisé par le raisonnement ?).")
    if fmt == "json" and texte:
        try:
            json.loads(texte)
        except ValueError:
            notes.append("ATTENTION : la sortie n'est pas un JSON valide.")
    if texte.startswith("IMPOSSIBLE:"):
        notes.append("Le modèle a refusé la tâche.")

    return texte + "\n\n---\n" + "\n".join(notes), False


def repondre(id_, resultat=None, erreur=None):
    msg = {"jsonrpc": "2.0", "id": id_}
    if erreur is not None:
        msg["error"] = erreur
    else:
        msg["result"] = resultat
    sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def traiter(msg: dict) -> None:
    methode = msg.get("method")
    id_ = msg.get("id")
    if id_ is None:  # notification : jamais de réponse
        return
    if methode == "initialize":
        version = (msg.get("params") or {}).get("protocolVersion", "2025-06-18")
        repondre(id_, {
            "protocolVersion": version,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "modele-local", "version": "1.0.0"},
        })
    elif methode == "ping":
        repondre(id_, {})
    elif methode == "tools/list":
        repondre(id_, {"tools": [OUTIL]})
    elif methode == "tools/call":
        params = msg.get("params") or {}
        if params.get("name") != OUTIL["name"]:
            repondre(id_, erreur={"code": -32602, "message": "Outil inconnu : %s" % params.get("name")})
            return
        texte, est_erreur = appeler_modele(params.get("arguments") or {})
        repondre(id_, {"content": [{"type": "text", "text": texte}], "isError": est_erreur})
    else:
        repondre(id_, erreur={"code": -32601, "message": "Méthode inconnue : %s" % methode})


def main() -> None:
    for ligne in sys.stdin:
        ligne = ligne.strip()
        if not ligne:
            continue
        try:
            msg = json.loads(ligne)
        except ValueError:
            repondre(None, erreur={"code": -32700, "message": "JSON invalide"})
            continue
        try:
            traiter(msg)
        except Exception as e:  # le serveur ne doit jamais tomber sur une requête
            if msg.get("id") is not None:
                repondre(msg["id"], erreur={"code": -32603, "message": str(e)})


if __name__ == "__main__":
    main()
