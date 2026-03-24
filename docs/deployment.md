# Deployment Guide

## Production topology

```
Browser ──HTTPS──► Cloudflare (DNS + TLS + CDN)
                       │
                  HTTP (port 80)
                       │
                 Hetzner VM
                 ┌─────────────────────────────────┐
                 │  Docker Compose                  │
                 │                                  │
                 │  nginx ──► Django (gunicorn)     │
                 │              │                   │
                 │            postgres   redis      │
                 └─────────────────────────────────┘
```

- **Cloudflare** terminates TLS and forwards plain HTTP to the VM on port 80.
  Cloudflare sets `X-Forwarded-Proto: https` on every forwarded request.
- **nginx** is HTTP-only (no certs on the VM). It serves static/media files
  directly and proxies everything else to gunicorn on port 8000.
- **Django** trusts `X-Forwarded-Proto` because `DJANGO_HTTPS_MODE=proxy`
  sets `SECURE_PROXY_SSL_HEADER`. All secure-cookie and HTTPS-redirect logic
  depends on this header being present and trustworthy.
- **PostgreSQL** and **Redis** are local Docker services on the same compose
  network. Neither is exposed on a host port in production.

## Cloudflare requirements

1. **Proxy mode**: DNS records for `biobrassica.pt`, `www.biobrassica.pt`,
   `loja.biobrassica.pt`, and `admin.biobrassica.pt` must use the orange-cloud
   (proxied) setting. Without this, TLS terminates at the VM and
   `X-Forwarded-Proto` is never set.

2. **SSL/TLS mode**: Set to **Full** (not Full Strict). There is no certificate
   on the VM — the upstream connection from Cloudflare to nginx is plain HTTP.

3. The VM's firewall must allow inbound TCP on port 80 from Cloudflare IP ranges
   only. Block port 80 from the public internet to prevent bypassing Cloudflare.
   See https://www.cloudflare.com/ips/ for the current ranges.

4. If Cloudflare's "Always Use HTTPS" is enabled, browser-to-Cloudflare
   redirects are handled there. Django's `SECURE_SSL_REDIRECT=True` is a
   defense-in-depth backstop for requests that reach the app without the header.

## Compose files

- `docker-compose.yml` — production stack (only this file is used on the VM)
- `docker-compose.dev.yml` — development-only overrides; never used in production

Production always uses the base file explicitly:

```sh
docker compose -f docker-compose.yml build
docker compose -f docker-compose.yml up -d --remove-orphans
```

Do NOT run plain `docker compose up` on the VM — it picks up
`docker-compose.override.yml` if one exists and can load dev behavior.

Development uses both files:

```sh
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

## Environment variables

Copy `.env.example` to `.env` and fill in real values before the first deploy:

```sh
cp .env.example .env
$EDITOR .env
```

Docker Compose reads `.env` automatically when no `--env-file` is specified.

### Required variables

| Variable | Purpose |
|---|---|
| `DJANGO_SECRET_KEY` | Cryptographic key — generate with `openssl rand -hex 50` |
| `DJANGO_HTTPS_MODE` | Must be `proxy` (Cloudflare terminates TLS) |
| `DB_PASSWORD` | PostgreSQL password |
| `EMAIL_HOST` | SMTP hostname (e.g. `smtp-relay.brevo.com`) |
| `EMAIL_HOST_USER` | SMTP username |
| `EMAIL_HOST_PASSWORD` | SMTP password |
| `IFTHENPAY_BACKOFFICE_KEY` | ifthenpay back-office key |
| `IFTHENPAY_MBWAY_KEY` | ifthenpay MB WAY key |
| `IFTHENPAY_MB_ENTITY` | Multibanco entity |
| `IFTHENPAY_MB_SUBENTITY` | Multibanco sub-entity |
| `IFTHENPAY_CCARD_KEY` | ifthenpay credit card key |
| `IFTHENPAY_ANTI_PHISHING_KEY` | ifthenpay anti-phishing key |

### Optional variables (defaults shown)

| Variable | Default | Purpose |
|---|---|---|
| `DJANGO_LOG_LEVEL` | `INFO` | Django log verbosity (`DEBUG`/`INFO`/`WARNING`/`ERROR`) |
| `ALLOWED_HOSTS` | all four production domains | Override only if adding new hostnames |
| `DB_NAME` | `biobrassica` | PostgreSQL database name |
| `DB_USER` | `biobrassica` | PostgreSQL user |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection URL |
| `IFTHENPAY_CALLBACK_URL` | `https://loja.biobrassica.pt/api/payments/callback/` | Payment callback URL |
| `EMAIL_PORT` | `587` | SMTP port (587 = STARTTLS) |
| `STAFF_NOTIFICATION_EMAILS` | _(empty)_ | Comma-separated notification recipients |

