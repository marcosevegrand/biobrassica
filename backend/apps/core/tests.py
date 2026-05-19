import stat
import subprocess
import tempfile
from pathlib import Path

from django.core.cache import cache
from django.conf import settings
from django.contrib.auth.models import Permission
from django.db import connection
from django.test import RequestFactory, TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch

from apps.accounts.models import User
from apps.catalog.models import Location
from apps.core.site_content import get_shop_base_url, get_website_base_url
from apps.orders.models import Order
from apps.payments.models import Payment
from apps.core.site_content import clear_contact_locations_cache, get_contact_locations


MIRROR_DOMAIN_SETTINGS = {
	'ALLOWED_HOSTS': [
		'biobrassica.pt',
		'www.biobrassica.pt',
		'loja.biobrassica.pt',
		'admin.biobrassica.pt',
		'marcosevegrand.com',
		'www.marcosevegrand.com',
		'loja.marcosevegrand.com',
		'admin.marcosevegrand.com',
	],
	'PUBLIC_DOMAINS': ['biobrassica.pt', 'marcosevegrand.com'],
	'WEBSITE_HOST': 'biobrassica.pt',
	'WEBSITE_ALLOWED_HOSTS': [
		'biobrassica.pt',
		'www.biobrassica.pt',
		'marcosevegrand.com',
		'www.marcosevegrand.com',
	],
	'SHOP_HOST': 'loja.biobrassica.pt',
	'SHOP_ALLOWED_HOSTS': ['loja.biobrassica.pt', 'loja.marcosevegrand.com'],
	'ADMIN_HOST': 'admin.biobrassica.pt',
	'ADMIN_ALLOWED_HOSTS': ['admin.biobrassica.pt', 'admin.marcosevegrand.com'],
	'SHOP_BASE_URL': 'https://loja.biobrassica.pt',
}


class SubdomainRoutingTests(TestCase):
	def test_shop_host_routes_to_shop_urls(self):
		response = self.client.get('/pt/', HTTP_HOST='loja.lvh.me')

		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'catalog/shop_home.html')
		self.assertContains(response, '/static/js/htmx.min.js')
		self.assertContains(response, 'https://lvh.me/pt/contactos/')
		self.assertContains(response, 'https://lvh.me')
		self.assertNotContains(response, 'https://biobrassica.pt/pt/contactos/')
		self.assertNotContains(response, 'https://unpkg.com/htmx.org@2.0.4')
		self.assertNotContains(response, 'fonts.googleapis.com')

	@override_settings(**MIRROR_DOMAIN_SETTINGS)
	def test_shop_host_preserves_alias_domain_family_for_website_links(self):
		response = self.client.get('/pt/', HTTP_HOST='loja.marcosevegrand.com')

		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'catalog/shop_home.html')
		self.assertContains(response, 'https://marcosevegrand.com/pt/contactos/')
		self.assertContains(response, 'https://marcosevegrand.com')
		self.assertNotContains(response, 'https://biobrassica.pt/pt/contactos/')

	@override_settings(**MIRROR_DOMAIN_SETTINGS)
	def test_www_host_collapses_to_bare_domain_for_absolute_urls(self):
		request = RequestFactory().get('/', HTTP_HOST='www.marcosevegrand.com')

		self.assertEqual(get_website_base_url(request=request), 'https://marcosevegrand.com')
		self.assertEqual(get_shop_base_url(request=request), 'https://loja.marcosevegrand.com')

	def test_admin_is_blocked_on_website_host(self):
		response = self.client.get('/admin/', HTTP_HOST='lvh.me')

		self.assertEqual(response.status_code, 404)

	@override_settings(SITE_ROLE='shop', ROOT_URLCONF='config.urls_shop')
	def test_site_role_can_force_shop_urls_without_shop_host(self):
		response = self.client.get('/pt/', HTTP_HOST='lvh.me')

		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'catalog/shop_home.html')

	@override_settings(SITE_ROLE='admin', ROOT_URLCONF='config.urls_admin')
	def test_site_role_can_force_admin_urls_without_admin_host(self):
		response = self.client.get('/', HTTP_HOST='lvh.me')

		self.assertEqual(response.status_code, 302)
		self.assertEqual(response['Location'], '/admin/')
		self.assertEqual(response.headers.get('Content-Language'), 'pt')


@override_settings(ROOT_URLCONF='config.urls_shop')
class HealthEndpointTests(TestCase):
	def test_health_endpoint_returns_ok_json(self):
		response = self.client.get('/_health/', HTTP_HOST='loja.lvh.me')

		self.assertEqual(response.status_code, 200)
		self.assertJSONEqual(response.content, {'status': 'ok'})

	def test_health_endpoint_hides_internal_exception_details(self):
		with patch('apps.core.health.connection.cursor', side_effect=RuntimeError('database biobrassica unavailable')):
			response = self.client.get('/_health/', HTTP_HOST='loja.lvh.me')

		self.assertEqual(response.status_code, 500)
		self.assertJSONEqual(response.content, {'status': 'error'})
		self.assertNotIn('database biobrassica unavailable', response.content.decode())

	def test_docker_healthcheck_uses_role_fallback_when_allowed_hosts_env_is_unset(self):
		script_path = Path(settings.BASE_DIR) / 'docker-healthcheck.sh'

		with tempfile.TemporaryDirectory() as temp_dir:
			stub_curl = Path(temp_dir) / 'curl'
			stub_curl.write_text(
				"#!/bin/sh\nprintf '%s\\n' \"$@\"\n",
				encoding='utf-8',
			)
			stub_curl.chmod(stub_curl.stat().st_mode | stat.S_IXUSR)

			env = {
				'PATH': temp_dir,
				'SITE_ROLE': 'shop',
				'PRIMARY_DOMAIN': 'example.com',
			}

			result = subprocess.run(
				['/bin/sh', str(script_path)],
				capture_output=True,
				text=True,
				env=env,
				check=False,
			)

		self.assertEqual(result.returncode, 0, msg=result.stderr)
		self.assertIn('Host: loja.example.com', result.stdout)
		self.assertFalse(result.stderr)


