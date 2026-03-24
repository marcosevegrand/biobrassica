#!/bin/sh
set -eu

if [ "${DJANGO_SETTINGS_MODULE:-}" = "config.settings.production" ]; then
    for var in \
        DJANGO_SECRET_KEY \
        DB_PASSWORD \
        EMAIL_HOST \
        EMAIL_HOST_USER \
        EMAIL_HOST_PASSWORD \
        IFTHENPAY_BACKOFFICE_KEY \
        IFTHENPAY_MBWAY_KEY \
        IFTHENPAY_MB_ENTITY \
        IFTHENPAY_MB_SUBENTITY \
        IFTHENPAY_CCARD_KEY \
        IFTHENPAY_ANTI_PHISHING_KEY; do
        eval "value=\${$var:-}"
        if [ -z "$value" ]; then
            echo "Missing required environment variable: $var" >&2
            exit 1
        fi
    done

    /usr/local/bin/python manage.py migrate --noinput
    /usr/local/bin/python manage.py collectstatic --noinput
    /usr/local/bin/python manage.py compilemessages
fi

exec "$@"