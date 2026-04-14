# Audit Findings

## Summary

| Metric | Count |
|---|---:|
| Critical | 0 |
| High | 1 |
| Medium | 33 |
| Low | 2 |
| Info | 0 |

| Category | Count |
|---|---:|
| Security | 4 |
| Code Quality | 21 |
| Organization | 1 |
| Deployment | 5 |
| Performance | 0 |
| i18n | 0 |
| Testing | 5 |

## Legend

### Severity Definitions

| Level | Meaning |
|---|---|
| Critical | Exploitable security vulnerability, data loss risk, or system-breaking bug in production. |
| High | Significant correctness bug, auth bypass path, missing validation on external input, or production-impacting configuration flaw. |
| Medium | Moderate code quality issue, missing edge-case handling, test gap on a critical path, or non-ideal but recoverable pattern. |
| Low | Minor maintainability issue, small optimization opportunity, or localized technical debt. |
| Info | Observation or follow-up suggestion with no immediate fix requirement. |

### Finding Template

```markdown
### [F-NNN] Title

| Field | Value |
|---|---|
| Category | Security |
| Subcategory | Auth |
| Severity | High |
| Phase | Phase 1 - Security & Authentication |
| Location | path/to/file.py:10 |

Description: Clear statement of the issue.

Evidence: Exact code path, behavior, or snippet that demonstrates the issue.

Impact: Why this matters operationally, functionally, or from a security perspective.

Recommendation: Concrete next step for the follow-up agent.
```

## Phase 1 - Security & Authentication

### [F-101] Guest order access tokens are propagated in query strings

| Field | Value |
|---|---|
| Category | Security |
| Subcategory | Access Control |
| Severity | Medium |
| Phase | Phase 1 - Security & Authentication |
| Location | backend/apps/orders/views.py:28 |

Description: Guest access to order and payment pages relies on a bearer-style `access_token`, but the application places that token directly in URLs and then accepts it from either `GET` or `POST` on subsequent requests.

Evidence: `_order_url()` builds links as `...?token={order.access_token}` and `_get_order_for_request()` reads the token from `request.GET` before falling back to `request.POST`. The same tokenized URL is used for Stripe success and cancel redirects in the checkout flow.

Impact: Query-string tokens are more likely to leak via browser history, server logs, analytics, copied links, and referrer headers. Anyone who obtains the URL can access the guest order flow until the token is rotated.

Recommendation: Move guest-order authorization to a less leak-prone mechanism such as a signed short-lived POST-only token, an HttpOnly session binding after the first verified visit, or one-time exchange flow. At minimum, stop emitting the token in URLs and stop accepting it through `GET`.

### [F-102] Django trusts a client-controlled forwarded-proto header in production

| Field | Value |
|---|---|
| Category | Security |
| Subcategory | Proxy Trust |
| Severity | Medium |
| Phase | Phase 1 - Security & Authentication |
| Location | nginx/nginx.conf:31 |

Description: The production stack is configured so Django trusts `X-Forwarded-Proto` to determine whether a request is secure, while Nginx forwards that header from the client instead of setting it authoritatively.

Evidence: `production.py` enables `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')` and `USE_X_FORWARDED_HOST = True` when `DJANGO_HTTPS_MODE=proxy`. In front of it, `nginx/nginx.conf` sets `proxy_set_header X-Forwarded-Proto $http_x_forwarded_proto;`, which passes through the incoming header value unchanged.

Impact: A client can influence Django's notion of request security and scheme-sensitive behavior. That can weaken HTTPS enforcement assumptions, affect absolute URL generation, and create subtle security regressions around secure redirects and cookie handling in proxy deployments.

Recommendation: Set `X-Forwarded-Proto` from Nginx's actual connection context, for example with `$scheme`, and review any other trusted forwarded headers so only the reverse proxy can supply them.

### [F-103] No Content Security Policy is defined despite third-party script dependencies

| Field | Value |
|---|---|
| Category | Security |
| Subcategory | Browser Hardening |
| Severity | Low |
| Phase | Phase 1 - Security & Authentication |
| Location | backend/templates/base.html:10 |

Description: The application loads external browser resources but does not define a Content-Security-Policy at either the Django or Nginx layer.

Evidence: The shared templates load Google Fonts, HTMX from `unpkg.com`, and an Elfsight script on the website home page. The Nginx virtual host configs add `X-Frame-Options`, `X-Content-Type-Options`, and `Referrer-Policy`, but no CSP header is present.

Impact: If an injection path is introduced elsewhere, the browser has no CSP boundary to reduce exploitability. The current setup also leaves third-party script execution broader than necessary.

Recommendation: Add a restrictive baseline CSP for shop, website, and admin surfaces, then explicitly allow only the required origins for fonts, styles, and third-party scripts. Prefer nonce- or hash-based allowances where practical.

### [F-104] Guest access token is disclosed to Stripe as checkout metadata

| Field | Value |
|---|---|
| Category | Security |
| Subcategory | Third-Party Data Exposure |
| Severity | Medium |
| Phase | Phase 1 - Security & Authentication |
| Location | backend/apps/payments/services.py:403 |

Description: The Stripe Checkout session metadata includes the order `access_token`, which is the same bearer token used to authorize guest access to order pages.

Evidence: `StripeService.create_checkout_session()` sends metadata containing `order_id`, `payment_id`, and `'access_token': str(order.access_token)` to Stripe.

Impact: The guest authorization token is unnecessarily replicated into a third-party system, where it may appear in dashboards, support tooling, webhook payload inspection, and provider-side logs. That increases the number of places from which guest order access can be recovered.

