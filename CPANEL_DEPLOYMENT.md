# Biobrassica — cPanel Deployment Guide

This guide is written for the actual cPanel account available to you:

- cPanel username: `biobrassica`
- Main domain available in **Domains**: `biobrassica.pt`
- No additional domains/subdomains allowed by the hosting plan
- `loja.biobrassica.pt` and `admin.biobrassica.pt` may exist in **Zone Editor**, but they are DNS-only and are **not** valid app entry points for this plan
- No Terminal access
- Deployment must use cPanel tools such as **File Manager**, **Database Wizard**, **phpMyAdmin**, **MultiPHP Manager**, **MultiPHP INI Editor**, **Cron Jobs**, **Errors**, and **Backup Wizard**

Final production URLs:

```text
Website: https://biobrassica.pt
Shop:    https://biobrassica.pt/loja
Admin:   https://biobrassica.pt/admin
Health:  https://biobrassica.pt/_health
```

Do not deploy this project expecting these URLs to work:

```text
https://loja.biobrassica.pt
https://admin.biobrassica.pt
```

Those names can resolve in DNS, but your plan does not create separate Apache/cPanel virtual hosts for them.

---

## 0. Local preparation before uploading

Do this on your local computer, before creating the ZIP you upload to cPanel.

### 0.1 Install production Composer dependencies

From the project folder on your computer, run:

```bash
composer install --no-dev --optimize-autoloader
```

The upload must include the `vendor/` folder. The cPanel account has no Terminal, so do not depend on running Composer on the server.

### 0.2 Confirm these files/folders exist locally

Before zipping, the project folder should include at least:

```text
app/
artisan
bootstrap/
composer.json
composer.lock
config/
database/
public/
public_html/
resources/
routes/
storage/
vendor/
.env.cpanel
```

Notes:

- `.env.cpanel` is intentionally ignored by Git, but it exists locally and contains the production environment template for this cPanel deployment.
- Do not commit `.env.cpanel`.
- Do not place `.env.cpanel` or `.env` in `/home/biobrassica/public_html`.

### 0.3 Create the ZIP

Create a ZIP containing the **contents of the project folder**, not a parent folder.

When extracted on cPanel, this should be true:

```text
/home/biobrassica/biobrassica/artisan
```

Not this:

```text
/home/biobrassica/biobrassica/some-extra-folder/artisan
```

---

## 1. Back up the cPanel account

Before changing files or database tables:

1. Open cPanel.
2. Go to **Files** → **Backup Wizard** or **Backup**.
3. Download a full backup if available.
4. If a full backup is not available, at least back up:
   - `/home/biobrassica/public_html`
   - the current database from **phpMyAdmin** using **Export**

Do not skip this if the site already has production data.

---

## 2. Set PHP 8.3 for the main domain

Only `biobrassica.pt` appears in your **Domains** / **MultiPHP Manager** area, so only configure that domain.

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

You cannot enable all extensions yourself from this cPanel interface. If one is missing, ask the hosting provider to enable it for PHP 8.3. `intl` is especially important because Filament requires it.

---

## 3. PHP basic settings

The repository includes this file:

```text
public_html/.user.ini
```

It is copied into:

```text
/home/biobrassica/public_html/.user.ini
```

It sets safe production values such as:

```ini
display_errors=Off
log_errors=On
memory_limit=256M
upload_max_filesize=20M
post_max_size=25M
max_execution_time=120
```

You may also view these settings in **Software** → **MultiPHP INI Editor**, but you do not need to manually create them there if `.user.ini` is uploaded correctly.

---

## 4. Database setup

Use cPanel → **Databases** → **Database Wizard** / **MySQL Database Wizard**.

Create or confirm these values:

```text
Database name entered: biobrassica
Database user entered: biobrassica
Final DB_DATABASE:     biobrassica_biobrassica
Final DB_USERNAME:     biobrassica_biobrassica
```

Steps:

1. Open **Database Wizard**.
2. Create database name `biobrassica`.
3. Create user name `biobrassica`.
4. Choose a strong database password.
5. Save the password somewhere secure.
6. Assign the user to the database.
7. Grant **ALL PRIVILEGES**.

If the database or user already exists, do not recreate it. Instead, confirm in **Manage My Databases** that user `biobrassica_biobrassica` has **ALL PRIVILEGES** on database `biobrassica_biobrassica`.

