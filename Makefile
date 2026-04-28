.PHONY: help env dev deploy backup restore reset verify cert createsuperuser

.DEFAULT_GOAL := help

help:
	@printf "\nBiobrassica\n\n"
	@printf "  make env              Create .env from .env.example if it does not exist\n"
	@printf "  make dev              Start the local development stack\n"
	@printf "  make deploy           Backup, build, migrate, collect static files, restart, and verify production\n"
	@printf "  make backup           Backup the production database and media into backups/\n"
	@printf "  make restore          Restore production data from the latest backup in backups/\n"
	@printf "  make reset            Hard-reset the production DB, redeploy, and optionally restore BACKUP=/path/to/db.sql.gz\n"
	@printf "  make verify           Verify the production stack is running and healthy\n"
	@printf "  make cert             Request or renew production TLS certificates\n"
	@printf "  make createsuperuser  Interactively create a Django/admin superuser in production\n\n"
	@printf "Advanced restore options remain available via ./scripts/restore.sh --help\n\n"

env:
	@if [ -f .env ]; then \
		echo ".env already exists; leaving it unchanged"; \
	else \
		cp .env.example .env; \
		chmod 600 .env 2>/dev/null || true; \
		echo "Created .env from .env.example"; \
	fi

dev:
	./scripts/dev.sh

deploy:
	./scripts/deploy.sh

backup:
	./scripts/backup.sh

restore:
	./scripts/restore.sh

reset:
	./scripts/reset.sh $(if $(BACKUP),--db "$(BACKUP)") $(if $(YES),--yes)

verify:
	./scripts/verify_stack.sh

cert:
	./scripts/request_certificate.sh

createsuperuser:
	./scripts/createsuperuser.sh