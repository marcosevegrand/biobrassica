# Deployment Guide

## Production topology

```
Browser ──HTTPS──► Cloudflare (DNS + TLS + CDN)
                       │
                  HTTP (port 80)
                       │
        OVHcloud VPS
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
| `STRIPE_SECRET_KEY` | Stripe secret API key |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret |

### Optional variables (defaults shown)

| Variable | Default | Purpose |
|---|---|---|
| `DJANGO_LOG_LEVEL` | `INFO` | Django log verbosity (`DEBUG`/`INFO`/`WARNING`/`ERROR`) |
| `ALLOWED_HOSTS` | all four production domains | Override only if adding new hostnames |
| `SHOP_BASE_URL` | `https://loja.biobrassica.pt` | Canonical shop base URL used in cross-site links |
| `DB_NAME` | `biobrassica` | PostgreSQL database name |
| `DB_USER` | `biobrassica` | PostgreSQL user |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection URL |
| `STRIPE_CURRENCY` | `eur` | Stripe currency for Checkout Sessions |
| `STRIPE_PUBLISHABLE_KEY` | _(empty)_ | Optional, only needed if you later add Stripe.js on the frontend |
| `EMAIL_PORT` | `587` | SMTP port (587 = STARTTLS) |
| `STAFF_NOTIFICATION_EMAILS` | _(empty)_ | Comma-separated notification recipients |

## TLS and proxy contract

- nginx is HTTP-only; TLS is handled entirely by Cloudflare.
- Cloudflare MUST forward `X-Forwarded-Proto: https` to the VM.
- nginx sets `proxy_set_header X-Forwarded-Proto https` itself; clients do not get to supply this header.
- Django's `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')` makes `request.is_secure()` return `True`.
- `USE_X_FORWARDED_HOST = True` ensures Django builds correct absolute URLs using the original `Host` header.
- `SECURE_REDIRECT_EXEMPT = [r'^_health/$']` keeps Docker health checks working without a spoofed HTTPS header.
- Unknown hostnames are rejected by nginx's `default_server` before reaching Django.

## Domain changes

When adding or changing public domains:

1. Update `ALLOWED_HOSTS` in the production environment.
2. Update the matching nginx `server_name` entries.
3. Reload or restart nginx after the compose deploy.
4. Verify `CSRF_TRUSTED_ORIGINS` implicitly covers the new hosts through `ALLOWED_HOSTS`.

## First deploy checklist

```sh
# 1. Clone repo and create env file
git clone <repo> /opt/biobrassica
cd /opt/biobrassica
cp .env.example .env && $EDITOR .env

# 2. Build images
docker compose -f docker-compose.yml build

# 3. Apply database migrations explicitly
docker compose -f docker-compose.yml run --rm django python manage.py migrate --noinput

# 4. Start services (entrypoint runs collectstatic + compilemessages)
docker compose -f docker-compose.yml up -d

# 5. Verify all containers are healthy
docker compose -f docker-compose.yml ps

# 6. Run Django deployment checks — must report zero issues
docker compose -f docker-compose.yml exec -T django python manage.py check --deploy

# 7. Create initial superuser
docker compose -f docker-compose.yml exec django python manage.py createsuperuser

# 8. Verify health endpoints
curl -s https://biobrassica.pt/_health/
curl -s https://loja.biobrassica.pt/_health/
curl -s https://admin.biobrassica.pt/_health/
```

## Exact OVHcloud VPS deploy sequence

Run this on a fresh OVHcloud Ubuntu VPS.

```sh
sudo apt-get update
sudo apt-get install -y ca-certificates curl git docker.io docker-compose-plugin
sudo systemctl enable --now docker

sudo mkdir -p /opt
cd /opt
sudo git clone <your-repo-url> biobrassica
sudo chown -R $USER:$USER /opt/biobrassica

cd /opt/biobrassica
cp .env.example .env
$EDITOR .env

docker compose -f docker-compose.yml config
docker compose -f docker-compose.yml build
docker compose -f docker-compose.yml run --rm django python manage.py migrate --noinput
docker compose -f docker-compose.yml up -d --remove-orphans

docker compose -f docker-compose.yml ps
docker compose -f docker-compose.yml exec -T django python manage.py check --deploy
docker compose -f docker-compose.yml exec django python manage.py createsuperuser

curl -s -H 'Host: biobrassica.pt' http://127.0.0.1/_health/
curl -s -H 'Host: loja.biobrassica.pt' http://127.0.0.1/_health/
curl -s -H 'Host: admin.biobrassica.pt' http://127.0.0.1/_health/
```

For subsequent releases on the OVH VPS:

```sh
cd /opt/biobrassica
git fetch --prune origin
git checkout --force <validated-commit-sha>
docker compose -f docker-compose.yml build
docker compose -f docker-compose.yml run --rm django python manage.py migrate --noinput
docker compose -f docker-compose.yml up -d --remove-orphans
docker compose -f docker-compose.yml exec -T django python manage.py check --deploy
```

### Startup behavior

Database migrations remain an explicit deploy step:

```sh
docker compose -f docker-compose.yml run --rm django python manage.py migrate --noinput
```

The production web container now fails fast during startup if migrations are
still pending. `collectstatic` and `compilemessages` run on production web
container startup when the entrypoint launches `gunicorn`; they do not run for
arbitrary one-off management commands such as `python manage.py migrate`.

## Subsequent deployments

```sh
cd /opt/biobrassica
git fetch --prune origin
git checkout --force <validated-commit-sha>
docker compose -f docker-compose.yml build
docker compose -f docker-compose.yml run --rm django python manage.py migrate --noinput
docker compose -f docker-compose.yml up -d --remove-orphans
```

Database migrations are an explicit deploy step and should complete
successfully before the new containers are brought up. On production web
startup, the entrypoint fails fast if migrations are pending, then runs
`collectstatic` and `compilemessages` before `gunicorn` starts serving traffic.

If you are deploying from GitHub Actions, use `${GITHUB_SHA}` as the validated
commit SHA on the server instead of pulling `main` directly. That keeps the
deployed revision identical to the one the workflow validated.

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

For a non-destructive smoke check of the backup configuration:

```sh
BACKUP_DRY_RUN=1 ./scripts/backup.sh "$(mktemp -d)"
```

For a restore helper rehearsal or live recovery, use
[scripts/restore.sh](../scripts/restore.sh):

```sh
sh ./scripts/restore.sh \
  --db /opt/biobrassica/backups/db_YYYYMMDD_HHMMSS.sql.gz \
  --media /opt/biobrassica/backups/media_YYYYMMDD_HHMMSS.tar.gz
