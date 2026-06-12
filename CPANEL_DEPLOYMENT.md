# Biobrassica — cPanel Git Deployment Guide

This guide is written for the actual hosting plan being used.

## Account assumptions

- cPanel username: `biobrassica`
- Main cPanel domain: `biobrassica.pt`
- Main document root: `/home/biobrassica/public_html`
- Laravel app path: `/home/biobrassica/biobrassica`
- PHP version: PHP 8.3
- No Terminal access
- No extra cPanel domains/subdomains allowed
- Deployment method: **cPanel Git™ Version Control** using `.cpanel.yml`

## Final URLs

Because the hosting plan does not allow real cPanel subdomains, the app uses paths:

```text
Website: https://biobrassica.pt
Shop:    https://biobrassica.pt/loja
Admin:   https://biobrassica.pt/admin
Health:  https://biobrassica.pt/_health
```

Do **not** use these as production app URLs:

```text
https://loja.biobrassica.pt
https://admin.biobrassica.pt
```

Those may exist in **Zone Editor**, but they are DNS-only on this plan. They do not create Apache/cPanel virtual hosts.

---

# 1. What is automated by `.cpanel.yml`

The repository contains a checked-in `.cpanel.yml` file.

When you click **Deploy HEAD Commit** in cPanel Git, it automatically:

1. Uses app path:

   ```text
   /home/biobrassica/biobrassica
   ```

2. Uses public path:

   ```text
   /home/biobrassica/public_html
   ```

3. Creates required folders:

   ```text
   /home/biobrassica/public_html/storage
   /home/biobrassica/biobrassica/bootstrap/cache
   /home/biobrassica/biobrassica/storage/framework/cache/data
   /home/biobrassica/biobrassica/storage/framework/sessions
   /home/biobrassica/biobrassica/storage/framework/views
   /home/biobrassica/biobrassica/storage/logs
   ```

4. Runs Composer install if Composer is available in cPanel.
5. Stops clearly if `vendor/autoload.php` is missing.
6. Stops clearly if `.env` is missing.
7. Copies everything from `public/` to `/home/biobrassica/public_html`.
8. Overwrites these public bridge files:

   ```text
   /home/biobrassica/public_html/index.php
   /home/biobrassica/public_html/.htaccess
   /home/biobrassica/public_html/.user.ini
   ```

9. Runs Laravel deployment commands:

   ```text
   php artisan optimize:clear
   php artisan migrate --force
   php artisan db:seed --force
   php artisan config:cache
   php artisan route:cache
   php artisan view:cache
   ```

After the first setup, normal deployments should be:

```text
Push code to Git → cPanel Git™ Version Control → Update from Remote → Deploy HEAD Commit
```

---

# 2. What is not automated

These must be done once in cPanel:

1. Set PHP 8.3 for `biobrassica.pt`.
2. Ensure PHP extension `intl` is enabled.
3. Create/confirm the MySQL database and user.
4. Create `/home/biobrassica/biobrassica/.env`.
5. Create/register the cPanel Git repository at `/home/biobrassica/biobrassica`.

---

# 3. Set PHP 8.3

1. Open cPanel.
2. Go to **Software** → **MultiPHP Manager**.
3. Select only `biobrassica.pt`.
4. Set PHP version to **8.3**.
5. Click **Apply**.

Required PHP extensions for PHP 8.3:

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

Important: **Filament requires `intl`**. Without it, Composer and/or the admin panel can fail.

If `intl` is not enabled, ask the host:

```text
Please enable the PHP intl extension for PHP 8.3 on my cPanel domain biobrassica.pt. My Laravel/Filament app requires it.
```

---

# 4. Confirm PHP INI settings

The repository includes:

```text
public_html/.user.ini
```

During Git deploy, `.cpanel.yml` copies it to:

```text
/home/biobrassica/public_html/.user.ini
```

It contains safe production settings:

```ini
display_errors=Off
log_errors=On
expose_php=Off
memory_limit=256M
upload_max_filesize=20M
post_max_size=25M
max_execution_time=120
```

You do not need to manually recreate these in **MultiPHP INI Editor** unless the hosting provider asks you to.

---

# 5. Create or confirm the database

Open cPanel → **Databases** → **Database Wizard** or **MySQL Database Wizard**.

Create:

```text
Database name entered: biobrassica
Database user entered: biobrassica
```

cPanel should create these final names:

```text
DB_DATABASE=biobrassica_biobrassica
DB_USERNAME=biobrassica_biobrassica
```

Steps:

