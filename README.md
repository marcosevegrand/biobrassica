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
make dev
```

`make dev` builds the development images, starts PostgreSQL, Redis, Django, Tailwind, and Mailpit, applies migrations, and compiles locale catalogs.

If you need to override development-only values such as Stripe credentials, create an optional `.env.dev` file and Docker Compose will pick it up automatically.

Local URLs:

- Website: http://lvh.me:8000
- Shop: http://loja.lvh.me:8000
- Admin: http://admin.lvh.me:8000
- Mailpit: http://localhost:8025

Useful follow-up commands:

```bash
docker compose -p biobrassica-dev -f docker-compose.yml -f docker-compose.dev.yml logs -f django tailwind
docker compose -p biobrassica-dev -f docker-compose.yml -f docker-compose.dev.yml exec django python manage.py createsuperuser
docker compose -p biobrassica-dev -f docker-compose.yml -f docker-compose.dev.yml exec django python manage.py shell
```

The Makefile surface is intentionally small:

- `make dev` starts the local stack.
- `make deploy` performs the production deployment flow.
- `make backup`, `make restore`, `make verify`, and `make cert` cover the operational tasks.
- For rare one-off Docker Compose or `manage.py` work, use the direct `docker compose ...` commands instead of growing the Makefile again.

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
make env
```

Fill in real secrets before starting the stack. Production Compose commands and the backup/restore scripts use `.env` through Docker Compose.

Payments are deployment-wide. Set `PAYMENT_PROVIDER=stripe` to keep the current hosted Stripe checkout flow, or `PAYMENT_PROVIDER=ifthenpay_mbway` to switch the shop to Ifthenpay MB WAY. Only one provider is active in a given deployment.

Provider-specific production variables:

