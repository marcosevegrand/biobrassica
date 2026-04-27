#!/usr/bin/env bash
# Request or renew the production TLS certificate bundle for the configured domains.

set -euo pipefail

SCRIPT_NAME=cert

# shellcheck disable=SC1091
source "$(CDPATH= cd -- "$(dirname "$0")" && pwd)/lib/common.sh"

require_command docker
setup_prod_compose
configure_public_domains

CERTBOT_EMAIL="$(env_value CERTBOT_EMAIL '')"
CERTBOT_STAGING="$(env_value CERTBOT_STAGING 0)"

if [ -z "$CERTBOT_EMAIL" ]; then
    die "set CERTBOT_EMAIL in .env before requesting a certificate"
fi

declare -A seen_hosts=()
domain_args=()

collect_domain_args() {
    local configured_hosts="$1"
    local host

    while IFS= read -r host; do
        [ -n "$host" ] || continue
        if [ -n "${seen_hosts[$host]+x}" ]; then
            continue
        fi
        seen_hosts[$host]=1
        domain_args+=(-d "$host")
    done <<EOF
$(csv_to_lines "$configured_hosts")
EOF
}

collect_domain_args "$WEBSITE_ALLOWED_HOSTS"
collect_domain_args "$SHOP_ALLOWED_HOSTS"
collect_domain_args "$ADMIN_ALLOWED_HOSTS"

if [ "${#domain_args[@]}" -eq 0 ]; then
    die "no domains configured; set PRIMARY_DOMAIN (and optionally DOMAIN_ALIASES) in .env"
fi

mkdir -p "$PROJECT_DIR/certbot/www" "$PROJECT_DIR/certbot/conf"

if service_is_running nginx; then
    log_step "nginx is running; using webroot validation"
    certbot_args=(
        certonly
        --webroot
        -w /var/www/certbot
        --cert-name "$TLS_CERT_NAME"
        "${domain_args[@]}"
        --email "$CERTBOT_EMAIL"
        --agree-tos
        --no-eff-email
    )
    if [ "$CERTBOT_STAGING" = "1" ]; then
        certbot_args+=(--staging)
    fi
    "${COMPOSE[@]}" --profile tools run --rm certbot "${certbot_args[@]}"
    log_step "reloading nginx"
    "${COMPOSE[@]}" exec -T nginx nginx -s reload
else
    log_step "nginx is not running; using standalone validation"
    certbot_args=(
        certonly
        --standalone
        --cert-name "$TLS_CERT_NAME"
        "${domain_args[@]}"
        --email "$CERTBOT_EMAIL"
        --agree-tos
        --no-eff-email
    )
    if [ "$CERTBOT_STAGING" = "1" ]; then
        certbot_args+=(--staging)
    fi
    "${COMPOSE[@]}" --profile tools run --rm --service-ports certbot "${certbot_args[@]}"
fi