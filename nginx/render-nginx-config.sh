#!/bin/sh
set -eu

normalize_host_list() {
    printf '%s' "$1" \
        | tr ',' '\n' \
        | sed 's/^[[:space:]]*//; s/[[:space:]]*$//' \
        | sed '/^$/d' \
        | xargs
}

unique_csv() {
    printf '%s' "$1" \
        | tr ',' '\n' \
        | sed 's/^[[:space:]]*//; s/[[:space:]]*$//' \
        | sed '/^$/d' \
        | awk '!seen[$0]++' \
        | paste -sd, -
}

base_domains() {
    unique_csv "${primary_domain},${domain_aliases}"
}

derived_host_csv() {
    role="$1"

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
    done <<EOF
$(printf '%s' "$resolved_domains" | tr ',' '\n')
EOF
}

primary_domain="${PRIMARY_DOMAIN:-biobrassica.pt}"
domain_aliases="${DOMAIN_ALIASES:-}"
resolved_domains="$(base_domains)"

website_host="${WEBSITE_HOST:-$primary_domain}"
website_allowed_hosts="${WEBSITE_ALLOWED_HOSTS:-$(derived_host_csv website | paste -sd, -)}"
shop_host="${SHOP_HOST:-loja.$primary_domain}"
shop_allowed_hosts="${SHOP_ALLOWED_HOSTS:-$(derived_host_csv shop | paste -sd, -)}"
admin_host="${ADMIN_HOST:-admin.$primary_domain}"
admin_allowed_hosts="${ADMIN_ALLOWED_HOSTS:-$(derived_host_csv admin | paste -sd, -)}"
tls_cert_name="${TLS_CERT_NAME:-$website_host}"

export WEBSITE_HOST="$website_host"
export WEBSITE_SERVER_NAMES="$(normalize_host_list "$website_allowed_hosts")"
export SHOP_HOST="$shop_host"
export SHOP_SERVER_NAMES="$(normalize_host_list "$shop_allowed_hosts")"
export ADMIN_HOST="$admin_host"
export ADMIN_SERVER_NAMES="$(normalize_host_list "$admin_allowed_hosts")"
export TLS_CERT_NAME="$tls_cert_name"

template_vars='${WEBSITE_HOST} ${WEBSITE_SERVER_NAMES} ${SHOP_HOST} ${SHOP_SERVER_NAMES} ${ADMIN_HOST} ${ADMIN_SERVER_NAMES} ${TLS_CERT_NAME}'

envsubst "$template_vars" \
    < /opt/biobrassica/templates/app.conf.template \
    > /etc/nginx/conf.d/app.conf
envsubst "$template_vars" \
    < /opt/biobrassica/templates/default.conf.template \
    > /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'