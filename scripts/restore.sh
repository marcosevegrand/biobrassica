#!/usr/bin/env bash
# Production restore helper — database + optional media files.
#
# Usage:
#   ./scripts/restore.sh --db /path/to/db.sql.gz [--media /path/to/media.tar.gz] [--yes]

set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

usage() {
    echo "Usage: ./scripts/restore.sh --db /path/to/db.sql.gz [--media /path/to/media.tar.gz] [--yes]" >&2
    exit 1
}

DB_BACKUP=
MEDIA_BACKUP=
ASSUME_YES=0

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
        --yes)
            ASSUME_YES=1
            shift
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

COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-biobrassica}"
COMPOSE_ARGS=(-p "$COMPOSE_PROJECT_NAME" -f "$PROJECT_DIR/docker-compose.yml")
if [ -f "$PROJECT_DIR/.env" ]; then
    COMPOSE_ARGS=(--env-file "$PROJECT_DIR/.env" "${COMPOSE_ARGS[@]}")
fi
COMPOSE=(docker compose "${COMPOSE_ARGS[@]}")
MEDIA_VOLUME="${COMPOSE_PROJECT_NAME}_media_files"
DRY_RUN="${RESTORE_DRY_RUN:-0}"

if [ "$DRY_RUN" = "1" ]; then
    echo "[restore] dry-run enabled"
    echo "[restore] would start db service via compose project ${COMPOSE_PROJECT_NAME}"
    echo "[restore] would restore database ${DB_NAME:-biobrassica} as ${DB_USER:-biobrassica} from ${DB_BACKUP}"
    if [ -n "$MEDIA_BACKUP" ]; then
        echo "[restore] would extract media archive ${MEDIA_BACKUP} into volume ${MEDIA_VOLUME}"
    else
        echo "[restore] media restore skipped"
    fi
    echo "[restore] would bring the full stack up with --remove-orphans"
    echo "[restore] would run host-header health checks for marcosevegrand.com, loja.marcosevegrand.com, and admin.marcosevegrand.com"
    exit 0
fi

if [ "$ASSUME_YES" != "1" ]; then
    if [ -t 0 ]; then
        printf "[restore] type RESTORE to continue: " >&2
        read -r confirmation
        if [ "$confirmation" != "RESTORE" ]; then
            echo "[restore] restore aborted" >&2
            exit 1
        fi
    else
        echo "[restore] --yes is required for non-interactive restores" >&2
        exit 1
    fi
fi

echo "[restore] ensuring db service is running"
"${COMPOSE[@]}" up -d db

DB_NAME="${DB_NAME:-$("${COMPOSE[@]}" exec -T db printenv POSTGRES_DB)}"
DB_USER="${DB_USER:-$("${COMPOSE[@]}" exec -T db printenv POSTGRES_USER)}"

echo "[restore] restoring database from $DB_BACKUP"
gunzip -c "$DB_BACKUP" | "${COMPOSE[@]}" exec -T db psql -U "$DB_USER" "$DB_NAME"

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
"${COMPOSE[@]}" up -d --remove-orphans

echo "[restore] verifying ingress and upstream health"
"$PROJECT_DIR/scripts/verify_stack.sh"

echo "[restore] restore verification completed"