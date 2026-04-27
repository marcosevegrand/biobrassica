#!/usr/bin/env bash
# Backup the production PostgreSQL database and media volume into backups/.

set -euo pipefail

SCRIPT_NAME=backup

# shellcheck disable=SC1091
source "$(CDPATH= cd -- "$(dirname "$0")" && pwd)/lib/common.sh"

require_command docker
setup_prod_compose

BACKUP_DIR="${1:-$PROJECT_DIR/backups}"
MEDIA_VOLUME="${COMPOSE_PROJECT_NAME}_media_files"
DRY_RUN="${BACKUP_DRY_RUN:-0}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"
STAMP="$(date +%Y%m%d_%H%M%S)"
DB_NAME="$(env_value DB_NAME biobrassica)"
DB_USER="$(env_value DB_USER biobrassica)"
DB_BACKUP="$BACKUP_DIR/db_${STAMP}.sql.gz"
MEDIA_BACKUP="$BACKUP_DIR/media_${STAMP}.tar.gz"

umask 077
mkdir -p "$BACKUP_DIR"

if [ "$DRY_RUN" = "1" ]; then
    log_step "dry-run enabled"
    log_step "database -> $DB_BACKUP"
    log_step "media -> $MEDIA_BACKUP"
    log_step "would prune backups older than $RETENTION_DAYS days"
    exit 0
fi

log_step "ensuring database container is running"
"${COMPOSE[@]}" up -d db >/dev/null

log_step "writing database backup"
"${COMPOSE[@]}" exec -T db pg_dump --clean --if-exists --no-owner --no-privileges -U "$DB_USER" "$DB_NAME" | gzip -c > "$DB_BACKUP"

log_step "writing media backup"
docker run --rm \
    -v "${MEDIA_VOLUME}:/data:ro" \
    -v "$BACKUP_DIR:/out" \
    alpine tar czf "/out/$(basename "$MEDIA_BACKUP")" -C /data .

find "$BACKUP_DIR" -name 'db_*.sql.gz' -mtime +"$RETENTION_DAYS" -delete
find "$BACKUP_DIR" -name 'media_*.tar.gz' -mtime +"$RETENTION_DAYS" -delete

log_step "database -> $DB_BACKUP"
log_step "media -> $MEDIA_BACKUP"
log_step "pruned backups older than $RETENTION_DAYS days"