## TLS and proxy contract

- nginx is HTTP-only; TLS is handled entirely by Cloudflare.
- Cloudflare MUST forward `X-Forwarded-Proto: https` to the VM.
- nginx passes this header unchanged to Django via `proxy_set_header X-Forwarded-Proto $http_x_forwarded_proto`.
- Django's `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')` makes `request.is_secure()` return `True`.
- `USE_X_FORWARDED_HOST = True` ensures Django builds correct absolute URLs using the original `Host` header.
- Unknown hostnames are rejected by nginx's `default_server` before reaching Django.

## First deploy checklist

```sh
# 1. Clone repo and create env file
git clone <repo> /opt/biobrassica
cd /opt/biobrassica
cp .env.example .env && $EDITOR .env   # fill in all required variables

# 2. Build images
docker compose -f docker-compose.yml build

# 3. Start services (entrypoint runs migrate + collectstatic + compilemessages)
docker compose -f docker-compose.yml up -d

# 4. Verify all containers are healthy
docker compose -f docker-compose.yml ps

# 5. Run Django deployment checks — must report zero issues
docker compose -f docker-compose.yml exec -T django python manage.py check --deploy

# 6. Create initial superuser
docker compose -f docker-compose.yml exec django python manage.py createsuperuser

# 7. Verify health endpoints
curl -s https://biobrassica.pt/_health/
curl -s https://loja.biobrassica.pt/_health/
curl -s https://admin.biobrassica.pt/_health/
```

## Subsequent deployments

```sh
cd /opt/biobrassica
git pull
docker compose -f docker-compose.yml build
docker compose -f docker-compose.yml up -d --remove-orphans
```

The entrypoint automatically runs `migrate`, `collectstatic`, and
`compilemessages` each time the Django container starts, so no extra steps
are needed for routine releases.

## Health checks

All three subdomains expose `/_health/` (GET, no auth). The endpoint runs
`SELECT 1` against PostgreSQL and returns `{"status": "ok"}` on success or
`{"status": "error", ...}` with HTTP 500 on failure.

Docker uses this endpoint to decide when the Django container is healthy before
nginx begins routing traffic to it.

## Static and media files

Static assets are collected into the `static_files` Docker volume at container
startup and served directly by nginx from `/var/www/static/`. Production uses
`ManifestStaticFilesStorage`, which appends a content hash to each filename.
This makes `Cache-Control: public, immutable` safe — browsers cache forever
and are forced to the new URL when the file changes.

Media uploads (product images, category images, etc.) are stored in the
`media_files` Docker volume and served by nginx from `/var/www/media/`.

Neither volume is mounted as a host-path bind mount in production, so files
survive container restarts but are lost if the volume is deleted. Include both
volumes in your backup strategy.

## Backups

A backup script is provided at [scripts/backup.sh](../scripts/backup.sh).
It dumps the database and archives the media volume, then prunes files older
than 14 days.

```sh
# One-off
./scripts/backup.sh /opt/biobrassica/backups

# Add to cron on the VM (daily at 03:00)
0 3 * * * /opt/biobrassica/scripts/backup.sh /opt/biobrassica/backups >> /var/log/biobrassica-backup.log 2>&1
```

For durable off-site storage, pipe the backup files from `/opt/biobrassica/backups/`
to Hetzner Object Storage, Backblaze B2, or restic. Rehearse restores regularly.

### Manual database restore

```sh
gunzip -c /opt/biobrassica/backups/db_YYYYMMDD_HHMMSS.sql.gz | \
    docker compose -f docker-compose.yml exec -T db psql -U biobrassica biobrassica
```

### Manual media restore

```sh
docker run --rm \
    -v biobrassica_media_files:/data \
    -v /opt/biobrassica/backups:/backup:ro \
    alpine sh -c "cd /data && tar xzf /backup/media_YYYYMMDD_HHMMSS.tar.gz"
```

## Payments

- Order creation and payment initiation are separate steps.
- `Multibanco` and `MB WAY` first move the order into `payment_pending`.
- The final confirmation page is only reachable after the payment is marked `paid`.
- Guest order/payment pages are protected by per-order access tokens.
- ifthenpay callbacks are validated against:
  - anti-phishing key
  - payment lookup
  - amount match when provided
  - Multibanco entity/reference match when provided
