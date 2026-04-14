# Biobrassica

Minimal Django deployment for a single VPS.

## Stack

- Django serves the website, shop, and admin.
- PostgreSQL stores application data.
- Redis backs cache and sessions.
- Nginx proxies the public hosts to Django.
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

Bring the stack up with standard Compose commands:

```bash
docker compose -f docker-compose.yml build
docker compose -f docker-compose.yml up -d
```

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
