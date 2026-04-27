import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import translation
from typing import Any, cast

from apps.catalog.models import Location
from apps.website.forms import TeamMemberAdminForm
from apps.website.models import TeamMember
from apps.website.models import WebsiteContent


GIF_BYTES = (
    b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04'
    b'\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
)

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


class TempMediaRootMixin:
    @classmethod
    def setUpClass(cls):
        cast(Any, super()).setUpClass()
        cls._temp_media_root = tempfile.mkdtemp()
        cls._media_override = override_settings(MEDIA_ROOT=cls._temp_media_root)
        cls._media_override.enable()

    @classmethod
    def tearDownClass(cls):
        cls._media_override.disable()
        shutil.rmtree(cls._temp_media_root, ignore_errors=True)
        cast(Any, super()).tearDownClass()


class WebsiteTestCase(TempMediaRootMixin, TestCase):
    def tearDown(self):
        translation.activate(settings.LANGUAGE_CODE)
        super().tearDown()


class TeamMemberAdminFormTests(WebsiteTestCase):
    def test_team_member_admin_form_combines_structured_role_fields(self):
        form = TeamMemberAdminForm(
            data={
                'name': 'Ângela Pereira',
                'role': '',
                'role_choice': TeamMemberAdminForm.ROLE_CUSTOM_CHOICE,
                'role_custom': 'Coordenadora de loja',
                'order': '1',
                'is_active': 'on',
            },
            files={
                'photo': SimpleUploadedFile('angela.gif', GIF_BYTES, content_type='image/gif'),
            },
        )

        self.assertTrue(form.is_valid(), form.errors)
        member = form.save(commit=False)

        self.assertEqual(member.role, 'Coordenadora de loja')

    def test_team_member_admin_form_queries_role_suggestions_once(self):
        TeamMember.objects.create(
            name='Rita',
            role='Backoffice',
            photo=SimpleUploadedFile('rita.gif', GIF_BYTES, content_type='image/gif'),
            order=2,
            is_active=True,
        )

        with CaptureQueriesContext(connection) as queries:
            form = TeamMemberAdminForm(
                data={
                    'name': 'Ângela Pereira',
                    'role': '',
                    'role_choice': TeamMemberAdminForm.ROLE_CUSTOM_CHOICE,
                    'role_custom': 'Coordenadora de loja',
                    'order': '1',
                    'is_active': 'on',
                },
                files={
                    'photo': SimpleUploadedFile('angela.gif', GIF_BYTES, content_type='image/gif'),
                },
            )

            self.assertTrue(form.is_valid(), form.errors)

        self.assertEqual(len(queries), 1)


class WebsiteContentValidationTests(WebsiteTestCase):
    def test_website_content_full_clean_normalizes_company_and_whatsapp_fields(self):
        content = WebsiteContent(
            company_legal_name='  Biobrassica, Lda.  ',
            company_address=' Rua Central 42, Braga ',
            company_nif='123 456 789',
            support_email=' Apoio@Biobrassica.PT ',
            whatsapp_number='912345678',
        )

        content.full_clean()

        self.assertEqual(content.company_legal_name, 'Biobrassica, Lda.')
        self.assertEqual(content.company_address, 'Rua Central 42, Braga')
        self.assertEqual(content.company_nif, '123456789')
        self.assertEqual(content.support_email, 'apoio@biobrassica.pt')
        self.assertEqual(content.whatsapp_number, '+351 912 345 678')

    def test_website_content_full_clean_rejects_invalid_whatsapp_number(self):
        content = WebsiteContent(whatsapp_number='12345')

        with self.assertRaises(ValidationError) as ctx:
            content.full_clean()

        self.assertIn('whatsapp_number', ctx.exception.message_dict)


