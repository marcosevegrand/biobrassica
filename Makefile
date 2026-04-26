.PHONY: help stack redeploy django backup restore verify

.DEFAULT_GOAL := help

ENV ?=
ENV_FILE ?= .env.dev
ACTION ?= ps
SERVICE ?=
DJANGO_SERVICE ?=
ARGS ?=
CMD ?=
FILE ?=
MEDIA ?=
YES ?=

ifeq ($(ENV),prod)
COMPOSE := docker compose -f docker-compose.yml
DEFAULT_DJANGO_SERVICE := django_website
DJANGO_COMMAND = $(COMPOSE) run --rm $(DJANGO_SERVICE) python manage.py $(CMD)
else ifeq ($(ENV),dev)
COMPOSE := docker compose --env-file $(ENV_FILE) -f docker-compose.yml -f docker-compose.dev.yml
DEFAULT_DJANGO_SERVICE := django
DJANGO_COMMAND = $(COMPOSE) exec $(DJANGO_SERVICE) python manage.py $(CMD)
endif

DJANGO_SERVICE := $(if $(strip $(DJANGO_SERVICE)),$(DJANGO_SERVICE),$(DEFAULT_DJANGO_SERVICE))

define require_env
	@test -n "$(strip $(ENV))" || (echo "Usage: make $(1) ENV=dev|prod $(2)" && exit 1)
	@case "$(ENV)" in dev|prod) ;; *) echo "ENV must be dev or prod"; exit 1 ;; esac
endef

define ensure_dev_env
	@if [ "$(ENV)" = "dev" ] && [ ! -f "$(ENV_FILE)" ]; then \
		cp .env.dev.example "$(ENV_FILE)"; \
		echo "Created $(ENV_FILE) from .env.dev.example"; \
	fi
endef

help: ## Show the minimal command surface
	@printf "\n"
	@printf "  Biobrassica\n\n"
	@printf "  Targets\n"
	@printf "    \033[36mhelp\033[0m     Show this help\n"
	@printf "    \033[36mstack\033[0m    Docker Compose lifecycle via explicit ENV=dev|prod\n"
	@printf "    \033[36mredeploy\033[0m Rebuild and recreate the full Compose stack\n"
	@printf "    \033[36mdjango\033[0m   Run python manage.py CMD=... via explicit ENV=dev|prod\n"
	@printf "    \033[36mbackup\033[0m   Backup the production database and media\n"
	@printf "    \033[36mrestore\033[0m  Restore production data from FILE=... with optional MEDIA=...\n"
	@printf "    \033[36mverify\033[0m   Verify the production nginx ingress and Django upstreams\n"
	@printf "\n"
	@printf "  ENV options\n"
	@printf "    dev      docker-compose.yml + docker-compose.dev.yml with .env.dev\n"
	@printf "    prod     docker-compose.yml only\n"
	@printf "\n"
	@printf "  ACTION options for stack\n"
	@printf "    up down build restart logs ps config\n"
	@printf "\n"
	@printf "  DJANGO_SERVICE options\n"
	@printf "    dev:  django\n"
	@printf "    prod: django_website django_shop django_admin\n"
	@printf "\n"
	@printf "  CMD options for django\n"
	@printf "    Any manage.py command works. Common values:\n"
	@printf "    migrate --noinput\n"
	@printf "    collectstatic --noinput\n"
	@printf "    compilemessages\n"
	@printf "    createsuperuser\n"
	@printf "    shell\n"
	@printf "    check --deploy\n"
	@printf "    reset_admin_password <email>\n"
	@printf "\n"
	@printf "  Optional args\n"
	@printf "    SERVICE=...    target one Compose service for stack\n"
	@printf "    ARGS='...'     pass extra Compose flags to stack\n"
	@printf "    FILE=...       database backup path for restore\n"
	@printf "    MEDIA=...      media archive path for restore\n"
	@printf "    YES=1          skip restore confirmation\n"
	@printf "\n"

stack: ## Run a Compose action via ACTION=... [SERVICE=...] [ARGS='...'] [ENV=dev|prod]
	$(call require_env,stack,ACTION=up|down|build|restart|logs|ps|config [SERVICE=name] [ARGS='...'])
	@case "$(ACTION)" in \
		up|down|build|restart|logs|ps|config) ;; \
		*) echo "Usage: make stack ENV=dev|prod ACTION=up|down|build|restart|logs|ps|config [SERVICE=name] [ARGS='...']"; exit 1 ;; \
	esac
	$(call ensure_dev_env)
	$(COMPOSE) $(ACTION) $(ARGS) $(SERVICE)

redeploy: ## Rebuild and recreate the full Compose stack [ENV=dev|prod] [ARGS='...']
	$(call require_env,redeploy,[ARGS='...'])
	$(call ensure_dev_env)
	$(COMPOSE) up --build -d --force-recreate --remove-orphans $(ARGS)

django: ## Run python manage.py CMD=... [ENV=dev|prod] [DJANGO_SERVICE=name]
	$(call require_env,django,CMD='migrate --noinput' [DJANGO_SERVICE=name])
	@test -n "$(strip $(CMD))" || (echo "Usage: make django ENV=dev|prod CMD='migrate --noinput' [DJANGO_SERVICE=name]" && exit 1)
	$(call ensure_dev_env)
	$(DJANGO_COMMAND)

backup: ## Backup the production database and media
	./scripts/backup.sh

verify: ## Verify the production stack from the VPS host
	$(call require_env,verify,)
	@if [ "$(ENV)" != "prod" ]; then echo "verify is only supported with ENV=prod"; exit 1; fi
	./scripts/verify_stack.sh

restore: ## Restore production data; usage: make restore FILE=/path/to/db.sql.gz [MEDIA=/path/to/media.tar.gz] [YES=1]
	@test -n "$(FILE)" || (echo "Usage: make restore FILE=/path/to/db.sql.gz [MEDIA=/path/to/media.tar.gz] [YES=1]" && exit 1)
	./scripts/restore.sh --db "$(FILE)" $(if $(MEDIA),--media "$(MEDIA)") $(if $(filter 1,$(YES)),--yes)