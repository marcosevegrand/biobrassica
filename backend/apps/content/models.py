import json
from django.utils.text import slugify

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import Any, cast

from apps.core.translations import get_translated_attr, translation_proxy
from apps.content.markdown import render_markdown


TRANSLATION_LANGUAGE_CHOICES = [('pt', _('Português')), ('en', _('Inglês')), ('fr', _('Francês'))]
INLINE_TRANSLATION_LANGUAGE_CHOICES = [('en', _('Inglês')), ('fr', _('Francês'))]


def _generate_unique_slug(model, value, *, instance_pk=None):
    base_slug = slugify(str(value or '').strip())[:180]
    if not base_slug:
        return ''

    slug = base_slug
    suffix = 2
    queryset = model.objects.all()
    if instance_pk is not None:
        queryset = queryset.exclude(pk=instance_pk)
    while queryset.filter(slug=slug).exists():
        slug = f'{base_slug[:180]}-{suffix}'
        suffix += 1
    return slug


def _normalize_string_list(value, *, field_name):
    if value in (None, ''):
        return []

    if isinstance(value, str):
        try:
            decoded_value = json.loads(value)
        except (TypeError, ValueError):
            items = value.splitlines() if '\n' in value else value.split(',')
        else:
            return _normalize_string_list(decoded_value, field_name=field_name)
    elif isinstance(value, (list, tuple)):
        items = value
    else:
        raise ValidationError({field_name: _('Use uma lista de texto.')})

    normalized_items = []
    for item in items:
        if not isinstance(item, str):
            raise ValidationError({field_name: _('Use apenas valores de texto.')})
        item = item.strip()
        if item:
            normalized_items.append(item)
    return normalized_items


