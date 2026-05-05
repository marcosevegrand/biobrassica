from django.contrib import admin, messages
from django.contrib.admin import StackedInline
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from typing import Any, cast
from unfold.admin import ModelAdmin, TabularInline

from apps.content.forms import (
    BlogPostAdminForm,
    BlogPostTranslationAdminForm,
    RecipeAdminForm,
    RecipeTranslationAdminForm,
)
from apps.content.models import (
    BlogPost, BlogPostTranslation,
    Recipe, RecipeTranslation,
)
from apps.core.admin_helpers import EditLinkAdminMixin, render_image_preview
from apps.core.admin_helpers import WorkflowAdminMixin, render_status_badge, render_summary_panel


# --- Blog ---

class BlogPostTranslationInline(TabularInline):
    model = BlogPostTranslation
    form = BlogPostTranslationAdminForm
    extra = 0
    max_num = 2
    fields = ('language', 'title', 'excerpt', 'content', 'meta_description')
    verbose_name = _('tradução')
    verbose_name_plural = _('Traduções EN/FR')
    section_cta_label = _('Adicionar tradução EN/FR')
    section_empty_title = _('Sem traduções EN/FR')
    section_empty_body = _('Adicione Inglês e/ou Francês quando precisar de tradução adicional.')

    def get_queryset(self, request):
        return super().get_queryset(request).exclude(language='pt')


