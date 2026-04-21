from django.core.cache import cache
from django.conf import settings
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch

from apps.accounts.models import User
from apps.catalog.models import Location
from apps.orders.models import Order
from apps.payments.models import Payment
from apps.core.site_content import clear_contact_locations_cache, get_contact_locations


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


@override_settings(ROOT_URLCONF='config.urls_website')
class WebsiteRoutingTests(TestCase):
	def test_website_host_pt_renders_home_template(self):
		response = self.client.get('/pt/', HTTP_HOST='lvh.me')

		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'website/home.html')
		self.assertContains(response, '/static/js/instagram-feed.js')
		self.assertNotContains(response, 'fonts.googleapis.com')


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
			status=Order.Status.PAID,
		)
		self.order = Order.objects.get(email=self.customer.email)
		Payment.objects.create(
			order=self.order,
			method=Payment.Method.STRIPE,
			status=Payment.Status.PAID,
			amount='12.00',
			paid_at=timezone.now(),
		)

		self.client.defaults['HTTP_HOST'] = 'admin.lvh.me'
		self.client.force_login(self.admin_user)

	def test_admin_dashboard_renders_operational_panels(self):
		response = self.client.get(reverse('admin:index'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Contas ativas')
		self.assertContains(response, 'Encomendas pagas')
		self.assertContains(response, 'Volume transacionado')
		self.assertContains(response, '12.00€')
		self.assertContains(response, 'Reposição urgente')
		self.assertContains(response, 'Levantamentos de hoje')
		self.assertContains(response, 'Recuperação de pagamentos')
		self.assertContains(response, 'Fila operacional')
		self.assertNotContains(response, 'Painel operacional')
		self.assertNotContains(response, 'Atalhos rápidos')
		self.assertNotContains(response, 'Authentication and Authorization')
		self.assertNotContains(response, 'Gerir equipa')

	def test_admin_dashboard_excludes_refunded_orders_from_paid_metrics(self):
		refunded_order = Order.objects.create(
			user=self.customer,
			name='Cliente Reembolso',
			email='refund@example.com',
			fulfillment_method=Order.FulfillmentMethod.PICKUP,
			pickup_location=Order.PickupLocation.BRAGA,
			subtotal='8.00',
			total='8.00',
			status=Order.Status.PREPARING,
		)
		Payment.objects.create(
			order=refunded_order,
			method=Payment.Method.STRIPE,
			status=Payment.Status.REFUNDED,
			amount='8.00',
		)

		response = self.client.get(reverse('admin:index'))
		metric_map = {card['label']: card['value'] for card in response.context['dashboard_metric_cards']}
		paid_orders = metric_map.get('Encomendas pagas', metric_map.get('Paid orders'))

		self.assertEqual(paid_orders, 1)

	def test_admin_branding_uses_biobrassica_sidebar_logo(self):
		self.assertEqual(settings.UNFOLD['SITE_LOGO'], '/static/images/brand/favicon_green.png')
		self.assertIsNone(settings.UNFOLD['SITE_SYMBOL'])
