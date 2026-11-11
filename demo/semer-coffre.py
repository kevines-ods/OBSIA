#!/usr/bin/env python3
"""Sème un coffre de démonstration : faux PROJETS, SAVOIRS, courrier, tâches.

À lancer depuis la racine du coffre parent (le dossier qui contient OBSIA/),
après `python3 OBSIA/scripts/installer.py --appliquer`. Idempotent : une note
qui existe déjà n'est ni écrasée ni dupliquée.
"""
import sys
from pathlib import Path

NOTES = {
    "0-PROJETS/demo-site-vitrine/demo-site-vitrine — résumé.md": """---
kind: projet
titre: Site vitrine du cabinet de conseil Argos
statut: en cours
début: 2026-09-12
tags: [projet, web, vitrine]
---

# Site vitrine du cabinet Argos — résumé

**Objectif.** Refondre le site vitrine du cabinet Argos : une page d'accueil,
une page services, un formulaire de contact. Livraison prévue fin décembre.

**Chantiers en cours**

- [ ] Intégration de la maquette validée (en cours)
- [x] Choix de la stack (Astro + hébergement sur le serveur maison)
- [ ] Formulaire de contact avec anti-spam

**Décisions**

- 2026-10-02 — Astro retenu plutôt que WordPress : maintenance minimale,
  pages statiques, aucun plugin à surveiller.

**Liens**

- Carnet de chantier : `carnets/2026-10-05-demo-site-vitrine-sprint-maquette.md`
- Savoir mobilisé : `docker-compose-et-reverse-proxy.md`
""",
    "0-PROJETS/demo-site-vitrine/carnets/2026-10-05-demo-site-vitrine-sprint-maquette.md": """---
kind: carnet
agent: batisseur
projet: demo-site-vitrine
statut: en cours
date: 2026-10-05
tags: [carnet, sprint]
---

# Carnet — sprint maquette (octobre 2026)

Trois séances cette semaine. La grille d'accueil est en place, reste le
dépli des services en mobile. Le client veut un ton sobre, pas d'animation
d'entrée.
""",
    "0-PROJETS/gestion-budget-familial/gestion-budget-familial — résumé.md": """---
kind: projet
titre: Suivi du budget familial dans le coffre
statut: actif
début: 2026-08-01
tags: [projet, budget, tableur]
---

# Budget familial — résumé

**Objectif.** Tenir le budget du foyer dans une note mensuelle, avec un
tableau des postes de dépenses et un point à la fin du mois.

**Chantiers en cours**

- [ ] Clôture du mois d'octobre
- [x] Gabarit de note mensuelle créé

**Liens**

- `carnets/2026-10-31-gestion-budget-familial-cloture-octobre.md`
""",
    "0-PROJETS/gestion-budget-familial/carnets/2026-10-31-gestion-budget-familial-cloture-octobre.md": """---
kind: carnet
agent: assistant
projet: gestion-budget-familial
statut: en cours
date: 2026-10-31
tags: [carnet, budget]
---

# Rétrospective d'octobre

Les courses en vrac ont dérivé de 12 % : passer à un menu planifié sur
quatre semaines réduirait l'écart. À revoir en novembre.
""",
    "0-PROJETS/migration-serveur-home/migration-serveur-home — résumé.md": """---
kind: projet
titre: Migration du serveur maison vers Debian 13
statut: en cours
début: 2026-10-18
tags: [projet, serveur, migration]
---

# Migration du serveur maison — résumé

**Objectif.** Faire passer le serveur maison de Debian 12 à Debian 13 sans
couper les services plus de trente minutes.

**Chantiers en cours**

- [ ] Sauvegarde complète vérifiée (règle 3-2-1)
- [ ] Reprise des conteneurs Docker après migration
- [x] Inventaire des services hébergés

**Décisions**

- 2026-10-20 — On migre à froid un dimanche matin, fenêtre 7 h — 9 h.
""",
    "0-SAVOIRS/docker-compose-et-reverse-proxy.md": """---
kind: savoir
titre: Docker Compose et reverse proxy Caddy
tags: [savoir, docker, caddy, serveur]
---

# Docker Compose et reverse proxy Caddy

Le patron éprouvé pour exposer un service du serveur maison :

1. Un fichier compose par service, dans `/srv/<service>/`.
2. Le reverse proxy (Caddy) porte les certificats TLS ; les services
   n'écoutent que sur le réseau interne.
3. Les secrets dans un `.env` hors dépôt, lu par compose.

**Pièges rencontrés**

- Oublier le réseau externe `caddy` dans le compose : le proxy ne joint pas
  le service et Caddy renvoie une 502 silencieuse.
""",
    "0-SAVOIRS/mermaid-diagrammes.md": """---
kind: savoir
titre: Diagrammes Mermaid — patrons utiles
tags: [savoir, mermaid, diagramme]
---

# Diagrammes Mermaid — patrons utiles

- `flowchart LR` pour un flux de décision, `sequenceDiagram` pour un
  échange entre systèmes.
- Toujours nommer les nœuds (`A[Texte]`) : les libellés longs cassent le
  rendu autrement.
- Le rendu passe par `mmdc` ; vérifier le SVG produit avant de l'archiver.
""",
    "0-SAVOIRS/rg-recherche-dans-le-coffre.md": """---
kind: savoir
titre: Chercher efficacement dans le coffre avec ripgrep
tags: [savoir, ripgrep, recherche]
---

# Chercher dans le coffre avec ripgrep

`rg -i --glob '!OBSIA/**' "motif"` depuis la racine du coffre couvre la
mémoire sans le produit. Pour dater un souvenir : chercher sur la plage de
dates dans le frontmatter plutôt que dans le corps des notes.
""",
    "0-EN-VRAC/idée-rappel-tâches.md": """---
kind: en-vrac
date: 2026-11-02
tags: [en-vrac, idée]
---

# Idée notée en vrac

Et si la tâche planifiée du matin ajoutait un résumé du courrier non lu
dans la note du jour ? À trier plus tard.
""",
    "0-EN-VRAC/article-sur-les-mcp.md": """---
kind: en-vrac
date: 2026-11-05
tags: [en-vrac, article, mcp]
---

# Article à trier

Article croisé sur le protocole MCP et la sécurité des serveurs d'outils :
à lire, puis à déposer dans les savoirs ou à jeter.
""",
    "_MAINTENANCE/courrier/2026-11-08-faille-cve-service-sauvegarde.md": """---
kind: message
date: 2026-11-08
de: administrateur
pour: batisseur
sujet: Faille CVE-2026-3411 dans l'image de sauvegarde — mettre à jour avant le 15
lu:
  - "2026-11-09 batisseur 1a4d"
---

L'image `restic-server` en service sur le serveur maison est touchée par la
CVE-2026-3411 (contournement d'authentification). Une version corrigée est
publiée. Il faut mettre à jour le conteneur et vérifier que la tâche de
sauvegarde du dimanche tourne toujours. Le chantier est rattaché au projet
`migration-serveur-home`.
""",
    "_MAINTENANCE/courrier/2026-11-10-retour-client-formulaire.md": """---
kind: message
date: 2026-11-10
de: assistant
projet: demo-site-vitrine
sujet: Le client veut un menu anti-spam sur le formulaire de contact
---

Retour du cabinet Argos par courriel : le formulaire de contact doit filtrer
les soumissions automatiques avant la mise en ligne. Un honeypot suffit
d'après lui, mais confirmer avec lui si un captcha visible est refusé.
""",
    "0-PROJETS/tâches-planifiées/brief-du-matin.md": """---
schema: 1
kind: tâche
name: brief-du-matin
description: Chaque matin, résumer au projet courant le courrier non lu et l'état des chantiers.
module: planification
mode: agent
quand: "0 8 * * *"
fuseau: Europe/Paris
exécutant: local
agent: assistant
actif: true
---

# Tâche — Brief du matin

## Intention

Ouvrir la journée en sachant ce qui a bougé : messages du courrier non lus,
carnets `statut: en cours`, tâches planifiées qui ont tourné pendant la nuit.

## Instruction

1. Lister les messages non lus de `_MAINTENANCE/courrier/` pour le projet
   et pour l'agent `assistant`.
2. Résumer chaque message en une ligne, avec son lien.
3. Écrire le résumé dans la note du jour du projet courant.
""",
}


def principal():
    racine = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    if not (racine / "OBSIA").is_dir():
        sys.exit(f"usage : {sys.argv[0]} <racine du coffre parent (celui qui contient OBSIA/)>")
    crees, passes = 0, 0
    for rel, corps in NOTES.items():
        cible = racine / rel
        if cible.exists():
            passes += 1
            continue
        cible.parent.mkdir(parents=True, exist_ok=True)
        cible.write_text(corps, encoding="utf-8")
        crees += 1
        print(f"  créé     : {rel}")
    for dossier in ["0-DOCUMENTS", "0-MEMOIRES/courrier"]:
        (racine / dossier).mkdir(parents=True, exist_ok=True)
    print(f"Semailles : {crees} note(s) créée(s), {passes} déjà présente(s).")


if __name__ == "__main__":
    principal()
