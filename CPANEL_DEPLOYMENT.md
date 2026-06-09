# Biobrassica — cPanel Git Deployment Guide

This guide matches your real cPanel limitations:

- cPanel username: `biobrassica`
- Only `biobrassica.pt` exists as a real cPanel domain
- Your plan does **not** allow additional domains/subdomains in cPanel
- `loja.biobrassica.pt` and `admin.biobrassica.pt` may exist in **Zone Editor**, but they are DNS-only and are not valid app entry points
- No Terminal access
- Deployment should use **Git™ Version Control** + `.cpanel.yml`

Final URLs:

```text
Website: https://biobrassica.pt
Shop:    https://biobrassica.pt/loja
Admin:   https://biobrassica.pt/admin
Health:  https://biobrassica.pt/_health
```

---

## What the `.cpanel.yml` now automates

The checked-in `.cpanel.yml` automatically does this when you click **Deploy HEAD Commit** in cPanel Git:

1. Uses the app path:

   ```text
   /home/biobrassica/biobrassica
   ```

2. Uses the public path:

   ```text
   /home/biobrassica/public_html
   ```

3. Creates required writable folders.
4. Runs Composer install if cPanel Composer exists.
5. Stops deployment if `vendor/autoload.php` is missing.
6. Stops deployment if `.env` is missing.
7. Copies everything from `public/` to `public_html/`.
8. Overwrites `public_html/index.php`, `.htaccess`, and `.user.ini` with the cPanel bridge files.
9. Runs:

   ```text
   php artisan optimize:clear
   php artisan migrate --force
   php artisan db:seed --force
   php artisan config:cache
   php artisan route:cache
   php artisan view:cache
   ```

This means repeat deployments become:

```text
cPanel → Git™ Version Control → Manage → Update from Remote → Deploy HEAD Commit
```

---

## What cannot be automated by `.cpanel.yml`

These must still be done once in cPanel:

1. Set PHP 8.3 for `biobrassica.pt`.
2. Ensure PHP extension `intl` is enabled.
3. Create the database and database user.
4. Create the `.env` file with secrets.
5. Create/register the cPanel Git repository.

After that, Git deploy handles the normal deployment tasks.

---

## 1. Set PHP 8.3

1. Open cPanel.
2. Go to **Software** → **MultiPHP Manager**.
3. Select `biobrassica.pt`.
4. Set PHP version to **8.3**.
5. Click **Apply**.

Required PHP 8.3 extensions:

```text
intl
pdo_mysql
mbstring
fileinfo
zip
openssl
tokenizer
ctype
xml
dom
```

Important: Filament requires `intl`. Without `intl`, Composer or the admin panel can fail.

If you cannot enable `intl` in cPanel, ask the host:

```text
Please enable the PHP intl extension for PHP 8.3 on my cPanel domain biobrassica.pt. My Laravel/Filament app requires it.
```

---

## 2. Configure PHP INI settings

The repository includes:

```text
public_html/.user.ini
```

The Git deploy copies it to:

```text
/home/biobrassica/public_html/.user.ini
```

It sets:

```ini
display_errors=Off
log_errors=On
expose_php=Off
memory_limit=256M
upload_max_filesize=20M
post_max_size=25M
max_execution_time=120
```

You do not need to manually recreate these values in MultiPHP INI Editor unless your host requires it.

---

## 3. Create or confirm the database

Open cPanel → **Databases** → **Database Wizard**.

Use:

```text
Database name entered: biobrassica
Database user entered: biobrassica
```

cPanel should create:

```text
DB_DATABASE=biobrassica_biobrassica
DB_USERNAME=biobrassica_biobrassica
```

Steps:

1. Create database `biobrassica`.
2. Create user `biobrassica`.
3. Choose a strong password.
4. Save that password.
5. Add the user to the database.
6. Grant **ALL PRIVILEGES**.

If the database already exists, go to **Manage My Databases** and confirm the user has **ALL PRIVILEGES**.

---

## 4. Confirm domain document root

Open cPanel → **Domains**.

Confirm:

```text
Domain:        biobrassica.pt
Document root: /home/biobrassica/public_html
PHP version:   8.3
```

Enable **Force HTTPS Redirect** for `biobrassica.pt` after SSL is active.

Do not create deployment instructions for `loja.biobrassica.pt` or `admin.biobrassica.pt`. Your production paths are:

```text
/loja
/admin
```

---

## 5. Enable hidden files in File Manager

You need this to see/edit `.env`, `.htaccess`, and `.user.ini`.

1. Open cPanel → **Files** → **File Manager**.
2. Click **Settings**.
3. Enable **Show Hidden Files (dotfiles)**.
4. Click **Save**.

---

