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
- `make django ...` runs `python manage.py ...` inside the selected Django service.
- `make backup` and `make restore ...` stay explicit because they are production recovery operations.
- `ENV=dev|prod` must always be explicit for `make stack ...` and `make django ...`.

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
make stack ENV=prod ACTION=build
make stack ENV=prod ACTION=up ARGS='-d'
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