Recommendation: Remove the access token from Stripe metadata and restrict metadata to opaque internal identifiers only. If correlation is needed, use the order ID or payment ID and keep the guest token strictly internal.

## Phase 2 - Payment & Order Pipeline

### [F-201] Checkout flow bypasses the stock-safe service layer and never decrements inventory

| Field | Value |
|---|---|
| Category | Code Quality |
| Subcategory | Data Integrity |
| Severity | High |
| Phase | Phase 2 - Payment & Order Pipeline |
| Location | backend/apps/orders/views.py:123 |

Description: The active checkout path creates orders directly in the view instead of using the existing service that locks products, validates stock, decrements inventory, and clears the cart atomically.

Evidence: `checkout_confirm()` calls `Order.objects.create()` and `OrderItem.objects.create()` directly, then deletes the cart items. It never calls `create_order_from_cart()`, even though that service exists specifically to lock inventory with `select_for_update()`, validate availability, decrement `product.stock`, and clear the cart inside a transaction.

Impact: Orders can be accepted against stale stock and inventory is not reserved when checkout starts. That creates a direct oversell path and breaks stock accuracy under concurrent checkouts.

Recommendation: Route checkout creation through `create_order_from_cart()` or an equivalent single transactional service. The view should not duplicate order assembly and stock handling logic.

### [F-202] Stripe session creation failure leaves orphaned pending orders after clearing the cart

| Field | Value |
|---|---|
| Category | Code Quality |
| Subcategory | Failure Recovery |
| Severity | Medium |
| Phase | Phase 2 - Payment & Order Pipeline |
| Location | backend/apps/orders/views.py:123 |

Description: The checkout flow persists the order, order items, payment record, and cart deletion before attempting to create the Stripe Checkout session, but does not roll back or restore state when that external call fails.

Evidence: In `checkout_confirm()`, the view creates the order and items, deletes `CartItem`s, creates a pending `Payment`, and moves the order to `payment_pending` before calling `stripe_service.create_checkout_session()`. On exception, it logs the error, shows a flash message, and redirects back to checkout without recreating the cart or cancelling the order.

Impact: Customers can lose their cart while the system accumulates abandoned pending orders and payments that were never actually linked to a Stripe session. Recovery is manual and the user is redirected back to a checkout path that now has no cart state.

Recommendation: Wrap local state changes and external session preparation in a recovery-oriented workflow. Either create the Stripe session before clearing the cart, or use a transaction plus compensating cleanup so failed session creation does not leave orphaned payment state.

### [F-203] Payment expiry polling bypasses the service-layer transition logic

| Field | Value |
|---|---|
| Category | Code Quality |
| Subcategory | State Consistency |
| Severity | Medium |
| Phase | Phase 2 - Payment & Order Pipeline |
| Location | backend/apps/orders/views.py:257 |

Description: The polling branch in `payment_status()` marks Stripe payments as expired by mutating the `Payment` model directly instead of calling the dedicated expiry service.

Evidence: When Stripe reports `session.status == 'expired'`, the view assigns `payment.status = Payment.Status.EXPIRED` and saves `status` and `last_error` directly. The existing `expire_pending_payment()` service also transitions the related order from `payment_pending` back to `pending`, but that service is not used here.

Impact: Order and payment states can diverge after expiry polling, leaving expired payments attached to orders that still appear to be awaiting payment. That weakens operational clarity and can interfere with retry flows or admin actions.

Recommendation: Replace the inline mutation with `expire_pending_payment()` so expiry handling stays consistent across polling, background cleanup, and webhook-driven flows.

### [F-204] Duplicate webhook deliveries are not atomically deduplicated

| Field | Value |
|---|---|
| Category | Code Quality |
| Subcategory | Webhook Idempotency |
| Severity | Medium |
| Phase | Phase 2 - Payment & Order Pipeline |
| Location | backend/apps/payments/views.py:81 |

Description: Stripe webhook idempotency is implemented as a pre-check plus insert, but the deduplication is not atomic.

Evidence: `stripe_callback()` first queries `existing_callback = PaymentCallback.objects.filter(provider_event_id=event_id).first()` and only then calls `PaymentCallback.objects.create(...)`. The model also enforces a unique constraint on `provider_event_id`, so concurrent deliveries of the same event can race between the existence check and the insert.

Impact: Under concurrent retries from Stripe, one request can raise a uniqueness error before the handler returns `200 OK`. That turns an otherwise harmless duplicate delivery into a server error and can trigger additional webhook retries and noisy operational failures.

Recommendation: Make webhook deduplication atomic by moving the insert into a transaction and treating uniqueness collisions as successful duplicates, or use `get_or_create()` on the event identifier with proper integrity-error handling.

### [F-205] Refund webhooks do not reconcile order workflow state

| Field | Value |
|---|---|
| Category | Code Quality |
| Subcategory | Financial State Consistency |
| Severity | Medium |
| Phase | Phase 2 - Payment & Order Pipeline |
| Location | backend/apps/payments/views.py:121 |

Description: Refund processing updates the payment state only and leaves the related order workflow untouched.

Evidence: `stripe_callback()` handles `charge.refunded` by calling `mark_payment_refunded(locked_payment)`. In turn, `mark_payment_refunded()` only transitions `Payment.status` to `refunded` and logs the change; it does not move the order out of `paid` or reverse any fulfillment state.

Impact: Refunded orders can remain in `paid`, `preparing`, or later workflow states even though the financial state has been reversed. That creates reconciliation drift between customer payment status and operational fulfillment state.

Recommendation: Define an explicit refund workflow for orders, including how refunded-but-unfulfilled orders should transition and whether stock or downstream fulfillment state must be rolled back.

### [F-206] Pending Stripe sessions have no local expiry deadline or autonomous cleanup path