- `PAYMENT_PROVIDER=stripe`: `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, optional `STRIPE_PUBLISHABLE_KEY`, `STRIPE_CURRENCY`
- `PAYMENT_PROVIDER=ifthenpay_mbway`: `IFTHENPAY_MBWAY_KEY`, `IFTHENPAY_ANTI_PHISHING_KEY`, optional `IFTHENPAY_API_BASE_URL`

Production domain routing is env-driven. In the normal case, configure only these in `.env` instead of editing Compose or nginx files:

- `PRIMARY_DOMAIN`: default bare domain family for the deployment
- `DOMAIN_ALIASES`: optional comma-separated bare domains that should also be accepted as mirror families
- `TLS_CERT_NAME`: optional certbot live directory name nginx should read; when empty it falls back to the canonical website host
- `CERTBOT_EMAIL`: email used by `./scripts/request_certificate.sh`

From those values, the stack derives these host families automatically:

- Website: `$PRIMARY_DOMAIN` and `www.$PRIMARY_DOMAIN`
- Shop: `loja.$PRIMARY_DOMAIN`
- Admin: `admin.$PRIMARY_DOMAIN`
- Every domain listed in `DOMAIN_ALIASES` gets the same `www.`, `loja.`, and `admin.` variants added automatically

Public routing follows these rules:

- Bare website hosts are mirrored within their own family, so a user entering through `marcosevegrand.com` stays on the `marcosevegrand.com` family and a user entering through `biobrassica.pt` stays on the `biobrassica.pt` family
- `www.` remains an entry alias only and redirects to the bare website host in the same family
- `loja.` and `admin.` stay within the same family instead of redirecting back to the primary domain family

Explicit `WEBSITE_HOST`, `WEBSITE_ALLOWED_HOSTS`, `SHOP_HOST`, `SHOP_ALLOWED_HOSTS`, `ADMIN_HOST`, and `ADMIN_ALLOWED_HOSTS` overrides still exist, but they are now only for non-standard host layouts.

For example, to use `biobrassica.pt` as the default family while still serving `marcosevegrand.com` as a mirrored family:

```env
PRIMARY_DOMAIN=biobrassica.pt
DOMAIN_ALIASES=marcosevegrand.com
TLS_CERT_NAME=biobrassica.pt
```

When MB WAY is active, checkout requires a customer mobile number, creates the MB WAY payment request at order confirmation time, and keeps the customer on the internal payment-status page while Biobrassica waits for the Ifthenpay callback.

The production web tier is split into three services:

- `django_website` for the canonical website host plus its `www.` alias, and the same pair for every alias domain
- `django_shop` for `loja.` hosts derived from the canonical and alias domains
- `django_admin` for `admin.` hosts derived from the canonical and alias domains

Deploy new production changes with:

```bash
make deploy
```

`make deploy` builds the production images, starts the stateful services, applies migrations, collects static files, recreates the full stack, and runs the production health checks.
It also takes a fresh backup before changing the running production stack.

Before a deploy that may interrupt checkout, pause payments in one of these ways:

```bash
# Hard-disable from the server environment, then deploy
PAYMENTS_FORCE_DISABLED=1 make deploy
```

Or use the admin backoffice and toggle `Pagamentos ativos` in the Website content record. The environment flag wins over the admin toggle and is the safer fallback if the admin host is unavailable.

For rare production `manage.py` commands that are not part of the standard deploy flow, run them directly against the website image:

```bash
docker compose --env-file .env -p biobrassica -f docker-compose.yml run --rm django_website python manage.py reset_admin_password admin@example.com
```

Production web containers still fail fast on pending migrations, but they no longer run `collectstatic` automatically unless `DJANGO_COLLECTSTATIC_ON_START=1` is set intentionally.

Production nginx now terminates TLS directly for every host derived from `PRIMARY_DOMAIN` and `DOMAIN_ALIASES`, unless you intentionally override the host lists. HTTP upgrades stay on the same host, `www.` normalizes to the bare website host inside the same family, and bare website, `loja.`, and `admin.` hosts do not redirect across domain families.

The production stack keeps `DJANGO_HTTPS_MODE=proxy` because Django still sits behind nginx and trusts `X-Forwarded-Proto` from the proxy.

Before the first full startup, create the certbot working directories:

```bash
mkdir -p certbot/www certbot/conf
```

Bootstrap the first certificate before starting nginx. The helper script reads the canonical domain and alias domains from `.env`, expands them into website/shop/admin hostnames, deduplicates them, and requests one certificate bundle for all configured public hosts:

```bash
make cert
```

If nginx is already running, `make cert` uses the ACME webroot and reloads nginx afterwards. If nginx is not running yet, it falls back to standalone validation on port 80. Set `CERTBOT_STAGING=1` in `.env` when you want to hit Let's Encrypt staging during first-run tests.

Once the certificate exists, start the production stack:

```bash
make deploy
```

Renewal uses the shared ACME webroot while nginx is already serving HTTP:

```bash
make cert
```

After rollout, verify nginx, redirects, certificates, and upstream health from the VPS host:

```bash
make verify
```

`make verify` now expects same-host HTTP to HTTPS redirects for bare website, shop, and admin hosts, plus same-family `www.` to bare redirects for website hosts.

If you need raw curl checks while debugging a 521, read the canonical host values straight from `.env` so the commands use the same configured hosts as nginx and Django without shell-sourcing the whole file:

```bash
PRIMARY_DOMAIN=$(sed -n 's/^PRIMARY_DOMAIN=//p' .env | tail -n 1)
WEBSITE_HOST=$(sed -n 's/^WEBSITE_HOST=//p' .env | tail -n 1)
SHOP_HOST=$(sed -n 's/^SHOP_HOST=//p' .env | tail -n 1)
ADMIN_HOST=$(sed -n 's/^ADMIN_HOST=//p' .env | tail -n 1)

WEBSITE_HOST=${WEBSITE_HOST:-$PRIMARY_DOMAIN}
SHOP_HOST=${SHOP_HOST:-loja.$PRIMARY_DOMAIN}
ADMIN_HOST=${ADMIN_HOST:-admin.$PRIMARY_DOMAIN}

curl -I "http://${WEBSITE_HOST}"
curl -I "https://${WEBSITE_HOST}"
curl -I "https://${SHOP_HOST}"
curl -I "https://${ADMIN_HOST}"
```

Because production enables HSTS for subdomains and preload, every public hostname must be healthy on HTTPS before you expose this configuration to traffic.

## Backup and Restore

Backup database and media:

```bash
make backup
```

By default, that writes backups into the repo-local `backups/` directory.

To override the destination explicitly:

```bash
./scripts/backup.sh /path/to/backups
```

Restore the latest backup pair from `backups/`:

```bash
make restore
```

For an explicit database or media archive, use the script directly:

```bash
./scripts/restore.sh --db /path/to/db.sql.gz --yes
./scripts/restore.sh --db /path/to/db.sql.gz --media /path/to/media.tar.gz --yes
```

## Notes

- Development can use an optional `.env.dev` file for local-only overrides.
- Production uses `.env`, created from `.env.example`.
- Translation maintenance is supported through `backend/scripts/fill_translations.py` plus `docker compose ... exec django python manage.py compilemessages` in development.
