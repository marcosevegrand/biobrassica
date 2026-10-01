# Biobrassica — Website

Static website for Biobrassica. Plain HTML, CSS and JavaScript — no build step, no
server-side code. It can be served from any static host, including GitHub Pages.

## Pages

| File | URL (custom domain) |
| --- | --- |
| `index.html` | `/` |
| `quem-somos.html` | `/quem-somos.html` |
| `agricultura-bio.html` | `/agricultura-bio.html` |
| `contactos.html` | `/contactos.html` |
| `privacidade.html` | `/privacidade.html` |
| `termos.html` | `/termos.html` |
| `404.html` | not-found page (served automatically by GitHub Pages) |

## Structure

```
index.html, *.html      the pages
404.html                not-found page
CNAME                   custom domain for GitHub Pages (biobrassica.pt)
css/                    biobrassica-overrides.css (fonts, prose, custom utilities)
js/navbar.js            mobile menu and navbar scroll behaviour
images/                 brand, people, products, arts, certs, shop
videos/                 promo video
fonts/                  Lora + Inter webfonts
robots.txt              crawler rules
.nojekyll               tells GitHub Pages not to run Jekyll
```

Styling is done with the Tailwind CSS Play CDN (`https://cdn.tailwindcss.com`) plus
`css/biobrassica-overrides.css`. No compilation is required.

## The shop

The shop is hosted separately at **<https://biobrassica.pt/loja>**. All "Loja" links
and CTAs on the site (navbar, footer, home and agriculture pages) point there.

## Local preview

Any static file server works, for example:

```bash
python3 -m http.server 8080
```

Then open <http://localhost:8080>.

## Deploying to GitHub Pages

1. Push this repository to GitHub.
2. In the repository, go to **Settings → Pages**.
3. Under **Build and deployment**, choose **Deploy from a branch**, select the branch
   (e.g. `main`) and the **`/` (root)** folder, then save.
3. The custom domain is already configured via the `CNAME` file at the repository
   root (containing `biobrassica.pt`). Just make sure the domain's DNS is pointed at
   GitHub Pages as described in the GitHub Pages documentation.

`404.html` is used by GitHub Pages for unknown paths. Note that it references assets
with root-relative paths (`/images/...`), which requires the site to be served from the
domain root (custom domain or `user.github.io`). If you host it under a project
subpath (`user.github.io/repo/`), update those paths in `404.html`.

## Notes

- The former Laravel application, Filament admin panel, database and the shop/catalog
  code have been removed. Content is now static.
- The Blog and Receitas sections were database-driven and empty; they have been removed
  along with their navigation links.
- The footer copyright year is filled in at runtime by a one-line script, so it stays
  current without a build step.