## 6. Create the cPanel Git repository

Open cPanel → **Files** → **Git™ Version Control**.

### 6.1 Create repository

1. Click **Create**.
2. Enable **Clone a Repository**.
3. In **Clone URL**, enter your remote Git repository URL.
4. In **Repository Path**, enter exactly:

   ```text
   /home/biobrassica/biobrassica
   ```

5. In **Repository Name**, enter:

   ```text
   Biobrassica
   ```

6. Click **Create**.

### 6.2 Important notes

- The repository path must be `/home/biobrassica/biobrassica` because `.cpanel.yml` expects that path.
- Do not clone the repository directly into `/home/biobrassica/public_html`.
- If cPanel says the path is not empty, either empty that folder first or choose **Add Existing Repository** only if it is already the correct Git repository.
- If your remote repository is private, cPanel may require SSH key setup. If that is blocked by your plan, use a public repository or ask the host how private Git repositories are supported in your account.

---

## 7. Create the `.env` file once

The `.env` file is intentionally not committed to Git. You must create it once using File Manager.

Create:

```text
/home/biobrassica/biobrassica/.env
```

Use your local `.env.cpanel` as the source. Fill real values for:

```text
APP_KEY
DB_PASSWORD
MAIL_PASSWORD
ADMIN_PASSWORD
MANUAL_MBWAY_NUMBER
BANK_TRANSFER_IBAN
BANK_TRANSFER_BIC
```

Minimum expected shape:

```env
APP_NAME=Biobrassica
APP_ENV=production
APP_DEBUG=false
APP_URL=https://biobrassica.pt
APP_KEY=base64:YOUR_APP_KEY
APP_TIMEZONE=Europe/Lisbon
APP_LOCALE=pt
APP_FALLBACK_LOCALE=pt
APP_PUBLIC_PATH=/home/biobrassica/public_html

LOG_CHANNEL=stack
LOG_LEVEL=error

DB_CONNECTION=mysql
DB_HOST=localhost
DB_PORT=3306
DB_DATABASE=biobrassica_biobrassica
DB_USERNAME=biobrassica_biobrassica
DB_PASSWORD=YOUR_DATABASE_PASSWORD

CACHE_STORE=database
SESSION_DRIVER=database
SESSION_LIFETIME=120
SESSION_SECURE_COOKIE=true
SESSION_SAME_SITE=lax
QUEUE_CONNECTION=sync
FILESYSTEM_DISK=public
FILAMENT_FILESYSTEM_DISK=public
PUBLIC_DISK_ROOT=/home/biobrassica/public_html/storage

MAIL_MAILER=smtp
MAIL_SCHEME=smtp
MAIL_HOST=mail.biobrassica.pt
MAIL_PORT=587
MAIL_USERNAME=loja@biobrassica.pt
MAIL_PASSWORD=YOUR_EMAIL_PASSWORD
MAIL_FROM_ADDRESS=loja@biobrassica.pt
MAIL_FROM_NAME=Biobrassica

PRIMARY_DOMAIN=biobrassica.pt
SHOP_PATH=loja
ADMIN_PATH=admin

ADMIN_NAME=Biobrassica Admin
ADMIN_EMAIL=admin@biobrassica.pt
ADMIN_PASSWORD=YOUR_ADMIN_PASSWORD
ADMIN_EMAILS=admin@biobrassica.pt

MANUAL_MBWAY_NUMBER=YOUR_MBWAY_NUMBER
BANK_TRANSFER_BENEFICIARY=Biobrassica
BANK_TRANSFER_IBAN=YOUR_IBAN
BANK_TRANSFER_BIC=YOUR_BIC

STAFF_NOTIFICATION_EMAILS=
```

Rules:

- Do not put `.env` in `/home/biobrassica/public_html`.
- Do not commit `.env`.
- Do not add `APP_DEBUG=true`.
- Use `CACHE_STORE`, not `CACHE_DRIVER`.
- Use `MAIL_SCHEME=smtp`, not `MAIL_ENCRYPTION=tls`.

---

## 8. First deployment with Git

After the repository exists and `.env` exists:

1. Open cPanel → **Files** → **Git™ Version Control**.
2. Find repository **Biobrassica**.
3. Click **Manage**.
4. Open **Pull or Deploy**.
5. Click **Update from Remote**.
6. Wait for cPanel to finish pulling.
7. Click **Deploy HEAD Commit**.

The `.cpanel.yml` will then:

- create required folders,
- install Composer dependencies if Composer exists,
- copy public files to `public_html`,
- run migrations,
- seed the admin user,
- cache config/routes/views.

If the deploy fails, read the deployment output in cPanel. The `.cpanel.yml` intentionally stops with clear messages if `.env` or `vendor/autoload.php` is missing.

