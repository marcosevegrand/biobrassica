from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.utils.safestring import mark_safe

from apps.core.translations import get_translated_attr, translation_proxy
from apps.content.sanitization import sanitize_html


class BlogPost(models.Model):
    slug = models.SlugField('slug', unique=True, max_length=200)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='blog_posts',
        verbose_name='autor',
    )
    cover_image = models.ImageField('imagem de capa', upload_to='blog/covers/', blank=True)
    is_published = models.BooleanField('publicado', default=False, db_index=True)
    published_at = models.DateTimeField('publicado em', null=True, blank=True)
    tags = models.JSONField('etiquetas', default=list, blank=True, help_text='Lista de tags, ex: ["receitas", "bio"]')
    created_at = models.DateTimeField('criado em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizado em', auto_now=True)

    class Meta:
        ordering = ['-published_at', '-created_at']
        verbose_name = 'artigo do blog'
        verbose_name_plural = 'artigos do blog'
        indexes = [
            GinIndex(fields=['tags'], name='content_blog_tags_gin'),
        ]

    def __str__(self):
        return get_translated_attr(self, 'title', default=self.slug, lang='pt')

    def get_title(self, lang=None):
        return get_translated_attr(self, 'title', default=self.slug, lang=lang)

    def get_excerpt(self, lang=None):
        return get_translated_attr(self, 'excerpt', default='', lang=lang)

    def get_content(self, lang=None):
        return get_translated_attr(self, 'content', default='', lang=lang)

    @property
    def safe_translation(self):
        return translation_proxy(self)

    @property
    def tags_list(self):
        """Return tags as a list (handles both list and comma-separated string)."""
        if isinstance(self.tags, list):
            return self.tags
        if isinstance(self.tags, str):
            return [t.strip() for t in self.tags.split(',') if t.strip()]
        return []


class BlogPostTranslation(models.Model):
    blog_post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='translations', verbose_name='artigo do blog')
    language = models.CharField('idioma', max_length=2, choices=[('pt', 'Português'), ('en', 'Inglês'), ('fr', 'Francês')])
    title = models.CharField('título', max_length=255)
    excerpt = models.TextField('resumo', blank=True, help_text='Resumo curto para listagens')
    content = models.TextField('conteúdo', help_text='Conteúdo do artigo (HTML)')
    meta_description = models.CharField('meta descrição', max_length=160, blank=True)

    class Meta:
        verbose_name = 'tradução de artigo'
        verbose_name_plural = 'traduções de artigo'
        constraints = [
            models.UniqueConstraint(
                fields=['blog_post', 'language'],
                name='content_unique_blog_translation_language',
            ),
        ]

    def __str__(self):
        return f'{self.title} ({self.language})'

    @property
    def rendered_content(self):
        return mark_safe(self.content)

    def save(self, *args, **kwargs):
        self.content = sanitize_html(self.content)
        super().save(*args, **kwargs)


class Recipe(models.Model):
    class Difficulty(models.TextChoices):
        EASY = 'easy', 'Fácil'
        MEDIUM = 'medium', 'Médio'
        HARD = 'hard', 'Difícil'

    slug = models.SlugField('slug', unique=True, max_length=200)
    cover_image = models.ImageField('imagem de capa', upload_to='recipes/covers/', blank=True)
    prep_time = models.PositiveIntegerField('tempo de preparação', help_text='Tempo de preparação em minutos')
    cook_time = models.PositiveIntegerField('tempo de cozedura', null=True, blank=True, help_text='Tempo de cozedura em minutos')
    servings = models.PositiveIntegerField('doses', default=4)
    difficulty = models.CharField('dificuldade', max_length=10, choices=Difficulty.choices, default=Difficulty.MEDIUM)
    related_products = models.ManyToManyField(
        'catalog.Product',
        blank=True,
        related_name='recipes',
        verbose_name='produtos relacionados',
        help_text='Produtos relacionados (comprar ingredientes)',
    )
    tags = models.JSONField('etiquetas', default=list, blank=True, help_text='Tags para filtragem, ex: ["vegetariano", "sem glúten"]')
    is_published = models.BooleanField('publicado', default=False, db_index=True)
    created_at = models.DateTimeField('criado em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizado em', auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'receita'
        verbose_name_plural = 'receitas'
        indexes = [
            GinIndex(fields=['tags'], name='content_recipe_tags_gin'),
        ]

    def __str__(self):
        return get_translated_attr(self, 'title', default=self.slug, lang='pt')

    def get_title(self, lang=None):
        return get_translated_attr(self, 'title', default=self.slug, lang=lang)

    def get_description(self, lang=None):
        return get_translated_attr(self, 'description', default='', lang=lang)

    @property
    def tags_list(self):
        if isinstance(self.tags, list):
            return self.tags
        if isinstance(self.tags, str):
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []

    def get_ingredients(self, lang=None):
        translation = self.safe_translation if lang is None else translation_proxy(self, lang=lang)
        value = translation.ingredients
        if not value:
            return []

        if isinstance(value, list):
            return value
        if isinstance(value, str):
            return [line.strip() for line in value.splitlines() if line.strip()]
        return []

    def get_instructions(self, lang=None):
        translation = self.safe_translation if lang is None else translation_proxy(self, lang=lang)
        value = translation.instructions
        if not value:
            return []

        if isinstance(value, list):
            return value
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return []

    @property
    def total_time(self):
        total = self.prep_time
        if self.cook_time:
            total += self.cook_time
        return total

    @property
    def safe_translation(self):
        return translation_proxy(self)


class RecipeTranslation(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='translations', verbose_name='receita')
    language = models.CharField('idioma', max_length=2, choices=[('pt', 'Português'), ('en', 'Inglês'), ('fr', 'Francês')])
    title = models.CharField('título', max_length=255)
    description = models.TextField('descrição', blank=True, help_text='Descrição curta')
    ingredients = models.JSONField(
        'ingredientes',
        default=list,
        help_text='Lista de ingredientes: ["200g farinha", "2 ovos", ...]',
    )
    instructions = models.JSONField(
        'instruções',
        default=list,
        help_text='Lista de passos de preparação: ["Pré-aquecer o forno...", "Misturar..."]',
    )
    meta_description = models.CharField('meta descrição', max_length=160, blank=True)

    class Meta:
        verbose_name = 'tradução de receita'
        verbose_name_plural = 'traduções de receita'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'language'],
                name='content_unique_recipe_translation_language',
            ),
        ]

    def __str__(self):
        return f'{self.title} ({self.language})'
