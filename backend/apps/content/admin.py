from django.contrib import admin, messages
from django.contrib.admin import StackedInline
from django.db.models import Count, Q
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from unfold.admin import ModelAdmin, TabularInline

from apps.content.forms import (
    BlogPostAdminForm,
    RecipeAdminForm,
    RecipeTranslationAdminForm,
)
from apps.content.models import (
    BlogPost, BlogPostTranslation,
    Recipe, RecipeTranslation,
)
from apps.core.admin_helpers import DefaultLanguageInlineMixin, EditLinkAdminMixin, render_image_preview
from apps.core.admin_helpers import WorkflowAdminMixin, render_status_badge, render_summary_panel


# --- Blog ---

class BlogPostTranslationInline(DefaultLanguageInlineMixin, TabularInline):
    model = BlogPostTranslation
    extra = 1
    max_num = 3


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
    list_editable = ('is_published',)
    search_fields = ('slug', 'translations__title')
    search_help_text = 'Pesquise por slug ou título traduzido do artigo.'
    prepopulated_fields = {'slug': ()}
    inlines = [BlogPostTranslationInline]
    readonly_fields = ('editorial_readiness_panel', 'cover_image_preview', 'created_at', 'updated_at')
    list_filter_submit = True
    compressed_fields = True

    fieldsets = (
        (None, {
            'fields': ('slug', 'author', 'cover_image', 'cover_image_preview', 'tags'),
        }),
        ('Publicação', {
            'fields': ('is_published', 'published_at', 'editorial_readiness_panel'),
        }),
        ('Datas', {
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
                {'label': 'Rascunhos', 'value': queryset.filter(is_published=False).count(), 'context': 'Artigos por lançar', 'link': f'{base_url}?is_published__exact=0'},
                {'label': 'Publicados', 'value': queryset.filter(is_published=True).count(), 'context': 'Conteúdo visível', 'link': f'{base_url}?is_published__exact=1'},
                {'label': 'Sem capa', 'value': queryset.filter(cover_image='').count(), 'context': 'Impacto visual incompleto', 'link': base_url},
                {'label': 'Sem tradução PT', 'value': queryset.filter(pt_translation_count=0).count(), 'context': 'Bloqueia revisão editorial', 'link': base_url},
            ],
        }
        return super().changelist_view(request, extra_context=extra_context)

    def save_model(self, request, obj, form, change):
        if obj.is_published and obj.published_at is None:
            obj.published_at = timezone.now()
        if not obj.is_published:
            obj.published_at = None
        super().save_model(request, obj, form, change)

    def get_changeform_submit_actions(self, request, obj):
        if obj.is_published:
            return [{'action_name': '_unpublish_post', 'description': 'Retirar publicação'}]
        return [{'action_name': '_publish_post', 'description': 'Publicar artigo'}]

    def handle_changeform_submit_action(self, request, obj, action_name):
        if action_name == '_publish_post':
            blockers = self._blog_publish_blockers(obj)
            if blockers:
                self.message_user(request, 'Não foi possível publicar: ' + '; '.join(blockers), level=messages.WARNING)
            elif not obj.is_published:
                obj.is_published = True
                obj.published_at = timezone.now()
                obj.save(update_fields=['is_published', 'published_at', 'updated_at'])
                self.message_user(request, 'Artigo publicado.', level=messages.SUCCESS)
            return HttpResponseRedirect(request.path)

        if action_name == '_unpublish_post':
            if obj.is_published:
                obj.is_published = False
                obj.published_at = None
                obj.save(update_fields=['is_published', 'published_at', 'updated_at'])
                self.message_user(request, 'Artigo retirado de publicação.', level=messages.SUCCESS)
            return HttpResponseRedirect(request.path)

        return None

    @admin.display(description='Estado')
    def publication_badge(self, obj):
        if obj.is_published:
            return render_status_badge('Publicado', 'success')
        return render_status_badge('Rascunho', 'warning')

    @admin.display(description='Prontidão')
    def readiness_badge(self, obj):
        blockers = self._blog_publish_blockers(obj)
        if blockers:
            return render_status_badge('Em falta', 'danger')
        if obj.author_id is None:
            return render_status_badge('Rever autor', 'warning')
        return render_status_badge('Pronto', 'success')

    @admin.display(description='Checklist editorial')
    def editorial_readiness_panel(self, obj):
        if obj is None:
            return 'Guarde o artigo para ver o checklist editorial.'

        blockers = self._blog_publish_blockers(obj)
        footer = 'Bloqueadores: ' + '; '.join(blockers) if blockers else 'Artigo pronto para publicação. Confirme apenas o autor e o momento de publicação.'
        return render_summary_panel(
            'Checklist editorial',
            [
                ('Estado', 'Publicado' if obj.is_published else 'Rascunho'),
                ('Autor', obj.author or 'Sem autor atribuído'),
                ('Traduções', getattr(obj, 'translation_count', obj.translations.count())),
                ('Tradução PT', 'Sim' if getattr(obj, 'pt_translation_count', obj.translations.filter(language='pt').count()) else 'Não'),
                ('Imagem de capa', 'Sim' if obj.cover_image else 'Não'),
                ('Tags', ', '.join(obj.tags_list) or 'Sem tags'),
                ('Publicado em', obj.published_at or 'Ainda não publicado'),
            ],
            footer=footer,
        )

    def _blog_publish_blockers(self, obj):
        blockers = []
        if not getattr(obj, 'pt_translation_count', None):
            if not obj.translations.filter(language='pt').exists():
                blockers.append('adicionar tradução PT')
        if not obj.cover_image:
            blockers.append('carregar imagem de capa')
        return blockers

    @admin.display(description='Pré-visualização')
    def cover_image_preview(self, obj):
        return render_image_preview(getattr(obj, 'cover_image', None), width=120, height=120)


# --- Recipes ---

class RecipeTranslationInline(DefaultLanguageInlineMixin, StackedInline):
    model = RecipeTranslation
    form = RecipeTranslationAdminForm
    extra = 1
    max_num = 3


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
    list_editable = ('is_published',)
    search_fields = ('slug', 'translations__title')
    search_help_text = 'Pesquise por slug ou título traduzido da receita.'
    prepopulated_fields = {'slug': ()}
    filter_horizontal = ('related_products',)
    inlines = [RecipeTranslationInline]
    readonly_fields = ('editorial_readiness_panel', 'cover_image_preview', 'created_at', 'updated_at')
    list_filter_submit = True
    compressed_fields = True

    fieldsets = (
        (None, {
            'fields': ('slug', 'cover_image', 'cover_image_preview', 'tags'),
        }),
        ('Detalhes', {
            'fields': ('prep_time', 'cook_time', 'servings', 'difficulty'),
        }),
        ('Produtos Relacionados', {
            'fields': ('related_products',),
        }),
        ('Publicação', {
            'fields': ('is_published', 'editorial_readiness_panel'),
        }),
        ('Datas', {
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
                {'label': 'Rascunhos', 'value': queryset.filter(is_published=False).count(), 'context': 'Receitas por validar', 'link': f'{base_url}?is_published__exact=0'},
                {'label': 'Publicadas', 'value': queryset.filter(is_published=True).count(), 'context': 'Receitas disponíveis', 'link': f'{base_url}?is_published__exact=1'},
                {'label': 'Sem capa', 'value': queryset.filter(cover_image='').count(), 'context': 'Visual incompleto', 'link': base_url},
                {'label': 'Sem produtos relacionados', 'value': queryset.filter(related_product_count=0).count(), 'context': 'Oportunidade de cross-sell', 'link': base_url},
            ],
        }
        return super().changelist_view(request, extra_context=extra_context)

    def get_changeform_submit_actions(self, request, obj):
        if obj.is_published:
            return [{'action_name': '_unpublish_recipe', 'description': 'Retirar publicação'}]
        return [{'action_name': '_publish_recipe', 'description': 'Publicar receita'}]

    def handle_changeform_submit_action(self, request, obj, action_name):
        if action_name == '_publish_recipe':
            blockers = self._recipe_publish_blockers(obj)
            if blockers:
                self.message_user(request, 'Não foi possível publicar: ' + '; '.join(blockers), level=messages.WARNING)
            elif not obj.is_published:
                obj.is_published = True
                obj.save(update_fields=['is_published', 'updated_at'])
                self.message_user(request, 'Receita publicada.', level=messages.SUCCESS)
            return HttpResponseRedirect(request.path)

        if action_name == '_unpublish_recipe':
            if obj.is_published:
                obj.is_published = False
                obj.save(update_fields=['is_published', 'updated_at'])
                self.message_user(request, 'Receita retirada de publicação.', level=messages.SUCCESS)
            return HttpResponseRedirect(request.path)

        return None

    @admin.display(description='Estado')
    def publication_badge(self, obj):
        if obj.is_published:
            return render_status_badge('Publicada', 'success')
        return render_status_badge('Rascunho', 'warning')

    @admin.display(description='Prontidão')
    def readiness_badge(self, obj):
        blockers = self._recipe_publish_blockers(obj)
        if blockers:
            return render_status_badge('Em falta', 'danger')
        if getattr(obj, 'related_product_count', obj.related_products.count()) == 0:
            return render_status_badge('Sem cross-sell', 'warning')
        return render_status_badge('Pronta', 'success')

    @admin.display(ordering='related_product_count', description='Produtos')
    def related_products_count_display(self, obj):
        return getattr(obj, 'related_product_count', obj.related_products.count())

    @admin.display(description='Tempo total')
    def total_time_display(self, obj):
        return f'{obj.total_time} min'

    @admin.display(description='Checklist editorial')
    def editorial_readiness_panel(self, obj):
        if obj is None:
            return 'Guarde a receita para ver o checklist editorial.'

        pt_translation = obj.translations.filter(language='pt').first()
        has_ingredients = bool(pt_translation and obj.get_ingredients(lang='pt'))
        has_instructions = bool(pt_translation and obj.get_instructions(lang='pt'))
        blockers = self._recipe_publish_blockers(obj, pt_translation=pt_translation)
        footer = 'Bloqueadores: ' + '; '.join(blockers) if blockers else 'Receita pronta. Considere apenas relacionar produtos para reforçar conversão.'
        return render_summary_panel(
            'Checklist editorial',
            [
                ('Estado', 'Publicada' if obj.is_published else 'Rascunho'),
                ('Traduções', getattr(obj, 'translation_count', obj.translations.count())),
                ('Tradução PT', 'Sim' if getattr(obj, 'pt_translation_count', obj.translations.filter(language='pt').count()) else 'Não'),
                ('Ingredientes PT', 'Sim' if has_ingredients else 'Não'),
                ('Passos PT', 'Sim' if has_instructions else 'Não'),
                ('Imagem de capa', 'Sim' if obj.cover_image else 'Não'),
                ('Produtos relacionados', getattr(obj, 'related_product_count', obj.related_products.count())),
                ('Tags', ', '.join(obj.tags_list) or 'Sem tags'),
            ],
            footer=footer,
        )

    def _recipe_publish_blockers(self, obj, *, pt_translation=None):
        blockers = []
        translation = pt_translation
        if translation is None:
            translation = obj.translations.filter(language='pt').first()
        if translation is None:
            blockers.append('adicionar tradução PT')
        else:
            if not obj.get_ingredients(lang='pt'):
                blockers.append('preencher ingredientes PT')
            if not obj.get_instructions(lang='pt'):
                blockers.append('preencher passos PT')
        if not obj.cover_image:
            blockers.append('carregar imagem de capa')
        return blockers

    @admin.display(description='Pré-visualização')
    def cover_image_preview(self, obj):
        return render_image_preview(getattr(obj, 'cover_image', None), width=120, height=120)
