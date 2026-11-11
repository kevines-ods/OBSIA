#!/usr/bin/env bash
# Tourne les scènes de démonstration : une vraie séance opencode, un vrai
# modèle, une frappe simulée par VHS.
#
#   ./tourner.sh                 toutes les scènes
#   ./tourner.sh 2-reprise       une seule
#
# Variables :
#   OBSIA_DEMO_MODELE   modèle opencode (défaut : opencode/big-pickle) ;
#                       « opencode models | grep free » liste les gratuits
#   OBSIA_DEMO_DOSSIER  dossier jetable du coffre fictif (défaut : ~/demo-obsia)
#   OBSIA_DEMO_SORTIE   où poser les vidéos (défaut : ./videos, non versionné)
#
# Le coffre fictif est remonté avant chaque scène : chaque prise part du même
# état. Le modèle, lui, ne répond jamais deux fois pareil — on refait la prise
# qui ne plaît pas.
set -euo pipefail

ici="$(cd "$(dirname "$0")" && pwd)"
modele="${OBSIA_DEMO_MODELE:-opencode/big-pickle}"
dossier="${OBSIA_DEMO_DOSSIER:-$HOME/demo-obsia}"
sortie="${OBSIA_DEMO_SORTIE:-$ici/videos}"

for outil in vhs opencode ffmpeg ttyd; do
  command -v "$outil" >/dev/null || { echo "Il manque : $outil" >&2; exit 1; }
done

if [ "$#" -gt 0 ]; then scenes=("$@"); else
  scenes=(); for f in "$ici"/scenes/*.tape; do scenes+=("$(basename "$f" .tape)"); done
fi

mkdir -p "$sortie"
export OBSIA_DEMO_COFFRE="$dossier/Mon coffre"

for scene in "${scenes[@]}"; do
  bande="$ici/scenes/$scene.tape"
  [ -f "$bande" ] || { echo "Scène inconnue : $scene" >&2; exit 1; }
  echo "── $scene ($modele)"
  "$ici/monter_coffre_fictif.sh" "$dossier" >/dev/null
  printf '{\n  "$schema": "https://opencode.ai/config.json",\n  "model": "%s"\n}\n' \
    "$modele" > "$OBSIA_DEMO_COFFRE/opencode.json"
  (cd "$sortie" && vhs "$bande" >/dev/null) || { echo "   échec de vhs" >&2; exit 1; }
  echo "   $sortie/$scene.mp4"
done