class BlogPost(models.Model):
    slug = models.SlugField(_('slug'), unique=True, max_length=200)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='blog_posts',
        verbose_name=_('autor'),
    )
    cover_image = models.ImageField(_('imagem de capa'), upload_to='blog/covers/', blank=True)
    is_published = models.BooleanField(_('publicado'), default=False, db_index=True)
    published_at = models.DateTimeField(_('publicado em'), null=True, blank=True)
    tags = models.JSONField(_('etiquetas'), default=list, blank=True, help_text=_('Lista de tags, ex: ["receitas", "bio"]'))
    created_at = models.DateTimeField(_('criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('atualizado em'), auto_now=True)

    class Meta:
        ordering = ['-published_at', '-created_at']
        verbose_name = _('artigo do blog')
        verbose_name_plural = _('artigos do blog')

    def __str__(self):
        return self.get_title('pt') or self.slug

    def clean(self):
        super().clean()
        translations = cast(Any, self).translations
        errors = {}
        draft_translation = getattr(self, '_pt_translation_draft', None) or {}

        self.slug = str(self.slug or '').strip()
        pt_title = draft_translation.get('title') or self.get_title('pt')
        if not self.slug and pt_title:
            self.slug = _generate_unique_slug(self.__class__, pt_title, instance_pk=self.pk)

        try:
            self.tags = _normalize_string_list(self.tags, field_name='tags')
        except ValidationError as error:
            errors.update(error.message_dict)

        if not self.is_published:
            if errors:
                raise ValidationError(errors)
            return

        publish_errors = []
        has_pt_translation = bool(draft_translation) or (self.pk and translations.filter(language='pt').exists())
        if not has_pt_translation:
            publish_errors.append(_('adicionar tradução PT'))
        elif not (draft_translation.get('excerpt') or self.get_summary(lang='pt')):
            publish_errors.append(_('preencher resumo PT'))
        elif not (draft_translation.get('content') or self.get_content(lang='pt')):
            publish_errors.append(_('preencher conteúdo PT'))
        if not self.cover_image:
            publish_errors.append(_('carregar imagem de capa'))

        if publish_errors:
            errors['__all__'] = publish_errors
        if errors:
            raise ValidationError(errors)

    def get_title(self, lang=None):
        if not self.pk:
            return self.slug
        return get_translated_attr(self, 'title', default=self.slug, lang=lang)

    def get_summary(self, lang=None):
        if not self.pk:
            return ''
        return get_translated_attr(self, 'excerpt', default='', lang=lang)

    def get_excerpt(self, lang=None):
        return self.get_summary(lang=lang)

    def get_content(self, lang=None):
        if not self.pk:
            return ''
        return get_translated_attr(self, 'content', default='', lang=lang)

    def get_rendered_content(self, lang=None):
        return render_markdown(self.get_content(lang=lang))

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
    blog_post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='translations', verbose_name=_('artigo do blog'))
    language = models.CharField(_('idioma'), max_length=2, choices=TRANSLATION_LANGUAGE_CHOICES)
    title = models.CharField(_('título'), max_length=255)
    excerpt = models.TextField(_('resumo'), help_text=_('Resumo curto para listagens'))
    content = models.TextField(_('conteúdo'), help_text=_('Conteúdo do artigo em Markdown'))
    meta_description = models.CharField(_('meta descrição'), max_length=160, blank=True)

    class Meta:
        verbose_name = _('tradução de artigo')
        verbose_name_plural = _('traduções de artigo')
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
        return render_markdown(self.content)


class Recipe(models.Model):
    class Difficulty(models.TextChoices):
        EASY = 'easy', _('Fácil')
        MEDIUM = 'medium', _('Médio')
        HARD = 'hard', _('Difícil')

    slug = models.SlugField(_('slug'), unique=True, max_length=200)
    cover_image = models.ImageField(_('imagem de capa'), upload_to='recipes/covers/', blank=True)
    prep_time = models.PositiveIntegerField(_('tempo de preparação'), help_text=_('Tempo de preparação em minutos'))
    cook_time = models.PositiveIntegerField(_('tempo de cozedura'), null=True, blank=True, help_text=_('Tempo de cozedura em minutos'))
    servings = models.PositiveIntegerField(_('doses'), default=4)
    difficulty = models.CharField(_('dificuldade'), max_length=10, choices=Difficulty.choices, default=Difficulty.MEDIUM)
    related_products = models.ManyToManyField(
        'catalog.Product',
        blank=True,
        related_name='recipes',
        verbose_name=_('produtos relacionados'),
        help_text=_('Produtos relacionados (comprar ingredientes)'),
    )
    tags = models.JSONField(_('etiquetas'), default=list, blank=True, help_text=_('Tags para filtragem, ex: ["vegetariano", "sem glúten"]'))
    is_published = models.BooleanField(_('publicado'), default=False, db_index=True)
    created_at = models.DateTimeField(_('criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('atualizado em'), auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('receita')
        verbose_name_plural = _('receitas')

    def __str__(self):
        return self.get_title('pt') or self.slug

    def clean(self):
        super().clean()
        translations = cast(Any, self).translations
        errors = {}
        draft_translation = getattr(self, '_pt_translation_draft', None) or {}

        self.slug = str(self.slug or '').strip()
        pt_title = draft_translation.get('title') or self.get_title('pt')
        if not self.slug and pt_title:
            self.slug = _generate_unique_slug(self.__class__, pt_title, instance_pk=self.pk)

        try:
            self.tags = _normalize_string_list(self.tags, field_name='tags')
        except ValidationError as error:
            errors.update(error.message_dict)

        if not self.is_published:
            if errors:
                raise ValidationError(errors)
            return

        publish_errors = []
        has_pt_translation = bool(draft_translation) or (self.pk and translations.filter(language='pt').exists())
        if not has_pt_translation:
            publish_errors.append(_('adicionar tradução PT'))
        else:
            if not (draft_translation.get('description') or self.get_summary(lang='pt')):
                publish_errors.append(_('preencher resumo PT'))
            if not (draft_translation.get('content') or self.get_content(lang='pt')):
                publish_errors.append(_('preencher conteúdo PT'))
        if not self.cover_image:
            publish_errors.append(_('carregar imagem de capa'))

        if publish_errors:
            errors['__all__'] = publish_errors
        if errors:
            raise ValidationError(errors)

    def get_title(self, lang=None):
        if not self.pk:
            return self.slug
        return get_translated_attr(self, 'title', default=self.slug, lang=lang)

    def get_description(self, lang=None):
        if not self.pk:
            return ''
        return get_translated_attr(self, 'description', default='', lang=lang)

    def get_summary(self, lang=None):
        return self.get_description(lang=lang)

    def get_content(self, lang=None):
        if not self.pk:
            return ''
        return get_translated_attr(self, 'content', default='', lang=lang)

    def get_rendered_content(self, lang=None):
        return render_markdown(self.get_content(lang=lang))

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
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='translations', verbose_name=_('receita'))
    language = models.CharField(_('idioma'), max_length=2, choices=TRANSLATION_LANGUAGE_CHOICES)
    title = models.CharField(_('título'), max_length=255)
    description = models.TextField(_('resumo'), help_text=_('Resumo curto'))
    content = models.TextField(_('conteúdo'), blank=True, help_text=_('Conteúdo da receita em Markdown'))
    ingredients = models.JSONField(
        _('ingredientes'),
        default=list,
        help_text=_('Lista de ingredientes: ["200g farinha", "2 ovos", ...]'),
    )
    instructions = models.JSONField(
        _('instruções'),
        default=list,
        help_text=_('Lista de passos de preparação: ["Pré-aquecer o forno...", "Misturar..."]'),
    )
    meta_description = models.CharField(_('meta descrição'), max_length=160, blank=True)

    class Meta:
        verbose_name = _('tradução de receita')
        verbose_name_plural = _('traduções de receita')
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'language'],
                name='content_unique_recipe_translation_language',
            ),
        ]

    def __str__(self):
        return f'{self.title} ({self.language})'

    @property
    def rendered_content(self):
        return render_markdown(self.content)

    def clean(self):
        super().clean()
        errors = {}

        try:
            self.ingredients = _normalize_string_list(self.ingredients, field_name='ingredients')
        except ValidationError as error:
            errors.update(error.message_dict)

        try:
            self.instructions = _normalize_string_list(self.instructions, field_name='instructions')
        except ValidationError as error:
            errors.update(error.message_dict)

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean(validate_unique=False, validate_constraints=False)
        return super().save(*args, **kwargs)
