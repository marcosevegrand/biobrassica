import logging

from django.conf import settings

logger = logging.getLogger(__name__)

INSTAGRAM_USERNAME = 'biobrassica'
INSTAGRAM_BASE_URL = 'https://www.instagram.com'


def fetch_instagram_posts(username=INSTAGRAM_USERNAME, count=5):
    """Return post data for Instagram embed rendering.

    Instagram no longer exposes post data in its server-rendered HTML or
    public API endpoints (everything requires authentication).  Use the
    Django admin to add post shortcodes manually, or set the
    ``INSTAGRAM_POST_SHORTCODES`` setting with a list of shortcodes.

    This function reads from the setting as a convenience fallback so the
    management command can still seed the database.
    """
    shortcodes = getattr(settings, 'INSTAGRAM_POST_SHORTCODES', [])

    if not shortcodes:
        logger.warning(
            'No INSTAGRAM_POST_SHORTCODES configured. '
            'Add post shortcodes in Django admin or settings.'
        )
        return []

    posts = []
    for shortcode in shortcodes[:count]:
        posts.append({
            'instagram_id': shortcode,
            'permalink': f'{INSTAGRAM_BASE_URL}/p/{shortcode}/',
        })

    logger.info('Returning %d post(s) from INSTAGRAM_POST_SHORTCODES', len(posts))
    return posts
