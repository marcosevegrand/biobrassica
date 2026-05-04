from collections.abc import Iterator
import os
import shutil
from urllib.parse import urlsplit, urlunsplit

import pytest
from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY
from django.contrib.sessions.backends.db import SessionStore
from django.db import connections
from playwright.sync_api import Page, sync_playwright

from tests.factories.accounts import UserFactory


def _replace_host(url: str, host: str) -> str:
    parsed = urlsplit(url)
    netloc = host
    if parsed.port:
        netloc = f'{host}:{parsed.port}'
    return urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))


def _chromium_launch_options() -> dict:
    executable_path = os.environ.get('PLAYWRIGHT_CHROMIUM_EXECUTABLE')
    if executable_path:
        return {'headless': True, 'executable_path': executable_path}

    for candidate in ('google-chrome-stable', 'google-chrome', 'chromium', 'chromium-browser'):
        resolved = shutil.which(candidate)
        if resolved:
            return {'headless': True, 'executable_path': resolved}

    return {'headless': True}


@pytest.fixture
def shop_live_server_url(live_server) -> str:
    return _replace_host(live_server.url, 'loja.lvh.me')


@pytest.fixture
def browser_page(db, shop_live_server_url: str) -> Iterator[Page]:
    previous_async_setting = os.environ.get('DJANGO_ALLOW_ASYNC_UNSAFE')
    os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
    user = UserFactory()
    session = SessionStore()
    session[SESSION_KEY] = str(user.pk)
    session[BACKEND_SESSION_KEY] = 'django.contrib.auth.backends.ModelBackend'
    session[HASH_SESSION_KEY] = user.get_session_auth_hash()
    session.save()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(**_chromium_launch_options())
        context = browser.new_context(base_url=shop_live_server_url, locale='pt-PT')
        context.add_cookies([
            {
                'name': 'sessionid',
                'value': session.session_key,
                'domain': 'loja.lvh.me',
                'path': '/',
                'httpOnly': True,
                'sameSite': 'Lax',
            },
        ])
        page = context.new_page()
        try:
            yield page
        finally:
            context.close()
            browser.close()
            connections.close_all()
            if previous_async_setting is None:
                os.environ.pop('DJANGO_ALLOW_ASYNC_UNSAFE', None)
            else:
                os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = previous_async_setting
