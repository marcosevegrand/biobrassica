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
make stripe-listen
```

Development URLs:

- Website: http://lvh.me
- Shop: http://loja.lvh.me
- Admin: http://admin.lvh.me
- Mailpit: http://localhost:8025

### Stripe test mode in development

Stripe does not have a separate "sandbox" product for this integration. For this app,
you use Stripe test mode with test API keys and a webhook listener.

1. Copy `.env.dev.example` to `.env.dev` if it does not exist.
2. Set `STRIPE_SECRET_KEY` in `.env.dev` to your Stripe test secret key.
3. Start the local stack:

```sh
make up
```

4. In a second terminal, start the webhook forwarder:

```sh
make stripe-listen
```

5. The Stripe CLI prints a webhook signing secret beginning with `whsec_...`.
	Copy that value into `STRIPE_WEBHOOK_SECRET` in `.env.dev`.
6. Restart Django so it picks up the new webhook secret:

```sh
make restart
```

7. Use Stripe test cards during checkout, for example `4242 4242 4242 4242`.

Keep the `make stripe-listen` terminal running while you test payments locally.
If you stop and restart the listener, Stripe may issue a new webhook signing secret,
so update `.env.dev` and restart Django again.

## Production deployment

Production assumes TLS terminates upstream of the bundled nginx container.
The checked-in nginx configuration is HTTP-only by design and expects the upstream proxy or load balancer to forward the original scheme via `X-Forwarded-Proto`.

Production must use only the base compose file:

```sh
docker compose -f docker-compose.yml build
docker compose -f docker-compose.yml up -d --remove-orphans
```

Do not use `docker compose up` without `-f docker-compose.yml` on the server.
Run database migrations explicitly before starting the production web
container. The production entrypoint now fails fast on pending migrations
instead of starting gunicorn against an out-of-date schema.

Detailed operational guidance lives in [docs/deployment.md](docs/deployment.md).

## Documentation

- [Deployment guide](docs/deployment.md)
- [Architecture note](docs/architecture.md)