#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-biobrassica}"
COMPOSE_ARGS=(-p "$COMPOSE_PROJECT_NAME" -f "$PROJECT_DIR/docker-compose.yml")
if [ -f "$PROJECT_DIR/.env" ]; then
    COMPOSE_ARGS=(--env-file "$PROJECT_DIR/.env" "${COMPOSE_ARGS[@]}")
fi
COMPOSE=(docker compose "${COMPOSE_ARGS[@]}")
DRY_RUN="${VERIFY_DRY_RUN:-0}"
ENV_FILE="$PROJECT_DIR/.env"

env_value() {
    local name="$1"
    local default="$2"
    local line

    if [ -n "${!name:-}" ]; then
        printf '%s' "${!name}"
        return 0
    fi

    if [ -f "$ENV_FILE" ]; then
        line="$(grep -E "^${name}=" "$ENV_FILE" | tail -n 1 || true)"
        if [ -n "$line" ]; then
            printf '%s' "${line#*=}"
            return 0
        fi
    fi

    printf '%s' "$default"
}

unique_csv() {
    printf '%s' "$1" | tr ',' '\n' | sed 's/^[[:space:]]*//; s/[[:space:]]*$//' | sed '/^$/d' | awk '!seen[$0]++' | paste -sd, -
}

derived_hosts_csv() {
    local role="$1"
    local domains_csv="$2"
    local domain

    while IFS= read -r domain; do
        [ -n "$domain" ] || continue
        case "$role" in
            website)
                printf '%s\n' "$domain"
                printf 'www.%s\n' "$domain"
                ;;
            shop)
                printf 'loja.%s\n' "$domain"
                ;;
            admin)
                printf 'admin.%s\n' "$domain"
                ;;
        esac
    done <<EOF | awk '!seen[$0]++' | paste -sd, -
$(printf '%s' "$domains_csv" | tr ',' '\n' | sed 's/^[[:space:]]*//; s/[[:space:]]*$//' | sed '/^$/d')
EOF
}

PRIMARY_DOMAIN="$(env_value PRIMARY_DOMAIN marcosevegrand.com)"
DOMAIN_ALIASES="$(env_value DOMAIN_ALIASES '')"
PUBLIC_DOMAINS="$(unique_csv "${PRIMARY_DOMAIN},${DOMAIN_ALIASES}")"

WEBSITE_HOST="$(env_value WEBSITE_HOST "$PRIMARY_DOMAIN")"
WEBSITE_ALLOWED_HOSTS="$(env_value WEBSITE_ALLOWED_HOSTS "$(derived_hosts_csv website "$PUBLIC_DOMAINS")")"
SHOP_HOST="$(env_value SHOP_HOST "loja.${PRIMARY_DOMAIN}")"
SHOP_ALLOWED_HOSTS="$(env_value SHOP_ALLOWED_HOSTS "$(derived_hosts_csv shop "$PUBLIC_DOMAINS")")"
ADMIN_HOST="$(env_value ADMIN_HOST "admin.${PRIMARY_DOMAIN}")"
ADMIN_ALLOWED_HOSTS="$(env_value ADMIN_ALLOWED_HOSTS "$(derived_hosts_csv admin "$PUBLIC_DOMAINS")")"
TLS_CERT_NAME="$(env_value TLS_CERT_NAME "$WEBSITE_HOST")"

split_hosts() {
    printf '%s' "$1" | tr ',' '\n' | sed 's/^[[:space:]]*//; s/[[:space:]]*$//' | sed '/^$/d'
}

append_redirect_checks() {
    local canonical_host="$1"
    local configured_hosts="$2"
    local host

    while IFS= read -r host; do
        http_redirect_checks+=("${host}|https://${canonical_host}/")
        if [ "$host" != "$canonical_host" ]; then
            https_redirect_checks+=("${host}|https://${canonical_host}/")
        fi
    done <<EOF
$(split_hosts "$configured_hosts")
EOF
}

http_redirect_checks=()
https_redirect_checks=()

append_redirect_checks "$WEBSITE_HOST" "$WEBSITE_ALLOWED_HOSTS"
append_redirect_checks "$SHOP_HOST" "$SHOP_ALLOWED_HOSTS"
append_redirect_checks "$ADMIN_HOST" "$ADMIN_ALLOWED_HOSTS"

health_checks=(
    "${WEBSITE_HOST}|django_website"
    "${SHOP_HOST}|django_shop"
    "${ADMIN_HOST}|django_admin"
)

cert_files=(
    "$PROJECT_DIR/certbot/conf/live/${TLS_CERT_NAME}/fullchain.pem"
    "$PROJECT_DIR/certbot/conf/live/${TLS_CERT_NAME}/privkey.pem"
)

