.PHONY: help setup-env setup init up down build restart status logs shell migrate makemigrations createsuperuser collectstatic seed css-build messages compilemessages test lint format typecheck check backup restore prod-build prod-up prod-restart prod-logs prod-shell prod-migrate prod-collectstatic prod-reset-admin-password prod-config stripe-listen

.DEFAULT_GOAL := help

ENV_FILE ?= .env.dev
SERVICE ?= django
LOG_ARGS ?= -f --tail=200
TEST_ARGS ?=
PYTEST_MARKERS ?=
PYTEST_ARGS ?=

COMPOSE_PROD := docker compose -f docker-compose.yml
COMPOSE_DEV := docker compose --env-file $(ENV_FILE) -f docker-compose.yml -f docker-compose.dev.yml
DJANGO_EXEC := $(COMPOSE_DEV) exec django
PROD_SERVICE ?= django_website
PROD_DJANGO_SERVICE ?= django_website
PROD_LOG_ARGS ?= -f --tail=200
PROD_DJANGO_EXEC := $(COMPOSE_PROD) exec $(PROD_DJANGO_SERVICE)

help: ## Show available commands
	@echo ""
	@echo "  Biobrassica"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "  Development URLs"
	@echo "    Website: http://lvh.me"
	@echo "    Shop:    http://loja.lvh.me"
	@echo "    Admin:   http://admin.lvh.me"
	@echo "    Mail:    http://localhost:8025"
	@echo ""
	@echo "  Examples"
	@echo "    make init"
	@echo "    make logs SERVICE=nginx"
	@echo "    make test PYTEST_MARKERS='fast or contract'"
	@echo "    make prod-build PROD_SERVICE=django_shop"
	@echo "    make prod-restart PROD_SERVICE=django_admin"
	@echo ""


.env.dev:
	cp .env.dev.example .env.dev
	@echo "Created .env.dev from .env.dev.example"

setup-env: .env.dev ## Create the development env file if missing

setup: setup-env build up init createsuperuser ## Build the dev stack and bootstrap the database

init: .env.dev ## Initialize the dev stack (migrate, collectstatic, compilemessages)
	$(MAKE) migrate
	$(MAKE) collectstatic
	$(MAKE) compilemessages

up: .env.dev ## Start the development stack
	$(COMPOSE_DEV) up -d

down: .env.dev ## Stop the development stack
	$(COMPOSE_DEV) down

build: .env.dev ## Build development images
	$(COMPOSE_DEV) build

restart: .env.dev ## Restart one service; override with SERVICE=name
	$(COMPOSE_DEV) restart $(SERVICE)

status: .env.dev ## Show running containers
	$(COMPOSE_DEV) ps

logs: .env.dev ## Follow logs; override with SERVICE=name or LOG_ARGS='--tail=50'
	$(COMPOSE_DEV) logs $(LOG_ARGS) $(SERVICE)

shell: .env.dev ## Open a Django shell
	$(DJANGO_EXEC) python manage.py shell

migrate: .env.dev ## Apply database migrations
	$(DJANGO_EXEC) python manage.py migrate

makemigrations: .env.dev ## Create new migrations
	$(DJANGO_EXEC) python manage.py makemigrations

createsuperuser: .env.dev ## Create an admin user
	$(DJANGO_EXEC) python manage.py createsuperuser

collectstatic: .env.dev ## Collect static files
	$(DJANGO_EXEC) python manage.py collectstatic --noinput

seed: .env.dev ## Seed content from markdown
	$(DJANGO_EXEC) python manage.py runscript seed_from_markdown

css-build: .env.dev ## Rebuild Tailwind CSS once
	$(COMPOSE_DEV) run --rm tailwind npx @tailwindcss/cli -i assets/css/input.css -o static/css/output.css

messages: .env.dev ## Extract translatable strings
	$(DJANGO_EXEC) python manage.py makemessages -l pt -l en -l fr --no-wrap

compilemessages: .env.dev ## Compile translation catalogs
	$(DJANGO_EXEC) python manage.py compilemessages

test: .env.dev ## Run manage.py test, or pytest with PYTEST_MARKERS/PYTEST_ARGS
	@if [ -n "$(strip $(PYTEST_MARKERS))" ] || [ -n "$(strip $(PYTEST_ARGS))" ]; then \
		$(DJANGO_EXEC) pytest $(if $(strip $(PYTEST_MARKERS)),-m "$(PYTEST_MARKERS)") $(PYTEST_ARGS); \
	else \
		$(DJANGO_EXEC) python manage.py test $(TEST_ARGS); \
	fi

lint: .env.dev ## Run Ruff
	$(DJANGO_EXEC) ruff check .

format: .env.dev ## Run Ruff formatter
	$(DJANGO_EXEC) ruff format .

typecheck: .env.dev ## Run Pyright
	$(DJANGO_EXEC) pyright

check: .env.dev ## Run Django deployment checks
	$(DJANGO_EXEC) python manage.py check --deploy

backup: ## Backup the production database and media
	./scripts/backup.sh

restore: ## Restore production data; usage: make restore FILE=/path/to/db.sql.gz [MEDIA=/path/to/media.tar.gz] [YES=1]
	@test -n "$(FILE)" || (echo "Usage: make restore FILE=/path/to/db.sql.gz [MEDIA=/path/to/media.tar.gz] [YES=1]" && exit 1)
	./scripts/restore.sh --db "$(FILE)" $(if $(MEDIA),--media "$(MEDIA)") $(if $(filter 1,$(YES)),--yes)

prod-build: ## Build one production service; override with PROD_SERVICE=name
	$(COMPOSE_PROD) build $(PROD_SERVICE)

prod-up: ## Start one production service; override with PROD_SERVICE=name
	$(COMPOSE_PROD) up -d $(PROD_SERVICE)

prod-restart: ## Restart one production service; override with PROD_SERVICE=name
	$(COMPOSE_PROD) restart $(PROD_SERVICE)

prod-logs: ## Follow production logs; override with PROD_SERVICE=name or PROD_LOG_ARGS='--tail=50'
	$(COMPOSE_PROD) logs $(PROD_LOG_ARGS) $(PROD_SERVICE)

prod-shell: ## Open a production Django shell; override with PROD_DJANGO_SERVICE=name
	$(PROD_DJANGO_EXEC) python manage.py shell

prod-migrate: ## Run production migrations; override with PROD_DJANGO_SERVICE=name
	$(PROD_DJANGO_EXEC) python manage.py migrate --noinput

prod-collectstatic: ## Collect production static files explicitly; override with PROD_DJANGO_SERVICE=name
	$(PROD_DJANGO_EXEC) python manage.py collectstatic --noinput

prod-reset-admin-password: ## Reset a production admin password; usage: make prod-reset-admin-password EMAIL=admin@example.com [PROD_DJANGO_SERVICE=django_admin]
	@test -n "$(EMAIL)" || (echo "Usage: make prod-reset-admin-password EMAIL=admin@example.com [PROD_DJANGO_SERVICE=django_admin]" && exit 1)
	$(PROD_DJANGO_EXEC) python manage.py reset_admin_password "$(EMAIL)"

prod-config: ## Print the production Compose config
	$(COMPOSE_PROD) config

stripe-listen: .env.dev ## Forward Stripe test webhooks into local nginx
	$(COMPOSE_DEV) run --rm stripe-cli listen --forward-to http://nginx/api/payments/callback/stripe/ --events checkout.session.completed,checkout.session.async_payment_succeeded,checkout.session.async_payment_failed,checkout.session.expired,payment_intent.payment_failed,charge.refunded
