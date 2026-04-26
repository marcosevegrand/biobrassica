# Biobrassica

Minimal Django deployment for a single VPS.

## Stack

- Three Django web services run the website, shop, and admin from one shared codebase.
- PostgreSQL stores application data.
- Redis backs cache and sessions.
- Nginx proxies each public host to its matching Django service.
- Docker Compose runs the whole stack on one machine.

## Local Development

Prerequisites:

- Docker with Compose support

Setup:

```bash
make stack ENV=dev ACTION=up ARGS='-d'
make django ENV=dev CMD='migrate'
make django ENV=dev CMD='collectstatic --noinput'
make django ENV=dev CMD='compilemessages'
make django ENV=dev CMD='createsuperuser'
```

Local URLs:

- Website: http://lvh.me
- Shop: http://loja.lvh.me
- Admin: http://admin.lvh.me
- Mailpit: http://localhost:8025

Useful commands:

```bash
make stack ENV=dev ACTION=logs
make stack ENV=dev ACTION=logs SERVICE=nginx ARGS='-f --tail=200'
make stack ENV=dev ACTION=ps
make django ENV=dev CMD='shell'
make django ENV=dev CMD='test'
make django ENV=dev CMD='makemessages -l pt -l en -l fr --no-wrap'
make django ENV=dev CMD='compilemessages'
```

The Makefile keeps a deliberately small surface:

- `make stack ...` covers Docker Compose lifecycle work in dev and prod.
- `make redeploy ENV=...` rebuilds and recreates the full Compose stack in one step.
- `make django ...` runs `python manage.py ...` inside the selected Django service.
- `make backup` and `make restore ...` stay explicit because they are production recovery operations.
- `ENV=dev|prod` must always be explicit for `make stack ...` and `make django ...`.

## Validation

Canonical local validation uses `backend/.venv` together with the SQLite test settings in [backend/config/settings/test_sqlite.py](backend/config/settings/test_sqlite.py).

One-time setup:

```bash
python -m venv backend/.venv
backend/.venv/bin/python -m pip install --upgrade pip
backend/.venv/bin/python -m pip install -r backend/requirements-dev.txt
backend/.venv/bin/python -m playwright install chromium
```

If `compilemessages` is not available on your machine, install GNU gettext first.

Run the full local validation workflow:

```bash
cd backend
DJANGO_SETTINGS_MODULE=config.settings.test_sqlite DJANGO_ALLOW_INSECURE_DEFAULTS=1 .venv/bin/python manage.py compilemessages
cd ..
backend/.venv/bin/python -m pyright
cd backend
DJANGO_SETTINGS_MODULE=config.settings.test_sqlite DJANGO_ALLOW_INSECURE_DEFAULTS=1 .venv/bin/python -m pytest -q
```

The full pytest run already includes the Playwright browser suite. For faster UI-only debugging, run just the browser slice:

```bash
cd backend
DJANGO_SETTINGS_MODULE=config.settings.test_sqlite DJANGO_ALLOW_INSECURE_DEFAULTS=1 .venv/bin/python -m pytest tests/browser -q
```

CI uses the same SQLite settings, compiles locale catalogs before tests, installs Playwright Chromium, and runs `pyright` plus the full pytest suite via [/.github/workflows/validate.yml](.github/workflows/validate.yml).

## Production

Production uses [docker-compose.yml](docker-compose.yml) only.

Required setup:

```bash
cp .env.example .env
```

Fill in real secrets before starting the stack. Production Compose commands and the backup/restore scripts use `.env` through Docker Compose.

Payments are deployment-wide. Set `PAYMENT_PROVIDER=stripe` to keep the current hosted Stripe checkout flow, or `PAYMENT_PROVIDER=ifthenpay_mbway` to switch the shop to Ifthenpay MB WAY. Only one provider is active in a given deployment.

Provider-specific production variables:

