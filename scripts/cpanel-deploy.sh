#!/bin/sh

set -u

echo "== Biobrassica cPanel deployment started =="

APPPATH="${APPPATH:-$(pwd)}"
PUBLICPATH="${PUBLICPATH:-$HOME/public_html}"

if [ ! -d "$APPPATH" ]; then
    echo "ERROR: Application path does not exist: $APPPATH"
    exit 1
fi

cd "$APPPATH" || exit 1

case "$PUBLICPATH" in
    "$APPPATH"|"$APPPATH"/*)
        echo "ERROR: PUBLICPATH must not be inside the git checkout; refusing to dirty the repository."
        echo "APPPATH=$APPPATH"
        echo "PUBLICPATH=$PUBLICPATH"
        exit 1
        ;;
esac

mkdir -p "$PUBLICPATH" \
    "$PUBLICPATH/storage" \
    "$APPPATH/bootstrap/cache" \
    "$APPPATH/storage/app/public" \
    "$APPPATH/storage/framework/cache/data" \
    "$APPPATH/storage/framework/sessions" \
    "$APPPATH/storage/framework/views" \
    "$APPPATH/storage/logs"

if [ -d "$APPPATH/public" ]; then
    cp -R "$APPPATH/public/." "$PUBLICPATH/"
fi

if [ -f "$APPPATH/public_html/index.php" ]; then
    cp "$APPPATH/public_html/index.php" "$PUBLICPATH/index.php"
fi

if [ -f "$APPPATH/public_html/.htaccess" ]; then
    cp "$APPPATH/public_html/.htaccess" "$PUBLICPATH/.htaccess"
fi

if [ -f "$APPPATH/public_html/.user.ini" ]; then
    cp "$APPPATH/public_html/.user.ini" "$PUBLICPATH/.user.ini"
fi

PHP_BIN="${PHP_BIN:-}"

if [ -z "$PHP_BIN" ]; then
    for candidate in \
        /usr/local/bin/php \
        /opt/cpanel/ea-php83/root/usr/bin/php \
        /opt/cpanel/ea-php82/root/usr/bin/php \
        /usr/bin/php
    do
        if [ -x "$candidate" ]; then
            PHP_BIN="$candidate"
            break
        fi
    done
fi

if [ -z "$PHP_BIN" ] && command -v php >/dev/null 2>&1; then
    PHP_BIN="$(command -v php)"
fi

if [ -z "$PHP_BIN" ]; then
    echo "ERROR: Could not find a PHP binary. Set PHP_BIN in cPanel deployment environment."
    exit 1
fi

echo "Using PHP: $PHP_BIN"
"$PHP_BIN" -v

if [ ! -f "$APPPATH/artisan" ]; then
    echo "ERROR: artisan not found in $APPPATH"
    exit 1
fi

if [ ! -f "$APPPATH/vendor/autoload.php" ]; then
    if command -v composer >/dev/null 2>&1; then
        echo "vendor/autoload.php missing; running composer install"
        composer install --no-dev --no-interaction --prefer-dist --optimize-autoloader --no-scripts || exit 1
        "$PHP_BIN" artisan package:discover --ansi || exit 1
    else
        echo "ERROR: vendor/autoload.php missing and composer is not available."
        exit 1
    fi
fi

"$PHP_BIN" artisan optimize:clear || true
"$PHP_BIN" artisan migrate --force || exit 1
"$PHP_BIN" artisan db:seed --class=Database\\Seeders\\AdminUserSeeder --force || exit 1

"$PHP_BIN" artisan config:cache || echo "WARNING: config:cache failed"
"$PHP_BIN" artisan route:cache || echo "WARNING: route:cache failed"
"$PHP_BIN" artisan view:cache || echo "WARNING: view:cache failed"

echo "== Biobrassica cPanel deployment completed =="
