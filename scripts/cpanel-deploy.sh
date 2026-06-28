#!/bin/sh

set -u

echo "== Biobrassica cPanel deployment started =="

APPPATH="${APPPATH:-$(pwd)}"
PUBLICPATH="${PUBLICPATH:-$HOME/public_html}"
SOURCEPATH="${SOURCEPATH:-$(pwd)}"

DEPLOY_WARNINGS=0

log() {
    echo "$1"

    if [ -n "${LOGFILE:-}" ]; then
        echo "$1" >> "$LOGFILE"
    fi
}

warn() {
    DEPLOY_WARNINGS=1
    log "WARNING: $1"
}

write_status() {
    message="$1"

    if [ -n "${STATUSFILE:-}" ]; then
        echo "$message" > "$STATUSFILE" 2>/dev/null || true
    fi
}

finish() {
    if [ "$DEPLOY_WARNINGS" -eq 0 ]; then
        write_status "Biobrassica deployment completed successfully at $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
    else
        write_status "Biobrassica deployment completed with warnings at $(date -u '+%Y-%m-%d %H:%M:%S UTC'). Check storage/logs/cpanel-deploy.log."
    fi

    log "== Biobrassica cPanel deployment completed =="
    exit 0
}

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
write_status "Biobrassica deployment started at $(date -u '+%Y-%m-%d %H:%M:%S UTC')"

{
    echo ""
    echo "== $(date -u '+%Y-%m-%d %H:%M:%S UTC') =="
    echo "SOURCEPATH=$SOURCEPATH"
    echo "APPPATH=$APPPATH"
    echo "PUBLICPATH=$PUBLICPATH"
} >> "$LOGFILE"

if [ -d "$APPPATH/public" ]; then
    log "Copying public assets"
    if command -v rsync >/dev/null 2>&1; then
        rsync -a --exclude='storage' "$APPPATH/public/." "$PUBLICPATH/" >> "$LOGFILE" 2>&1 || warn "public asset rsync failed"
    else
        (cd "$APPPATH/public" && tar --exclude='./storage' -cf - .) | (cd "$PUBLICPATH" && tar -xf -) >> "$LOGFILE" 2>&1 || warn "public asset copy failed"
    fi
else
    warn "public directory not found at $APPPATH/public"
fi

if [ -f "$APPPATH/public_html/index.php" ]; then
    cp "$APPPATH/public_html/index.php" "$PUBLICPATH/index.php" >> "$LOGFILE" 2>&1 || warn "could not copy public_html/index.php"
else
    warn "public_html/index.php not found in repository"
fi

if [ -f "$APPPATH/public_html/.htaccess" ]; then
    cp "$APPPATH/public_html/.htaccess" "$PUBLICPATH/.htaccess" >> "$LOGFILE" 2>&1 || warn "could not copy public_html/.htaccess"
else
    warn "public_html/.htaccess not found in repository"
fi

if [ -f "$APPPATH/public_html/.user.ini" ]; then
    cp "$APPPATH/public_html/.user.ini" "$PUBLICPATH/.user.ini" >> "$LOGFILE" 2>&1 || warn "could not copy public_html/.user.ini"
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
    warn "Could not find a PHP binary. Public files were copied, but migrations/cache were skipped."
    finish
fi

log "Using PHP: $PHP_BIN"
"$PHP_BIN" -v >> "$LOGFILE" 2>&1 || warn "PHP binary exists but php -v failed"

if [ ! -f "$APPPATH/artisan" ]; then
    warn "artisan not found in $APPPATH. Public files were copied, but migrations/cache were skipped."
    finish
fi

if [ ! -f "$APPPATH/vendor/autoload.php" ]; then
    if command -v composer >/dev/null 2>&1; then
        log "vendor/autoload.php missing; running composer install"
        composer install --no-dev --no-interaction --prefer-dist --optimize-autoloader --no-scripts >> "$LOGFILE" 2>&1 || warn "composer install failed"
        if [ -f "$APPPATH/vendor/autoload.php" ]; then
            "$PHP_BIN" artisan package:discover --ansi >> "$LOGFILE" 2>&1 || warn "package discovery failed"
        fi
    else
        warn "vendor/autoload.php missing and composer is not available. Public files were copied, but Laravel cannot boot until dependencies are installed."
        finish
    fi
fi

run_artisan() {
    label="$1"
    shift

    log "Running: php artisan $*"
    if "$PHP_BIN" artisan "$@" >> "$LOGFILE" 2>&1; then
        log "OK: $label"
        return 0
    fi

    warn "$label failed. Check $LOGFILE in cPanel File Manager."
    return 0
}

run_artisan "optimize clear" optimize:clear
run_artisan "migrations" migrate --force
run_artisan "admin user seed" db:seed --class=Database\\Seeders\\AdminUserSeeder --force

run_artisan "config cache" config:cache
run_artisan "route cache" route:cache
run_artisan "view cache" view:cache

finish
