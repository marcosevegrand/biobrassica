#!/usr/bin/env bash
# Start the local development stack and run the minimal setup tasks.

set -euo pipefail

SCRIPT_NAME=dev

# shellcheck disable=SC1091
source "$(CDPATH= cd -- "$(dirname "$0")" && pwd)/lib/common.sh"

require_command docker
setup_dev_compose

log_step "starting development services"
"${COMPOSE[@]}" up -d --build db redis django tailwind mailpit

log_step "applying database migrations"
dev_manage migrate --noinput

log_step "compiling locale catalogs"
dev_manage compilemessages

cat <<'EOF'
[dev] Ready.
[dev] Website: http://lvh.me:8000
[dev] Shop:    http://loja.lvh.me:8000
[dev] Admin:   http://admin.lvh.me:8000
[dev] Mailpit: http://localhost:8025
EOF