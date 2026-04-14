#!/bin/sh
# Production backup script — database + media files.
#
# Usage:
#   ./scripts/backup.sh [/path/to/backup/dir]
#
# If no directory is given, backups are written to /opt/biobrassica/backups/.
# Add to cron (daily at 03:00):
#   0 3 * * * /opt/biobrassica/scripts/backup.sh /opt/biobrassica/backups >> /var/log/biobrassica-backup.log 2>&1
#
# Retention: the script removes backups older than 14 days.
# For durable off-site storage, pipe the output files to rclone/s3cmd/restic.

set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    . "$PROJECT_DIR/.env"
    set +a
fi

BACKUP_DIR="${1:-/opt/biobrassica/backups}"
DB_NAME="${DB_NAME:-biobrassica}"
DB_USER="${DB_USER:-biobrassica}"
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-biobrassica}"
COMPOSE="docker compose -p ${COMPOSE_PROJECT_NAME} -f ${PROJECT_DIR}/docker-compose.yml"
MEDIA_VOLUME="${COMPOSE_PROJECT_NAME}_media_files"
DRY_RUN="${BACKUP_DRY_RUN:-0}"
DATE="$(date +%Y%m%d_%H%M%S)"

mkdir -p "$BACKUP_DIR"

if [ "$DRY_RUN" = "1" ]; then
    echo "[backup] dry-run enabled"
    echo "[backup] database → $BACKUP_DIR/db_${DATE}.sql.gz"
    echo "[backup] media → $BACKUP_DIR/media_${DATE}.tar.gz"
    echo "[backup] would use compose project ${COMPOSE_PROJECT_NAME} with DB ${DB_NAME} (${DB_USER})"
    echo "[backup] prune backups older than 14 days"
    exit 0
fi

# --- Database ---
DB_BACKUP="$BACKUP_DIR/db_${DATE}.sql.gz"
$COMPOSE exec -T db pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$DB_BACKUP"
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
