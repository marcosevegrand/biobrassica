#!/bin/sh
set -eu

normalize_host_list() {
    printf '%s' "$1" \
        | tr ',' '\n' \
        | sed 's/^[[:space:]]*//; s/[[:space:]]*$//' \
        | sed '/^$/d' \
        | xargs
}

website_host="${WEBSITE_HOST:-marcosevegrand.com}"
website_allowed_hosts="${WEBSITE_ALLOWED_HOSTS:-marcosevegrand.com,www.marcosevegrand.com}"
shop_host="${SHOP_HOST:-loja.marcosevegrand.com}"
shop_allowed_hosts="${SHOP_ALLOWED_HOSTS:-loja.marcosevegrand.com}"
admin_host="${ADMIN_HOST:-admin.marcosevegrand.com}"
admin_allowed_hosts="${ADMIN_ALLOWED_HOSTS:-admin.marcosevegrand.com}"
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