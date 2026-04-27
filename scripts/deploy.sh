#!/usr/bin/env bash
# Build and redeploy the production stack with the required Django release tasks.

set -euo pipefail

SCRIPT_NAME=deploy

# shellcheck disable=SC1091
source "$(CDPATH= cd -- "$(dirname "$0")" && pwd)/lib/common.sh"

require_command docker
setup_prod_compose

log_step "creating a pre-deploy backup"
"$PROJECT_DIR/scripts/backup.sh"

log_step "building production images"
"${COMPOSE[@]}" build django_website django_shop django_admin

log_step "starting stateful services"
"${COMPOSE[@]}" up -d db redis

log_step "applying database migrations"
prod_manage migrate --noinput

log_step "collecting static files"
prod_manage collectstatic --noinput

log_step "starting the full stack"
"${COMPOSE[@]}" up -d --force-recreate --remove-orphans

log_step "verifying deployment"
"$PROJECT_DIR/scripts/verify_stack.sh"