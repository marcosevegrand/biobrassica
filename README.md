# Biobrassica

Plataforma de comércio eletrónico para produtos biológicos — website, loja online e painel de administração.

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Backend | Django 6.0 (Python 3.12) |
| Admin UI | Django-Unfold (tema personalizado) |
| Base de dados | PostgreSQL |
| Cache / Sessões | Redis |
| Web server | Gunicorn + Nginx + certbot (TLS) |
| Frontend | Django Templates + HTMX + Tailwind CSS v4 + Alpine.js |
| Infraestrutura | Docker Compose — 3 serviços Django (website, loja, admin) num só VPS |
| Testes | pytest + pytest-django + pytest-xdist + Playwright + coverage |
| Linting | ruff + pyright |
| Conteúdo | Markdown + bleach (HTML sanitizado) |
| Imagens | Pillow |
| Email | Brevo SMTP (Mailpit em dev) |
| Pagamentos | Manuais apenas — MB WAY + Transferência bancária (métodos no backoffice, credenciais no `.env`) |
| i18n | Português (padrão), Inglês, Francês |

## Desenvolvimento Local

Pré-requisitos: Docker com suporte a Compose.

```bash
make dev
```

O `make dev` constrói as imagens de desenvolvimento, inicia PostgreSQL, Redis, Django, Tailwind e Mailpit, aplica migrações e compila traduções.

URLs locais:

- Website: http://lvh.me:8000
- Loja: http://loja.lvh.me:8000
- Admin: http://admin.lvh.me:8000
- Mailpit: http://localhost:8025

Comandos úteis:

```bash
docker compose -p biobrassica-dev -f docker-compose.yml -f docker-compose.dev.yml logs -f django tailwind
docker compose -p biobrassica-dev -f docker-compose.yml -f docker-compose.dev.yml exec django python manage.py createsuperuser
docker compose -p biobrassica-dev -f docker-compose.yml -f docker-compose.dev.yml exec django python manage.py shell
```

Para valores de desenvolvimento (ex.: credenciais de email), cria um ficheiro `.env.dev` opcional.

## Fluxo de Compra

1. **Cliente adiciona produtos ao carrinho** — sem reserva de stock.
2. **Cliente entra no checkout** — o stock é reservado por 30 minutos (configurável em **Configurações**), mas não é criada encomenda nem pagamento.
3. **Cliente confirma o checkout** — a encomenda e o pagamento são criados. Stock já estava reservado.
4. **Cliente paga (MB WAY ou transferência)** — staff confirma manualmente o pagamento no backoffice.
5. **Staff avança a encomenda** — Preparação → Pronta/Em trânsito → Entregue.

**Regras de stock:**

- Encomenda cancelada → stock reposto.
- Pagamento cancelado ≠ encomenda cancelada (ambos são manuais).
- Checkout abandonado ou expirado (30 min) → stock libertado, cliente forçado a recomeçar.
- Pagamento expirado → apenas o pagamento é cancelado. Encomenda mantém-se pendente para o cliente reiniciar.

**Configuração dos timeouts no backoffice** (`Configurações`):

- `payment_timeout_minutes` — tempo máximo para pagar. `0` = sem limite.
- `checkout_reservation_minutes` — tempo que o stock fica reservado durante o checkout. `0` = sem reserva (stock deduzido ao confirmar encomenda, como fallback).

## Comandos Makefile

| Comando | Descrição |
|---------|-----------|
| `make dev` | Inicia o stack de desenvolvimento |
| `make deploy` | Backup, build, migrate, collectstatic, restart e verify em produção |
| `make backup` | Backup da base de dados e media |
| `make restore` | Restaura o backup mais recente |
| `make reset` | Reset completo da DB de produção e redeploy |
| `make verify` | Verifica que o stack de produção está saudável |
| `make cert` | Gere ou renova certificados TLS |
| `make createsuperuser` | Cria superutilizador Django em produção |
| `make cron` | Cancela pagamentos expirados e liberta reservas de stock expiradas |

Para comandos pontuais de `manage.py` em produção:

```bash
docker compose --env-file .env -p biobrassica -f docker-compose.yml run --rm django_website python manage.py <comando>
```

## Validação

Validação local usa `backend/.venv` com SQLite.

Setup único:

