#!/usr/bin/env bash

COMMON_DIR="$(CDPATH= cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_DIR="$(dirname "$COMMON_DIR")"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

log_step() {
    printf '[%s] %s\n' "${SCRIPT_NAME:-script}" "$*"
}

die() {
    printf '[%s] %s\n' "${SCRIPT_NAME:-script}" "$*" >&2
    exit 1
}

require_command() {
    command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"
}

require_prod_env_file() {
    [ -f "$PROJECT_DIR/.env" ] || die "missing $PROJECT_DIR/.env; copy .env.example to .env and fill it in first"
}

setup_prod_compose() {
    require_prod_env_file
    COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-biobrassica}"
    ENV_FILE="$PROJECT_DIR/.env"
    COMPOSE=(
        docker compose
        --env-file "$ENV_FILE"
        -p "$COMPOSE_PROJECT_NAME"
        -f "$PROJECT_DIR/docker-compose.yml"
    )
}

setup_dev_compose() {
    COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-biobrassica-dev}"
    ENV_FILE="$PROJECT_DIR/.env.dev"
    COMPOSE=(
        docker compose
        -p "$COMPOSE_PROJECT_NAME"
        -f "$PROJECT_DIR/docker-compose.yml"
        -f "$PROJECT_DIR/docker-compose.dev.yml"
    )
    if [ -f "$ENV_FILE" ]; then
        COMPOSE=(
            docker compose
            --env-file "$ENV_FILE"
            -p "$COMPOSE_PROJECT_NAME"
            -f "$PROJECT_DIR/docker-compose.yml"
            -f "$PROJECT_DIR/docker-compose.dev.yml"
        )
    fi
}

env_value() {
    local name="$1"
    local default="$2"
    local line

    if [ -n "${!name:-}" ]; then
        printf '%s' "${!name}"
        return 0
    fi

    if [ -n "${ENV_FILE:-}" ] && [ -f "$ENV_FILE" ]; then
        line="$(grep -E "^${name}=" "$ENV_FILE" | tail -n 1 || true)"
        if [ -n "$line" ]; then
            printf '%s' "${line#*=}"
            return 0
        fi
    fi

    printf '%s' "$default"
}

csv_to_lines() {
    printf '%s' "$1" | tr ',' '\n' | sed 's/^[[:space:]]*//; s/[[:space:]]*$//' | sed '/^$/d'
}

unique_csv() {
    csv_to_lines "$1" | awk '!seen[$0]++' | paste -sd, -
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
            *)
                die "unknown host role: $role"
                ;;
        esac
    done <<EOF | awk '!seen[$0]++' | paste -sd, -
$(csv_to_lines "$domains_csv")
EOF
}

configure_public_domains() {
    PRIMARY_DOMAIN="$(env_value PRIMARY_DOMAIN biobrassica.pt)"
    DOMAIN_ALIASES="$(env_value DOMAIN_ALIASES '')"
    PUBLIC_DOMAINS="$(unique_csv "${PRIMARY_DOMAIN},${DOMAIN_ALIASES}")"

    WEBSITE_HOST="$(env_value WEBSITE_HOST "$PRIMARY_DOMAIN")"
    WEBSITE_ALLOWED_HOSTS="$(env_value WEBSITE_ALLOWED_HOSTS "$(derived_hosts_csv website "$PUBLIC_DOMAINS")")"
    SHOP_HOST="$(env_value SHOP_HOST "loja.${PRIMARY_DOMAIN}")"
    SHOP_ALLOWED_HOSTS="$(env_value SHOP_ALLOWED_HOSTS "$(derived_hosts_csv shop "$PUBLIC_DOMAINS")")"
    ADMIN_HOST="$(env_value ADMIN_HOST "admin.${PRIMARY_DOMAIN}")"
    ADMIN_ALLOWED_HOSTS="$(env_value ADMIN_ALLOWED_HOSTS "$(derived_hosts_csv admin "$PUBLIC_DOMAINS")")"
    TLS_CERT_NAME="$(env_value TLS_CERT_NAME "$WEBSITE_HOST")"
}

service_is_running() {
    local service="$1"

    "${COMPOSE[@]}" ps --status running --services | grep -qx "$service"
}

prod_manage() {
    "${COMPOSE[@]}" run --rm django_website python manage.py "$@"
}

dev_manage() {
    "${COMPOSE[@]}" exec -T django python manage.py "$@"
}