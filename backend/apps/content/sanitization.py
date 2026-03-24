import re

import bleach


ALLOWED_TAGS = [
    'a',
    'blockquote',
    'br',
    'em',
    'figcaption',
    'figure',
    'h2',
    'h3',
    'h4',
    'hr',
    'img',
    'li',
    'ol',
    'p',
    'strong',
    'ul',
]

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'rel', 'target', 'title'],
    'img': ['alt', 'src', 'title'],
}

ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']

DISALLOWED_BLOCK_TAGS_RE = re.compile(
    r'<\s*(script|style|iframe|object|embed)[^>]*>.*?<\s*/\s*\1\s*>',
    re.IGNORECASE | re.DOTALL,
)


def sanitize_html(value: str) -> str:
    if not value:
        return ''

    value = DISALLOWED_BLOCK_TAGS_RE.sub('', value)

    cleaned = bleach.clean(
        value,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
        strip_comments=True,
    )
    return bleach.linkify(cleaned, skip_tags=['pre', 'code'])