@admin.register(BlogPost)
class BlogPostAdmin(WorkflowAdminMixin, EditLinkAdminMixin, ModelAdmin):
    list_before_template = 'admin/content/blogpost/workflow_overview.html'

    form = BlogPostAdminForm
    list_display = (
        '__str__',
        'author',
        'is_published',
        'publication_badge',
        'readiness_badge',
        'published_at',
        'created_at',
        'edit_link',
    )
    list_filter = ('is_published', 'author', 'created_at', 'published_at')
    search_fields = ('slug', 'translations__title')
    search_help_text = _('Pesquise por slug ou título traduzido do artigo.')
    inlines = [BlogPostTranslationInline]
    readonly_fields = ('editorial_readiness_panel', 'cover_image_preview', 'created_at', 'updated_at')
    list_filter_submit = True
    compressed_fields = True

    fieldsets = (
        (None, {
            'fields': ('slug', 'title', 'excerpt', 'content', 'author', 'cover_image', 'cover_image_preview', 'tags'),
        }),
        (_('Publicação'), {
            'fields': ('is_published', 'published_at', 'editorial_readiness_panel'),
        }),
        (_('Datas'), {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author').annotate(
            translation_count=Count('translations', distinct=True),
            pt_translation_count=Count('translations', filter=Q(translations__language='pt'), distinct=True),
        )

    def changelist_view(self, request, extra_context=None):
        queryset = self.get_queryset(request)
        base_url = reverse('admin:content_blogpost_changelist')
        extra_context = {
            **(extra_context or {}),
            'workflow_metric_cards': [
                {'label': _('Rascunhos'), 'value': queryset.filter(is_published=False).count(), 'context': _('Artigos por lançar'), 'link': f'{base_url}?is_published__exact=0'},
                {'label': _('Publicados'), 'value': queryset.filter(is_published=True).count(), 'context': _('Conteúdo visível'), 'link': f'{base_url}?is_published__exact=1'},
                {'label': _('Sem capa'), 'value': queryset.filter(cover_image='').count(), 'context': _('Impacto visual incompleto'), 'link': base_url},
                {'label': _('Sem tradução PT'), 'value': queryset.filter(pt_translation_count=0).count(), 'context': _('Bloqueia revisão editorial'), 'link': base_url},
            ],
        }
        return super().changelist_view(request, extra_context=extra_context)

    def save_model(self, request, obj, form, change):
        blog_post = cast(BlogPost, obj)
        blog_post.slug = blog_post.slug or ''
        publish_after_related = not change and blog_post.is_published
        if publish_after_related:
            blog_post.is_published = False
        if blog_post.is_published and blog_post.published_at is None:
            blog_post.published_at = timezone.now()
        if not blog_post.is_published:
            blog_post.published_at = None
        blog_post._publish_after_related = publish_after_related
        super().save_model(request, blog_post, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        blog_post = cast(BlogPost, form.instance)
        self._sync_pt_translation(blog_post, form.cleaned_data)
        if getattr(blog_post, '_publish_after_related', False):
            blog_post.is_published = True
            blog_post.published_at = timezone.now()
            blog_post.full_clean()
            blog_post.save(update_fields=['is_published', 'published_at', 'updated_at'])

    def get_changeform_submit_actions(self, request, obj):
        if obj.is_published:
            return [{'action_name': '_unpublish_post', 'description': _('Retirar publicação')}]
        return [{'action_name': '_publish_post', 'description': _('Publicar artigo')}]

    def handle_changeform_submit_action(self, request, obj, action_name):
        if action_name == '_publish_post':
            blockers = self._blog_publish_blockers(obj)
            if blockers:
                blocker_text = '; '.join(str(blocker) for blocker in blockers)
                self.message_user(request, _('Não foi possível publicar: ') + blocker_text, level=messages.WARNING)
            elif not obj.is_published:
                obj.is_published = True
                obj.published_at = timezone.now()
                obj.save(update_fields=['is_published', 'published_at', 'updated_at'])
                self.message_user(request, _('Artigo publicado.'), level=messages.SUCCESS)
            return HttpResponseRedirect(request.path)

        if action_name == '_unpublish_post':
            if obj.is_published:
                obj.is_published = False
                obj.published_at = None
                obj.save(update_fields=['is_published', 'published_at', 'updated_at'])
                self.message_user(request, _('Artigo retirado de publicação.'), level=messages.SUCCESS)
            return HttpResponseRedirect(request.path)

        return None

    @admin.display(description=_('Estado'))
    def publication_badge(self, obj):
        if obj.is_published:
            return render_status_badge(_('Publicado'), 'success')
        return render_status_badge(_('Rascunho'), 'warning')

    @admin.display(description=_('Prontidão'))
    def readiness_badge(self, obj):
        blockers = self._blog_publish_blockers(obj)
        if blockers:
            return render_status_badge(_('Em falta'), 'danger')
        if obj.author_id is None:
            return render_status_badge(_('Rever autor'), 'warning')
        return render_status_badge(_('Pronto'), 'success')

    @admin.display(description=_('Checklist editorial'))
    def editorial_readiness_panel(self, obj):
        if obj is None:
            return _('Guarde o artigo para ver o checklist editorial.')

        blockers = self._blog_publish_blockers(obj)
        footer = (_('Bloqueadores: ') + '; '.join(str(blocker) for blocker in blockers)) if blockers else _('Artigo pronto para publicação. Confirme apenas o autor e o momento de publicação.')
        return render_summary_panel(
            _('Checklist editorial'),
            [
                (_('Estado'), _('Publicado') if obj.is_published else _('Rascunho')),
                (_('Autor'), obj.author or _('Sem autor atribuído')),
                (_('Traduções'), getattr(obj, 'translation_count', obj.translations.count())),
                (_('Tradução PT'), _('Sim') if getattr(obj, 'pt_translation_count', obj.translations.filter(language='pt').count()) else _('Não')),
                (_('Imagem de capa'), _('Sim') if obj.cover_image else _('Não')),
                (_('Tags'), ', '.join(obj.tags_list) or _('Sem tags')),
                (_('Publicado em'), obj.published_at or _('Ainda não publicado')),
            ],
            footer=footer,
        )

    def _blog_publish_blockers(self, obj):
        return self._publication_blockers(obj)

    def _sync_pt_translation(self, obj, cleaned_data):
        BlogPostTranslation.objects.update_or_create(
            blog_post=obj,
            language='pt',
            defaults={
                'title': cleaned_data['title'],
                'excerpt': cleaned_data['excerpt'],
                'content': cleaned_data['content'],
                'meta_description': '',
            },
        )
        if not obj.slug:
            obj.slug = obj.slug or ''
            obj.full_clean()
            obj.save(update_fields=['slug', 'updated_at'])

    def _publication_blockers(self, obj: Any):
        original_is_published = obj.is_published
        original_published_at = getattr(obj, 'published_at', None)
        obj.is_published = True
        if hasattr(obj, 'published_at') and obj.published_at is None:
            obj.published_at = timezone.now()
        try:
            obj.full_clean()
        except ValidationError as error:
            return list(error.messages)
        finally:
            obj.is_published = original_is_published
            if hasattr(obj, 'published_at'):
                obj.published_at = original_published_at
        return []

    @admin.display(description=_('Pré-visualização'))
    def cover_image_preview(self, obj):
        return render_image_preview(getattr(obj, 'cover_image', None), width=120, height=120)


# --- Recipes ---

class RecipeTranslationInline(StackedInline):
    model = RecipeTranslation
    form = RecipeTranslationAdminForm
    extra = 0
    max_num = 2
    fields = ('language', 'title', 'description', 'content', 'meta_description')
    verbose_name = _('tradução')
    verbose_name_plural = _('Traduções EN/FR')
    section_cta_label = _('Adicionar tradução EN/FR')
    section_empty_title = _('Sem traduções EN/FR')
    section_empty_body = _('Adicione Inglês e/ou Francês quando precisar de tradução adicional.')

    def get_queryset(self, request):
        return super().get_queryset(request).exclude(language='pt')


@admin.register(Recipe)
class RecipeAdmin(WorkflowAdminMixin, EditLinkAdminMixin, ModelAdmin):
    list_before_template = 'admin/content/recipe/workflow_overview.html'

    form = RecipeAdminForm
    list_display = (
        '__str__',
        'difficulty',
        'prep_time',
        'total_time_display',
        'servings',
        'is_published',
        'publication_badge',
        'readiness_badge',
        'related_products_count_display',
        'created_at',
        'edit_link',
    )
    list_filter = ('is_published', 'difficulty', 'created_at', 'related_products')
    search_fields = ('slug', 'translations__title')
    search_help_text = _('Pesquise por slug ou título traduzido da receita.')
    filter_horizontal = ('related_products',)
    inlines = [RecipeTranslationInline]
    readonly_fields = ('editorial_readiness_panel', 'cover_image_preview', 'created_at', 'updated_at')
    list_filter_submit = True
    compressed_fields = True

    fieldsets = (
        (None, {
            'fields': ('slug', 'title', 'description', 'content', 'cover_image', 'cover_image_preview', 'tags'),
        }),
        (_('Detalhes'), {
            'fields': ('prep_time', 'cook_time', 'servings', 'difficulty'),
        }),
        (_('Produtos Relacionados'), {
            'fields': ('related_products',),
        }),
        (_('Publicação'), {
            'fields': ('is_published', 'editorial_readiness_panel'),
        }),
        (_('Datas'), {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            translation_count=Count('translations', distinct=True),
            pt_translation_count=Count('translations', filter=Q(translations__language='pt'), distinct=True),
            related_product_count=Count('related_products', distinct=True),
        )

    def changelist_view(self, request, extra_context=None):
        queryset = self.get_queryset(request)
        base_url = reverse('admin:content_recipe_changelist')
        extra_context = {
            **(extra_context or {}),
            'workflow_metric_cards': [
                {'label': _('Rascunhos'), 'value': queryset.filter(is_published=False).count(), 'context': _('Receitas por validar'), 'link': f'{base_url}?is_published__exact=0'},
                {'label': _('Publicadas'), 'value': queryset.filter(is_published=True).count(), 'context': _('Receitas disponíveis'), 'link': f'{base_url}?is_published__exact=1'},
                {'label': _('Sem capa'), 'value': queryset.filter(cover_image='').count(), 'context': _('Visual incompleto'), 'link': base_url},
                {'label': _('Sem produtos relacionados'), 'value': queryset.filter(related_product_count=0).count(), 'context': _('Oportunidade de cross-sell'), 'link': base_url},
            ],
        }
        return super().changelist_view(request, extra_context=extra_context)

    def get_changeform_submit_actions(self, request, obj):
        if obj.is_published:
            return [{'action_name': '_unpublish_recipe', 'description': _('Retirar publicação')}]
        return [{'action_name': '_publish_recipe', 'description': _('Publicar receita')}]

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        recipe = cast(Recipe, form.instance)
        self._sync_pt_translation(recipe, form.cleaned_data)
        if getattr(recipe, '_publish_after_related', False):
            recipe.is_published = True
            recipe.full_clean()
            recipe.save(update_fields=['is_published', 'updated_at'])

    def handle_changeform_submit_action(self, request, obj, action_name):
        if action_name == '_publish_recipe':
            blockers = self._recipe_publish_blockers(obj)
            if blockers:
                blocker_text = '; '.join(str(blocker) for blocker in blockers)
                self.message_user(request, _('Não foi possível publicar: ') + blocker_text, level=messages.WARNING)
            elif not obj.is_published:
                obj.is_published = True
                obj.save(update_fields=['is_published', 'updated_at'])
                self.message_user(request, _('Receita publicada.'), level=messages.SUCCESS)
            return HttpResponseRedirect(request.path)

        if action_name == '_unpublish_recipe':
            if obj.is_published:
                obj.is_published = False
                obj.save(update_fields=['is_published', 'updated_at'])
                self.message_user(request, _('Receita retirada de publicação.'), level=messages.SUCCESS)
            return HttpResponseRedirect(request.path)

        return None

    def save_model(self, request, obj, form, change):
        recipe = cast(Recipe, obj)
        recipe.slug = recipe.slug or ''
        recipe._publish_after_related = not change and recipe.is_published
        if recipe._publish_after_related:
            recipe.is_published = False
        super().save_model(request, recipe, form, change)

    @admin.display(description=_('Estado'))
    def publication_badge(self, obj):
        if obj.is_published:
            return render_status_badge(_('Publicada'), 'success')
        return render_status_badge(_('Rascunho'), 'warning')

    @admin.display(description=_('Prontidão'))
    def readiness_badge(self, obj):
        blockers = self._recipe_publish_blockers(obj)
        if blockers:
            return render_status_badge(_('Em falta'), 'danger')
        if getattr(obj, 'related_product_count', obj.related_products.count()) == 0:
            return render_status_badge(_('Sem cross-sell'), 'warning')
        return render_status_badge(_('Pronta'), 'success')

    @admin.display(ordering='related_product_count', description=_('Produtos'))
    def related_products_count_display(self, obj):
        return getattr(obj, 'related_product_count', obj.related_products.count())

    @admin.display(description=_('Tempo total'))
    def total_time_display(self, obj):
        return f'{obj.total_time} min'

    @admin.display(description=_('Checklist editorial'))
    def editorial_readiness_panel(self, obj):
        if obj is None:
            return _('Guarde a receita para ver o checklist editorial.')

        pt_translation = obj.translations.filter(language='pt').first()
        has_summary = bool(pt_translation and obj.get_summary(lang='pt'))
        has_content = bool(pt_translation and obj.get_content(lang='pt'))
        blockers = self._recipe_publish_blockers(obj, pt_translation=pt_translation)
        footer = (_('Bloqueadores: ') + '; '.join(str(blocker) for blocker in blockers)) if blockers else _('Receita pronta. Considere apenas relacionar produtos para reforçar conversão.')
        return render_summary_panel(
            _('Checklist editorial'),
            [
                (_('Estado'), _('Publicada') if obj.is_published else _('Rascunho')),
                (_('Traduções'), getattr(obj, 'translation_count', obj.translations.count())),
                (_('Tradução PT'), _('Sim') if getattr(obj, 'pt_translation_count', obj.translations.filter(language='pt').count()) else _('Não')),
                (_('Resumo PT'), _('Sim') if has_summary else _('Não')),
                (_('Conteúdo PT'), _('Sim') if has_content else _('Não')),
                (_('Imagem de capa'), _('Sim') if obj.cover_image else _('Não')),
                (_('Produtos relacionados'), getattr(obj, 'related_product_count', obj.related_products.count())),
                (_('Tags'), ', '.join(obj.tags_list) or _('Sem tags')),
            ],
            footer=footer,
        )

    def _recipe_publish_blockers(self, obj, *, pt_translation=None):
        return self._publication_blockers(obj)

    def _sync_pt_translation(self, obj, cleaned_data):
        RecipeTranslation.objects.update_or_create(
            recipe=obj,
            language='pt',
            defaults={
                'title': cleaned_data['title'],
                'description': cleaned_data['description'],
                'content': cleaned_data['content'],
                'ingredients': [],
                'instructions': [],
                'meta_description': '',
            },
        )
        if not obj.slug:
            obj.slug = obj.slug or ''
            obj.full_clean()
            obj.save(update_fields=['slug', 'updated_at'])

    def _publication_blockers(self, obj):
        original_is_published = obj.is_published
        obj.is_published = True
        try:
            obj.full_clean()
        except ValidationError as error:
            return list(error.messages)
        finally:
            obj.is_published = original_is_published
        return []

    @admin.display(description=_('Pré-visualização'))
    def cover_image_preview(self, obj):
        return render_image_preview(getattr(obj, 'cover_image', None), width=120, height=120)
