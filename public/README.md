# Static Asset Contract

This directory mixes source assets and generated assets used by Django.

Source assets:
- `css/input.css`: Tailwind source plus local font declarations.
- `js/navbar.js`: shared navigation behaviour.
- `js/product_list.js`: product-list interactions.
- `js/htmx.min.js`: vendored HTMX runtime used by shop templates.
- `js/instagram-feed.js`: lazy loader and fallback handler for the external Instagram widget.
- `fonts/`: self-hosted webfont binaries referenced by `css/input.css`.
- `images/`, `img/`, `videos/`: source media referenced directly by templates.

Generated asset:
- `css/output.css`: compiled Tailwind bundle generated from `css/input.css`.

Build contract:
- When `css/input.css` changes, rebuild `css/output.css` before shipping.
- Vendored third-party files should stay pinned to explicit versions and only be replaced intentionally.