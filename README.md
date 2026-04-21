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
make setup-env
make up
make init
make createsuperuser
```

Local URLs:

- Website: http://lvh.me
- Shop: http://loja.lvh.me
- Admin: http://admin.lvh.me
- Mailpit: http://localhost:8025

Useful commands:

```bash
make init
make logs
make logs SERVICE=nginx
make shell
make test
make test PYTEST_MARKERS='fast or contract'
make lint
make typecheck
make messages
make compilemessages
```

## Production

Production uses [docker-compose.yml](docker-compose.yml) only.

Required setup:

```bash
cp .env.example .env
```

Fill in real secrets before starting the stack. Production Compose commands and the backup/restore scripts use `.env` through Docker Compose.

The production web tier is split into three services:

- `django_website` for `marcosevegrand.com` and `www.marcosevegrand.com`
- `django_shop` for `loja.marcosevegrand.com`
- `django_admin` for `admin.marcosevegrand.com`

Bring the stack up with standard Compose commands:

```bash
docker compose -f docker-compose.yml build
docker compose -f docker-compose.yml up -d
```

For targeted releases, build or restart only the site you are changing:

```bash
make prod-build PROD_SERVICE=django_shop
make prod-restart PROD_SERVICE=django_shop
```

Run release tasks explicitly from one Django service instead of on every container start:

```bash
make prod-migrate
make prod-collectstatic
```

Before a redeploy that may interrupt checkout, pause payments in one of these ways:

```bash
# Hard-disable from the server environment, then restart the affected Django service(s)
PAYMENTS_FORCE_DISABLED=1
make prod-restart PROD_SERVICE=django_shop
make prod-restart PROD_SERVICE=django_admin
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
make prod-reset-admin-password EMAIL=admin@example.com PROD_DJANGO_SERVICE=django_admin
```

The command asks for the new password twice, validates it with Django's password validators, and refuses non-staff accounts unless `--allow-non-staff` is passed manually.

Renewal uses the shared ACME webroot while nginx is already serving HTTP:

```bash
docker compose -f docker-compose.yml --profile tools run --rm certbot \
	renew --webroot -w /var/www/certbot
docker compose -f docker-compose.yml exec nginx nginx -s reload
```

After rollout, verify redirects and certificates:

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
./scripts/backup.sh /path/to/backups
```

Restore database, with optional media restore:

```bash
./scripts/restore.sh --db /path/to/db.sql.gz --yes
./scripts/restore.sh --db /path/to/db.sql.gz --media /path/to/media.tar.gz --yes
```

Or via Make:

```bash
make restore FILE=/path/to/db.sql.gz YES=1
make restore FILE=/path/to/db.sql.gz MEDIA=/path/to/media.tar.gz YES=1
```

## Notes

- Development uses `.env.dev`, created from `.env.dev.example`.
- Production uses `.env`, created from `.env.example`.
- Translation maintenance is supported through `backend/scripts/fill_translations.py` plus `make compilemessages`.
