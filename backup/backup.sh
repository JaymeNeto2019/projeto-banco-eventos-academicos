#!/usr/bin/env bash
# Backup lógico do banco (B7). Uso: bash backup.sh        (agende no cron; ver README_backup.md)
# Credenciais ficam em backup.cnf (fora do Git). Variáveis opcionais: DB_NAME, BACKUP_DIR, RETENCAO_DIAS.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
CNF="${BACKUP_CNF:-$DIR/backup.cnf}"
DEST="${BACKUP_DIR:-$DIR/dumps}"
DB="${DB_NAME:-eventos_academicos}"
RETENCAO_DIAS="${RETENCAO_DIAS:-14}"

[ -f "$CNF" ] || { echo "Falta $CNF (copie backup.cnf.exemplo e preencha)"; exit 1; }
mkdir -p "$DEST"
ARQ="$DEST/${DB}_$(date +%Y%m%d_%H%M%S).sql.gz"

# --single-transaction: cópia consistente sem travar as tabelas InnoDB; inclui gatilhos, rotinas e eventos.
mysqldump --defaults-extra-file="$CNF" --single-transaction --routines --triggers --events "$DB" | gzip > "$ARQ"
gzip -t "$ARQ"                                   # confere se o arquivo compactado não está corrompido
find "$DEST" -name "${DB}_*.sql.gz" -mtime +"$RETENCAO_DIAS" -delete   # retenção
echo "Backup OK: $ARQ ($(du -h "$ARQ" | cut -f1))"
