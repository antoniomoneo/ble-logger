#!/bin/bash
set -e

REPO_DIR="/home/tcd/ble-logger"
DATA_DIR="$REPO_DIR/data"

cd "$REPO_DIR"

# Asegurar que todo está actualizado
git pull --rebase

# Comprimir todos los datos en un tar.gz con fecha
ARCHIVE="data-$(date +%Y-%m-%d-%H%M).tar.gz"
tar czf "$ARCHIVE" -C "$DATA_DIR" .

# Añadir al repo
git add "$ARCHIVE"
git commit -m "Data upload $(date -u +'%Y-%m-%d %H:%M:%S UTC')"
git push
