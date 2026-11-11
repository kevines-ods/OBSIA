#!/usr/bin/env bash
# Session de démo OBSIA — jouée sous PTY pour l'enregistrement.
# Usage : session-demo.sh <racine du coffre parent>
set -eu
COFFRE="${1:?usage : session-demo.sh <racine du coffre parent>}"
cd "$COFFRE"

tput clear
echo "════════════════════════════════════════════════════════════════"
echo "  OBSIA — démo : un coffre de notes piloté par un harness (opencode)"
echo "════════════════════════════════════════════════════════════════"
echo
sleep 1

echo '$ ls'
ls -F
sleep 1.2

echo
echo '$ head -12 AGENTS.md'
head -12 AGENTS.md
sleep 1.2

echo
echo '$ opencode run  -m obsia-mock/mock-brain "Fais-moi visiter le coffre"'
echo
opencode run -m obsia-mock/mock-brain "Fais-moi visiter le coffre"
sleep 1

echo
echo '$ head -12 "_MAINTENANCE/courrier/2026-11-10-retour-client-formulaire.md"'
head -12 "_MAINTENANCE/courrier/2026-11-10-retour-client-formulaire.md"
sleep 1.5

echo
echo "— Fin de la démo. Le courrier porte maintenant la lecture tracée :"
echo "  lu: 2026-11-11 assistant demo — écrite par opencode pendant la session."
sleep 2
