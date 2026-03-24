from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.orders.models import Order
from apps.payments.models import Payment


class SubdomainRoutingTests(TestCase):
	def test_shop_host_routes_to_shop_urls(self):
		response = self.client.get('/pt/', HTTP_HOST='loja.lvh.me')

		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'catalog/shop_home.html')

	def test_admin_is_blocked_on_website_host(self):
		response = self.client.get('/admin/', HTTP_HOST='lvh.me')

		self.assertEqual(response.status_code, 404)


@override_settings(ROOT_URLCONF='config.urls_shop')
class HealthEndpointTests(TestCase):
	def test_health_endpoint_returns_ok_json(self):
		response = self.client.get('/_health/', HTTP_HOST='loja.lvh.me')

		self.assertEqual(response.status_code, 200)
		self.assertJSONEqual(response.content, {'status': 'ok'})


@override_settings(ROOT_URLCONF='config.urls_website')
class WebsiteRoutingTests(TestCase):
	def test_website_host_pt_renders_home_template(self):
		response = self.client.get('/pt/', HTTP_HOST='lvh.me')

		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'website/home.html')


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
			method=Payment.Method.MBWAY,
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

	def test_admin_branding_uses_biobrassica_sidebar_logo(self):
		self.assertEqual(settings.UNFOLD['SITE_LOGO'], '/static/images/brand/favicon_green.png')
		self.assertIsNone(settings.UNFOLD['SITE_SYMBOL'])
