# OpenClaw 2.0

**Statut : gabarit v1 — à valider sur machine réelle.**

> « OpenClaw 2.0 » est un **alias de release** (la `2026.8.1`) ; le paquet, lui,
> est **versionné par date** (`v2026.9.3`, …). Ne pas confondre l'alias et le
> numéro de paquet.

OpenClaw est un assistant personnel autonome (skills + MCP), pas un agent CLI
calqué sur un répertoire de travail. L'intégration vise l'accès au coffre
comme base de connaissances et la reprise des tâches.

1. Déclarer le bloc MCP `coffre-parent` (commun.md) dans la configuration MCP
   d'OpenClaw, pointant sur la racine du coffre (parent d'OBSIA).
2. Donner à OpenClaw le chemin du dépôt OBSIA pour lire le cerveau :
   `CLAUDE.md` ou `prompt-systeme.md` (généré par
   `python3 scripts/generer_prompt.py`).
3. Laisser OpenClaw utiliser ses propres skills ; les skills OBSIA restent la
   référence du coffre (§5) — ne pas les dupliquer dans les skills d'OpenClaw,
   pour éviter la divergence.

> À compléter avec la configuration réelle d'OpenClaw 2.0 (emplacement MCP,
> chargement de contexte) quand tu y auras accès.
