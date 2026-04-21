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

http_redirect_checks=(
    "marcosevegrand.com|https://marcosevegrand.com/"
    "www.marcosevegrand.com|https://marcosevegrand.com/"
    "loja.marcosevegrand.com|https://loja.marcosevegrand.com/"
    "admin.marcosevegrand.com|https://admin.marcosevegrand.com/"
)

https_redirect_checks=(
    "www.marcosevegrand.com|https://marcosevegrand.com/"
)

health_checks=(
    "marcosevegrand.com|django_website"
    "loja.marcosevegrand.com|django_shop"
    "admin.marcosevegrand.com|django_admin"
)

cert_files=(
    "$PROJECT_DIR/certbot/conf/live/marcosevegrand.com/fullchain.pem"
    "$PROJECT_DIR/certbot/conf/live/marcosevegrand.com/privkey.pem"
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
        :
    else
        log_step "TLS files are present; inspect nginx logs below"
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