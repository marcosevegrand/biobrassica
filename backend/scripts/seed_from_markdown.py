"""
Seed Django database from existing Astro markdown content files.

Usage:
    cd loja/
    source .venv/bin/activate
    python manage.py shell < scripts/seed_from_markdown.py
"""
import re
import os
from decimal import Decimal, InvalidOperation
from pathlib import Path

import django

# Ensure Django is set up
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.catalog.models import Category, CategoryTranslation, Product, ProductTranslation  # noqa: E402

# Use manage.py location to find project root
LOJA_DIR = Path(os.environ.get('MANAGE_PY_DIR', Path.cwd()))
SITE_DIR = LOJA_DIR.parent / 'site'

# Fallback: if running from loja/ itself
if not SITE_DIR.exists():
    SITE_DIR = LOJA_DIR / '..' / 'site'
    SITE_DIR = SITE_DIR.resolve()

PRODUCTS_DIR = SITE_DIR / 'src' / 'content' / 'products'
CATEGORIES_DIR = SITE_DIR / 'src' / 'content' / 'categories'


def parse_frontmatter(filepath):
    """Parse YAML-like frontmatter from a markdown file."""
    text = filepath.read_text(encoding='utf-8')
    match = re.match(r'^---\s*\n(.*?)\n---', text, re.DOTALL)
    if not match:
        return {}

    data = {}
    for line in match.group(1).split('\n'):
        line = line.strip()
        if ':' not in line or line.startswith('#'):
            continue

        key, _, value = line.partition(':')
        key = key.strip()
        value = value.strip()

        # Remove quotes
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]

        # Handle arrays (before booleans since arrays contain strings)
        if isinstance(value, str) and value.startswith('[') and value.endswith(']'):
            items = value[1:-1].split(',')
            value = [i.strip().strip('"').strip("'") for i in items if i.strip()]
        # Handle booleans
        elif isinstance(value, str) and value.lower() == 'true':
            value = True
        elif isinstance(value, str) and value.lower() == 'false':
            value = False

        data[key] = value

    return data


def parse_price(price_display):
    """Extract numeric price from display string like '6,80€ / 500g'."""
    if not price_display:
        return Decimal('0.00'), 'un'

    # Find the price part
    price_match = re.search(r'([\d,]+)\s*€', str(price_display))
    if price_match:
        price_str = price_match.group(1).replace(',', '.')
        try:
            price = Decimal(price_str)
        except InvalidOperation:
            price = Decimal('0.00')
    else:
        price = Decimal('0.00')

    # Find the unit part
    unit_match = re.search(r'/\s*(.+)$', str(price_display))
    unit = unit_match.group(1).strip() if unit_match else 'un'

    return price, unit


def seed_categories():
    """Import categories from markdown files."""
    if not CATEGORIES_DIR.exists():
        print(f"Categories directory not found: {CATEGORIES_DIR}")
        return

    count = 0
    for filepath in CATEGORIES_DIR.glob('*.md'):
        data = parse_frontmatter(filepath)
        if not data.get('key'):
            continue

        slug = data['key']
        lang = data.get('lang', 'pt')
        name = data.get('name', slug)
        order = int(data.get('order', 0)) if data.get('order') else 0

        category, created = Category.objects.get_or_create(
            slug=slug,
            defaults={'order': order},
        )

        CategoryTranslation.objects.update_or_create(
            category=category,
            language=lang,
            defaults={'name': name},
        )

        count += 1
        if created:
            print(f"  Created category: {slug}")
        else:
            print(f"  Updated category translation: {slug} ({lang})")

    print(f"Processed {count} category files.")


def seed_products():
    """Import products from markdown files."""
    if not PRODUCTS_DIR.exists():
        print(f"Products directory not found: {PRODUCTS_DIR}")
        return

    count = 0
    for filepath in PRODUCTS_DIR.glob('*.md'):
        data = parse_frontmatter(filepath)
        if not data.get('title'):
            continue

        lang = data.get('lang', 'pt')
        title = data['title']
        category_name = data.get('category', '')
        price_display = data.get('priceDisplay', '')
        is_highlight = data.get('isHighlight', False)
        locations = data.get('locations', [])
        if isinstance(locations, str):
            locations = [locations]

        price, unit = parse_price(price_display)

        # Generate slug from filename
        slug = filepath.stem

        # Find or create category
        category = None
        if category_name:
            cat_trans = CategoryTranslation.objects.filter(name=category_name).first()
            if cat_trans:
                category = cat_trans.category
            else:
                cat_slug = re.sub(r'[^a-z0-9]+', '-', category_name.lower()).strip('-')
                category, _ = Category.objects.get_or_create(slug=cat_slug)
                CategoryTranslation.objects.get_or_create(
                    category=category,
                    language=lang,
                    defaults={'name': category_name},
                )

        if not category:
            category, _ = Category.objects.get_or_create(slug='outros')
            CategoryTranslation.objects.get_or_create(
                category=category, language='pt',
                defaults={'name': 'Outros'},
            )

        # Create or find product (use a base slug without lang suffix for matching)
        base_slug = re.sub(r'-(pt|en|fr)$', '', slug)
        product = Product.objects.filter(slug=base_slug).first()

        if not product:
            product, created = Product.objects.get_or_create(
                slug=base_slug,
                defaults={
                    'category': category,
                    'price': price,
                    'quantity': unit or '1 un',
                    'stock': 10,
                    'is_highlight': bool(is_highlight),
                    'available_locations': locations,
                    'brand': 'Biobrassica',
                    'bio_code': 'PT-BIO-03',
                },
            )
            if created:
                print(f"  Created product: {base_slug}")

        ProductTranslation.objects.update_or_create(
            product=product,
            language=lang,
            defaults={
                'name': title,
                'description': title,
                'allergens': 'Informação não disponível.',
                'ingredients': 'Informação não disponível.',
            },
        )

        count += 1

    print(f"Processed {count} product files.")


if __name__ == '__main__' or True:
    print("=== Seeding Categories ===")
    seed_categories()
    print()
    print("=== Seeding Products ===")
    seed_products()
    print()
    print("Done!")
