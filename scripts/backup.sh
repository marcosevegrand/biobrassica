#!/usr/bin/env bash
# Production backup script — database + media files.
#
# Usage:
#   ./scripts/backup.sh [/path/to/backup/dir]
#
# If no directory is given, backups are written to the repo-local backups/ directory.
# Add to cron (daily at 03:00):
#   0 3 * * * /home/deploy/biobrassica/scripts/backup.sh >> /var/log/biobrassica-backup.log 2>&1
#
# Retention: the script removes backups older than 14 days.

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

BACKUP_DIR="${1:-$PROJECT_DIR/backups}"
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-biobrassica}"
COMPOSE_ARGS=(-p "$COMPOSE_PROJECT_NAME" -f "$PROJECT_DIR/docker-compose.yml")
if [ -f "$PROJECT_DIR/.env" ]; then
    COMPOSE_ARGS=(--env-file "$PROJECT_DIR/.env" "${COMPOSE_ARGS[@]}")
fi
COMPOSE=(docker compose "${COMPOSE_ARGS[@]}")
MEDIA_VOLUME="${COMPOSE_PROJECT_NAME}_media_files"
DRY_RUN="${BACKUP_DRY_RUN:-0}"
DATE="$(date +%Y%m%d_%H%M%S)"

mkdir -p "$BACKUP_DIR"

if [ "$DRY_RUN" = "1" ]; then
    echo "[backup] dry-run enabled"
    echo "[backup] database → $BACKUP_DIR/db_${DATE}.sql.gz"
    echo "[backup] media → $BACKUP_DIR/media_${DATE}.tar.gz"
    echo "[backup] would use compose project ${COMPOSE_PROJECT_NAME}"
    echo "[backup] prune backups older than 14 days"
    exit 0
fi

"${COMPOSE[@]}" up -d db >/dev/null

DB_NAME="${DB_NAME:-$("${COMPOSE[@]}" exec -T db printenv POSTGRES_DB)}"
DB_USER="${DB_USER:-$("${COMPOSE[@]}" exec -T db printenv POSTGRES_USER)}"

# --- Database ---
DB_BACKUP="$BACKUP_DIR/db_${DATE}.sql.gz"
"${COMPOSE[@]}" exec -T db pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$DB_BACKUP"
echo "[backup] database → $DB_BACKUP"

# --- Media files ---
MEDIA_BACKUP="$BACKUP_DIR/media_${DATE}.tar.gz"
docker run --rm \
    -v "${MEDIA_VOLUME}:/data:ro" \
    -v "$BACKUP_DIR":/out \
    alpine tar czf "/out/media_${DATE}.tar.gz" -C /data .
echo "[backup] media → $MEDIA_BACKUP"

# --- Prune old backups (keep 14 days) ---
find "$BACKUP_DIR" -name "db_*.sql.gz" -mtime +14 -delete
find "$BACKUP_DIR" -name "media_*.tar.gz" -mtime +14 -delete
echo "[backup] pruned backups older than 14 days"
