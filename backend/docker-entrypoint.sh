#!/bin/sh
set -eu

if [ "${DJANGO_SETTINGS_MODULE:-}" = "config.settings.production" ]; then
    for var in \
        DJANGO_SECRET_KEY \
        DB_PASSWORD \
        EMAIL_HOST \
        EMAIL_HOST_USER \
        EMAIL_HOST_PASSWORD \
        STRIPE_SECRET_KEY \
        STRIPE_WEBHOOK_SECRET; do
        eval "value=\${$var:-}"
        if [ -z "$value" ]; then
            echo "Missing required environment variable: $var" >&2
            exit 1
        fi
    done

    if [ "${1:-}" = "gunicorn" ]; then
        if ! /usr/local/bin/python manage.py migrate --check --noinput; then
            echo "Pending Django migrations detected. Run '/usr/local/bin/python manage.py migrate --noinput' before starting the production web container." >&2
            exit 1
        fi

        /usr/local/bin/python manage.py collectstatic --noinput
    fi
fi

exec "$@"