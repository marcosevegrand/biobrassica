# Architecture

Biobrassica is a single Django codebase that serves three surfaces from the same deployment:

- website content on the base domain
- shop flows on the `loja.` subdomain
- Django admin on the `admin.` subdomain

The repository is organized around one backend project in [backend](../backend), deployment assets in [nginx](../nginx) and the compose files at the repo root, and short operational notes in [docs](.).

## Request routing

Subdomain dispatch lives in [backend/config/middleware.py](../backend/config/middleware.py).

- `loja.*` requests are routed to `config.urls_shop` and tagged with `request.subdomain = 'shop'`.
- `admin.*` requests are routed to `config.urls_admin` and tagged with `request.subdomain = 'admin'`.
- Everything else goes to `config.urls_website` and is treated as `website`.

The same middleware also applies admin-specific behavior:

- admin requests are forced to Portuguese by activating `pt`
- admin responses default `Content-Language: pt`
- `SubdomainSecurityMiddleware` rejects `/admin/` paths on non-admin hosts and limits admin hosts to `/admin/`, `/static/`, `/media/`, and `/_health/`

This keeps website, shop, and admin separated at the URLConf boundary without splitting them into separate Django projects.

## App structure

Code is grouped under [backend/apps](../backend/apps):

- `accounts`: authentication and user-facing account flows
- `cart`: cart persistence, session/user cart resolution, stock adjustment helpers
- `catalog`: categories, products, and storefront query helpers
- `content`: blog, recipes, and editorial content
- `core`: shared admin helpers, translation fallback utilities, health/admin plumbing
- `orders`: order creation and order-facing workflows
- `payments`: payment state handling and provider integration
- `website`: website-specific views/templates not tied to shop checkout flows

The apps are separated by feature, but a few shared modules are intentionally cross-cutting.

## Service-layer boundaries

The current codebase keeps write-heavy orchestration in service modules instead of burying it in views or models.

### Cart services

[backend/apps/cart/services.py](../backend/apps/cart/services.py) handles cart lifecycle concerns:

- resolve the active cart from authenticated users or sessions
- create carts for authenticated or anonymous traffic
- merge anonymous carts into user carts after login
- clear cart contents after checkout
- adjust cart lines against current stock and report shortages

Views should treat this module as the boundary for cart mutation and cart/session reconciliation.

### Order services

[backend/apps/orders/services.py](../backend/apps/orders/services.py) contains transactional order creation.

- `create_order_from_cart(...)` creates the order, snapshots order items, and clears the cart in one atomic flow

That keeps checkout-to-order conversion consistent and avoids duplicating order assembly logic across views.

### Payment services

[backend/apps/payments/services.py](../backend/apps/payments/services.py) owns payment state transitions and provider integration.

- webhook sanitization and Stripe client helpers isolate external-provider handling
- payment status transitions (`paid`, `failed`, reset) update both `Payment` and related `Order`
- notification scheduling is deferred with `transaction.on_commit`
- Stripe Checkout session creation and webhook verification live in the same service layer

This is the main boundary between checkout/order state and external payment systems.

## Shared query and translation helpers

Two patterns are reused across apps to keep read paths consistent.

### Translation fallback

[backend/apps/core/translations.py](../backend/apps/core/translations.py) centralizes language normalization, fallback selection, translation prefetching, and translated attribute access.

- `translation_prefetch(...)` builds ranked prefetches for primary language plus fallback
- `select_translation(...)` and `get_translated_attr(...)` choose the best available translation, with optional fallback on empty values
- `TranslationProxy` gives models a lightweight translated attribute facade

Catalog and content code rely on this module rather than implementing per-model translation fallback rules.

### Queryset helpers

[backend/apps/catalog/querysets.py](../backend/apps/catalog/querysets.py) defines reusable storefront querysets for active categories/products, highlighted products, latest products, and detail views.

[backend/apps/content/querysets.py](../backend/apps/content/querysets.py) does the same for published blog posts and recipes, including recipe detail prefetches for related products.

These helpers keep view code thin and make prefetch/select-related behavior explicit in one place.

## Admin helpers

[backend/apps/core/admin_helpers.py](../backend/apps/core/admin_helpers.py) contains reusable admin utilities and mixins:

- order movement helpers for manually sortable models
- shared link, image preview, and badge renderers
- mixins for default inline language, edit links, and order controls

Admin classes should compose these helpers instead of repeating small UI utilities in each app's `admin.py`.

## Verification snapshot

Current verification state is intentionally uneven:

- targeted Django tests pass for the areas being worked on
- Ruff passes
- Pyright still has a large repo-wide backlog and is not yet a clean signal for the full codebase

Treat Django tests and Ruff as the reliable local guardrails today, and use Pyright output as backlog triage rather than a release gate.