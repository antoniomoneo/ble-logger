#!/bin/bash
DATA_DIR="/home/tcd/ble-logger/data"

# Comprimir todos los CSV de días anteriores (no toca el de hoy)
find "$DATA_DIR" -type f -name "seen-*.csv" ! -name "seen-$(date +%Y-%m-%d).csv" -exec gzip -f {} \;

# Borrar ficheros .csv.gz de más de 30 días
find "$DATA_DIR" -type f -name "seen-*.csv.gz" -mtime +30 -delete