1. Create database `biobrassica`.
2. Create user `biobrassica`.
3. Choose a strong database password.
4. Save the password.
5. Add user `biobrassica_biobrassica` to database `biobrassica_biobrassica`.
6. Grant **ALL PRIVILEGES**.

If the database already exists, open **Manage My Databases** and confirm that user `biobrassica_biobrassica` has **ALL PRIVILEGES** on database `biobrassica_biobrassica`.

---

# 6. Confirm the main domain

Open cPanel → **Domains**.

Confirm:

```text
Domain:        biobrassica.pt
Document root: /home/biobrassica/public_html
PHP version:   8.3
```

After SSL is active, enable **Force HTTPS Redirect** for `biobrassica.pt`.

Do not configure deployment around `loja.biobrassica.pt` or `admin.biobrassica.pt`. The app uses:

```text
/loja
/admin
```

---

# 7. Enable hidden files in File Manager

This is necessary to see/edit dotfiles like `.env`, `.htaccess`, and `.user.ini`.

1. Open cPanel → **Files** → **File Manager**.
2. Click **Settings**.
3. Enable **Show Hidden Files (dotfiles)**.
4. Click **Save**.

---

# 8. Create the cPanel Git repository

Open cPanel → **Files** → **Git™ Version Control**.

## 8.1 Create repository

1. Click **Create**.
2. Enable **Clone a Repository**.
3. In **Clone URL**, enter the remote Git repository URL.
4. In **Repository Path**, enter exactly:

   ```text
   /home/biobrassica/biobrassica
   ```

5. In **Repository Name**, enter:

   ```text
   Biobrassica
   ```

6. Click **Create**.

## 8.2 Important repository notes

- The repository path must be `/home/biobrassica/biobrassica`.
- Do not clone into `/home/biobrassica/public_html`.
- Do not manually edit app code in File Manager after cloning; push changes to Git instead.
- If the remote repository is private, cPanel may require SSH key configuration. If your plan blocks that, use a public repository or ask the host how private Git repositories are supported.

---

# 9. Create the `.env` file

The Laravel `.env` is not committed to Git. You must create it once.

Create this file:

```text
/home/biobrassica/biobrassica/.env
```

Use your local `.env.cpanel` as the source. Fill in real secret values.

Minimum required shape:

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
- Do not commit `.env.cpanel`.
- Do not add `APP_DEBUG=true`.
- Use `CACHE_STORE`, not `CACHE_DRIVER`.
- Use `MAIL_SCHEME=smtp`, not `MAIL_ENCRYPTION=tls`.

---

# 10. First Git deployment

After the repository exists and `.env` exists:

1. Open cPanel → **Files** → **Git™ Version Control**.
2. Find repository **Biobrassica**.
3. Click **Manage**.
4. Open **Pull or Deploy**.
5. Click **Update from Remote**.
6. Wait until cPanel finishes pulling.
7. Click **Deploy HEAD Commit**.

During deployment, `.cpanel.yml` will:

- create folders,
- run Composer if available,
- copy public assets,
- publish bridge files,
- migrate the database,
- seed the admin user,
- cache config/routes/views.

If deploy fails, read the output shown by cPanel. The deploy script intentionally stops with clear messages when `.env` or `vendor/autoload.php` is missing.

---

# 11. If Composer is not available in cPanel

The deploy script tries:

```text
/opt/cpanel/composer/bin/composer
composer
```

If neither exists, deploy will continue only if `vendor/autoload.php` already exists.

Fallback:

1. On your local computer, install dependencies:

   ```bash
   composer install --no-dev --optimize-autoloader
   ```

2. Upload your local `vendor/` folder to:

   ```text
   /home/biobrassica/biobrassica/vendor
   ```

3. Click **Deploy HEAD Commit** again.

Important: cPanel still needs PHP `intl` enabled. Ignoring `ext-intl` only bypasses Composer checks; it does not make Filament safe to run without `intl`.

---

# 12. Repeat deployments

After first successful setup, normal updates are:

1. Push code to the remote Git repository.
2. Open cPanel → **Git™ Version Control**.
3. Click **Manage** for **Biobrassica**.
4. Click **Update from Remote**.
5. Click **Deploy HEAD Commit**.

No File Manager copying should be needed for normal deploys.

---

# 13. Test the site

Test in this order.

## 13.1 Health check

```text
https://biobrassica.pt/_health
```

Expected:

```json
{"status":"ok"}
```

## 13.2 Website

```text
https://biobrassica.pt
```

## 13.3 Shop

```text
https://biobrassica.pt/loja
https://biobrassica.pt/loja/produtos
https://biobrassica.pt/loja/conta/entrar
```

