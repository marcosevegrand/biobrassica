#!/usr/bin/env bash
set -euo pipefail

SCRIPT_NAME="createsuperuser"
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
. "$SCRIPT_DIR/lib/common.sh"

require_command docker
setup_prod_compose

log_step "Iniciando criação interativa de superutilizador no serviço django_admin..."
log_step "Será necessário fornecer email, nome de utilizador e password."

exec "${COMPOSE[@]}" run --rm -it django_admin python manage.py createsuperuser
