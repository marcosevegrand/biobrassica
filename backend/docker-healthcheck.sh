#!/bin/sh
set -eu

health_host="${HEALTHCHECK_HOST:-${ALLOWED_HOSTS%%,*}}"
primary_domain="${PRIMARY_DOMAIN:-marcosevegrand.com}"
site_role="${SITE_ROLE:-website}"

if [ -z "$health_host" ]; then
    case "$site_role" in
        website)
            health_host="${WEBSITE_HOST:-$primary_domain}"
            ;;
        shop)
            health_host="${SHOP_HOST:-loja.$primary_domain}"
            ;;
        admin)
            health_host="${ADMIN_HOST:-admin.$primary_domain}"
            ;;
    esac
fi

if [ -z "$health_host" ]; then
    echo "Unable to determine healthcheck host" >&2
    exit 1
fi

exec curl -fsS -H "Host: $health_host" http://localhost:8000/_health/