```

```sh
# One-off
./scripts/backup.sh /opt/biobrassica/backups

# Add to cron on the VM (daily at 03:00)
0 3 * * * /opt/biobrassica/scripts/backup.sh /opt/biobrassica/backups >> /var/log/biobrassica-backup.log 2>&1
```

For durable off-site storage, pipe the backup files from `/opt/biobrassica/backups/`
to OVHcloud Object Storage, Backblaze B2, or restic. Rehearse restores regularly.

## Restore Rehearsal Checklist

Use this non-destructive flow to verify the backup/restore contract without
touching the live database or media volume:

```sh
TMP_DIR="$(mktemp -d)"

# 1. Confirm the backup script wiring.
BACKUP_DRY_RUN=1 ./scripts/backup.sh "$TMP_DIR"

# 2. Create a real backup set.
./scripts/backup.sh "$TMP_DIR"

# 3. Locate the generated archives.
DB_BACKUP="$(find "$TMP_DIR" -maxdepth 1 -name 'db_*.sql.gz' | head -n 1)"
MEDIA_BACKUP="$(find "$TMP_DIR" -maxdepth 1 -name 'media_*.tar.gz' | head -n 1)"

# 4. Verify archive integrity.
gunzip -t "$DB_BACKUP"
tar tzf "$MEDIA_BACKUP" > /dev/null

# 5. Rehearse the restore plan without mutating production.
RESTORE_DRY_RUN=1 sh ./scripts/restore.sh --db "$DB_BACKUP" --media "$MEDIA_BACKUP"
```

Record the exact backup filenames you validated and any issues found during the
rehearsal in the deployment log or incident notes.

## Rollback

Rollback is appropriate when the new revision has been deployed but the stack
fails deployment checks, local host-header health checks, or a critical
production behavior regresses immediately after release.

Identify the previous revision before deployment with:

```sh
cd /opt/biobrassica
git rev-parse HEAD
```

If the new revision is already checked out, recover the prior SHA from the
deploy logs or from the local reflog:

```sh
cd /opt/biobrassica
git reflog --format='%H %gs' -n 5
```

The GitHub Actions deploy job now prints the pre-deploy value as the rollback
candidate before switching to the new commit.

To roll back application code to the previously deployed SHA:

```sh
cd /opt/biobrassica
git checkout --force <previous-sha>
docker compose -f docker-compose.yml build
# Automatic schema reversal is not the default rollback path.
docker compose -f docker-compose.yml up -d --remove-orphans
docker compose -f docker-compose.yml exec -T django python manage.py check --deploy
curl -fsS -H 'Host: biobrassica.pt' http://127.0.0.1/_health/ > /dev/null
curl -fsS -H 'Host: loja.biobrassica.pt' http://127.0.0.1/_health/ > /dev/null
curl -fsS -H 'Host: admin.biobrassica.pt' http://127.0.0.1/_health/ > /dev/null
```

Do not assume backwards compatibility after schema changes. Evaluate migration
compatibility before starting older application code against a newer database.
If schema rollback is required, rehearse it separately before production use.

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

## Stripe webhook secret

`STRIPE_WEBHOOK_SECRET` is not a value you invent yourself.

- In production, create the webhook endpoint in Stripe for `/api/payments/callback/stripe/` and copy the signing secret that Stripe shows for that endpoint.
- In local development, run `make stripe-listen` and copy the `whsec_...` secret printed by the Stripe CLI.
- The value must exactly match the endpoint that is sending the webhook requests.
- It normally starts with `whsec_`.
- It does not need any special permissions or custom format beyond being the exact signing secret issued by Stripe.

## Payments

- Order creation and payment initiation are separate steps.
- Stripe Checkout moves the order into `payment_pending` until the webhook confirms payment.
- The final confirmation page is only reachable after the payment is marked `paid`.
- Guest order/payment pages are protected by per-order access tokens.
- Stripe webhooks are validated against the Stripe signing secret before they can update a payment.

### Stripe dashboard setup

- Configure the production webhook endpoint as `https://loja.biobrassica.pt/api/payments/callback/stripe/`.
- Subscribe at minimum to these events:
  - `checkout.session.completed`
  - `checkout.session.async_payment_succeeded`
  - `checkout.session.async_payment_failed`
  - `checkout.session.expired`
  - `payment_intent.payment_failed`
  - `charge.refunded`
- Copy the Stripe webhook signing secret into `STRIPE_WEBHOOK_SECRET` in production.

## OVHcloud backups

OVHcloud VPS backups do not require application code changes.

- Keep OVHcloud snapshots or backup storage enabled for infrastructure recovery.
- Also keep application-level backups for PostgreSQL and media using `scripts/backup.sh`.
- Store the resulting archives outside the live VPS when possible.
