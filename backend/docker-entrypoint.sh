#!/bin/sh
set -eu

if [ "${DJANGO_SETTINGS_MODULE:-}" = "config.settings.production" ]; then
    collectstatic_on_start="${DJANGO_COLLECTSTATIC_ON_START:-0}"
    payment_provider="${PAYMENT_PROVIDER:-stripe}"

    case "$payment_provider" in
        stripe)
            payment_vars="STRIPE_SECRET_KEY STRIPE_WEBHOOK_SECRET"
            ;;
        ifthenpay_mbway)
            payment_vars="IFTHENPAY_MBWAY_KEY IFTHENPAY_ANTI_PHISHING_KEY"
            ;;
        *)
            echo "Invalid PAYMENT_PROVIDER: $payment_provider" >&2
            exit 1
            ;;
    esac

    for var in \
        DJANGO_SECRET_KEY \
        DB_PASSWORD \
        EMAIL_HOST \
        EMAIL_HOST_USER \
        EMAIL_HOST_PASSWORD; do
        eval "value=\${$var:-}"
        if [ -z "$value" ]; then
            echo "Missing required environment variable: $var" >&2
            exit 1
        fi
    done

    for var in $payment_vars; do
        eval "value=\${$var:-}"
        if [ -z "$value" ]; then
            echo "Missing required environment variable for $payment_provider: $var" >&2
            exit 1
        fi
    done

    if [ "${1:-}" = "gunicorn" ]; then
        if ! /usr/local/bin/python manage.py migrate --check --noinput; then
            echo "Pending Django migrations detected. Run '/usr/local/bin/python manage.py migrate --noinput' before starting the production web container." >&2
            exit 1
        fi

        if [ "$collectstatic_on_start" = "1" ]; then
            /usr/local/bin/python manage.py collectstatic --noinput
        fi
    fi
fi

exec "$@"