| Field | Value |
|---|---|
| Category | Code Quality |
| Subcategory | Retry Recovery |
| Severity | Medium |
| Phase | Phase 2 - Payment & Order Pipeline |
| Location | backend/apps/payments/services.py:304 |

Description: The payment layer has code to expire stale pending payments, but Stripe checkout setup does not persist an expiry timestamp and no autonomous cleanup path is wired into the application flow.

Evidence: `expire_stale_pending_payments()` exists, but current Stripe setup in `reset_payment()` and `configure_stripe_checkout()` explicitly sets `payment.expires_at = None`. The order then depends on either a delivered webhook or a user revisit to `payment_status()` to leave the `payment_pending` state.

Impact: If Stripe sends no usable expiry signal to the app, or the callback is missed and the customer never returns, orders can remain stuck in `payment_pending` indefinitely with no local deadline to recover them.

Recommendation: Persist a concrete local expiry timestamp when creating the Stripe session and run the stale-payment expiry service from a scheduled job or equivalent background process.

## Phase 3 - Data Models & Business Logic

### [F-301] Pickup-location selection is not validated against product availability

| Field | Value |
|---|---|
| Category | Code Quality |
| Subcategory | Business Rules |
| Severity | Medium |
| Phase | Phase 3 - Data Models & Business Logic |
| Location | backend/apps/orders/forms.py:17 |

Description: Products define per-location pickup availability, but the order pipeline only validates that some pickup location was selected, not that the chosen location can actually fulfill every line item.

Evidence: `Product.available_locations` is modeled as a many-to-many relation to catalog locations, but checkout uses hardcoded `Order.PickupLocation` choices. `CheckoutForm` only checks that `pickup_location` is non-empty for pickup orders and never cross-checks the selected location against the cart products.

Impact: The system can accept pickup orders for locations where one or more products are not available, creating unfulfillable orders despite having location-specific availability data in the catalog.

Recommendation: Validate the selected pickup location against all cart items before order creation, and derive selectable pickup options from active `Location` records rather than from hardcoded order enums.

### [F-302] Publication rules for blog posts and recipes are enforced only in admin UI

| Field | Value |
|---|---|
| Category | Code Quality |
| Subcategory | Domain Invariants |
| Severity | Medium |
| Phase | Phase 3 - Data Models & Business Logic |
| Location | backend/apps/content/querysets.py:9 |

Description: The public content layer treats `is_published=True` as sufficient for visibility, while the actual editorial readiness rules live only in admin-side helper logic.

Evidence: Public querysets expose any `BlogPost` or `Recipe` with `is_published=True`. The admin classes implement publish blockers for missing PT translation, missing cover image, and missing recipe ingredients/instructions, but the `BlogPost` and `Recipe` models do not enforce those rules in `clean()` or `save()`.

Impact: Programmatic writes, scripts, imports, or future non-admin entry points can publish incomplete content that the public site will render immediately, bypassing the editorial constraints assumed by the admin workflow.

Recommendation: Move publish invariants into model validation or a dedicated publish service so every write path enforces the same readiness rules before content becomes public.

### [F-303] Website content singleton is enforced only in admin permissions

| Field | Value |
|---|---|
| Category | Organization |
| Subcategory | Source of Truth |
| Severity | Low |
| Phase | Phase 3 - Data Models & Business Logic |
| Location | backend/apps/website/views.py:28 |

Description: The website content system behaves like a singleton, but that invariant is not enforced at the model or database layer.

Evidence: Public views resolve site content with `WebsiteContent.objects.first()`, while admin merely hides the add button once one row exists. The model itself allows multiple rows and the site will silently use whichever row happens to sort first.

Impact: If multiple `WebsiteContent` records are created outside the admin guardrail, the public website will have a nondeterministic source of truth for core static content.

Recommendation: Enforce the singleton invariant in the model or database layer, or switch to an explicit single-record pattern such as a dedicated singleton model/service.

### [F-304] Product image model does not enforce a single primary image per product

| Field | Value |
|---|---|
| Category | Code Quality |
| Subcategory | Domain Invariants |
| Severity | Medium |
| Phase | Phase 3 - Data Models & Business Logic |
| Location | backend/apps/catalog/models.py:225 |

Description: The catalog treats `is_primary` as a special invariant for product merchandising, but the data model does not enforce that only one image per product can be marked primary.

Evidence: `Product.primary_image` returns the first image flagged `is_primary`, falling back to the first image in the relation. `ProductImage` defines `is_primary` as a plain boolean with no uniqueness constraint or model-level validation to prevent multiple primary images for the same product.

Impact: Multiple primary images can coexist, making storefront rendering order-dependent and undermining the admin workflow’s assumption that a product has one canonical merchandising image.

Recommendation: Add a conditional uniqueness constraint or model validation that guarantees at most one primary image per product, and define how existing duplicates should be repaired.

### [F-305] Storefront visibility rules conflict with translation fallback behavior

| Field | Value |
|---|---|
| Category | Code Quality |
| Subcategory | Source of Truth |
| Severity | Medium |
| Phase | Phase 3 - Data Models & Business Logic |
| Location | backend/apps/catalog/querysets.py:16 |

Description: The catalog storefront requires a translation in the current request language for products to be queryable at all, even though the translation helper layer is explicitly built to fall back to Portuguese.

Evidence: `active_product_queryset()` filters with `translations__language=normalized_lang`, excluding products without an exact translation in the active language. At the same time, `get_translated_attr()` and `translation_prefetch()` support ordered fallback to Portuguese, and admin publication/readiness logic is centered on PT completeness rather than per-language completeness.

