#!/usr/bin/env bash
# Build and redeploy the production stack with the required Django release tasks.

set -euo pipefail

SCRIPT_NAME=deploy

# shellcheck disable=SC1091
source "$(CDPATH= cd -- "$(dirname "$0")" && pwd)/lib/common.sh"

require_command docker
setup_prod_compose

# Start stateful services early — needed for backup and later for migrations.
log_step "starting database and redis"
"${COMPOSE[@]}" up -d db redis

# Backup runs in the background while we build images.
BACKUP_PID=""
log_step "creating a pre-deploy backup (background)"
"$PROJECT_DIR/scripts/backup.sh" &
BACKUP_PID=$!

# Build: django_website is enough — django_shop and django_admin share the same image.
# Nginx is built in parallel.
log_step "building production images"
"${COMPOSE[@]}" build --parallel django_website nginx

# Wait for backup to finish before proceeding.
if [ -n "$BACKUP_PID" ]; then
    log_step "waiting for backup to finish"
    wait "$BACKUP_PID" || log_step "backup completed with warnings"
fi

log_step "applying database migrations"
prod_manage migrate --noinput

log_step "collecting static files"
prod_manage collectstatic --noinput

log_step "starting the full stack"
"${COMPOSE[@]}" up -d --remove-orphans

log_step "verifying deployment"
"$PROJECT_DIR/scripts/verify_stack.sh"