- `PAYMENT_PROVIDER=stripe`: `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, optional `STRIPE_PUBLISHABLE_KEY`, `STRIPE_CURRENCY`
- `PAYMENT_PROVIDER=ifthenpay_mbway`: `IFTHENPAY_MBWAY_KEY`, `IFTHENPAY_ANTI_PHISHING_KEY`, optional `IFTHENPAY_API_BASE_URL`

When MB WAY is active, checkout requires a customer mobile number, creates the MB WAY payment request at order confirmation time, and keeps the customer on the internal payment-status page while Biobrassica waits for the Ifthenpay callback.

The production web tier is split into three services:

- `django_website` for `marcosevegrand.com` and `www.marcosevegrand.com`
- `django_shop` for `loja.marcosevegrand.com`
- `django_admin` for `admin.marcosevegrand.com`

Bring the stack up with standard Compose commands:

```bash
make stack ENV=prod ACTION=build
make stack ENV=prod ACTION=up ARGS='-d'
```

Or rebuild and recreate every service in one command:

```bash
make redeploy ENV=prod
```

For targeted releases, build and recreate only the site you are changing:

```bash
make stack ENV=prod ACTION=build SERVICE=django_shop
make stack ENV=prod ACTION=up SERVICE=django_shop ARGS='-d'
```

Run release tasks explicitly from one Django service instead of on every container start:

```bash
make django ENV=prod DJANGO_SERVICE=django_website CMD='migrate --noinput'
make django ENV=prod DJANGO_SERVICE=django_website CMD='collectstatic --noinput'
make django ENV=prod DJANGO_SERVICE=django_website CMD='compilemessages'
```

In production, `make django ...` runs as a one-off container from the selected service image, so it still works before the web containers are up.

Before a redeploy that may interrupt checkout, pause payments in one of these ways:

```bash
# Hard-disable from the server environment, then restart the affected Django service(s)
PAYMENTS_FORCE_DISABLED=1
make stack ENV=prod ACTION=up SERVICE=django_shop ARGS='-d'
make stack ENV=prod ACTION=up SERVICE=django_admin ARGS='-d'
```

Or use the admin backoffice and toggle `Pagamentos ativos` in the Website content record. The environment flag wins over the admin toggle and is the safer fallback if the admin host is unavailable.

Production web containers still fail fast on pending migrations, but they no longer run `collectstatic` automatically unless `DJANGO_COLLECTSTATIC_ON_START=1` is set intentionally.

Production nginx now terminates TLS directly for:

- `marcosevegrand.com`
- `www.marcosevegrand.com`
- `loja.marcosevegrand.com`
- `admin.marcosevegrand.com`

The production stack keeps `DJANGO_HTTPS_MODE=proxy` because Django still sits behind nginx and trusts `X-Forwarded-Proto` from the proxy.

Before the first full startup, create the certbot working directories:

```bash
mkdir -p certbot/www certbot/conf
```

Bootstrap the first certificate before starting nginx, using the Certbot utility service profile on port 80:

```bash
docker compose -f docker-compose.yml --profile tools run --rm --service-ports certbot \
	certonly --standalone \
	-d marcosevegrand.com \
	-d www.marcosevegrand.com \
	-d loja.marcosevegrand.com \
	-d admin.marcosevegrand.com \
	--email you@example.com \
	--agree-tos \
	--no-eff-email
```

Once the certificate exists, start the production stack:

```bash
docker compose -f docker-compose.yml up -d
```

To reset the password of an admin/staff account from the VPS without editing the database manually:

```bash
make django ENV=prod DJANGO_SERVICE=django_admin CMD='reset_admin_password admin@example.com'
```

The command asks for the new password twice, validates it with Django's password validators, and refuses non-staff accounts unless `--allow-non-staff` is passed manually.

Renewal uses the shared ACME webroot while nginx is already serving HTTP:

```bash
docker compose -f docker-compose.yml --profile tools run --rm certbot \
	renew --webroot -w /var/www/certbot
docker compose -f docker-compose.yml exec nginx nginx -s reload
```

After rollout, verify nginx, redirects, certificates, and upstream health from the VPS host:

```bash
make verify ENV=prod
```

If you need raw curl checks while debugging a 521, these are still useful:

```bash
curl -I http://marcosevegrand.com
curl -I https://marcosevegrand.com
curl -I https://loja.marcosevegrand.com
curl -I https://admin.marcosevegrand.com
```

Because production enables HSTS for subdomains and preload, every public hostname must be healthy on HTTPS before you expose this configuration to traffic.

## Backup and Restore

Backup database and media:

```bash
./scripts/backup.sh
```

By default, that writes backups into `~/biobrassica/backups` when the deployed repo lives at `~/biobrassica`.

To override the destination explicitly:

```bash
./scripts/backup.sh /path/to/backups
```

Restore database, with optional media restore:

```bash
./scripts/restore.sh --db /path/to/db.sql.gz --yes
./scripts/restore.sh --db /path/to/db.sql.gz --media /path/to/media.tar.gz --yes
```

Or via Make:

```bash
make backup
make restore FILE=/path/to/db.sql.gz YES=1
make restore FILE=/path/to/db.sql.gz MEDIA=/path/to/media.tar.gz YES=1
```

## Notes

- Development uses `.env.dev`, created automatically from `.env.dev.example` when an `ENV=dev` `make stack ...` or `make django ...` command runs.
- Production uses `.env`, created from `.env.example`.
- Translation maintenance is supported through `backend/scripts/fill_translations.py` plus `make django ENV=dev CMD='compilemessages'`.
