import re

from django.utils.html import escape
from django.utils.safestring import mark_safe

from apps.content.sanitization import sanitize_html


_BOLD_RE = re.compile(r'\*\*(.+?)\*\*')
_ITALIC_RE = re.compile(r'(?<!\*)\*(.+?)\*(?!\*)')
_LINK_RE = re.compile(r'\[(.+?)\]\((https?://[^\s)]+)\)')
_ANY_LINK_RE = re.compile(r'\[(.+?)\]\(([^\s)]+)\)')


def _render_inline(text: str) -> str:
    escaped = escape(text)
    escaped = _LINK_RE.sub(r'<a href="\2">\1</a>', escaped)
    escaped = _ANY_LINK_RE.sub(r'\1', escaped)
    escaped = _BOLD_RE.sub(r'<strong>\1</strong>', escaped)
    escaped = _ITALIC_RE.sub(r'<em>\1</em>', escaped)
    return escaped


def render_markdown(value: str):
    text = str(value or '').strip()
    if not text:
        return mark_safe('')

    blocks = []
    list_items: list[str] = []

    def flush_list():
        nonlocal list_items
        if list_items:
            blocks.append('<ul>' + ''.join(f'<li>{item}</li>' for item in list_items) + '</ul>')
            list_items = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            flush_list()
            continue

        if line.startswith('- '):
            list_items.append(_render_inline(line[2:].strip()))
            continue

        flush_list()

        if line.startswith('### '):
            blocks.append(f'<h3>{_render_inline(line[4:])}</h3>')
        elif line.startswith('## '):
            blocks.append(f'<h2>{_render_inline(line[3:])}</h2>')
        elif line.startswith('# '):
            blocks.append(f'<h1>{_render_inline(line[2:])}</h1>')
        else:
            blocks.append(f'<p>{_render_inline(line)}</p>')

    flush_list()
    return mark_safe(sanitize_html(''.join(blocks)))
