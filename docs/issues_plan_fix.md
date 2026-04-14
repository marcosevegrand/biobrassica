I'll start by reading the full audit findings document and the repository context files to understand every finding and the codebase architecture before designing the remediation plan.     

Read [](file:///home/marco/Projects/biobrassica/audit-findings.md#1-1), lines 1 to 200

Read memory architecture.md

Read memory admin.md

Read memory deployment.md

Read memory tooling.md

Read [](file:///home/marco/Projects/biobrassica/audit-findings.md#200-200), lines 200 to 500

Read [](file:///home/marco/Projects/biobrassica/audit-findings.md#500-500), lines 500 to 733

Good — I now have the full audit document. Now I need to deeply explore the specific code areas referenced by the findings so the fix instructions are concrete and accurate. I'll dispatch parallel subagents to cover the main clusters.   

Explore checkout/order/payment code

Explore catalog/content/admin models

Explore deployment/config/nginx/tests

Read [](file:///home/marco/Projects/biobrassica/backend/package.json)

Read [](file:///home/marco/Projects/biobrassica/backend/config/settings/base.py#1-1), lines 1 to 200

Read [](file:///home/marco/Projects/biobrassica/nginx/nginx.conf)

Read [](file:///home/marco/Projects/biobrassica/docker-compose.yml)

Read [](file:///home/marco/Projects/biobrassica/backend/Dockerfile)

Read [](file:///home/marco/Projects/biobrassica/backend/apps/orders/views.py)

Read [](file:///home/marco/Projects/biobrassica/backend/apps/cart/context_processors.py)

Read [](file:///home/marco/Projects/biobrassica/backend/apps/orders/services.py)

Read [](file:///home/marco/Projects/biobrassica/backend/apps/orders/models.py)

Read [](file:///home/marco/Projects/biobrassica/backend/apps/orders/forms.py)

Read [](file:///home/marco/Projects/biobrassica/backend/apps/payments/services.py)

Read [](file:///home/marco/Projects/biobrassica/backend/apps/payments/views.py)

Read [](file:///home/marco/Projects/biobrassica/backend/apps/payments/models.py)

Read [](file:///home/marco/Projects/biobrassica/backend/apps/cart/services.py)

Read [](file:///home/marco/Projects/biobrassica/backend/apps/catalog/models.py)

Read [](file:///home/marco/Projects/biobrassica/backend/apps/catalog/querysets.py)

Read [](file:///home/marco/Projects/biobrassica/backend/apps/catalog/admin.py#1-1), lines 1 to 600

Read [](file:///home/marco/Projects/biobrassica/backend/apps/content/models.py)

Read [](file:///home/marco/Projects/biobrassica/backend/apps/content/querysets.py)

Read [](file:///home/marco/Projects/biobrassica/backend/apps/content/admin.py)

Read [](file:///home/marco/Projects/biobrassica/backend/apps/website/models.py)

Read [](file:///home/marco/Projects/biobrassica/backend/apps/website/views.py)

Read [](file:///home/marco/Projects/biobrassica/backend/apps/website/admin.py)

Read [](file:///home/marco/Projects/biobrassica/backend/apps/accounts/admin.py)

Read [](file:///home/marco/Projects/biobrassica/backend/apps/core/admin_dashboard.py)

Read [](file:///home/marco/Projects/biobrassica/backend/apps/core/admin_helpers.py)

Read [](file:///home/marco/Projects/biobrassica/backend/config/settings/production.py)

Read [](file:///home/marco/Projects/biobrassica/docker-compose.dev.yml)

Read [](file:///home/marco/Projects/biobrassica/backend/docker-entrypoint.sh)

Read [](file:///home/marco/Projects/biobrassica/.gitignore)

Read [](file:///home/marco/Projects/biobrassica/scripts/backup.sh)

Searched for regex `class Product|is_active|stock` (`**/backend/apps/catalog/models.py`), 11 results

Read [](file:///home/marco/Projects/biobrassica/backend/apps/cart/models.py)

Searched for files matching `**/.github/workflows/**`, 2 matches

Read [](file:///home/marco/Projects/biobrassica/nginx/conf.d/biobrassica.conf)

Read [](file:///home/marco/Projects/biobrassica/nginx/conf.d/loja.conf)

Read [](file:///home/marco/Projects/biobrassica/nginx/conf.d/admin.conf)

Read [](file:///home/marco/Projects/biobrassica/.github/workflows/ci.yml)

Read [](file:///home/marco/Projects/biobrassica/.github/workflows/deploy.yml)

Searched for files matching `**/backend/static`, no matches

Read [](file:///home/marco/Projects/biobrassica/backend/templates/base.html)

Read [](file:///home/marco/Projects/biobrassica/backend/templates/base_website.html)

Read [](file:///home/marco/Projects/biobrassica/backend/templates/base_root.html)

Read [](file:///home/marco/Projects/biobrassica/backend/static)

Read [](file:///home/marco/Projects/biobrassica/backend/static/js)

Read [](file:///home/marco/Projects/biobrassica/backend/static/css)

Read [](file:///home/marco/Projects/biobrassica/backend/static/js/navbar.js#1-1), lines 1 to 100

Read [](file:///home/marco/Projects/biobrassica/backend/static/css/input.css#1-1), lines 1 to 100

Read [](file:///home/marco/Projects/biobrassica/backend/apps/core/translations.py#1-1), lines 1 to 150

Read [](file:///home/marco/Projects/biobrassica/backend/apps/orders/tests.py#1-1), lines 1 to 200

Read [](file:///home/marco/Projects/biobrassica/backend/apps/payments/tests.py#1-1), lines 1 to 200

Read [](file:///home/marco/Projects/biobrassica/backend/apps/cart/tests.py#1-1), lines 1 to 200

Read [](file:///home/marco/Projects/biobrassica/backend/config/settings/base.py#200-200), lines 200 to 250

Searched for files matching `**/backend/config/settings`, no matches

Read [](file:///home/marco/Projects/biobrassica/backend/config/settings)

Read [](file:///home/marco/Projects/biobrassica/backend/config/settings/development.py)

Compacted conversation

Read [](file:///home/marco/Projects/biobrassica/audit-findings.md#1-1), lines 1 to 250

Read [](file:///home/marco/.config/Code/User/workspaceStorage/2de3c258fa7316b4dbfe9bfb6627bdb6/GitHub.copilot-chat/chat-session-resources/43f86d8c-0c79-41d6-ac1d-ea6a69686163/toolu_bdrk_01BJ3gZXzRnehaU1KRgUugXX__vscode-1775569959759/content.txt#1-1), lines 1 to 500

Read [](file:///home/marco/.config/Code/User/workspaceStorage/2de3c258fa7316b4dbfe9bfb6627bdb6/GitHub.copilot-chat/chat-session-resources/43f86d8c-0c79-41d6-ac1d-ea6a69686163/toolu_bdrk_01GScaTVjJWQ3NSZ9erkpew9__vscode-1775569959760/content.txt#1-1), lines 1 to 500

Read [](file:///home/marco/.config/Code/User/workspaceStorage/2de3c258fa7316b4dbfe9bfb6627bdb6/GitHub.copilot-chat/chat-session-resources/43f86d8c-0c79-41d6-ac1d-ea6a69686163/toolu_bdrk_01SRpgU49BcGeSHTdeZz1vJw__vscode-1775569959761/content.txt)

Let me read the remaining audit findings and key code files I still need for precise fix instructions. 

Read [](file:///home/marco/Projects/biobrassica/audit-findings.md#250-250), lines 250 to 733

I now have deep code-level context for every finding. Let me write the comprehensive remediation plan. 

Created memory file [](file:///home/marco/.config/Code/User/workspaceStorage/2de3c258fa7316b4dbfe9bfb6627bdb6/GitHub.copilot-chat/memory-tool/memories/NDNmODZkOGMtMGM3OS00MWQ2LWFjMWQtZWE2YTY5Njg2MTYz/plan.md)

Deleted memory [](file:///home/marco/.config/Code/User/workspaceStorage/2de3c258fa7316b4dbfe9bfb6627bdb6/GitHub.copilot-chat/memory-tool/memories/NDNmODZkOGMtMGM3OS00MWQ2LWFjMWQtZWE2YTY5Njg2MTYz/plan.md)

Created memory file [](file:///home/marco/.config/Code/User/workspaceStorage/2de3c258fa7316b4dbfe9bfb6627bdb6/GitHub.copilot-chat/memory-tool/memories/NDNmODZkOGMtMGM3OS00MWQ2LWFjMWQtZWE2YTY5Njg2MTYz/plan.md)

Here is the full remediation plan.

---

## Plan: Remediate All 36 Audit Findings

Fix every finding from the audit in **9 dependency-ordered phases**. Phase 1 fixes the only **High** severity issue (checkout bypasses stock safety). Phases 2–8 address Medium/Low findings grouped by domain and dependency. Phase 9 fills testing gaps. Each phase is independently verifiable and deployable.

---

## Phase 1 — Checkout Pipeline Safety (HIGH PRIORITY)

*Fixes: **F-201**, **F-202**, **F-402**. Depends on: nothing. Blocks: Phase 3, Phase 9.*

### Step 1.1 — Route checkout through `create_order_from_cart()` [F-201]

**Root cause**: `checkout_confirm()` (views.py) manually creates Order + OrderItems inline instead of calling `create_order_from_cart()` (services.py), which wraps everything in `transaction.atomic()`, uses `select_for_update()`, validates stock+active status, and decrements inventory.

**Fix**:
- Refactor `checkout_confirm()` to call `create_order_from_cart(cart, form.cleaned_data, lang)` instead of direct `Order.objects.create()` + loop.
- Adjust `create_order_from_cart()` signature if needed to accept full checkout form data (name, email, phone, fulfillment fields, notes).
- Remove inline Order/OrderItem creation and cart clearing from the view — the service handles it atomically.
- Handle `StockValidationError` in the view: re-render checkout form with stock error messages, call `adjust_cart_items_for_stock()`.

**Files**: orders/views.py (~L107–177), orders/services.py (~L78–184)

**Tests**: (1) Checkout with insufficient stock returns form error, no order created. (2) Checkout with deactivated product returns form error.

### Step 1.2 — Wrap Stripe session creation in recovery flow [F-202]

**Root cause**: The view creates Order/Payment, clears cart, *then* calls Stripe — if Stripe fails, the cart is gone and the order is orphaned.

**Fix** (preferred approach): Create the Stripe session **before** clearing the cart. Only clear the cart after a successful session link. If the service creates the order atomically (Step 1.1), keep cart clearing as a separate post-service step that only commits after Stripe succeeds. On Stripe failure: cancel the order via `cancel_unpaid_order()` and redirect to cart (still intact).

**Files**: orders/views.py (~L149–169)

**Tests**: (1) Stripe failure does not delete cart items. (2) Stripe failure does not leave order in `payment_pending`.

### Step 1.3 — Filter inactive products from cart and checkout [F-402]

**Root cause**: `get_cart_items_queryset()` (services.py) does no `is_active` filtering. `add_product_to_cart()` (~L52) also doesn't check.

**Fix**:
- Add `.filter(product__is_active=True)` to `get_cart_items_queryset()`.
- Add an `is_active` guard in `add_product_to_cart()` — return error if product is inactive.
- In cart detail view, display a message when items were silently removed.

**Files**: cart/services.py (~L21, ~L52)

**Tests**: (1) Deactivated product disappears from cart queryset. (2) Adding inactive product fails.

---

## Phase 2 — Security Hardening (*parallel with Phase 1*)

*Fixes: **F-101**, **F-102**, **F-103**, **F-104**. Depends on: nothing. Blocks: Phase 8 (F-602).*

### Step 2.1 — Fix nginx to set X-Forwarded-Proto authoritatively [F-102]

**Root cause**: nginx.conf passes `$http_x_forwarded_proto` (client-supplied) instead of setting it.

**Fix**: Change to `proxy_set_header X-Forwarded-Proto https;` hardcoded — all production traffic must come through Cloudflare TLS. Dev doesn't use production settings (`SECURE_SSL_REDIRECT=False`).

**Files**: nginx.conf L31

### Step 2.2 — Move guest order tokens out of query strings [F-101]

**Root cause**: `_order_url()` (views.py) puts `?token=...` in URLs. `_get_order_for_request()` reads from `GET`.

**Fix**: On first verified visit with valid token, bind order access to the session (`request.session[f'order_{pk}_verified'] = True`). Strip the token from the URL via redirect. Change `_get_order_for_request()` to check session first, then POST only. Stripe success/cancel URLs keep the token (Stripe needs it) but the receiving view does a one-time exchange into session then redirects clean.

**Files**: orders/views.py — `_order_url()`, `_get_order_for_request()`, `payment_status()`, `order_complete()`

**Tests**: (1) After initial token verification, session-based access works without token. (2) GET-only token is rejected after first exchange.

### Step 2.3 — Remove access_token from Stripe metadata [F-104]

**Root cause**: `create_checkout_session()` (services.py) includes `access_token` in metadata.

**Fix**: Remove the `access_token` key from the metadata dict. Webhook handler uses `session_id`/`payment_intent_id` for lookup — no dependency.

**Files**: payments/services.py (~L295)

### Step 2.4 — Add Content-Security-Policy headers [F-103]

**Fix**: Add CSP headers in each nginx vhost config, differentiated per subdomain. Start with `Content-Security-Policy-Report-Only` to avoid breakage, then enforce after monitoring.

- **Website** (biobrassica.conf): Allow `fonts.googleapis.com`, `fonts.gstatic.com`, `static.elfsight.com`, `google.com/maps`
- **Shop** (loja.conf): Allow `unpkg.com` (HTMX), `js.stripe.com`, `api.stripe.com`, fonts
- **Admin** (admin.conf): `'self'` + `'unsafe-inline'` for Unfold admin scripts, fonts

**Files**: biobrassica.conf, loja.conf, admin.conf

---

## Phase 3 — Payment State Machine Fixes

*Fixes: **F-203**, **F-204**, **F-205**, **F-206**. Depends on: Phase 1. Blocks: Phase 5.*

### Step 3.1 — Use service for expiry in polling view [F-203]

**Root cause**: `payment_status()` (views.py) directly mutates `payment.status = EXPIRED` instead of calling `expire_pending_payment()`.

**Fix**: Replace inline `payment.status = Payment.Status.EXPIRED; payment.save(...)` with `expire_pending_payment(payment, reason='stripe checkout expired (poll)')`. This also transitions the order back to `pending`.

**Files**: orders/views.py ~L257

### Step 3.2 — Make webhook deduplication atomic [F-204]

**Root cause**: `stripe_callback()` (views.py) does `filter().first()` then `create()` — race window.

**Fix**: Replace with `PaymentCallback.objects.get_or_create(provider_event_id=event_id, defaults={...})`. If `created=False`, return early. Add `try/except IntegrityError` as safety net.

**Files**: payments/views.py ~L56–72

### Step 3.3 — Define refund → order state reconciliation [F-205]

**Root cause**: `mark_payment_refunded()` only transitions Payment.status; Order stays in `paid`/`preparing`/etc.

**Fix**:
- Extend `mark_payment_refunded()` to also transition the order:
  - `paid` → `cancelled` (auto)
  - `preparing`/`ready` → flag for manual review (add refund note, don't auto-cancel)
  - `delivered` → no order change (post-delivery financial adjustment)
- Update `VALID_TRANSITIONS` in orders/models.py to allow `paid → cancelled`.

**Files**: payments/services.py, orders/models.py (~L18–25)

**Tests**: (1) Refund on `paid` order → order becomes `cancelled`. (2) Refund on `preparing` order → flagged, not auto-cancelled.

### Step 3.4 — Set local expiry deadline on payments [F-206]

**Root cause**: `configure_stripe_checkout()` sets `payment.expires_at = None`. No background cleanup runs `expire_stale_pending_payments()`.

**Fix**:
- Set `payment.expires_at = timezone.now() + timedelta(hours=1)` after Stripe session creation in `checkout_confirm()`.
- Create management command `expire_stale_payments` that calls the existing `expire_stale_pending_payments()`.
- Document cron: `*/15 * * * * docker compose exec django python manage.py expire_stale_payments`.

**Files**: orders/views.py, `backend/apps/payments/management/commands/expire_stale_payments.py` (new)

---

## Phase 4 — Domain Model Integrity (*parallel with Phase 3*)

*Fixes: **F-301**, **F-302**, **F-303**, **F-304**, **F-305**. Depends on: Phase 1.*

### Step 4.1 — Primary image uniqueness constraint [F-304]

**Fix**: Add `UniqueConstraint(fields=['product'], condition=Q(is_primary=True), name='unique_primary_image_per_product')` to `ProductImage.Meta.constraints`. Data migration to deduplicate existing rows (keep first by `order` field).

**Files**: catalog/models.py ~L210–225, new migration

### Step 4.2 — Website content DB-level singleton [F-303]

**Fix**: Override `save()` to force `self.pk = 1`. Add check constraint or override `id` field to `PositiveIntegerField(primary_key=True, default=1)`.

**Files**: website/models.py ~L46–87, new migration

### Step 4.3 — Move publication blockers to model validation [F-302]

**Fix**: Add `clean()` to `BlogPost` and `Recipe` that enforces: when `is_published=True`, must have PT translation (+ cover image for blog, + ingredients/instructions for recipe). Admin methods can delegate to `model.full_clean()`.

**Files**: content/models.py (~L13–51 BlogPost, ~L77–153 Recipe), content/admin.py

### Step 4.4 — Align storefront language fallback policy [F-305]

**Recommended approach**: Use PT fallback in storefront queries — consistent with admin readiness rules and translation system.

**Fix**: Remove `translations__language=normalized_lang` filter from `active_product_queryset()` (querysets.py). Keep `is_active=True` as the only hard filter. The prefetch + `select_translation()` handles language fallback at render time.

**Files**: catalog/querysets.py ~L14–24

### Step 4.5 — Validate pickup location against product availability [F-301]

**Fix**: In `CheckoutForm.clean()`, when `fulfillment_method == PICKUP`, verify the selected location is in the intersection of all cart products' `available_locations`. Requires passing cart items to the form.

**Files**: orders/forms.py, orders/views.py (pass cart items to form)

---

## Phase 5 — Admin Workflow Alignment

*Fixes: **F-501**, **F-502**, **F-503**, **F-505**, **F-506**. Depends on: Phase 3 (refund reconciliation), Phase 4 (model invariants).*

### Step 5.1 — Remove changelist publish toggle bypass [F-501]

**Fix**: Remove `'is_published'` from `list_editable` in `BlogPostAdmin` (admin.py) and `RecipeAdmin`. Publication only through guarded change-form actions (which now call `model.clean()` per Phase 4).

### Step 5.2 — Unify product readiness rules [F-502]

**Fix**: Add readiness check to `Product.clean()` that prevents `is_active=True` without: `stock > 0`, PT translation, one primary image, ≥1 available location. Refactor `_can_reactivate_product()` and ops_queue filters to reuse same logic. Remove `is_active` from `list_editable` or override `save_model()` to enforce readiness.

**Files**: catalog/models.py, catalog/admin.py (~L459, ~L340–362)

### Step 5.3 — Fix dashboard to account for refund state [F-503]

**Fix**: After Phase 3 Step 3.3, refunded `paid` orders auto-cancel (drop out of counts). For in-progress refunds: add `.exclude(payments__status='refunded')` to `paid_orders` and `todays_pickups` queries.

**Files**: core/admin_dashboard.py (~L84–118)

### Step 5.4 — Filter customer revenue by realized payments [F-505]

**Fix**: Update `lifetime_revenue` annotation to: `Sum('orders__total', filter=Q(orders__status__in=['paid','preparing','ready','delivered']) & ~Q(orders__payments__status='refunded'), distinct=True)`.

**Files**: accounts/admin.py (~L50–54)

### Step 5.5 — Derive checkout options from active records [F-506]

**Fix**: Build `CheckoutForm` pickup_location choices dynamically from `Location.objects.filter(is_active=True)`. Validate in `clean()` against active records. Full FK migration from enum to Location is a follow-up.

**Files**: orders/forms.py, orders/views.py

---

## Phase 6 — Templates & Content Source of Truth (*parallel with Phase 5*)

*Fixes: **F-401**, **F-803**, **F-804**.*

### Step 6.1 — Replace hardcoded production URLs [F-401]

**Fix**: Create a template tag or context processor providing `shop_url` for the current environment. Add `SHOP_DOMAIN` setting. Replace all `https://loja.biobrassica.pt/...` in templates.

**Files**: New `backend/apps/core/templatetags/shop_urls.py`, recipe_detail.html, navbar/footer components, home.html, agriculture.html, base.py

### Step 6.2 — Render contact data from managed records [F-803]

**Fix**: Create a context processor providing active locations. Replace hardcoded address/phone/email in footer templates with template loops.

**Files**: New context processor, footer_website.html

### Step 6.3 — Centralize marketing/legal copy [F-804]

**Fix**: Add company details fields to `WebsiteContent` model (address, NIF, support email). Replace scattered template literals with managed content references. Privacy/terms pages pull from managed content.

**Files**: website/models.py, home.html, template updates

---

## Phase 7 — Frontend Assets & Build (*independent*)

*Fixes: **F-801**, **F-802**, **F-805**.*

### Step 7.1 — Standardize Tailwind toolchain [F-802]

**Fix**: Update Dockerfile standalone binary from v4.1.8 to v4.2.2 (matching package.json).

### Step 7.2 — Commit source JS, define asset contract [F-805]

**Fix**: Ensure navbar.js is tracked in git. Add `backend/static/README.md` documenting source vs generated assets.

### Step 7.3 — Self-host critical frontend assets [F-801]

**Fix**: Download HTMX 2.0.4 to `backend/static/js/htmx.min.js`. Download Inter/Lora WOFF2 to `backend/static/fonts/`. Add local `@font-face` declarations in input.css. Update base.html references. Isolate Elfsight embed with graceful degradation.

---

## Phase 8 — Deployment & Configuration

*Fixes: **F-601**, **F-602**, **F-603**, **F-604**. Depends on: Phase 2 (nginx fix).*

### Step 8.1 — Fix health check [F-602]

**Fix**: Add `SECURE_REDIRECT_EXEMPT = [r'^_health/']` to production.py. Remove spoofed header from docker-compose.yml healthcheck.

### Step 8.2 — Centralize domain config [F-601]

**Fix**: Derive `CSRF_TRUSTED_ORIGINS` from `ALLOWED_HOSTS` in production.py: `[f'https://{h}' for h in ALLOWED_HOSTS if h != '*']`. Document nginx server_name change procedure in deployment.md.

### Step 8.3 — Parameterize backup script [F-603]

**Fix**: Use `${DB_NAME:-biobrassica}`, `${DB_USER:-biobrassica}`, `${COMPOSE_PROJECT_NAME:-biobrassica}` in backup.sh. Source .env if present.

### Step 8.4 — Separate migrations from startup [F-604]

**Fix**: Remove `migrate` from docker-entrypoint.sh. Add explicit `docker compose run --rm django python manage.py migrate` in deploy.yml before `up -d`. Keep `collectstatic`/`compilemessages` in entrypoint (idempotent, needed per container).

---

## Phase 9 — Regression Test Suite

*Fixes: **F-701**, **F-702**, **F-703**, **F-704**, **F-705**. Depends on: all previous phases.*

| Step | Finding | What to add |
|---|---|---|
| 9.1 | F-701 | Expand CI to `python manage.py test apps/` (all suites) |
| 9.2 | F-703 | Cart drift tests: deactivate product → assert excluded from cart; checkout rejects |
| 9.3 | F-704 | Refund regression: webhook → order cancelled; excluded from dashboard; excluded from revenue |
| 9.4 | F-702 | Deployment smoke: build prod image + run entrypoint in CI; backup script dry-run |
| 9.5 | F-705 | Playwright cart popup tests (lowest priority, deferrable) |

---

## Verification (Per-Phase)

1. **Phase 1**: `python manage.py test apps.orders apps.cart` — insufficient stock blocks checkout, inactive products excluded from cart, Stripe failure preserves cart
2. **Phase 2**: Manual nginx test + browser CSP console check + guest URL contains no token after first visit
3. **Phase 3**: `python manage.py test apps.payments apps.orders` — poll expiry transitions both models, duplicate webhook returns 200, refund cancels paid order
4. **Phase 4**: `python manage.py test apps.catalog apps.content apps.website` — duplicate primary image blocked, singleton enforced, publish without PT blocked, EN storefront shows PT-fallback products
5. **Phase 5**: `python manage.py test apps.catalog apps.content apps.accounts apps.orders` — changelist can't publish, revenue excludes cancelled, checkout rejects deactivated locations
6. **Phase 6**: `grep -r 'loja.biobrassica.pt' backend/templates/` returns zero matches; footers render from Location data
7. **Phase 7**: Compare dev vs prod `output.css` — identical; htmx.min.js served locally
8. **Phase 8**: `docker compose up` starts without running migrations; health check works without spoofed header; backup script uses env vars
9. **Phase 9**: `python manage.py test apps/` passes in CI with full suite

## Decisions

- **Language fallback (F-305)**: PT fallback in storefront queries (consistent with rest of app). Alternative: strict per-language completeness (higher content burden).
- **Checkout location model (F-506)**: Form-level validation first. Full FK migration from enum to Location deferred.
- **Browser tests (F-705)**: Lowest priority, deferrable.
- **Refund order state (F-205)**: `paid` → auto-cancel; `preparing`/`ready` → flag only; `delivered` → no change.
- **Singleton pattern (F-303)**: `pk=1` override (simplest, battle-tested in Django).