## 13.4 Admin

```text
https://biobrassica.pt/admin
```

Login with:

```text
Email: admin@biobrassica.pt
Password: ADMIN_PASSWORD from .env
```

---

# 14. Troubleshooting

## Deploy button is disabled

cPanel requires:

- `.cpanel.yml` checked in at the repository root,
- at least one branch,
- clean working tree.

Commit and push `.cpanel.yml`, then click **Update from Remote**.

If cPanel shows this message:

```text
The system cannot deploy
For deployment, ensure that your repository meets the following requirements:
A valid .cpanel.yml file exists.
No uncommitted changes exist on the checked-out branch.
```

use this checklist:

1. On your local computer, confirm `.cpanel.yml` is committed and pushed:

   ```bash
   git status
   git add .cpanel.yml CPANEL_DEPLOYMENT.md .gitignore .env.example
   git commit -m "Configure cPanel deployment"
   git push
   ```

   If Git says there is nothing to commit, just run `git push`.

2. In cPanel → **Git™ Version Control** → **Manage** → **Basic Information**, confirm the repository path is exactly:

   ```text
   /home/biobrassica/biobrassica
   ```

3. In cPanel → **Git™ Version Control** → **Manage** → **Pull or Deploy**, click:

   ```text
   Update from Remote
   ```

4. If deployment is still disabled, the cPanel checkout probably has uncommitted changes. This commonly happens when `.cpanel.yml`, `.htaccess`, `index.php`, or other tracked files were edited directly in File Manager.

5. Since this cPanel account has no Terminal, the cleanest recovery is to recreate the cPanel clone:

   - In File Manager, download or copy this file somewhere safe:

     ```text
     /home/biobrassica/biobrassica/.env
     ```

   - In cPanel → **Git™ Version Control**, remove/unregister the repository.
   - In File Manager, rename the old folder:

     ```text
     /home/biobrassica/biobrassica
     ```

     to:

     ```text
     /home/biobrassica/biobrassica_old
     ```

   - Recreate the repository in cPanel Git using path:

     ```text
     /home/biobrassica/biobrassica
     ```

   - Put the saved `.env` back into:

     ```text
     /home/biobrassica/biobrassica/.env
     ```

   - Go to **Pull or Deploy** and click **Deploy HEAD Commit**.

Important: do not create or edit `.cpanel.yml` directly in cPanel File Manager. It must be committed to Git and pulled from the remote repository. Editing tracked files directly in cPanel makes the working tree dirty, and cPanel disables deployment.

## Composer fails with `ext-intl` missing

Ask the host to enable PHP `intl` for PHP 8.3 on `biobrassica.pt`.

Do not deploy this app without `intl`; Filament requires it.

## Deployment stopped: `.env` is missing

Create:

```text
/home/biobrassica/biobrassica/.env
```

Then click **Deploy HEAD Commit** again.

## Deployment stopped: `vendor/autoload.php` is missing

Composer was not available or failed. Either fix Composer/`intl`, or upload `vendor/` manually once.

## 503: Application is not fully installed

Check:

```text
/home/biobrassica/biobrassica/bootstrap/app.php
/home/biobrassica/biobrassica/vendor/autoload.php
/home/biobrassica/public_html/index.php
```

`public_html/index.php` must be the bridge file from the repository's `public_html/index.php`.

## 500 Internal Server Error

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

## `/loja` returns 404

Confirm `.env` has:

```env
SHOP_PATH=loja
```

Then run deploy again so route cache is rebuilt.

## `/admin` does not load

Confirm `.env` has:

```env
ADMIN_PATH=admin
```

Then run deploy again so config and route caches are rebuilt.

## Admin says you do not have access

Confirm `.env` has:

```env
ADMIN_EMAIL=admin@biobrassica.pt
ADMIN_EMAILS=admin@biobrassica.pt
```

Then deploy again so `db:seed --force` runs.

## CSS, JS, or images are missing

Click **Deploy HEAD Commit** again. The deploy copies:

```text
public/ → /home/biobrassica/public_html
```

## Uploads fail

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

# 15. Do not do these things

Do not:

- clone the Git repository into `/home/biobrassica/public_html`,
- put `.env` in `/home/biobrassica/public_html`,
- rely on `loja.biobrassica.pt` or `admin.biobrassica.pt`,
- run `storage:link`,
- leave `APP_DEBUG=true`,
- commit `.env` or `.env.cpanel`,
- edit app code in File Manager after Git setup; change code locally, push to Git, then deploy.