Impact: Products considered operationally ready can disappear entirely from non-PT storefronts instead of rendering with PT fallback. That creates inconsistent rules between the domain translation layer, admin workflow, and public query layer.

Recommendation: Decide whether storefront behavior should require exact-language completeness or use PT fallback. Then enforce that rule consistently in querysets, admin readiness checks, and publication criteria.

## Phase 4 - Views & Templates

### [F-401] Website and content templates hardcode production shop URLs instead of using routed links

| Field | Value |
|---|---|
| Category | Code Quality |
| Subcategory | Routing Consistency |
| Severity | Medium |
| Phase | Phase 4 - Views & Templates |
| Location | backend/templates/content/recipe_detail.html:138 |

Description: Multiple public templates link to the shop using hardcoded absolute `https://loja.biobrassica.pt/...` URLs instead of route-aware links built from Django URL configuration or current-host context.

Evidence: The pattern appears in recipe cross-sell links, website CTAs, and website navigation/footer links. Examples include `recipe_detail.html`, `components/navbar_website.html`, `components/footer_website.html`, `website/home.html`, and `website/agriculture.html`.

Impact: These links bypass environment-aware routing, making local/staging deployments inconsistent with production, breaking host portability, and potentially dropping language or subdomain behavior that the request middleware is supposed to control.

Recommendation: Replace hardcoded production hosts with route-aware links or a centralized host builder that respects the current environment, language, and subdomain configuration.

### [F-402] Cart and checkout render and sell products outside the storefront visibility rules

| Field | Value |
|---|---|
| Category | Code Quality |
| Subcategory | Query / Template Consistency |
| Severity | Medium |
| Phase | Phase 4 - Views & Templates |
| Location | backend/apps/cart/services.py:34 |

Description: The cart and checkout flows operate on raw cart items and render product data directly from `CartItem.product`, instead of reusing the catalog queryset that defines which products are actually visible and valid on the storefront.

Evidence: `get_cart_items_queryset()` simply selects related `product` rows and prefetches translations/images. Cart templates render `item.product.get_name` and `item.product.primary_image`, while checkout builds orders from `CartItem.objects.filter(cart=cart).select_related('product')`. None of those paths apply `active_product_queryset()`, `product__is_active=True`, or exact-language translation filters. A product only needs to be active at add-to-cart time.

Impact: A product that is later deactivated, loses its required storefront translation, or otherwise stops qualifying for catalog display can still remain in carts, appear in checkout, and be sold. That creates drift between what the storefront lists and what the order pipeline will still accept.

Recommendation: Revalidate cart and checkout items against the same visibility and availability rules used by the storefront before rendering or creating orders, and remove or flag items that are no longer saleable.

## Phase 5 - Admin Interface & Workflows

### [F-501] Content changelist publish toggles bypass the editorial blockers shown in the change form

| Field | Value |
|---|---|
| Category | Code Quality |
| Subcategory | Admin Workflow Consistency |
| Severity | Medium |
| Phase | Phase 5 - Admin Interface & Workflows |
| Location | backend/apps/content/admin.py:47 |

Description: The content admin exposes inline `is_published` toggles on the changelist, but the actual publish blockers only run through the custom change-form submit actions.

Evidence: Both `BlogPostAdmin` and `RecipeAdmin` declare `list_editable = ('is_published',)`. Their publish readiness checks live in `_blog_publish_blockers()` / `_recipe_publish_blockers()` and are enforced only inside `handle_changeform_submit_action()` for `_publish_post` and `_publish_recipe`. The list-edit path does not call those blockers; for blog posts it only normalizes `published_at`, and for recipes it directly persists `is_published`.

Impact: Editors can publish incomplete blog posts or recipes directly from the changelist even though the change form presents publication as a guarded workflow. That undermines the admin’s own editorial guidance and reinforces the Phase 3 invariant drift.

Recommendation: Remove changelist publication toggles or route all publish/unpublish operations through a shared service or model-level validation that enforces the same blockers everywhere.

### [F-502] Catalog admin product-activation controls use inconsistent readiness rules and bypass paths

| Field | Value |
|---|---|
| Category | Code Quality |
| Subcategory | Admin Workflow Consistency |
| Severity | Medium |
| Phase | Phase 5 - Admin Interface & Workflows |
| Location | backend/apps/catalog/admin.py:479 |

Description: The product admin presents activation and reactivation as a guarded workflow, but it uses inconsistent readiness rules across cards, buttons, and changelist edits.

Evidence: The `ready-to-reactivate` queue and `_can_reactivate_product()` require only `stock > 0`, a Portuguese translation, and at least one primary image. They do not require any available pickup locations, do not detect the multiple-primary-image problem from F-304, and do not align with `active_product_queryset()` which requires an exact translation in the active storefront language rather than PT fallback. At the same time, `ProductAdmin.list_editable` exposes direct changelist edits for `is_active`, `stock`, `allow_shipping`, and related merchandising fields, so operators can activate products without passing through `_can_reactivate_product()` or any shared validation path.

Impact: Operations staff can see products labeled as ready and reactivate them even when those products still will not behave correctly in the storefront or fulfillment flow, while other edit paths bypass the guarded workflow entirely. The admin dashboard therefore becomes an unreliable operational source of truth rather than an enforceable control surface.

Recommendation: Define a single shared “catalog ready” rule and reuse it in admin cards, queue filters, reactivation actions, changelist edits, and storefront query logic so operational readiness means the same thing everywhere.

### [F-503] Order admin dashboards and action buttons ignore refunded-payment fallout until transition time

| Field | Value |
|---|---|
| Category | Code Quality |
| Subcategory | Admin Workflow Consistency |
| Severity | Medium |
| Phase | Phase 5 - Admin Interface & Workflows |
| Location | backend/apps/core/admin_dashboard.py:29 |

