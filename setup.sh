#!/usr/bin/env bash
# ============================================================
# OBSIA — Restructuration monorepo (une seule exécution)
#
# Transforme obsia_vault/ (coffre seul) en monorepo Obsia/
#   Obsia/
#   ├── obsia_vault/   → CŒUR (mémoire + IA/agents + IA/skills)
#   └── build/        → FRAMEWORK (Tauri/Rust — terminal humain)
#
# Exécuter UNE SEULE FOIS depuis Obsia/:
#     bash setup.sh
# ============================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VAULT="$ROOT/obsia_vault"

echo "=== OBSIA monorepo setup ==="
echo "Root : $ROOT"
echo "Vault: $VAULT"

# 1. Supprimer le .git imbriqué (si présent) → Obsia/ devient la seule racine git
if [ -d "$VAULT/.git" ]; then
  rm -rf "$VAULT/.git"
  echo "[ok] .git imbriqué supprimé dans obsia_vault/"
else
  echo "[skip] aucun .git imbriqué à supprimer"
fi

# 2. Créer le dossier build/ (contient src/ + src-tauri/)
mkdir -p "$ROOT/build"
echo "[ok] dossier build/ créé"

# 3. Configurer le remote (push) vers GitHub
git -C "$ROOT" remote set-url origin "https://github.com/kevines-ods/OBSIA"
echo "[ok] remote origin configuré"

# 4. Premier commit monorepo
cd "$ROOT"
git add -A
git -c user.name="OBSIA Assistant" -c user.email="assistant@obsia.local" \
  commit -m "chore: baseline monorepo (coffre obsia_vault/ + build/)"
echo "[ok] commit baseline créé"

echo "=== FIN ==="
echo "Cœur   : obsia_vault/  ($(git rev-parse --is-inside-work-tree && echo git-ok))"
echo "Build  : build/"
echo "README : README.md"
echo "Docs   : obsia_vault/README.md, obsia_vault/RUNTIME.md"
