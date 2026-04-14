import pytest

from tests.factories.accounts import UserFactory


@pytest.fixture
def shop_client(client):
    client.defaults['HTTP_HOST'] = 'loja.lvh.me'
    return client


@pytest.fixture
def website_client(client):
    client.defaults['HTTP_HOST'] = 'lvh.me'
    return client


@pytest.fixture
def admin_client(client, db):
    user = UserFactory(is_staff=True, is_superuser=True)
    client.defaults['HTTP_HOST'] = 'admin.lvh.me'
    client.force_login(user)
    return client