Description: Admin operational views continue to classify refunded orders as paid or actionable because they key off order status, while refund handling leaves order status unreconciled and the payment-state guard only triggers when an action is attempted.

Evidence: Phase 2 already established that refund callbacks mark `Payment.status = refunded` without reconciling the related order workflow. The dashboard still counts `paid_orders` by `Order.status in [paid, preparing, ready, delivered]`, and `todays_pickups` uses similar status filters. In `OrderAdmin`, change-form buttons are shown from `obj.can_transition_to(...)`, which only checks order-state adjacency; the payment-state validation is enforced later by `transition_order_status()` / `order.full_clean()`.

Impact: Refunded orders can continue to appear in paid or pickup operational buckets, and admins can be shown workflow buttons that inevitably fail when clicked. That both obscures refund fallout and creates avoidable operator confusion.

Recommendation: Reconcile order workflow state when payments are refunded, and derive dashboard buckets and available admin actions from both order state and payment state instead of order status alone.

### [F-505] Customer admin revenue panels count non-realized orders as commercial revenue

| Field | Value |
|---|---|
| Category | Code Quality |
| Subcategory | Admin Reporting Accuracy |
| Severity | Medium |
| Phase | Phase 5 - Admin Interface & Workflows |
| Location | backend/apps/accounts/admin.py:74 |

Description: The customer backoffice labels a metric as accumulated revenue, but it is calculated from all related orders regardless of payment or cancellation outcome.

Evidence: `UserAdmin.get_queryset()` annotates `lifetime_revenue=Coalesce(Sum('orders__total', distinct=True), ...)` with no status or payment filter. `customer_snapshot_panel()` then renders this value as `Receita acumulada`. Orders in `pending`, `payment_pending`, `cancelled`, or refund-affected states are therefore included in the figure.

Impact: Support and account-management staff can treat uncollected or reversed orders as realized revenue when assessing customer value. That distorts operational decisions and makes admin reporting inconsistent with the payment-state issues already identified in Phase 2 and Phase 5.

Recommendation: Base customer revenue metrics on confirmed paid payments or on orders in explicitly realized states only, and label gross-order totals separately if that view is still useful.

### [F-506] Location and delivery-method admin controls do not govern checkout options

| Field | Value |
|---|---|
| Category | Code Quality |
| Subcategory | Admin Source of Truth |
| Severity | Medium |
| Phase | Phase 5 - Admin Interface & Workflows |
| Location | backend/apps/catalog/admin.py:25 |

Description: The backoffice provides operational controls and readiness cards for `Location` and `DeliveryMethod`, but checkout does not use those models as the source of truth for selectable pickup and fulfillment options.

Evidence: `LocationAdmin` and `DeliveryMethodAdmin` expose `is_active` toggles and workflow cards that describe those records as available to the business. However, `CheckoutForm` builds `fulfillment_method` and `pickup_location` from `Order.FulfillmentMethod.choices` and `Order.PickupLocation.choices`, both hardcoded enums on the order model. The active/inactive state of admin-managed `Location` and `DeliveryMethod` records is not consulted when validating checkout choices.

Impact: Operations staff can change or deactivate delivery and pickup records in admin without changing what checkout still offers to customers. That makes the configuration screens look authoritative when they are only partially connected to the real ordering flow.

Recommendation: Make checkout options derive from active `Location` and `DeliveryMethod` records, or reduce the admin UI so it no longer implies those models control transactional availability.

## Phase 6 - Configuration & Deployment

### [F-601] Domain onboarding is split across environment, Django, and nginx with inconsistent sources of truth

| Field | Value |
|---|---|
| Category | Deployment |
| Subcategory | Host / Origin Configuration |
| Severity | Medium |
| Phase | Phase 6 - Configuration & Deployment |
| Location | backend/config/settings/production.py:17 |

Description: Production host/origin trust is only partially environment-driven. Adding or changing domains requires coordinated edits in multiple files, but the deployment guidance suggests `ALLOWED_HOSTS` is the main override point.

Evidence: `production.py` reads `ALLOWED_HOSTS` from the environment, but `CSRF_TRUSTED_ORIGINS` is hardcoded to the four production domains. nginx server blocks are also hardcoded with explicit `server_name` values in `nginx/conf.d/*.conf`. Meanwhile, the deployment guide says `ALLOWED_HOSTS` should be overridden when adding hostnames.

Impact: A new domain or alias can be added in one layer and still fail elsewhere: nginx may reject it before Django sees it, or Django may accept it for GET requests while CSRF-protected POST flows fail. This creates fragile deployments and misleading operator guidance.

Recommendation: Centralize host/origin configuration so the same source of truth drives nginx `server_name`, Django `ALLOWED_HOSTS`, and `CSRF_TRUSTED_ORIGINS`, or explicitly document all required change points and validate them during deploy.

### [F-602] The production HTTPS contract is validated with spoofed headers rather than real proxy state

| Field | Value |
|---|---|
| Category | Deployment |
| Subcategory | Reverse Proxy Contract |
| Severity | Medium |
| Phase | Phase 6 - Configuration & Deployment |
| Location | docker-compose.yml:29 |

Description: The stack’s health and secure-request behavior depend on injecting `X-Forwarded-Proto: https` into plain HTTP hops, which validates an assumed proxy contract rather than the actual reverse-proxy state.

Evidence: The Django container healthcheck calls `curl -H "X-Forwarded-Proto: https" http://localhost:8000/_health/`. The deployment guide says Cloudflare must forward that header, nginx passes it unchanged with `proxy_set_header X-Forwarded-Proto $http_x_forwarded_proto`, and Django uses `SECURE_PROXY_SSL_HEADER` in proxy mode to decide whether requests are secure.