@override_settings(ROOT_URLCONF='config.urls_website')
class WebsiteRoutingTests(TestCase):
	def test_website_host_pt_renders_home_template(self):
		response = self.client.get('/pt/', HTTP_HOST='lvh.me')

		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'website/home.html')
		self.assertContains(response, '@biobrassica')
		self.assertNotContains(response, 'fonts.googleapis.com')

	@override_settings(ROOT_URLCONF='config.urls_shop')
	def test_shop_homepage_relies_on_compiled_display_utilities(self):
		response = self.client.get('/pt/', HTTP_HOST='loja.lvh.me')

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, '/static/images/people/002.jpg')
		self.assertNotContains(response, '.hidden { display: none !important; }')
		self.assertNotContains(response, '.block { display: block !important; }')

	def test_website_contacts_uses_hardcoded_public_store_locations(self):
		from apps.catalog.models import Location

		Location.objects.create(name='Pickup Temporário', address='Rua Temporária', is_active=True, order=1)
		response = self.client.get(reverse('website:contacts'), HTTP_HOST='lvh.me')

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Loja Braga')
		self.assertContains(response, 'Loja Guimarães')
		self.assertNotContains(response, 'Pickup Temporário')


@override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
class ContactLocationsCacheTests(TestCase):
	def setUp(self):
		cache.clear()
		clear_contact_locations_cache()

	def test_contact_locations_are_cached_after_first_query(self):
		Location.objects.create(name='Loja Braga', address='Rua A', is_active=True, order=1)

		with CaptureQueriesContext(connection) as queries:
			first_result = get_contact_locations()
			second_result = get_contact_locations()

		self.assertEqual(len(queries), 1)
		self.assertEqual(first_result, second_result)

	def test_location_changes_invalidate_contact_locations_cache(self):
		Location.objects.create(name='Loja Braga', address='Rua A', is_active=True, order=1)
		first_result = get_contact_locations()

		Location.objects.create(name='Loja Guimarães', address='Rua B', is_active=True, order=2)
		second_result = get_contact_locations()

		self.assertEqual([location['name'] for location in first_result], ['Loja Braga'])
		self.assertEqual([location['name'] for location in second_result], ['Loja Braga', 'Loja Guimarães'])


@override_settings(ROOT_URLCONF='config.urls_admin')
class AdminDashboardTests(TestCase):
	def setUp(self):
		self.admin_user = User.objects.create_superuser(
			email='admin@example.com',
			username='admin',
			password='testpass123',
		)
		self.customer = User.objects.create_user(
			email='cliente@biobrassica.pt',
			username='cliente',
			password='testpass123',
		)
		Order.objects.create(
			user=self.customer,
			name='Cliente Dashboard',
			email=self.customer.email,
			fulfillment_method=Order.FulfillmentMethod.PICKUP,
			pickup_location=Order.PickupLocation.BRAGA,
			subtotal='12.00',
			total='12.00',
			status=Order.Status.PREPARING,
			payment_state=Order.PaymentState.CONFIRMED,
		)
		self.order = Order.objects.get(email=self.customer.email)
		Payment.objects.create(
			order=self.order,
			method=Payment.Method.MBWAY_MANUAL,
			status=Payment.Status.CONFIRMED,
			amount='12.00',
			paid_at=timezone.now(),
		)

		self.client.defaults['HTTP_HOST'] = 'admin.lvh.me'
		self.client.force_login(self.admin_user)

	def test_admin_root_redirects_to_operational_panel(self):
		response = self.client.get(reverse('admin:index'))

		self.assertEqual(response.status_code, 302)
		self.assertEqual(response['Location'], reverse('operacoes_painel'))

	def test_operational_panel_renders_in_flight_orders(self):
		response = self.client.get(reverse('operacoes_painel'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Painel')
		self.assertContains(response, 'Cliente Dashboard')
		self.assertContains(response, 'Encomendas')
		self.assertContains(response, 'Produtos')

	def test_admin_branding_uses_biobrassica_sidebar_logo(self):
		self.assertEqual(settings.UNFOLD['SITE_LOGO'], '/static/images/brand/favicon_green.png')
		self.assertIsNone(settings.UNFOLD['SITE_SYMBOL'])

	def test_operational_panel_preserves_admin_navigation_for_superuser(self):
		response = self.client.get(reverse('operacoes_painel'))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.context['opts'], Order._meta)
		self.assertTrue(response.context['sidebar_navigation'])
		self.assertContains(response, 'Painel')
		self.assertContains(response, 'Encomendas')
		self.assertContains(response, 'Produtos')
		self.assertNotContains(response, 'You don’t have permission to view or edit anything.')

	def test_operational_panel_blocks_staff_without_order_access(self):
		staff_user = User.objects.create_user(
			email='equipa@biobrassica.pt',
			username='equipa',
			password='testpass123',
			is_staff=True,
		)
		staff_user.user_permissions.add(Permission.objects.get(codename='view_user'))

		self.client.force_login(staff_user)
		response = self.client.get(reverse('operacoes_painel'))

		self.assertEqual(response.status_code, 403)

	def test_admin_change_form_no_longer_renders_form_navigation_block(self):
		response = self.client.get(reverse('admin:catalog_category_add'))

		self.assertEqual(response.status_code, 200)
		self.assertNotContains(response, 'Navegação do formulário')
