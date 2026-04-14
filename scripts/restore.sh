#!/bin/sh
# Production restore helper — database + optional media files.
#
# Usage:
#   sh ./scripts/restore.sh --db /path/to/db.sql.gz [--media /path/to/media.tar.gz]

set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    . "$PROJECT_DIR/.env"
    set +a
fi

usage() {
    echo "Usage: sh ./scripts/restore.sh --db /path/to/db.sql.gz [--media /path/to/media.tar.gz]" >&2
    exit 1
}

DB_BACKUP=
MEDIA_BACKUP=

while [ "$#" -gt 0 ]; do
    case "$1" in
        --db)
            [ "$#" -ge 2 ] || usage
            DB_BACKUP="$2"
            shift 2
            ;;
        --media)
            [ "$#" -ge 2 ] || usage
            MEDIA_BACKUP="$2"
            shift 2
            ;;
        *)
            usage
            ;;
    esac
done

[ -n "$DB_BACKUP" ] || usage
[ -f "$DB_BACKUP" ] || {
    echo "[restore] database backup not found: $DB_BACKUP" >&2
    exit 1
}

if [ -n "$MEDIA_BACKUP" ] && [ ! -f "$MEDIA_BACKUP" ]; then
    echo "[restore] media backup not found: $MEDIA_BACKUP" >&2
    exit 1
fi

DB_NAME="${DB_NAME:-biobrassica}"
DB_USER="${DB_USER:-biobrassica}"
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-biobrassica}"
COMPOSE_FILE="${PROJECT_DIR}/docker-compose.yml"
COMPOSE="docker compose -p ${COMPOSE_PROJECT_NAME} -f ${COMPOSE_FILE}"
MEDIA_VOLUME="${COMPOSE_PROJECT_NAME}_media_files"
DRY_RUN="${RESTORE_DRY_RUN:-0}"

if [ "$DRY_RUN" = "1" ]; then
    echo "[restore] dry-run enabled"
    echo "[restore] would start db service via compose project ${COMPOSE_PROJECT_NAME}"
    echo "[restore] would restore database ${DB_NAME} as ${DB_USER} from ${DB_BACKUP}"
    if [ -n "$MEDIA_BACKUP" ]; then
        echo "[restore] would extract media archive ${MEDIA_BACKUP} into volume ${MEDIA_VOLUME}"
    else
        echo "[restore] media restore skipped"
    fi
    echo "[restore] would bring the full stack up with --remove-orphans"
    echo "[restore] would run host-header health checks for biobrassica.pt, loja.biobrassica.pt, and admin.biobrassica.pt"
    exit 0
fi

echo "[restore] ensuring db service is running"
$COMPOSE up -d db

echo "[restore] restoring database from $DB_BACKUP"
gunzip -c "$DB_BACKUP" | $COMPOSE exec -T db psql -U "$DB_USER" "$DB_NAME"

if [ -n "$MEDIA_BACKUP" ]; then
    MEDIA_BACKUP_DIR="$(CDPATH= cd -- "$(dirname "$MEDIA_BACKUP")" && pwd)"
    MEDIA_BACKUP_FILE="$(basename "$MEDIA_BACKUP")"
    echo "[restore] restoring media from $MEDIA_BACKUP"
    docker run --rm \
        -v "${MEDIA_VOLUME}:/data" \
        -v "${MEDIA_BACKUP_DIR}:/backup:ro" \
        alpine sh -eu -c "cd /data && tar xzf '/backup/${MEDIA_BACKUP_FILE}'"
fi

echo "[restore] starting full stack"
$COMPOSE up -d --remove-orphans

for host in biobrassica.pt loja.biobrassica.pt admin.biobrassica.pt; do
    echo "[restore] health check for $host"
    curl -fsS -H "Host: $host" http://127.0.0.1/_health/ > /dev/null
done

echo "[restore] restore verification completed"