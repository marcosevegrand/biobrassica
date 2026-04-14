# Testing Rollout

## Scope Inventory

This document is the implementation checklist for the phased test rollout. It turns the test strategy into concrete files, suites, and behaviors that need to exist in the repository.

## Phase 1: Infrastructure

Files to add or update:
- `backend/requirements-dev.txt`
- `backend/pytest.ini`
- `backend/conftest.py`
- `backend/tests/__init__.py`
- `backend/tests/conftest.py`
- `backend/tests/factories/__init__.py`
- `backend/tests/factories/accounts.py`
- `backend/tests/factories/orders.py`
- `backend/tests/factories/payments.py`
- `Makefile`
- `.github/workflows/ci.yml`

Things to implement:
- Pytest and pytest-django as the primary new runner.
- Marker taxonomy: `fast`, `integration`, `contract`, `security`, `browser`, `performance`, `admin`, `subdomain`, `htmx`, `stripe`, `slow`.
- Shared factories for core business models.
- Shared fixtures for shop/admin hosts and authenticated admin clients.
- Local commands for phased execution.
- CI job split for fast, integration, contracts, migrations, and browser/security follow-up jobs.

## Phase 2: Payments and Orders

Files to add:
- `backend/tests/payments/test_services.py`
- `backend/tests/payments/test_contracts.py`
- `backend/tests/payments/test_webhooks.py`
- `backend/tests/orders/test_services.py`
- `backend/tests/orders/test_checkout_integration.py`
- `backend/tests/orders/test_access_control.py`

Tests to implement:
- Payment state transitions: paid, failed, expired, refunded.
- Payment callback payload sanitization and IP anonymization.
- Stripe callback deduplication and signature validation.
- Notification scheduling on commit.
- Expiry cleanup and recovery paths.
- Checkout creation through the service layer.
- Order state transitions and stock restoration on cancellation.
- Guest token access rules for order completion and payment status.

## Phase 3: Cart and Catalog

Files to add:
- `backend/tests/cart/test_services.py`
- `backend/tests/cart/test_views.py`
- `backend/tests/cart/test_htmx.py`
- `backend/tests/catalog/test_models.py`
- `backend/tests/catalog/test_querysets.py`
- `backend/tests/catalog/test_views.py`
- `backend/tests/catalog/test_admin.py`

Tests to implement:
- Anonymous and authenticated cart lifecycle.
- Cart merge after registration/login.
- Quantity update, deletion, and stock reconciliation.
- HTMX fragment and out-of-band swap responses.
- Product/category constraints and translated visibility.
- Prefetch and query-count regression checks.
- Catalog admin workflows.

## Phase 4: Content, Website, Accounts, and Core

Files to add:
- `backend/tests/content/test_sanitization.py`
- `backend/tests/content/test_views.py`
- `backend/tests/content/test_admin.py`
- `backend/tests/website/test_views.py`
- `backend/tests/accounts/test_views.py`
- `backend/tests/accounts/test_forms.py`
- `backend/tests/core/test_middleware.py`
- `backend/tests/core/test_translations.py`
- `backend/tests/core/test_admin_dashboard.py`
- `backend/tests/core/test_admin_helpers.py`

Tests to implement:
- HTML sanitization corpus for scripts, iframes, SVG, data URIs, and malformed payloads.
- Translation fallback for website and shared content.
- Registration, profile, password reset, and cart merge boundaries.
- Subdomain routing and path isolation.
- Admin dashboard aggregation and helper workflow behavior.

## Phase 5: Cross-App, Browser, Security, Performance

Files to add:
- `backend/tests/integration/test_checkout_journey.py`
- `backend/tests/integration/test_subdomain_journeys.py`
- `backend/tests/security/test_sanitization.py`
- `backend/tests/security/test_subdomain_abuse.py`
- `backend/tests/security/test_guest_order_tokens.py`
- `backend/tests/performance/test_query_counts.py`
- `backend/tests/browser/test_shop_checkout.spec.ts`
- `backend/tests/browser/test_admin_workflows.spec.ts`
- `backend/tests/browser/test_navigation.spec.ts`

Tests to implement:
- Full anonymous browse to cart to checkout to payment to order completion flow.
- Authenticated order history and anonymous token-based guest access.
- Browser smoke coverage for navbar, subdomain navigation, and HTMX updates.
- Security smoke for route isolation, webhook rejection, and token misuse.
- Query-count smoke coverage for catalog, content, cart summary, dashboard, and checkout.

## Naming Rules

- Test files: `test_<concern>.py`
- Grouped classes: `<Subject><Layer>Tests`
- Test names: `test_<expected_behavior>_when_<condition>` or `test_<action>_<result>`
- Factory names mirror model names: `UserFactory`, `OrderFactory`, `PaymentFactory`
- Fixture names describe business scenarios: `guest_cart`, `paid_order`, `admin_client`, `shop_client_pt`

## Current Start Point

This rollout starts with Phase 1 plus the first payment service batch because payments are the highest-risk business logic area and can validate the new test foundation immediately.