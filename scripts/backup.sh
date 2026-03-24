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

BACKUP_DIR="${1:-/opt/biobrassica/backups}"
COMPOSE="docker compose -f /opt/biobrassica/docker-compose.yml"
DATE="$(date +%Y%m%d_%H%M%S)"

mkdir -p "$BACKUP_DIR"

# --- Database ---
DB_BACKUP="$BACKUP_DIR/db_${DATE}.sql.gz"
$COMPOSE exec -T db pg_dump -U biobrassica biobrassica | gzip > "$DB_BACKUP"
echo "[backup] database → $DB_BACKUP"

# --- Media files ---
MEDIA_BACKUP="$BACKUP_DIR/media_${DATE}.tar.gz"
docker run --rm \
    -v biobrassica_media_files:/data:ro \
    -v "$BACKUP_DIR":/out \
    alpine tar czf "/out/media_${DATE}.tar.gz" -C /data .
echo "[backup] media → $MEDIA_BACKUP"

# --- Prune old backups (keep 14 days) ---
find "$BACKUP_DIR" -name "db_*.sql.gz" -mtime +14 -delete
find "$BACKUP_DIR" -name "media_*.tar.gz" -mtime +14 -delete
echo "[backup] pruned backups older than 14 days"
