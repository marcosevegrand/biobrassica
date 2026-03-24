from django.contrib.auth import get_user_model
from django.contrib.postgres.indexes import GinIndex
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, connection, transaction
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from typing import Any, cast

from apps.content.models import BlogPost, BlogPostTranslation, Recipe, RecipeTranslation


GIF_BYTES = (
    b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04'
    b'\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
)


@override_settings(ROOT_URLCONF='config.urls_website')
class BlogPostSanitizationTests(TestCase):
    def setUp(self):
        self.post = BlogPost.objects.create(
            slug='seguranca-no-blog',
            is_published=True,
            published_at=timezone.now(),
            tags=['bio'],
        )

    def test_blog_translation_save_sanitizes_unsafe_html(self):
        translation = BlogPostTranslation.objects.create(
            blog_post=self.post,
            language='pt',
            title='Segurança no Blog',
            excerpt='Resumo',
            content='''
                <p>Introdução <strong>segura</strong>.</p>
                <script>alert("xss")</script>
                <a href="javascript:alert(1)" onclick="alert(2)">ligação</a>
                <img src="https://example.com/image.jpg" onerror="alert(3)" alt="capa">
            ''',
        )

        self.assertNotIn('<script>', translation.content)
        self.assertNotIn('onclick=', translation.content)
        self.assertNotIn('javascript:alert', translation.content)
        self.assertIn('<strong>segura</strong>', translation.content)
        self.assertIn('<img src="https://example.com/image.jpg" alt="capa">', translation.content)

    def test_blog_detail_renders_sanitized_content_only(self):
        BlogPostTranslation.objects.create(
            blog_post=self.post,
            language='pt',
            title='Segurança no Blog',
            excerpt='Resumo',
            content='''
                <h2>Título</h2>
                <p><a href="https://biobrassica.pt" target="_blank">Fonte</a></p>
                <script>alert("xss")</script>
                <p><a href="javascript:alert(1)">Malicioso</a></p>
            ''',
        )

        response = self.client.get(
            reverse('content:blog_detail', kwargs={'slug': self.post.slug}),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<h2>Título</h2>', html=True)
        self.assertContains(response, 'href="https://biobrassica.pt"')
        self.assertNotContains(response, 'alert("xss")')
        self.assertNotContains(response, 'javascript:alert(1)')


class ContentConstraintTests(TestCase):
    def setUp(self):
        self.post = BlogPost.objects.create(
            slug='artigo-bio',
            is_published=True,
            published_at=timezone.now(),
        )
        BlogPostTranslation.objects.create(
            blog_post=self.post,
            language='pt',
            title='Artigo bio',
            excerpt='Resumo',
            content='<p>Conteúdo</p>',
        )

        self.recipe = Recipe.objects.create(
            slug='sopa-bio',
            prep_time=15,
            cook_time=30,
            servings=4,
            is_published=True,
        )
        RecipeTranslation.objects.create(
            recipe=self.recipe,
            language='pt',
            title='Sopa bio',
            description='Descrição',
            ingredients=['1 cebola'],
            instructions=['Cortar e cozinhar'],
        )

    def test_duplicate_blog_translation_language_is_rejected(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                BlogPostTranslation.objects.create(
                    blog_post=self.post,
                    language='pt',
                    title='Artigo duplicado',
                    excerpt='Resumo',
                    content='<p>Outro conteúdo</p>',
                )

    def test_duplicate_recipe_translation_language_is_rejected(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                RecipeTranslation.objects.create(
                    recipe=self.recipe,
                    language='pt',
                    title='Sopa duplicada',
                    description='Outra descrição',
                    ingredients=['2 cebolas'],
                    instructions=['Misturar'],
                )


class ContentIndexTests(TestCase):
    def test_blogpost_tags_uses_named_gin_index(self):
        index = next(idx for idx in BlogPost._meta.indexes if idx.name == 'content_blog_tags_gin')

        self.assertIsInstance(index, GinIndex)
        self.assertEqual(index.fields, ['tags'])

    def test_recipe_tags_uses_named_gin_index(self):
        index = next(idx for idx in Recipe._meta.indexes if idx.name == 'content_recipe_tags_gin')

        self.assertIsInstance(index, GinIndex)
        self.assertEqual(index.fields, ['tags'])


@override_settings(ROOT_URLCONF='config.urls_website')
class ContentListAndDetailViewTests(TestCase):
    def setUp(self):
        for index in range(10):
            post = BlogPost.objects.create(
                slug=f'artigo-{index}',
                is_published=True,
                published_at=timezone.now(),
                tags=['bio'],
            )
            BlogPostTranslation.objects.create(
                blog_post=post,
                language='pt',
                title=f'Artigo {index}',
                excerpt='Resumo',
                content='<p>Conteúdo</p>',
            )

        for index in range(10):
            recipe = Recipe.objects.create(
                slug=f'receita-{index}',
                prep_time=15,
                cook_time=10,
                servings=4,
                is_published=True,
                tags=['bio'],
            )
            RecipeTranslation.objects.create(
                recipe=recipe,
                language='pt',
                title=f'Receita {index}',
                description='Descrição',
                ingredients=['1 ingrediente'],
                instructions=['1 passo'],
            )

        self.recipe = Recipe.objects.create(
            slug='receita-com-relacao',
            prep_time=20,
            cook_time=15,
            servings=4,
            is_published=True,
        )
        RecipeTranslation.objects.create(
            recipe=self.recipe,
            language='pt',
            title='Receita com relação',
            description='Descrição',
            ingredients=['1 ingrediente'],
            instructions=['1 passo'],
        )

    def test_blog_list_paginates_and_preserves_tag_filter(self):
        response = self.client.get(reverse('content:blog_list'), {'tag': 'bio', 'page': 2})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(response.context['page_obj'].number, 2)
        self.assertEqual(response.context['pagination_query'], 'tag=bio')
        self.assertEqual(len(response.context['posts']), 1)

    def test_recipe_list_paginates(self):
        response = self.client.get(reverse('content:recipe_list'), {'page': 2})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(response.context['page_obj'].number, 2)
        self.assertEqual(len(response.context['recipes']), 2)

    def test_recipe_detail_stays_within_expected_query_budget(self):
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(reverse('content:recipe_detail', kwargs={'slug': self.recipe.slug}))
            self.assertEqual(response.status_code, 200)

        self.assertLessEqual(len(queries), 8)


@override_settings(ROOT_URLCONF='config.urls_admin')
class ContentAdminWorkflowTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_user = cast(Any, user_model._default_manager).create_superuser(
            email='admin@example.com',
            username='admin',
            password='testpass123',
        )
        self.client.defaults['HTTP_HOST'] = 'admin.lvh.me'
        self.client.force_login(self.admin_user)

        self.blog_post = BlogPost.objects.create(
            slug='admin-blog-post',
            author=self.admin_user,
            tags=['bio', 'novidade'],
        )
        BlogPostTranslation.objects.create(
            blog_post=self.blog_post,
            language='pt',
            title='Artigo admin',
            excerpt='Resumo editorial',
            content='<p>Conteúdo editorial</p>',
        )

        self.recipe = Recipe.objects.create(
            slug='admin-recipe',
            prep_time=20,
            cook_time=10,
            servings=4,
            tags=['bio'],
        )
        RecipeTranslation.objects.create(
            recipe=self.recipe,
            language='pt',
            title='Receita admin',
            description='Descrição da receita',
            ingredients=['2 cenouras'],
            instructions=['Misturar tudo'],
        )

    def test_blog_admin_changelist_shows_editorial_workflow_cards(self):
        response = self.client.get(reverse('admin:content_blogpost_changelist'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Rascunhos')
        self.assertContains(response, 'Sem capa')
        self.assertContains(response, 'Sem tradução PT')

    def test_blog_change_form_publish_action_sets_timestamp(self):
        self.blog_post.cover_image = SimpleUploadedFile('blog.gif', GIF_BYTES, content_type='image/gif')
        self.blog_post.save(update_fields=['cover_image', 'updated_at'])

        response = self.client.post(
            reverse('admin:content_blogpost_change', args=[self.blog_post.pk]),
            {'_publish_post': '1'},
            follow=True,
        )

        self.blog_post.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.blog_post.is_published)
        self.assertIsNotNone(self.blog_post.published_at)
        self.assertContains(response, 'Checklist editorial')
        self.assertContains(response, 'Artigo publicado.')

    def test_recipe_change_form_shows_editorial_checklist_and_publish_button(self):
        self.recipe.cover_image = SimpleUploadedFile('recipe.gif', GIF_BYTES, content_type='image/gif')
        self.recipe.save(update_fields=['cover_image', 'updated_at'])

        response = self.client.get(reverse('admin:content_recipe_change', args=[self.recipe.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Checklist editorial')
        self.assertContains(response, 'Publicar receita')
        self.assertContains(response, 'Produtos relacionados')

    def test_recipe_publish_action_requires_cover_image(self):
        response = self.client.post(
            reverse('admin:content_recipe_change', args=[self.recipe.pk]),
            {'_publish_recipe': '1'},
            follow=True,
        )

        self.recipe.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.recipe.is_published)
        self.assertContains(response, 'Não foi possível publicar: carregar imagem de capa')