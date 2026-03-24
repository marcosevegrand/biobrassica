from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from typing import Any, cast

from apps.catalog.models import Location
from apps.website.models import TeamMember
from apps.website.models import WebsiteContent


GIF_BYTES = (
    b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04'
    b'\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
)


@override_settings(ROOT_URLCONF='config.urls_website')
class WebsiteAboutViewTests(TestCase):
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
class WebsiteContentTranslationTests(TestCase):
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


@override_settings(ROOT_URLCONF='config.urls_website')
class WebsiteContactsViewTests(TestCase):
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


@override_settings(ROOT_URLCONF='config.urls_admin')
class TeamMemberAdminWorkflowTests(TestCase):
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


@override_settings(ROOT_URLCONF='config.urls_admin')
class WebsiteContentAdminTests(TestCase):
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
        self.assertContains(response, 'Operação editorial')
        self.assertContains(response, 'Gerir equipa')
        self.assertContains(response, 'Gerir lojas')