```bash
python -m venv backend/.venv
backend/.venv/bin/python -m pip install --upgrade pip
backend/.venv/bin/python -m pip install -r backend/requirements-dev.txt
backend/.venv/bin/python -m playwright install chromium
```

Workflow completo de validação:

```bash
cd backend
DJANGO_SETTINGS_MODULE=config.settings.test_sqlite DJANGO_ALLOW_INSECURE_DEFAULTS=1 .venv/bin/python manage.py compilemessages
cd ..
backend/.venv/bin/python -m pyright
cd backend
DJANGO_SETTINGS_MODULE=config.settings.test_sqlite DJANGO_ALLOW_INSECURE_DEFAULTS=1 .venv/bin/python -m pytest -q
```

CI usa as mesmas settings SQLite em [/.github/workflows/validate.yml](.github/workflows/validate.yml).

## Produção

Produção usa apenas [docker-compose.yml](docker-compose.yml).

Setup inicial:

```bash
make env   # cria .env a partir de .env.example
```

Preenche os segredos em `.env` antes de iniciar o stack.

**Domain routing** é controlado por variáveis de ambiente:

- `PRIMARY_DOMAIN` — domínio principal (ex.: `biobrassica.pt`)
- `DOMAIN_ALIASES` — domínios alternativos (separados por vírgula)
- `TLS_CERT_NAME` — nome do diretório certbot (opcional)
- `CERTBOT_EMAIL` — email para notificações Let's Encrypt

A partir destes valores, o stack deriva automaticamente:

- Website: `PRIMARY_DOMAIN` e `www.PRIMARY_DOMAIN`
- Loja: `loja.PRIMARY_DOMAIN`
- Admin: `admin.PRIMARY_DOMAIN`

Cada domínio em `DOMAIN_ALIASES` recebe as mesmas variantes `www.`, `loja.` e `admin.`.

Os três serviços de produção:

- `django_website` — website público + www
- `django_shop` — loja online
- `django_admin` — painel de administração

Deploy:

```bash
make deploy
```

Antes de um deploy que possa interromper o checkout, desativa pagamentos no backoffice: **Configurações → Loja ativa**. O estado é persistido na base de dados e aplicado imediatamente.

As credenciais de pagamento manual são configuradas apenas por variáveis de ambiente: `MANUAL_MBWAY_NUMBER`, `BANK_TRANSFER_BENEFICIARY`, `BANK_TRANSFER_IBAN` e `BANK_TRANSFER_BIC`.

O stack de produção usa `DJANGO_HTTPS_MODE=proxy` (Django atrás do Nginx, confia em `X-Forwarded-Proto`). HSTS está ativo com `includeSubDomains` e `preload` — todos os hostnames públicos precisam de HTTPS funcional antes de expor a configuração a tráfego real.

Certificados antes do primeiro arranque:

```bash
mkdir -p certbot/www certbot/conf
make cert
make deploy
```

Renovação:

```bash
make cert
```

Verificação pós-deploy:

```bash
make verify
```

### Tarefas Periódicas

Para correr as tarefas de manutenção manualmente ou via cron:

```bash
make cron
```

Isto executa:

- `cancel_expired_payments` — cancela pagamentos cujo prazo expirou.
- `release_expired_reservations` — liberta stock reservado no checkout que não foi confirmado a tempo.

## Backup e Restauro

Backup da base de dados e media:

```bash
make backup
```

Restauro do último backup:

```bash
make restore
```

Reset completo da base de dados de produção:

```bash
make reset
make reset BACKUP=/caminho/para/db.sql.gz      # restaurar dump específico
make reset BACKUP=/caminho/para/db.sql.gz YES=1  # não-interativo
```

`make reset` preserva o volume de media. Para restaurar media também, usa `make restore` ou `./scripts/restore.sh` diretamente.

## Notas

- `.env.dev` opcional para overrides de desenvolvimento.
- `.env` em produção, criado a partir de `.env.example`.
- Traduções: `backend/scripts/fill_translations.py` + `python manage.py compilemessages`.
- A aplicação `apps.core` contém o singleton `ShopSettings` com configurações operacionais da loja (timeouts, métodos de pagamento, etc.). Credenciais sensíveis de pagamento ficam fora do backoffice e vêm do `.env`.