---

## 5. Domain setup

In cPanel → **Domains**, the only required domain is:

```text
Domain:        biobrassica.pt
Document root: /home/biobrassica/public_html
PHP version:   8.3
```

Enable **Force HTTPS Redirect** for `biobrassica.pt` after SSL is active.

Do not create deployment steps for `loja.biobrassica.pt` or `admin.biobrassica.pt`, because your plan does not allow them as real cPanel domains. The app uses paths instead:

```text
/loja
/admin
```

Zone Editor records for `loja` and `admin` are not required for this deployment. You can leave existing DNS records alone, but they are not the production app URLs.

---

## 6. Enable hidden files in File Manager

This is required because `.htaccess`, `.user.ini`, `.env`, and `.env.cpanel` are dotfiles.

1. Open cPanel → **Files** → **File Manager**.
2. Click **Settings** in the top-right corner.
3. Enable **Show Hidden Files (dotfiles)**.
4. Click **Save**.

---

## 7. Upload the private Laravel app

The private app folder is:

```text
/home/biobrassica/biobrassica
```

Steps:

1. Open **File Manager**.
2. Go to:

   ```text
   /home/biobrassica
   ```

3. Create a folder named:

   ```text
   biobrassica
   ```

4. Open:

   ```text
   /home/biobrassica/biobrassica
   ```

5. Upload your project ZIP.
6. Select the ZIP.
7. Click **Extract**.
8. Confirm that `artisan` is directly here:

   ```text
   /home/biobrassica/biobrassica/artisan
   ```

9. Confirm that `vendor/autoload.php` exists:

   ```text
   /home/biobrassica/biobrassica/vendor/autoload.php
   ```

10. Delete the uploaded ZIP after extraction to save disk space.

Final private app folder should include:

```text
/home/biobrassica/biobrassica/app
/home/biobrassica/biobrassica/artisan
/home/biobrassica/biobrassica/bootstrap
/home/biobrassica/biobrassica/config
/home/biobrassica/biobrassica/database
/home/biobrassica/biobrassica/public
/home/biobrassica/biobrassica/public_html
/home/biobrassica/biobrassica/resources
/home/biobrassica/biobrassica/routes
/home/biobrassica/biobrassica/storage
/home/biobrassica/biobrassica/vendor
```

---

## 8. Prepare the public web root

The public web root is:

```text
/home/biobrassica/public_html
```

Only public files should be there. The Laravel app code must stay outside it.

### 8.1 Back up or clear old public files

In File Manager, open:

```text
/home/biobrassica/public_html
```

If this folder contains an old failed deployment, either:

- rename it temporarily, for example to `public_html_old_backup`, or
- delete old files after confirming you have a backup.

If a `.well-known` folder exists, you may leave it. It is often used for SSL validation.

### 8.2 Copy Laravel public assets

Copy **all contents inside** this folder:

```text
/home/biobrassica/biobrassica/public
```

into:

```text
/home/biobrassica/public_html
```

This copies assets such as:

```text
css/
js/
images/
fonts/
media/
videos/
favicon.ico
robots.txt
Filament assets
```

### 8.3 Overwrite with cPanel bridge files

Now copy these three files from:

```text
/home/biobrassica/biobrassica/public_html
```

into:

```text
/home/biobrassica/public_html
```

Overwrite if prompted:

```text
index.php
.htaccess
.user.ini
```

This overwrite is intentional.

Why:

- `public/index.php` is Laravel's normal front controller.
- `public_html/index.php` is the cPanel bridge that loads the app from `/home/biobrassica/biobrassica`.
- `public_html/.htaccess` contains the correct rewrite/security rules for this cPanel deployment.
- `public_html/.user.ini` contains PHP production settings.

### 8.4 Create upload folder

Create this folder manually:

```text
/home/biobrassica/public_html/storage
```

The app is configured to store public uploads directly there. This avoids relying on Laravel's `storage:link`, because shared cPanel often blocks symlinks.

---

## 9. Create the production `.env`

The real Laravel environment file must be here:

```text
/home/biobrassica/biobrassica/.env
```

Recommended method:

1. In File Manager, open:

   ```text
   /home/biobrassica/biobrassica
   ```