Impact: Health checks can report the application healthy even when the real proxy chain is misconfigured, because the health probe forges the exact header Django expects. The deployment’s HTTPS correctness therefore depends on a header-spoofing convention instead of an authoritative internal signal.

Recommendation: Make the reverse proxy set forwarded scheme authoritatively from connection context, and use health checks that validate the real proxy path or a dedicated internal endpoint that does not require spoofed HTTPS headers.

### [F-603] Backup and restore tooling hardcodes deployment defaults that the documented configuration says are overrideable

| Field | Value |
|---|---|
| Category | Deployment |
| Subcategory | Backup / Recovery |
| Severity | Medium |
| Phase | Phase 6 - Configuration & Deployment |
| Location | scripts/backup.sh:20 |

Description: The backup workflow assumes the default database name, default database user, default compose project name, and default media volume name, even though the production configuration and deployment guide present some of those values as configurable.

Evidence: `scripts/backup.sh` runs `pg_dump -U biobrassica biobrassica` and restores media through the fixed volume name `biobrassica_media_files`. The deployment guide documents `DB_NAME` and `DB_USER` as optional overrides, and Docker Compose derives named volume prefixes from the project name unless explicitly fixed. The script does not read the active env file or compose project name before choosing targets.

Impact: Backups and restores can silently stop matching the live deployment as soon as the stack is deployed with non-default database identifiers or a different compose project name. Recovery tooling then fails exactly when it is needed most.

Recommendation: Parameterize backup and restore commands from the active compose environment and explicit volume names, or document that those deployment values are fixed and not safely overrideable.

### [F-604] Release startup is non-atomic and mutates persistent state before the new version is proven healthy

| Field | Value |
|---|---|
| Category | Deployment |
| Subcategory | Release / Rollback Safety |
| Severity | Medium |
| Phase | Phase 6 - Configuration & Deployment |
| Location | backend/docker-entrypoint.sh:5 |

Description: Every production startup runs schema migrations, static collection, and message compilation inside the application container before the new release is considered healthy, but the documented release flow provides no rollback-safe sequencing or automated recovery if those steps partially succeed and the app then fails.

Evidence: `backend/docker-entrypoint.sh` runs `manage.py migrate --noinput`, `collectstatic --noinput`, and `compilemessages` on every production start. The documented deployment sequence and GitHub deploy workflow then do `docker compose ... build` followed by `up -d --remove-orphans`, with no dedicated migration job, no post-start rollback step, and only a shallow homepage curl in the deploy workflow. Static assets are written into the persistent `static_files` volume, so startup mutates shared runtime state across releases.

Impact: A bad release can leave the environment in a mixed state: database schema may already be advanced, the shared static volume may already contain new assets, and the new app version may still fail to stay up. Rolling back the code alone is therefore not guaranteed to restore a consistent runtime.

Recommendation: Separate migrations and asset publication from app startup, add explicit post-deploy verification with rollback procedures, and treat static/schema changes as coordinated release steps rather than side effects of container boot.

## Phase 7 - Testing & Internationalization

### [F-701] CI does not cover the admin drift paths identified in Phases 3 to 5

| Field | Value |
|---|---|
| Category | Testing |
| Subcategory | Regression Coverage |
| Severity | Medium |
| Phase | Phase 7 - Testing & Internationalization |
| Location | .github/workflows/ci.yml:60 |

Description: The current automated test selection misses the admin surfaces where several of the documented invariants and reporting drifts live, so the problematic behavior can regress without any CI signal.

Evidence: CI runs only `apps.core.tests`, `apps.orders.tests`, and `apps.payments.tests`. The repository does contain test modules for `accounts`, `catalog`, `content`, and `website`, but the reviewed tests in `content/tests.py` and `catalog/tests.py` mainly assert workflow cards and guarded change-form actions, not the changelist `list_editable` bypasses, customer revenue reporting drift, website-content fallback drift, or checkout/config source-of-truth mismatches identified in Phases 5 and 6.

Impact: The codebase has no enforced regression net for several backoffice behaviors that currently look correct in the UI while diverging from the underlying business rules. Those mismatches can persist or worsen unnoticed.

Recommendation: Add focused tests for the documented admin bypass/reporting scenarios and include the affected app suites in CI, at least for targeted regression modules around catalog, content, accounts, and website admin behavior.

### [F-702] Deployment and recovery contracts are effectively untested

| Field | Value |
|---|---|
| Category | Testing |
| Subcategory | Operational Coverage |
| Severity | Medium |
| Phase | Phase 7 - Testing & Internationalization |
| Location | .github/workflows/deploy.yml:89 |

Description: The repository validates configuration shape and basic Django deploy checks, but it does not automate the startup, proxy, backup, restore, or rollback paths that several Phase 6 findings depend on.

Evidence: CI validates `docker compose config`, runs Django migrations/tests, and executes `manage.py check --deploy`. The deploy workflow then builds and starts the stack before running a shallow homepage curl. There is no automated execution of the production entrypoint sequence, no test of `scripts/backup.sh`, no restore rehearsal, no verification of the forwarded-header contract, and no rollback check after partial startup failure.

Impact: Operational regressions in startup sequencing, backup compatibility, or reverse-proxy assumptions are likely to be discovered only during deployment or incident response, when the cost of failure is highest.

Recommendation: Introduce at least one automated production-like smoke path that exercises container startup semantics, and add scheduled or manual verification for backup/restore and rollback procedures.

### [F-703] Cart and storefront visibility drift has no focused regression coverage

