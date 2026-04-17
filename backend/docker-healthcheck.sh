#!/bin/sh
set -eu

health_host="${HEALTHCHECK_HOST:-${ALLOWED_HOSTS%%,*}}"

if [ -z "$health_host" ]; then
    echo "Unable to determine healthcheck host" >&2
    exit 1
fi

exec curl -fsS -H "Host: $health_host" http://localhost:8000/_health/