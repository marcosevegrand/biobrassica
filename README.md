# Biobrassica

Django-based website, shop, and admin for Biobrassica.

## Local development

Development now uses an explicit compose file pair:

```sh
make up
```

The development Makefile bootstraps `.env.dev` from `.env.dev.example` automatically on first use.

That expands to:

```sh
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

Useful commands:

```sh
make build
make migrate
make test
make coverage
make check
make prod-config
```

Development URLs:

- Website: http://lvh.me
- Shop: http://loja.lvh.me
- Admin: http://admin.lvh.me
- Mailpit: http://localhost:8025

## Production deployment

Production assumes TLS terminates upstream of the bundled nginx container.
The checked-in nginx configuration is HTTP-only by design and expects the upstream proxy or load balancer to forward the original scheme via `X-Forwarded-Proto`.

Production must use only the base compose file:

```sh
docker compose -f docker-compose.yml build
docker compose -f docker-compose.yml up -d --remove-orphans
```

Do not use `docker compose up` without `-f docker-compose.yml` on the server.

Detailed operational guidance lives in [docs/deployment.md](docs/deployment.md).

## Documentation

- [Deployment guide](docs/deployment.md)
- [Architecture note](docs/architecture.md)