| Field | Value |
|---|---|
| Category | Testing |
| Subcategory | Regression Coverage |
| Severity | Medium |
| Phase | Phase 7 - Testing & Internationalization |
| Location | backend/apps/cart/tests.py:17 |

Description: The existing cart and checkout tests exercise quantity changes and checkout happy paths, but they do not cover the Phase 4 drift where carts retain products that are no longer valid on the storefront.

Evidence: `cart/tests.py` verifies anonymous carts, HTMX fragments, and quantity behavior, and `orders/tests.py` verifies checkout with active products and shipping constraints. The reviewed tests do not assert what happens when a product becomes inactive after being added to cart, loses the current-language storefront translation, or otherwise stops matching `active_product_queryset()` while still being present in `CartItem` rows.

Impact: The cart/storefront mismatch documented in F-402 can regress indefinitely without any automated signal. A future change could deepen the inconsistency between catalog visibility and checkout sellability without breaking the current test suite.

Recommendation: Add regression tests that place products in a cart and then invalidate storefront eligibility through deactivation or translation changes, asserting that cart rendering and checkout revalidate those items correctly.

### [F-704] Refund fallout and admin reporting mismatches are not covered by automated tests

| Field | Value |
|---|---|
| Category | Testing |
| Subcategory | Regression Coverage |
| Severity | Medium |
| Phase | Phase 7 - Testing & Internationalization |
| Location | backend/apps/payments/tests.py:1 |

Description: The payment tests cover successful callbacks, invalid signatures, and duplicate-event handling, but they do not cover the refund and reporting fallout already documented in Phases 2 and 5.

Evidence: `payments/tests.py` includes webhook tests for payment success and duplicate callback idempotency, but there is no reviewed test asserting that refunded payments reconcile order workflow state, disappear from paid operational buckets, or stop being counted as realized customer revenue in the admin. Likewise, the accounts and orders admin tests validate card presence and basic actions, not the accuracy of those metrics after refunds or cancellations.

Impact: The refund/admin drift documented in F-205, F-503, and F-505 can persist unnoticed because the test suite never exercises the affected reporting and workflow states.

Recommendation: Add tests that simulate refund callbacks end to end and then assert order state, admin action availability, dashboard bucket membership, and customer revenue reporting all stay consistent.

### [F-705] Cart popup and HTMX interaction paths have no browser-level regression coverage

| Field | Value |
|---|---|
| Category | Testing |
| Subcategory | Frontend Regression Coverage |
| Severity | Medium |
| Phase | Phase 7 - Testing & Internationalization |
| Location | backend/static/js/navbar.js:1 |

Description: The cart preview relies on client-side popup state management and HTMX swap behavior, but the repository has no browser-level tests covering those interactions.

Evidence: The popup is rendered through `cart/_cart_popup.html`, reopened by a `htmx:afterSwap` listener in `navbar.js`, and coordinated with separate OOB fragments like the cart count and site messages. The reviewed Python tests cover HTMX responses and fragment payloads, but there are no browser tests exercising click-to-open behavior, outside-click dismissal, close-button handling, or popup persistence after HTMX cart updates.

Impact: Regressions in cart-preview behavior can reach production even if server-side fragments remain correct. A small DOM or JS change can silently break one of the highest-visibility commerce interactions without failing CI.

Recommendation: Add a lightweight browser regression suite for the cart popup and navbar interactions, covering open/close behavior, HTMX cart updates, empty-cart transitions, and coexistence with other transient UI like flash messages.

### Priority Regression Clusters

1. Payment and order-state reconciliation
	First tests to add: refund webhook updates, duplicate/refund sequencing, actionable admin buttons after refund, and dashboard bucket accuracy.

2. Cart and storefront eligibility drift
	First tests to add: product added to cart then deactivated, translation removed after cart insertion, and checkout rejection or cart flagging for no-longer-saleable items.

3. Admin source-of-truth and reporting drift
	First tests to add: changelist `list_editable` bypasses for publish/activate flows, customer revenue metric filtering, and checkout options staying aligned with active location/delivery records.

4. Deployment and recovery contract smoke coverage
	First tests to add: production-like startup smoke, forwarded-header contract verification, backup script execution contract, and rollback behavior after partial startup failure.

## Phase 8 - Frontend Assets & Static Files

### [F-801] Public frontend depends on external CDN assets and third-party embeds without local fallback

| Field | Value |
|---|---|
| Category | Code Quality |
| Subcategory | Frontend Dependency Management |
| Severity | Medium |
| Phase | Phase 8 - Frontend Assets & Static Files |
| Location | backend/templates/base.html:10 |

Description: Core frontend rendering depends on externally hosted fonts and scripts, and those dependencies are loaded directly at runtime rather than being bundled or mirrored locally.

Evidence: The base templates load Google Fonts from `fonts.googleapis.com` / `fonts.gstatic.com`, the shop base loads HTMX from `unpkg.com`, and the home page loads the Elfsight platform script from `elfsightcdn.com` for the Instagram feed. None of those resources are pinned with integrity metadata or backed by a local fallback path.

Impact: A CDN outage, regional block, CSP tightening, or third-party script regression can degrade rendering or interactivity on the live site independently of the application deployment. It also widens the runtime dependency surface for the public pages.

Recommendation: Self-host critical frontend assets where practical, add integrity/fallback strategies for unavoidable third-party dependencies, and isolate optional embeds so their failure does not affect core page behavior.

### [F-802] Tailwind asset generation uses inconsistent toolchains and versions across environments

| Field | Value |
|---|---|
| Category | Code Quality |
| Subcategory | Frontend Build Consistency |
| Severity | Medium |
| Phase | Phase 8 - Frontend Assets & Static Files |
| Location | backend/Dockerfile:27 |

