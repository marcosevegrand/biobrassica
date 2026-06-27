#!/bin/sh

set -u

echo "== Biobrassica cPanel deployment started =="

APPPATH="${APPPATH:-$(pwd)}"
PUBLICPATH="${PUBLICPATH:-$HOME/public_html}"
SOURCEPATH="${SOURCEPATH:-$(pwd)}"

if [ ! -d "$APPPATH" ]; then
    echo "Application path does not exist; creating: $APPPATH"
    mkdir -p "$APPPATH" || exit 1
fi

case "$PUBLICPATH" in
    "$SOURCEPATH"|"$SOURCEPATH"/*)
        echo "ERROR: PUBLICPATH must not be inside the git checkout; refusing to dirty the repository."
        echo "SOURCEPATH=$SOURCEPATH"
        echo "PUBLICPATH=$PUBLICPATH"
        exit 1
        ;;
esac

if [ "$SOURCEPATH" != "$APPPATH" ]; then
    echo "Syncing repository from $SOURCEPATH to application path $APPPATH"
    if command -v rsync >/dev/null 2>&1; then
        rsync -a --delete \
            --exclude='.git' \
            --exclude='.env' \
            --exclude='vendor' \
            --exclude='storage/app/public' \
            --exclude='storage/logs' \
            "$SOURCEPATH/" "$APPPATH/" || exit 1
    else
        echo "rsync unavailable; copying files without delete cleanup"
        (cd "$SOURCEPATH" && tar --exclude='./.git' --exclude='./.env' --exclude='./vendor' --exclude='./storage/app/public' --exclude='./storage/logs' -cf - .) | (cd "$APPPATH" && tar -xf -) || exit 1
    fi
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

LOGFILE="$APPPATH/storage/logs/cpanel-deploy.log"
STATUSFILE="$PUBLICPATH/deploy-status.txt"

{
    echo ""
    echo "== $(date -u '+%Y-%m-%d %H:%M:%S UTC') =="
    echo "SOURCEPATH=$SOURCEPATH"
    echo "APPPATH=$APPPATH"
    echo "PUBLICPATH=$PUBLICPATH"
} >> "$LOGFILE"

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

DEPLOY_WARNINGS=0

run_artisan() {
    label="$1"
    shift

    echo "Running: php artisan $*"
    if "$PHP_BIN" artisan "$@" >> "$LOGFILE" 2>&1; then
        echo "OK: $label"
        return 0
    fi

    DEPLOY_WARNINGS=1
    echo "WARNING: $label failed. Check $LOGFILE in cPanel File Manager."
    return 0
}

run_artisan "optimize clear" optimize:clear
run_artisan "migrations" migrate --force
run_artisan "admin user seed" db:seed --class=Database\\Seeders\\AdminUserSeeder --force

run_artisan "config cache" config:cache
run_artisan "route cache" route:cache
run_artisan "view cache" view:cache

if [ "$DEPLOY_WARNINGS" -eq 0 ]; then
    echo "Biobrassica deployment completed successfully at $(date -u '+%Y-%m-%d %H:%M:%S UTC')" > "$STATUSFILE"
else
    echo "Biobrassica deployment completed with warnings at $(date -u '+%Y-%m-%d %H:%M:%S UTC'). Check storage/logs/cpanel-deploy.log." > "$STATUSFILE"
fi

echo "== Biobrassica cPanel deployment completed =="
exit 0
