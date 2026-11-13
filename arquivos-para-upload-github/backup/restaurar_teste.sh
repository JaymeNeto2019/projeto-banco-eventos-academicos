#!/usr/bin/env bash
# Teste de restauração (B7): restaura o backup mais recente em um banco TEMPORÁRIO e compara as
# contagens de linhas com o banco original. Um backup que nunca foi restaurado não é backup.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
CNF="${BACKUP_CNF:-$DIR/backup.cnf}"
DEST="${BACKUP_DIR:-$DIR/dumps}"
DB="${DB_NAME:-eventos_academicos}"
TMP="${DB}_restore_test"
[[ "$DB" =~ ^[A-Za-z0-9_]+$ ]] || { echo 'Nome de banco inválido'; exit 1; }
[ -f "$CNF" ] || { echo "Falta $CNF"; exit 1; }
ARQ=""
for candidato in "$DEST"/"${DB}"_*.sql.gz; do
  [ -f "$candidato" ] || continue
  if [ -z "$ARQ" ] || [ "$candidato" -nt "$ARQ" ]; then ARQ="$candidato"; fi
done
[ -n "$ARQ" ] || { echo 'Nenhum backup encontrado'; exit 1; }
M() { mysql --defaults-extra-file="$CNF" -N -B "$@"; }

echo "Restaurando $ARQ em $TMP ..."
M -e "DROP DATABASE IF EXISTS \`$TMP\`; CREATE DATABASE \`$TMP\` CHARACTER SET utf8mb4;"
gunzip -c "$ARQ" | mysql --defaults-extra-file="$CNF" "$TMP"

ok=1
for t in $(M -e "SELECT table_name FROM information_schema.tables WHERE table_schema='$DB' AND table_type='BASE TABLE' ORDER BY 1"); do
  a=$(M -e "SELECT COUNT(*) FROM \`$DB\`.\`$t\`"); b=$(M -e "SELECT COUNT(*) FROM \`$TMP\`.\`$t\`")
  [ "$a" = "$b" ] && s="ok" || { s="DIFERENTE"; ok=0; }
  printf "%-28s original=%-8s restaurado=%-8s %s\n" "$t" "$a" "$b" "$s"
done
for objeto in triggers routines views; do
  case "$objeto" in
    triggers) coluna=trigger_schema;;
    routines) coluna=routine_schema;;
    views) coluna=table_schema;;
  esac
  a=$(M -e "SELECT COUNT(*) FROM information_schema.$objeto WHERE $coluna='$DB'")
  b=$(M -e "SELECT COUNT(*) FROM information_schema.$objeto WHERE $coluna='$TMP'")
  printf '%s original=%s restaurado=%s\n' "$objeto" "$a" "$b"
  [ "$a" = "$b" ] || ok=0
done
M -e "DROP DATABASE \`$TMP\`"
[ $ok = 1 ] && echo "RESTAURAÇÃO VERIFICADA" || { echo "FALHA: contagens diferentes"; exit 1; }
