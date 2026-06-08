# cPanel deployment guide (PHP 8.3, no terminal)

This Laravel app is prepared for your cPanel account `biobrassica`, where the app code lives outside the web root and only public files live in `public_html`.

## 1. cPanel settings

- **MultiPHP Manager:** select PHP **8.3** for `biobrassica.pt`, `loja.biobrassica.pt`, and `admin.biobrassica.pt`.
- Required PHP extensions: `intl`, `pdo_mysql`, `mbstring`, `fileinfo`, `zip`, `openssl`, `tokenizer`, `ctype`, `xml`, `dom`. If one is missing, ask the hosting provider to enable it for PHP 8.3.
- **Domains:** point all three domains/subdomains to the same document root: `/home/biobrassica/public_html`.
- **Domains → Force HTTPS Redirect:** enable it after SSL is issued.
- **Database Wizard:** create a MySQL/MariaDB database and user, then grant **ALL PRIVILEGES**.
- Do not use **Software Application Manager/Passenger** for this PHP app; use Apache + MultiPHP.

## 2. Upload the files with File Manager

Recommended layout:

```text
/home/biobrassica/biobrassica      # Laravel app, not public
/home/biobrassica/public_html      # public web root
```

Upload the Laravel app to `/home/biobrassica/biobrassica`, including `vendor/`. If your host cannot run Composer for you, build/upload the `vendor/` directory from your local machine.

Then put public files in `public_html`:

1. Copy/extract everything from the app's `public/` folder into `public_html`.
2. Overwrite `public_html/index.php`, `.htaccess`, and `.user.ini` with the versions from this repository's `public_html/` folder.
3. Do **not** place `.env`, `vendor/`, `storage/`, or the full app directly inside `public_html`.

## 3. Create `.env`

Copy `.env.example` to `.env` in `/home/biobrassica/biobrassica` and fill in:

- `APP_KEY` (generate locally with `php artisan key:generate --show`, or ask the host to run it once)
- `APP_PUBLIC_PATH=/home/biobrassica/public_html`
- `PUBLIC_DISK_ROOT=/home/biobrassica/public_html/storage`
- `DB_DATABASE`, `DB_USERNAME`, `DB_PASSWORD`
- cPanel email SMTP values
- `ADMIN_EMAIL`, `ADMIN_PASSWORD`, and `ADMIN_EMAILS`

Keep `APP_ENV=production` and `APP_DEBUG=false`.

## 4. Run one-time Artisan commands with cPanel Cron Jobs

If you have no terminal, use **Cron Jobs** to run each command once, then delete it after it succeeds. Use the PHP 8.3 binary shown by your host; common paths are `/usr/local/bin/php` or `/opt/cpanel/ea-php83/root/usr/bin/php`.

```bash
/opt/cpanel/ea-php83/root/usr/bin/php /home/biobrassica/biobrassica/artisan key:generate --force
/opt/cpanel/ea-php83/root/usr/bin/php /home/biobrassica/biobrassica/artisan migrate --force
/opt/cpanel/ea-php83/root/usr/bin/php /home/biobrassica/biobrassica/artisan db:seed --force
/opt/cpanel/ea-php83/root/usr/bin/php /home/biobrassica/biobrassica/artisan optimize:clear
/opt/cpanel/ea-php83/root/usr/bin/php /home/biobrassica/biobrassica/artisan config:cache
/opt/cpanel/ea-php83/root/usr/bin/php /home/biobrassica/biobrassica/artisan route:cache
/opt/cpanel/ea-php83/root/usr/bin/php /home/biobrassica/biobrassica/artisan view:cache
```

## 5. Verify

- Visit `https://biobrassica.pt/_health` — it should return `{"status":"ok"}`.
- Visit `https://biobrassica.pt`.
- Visit `https://admin.biobrassica.pt/admin` and log in with `ADMIN_EMAIL` / `ADMIN_PASSWORD`.
- If you see HTTP 500, check **Metrics → Errors** and `biobrassica/storage/logs/laravel.log` in File Manager.

## Optional: cPanel Git Version Control

This repository includes `.cpanel.yml` to copy public assets into `public_html`. It does not install Composer dependencies. If deploying with cPanel Git, you still need `vendor/` and `.env` in `/home/biobrassica/biobrassica`.