log_step() {
    echo "[verify] $*"
}

report_missing_certificates() {
    local missing=0
    local cert_file

    for cert_file in "${cert_files[@]}"; do
        if [ ! -r "$cert_file" ]; then
            if [ "$missing" -eq 0 ]; then
                log_step "missing TLS files required by nginx:"
            fi
            printf '[verify]   %s\n' "$cert_file"
            missing=1
        fi
    done

    return "$missing"
}

ensure_running_nginx() {
    if "${COMPOSE[@]}" ps --status running --services | grep -qx 'nginx'; then
        return 0
    fi

    log_step "nginx is not running"
    if report_missing_certificates; then
        log_step "TLS files are present; inspect nginx logs below"
    else
        log_step "restore the existing certbot/conf directory or issue a new certificate before restarting nginx"
    fi

    log_step "recent nginx logs"
    "${COMPOSE[@]}" logs --tail=100 nginx || true
    exit 1
}

check_http_redirect() {
    local host="$1"
    local expected_location="$2"
    local headers
    local status_code
    local location

    headers="$({ curl -fsS -D - -o /dev/null --max-redirs 0 --resolve "${host}:80:127.0.0.1" "http://${host}/"; } 2>&1 | tr -d '\r')"
    status_code="$(printf '%s\n' "$headers" | awk '/^HTTP\// {print $2; exit}')"
    location="$(printf '%s\n' "$headers" | awk 'BEGIN { IGNORECASE = 1 } /^Location:/ { print $2; exit }')"

    [ "$status_code" = "301" ]
    [ "$location" = "$expected_location" ]
}

check_https_redirect() {
    local host="$1"
    local expected_location="$2"
    local headers
    local status_code
    local location

    headers="$({ curl -fsS -D - -o /dev/null --max-redirs 0 --resolve "${host}:443:127.0.0.1" "https://${host}/"; } 2>&1 | tr -d '\r')"
    status_code="$(printf '%s\n' "$headers" | awk '/^HTTP\// {print $2; exit}')"
    location="$(printf '%s\n' "$headers" | awk 'BEGIN { IGNORECASE = 1 } /^Location:/ { print $2; exit }')"

    [ "$status_code" = "301" ]
    [ "$location" = "$expected_location" ]
}

check_https_health() {
    local host="$1"

    curl -fsS --resolve "${host}:443:127.0.0.1" "https://${host}/_health/" > /dev/null
}

check_upstream_health() {
    local host="$1"
    local service="$2"

    "${COMPOSE[@]}" exec -T nginx sh -eu -c \
        "wget -q -O /dev/null --header='Host: ${host}' 'http://${service}:8000/_health/'"
}

if [ "$DRY_RUN" = "1" ]; then
    log_step "dry-run enabled"
    log_step "would print docker compose status for ${COMPOSE_PROJECT_NAME}"
    log_step "would run nginx -t inside the nginx container"
    for check in "${http_redirect_checks[@]}"; do
        IFS='|' read -r host expected_location <<< "$check"
        log_step "would verify HTTP redirect for ${host} -> ${expected_location}"
    done
    for check in "${https_redirect_checks[@]}"; do
        IFS='|' read -r host expected_location <<< "$check"
        log_step "would verify HTTPS redirect for ${host} -> ${expected_location}"
    done
    for check in "${health_checks[@]}"; do
        IFS='|' read -r host service <<< "$check"
        log_step "would verify HTTPS /_health/ for ${host} via localhost"
        log_step "would verify nginx can reach ${service}:8000/_health/ for ${host}"
    done
    exit 0
fi

log_step "compose status"
"${COMPOSE[@]}" ps

ensure_running_nginx

log_step "validating nginx configuration"
"${COMPOSE[@]}" exec -T nginx nginx -t

for check in "${http_redirect_checks[@]}"; do
    IFS='|' read -r host expected_location <<< "$check"
    log_step "checking HTTP redirect for ${host}"
    check_http_redirect "$host" "$expected_location"
done

for check in "${https_redirect_checks[@]}"; do
    IFS='|' read -r host expected_location <<< "$check"
    log_step "checking HTTPS redirect for ${host}"
    check_https_redirect "$host" "$expected_location"
done

for check in "${health_checks[@]}"; do
    IFS='|' read -r host service <<< "$check"
    log_step "checking HTTPS health for ${host}"
    check_https_health "$host"
    log_step "checking nginx upstream for ${host} -> ${service}"
    check_upstream_health "$host" "$service"
done

log_step "all checks passed"