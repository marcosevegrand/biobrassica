# Biobrassica — Website

Static website for Biobrassica. Plain HTML, CSS and JavaScript — no runtime build,
server-side code or database. It can be served from any static host, including GitHub Pages.

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
css/                    compiled utilities + shared design system
js/navbar.js            mobile menu and navbar scroll behaviour
images/                 brand, people, products, arts, certs, shop
videos/                 promo video
fonts/                  Lora + Inter webfonts
scripts/                responsive image generation and static validation
tailwind.config.cjs     utility CSS generation settings
robots.txt              crawler rules
.nojekyll               tells GitHub Pages not to run Jekyll
```

Styling uses a checked-in, locally compiled `css/utilities.css` and the shared
design system in `css/biobrassica-overrides.css`. No CDN or compilation is needed
to preview or deploy the website. All fonts and images are hosted locally.

After changing utility classes in HTML or JavaScript, regenerate the CSS:

```bash
npx --yes tailwindcss@3.4.17 -i css/tailwind.css -o css/utilities.css --minify
```

The configuration is in `tailwind.config.cjs`. Commit the generated CSS alongside
your changes. Responsive image variants can be regenerated using Pillow:

```bash
python3 scripts/generate-images.py
```

Check local links, image dimensions and page conventions with:

```bash
python3 scripts/check-site.py
```

Maps are embedded directly in the contact page and load automatically, including
without JavaScript. The mobile menu supports Escape, outside clicks, expanded
state announcements and breakpoint changes. Animations respect reduced motion.

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
4. If using a custom domain, configure it in **Settings → Pages** and point its
   DNS at GitHub Pages as described in the GitHub Pages documentation. This
   repository does not currently include a `CNAME` file.

`404.html` is used by GitHub Pages for unknown paths. It injects a `<base>` tag at
runtime so its relative asset paths resolve correctly both from a project subpath
(`user.github.io/repo/`) and from a domain root (custom domain or `user.github.io`).

## Notes

- The former Laravel application, Filament admin panel, database and the shop/catalog
  code have been removed. Content is now static.
- The Blog and Receitas sections were database-driven and empty; they have been removed
  along with their navigation links.
- The footer copyright year is filled in at runtime by a one-line script, so it stays
  current without a build step.