---

## 9. If Composer is not available on cPanel

The `.cpanel.yml` tries these Composer options:

```text
/opt/cpanel/composer/bin/composer
composer
```

If neither exists, deployment stops unless `vendor/` already exists.

If that happens, use this fallback:

1. On your local computer, run:

   ```bash
   composer install --no-dev --optimize-autoloader
   ```

2. Upload the local `vendor/` folder to:

   ```text
   /home/biobrassica/biobrassica/vendor
   ```

3. Run **Deploy HEAD Commit** again.

You still need `intl` enabled on cPanel. Ignoring `ext-intl` only bypasses Composer checks; it does not make Filament safe to run without `intl`.

---

## 10. Repeat deployments

After the first successful deployment, normal updates are simple:

1. Push your changes to the remote Git repository.
2. Open cPanel → **Git™ Version Control**.
3. Click **Manage** on **Biobrassica**.
4. Click **Update from Remote**.
5. Click **Deploy HEAD Commit**.

No manual File Manager copying should be needed for normal updates.

---

## 11. Test the site

Test in this order.

### 11.1 Health check

```text
https://biobrassica.pt/_health
```

Expected:

```json
{"status":"ok"}
```

### 11.2 Website

```text
https://biobrassica.pt
```

### 11.3 Shop

```text
https://biobrassica.pt/loja
```

Also test:

```text
https://biobrassica.pt/loja/produtos
https://biobrassica.pt/loja/conta/entrar
```

### 11.4 Admin

```text
https://biobrassica.pt/admin
```

Login with:

```text
Email: admin@biobrassica.pt
Password: ADMIN_PASSWORD from .env
```

---

## 12. Troubleshooting

### Deploy button is disabled

cPanel requires:

- `.cpanel.yml` checked in at the repository root,
- at least one branch,
- clean working tree.

Commit and push `.cpanel.yml`, then click **Update from Remote**.

### Composer fails with `ext-intl` missing

Ask the host to enable PHP `intl` for PHP 8.3 on `biobrassica.pt`.

Do not accept a production deployment without `intl`; Filament requires it.

### Deployment stopped: `.env` is missing

Create:

```text
/home/biobrassica/biobrassica/.env
```

Then click **Deploy HEAD Commit** again.

### Deployment stopped: `vendor/autoload.php` is missing

Composer was not available or failed. Either fix Composer/`intl`, or upload `vendor/` manually once.

### 503 Application is not fully installed

Check:

```text
/home/biobrassica/biobrassica/bootstrap/app.php
/home/biobrassica/biobrassica/vendor/autoload.php
/home/biobrassica/public_html/index.php
```

`public_html/index.php` must be the bridge file from this repository's `public_html/index.php`.

### 500 Internal Server Error

Check:

```text
cPanel → Metrics → Errors
/home/biobrassica/biobrassica/storage/logs/laravel.log
```

Common causes:

- wrong database password,
- missing `intl`,
- `.env` typo,
- `storage/` or `bootstrap/cache/` not writable,
- incomplete `vendor/`.

### `/loja` returns 404

Confirm `.env` has:

```env
SHOP_PATH=loja
```

Then deploy again so `route:cache` runs.

### `/admin` does not load

Confirm `.env` has:

```env
ADMIN_PATH=admin
```

Then deploy again so `config:cache` and `route:cache` run.

### Admin says you do not have access

Confirm `.env` has:

```env
ADMIN_EMAIL=admin@biobrassica.pt
ADMIN_EMAILS=admin@biobrassica.pt
```

Then deploy again or run the seed step again through deployment.

### CSS, JS, or images missing

Click **Deploy HEAD Commit** again. The deploy copies:

```text
public/ → /home/biobrassica/public_html
```

and overwrites the bridge files.

### Uploads fail

Confirm this folder exists:

```text
/home/biobrassica/public_html/storage
```

Confirm `.env` has:

```env
FILESYSTEM_DISK=public
FILAMENT_FILESYSTEM_DISK=public
PUBLIC_DISK_ROOT=/home/biobrassica/public_html/storage
```

If it still fails, ask the host whether PHP-FPM requires folder permission `0775` for writable folders.

---

## 13. Do not do these things

Do not:

- clone the Git repository into `/home/biobrassica/public_html`,
- put `.env` in `/home/biobrassica/public_html`,
- rely on `loja.biobrassica.pt` or `admin.biobrassica.pt`,
- run `storage:link`,
- leave `APP_DEBUG=true`,
- commit `.env` or `.env.cpanel`,
- edit files inside cPanel Git repository with File Manager except for `.env`; prefer changing code locally, pushing to Git, then deploying.
