# Claude Code

**Statut : gabarit v1 — à valider sur machine réelle.**

Claude Code lit `CLAUDE.md` depuis le répertoire de travail. Pour brancher
OBSIA et le coffre parent :

1. Lancer la session depuis le dépôt OBSIA (`cd .../OBSIA && claude`) : le
   cerveau (`CLAUDE.md`) est chargé automatiquement (contrat + index).
2. Donner accès au coffre parent : autoriser la racine du coffre (parent du
   dépôt) comme répertoire de travail, ou déclarer le bloc MCP `coffre-parent`
   de `commun.md`.
3. Vérifier : demander la liste des dossiers de la racine du coffre (`..`). Si
   `SAVOIRS/` n'apparaît pas, l'accès n'est pas donné.

Autre usage (hors Claude Code) : régénérer le prompt avec
`python3 scripts/generer_prompt.py`.

> Le coffre ne dépend pas de Claude Code ; cette fiche n'est qu'un gabarit
> d'intégration.