Description: The project builds the same `output.css` artifact through different Tailwind installation paths and different versions depending on environment, making frontend assets environment-sensitive.

Evidence: `backend/package.json` pins `tailwindcss` and `@tailwindcss/cli` at `4.2.2`, while the production Dockerfile downloads a standalone Tailwind binary at `v4.1.8` from GitHub and runs it directly. Development uses `docker-compose.dev.yml` to `npm install` the npm CLI on container start and run it in watch mode. All of those paths target the same generated file `static/css/output.css`.

Impact: CSS output can differ between local development, committed artifacts, and production image builds even when application code is unchanged. That makes visual regressions harder to reproduce and increases the chance of shipping frontend discrepancies that were never seen in development.

Recommendation: Standardize on one Tailwind toolchain and version across development and production, and make asset generation deterministic rather than depending on environment-specific install paths.

### [F-803] Store contact data is duplicated across templates instead of being sourced from the managed location records

| Field | Value |
|---|---|
| Category | Code Quality |
| Subcategory | Template Source of Truth |
| Severity | Medium |
| Phase | Phase 8 - Frontend Assets & Static Files |
| Location | backend/templates/components/footer_website.html:49 |

Description: Public store names, addresses, phone numbers, email addresses, and WhatsApp contact details are repeated directly in multiple templates rather than being rendered from the admin-managed location/content sources.

Evidence: The website and shop footers hardcode Braga and Guimarães addresses, phone numbers, and `geral@biobrassica.pt`. WhatsApp numbers are also duplicated in footer templates and in the contacts page fallback. Meanwhile, the contacts page itself renders from `Location` records plus `DEFAULT_LOCATION_CONTENT` in the website views.

Impact: Operational contact changes must be updated in several unrelated templates to keep the public site consistent. That creates obvious drift risk between the contacts page, footers, and any admin-managed location data.

Recommendation: Render shared store/contact blocks from a single source of truth, ideally the active location records and centrally managed website content, instead of duplicating operational data in footer templates.

### [F-804] Marketing and legal fallback copy is scattered across templates and metadata blocks

| Field | Value |
|---|---|
| Category | Code Quality |
| Subcategory | Template Source of Truth |
| Severity | Medium |
| Phase | Phase 8 - Frontend Assets & Static Files |
| Location | backend/templates/website/home.html:73 |

Description: Public-facing CTA text, meta descriptions, and legal/business identity details are embedded directly across templates instead of being consistently driven by managed content or a shared configuration layer.

Evidence: The home CTA text falls back inside `website/home.html`; shop and website meta descriptions mention Braga and Guimarães directly in base templates; `catalog/shop_home.html` embeds contact CTAs and host links; `privacy.html` and `terms.html` hardcode company address, support email, and pickup wording. The website-content admin also describes missing sections as using a centralized fallback, but some of those live defaults actually come from scattered template literals and view-level constants rather than one managed source. These strings are therefore spread across multiple templates and code paths rather than unified behind website content or a central settings object.

Impact: Brand, compliance, and contact updates require manual edits across many templates, increasing the chance of stale public copy and inconsistent legal or operational messaging across pages. It also causes the admin summary to overstate how centralized the live fallback content really is.

Recommendation: Move repeated marketing/legal/contact copy into managed content or a centralized configuration layer, and keep templates focused on rendering shared data rather than embedding operational text repeatedly.

### [F-805] Frontend asset ownership is split between templates, ignored build outputs, and untracked source files

| Field | Value |
|---|---|
| Category | Deployment |
| Subcategory | Asset Build Contract |
| Severity | Medium |
| Phase | Phase 8 - Frontend Assets & Static Files |
| Location | backend/templates/base.html:13 |

Description: The public bases depend on generated CSS and custom navbar JavaScript, but the repository does not present a clear committed ownership contract for those assets.

Evidence: The base templates load `static 'css/output.css'` and `static 'js/navbar.js'`. `.gitignore` explicitly ignores `backend/static/css/output.css` and the collected `backend/staticfiles/` tree, while the current git index does not track `backend/static/js/navbar.js` even though the templates depend on it. That leaves runtime asset behavior split across template references, ignored build products, and locally present but untracked source files.

Impact: A deployment can appear correct in one environment because local generated or untracked assets exist, then fail or diverge elsewhere when those files are missing or built differently. This also makes code review and rollback less reliable because the effective frontend entrypoints are not fully represented in version control.

Recommendation: Define a single asset ownership contract: commit the source JS entrypoints, make generated CSS reproducible from committed inputs only, and ensure image/build pipelines never depend on ignored or untracked files being present on the deploy host.

## Audit Follow-up

This section records verified remediation work completed after the original audit snapshot.

### WebsiteContent Migration Incident

- Root cause: the website database schema in the affected environment was behind the code and missing migration `0008_websitecontent_company_details`, which adds `company_legal_name` and related fields.
- Deployment hardening: production web startup now runs `manage.py migrate --check --noinput` on the `gunicorn` path and exits early with an actionable error if migrations are pending.
- Documentation alignment: the deployment runbook and top-level README now state that migrations remain an explicit deploy step and that production web startup fails fast when schema changes are unapplied.
- CI and deploy validation: workflow smoke tests now invoke the real entrypoint on the `gunicorn --check-config` path so the migration guard is exercised during automation.
- Local verification: the running development stack has `website.0008` applied, `WebsiteContent.company_legal_name` is queryable through the ORM, and `/pt/`, `/en/`, and `/fr/` all return `200 OK`.
- Remaining operational action: any external environment that previously served the missing-column error must still run `python manage.py migrate --noinput` before restarting the production web container.