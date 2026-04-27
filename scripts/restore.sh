#!/usr/bin/env bash
# Restore the production database and, by default, the matching media archive.

set -euo pipefail

SCRIPT_NAME=restore

# shellcheck disable=SC1091
source "$(CDPATH= cd -- "$(dirname "$0")" && pwd)/lib/common.sh"

usage() {
    cat <<'EOF' >&2
Usage: ./scripts/restore.sh [--db /path/to/db.sql.gz] [--media /path/to/media.tar.gz] [--no-media] [--yes]

Defaults:
  - If --db is omitted, the latest backups/db_*.sql.gz file is used.
  - If --media is omitted, the matching media_*.tar.gz file is restored when present.
EOF
    exit 1
}

latest_backup() {
    local pattern="$1"

    if [ ! -d "$PROJECT_DIR/backups" ]; then
        return 0
    fi

    find "$PROJECT_DIR/backups" -maxdepth 1 -type f -name "$pattern" | sort | tail -n 1
}

matching_media_backup() {
    local db_backup="$1"
    local db_file
    local stamp
    local media_file

    db_file="$(basename "$db_backup")"
    stamp="${db_file#db_}"
    stamp="${stamp%.sql.gz}"
    media_file="$(dirname "$db_backup")/media_${stamp}.tar.gz"

    if [ -f "$media_file" ]; then
        printf '%s' "$media_file"
    fi
}

require_command docker
setup_prod_compose

DB_BACKUP=""
MEDIA_BACKUP=""
ASSUME_YES=0
RESTORE_MEDIA=1
DRY_RUN="${RESTORE_DRY_RUN:-0}"
MEDIA_VOLUME="${COMPOSE_PROJECT_NAME}_media_files"
DB_NAME="$(env_value DB_NAME biobrassica)"
DB_USER="$(env_value DB_USER biobrassica)"

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
        --no-media)
            RESTORE_MEDIA=0
            shift
            ;;
        --yes)
            ASSUME_YES=1
            shift
            ;;
        --help|-h)
            usage
            ;;
        *)
            usage
            ;;
    esac
done

if [ -z "$DB_BACKUP" ]; then
    DB_BACKUP="$(latest_backup 'db_*.sql.gz')"
fi

[ -n "$DB_BACKUP" ] || die "no database backup found in $PROJECT_DIR/backups"
[ -f "$DB_BACKUP" ] || die "database backup not found: $DB_BACKUP"

if [ "$RESTORE_MEDIA" = "1" ] && [ -z "$MEDIA_BACKUP" ]; then
    MEDIA_BACKUP="$(matching_media_backup "$DB_BACKUP")"
fi

if [ "$RESTORE_MEDIA" = "0" ] && [ -n "$MEDIA_BACKUP" ]; then
    die "cannot use --media and --no-media together"
fi

if [ -n "$MEDIA_BACKUP" ] && [ ! -f "$MEDIA_BACKUP" ]; then
    die "media backup not found: $MEDIA_BACKUP"
fi

if [ "$DRY_RUN" = "1" ]; then
    log_step "dry-run enabled"
    log_step "database backup -> $DB_BACKUP"
    if [ -n "$MEDIA_BACKUP" ]; then
        log_step "media backup -> $MEDIA_BACKUP"
    else
        log_step "media restore skipped"
    fi
    log_step "would stop the public web services before restoring"
    log_step "would restore database $DB_NAME as $DB_USER"
    log_step "would bring the full stack back up and verify it"
    exit 0
fi

log_step "database backup -> $DB_BACKUP"
if [ -n "$MEDIA_BACKUP" ]; then
    log_step "media backup -> $MEDIA_BACKUP"
else
    log_step "media restore skipped"
fi

if [ "$ASSUME_YES" != "1" ]; then
    if [ -t 0 ]; then
        printf '[restore] type RESTORE to continue: ' >&2
        read -r confirmation
        if [ "$confirmation" != "RESTORE" ]; then
            die "restore aborted"
        fi
    else
        die "--yes is required for non-interactive restores"
    fi
fi

log_step "stopping public web services"
"${COMPOSE[@]}" stop nginx django_website django_shop django_admin >/dev/null || true

log_step "ensuring database container is running"
"${COMPOSE[@]}" up -d db >/dev/null

log_step "resetting database"
"${COMPOSE[@]}" exec -T db psql -v ON_ERROR_STOP=1 -U "$DB_USER" postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();" >/dev/null
"${COMPOSE[@]}" exec -T db dropdb -U "$DB_USER" --if-exists "$DB_NAME"
"${COMPOSE[@]}" exec -T db createdb -U "$DB_USER" "$DB_NAME"

log_step "restoring database"
gunzip -c "$DB_BACKUP" | "${COMPOSE[@]}" exec -T db psql -v ON_ERROR_STOP=1 -U "$DB_USER" "$DB_NAME"

if [ -n "$MEDIA_BACKUP" ]; then
    log_step "restoring media"
    docker run --rm \
        -v "${MEDIA_VOLUME}:/data" \
        -v "$(dirname "$MEDIA_BACKUP"):/backup:ro" \
        alpine sh -eu -c "find /data -mindepth 1 -maxdepth 1 -exec rm -rf -- {} + && tar xzf '/backup/$(basename "$MEDIA_BACKUP")' -C /data"
fi

log_step "starting the full stack"
"${COMPOSE[@]}" up -d --remove-orphans

log_step "verifying restored services"
"$PROJECT_DIR/scripts/verify_stack.sh"

log_step "restore completed"