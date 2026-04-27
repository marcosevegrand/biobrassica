#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
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

COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-biobrassica}"
COMPOSE_ARGS=(-p "$COMPOSE_PROJECT_NAME" -f "$PROJECT_DIR/docker-compose.yml")
if [ -f "$ENV_FILE" ]; then
    COMPOSE_ARGS=(--env-file "$ENV_FILE" "${COMPOSE_ARGS[@]}")
fi
COMPOSE=(docker compose "${COMPOSE_ARGS[@]}")

PRIMARY_DOMAIN="$(env_value PRIMARY_DOMAIN marcosevegrand.com)"
DOMAIN_ALIASES="$(env_value DOMAIN_ALIASES '')"
PUBLIC_DOMAINS="$(unique_csv "${PRIMARY_DOMAIN},${DOMAIN_ALIASES}")"

WEBSITE_ALLOWED_HOSTS="$(env_value WEBSITE_ALLOWED_HOSTS "$(derived_hosts_csv website "$PUBLIC_DOMAINS")")"
SHOP_ALLOWED_HOSTS="$(env_value SHOP_ALLOWED_HOSTS "$(derived_hosts_csv shop "$PUBLIC_DOMAINS")")"
ADMIN_ALLOWED_HOSTS="$(env_value ADMIN_ALLOWED_HOSTS "$(derived_hosts_csv admin "$PUBLIC_DOMAINS")")"
WEBSITE_HOST="$(env_value WEBSITE_HOST "$PRIMARY_DOMAIN")"
TLS_CERT_NAME="$(env_value TLS_CERT_NAME "$WEBSITE_HOST")"
CERTBOT_EMAIL="$(env_value CERTBOT_EMAIL '')"
CERTBOT_STAGING="$(env_value CERTBOT_STAGING 0)"

if [ -z "$CERTBOT_EMAIL" ]; then
    echo "[certbot] set CERTBOT_EMAIL in .env before requesting a certificate" >&2
    exit 1
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
$(printf '%s' "$configured_hosts" | tr ',' '\n' | sed 's/^[[:space:]]*//; s/[[:space:]]*$//' | sed '/^$/d')
EOF
}

collect_domain_args "$WEBSITE_ALLOWED_HOSTS"
collect_domain_args "$SHOP_ALLOWED_HOSTS"
collect_domain_args "$ADMIN_ALLOWED_HOSTS"

if [ "${#domain_args[@]}" -eq 0 ]; then
    echo "[certbot] no domains configured; set PRIMARY_DOMAIN (and optionally DOMAIN_ALIASES) in .env" >&2
    exit 1
fi

mkdir -p "$PROJECT_DIR/certbot/www" "$PROJECT_DIR/certbot/conf"

echo "[certbot] requesting certificate ${TLS_CERT_NAME} for: ${domain_args[*]}"

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