@override_settings(ROOT_URLCONF='config.urls_website')
class WebsiteAboutViewTests(WebsiteTestCase):
    def test_about_page_renders_active_team_members_only(self):
        TeamMember.objects.create(
            name='Ângela Pereira',
            role='Fundadora',
            photo=SimpleUploadedFile('angela.gif', GIF_BYTES, content_type='image/gif'),
            order=1,
            is_active=True,
        )
        TeamMember.objects.create(
            name='Oculto',
            role='Backoffice',
            photo=SimpleUploadedFile('oculto.gif', GIF_BYTES, content_type='image/gif'),
            order=2,
            is_active=False,
        )

        response = self.client.get(reverse('website:about'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ângela Pereira')
        self.assertContains(response, 'Fundadora')
        self.assertNotContains(response, 'Oculto')

    def test_about_page_uses_admin_managed_content_when_available(self):
        content = WebsiteContent.objects.first() or WebsiteContent.objects.create()
        content.about_hero_title = 'Equipa e origem'
        content.about_hero_subtitle = 'Conteúdo vindo do backoffice'
        content.save(update_fields=['about_hero_title', 'about_hero_subtitle'])

        response = self.client.get(reverse('website:about'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Equipa e origem')
        self.assertContains(response, 'Conteúdo vindo do backoffice')


@override_settings(ROOT_URLCONF='config.urls_website')
class WebsiteContentTranslationTests(WebsiteTestCase):
    def setUp(self):
        self.content = WebsiteContent.objects.first() or WebsiteContent.objects.create()
        self.content.home_hero_title_line1 = 'Tudo que precisa para uma'
        self.content.home_hero_title_line2 = 'alimentação saudável'
        self.content.home_hero_tagline = 'Produtos biológicos, saudáveis para si, bons para o ambiente.'
        self.content.contacts_hero_title = 'Encontre-nos'
        self.content.save(
            update_fields=[
                'home_hero_title_line1',
                'home_hero_title_line2',
                'home_hero_tagline',
                'contacts_hero_title',
            ]
        )

    def test_homepage_uses_translated_admin_content_for_english(self):
        response = self.client.get('/en/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Everything you need for a')
        self.assertContains(response, 'healthy diet')
        self.assertContains(response, 'Organic products, healthy for you, good for the environment.')
        self.assertNotContains(response, 'Tudo que precisa para uma')
        self.assertNotContains(response, 'alimentação saudável')

    def test_contacts_uses_translated_admin_content_for_french(self):
        response = self.client.get('/fr/contactos/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Trouvez-nous')
        self.assertNotContains(response, 'Encontre-nos')

    def test_homepage_uses_environment_shop_domain_in_navigation(self):
        response = self.client.get('/en/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'https://loja.lvh.me/en/')

    @override_settings(**MIRROR_DOMAIN_SETTINGS)
    def test_homepage_preserves_alias_domain_family_in_shop_navigation(self):
        response = self.client.get('/en/', HTTP_HOST='marcosevegrand.com')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'https://loja.marcosevegrand.com/en/')
        self.assertNotContains(response, 'https://loja.biobrassica.pt/en/')


@override_settings(ROOT_URLCONF='config.urls_website')
class WebsiteContactsViewTests(WebsiteTestCase):
    def test_contacts_page_uses_centralized_meta_description_default(self):
        response = self.client.get(reverse('website:contacts'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Entre em contacto com a Biobrassica. Lojas em Braga e Guimarães, ou contacte-nos por telefone e email.')

    def test_contacts_page_uses_location_records(self):
        Location.objects.create(
            name='Loja Braga',
            address='Avenida Central\nBraga',
            phone='253 271 187',
            email='geral@biobrassica.pt',
            opening_hours='Segunda a Sábado\n9h00 – 19h30',
            map_embed_url='https://example.com/mapa',
            is_active=True,
        )

        response = self.client.get(reverse('website:contacts'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Loja Braga')
        self.assertContains(response, 'Avenida Central')
        self.assertContains(response, 'https://example.com/mapa')

    def test_footer_uses_active_location_records(self):
        Location.objects.create(
            name='Loja Guimarães',
            address='Rua Exemplo 5\nGuimarães',
            phone='253 145 388',
            email='guimaraes@biobrassica.pt',
            is_active=True,
        )

        response = self.client.get(reverse('website:home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Loja Guimarães')
        self.assertContains(response, 'guimaraes@biobrassica.pt')

    def test_homepage_footer_uses_managed_whatsapp_number_when_present(self):
        WebsiteContent.objects.create(whatsapp_number='+351 912 345 678')

        response = self.client.get(reverse('website:home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'https://wa.me/351912345678')


@override_settings(ROOT_URLCONF='config.urls_website')
class WebsiteLegalPagesTests(WebsiteTestCase):
    def test_privacy_and_terms_pages_use_managed_company_details(self):
        WebsiteContent.objects.create(
            company_legal_name='Biobrassica Cooperativa',
            company_address='Rua da Empresa 42, Braga',
            company_nif='123456789',
            support_email='apoio@biobrassica.pt',
        )

        privacy_response = self.client.get(reverse('website:privacy'))
        terms_response = self.client.get(reverse('website:terms'))

        self.assertEqual(privacy_response.status_code, 200)
        self.assertContains(privacy_response, 'Biobrassica Cooperativa')
        self.assertContains(privacy_response, 'Rua da Empresa 42, Braga')
        self.assertContains(privacy_response, 'apoio@biobrassica.pt')
        self.assertContains(privacy_response, '123456789')

        self.assertEqual(terms_response.status_code, 200)
        self.assertContains(terms_response, 'Biobrassica Cooperativa')
        self.assertContains(terms_response, 'Rua da Empresa 42, Braga')
        self.assertContains(terms_response, 'apoio@biobrassica.pt')
        self.assertContains(terms_response, '123456789')

    def test_privacy_and_terms_pages_use_centralized_defaults_without_website_content(self):
        privacy_response = self.client.get(reverse('website:privacy'))
        terms_response = self.client.get(reverse('website:terms'))

        self.assertEqual(privacy_response.status_code, 200)
        self.assertContains(privacy_response, 'Biobrassica, Lda.')
        self.assertContains(privacy_response, 'R. dos Capelistas 121, 4700-215 Braga')
        self.assertContains(privacy_response, 'geral@biobrassica.pt')

        self.assertEqual(terms_response.status_code, 200)
        self.assertContains(terms_response, 'Biobrassica, Lda.')
        self.assertContains(terms_response, 'R. dos Capelistas 121, 4700-215 Braga')
        self.assertContains(terms_response, 'geral@biobrassica.pt')


@override_settings(ROOT_URLCONF='config.urls_admin')
class TeamMemberAdminWorkflowTests(WebsiteTestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_user = cast(Any, user_model._default_manager).create_superuser(
            email='admin@example.com',
            username='admin',
            password='testpass123',
        )
        self.member = TeamMember.objects.create(
            name='Ângela Pereira',
            role='Fundadora',
            photo=SimpleUploadedFile('angela.gif', GIF_BYTES, content_type='image/gif'),
            order=1,
            is_active=True,
        )
        self.client.defaults['HTTP_HOST'] = 'admin.lvh.me'
        self.client.force_login(self.admin_user)

    def test_team_member_admin_changelist_shows_workflow_cards(self):
        response = self.client.get(reverse('admin:website_teammember_changelist'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Equipa ativa')
        self.assertContains(response, 'Ocultos')
        self.assertContains(response, 'Primeiros quatro')

    def test_team_member_change_form_can_hide_member(self):
        response = self.client.post(
            reverse('admin:website_teammember_change', args=[self.member.pk]),
            {'_hide_from_website': '1'},
            follow=True,
        )

        self.member.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.member.is_active)
        self.assertContains(response, 'Membro ocultado da página pública.')

    def test_team_member_change_form_uses_structured_role_fields(self):
        response = self.client.get(reverse('admin:website_teammember_change', args=[self.member.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="role_choice"', html=False)
        self.assertContains(response, 'name="role_custom"', html=False)


@override_settings(ROOT_URLCONF='config.urls_admin')
class WebsiteContentAdminTests(WebsiteTestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_user = cast(Any, user_model._default_manager).create_superuser(
            email='admin@example.com',
            username='admin',
            password='testpass123',
        )
        self.content = WebsiteContent.objects.create(home_hero_title_line1='Backoffice')
        self.client.defaults['HTTP_HOST'] = 'admin.lvh.me'
        self.client.force_login(self.admin_user)

    def test_website_content_change_form_shows_editorial_summary(self):
        response = self.client.get(reverse('admin:website_websitecontent_change', args=[self.content.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Navegação do formulário')
        self.assertContains(response, 'Operação editorial')
        self.assertContains(response, 'Pagamentos')
        self.assertContains(response, 'MB WAY manual')
        self.assertContains(response, 'Email de apoio')
        self.assertContains(response, 'Gerir equipa')
        self.assertContains(response, 'Gerir lojas')

    def test_website_content_change_form_rejects_invalid_company_fields(self):
        response = self.client.post(
            reverse('admin:website_websitecontent_change', args=[self.content.pk]),
            {
                'payments_enabled': 'on',
                'manual_mbway_number': '12345',
                'company_nif': '123',
                'support_email': 'apoio@biobrassica.pt',
                'whatsapp_number': '12345',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Indique um NIF português válido.')
        self.assertContains(response, 'Indique um telemóvel português válido.')
        self.assertContains(response, 'Indique um número WhatsApp português válido.')

    def test_website_content_change_form_can_disable_payments(self):
        response = self.client.post(
            reverse('admin:website_websitecontent_change', args=[self.content.pk]),
            {'_disable_payments': '1'},
            follow=True,
        )

        self.content.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.content.payments_enabled)
        self.assertContains(response, 'Pagamentos desativados.')


class WebsiteContentSingletonTests(WebsiteTestCase):
    def test_create_reuses_singleton_row(self):
        first = WebsiteContent.objects.create(home_hero_title_line1='Primeira versão')
        second = WebsiteContent.objects.create(home_hero_title_line1='Versão final')

        self.assertEqual(first.pk, 1)
        self.assertEqual(second.pk, 1)
        self.assertEqual(WebsiteContent.objects.count(), 1)
        self.assertEqual(WebsiteContent.objects.get(pk=1).home_hero_title_line1, 'Versão final')