2. If `.env.cpanel` exists there, copy it to `.env`.
3. If `.env.cpanel` does not exist there, create a new file named `.env` and paste the values from your local `.env.cpanel` file.
4. Edit `.env`.
5. Set your real database password.
6. Set a strong admin password.
7. Save the file.

Required production values:

```env
APP_NAME=Biobrassica
APP_ENV=production
APP_DEBUG=false
APP_URL=https://biobrassica.pt
APP_KEY=base64:YOUR_EXISTING_APP_KEY
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

Important:

- Do not add `APP_DEBUG=true` anywhere.
- Do not use `CACHE_DRIVER`; Laravel 11 uses `CACHE_STORE`.
- Do not use `MAIL_ENCRYPTION`; this app uses `MAIL_SCHEME=smtp`.
- Do not put `.env` inside `/home/biobrassica/public_html`.

---

## 10. Permissions

Set these folders to **0755** using File Manager → Permissions:

```text
/home/biobrassica/biobrassica/storage
/home/biobrassica/biobrassica/bootstrap/cache
/home/biobrassica/public_html/storage
```

If Laravel cannot write logs/cache/uploads after deployment, ask the hosting provider which writable permission is required for PHP-FPM on your account. Some shared hosts require **0775**.

Avoid **0777** unless your host specifically instructs it.

---

## 11. Find the PHP 8.3 CLI path for Cron Jobs

Cron commands need the PHP CLI binary path.

### 11.1 Set Cron Email first

1. Open cPanel → **Advanced** → **Cron Jobs**.
2. At the top, find **Cron Email**.
3. Enter your email address.
4. Click **Update Email**.

This lets you receive command output.

### 11.2 Test common PHP paths

Add a temporary Cron Job, once per minute, with this command:

```bash
/opt/cpanel/ea-php83/root/usr/bin/php -v
```

Wait one minute and check the email output.

If it reports PHP 8.3, use this path:

```text
/opt/cpanel/ea-php83/root/usr/bin/php
```

If it fails, delete that cron and try:

```bash
/usr/local/bin/php -v
```

Use whichever path reports PHP 8.3.

The remaining guide assumes:

```text
/opt/cpanel/ea-php83/root/usr/bin/php
```

If your host uses another path, replace it in every command below.

---

## 12. Run Laravel commands through Cron Jobs

Because there is no Terminal, each Artisan command must be run as a temporary Cron Job.

For each command below:

1. Open cPanel → **Advanced** → **Cron Jobs**.
2. Choose **Once Per Minute**.
3. Paste exactly one command.
4. Click **Add New Cron Job**.
5. Wait one minute.
6. Check the email output.
7. Delete that Cron Job.
8. Continue to the next command.

Do not leave these one-time commands running permanently.

### 12.1 Clear existing Laravel caches

Run this first so Laravel reads the fresh `.env`:

```bash
/opt/cpanel/ea-php83/root/usr/bin/php /home/biobrassica/biobrassica/artisan optimize:clear
```

Expected result includes messages like caches cleared successfully.

### 12.2 Run database migrations

```bash
/opt/cpanel/ea-php83/root/usr/bin/php /home/biobrassica/biobrassica/artisan migrate --force
```

This creates/updates the database tables.

If this fails, do not continue. Fix the database error first.

### 12.3 Create or update the admin user

```bash
/opt/cpanel/ea-php83/root/usr/bin/php /home/biobrassica/biobrassica/artisan db:seed --force
```

This creates/updates the user from:

```env
ADMIN_EMAIL=admin@biobrassica.pt
ADMIN_PASSWORD=...
```

### 12.4 Cache config

```bash
/opt/cpanel/ea-php83/root/usr/bin/php /home/biobrassica/biobrassica/artisan config:cache
```

### 12.5 Cache routes

```bash
/opt/cpanel/ea-php83/root/usr/bin/php /home/biobrassica/biobrassica/artisan route:cache
```

### 12.6 Cache views

```bash
/opt/cpanel/ea-php83/root/usr/bin/php /home/biobrassica/biobrassica/artisan view:cache
```

Do not run `storage:link`. This deployment uses:

```env
PUBLIC_DISK_ROOT=/home/biobrassica/public_html/storage
```

---

## 13. Test the deployment

Test in this order.

### 13.1 Health check

Open:

```text
https://biobrassica.pt/_health
```

Expected:

```json
{"status":"ok"}
```

If this fails, check:

```text
cPanel → Metrics → Errors
/home/biobrassica/biobrassica/storage/logs/laravel.log
```

### 13.2 Website

Open:

```text
https://biobrassica.pt
```

### 13.3 Shop

Open:

```text
https://biobrassica.pt/loja
```

Also test:

```text
https://biobrassica.pt/loja/produtos
https://biobrassica.pt/loja/conta/entrar
```

### 13.4 Admin

Open:

```text
https://biobrassica.pt/admin
```

Login with:

```text
Email: admin@biobrassica.pt
Password: the ADMIN_PASSWORD from .env
```

---

## 14. After deployment

After everything works:

1. Confirm `.env` still has:

   ```env
   APP_DEBUG=false
   ```

2. Delete all temporary Cron Jobs used for deployment.
3. Keep backups of:
   - `/home/biobrassica/biobrassica/.env`
   - database export from phpMyAdmin
   - uploaded project ZIP on your local computer, not necessarily on cPanel
4. In the admin panel, update website content and shop settings.

---

## 15. Troubleshooting

### 15.1 `503 Application is not fully installed`

The bridge file cannot find Laravel.

Check that these exist:

```text
/home/biobrassica/biobrassica/bootstrap/app.php
/home/biobrassica/biobrassica/vendor/autoload.php
```

Also confirm that `/home/biobrassica/public_html/index.php` is the cPanel bridge file from:

```text
/home/biobrassica/biobrassica/public_html/index.php
```

### 15.2 `500 Internal Server Error`

Check:

```text
cPanel → Metrics → Errors
/home/biobrassica/biobrassica/storage/logs/laravel.log
```

Common causes:

- Wrong database password.
- Missing PHP extension, especially `intl`.
- `.env` syntax typo.
- `storage` or `bootstrap/cache` not writable.
- `vendor/` missing or incomplete.

### 15.3 `/loja` returns 404

Check that route cache was rebuilt:

```bash
/opt/cpanel/ea-php83/root/usr/bin/php /home/biobrassica/biobrassica/artisan route:cache
```

Also confirm `SHOP_PATH=loja` exists in `.env`.

### 15.4 `/admin` does not load

Confirm:

```env
ADMIN_PATH=admin
```

Then rerun:

```bash
/opt/cpanel/ea-php83/root/usr/bin/php /home/biobrassica/biobrassica/artisan optimize:clear
/opt/cpanel/ea-php83/root/usr/bin/php /home/biobrassica/biobrassica/artisan config:cache
/opt/cpanel/ea-php83/root/usr/bin/php /home/biobrassica/biobrassica/artisan route:cache
```

### 15.5 Admin says you do not have access

Make sure the admin user's email is listed in `.env`:

```env
ADMIN_EMAILS=admin@biobrassica.pt
```

Then rerun the seed command:

```bash
/opt/cpanel/ea-php83/root/usr/bin/php /home/biobrassica/biobrassica/artisan db:seed --force
```

### 15.6 CSS, JS, or images are missing

Re-copy everything from:

```text
/home/biobrassica/biobrassica/public
```

to:

```text
/home/biobrassica/public_html
```

Then re-copy these bridge files:

```text
/home/biobrassica/biobrassica/public_html/index.php
/home/biobrassica/biobrassica/public_html/.htaccess
/home/biobrassica/biobrassica/public_html/.user.ini
```

to:

```text
/home/biobrassica/public_html
```

### 15.7 File uploads fail

Confirm this folder exists and is writable:

```text
/home/biobrassica/public_html/storage
```

Confirm `.env` has:

```env
FILESYSTEM_DISK=public
FILAMENT_FILESYSTEM_DISK=public
PUBLIC_DISK_ROOT=/home/biobrassica/public_html/storage
```

Then clear/cache config again.

---

## 16. What not to do

Do not:

- Put the full Laravel app inside `/home/biobrassica/public_html`.
- Put `.env` inside `/home/biobrassica/public_html`.
- Depend on `loja.biobrassica.pt` or `admin.biobrassica.pt`.
- Run `storage:link` for this deployment.
- Leave one-time Cron Jobs active.
- Enable `APP_DEBUG=true` in production.
