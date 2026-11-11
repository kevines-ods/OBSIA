#!/usr/bin/env bash
# Monte un coffre fictif, jetable, pour les vidéos de démonstration.
#
#   ./monter_coffre_fictif.sh [DOSSIER]
#
# DOSSIER (défaut : ~/demo-obsia) reçoit « Mon coffre/ » : un clone du dépôt
# courant, l'AGENTS.md posé par l'installateur, et des notes inventées.
# Rien n'y est réel : personne, machine ni projet. Le dossier est effacé et
# refait à chaque appel, pour que chaque prise parte du même état.
set -euo pipefail

depot="$(cd "$(dirname "$0")/../.." && pwd)"
base="${1:-$HOME/demo-obsia}"
coffre="$base/Mon coffre"

case "$base" in
  "$HOME"|/|"") echo "Refus : « $base » n'est pas un dossier jetable." >&2; exit 1 ;;
esac
if [ -e "$base" ] && [ ! -e "$base/.coffre-fictif" ]; then
  echo "Refus : « $base » existe et n'a pas été créé par ce script." >&2
  exit 1
fi

rm -rf "$base"
mkdir -p "$coffre"
touch "$base/.coffre-fictif"

git clone --quiet "$depot" "$coffre/OBSIA"
(cd "$coffre/OBSIA" && python3 scripts/installer.py --tout --appliquer >/dev/null)

cd "$coffre"
mkdir -p 0-EN-VRAC 0-SAVOIRS 0-DOCUMENTS _MAINTENANCE \
         "0-PROJETS/serre-connectée/arrosage-automatique/carnets"

# --- 0-EN-VRAC : trois notes brutes, à ranger --------------------------------
cat > "0-EN-VRAC/idée capteur humidité.md" <<'EOF'
vu une vidéo sur les capteurs d'humidité capacitifs, moins de corrosion que
les résistifs. à tester pour la serre ? prix autour de 3 euros pièce.
penser à calibrer dans l'air puis dans l'eau
EOF

cat > "0-EN-VRAC/commande docker vue sur un forum.md" <<'EOF'
docker system prune -a --volumes
quelqu'un disait que ça libère beaucoup de place. à vérifier avant de lancer,
je ne sais pas ce que ça supprime exactement
EOF

cat > "0-EN-VRAC/pain au levain.md" <<'EOF'
500 g farine T65, 350 g eau, 100 g levain, 10 g sel
pointage 4 h, façonnage, nuit au frigo, cuisson 240 °C en cocotte 45 min
EOF

# --- 0-SAVOIRS : une note déjà rangée ----------------------------------------
cat > "0-SAVOIRS/Sauvegarde 3-2-1.md" <<'EOF'
---
type: concept
tags: [sauvegarde]
---
# Sauvegarde 3-2-1

Trois copies des données, sur deux supports différents, dont une hors site.
Une sauvegarde qui n'a jamais été restaurée n'est pas une sauvegarde : elle
se teste.
EOF

# --- 0-PROJETS : un projet, un chantier, un carnet en cours ------------------
cat > "0-PROJETS/serre-connectée/serre-connectée — résumé.md" <<'EOF'
---
type: projet
---
# serre-connectée — résumé

Automatiser la petite serre du jardin : mesurer, arroser, être prévenu.
Matériel : un micro-contrôleur ESP32, une pompe 12 V, une cuve de 200 L.

## Chantiers
- `arrosage-automatique` — en cours.
EOF

cat > "0-PROJETS/serre-connectée/arrosage-automatique/arrosage-automatique — résumé.md" <<'EOF'
---
type: projet
---
# arrosage-automatique — résumé

Déclencher la pompe quand la terre est sèche, jamais plus de deux minutes
d'affilée, et jamais si la cuve est vide.
EOF

cat > "0-PROJETS/serre-connectée/arrosage-automatique/carnets/2026-11-08-arrosage-automatique-seuil-humidité.md" <<'EOF'
---
agent: batisseur
projet: arrosage-automatique
statut: en cours
---
# Carnet — arrosage-automatique — seuil d'humidité

## Demande
Trouver le seuil d'humidité qui déclenche l'arrosage.

## Plan
1. Relever le capteur terre sèche, puis terre arrosée. — fait
2. Choisir le seuil entre les deux. — fait
3. Ajouter la sécurité « cuve vide ». — **en cours**
4. Tester une semaine.

## Actions
- 2026-11-08 14:10 — relevés : 2 900 terre sèche, 1 400 terre arrosée.
- 2026-11-08 14:40 — seuil retenu : 2 300.
- 2026-11-08 15:05 — étape 3 commencée : le flotteur de cuve est branché,
  le code ne le lit pas encore.

## En attente
- Quelle durée d'arrosage maximale par jour ?
EOF

# --- Profil : quelques faits, pour que les réponses s'y adossent --------------
python3 - <<'EOF'
from pathlib import Path
p = Path("0-PERSONNELS/profil-utilisateur.md")
t = p.read_text(encoding="utf-8")
t = t.replace("🟡 Vide — à remplir au fil des premières sessions.",
              "🟢 Profil de démonstration — personne fictive.")
t = t.replace("À compléter : distribution, gestionnaire de paquets, environnement de bureau.\nLe profil d'installation en contient déjà une partie.",
              "Linux, bureau KDE. Un petit serveur à la maison pour ses conteneurs.")
t = t.replace("À compléter : ce que l'utilisateur attend qu'on lui explique, et ce qu'il sait\ndéjà.",
              "Bricole, ne code pas : veut qu'on lui explique chaque commande avant de la lancer.")
p.write_text(t, encoding="utf-8")
EOF

# --- Dépôt de données : la mémoire se versionne à part (§7.1) -----------------
printf 'OBSIA/\n' > .gitignore
git init --quiet
git add -A
git -c user.name="Démonstration" -c user.email="demo@example.invalid" \
    commit --quiet -m "Coffre fictif de démonstration"

echo "Coffre fictif prêt : $coffre"
