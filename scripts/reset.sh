#!/usr/bin/env bash
# Hard-reset the production PostgreSQL volume, redeploy the stack, and optionally restore a database backup.

set -euo pipefail

SCRIPT_NAME=reset

# shellcheck disable=SC1091
source "$(CDPATH= cd -- "$(dirname "$0")" && pwd)/lib/common.sh"

usage() {
    cat <<'EOF' >&2
Usage: ./scripts/reset.sh [--db /path/to/db.sql.gz] [--yes]

Defaults:
  - If --db is omitted, the stack is redeployed with a fresh empty database.
  - Media data is preserved; use ./scripts/restore.sh when you also need a media restore.
EOF
    exit 1
}

require_command docker
setup_prod_compose

DB_BACKUP=""
ASSUME_YES=0
DRY_RUN="${RESET_DRY_RUN:-0}"
DB_READY_TIMEOUT="${DB_READY_TIMEOUT:-60}"
DB_VOLUME="${COMPOSE_PROJECT_NAME}_pg_data"
DB_NAME="$(env_value DB_NAME biobrassica)"
DB_USER="$(env_value DB_USER biobrassica)"

while [ "$#" -gt 0 ]; do
    case "$1" in
        --db)
            [ "$#" -ge 2 ] || usage
            DB_BACKUP="$2"
            shift 2
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

if [ -n "$DB_BACKUP" ] && [ ! -f "$DB_BACKUP" ]; then
    die "database backup not found: $DB_BACKUP"
fi

if [ "$DRY_RUN" = "1" ]; then
    log_step "dry-run enabled"
    log_step "database volume -> $DB_VOLUME"
    if [ -n "$DB_BACKUP" ]; then
        log_step "database backup -> $DB_BACKUP"
    else
        log_step "database restore skipped"
    fi
    log_step "would stop the current production stack"
    log_step "would remove the PostgreSQL volume and rebuild the web images"
    log_step "would start db, then wait for $DB_NAME readiness"
    log_step "would apply migrations, collect static files, restart the full stack, and verify it"
    exit 0
fi

log_step "database volume -> $DB_VOLUME"
if [ -n "$DB_BACKUP" ]; then
    log_step "database backup -> $DB_BACKUP"
else
    log_step "database restore skipped"
fi

if [ "$ASSUME_YES" != "1" ]; then
    if [ -t 0 ]; then
        printf '[reset] type RESET to continue: ' >&2
        read -r confirmation
        if [ "$confirmation" != "RESET" ]; then
            die "reset aborted"
        fi
    else
        die "--yes is required for non-interactive resets"
    fi
fi

log_step "stopping production stack"
"${COMPOSE[@]}" down --remove-orphans >/dev/null || true

if docker volume inspect "$DB_VOLUME" >/dev/null 2>&1; then
    log_step "removing database volume"
    docker volume rm -f "$DB_VOLUME" >/dev/null
else
    log_step "database volume already absent"
fi

log_step "building production images"
"${COMPOSE[@]}" build django_website django_shop django_admin

log_step "starting stateful services"
"${COMPOSE[@]}" up -d db >/dev/null

log_step "waiting for database readiness"
wait_started_at=$SECONDS
while ! "${COMPOSE[@]}" exec -T db pg_isready -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; do
    if [ $((SECONDS - wait_started_at)) -ge "$DB_READY_TIMEOUT" ]; then
        die "database did not become ready within ${DB_READY_TIMEOUT}s"
    fi
    sleep 1
done

if [ -n "$DB_BACKUP" ]; then
    log_step "restoring database"
    gunzip -c "$DB_BACKUP" | "${COMPOSE[@]}" exec -T db psql -v ON_ERROR_STOP=1 -U "$DB_USER" "$DB_NAME"
fi

log_step "applying database migrations"
prod_manage migrate --noinput

log_step "collecting static files"
prod_manage collectstatic --noinput

log_step "starting the full stack"
"${COMPOSE[@]}" up -d --force-recreate --remove-orphans

log_step "verifying deployment"
"$PROJECT_DIR/scripts/verify_stack.sh"

log_step "reset completed"