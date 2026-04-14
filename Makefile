.PHONY: help up down logs shell migrate makemigrations createsuperuser test test-fast test-integration test-contracts test-browser-smoke test-security test-all lint format typecheck build restart seed collectstatic css-build status messages compilemessages check backup restore open prod-config coverage stripe-listen

.DEFAULT_GOAL := help

COMPOSE_PROD := docker compose -f docker-compose.yml
COMPOSE_DEV := test -f .env.dev || cp .env.dev.example .env.dev && docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml

# ──────────────────────────────────────────────
# 🥬 Biobrassica – Development Commands
# ──────────────────────────────────────────────

help: ## Show this help message
	@echo ""
	@echo "  🥬 Biobrassica – available commands"
	@echo "  ──────────────────────────────────────"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "  URLs (development):"
	@echo "    Website:  http://lvh.me"
	@echo "    Shop:     http://loja.lvh.me"
	@echo "    Admin:    http://admin.lvh.me"
	@echo "    Mail:     http://localhost:8025"
	@echo ""

# ── Docker ────────────────────────────────────

up: ## Start all services
	$(COMPOSE_DEV) up -d

down: ## Stop all services
	$(COMPOSE_DEV) down

restart: ## Restart Django server
	$(COMPOSE_DEV) restart django

build: ## Rebuild Docker images
	$(COMPOSE_DEV) build

status: ## Show running containers
	$(COMPOSE_DEV) ps

prod-config: ## Resolve production Docker Compose config
	$(COMPOSE_PROD) config

# ── Logs ──────────────────────────────────────

logs: ## Follow Django logs
	$(COMPOSE_DEV) logs -f django

logs-all: ## Follow all service logs
	$(COMPOSE_DEV) logs -f

logs-nginx: ## Follow nginx logs
	$(COMPOSE_DEV) logs -f nginx

logs-tailwind: ## Follow Tailwind watcher logs
	$(COMPOSE_DEV) logs -f tailwind

# ── Django ────────────────────────────────────

shell: ## Open Django shell
	$(COMPOSE_DEV) exec django python manage.py shell

dbshell: ## Open database shell
	$(COMPOSE_DEV) exec django python manage.py dbshell

migrate: ## Run database migrations
	$(COMPOSE_DEV) exec django python manage.py migrate

makemigrations: ## Create new migrations
	$(COMPOSE_DEV) exec django python manage.py makemigrations

createsuperuser: ## Create admin superuser
	$(COMPOSE_DEV) exec django python manage.py createsuperuser

collectstatic: ## Collect static files (for production)
	$(COMPOSE_DEV) exec django python manage.py collectstatic --noinput

seed: ## Seed database from markdown files
	$(COMPOSE_DEV) exec django python manage.py runscript seed_from_markdown

css-build: ## Force rebuild Tailwind CSS
	$(COMPOSE_DEV) run --rm tailwind npx @tailwindcss/cli -i /app/static/css/input.css -o /app/static/css/output.css

# ── i18n ──────────────────────────────────────

messages: ## Extract translatable strings
	$(COMPOSE_DEV) exec django python manage.py makemessages -l pt -l en -l fr --no-wrap

compilemessages: ## Compile .po → .mo translation files
	$(COMPOSE_DEV) exec django python manage.py compilemessages

# ── Quality ───────────────────────────────────

test: ## Run test suite
	$(COMPOSE_DEV) exec django python manage.py test

test-fast: ## Run fast pytest suites (unit/service/model/form/queryset/contracts)
	$(COMPOSE_DEV) exec django pytest -m "fast or contract"

test-integration: ## Run Django integration pytest suites
	$(COMPOSE_DEV) exec django pytest -m "integration and not browser"

test-contracts: ## Run contract pytest suites
	$(COMPOSE_DEV) exec django pytest -m contract

test-browser-smoke: ## Run browser smoke suite
	$(COMPOSE_DEV) exec django pytest -m browser

test-security: ## Run security smoke pytest suites
	$(COMPOSE_DEV) exec django pytest -m security

test-all: ## Run fast, integration, and contract pytest suites
	$(COMPOSE_DEV) exec django pytest -m "fast or integration or contract"

lint: ## Run linter (ruff)
	$(COMPOSE_DEV) exec django ruff check .

format: ## Auto-format code (ruff)
	$(COMPOSE_DEV) exec django ruff format .

typecheck: ## Run type checker (pyright)
	$(COMPOSE_DEV) exec django pyright

coverage: ## Run tests with coverage report
	$(COMPOSE_DEV) exec django coverage run --source=apps manage.py test
	$(COMPOSE_DEV) exec django coverage report

stripe-listen: ## Forward Stripe test-mode webhooks into local nginx
	$(COMPOSE_DEV) run --rm stripe-cli listen --forward-to http://nginx/api/payments/callback/stripe/ --events checkout.session.completed,checkout.session.async_payment_succeeded,checkout.session.async_payment_failed,checkout.session.expired,payment_intent.payment_failed,charge.refunded

check: ## Run Django deployment checks
	$(COMPOSE_DEV) exec django python manage.py check --deploy

# ── Database ──────────────────────────────────

backup: ## Backup database to .sql.gz
	@$(COMPOSE_DEV) exec -T db pg_dump -U biobrassica biobrassica | gzip > backup_$$(date +%Y%m%d_%H%M%S).sql.gz
	@echo "  ✅ Backup created: backup_$$(date +%Y%m%d_%H%M%S).sql.gz"

restore: ## Restore database from backup (usage: make restore FILE=backup.sql.gz)
	@test -n "$(FILE)" || (echo "  ❌ Usage: make restore FILE=backup.sql.gz" && exit 1)
	@gunzip -c $(FILE) | $(COMPOSE_DEV) exec -T db psql -U biobrassica biobrassica
	@echo "  ✅ Database restored from $(FILE)"

# ── Utilities ─────────────────────────────────

open: ## Open website in browser
	xdg-open http://lvh.me 2>/dev/null || open http://lvh.me 2>/dev/null || echo "Open http://lvh.me"

# ── First-time setup ─────────────────────────

setup: build up migrate createsuperuser ## Full first-time setup
	@echo ""
	@echo "  ✅ Setup complete!"
	@echo "  ──────────────────────────────────────"
	@echo "  Website:  http://lvh.me"
	@echo "  Shop:     http://loja.lvh.me"
	@echo "  Admin:    http://admin.lvh.me"
	@echo "  Mail:     http://localhost:8025"
	@echo ""
