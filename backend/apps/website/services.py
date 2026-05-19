import json
import logging
import re
from datetime import datetime, timezone

import requests

logger = logging.getLogger(__name__)

INSTAGRAM_USERNAME = 'biobrassica'
USER_AGENT = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
)
REQUEST_TIMEOUT = 30


def fetch_instagram_posts(username=INSTAGRAM_USERNAME, count=5):
    url = f'https://www.instagram.com/{username}/'
    headers = {
        'User-Agent': USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
    }

    try:
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning('Failed to fetch Instagram profile: %s', exc)
        return []

    html = resp.text
    posts = _extract_posts_from_html(html, count)

    if not posts:
        logger.warning('No posts found in Instagram profile page for @%s', username)
    else:
        logger.info('Found %d posts for @%s', len(posts), username)

    return posts


def _extract_posts_from_html(html, count):
    """Try multiple methods to extract post data from Instagram's profile HTML."""

    for method in (_try_shared_data, _try_next_data, _try_ld_json, _try_regex):
        posts = method(html, count)
        if posts:
            return posts

    return []


def _try_shared_data(html, count):
    """Extract from window._sharedData embedded JSON."""
    match = re.search(
        r'<script[^>]*>\s*window\._sharedData\s*=\s*({.*?});\s*</script>',
        html,
        re.DOTALL,
    )
    if not match:
        return []

    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        return []

    user = (
        data.get('entry_data', {})
        .get('ProfilePage', [{}])[0]
        .get('graphql', {})
        .get('user', {})
    )
    return _extract_timeline_media(user, count)


def _try_next_data(html, count):
    """Extract from __NEXT_DATA__ JSON (Next.js pattern)."""
    match = re.search(
        r'<script[^>]*id="__NEXT_DATA__"[^>]*type="application/json"[^>]*>(.*?)</script>',
        html,
        re.DOTALL,
    )
    if not match:
        return []

    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        return []

    user = (
        data.get('props', {})
        .get('pageProps', {})
        .get('user', {})
    )
    return _extract_timeline_media(user, count)


def _try_ld_json(html, count):
    """Extract from application/ld+json structured data."""
    posts = []
    for match in re.finditer(
        r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
        html,
        re.DOTALL,
    ):
        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue

        if not isinstance(data, (dict, list)):
            continue

        items = data if isinstance(data, list) else [data]
        for item in items:
            if item.get('@type') in ('ImageObject', 'SocialMediaPosting'):
                instagram_id = _shortcode_from_url(item.get('@id', '') or item.get('url', ''))
                if instagram_id:
                    posts.append({
                        'instagram_id': instagram_id,
                        'image_url': item.get('thumbnailUrl', '') or item.get('contentUrl', ''),
                        'caption': item.get('caption', '') or item.get('description', '') or '',
                        'permalink': item.get('@id', '') or item.get('url', ''),
                        'posted_at': _parse_date(item.get('datePublished', '')),
                    })
                if len(posts) >= count:
                    return posts

    return posts


def _try_regex(html, count):
    """Last-resort: regex search for shortcode and display_url patterns."""
    shortcodes = re.findall(r'"shortcode"\s*:\s*"([^"]+)"', html)
    urls = re.findall(r'"display_url"\s*:\s*"([^"]+)"', html)
    captions = re.findall(r'"edge_media_to_caption".*?"text"\s*:\s*"([^"]*)"', html, re.DOTALL)
    timestamps = re.findall(r'"taken_at_timestamp"\s*:\s*(\d+)', html)

    posts = []
    for i in range(min(len(shortcodes), len(urls), count)):
        caption = ''
        if i < len(captions):
            caption = captions[i].encode().decode('unicode_escape')
        posted_at = None
        if i < len(timestamps):
            posted_at = datetime.fromtimestamp(int(timestamps[i]), tz=timezone.utc)
        posts.append({
            'instagram_id': shortcodes[i],
            'image_url': urls[i],
            'caption': caption,
            'permalink': f'https://www.instagram.com/p/{shortcodes[i]}/',
            'posted_at': posted_at,
        })

    return posts[:count]


def _extract_timeline_media(user_data, count):
    """Extract posts from a user object with edge_owner_to_timeline_media."""
    edges = user_data.get('edge_owner_to_timeline_media', {}).get('edges', [])
    posts = []

    for edge in edges[:count]:
        node = edge.get('node', {})
        shortcode = node.get('shortcode', '')
        if not shortcode:
            continue

        caption_edges = node.get('edge_media_to_caption', {}).get('edges', [])
        caption = caption_edges[0].get('node', {}).get('text', '') if caption_edges else ''

        taken_at = node.get('taken_at_timestamp')
        posted_at = (
            datetime.fromtimestamp(taken_at, tz=timezone.utc)
            if taken_at else None
        )

        posts.append({
            'instagram_id': shortcode,
            'image_url': node.get('display_url', ''),
            'caption': caption,
            'permalink': f'https://www.instagram.com/p/{shortcode}/',
            'posted_at': posted_at,
        })

    return posts


def _shortcode_from_url(url):
    match = re.search(r'/p/([A-Za-z0-9_-]+)', url)
    return match.group(1) if match else ''


def _parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except (ValueError, TypeError):
        return None
