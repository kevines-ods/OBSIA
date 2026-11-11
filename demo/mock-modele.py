#!/usr/bin/env python3
"""Faux modèle local, compatible OpenAI, pour la démo OBSIA + opencode.

Sert sur 127.0.0.1:8090 des réponses scriptées : la séquence de pas est
déterminée par le nombre de messages assistant à tool_calls déjà présents
dans la conversation. Les outils du harness s'exécutent réellement ; seules
les réponses du « modèle » sont jouées.
"""
import json
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# ---------------------------------------------------------------- scénario
# Chaque entrée : soit un appel d'outil, soit le texte final.
SCENARIO = [
    {
        "texte": (
            "Bonjour ! Je suis l'assistant OBSIA, branché ici sur opencode. "
            "Je vais te faire visiter le coffre. Commençons par la racine."
        ),
        "outil": ("bash", {"command": "ls -F"}),
    },
    {
        "texte": "Voilà la structure du coffre : la mémoire vit à côté de l'outil OBSIA.",
        "outil": ("bash", {"command": "ls -F 0-PROJETS/"}),
    },
    {
        "texte": "Trois projets vivent ici. Ouvre le résumé du site vitrine.",
        "outil": ("read", {"filePath": "0-PROJETS/demo-site-vitrine/demo-site-vitrine — résumé.md"}),
    },
    {
        "texte": (
            "Chaque projet a son résumé : objectif, chantiers cochés, décisions "
            "datées. Voyons le courrier inter-agents."
        ),
        "outil": ("bash", {"command": "ls -F _MAINTENANCE/courrier/"}),
    },
    {
        "texte": "Deux messages en attente. Lis celui du cabinet Argos.",
        "outil": ("read", {"filePath": "_MAINTENANCE/courrier/2026-11-10-retour-client-formulaire.md"}),
    },
    {
        "texte": (
            "Le courrier porte une adresse — un agent ou un projet. Je marque "
            "ma lecture : une ligne datée et signée, écrite dans le fichier."
        ),
        "outil": ("edit", {
            "filePath": "_MAINTENANCE/courrier/2026-11-10-retour-client-formulaire.md",
            "oldString": "sujet: Le client veut un menu anti-spam sur le formulaire de contact\n---",
            "newString": "sujet: Le client veut un menu anti-spam sur le formulaire de contact\nlu:\n  - \"2026-11-11 assistant demo\"\n---",
        }),
    },
    {
        "texte": "Lecture tracée — le message reste visible pour les autres conversations du chantier. Passons aux tâches planifiées.",
        "outil": ("bash", {"command": "ls -F 0-PROJETS/tâches-planifiées/ && head -20 0-PROJETS/tâches-planifiées/brief-du-matin.md"}),
    },
    {
        "texte": "Un registre privé, hors dépôt public : chaque tâche se ré-instancie en timer systemd, change de machine sans se perdre.",
        "outil": ("read", {"filePath": "0-SAVOIRS/docker-compose-et-reverse-proxy.md"}),
    },
    {
        "texte": "Et les savoirs, la base de connaissances durable — lus par tous les agents du coffre. Bonne visite !",
        "outil": None,
    },
]


def etape_du_corps(corps):
    """Numéro d'étape = nombre de messages assistant portant des tool_calls."""
    n = 0
    for msg in corps.get("messages", []):
        if msg.get("role") == "assistant" and msg.get("tool_calls"):
            n += 1
    return n


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass

    def _json(self, code, obj):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.rstrip("/").endswith("/models"):
            self._json(200, {
                "object": "list",
                "data": [{"id": "mock-brain", "object": "model", "owned_by": "obsia-demo"}],
            })
        else:
            self._json(404, {"error": {"message": "inconnu"}})

    def do_POST(self):
        if not self.path.rstrip("/").endswith("/chat/completions"):
            self._json(404, {"error": {"message": "inconnu"}})
            return
        taille = int(self.headers.get("Content-Length", 0))
        corps = json.loads(self.rfile.read(taille) or b"{}")
        etape = min(etape_du_corps(corps), len(SCENARIO) - 1)
        pas = SCENARIO[etape]
        modele = corps.get("model", "mock-brain")
        ident = "chatcmpl-" + uuid.uuid4().hex[:12]

        deltas = []
        if pas.get("texte"):
            deltas.append({"role": "assistant", "content": ""})
            mots = pas["texte"].split(" ")
            bout, tampon = [], ""
            for m in mots:
                bout.append(m)
                tampon += m + " "
                if len(bout) >= 4:
                    deltas.append({"content": " ".join(bout) + " "})
                    bout = []
            if bout:
                deltas.append({"content": " ".join(bout)})

        fin = "stop"
        if pas.get("outil"):
            nom, args = pas["outil"]
            deltas.append({
                "tool_calls": [{
                    "index": 0,
                    "id": "call_" + uuid.uuid4().hex[:8],
                    "type": "function",
                    "function": {"name": nom, "arguments": json.dumps(args, ensure_ascii=False)},
                }]
            })
            fin = "tool_calls"

        if corps.get("stream"):
            lignes = []
            for d in deltas:
                lignes.append(json.dumps({
                    "id": ident, "object": "chat.completion.chunk",
                    "created": int(time.time()), "model": modele,
                    "choices": [{"index": 0, "delta": d, "finish_reason": None}],
                }, ensure_ascii=False))
            lignes.append(json.dumps({
                "id": ident, "object": "chat.completion.chunk",
                "created": int(time.time()), "model": modele,
                "choices": [{"index": 0, "delta": {}, "finish_reason": fin}],
            }, ensure_ascii=False))
            corps_sse = ("\n\n".join("data: " + l for l in lignes)
                         + "\n\ndata: [DONE]\n\n").encode()
            time.sleep(0.9)
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Content-Length", str(len(corps_sse)))
            self.end_headers()
            self.wfile.write(corps_sse)
            self.wfile.flush()
        else:
            message = {"role": "assistant", "content": pas.get("texte") or ""}
            if pas.get("outil"):
                nom, args = pas["outil"]
                message["content"] = None
                message["tool_calls"] = [{
                    "id": "call_" + uuid.uuid4().hex[:8],
                    "type": "function",
                    "function": {"name": nom, "arguments": json.dumps(args, ensure_ascii=False)},
                }]
            self._json(200, {
                "id": ident, "object": "chat.completion",
                "created": int(time.time()), "model": modele,
                "choices": [{"index": 0, "message": message, "finish_reason": fin}],
            })


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 8090), Handler).serve_forever()
