#!/usr/bin/env bash
# Teste de restauração (B7): restaura o backup mais recente em um banco TEMPORÁRIO e compara as
# contagens de linhas com o banco original. Um backup que nunca foi restaurado não é backup.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
CNF="${BACKUP_CNF:-$DIR/backup.cnf}"
DEST="${BACKUP_DIR:-$DIR/dumps}"
DB="${DB_NAME:-eventos_academicos}"
TMP="${DB}_restore_test"
ARQ="$(ls -1t "$DEST"/${DB}_*.sql.gz | head -1)"
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
echo "Gatilhos no restaurado: $(M -e "SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema='$TMP'") (original: $(M -e "SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema='$DB'"))"
M -e "DROP DATABASE \`$TMP\`"
[ $ok = 1 ] && echo "RESTAURAÇÃO VERIFICADA" || { echo "FALHA: contagens diferentes"; exit 1; }
