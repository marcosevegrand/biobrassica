"""Validate local links, image metadata and shared static-page conventions."""
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
errors = []


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.ids = Counter()
        self.links = []
        self.headings = 0
        self.feed(path.read_text())

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids[attrs['id']] += 1
        if tag == 'h1':
            self.headings += 1
        if tag == 'img':
            for required in ('alt', 'width', 'height'):
                if required not in attrs:
                    errors.append(f'{self.path.name}: image missing {required}: {attrs.get("src")}')
            for candidate in attrs.get('srcset', '').split(','):
                if candidate.strip():
                    self.links.append(candidate.strip().split()[0])
        if tag == 'iframe' and not attrs.get('title'):
            errors.append(f'{self.path.name}: iframe missing accessible title')
        for attribute in ('href', 'src', 'poster'):
            if attribute in attrs:
                self.links.append(attrs[attribute])


pages = {path.name: Page(path) for path in ROOT.glob('*.html')}
for name, page in pages.items():
    if page.headings != 1:
        errors.append(f'{name}: expected exactly one h1')
    for required in ('conteudo', 'site-header', 'mobile-menu', 'mobile-menu-btn'):
        if page.ids[required] != 1:
            errors.append(f'{name}: missing or duplicate {required}')
    for identifier, count in page.ids.items():
        if count > 1:
            errors.append(f'{name}: duplicate id {identifier}')
    for link in page.links:
        url = urlsplit(link)
        if url.scheme or url.netloc:
            continue
        target = ROOT / unquote(url.path) if url.path else page.path
        if not target.exists():
            errors.append(f'{name}: missing local target {link}')
        elif url.fragment and target.name in pages and url.fragment not in pages[target.name].ids:
            errors.append(f'{name}: missing anchor {link}')
    if 'cdn.tailwindcss.com' in page.path.read_text():
        errors.append(f'{name}: runtime Tailwind CDN dependency')

if errors:
    raise SystemExit('\n'.join(errors))
print(f'OK: {len(pages)} pages, local links, image dimensions and shared landmarks.')
