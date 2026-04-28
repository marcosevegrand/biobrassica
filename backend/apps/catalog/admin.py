import uuid
from typing import cast

from django.contrib import admin
from django.contrib.admin import StackedInline
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.http import HttpResponseRedirect
from django.forms.models import BaseInlineFormSet
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from unfold.admin import ModelAdmin, TabularInline

from apps.catalog.forms import ProductAdminForm, ProductImageInlineForm, ProductTranslationInlineForm
from apps.catalog.models import (
    Category, CategoryTranslation,
    Product, ProductTranslation, ProductImage,
    Location, DeliveryMethod,
)
from apps.core.admin_helpers import (
    DefaultLanguageInlineMixin,
    EditLinkAdminMixin,
    OrderableAdminMixin,
    render_image_preview,
    render_status_badge,
    render_summary_panel,
    WorkflowAdminMixin,
)
from apps.core.translations import translation_prefetch


# --- Location & Delivery ---

@admin.register(Location)
class LocationAdmin(WorkflowAdminMixin, OrderableAdminMixin, EditLinkAdminMixin, ModelAdmin):
    list_before_template = 'admin/catalog/location/workflow_overview.html'
    list_display = ('order_controls', 'name', 'pickup_location_code_display', 'location_readiness_badge', 'product_count_display', 'address_short', 'is_active', 'edit_link')
    list_editable = ('is_active',)
    search_fields = ('name', 'address', 'phone', 'email')
    search_help_text = _('Pesquise por nome, morada, telefone ou email da loja.')
    readonly_fields = ('location_operations_panel', 'image_preview')
    list_filter = ('is_active',)
    list_filter_submit = True
    compressed_fields = True

    fieldsets = (
        (_('Operação'), {
            'fields': ('name', 'pickup_location_code', 'is_active', 'location_operations_panel'),
        }),
        (_('Contacto e presença'), {
            'fields': ('address', 'phone', 'email', 'opening_hours', 'pickup_hours', 'map_embed_url', 'image', 'image_preview'),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(product_count=Count('products', distinct=True))

    def changelist_view(self, request, extra_context=None):
        queryset = self.get_queryset(request)
        base_url = reverse('admin:catalog_location_changelist')
        extra_context = {
            **(extra_context or {}),
            'workflow_metric_cards': [
                {'label': _('Lojas ativas'), 'value': queryset.filter(is_active=True).count(), 'context': _('Disponíveis no website e catálogo'), 'link': f'{base_url}?is_active__exact=1'},
                {'label': _('Sem imagem'), 'value': queryset.filter(image='').count(), 'context': _('Página contactos incompleta'), 'link': base_url},
                {'label': _('Sem mapa'), 'value': queryset.filter(map_embed_url='').count(), 'context': _('Falta contexto visual'), 'link': base_url},
                {'label': _('Sem produtos ligados'), 'value': queryset.filter(product_count=0).count(), 'context': _('Pickup sem catálogo associado'), 'link': base_url},
            ],
        }
        return super().changelist_view(request, extra_context=extra_context)

    def get_changeform_custom_tools(self, request, obj):
        return [
            {
                'title': _('Produtos desta loja'),
                'link': reverse('admin:catalog_product_changelist') + f'?available_locations__id__exact={obj.pk}',
                'icon': 'inventory_2',
                'blank': False,
            },
        ]

    def get_changeform_submit_actions(self, request, obj):
        if obj.is_active:
            return [{'action_name': '_deactivate_location', 'description': _('Desativar loja')}]
        return [{'action_name': '_activate_location', 'description': _('Ativar loja')}]

    def handle_changeform_submit_action(self, request, obj, action_name):
        if action_name == '_deactivate_location' and obj.is_active:
            obj.is_active = False
            obj.save(update_fields=['is_active'])
            self.message_user(request, _('Loja desativada.'), level=messages.SUCCESS)
            return HttpResponseRedirect(request.path)

        if action_name == '_activate_location' and not obj.is_active:
            obj.is_active = True
            obj.save(update_fields=['is_active'])
            self.message_user(request, _('Loja ativada.'), level=messages.SUCCESS)
            return HttpResponseRedirect(request.path)

        return None

    @admin.display(description=_('Morada'))
    def address_short(self, obj):
        return (obj.address[:60] + '…') if len(obj.address) > 60 else obj.address

    @admin.display(ordering='product_count', description=_('Produtos'))
    def product_count_display(self, obj):
        return getattr(obj, 'product_count', obj.products.count())

    @admin.display(ordering='pickup_location_code', description=_('Checkout'))
    def pickup_location_code_display(self, obj):
        return obj.get_pickup_location_code_display() if obj.pickup_location_code else '—'

    @admin.display(description=_('Prontidão'))
    def location_readiness_badge(self, obj):
        if not obj.is_active:
            return render_status_badge(_('Inativa'), 'warning')
        if not obj.pickup_location_code:
            return render_status_badge(_('Rever checkout'), 'warning')
        if not obj.image or not obj.map_embed_url:
            return render_status_badge(_('Rever contactos'), 'warning')
        return render_status_badge(_('Pronta'), 'success')

    @admin.display(description=_('Resumo operacional'))
    def location_operations_panel(self, obj):
        if obj is None:
            return _('Guarde a localização para ver o resumo operacional.')

        return render_summary_panel(
            _('Pickup e contactos'),
            [
                (_('Estado'), _('Ativa') if obj.is_active else _('Inativa')),
                (_('Checkout'), obj.get_pickup_location_code_display() if obj.pickup_location_code else _('Em falta')),
                (_('Produtos ligados'), getattr(obj, 'product_count', obj.products.count())),
                (_('Telefone'), obj.phone or _('Por preencher')),
                (_('Email'), obj.email or _('Por preencher')),
                (_('Horário'), obj.opening_hours or _('Por preencher')),
                (_('Mapa'), _('Configurado') if obj.map_embed_url else _('Em falta')),
            ],
            footer=_('Esta ficha alimenta a página de contactos e o contexto de levantamento em loja.'),
        )

    @admin.display(description=_('Pré-visualização'))
    def image_preview(self, obj):
        return render_image_preview(getattr(obj, 'image', None), width=112, height=84)


@admin.register(DeliveryMethod)
class DeliveryMethodAdmin(WorkflowAdminMixin, OrderableAdminMixin, EditLinkAdminMixin, ModelAdmin):
    list_before_template = 'admin/catalog/deliverymethod/workflow_overview.html'
    list_display = ('order_controls', 'name', 'delivery_status_badge', 'description_short', 'is_active', 'edit_link')
    list_editable = ('is_active',)
    search_fields = ('name', 'description')
    search_help_text = _('Pesquise pelo nome ou descrição do método.')
    readonly_fields = ('delivery_operations_panel',)
    list_filter = ('is_active',)
    list_filter_submit = True
    compressed_fields = True

    fieldsets = (
        (_('Operação'), {
            'fields': ('name', 'is_active', 'delivery_operations_panel'),
        }),
        (_('Descrição'), {
            'fields': ('description',),
        }),
    )

    def changelist_view(self, request, extra_context=None):
        queryset = self.get_queryset(request)
        base_url = reverse('admin:catalog_deliverymethod_changelist')
        extra_context = {
            **(extra_context or {}),
            'workflow_metric_cards': [
                {'label': _('Ativos'), 'value': queryset.filter(is_active=True).count(), 'context': _('Disponíveis ao negócio'), 'link': f'{base_url}?is_active__exact=1'},
                {'label': _('Inativos'), 'value': queryset.filter(is_active=False).count(), 'context': _('Guardados para revisão'), 'link': f'{base_url}?is_active__exact=0'},
                {'label': _('Sem descrição'), 'value': queryset.filter(description='').count(), 'context': _('Mensagem operacional incompleta'), 'link': base_url},
                {'label': _('Total'), 'value': queryset.count(), 'context': _('Configuração de entrega'), 'link': base_url},
            ],
        }
        return super().changelist_view(request, extra_context=extra_context)

    def get_changeform_submit_actions(self, request, obj):
        if obj.is_active:
            return [{'action_name': '_deactivate_method', 'description': _('Desativar método')}]
        return [{'action_name': '_activate_method', 'description': _('Ativar método')}]

    def handle_changeform_submit_action(self, request, obj, action_name):
        if action_name == '_deactivate_method' and obj.is_active:
            obj.is_active = False
            obj.save(update_fields=['is_active'])
            self.message_user(request, _('Método desativado.'), level=messages.SUCCESS)
            return HttpResponseRedirect(request.path)

        if action_name == '_activate_method' and not obj.is_active:
            obj.is_active = True
            obj.save(update_fields=['is_active'])
            self.message_user(request, _('Método ativado.'), level=messages.SUCCESS)
            return HttpResponseRedirect(request.path)

        return None

    @admin.display(description=_('Descrição'))
    def description_short(self, obj):
        return (obj.description[:60] + '…') if len(obj.description) > 60 else obj.description

    @admin.display(description='Estado')
    def delivery_status_badge(self, obj):
        if not obj.is_active:
            return render_status_badge(_('Inativo'), 'warning')
        if not obj.description:
            return render_status_badge(_('Completar descrição'), 'info')
        return render_status_badge(_('Pronto'), 'success')

    @admin.display(description=_('Resumo operacional'))
    def delivery_operations_panel(self, obj):
        if obj is None:
            return _('Guarde o método para ver o resumo operacional.')

        return render_summary_panel(
            _('Resumo do método'),
            [
                (_('Estado'), _('Ativo') if obj.is_active else _('Inativo')),
                (_('Nome'), obj.name),
                (_('Descrição'), obj.description or _('Por preencher')),
            ],
            footer=_('Use esta ficha para manter a linguagem operacional consistente no backoffice.'),
        )


# --- Category ---

class CategoryTranslationInline(DefaultLanguageInlineMixin, TabularInline):
    model = CategoryTranslation
    max_num = 3

    def get_extra(self, request, obj=None, **kwargs):
        return 0


@admin.register(Category)
class CategoryAdmin(WorkflowAdminMixin, OrderableAdminMixin, EditLinkAdminMixin, ModelAdmin):
    list_before_template = 'admin/catalog/category/workflow_overview.html'
    list_display = ('order_controls', '__str__', 'slug', 'category_health_badge', 'product_count_display', 'is_active', 'featured_badge', 'edit_link')
    list_editable = ('is_active',)
    search_fields = ('slug', 'translations__name')
    search_help_text = _('Pesquise por slug ou nome traduzido da categoria.')
    prepopulated_fields = {'slug': ()}
    inlines = [CategoryTranslationInline]
    readonly_fields = ('category_readiness_panel',)
    list_filter_submit = True
    compressed_fields = True

    fieldsets = (
        (_('Publicação'), {
            'fields': ('slug', 'is_active', 'is_featured', 'featured_message', 'category_readiness_panel'),
        }),
        (_('Imagem'), {
            'fields': ('image', 'order'),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            product_count=Count('products', distinct=True),
            active_product_count=Count('products', filter=Q(products__is_active=True), distinct=True),
            translation_count=Count('translations', distinct=True),
            pt_translation_count=Count('translations', filter=Q(translations__language='pt'), distinct=True),
        )

    def changelist_view(self, request, extra_context=None):
        queryset = self.get_queryset(request)
        base_url = reverse('admin:catalog_category_changelist')
        extra_context = {
            **(extra_context or {}),
            'workflow_metric_cards': [
                {'label': _('Ativas'), 'value': queryset.filter(is_active=True).count(), 'context': _('Categorias visíveis'), 'link': f'{base_url}?is_active__exact=1'},
                {'label': _('Em destaque'), 'value': queryset.filter(is_featured=True).count(), 'context': _('Merchandising da homepage'), 'link': f'{base_url}?is_featured__exact=1'},
                {'label': _('Sem tradução PT'), 'value': queryset.filter(pt_translation_count=0).count(), 'context': _('Bloqueia publicação base'), 'link': base_url},
                {'label': _('Sem produtos ativos'), 'value': queryset.filter(active_product_count=0).count(), 'context': _('Rever merchandising'), 'link': base_url},
            ],
        }
        return super().changelist_view(request, extra_context=extra_context)

    def get_changeform_custom_tools(self, request, obj):
        return [
            {
                'title': _('Produtos da categoria'),
                'link': reverse('admin:catalog_product_changelist') + f'?category__id__exact={obj.pk}',
                'icon': 'inventory_2',
                'blank': False,
            },
        ]

    def get_changeform_submit_actions(self, request, obj):
        if obj.is_featured:
            return [{'action_name': '_unfeature_category', 'description': _('Remover destaque')}]
        return [{'action_name': '_feature_category', 'description': _('Destacar categoria')}]

    def handle_changeform_submit_action(self, request, obj, action_name):
        if action_name == '_feature_category' and not obj.is_featured:
            obj.is_featured = True
            obj.save(update_fields=['is_featured'])
            self.message_user(request, _('Categoria destacada.'), level=messages.SUCCESS)
            return HttpResponseRedirect(request.path)

        if action_name == '_unfeature_category' and obj.is_featured:
            obj.is_featured = False
            obj.save(update_fields=['is_featured'])
            self.message_user(request, _('Categoria retirada do destaque.'), level=messages.SUCCESS)
            return HttpResponseRedirect(request.path)

        return None

    @admin.display(ordering='product_count', description=_('Produtos'))
    def product_count_display(self, obj):
        return getattr(obj, 'product_count', obj.products.count())

    @admin.display(description=_('Prontidão'))
    def category_health_badge(self, obj):
        if not obj.is_active:
            return render_status_badge(_('Inativa'), 'warning')
        if getattr(obj, 'pt_translation_count', 0) == 0:
            return render_status_badge(_('Sem PT'), 'danger')
        if getattr(obj, 'active_product_count', 0) == 0:
            return render_status_badge(_('Sem produtos ativos'), 'warning')
        return render_status_badge(_('Pronta'), 'success')

    @admin.display(description=_('Destaque'))
    def featured_badge(self, obj):
        if obj.is_featured:
            return render_status_badge(_('Em destaque'), 'info')
        return render_status_badge(_('Normal'), 'neutral')

    @admin.display(description=_('Checklist de categoria'))
    def category_readiness_panel(self, obj):
        if obj is None:
            return _('Guarde a categoria para ver o checklist operacional.')

        return render_summary_panel(
            _('Checklist da categoria'),
            [
                (_('Estado'), _('Ativa') if obj.is_active else _('Inativa')),
                (_('Destaque'), _('Sim') if obj.is_featured else _('Não')),
                (_('Traduções'), getattr(obj, 'translation_count', obj.translations.count())),
                (_('Tradução PT'), _('Sim') if getattr(obj, 'pt_translation_count', obj.translations.filter(language='pt').count()) else _('Não')),
                (_('Produtos totais'), getattr(obj, 'product_count', obj.products.count())),
                (_('Produtos ativos'), getattr(obj, 'active_product_count', obj.products.filter(is_active=True).count())),
            ],
            footer=_('Use o atalho superior para abrir o catálogo filtrado desta categoria.'),
        )


# --- Product ---

class RequiredTranslationInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        active_forms = [form for form in self.forms if form.cleaned_data and not form.cleaned_data.get('DELETE', False)]
        if not active_forms:
            raise ValidationError(_('O produto deve ter pelo menos uma designação, descrição, alergénicos e ingredientes.'))


class RequiredProductImageInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        active_forms = [form for form in self.forms if form.cleaned_data and not form.cleaned_data.get('DELETE', False)]
        primary_forms = [form for form in active_forms if form.cleaned_data.get('is_primary')]
        if len(primary_forms) > 1:
            raise ValidationError(_('Defina apenas uma imagem principal por produto.'))

class ProductTranslationInline(DefaultLanguageInlineMixin, StackedInline):
    model = ProductTranslation
    form = ProductTranslationInlineForm
    formset = RequiredTranslationInlineFormSet
    max_num = 3
    extra = 0
    verbose_name = _('tradução')
    verbose_name_plural = _('Traduções do produto')
    section_description = _('Adicione apenas as traduções necessárias. Comece por Português para desbloquear a publicação.')
    section_cta_label = _('Adicionar tradução')
    section_empty_title = _('Nenhuma tradução adicionada')
    section_empty_body = _('Crie primeiro a versão em Português. Depois adicione apenas os idiomas que a operação realmente precisa.')

    def get_extra(self, request, obj=None, **kwargs):
        return 0


class ProductImageInline(TabularInline):
    model = ProductImage
    form = ProductImageInlineForm
    formset = RequiredProductImageInlineFormSet
    extra = 0
    min_num = 0
    validate_min = False
    fields = ('image', 'image_preview', 'alt_text', 'order', 'is_primary')
    readonly_fields = ('image_preview',)
    verbose_name = _('imagem')
    verbose_name_plural = _('Imagens do produto')
    section_description = _('A galeria começa vazia. Adicione só as imagens finais e marque uma como principal.')
    section_cta_label = _('Adicionar imagem')
    section_empty_title = _('Galeria vazia')
    section_empty_body = _('Adicione imagens finais do produto e defina uma como principal para a loja e o merchandising.')

    @admin.display(description='Pré-visualização')
    def image_preview(self, obj):
        return render_image_preview(getattr(obj, 'image', None), width=56, height=56)


class ProductOpsQueueFilter(admin.SimpleListFilter):
    title = _('fila operacional')
    parameter_name = 'ops_queue'

    def lookups(self, request, model_admin):
        return [
            ('out-of-stock', _('Sem stock')),
            ('low-stock', _('Baixo stock')),
            ('missing-image', _('Sem imagem principal')),
            ('missing-pt', _('Sem tradução PT')),
            ('ready-to-reactivate', _('Prontos para reativar')),
            ('no-locations', _('Sem localizações')),
        ]

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'out-of-stock':
            return queryset.filter(is_active=True, stock=0)
        if value == 'low-stock':
            return queryset.filter(is_active=True, stock__gt=0, stock__lt=5)
        if value == 'missing-image':
            return queryset.filter(primary_image_count=0)
        if value == 'missing-pt':
            return queryset.filter(pt_translation_count=0)
        if value == 'ready-to-reactivate':
            return queryset.filter(
                is_active=False,
                stock__gt=0,
                pt_translation_count__gt=0,
                primary_image_count__gt=0,
                location_count__gt=0,
            )
        if value == 'no-locations':
            return queryset.filter(available_locations__isnull=True).distinct()
        return queryset


@admin.register(Product)
class ProductAdmin(WorkflowAdminMixin, EditLinkAdminMixin, ModelAdmin):
    TEMP_SLUG_PREFIX = 'produto-temp-'
    list_before_template = 'admin/catalog/product/workflow_overview.html'

    form = ProductAdminForm
    list_display = ('__str__', 'brand', 'category', 'price', 'quantity', 'stock', 'stock_badge', 'availability_badge', 'replenishment_priority', 'catalog_health_display', 'allow_shipping', 'is_active', 'is_preview_only', 'is_highlight', 'edit_link')
    list_filter = (ProductOpsQueueFilter, 'category', 'allow_shipping', 'is_active', 'is_preview_only', 'is_highlight', 'available_locations')
    list_editable = ('price', 'allow_shipping', 'stock', 'is_highlight')
    search_fields = ('slug', 'brand', 'bio_code', 'translations__name')
    search_help_text = _('Pesquise por slug, marca, código bio ou nome traduzido do produto.')
    prepopulated_fields = {'slug': ()}
    filter_horizontal = ('available_locations',)
    inlines = [ProductTranslationInline, ProductImageInline]
    readonly_fields = ('catalog_readiness_panel', 'replenishment_panel', 'stock_badge', 'availability_badge', 'created_at', 'updated_at')
    list_filter_submit = True
    compressed_fields = True

    fieldsets = (
        (_('Publicação e merchandising'), {
            'fields': ('category', 'slug', ('brand_choice', 'brand_custom'), 'bio_code', 'is_active', 'is_highlight', 'catalog_readiness_panel')
        }),
        (_('Venda e disponibilidade'), {
            'fields': ('price', ('quantity_value', 'quantity_unit'), 'stock', 'stock_badge', 'availability_badge', 'replenishment_panel', 'is_preview_only', 'allow_shipping', 'available_locations')
        }),
        (_('Datas'), {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def changelist_view(self, request, extra_context=None):
        queryset = self.get_queryset(request)
        base_url = reverse('admin:catalog_product_changelist')
        extra_context = {
            **(extra_context or {}),
            'workflow_metric_cards': [
                {'label': _('Ativos'), 'value': queryset.filter(is_active=True).count(), 'context': _('Catálogo visível'), 'link': f'{base_url}?is_active__exact=1'},
                {'label': _('Pré-visualização'), 'value': queryset.filter(is_active=True, is_preview_only=True).count(), 'context': _('Visíveis sem compra online'), 'link': f'{base_url}?is_preview_only__exact=1'},
                {'label': _('Sem stock'), 'value': queryset.filter(is_active=True, stock=0).count(), 'context': _('Rutura imediata'), 'link': f'{base_url}?ops_queue=out-of-stock'},
                {'label': _('Baixo stock'), 'value': queryset.filter(is_active=True, stock__gt=0, stock__lt=5).count(), 'context': _('Reposição desta semana'), 'link': f'{base_url}?ops_queue=low-stock'},
                {'label': _('Sem imagem principal'), 'value': queryset.filter(primary_image_count=0).count(), 'context': _('Bloqueia merchandising'), 'link': f'{base_url}?ops_queue=missing-image'},
                {'label': _('Prontos a reativar'), 'value': queryset.filter(is_active=False, stock__gt=0, pt_translation_count__gt=0, primary_image_count__gt=0, location_count__gt=0).count(), 'context': _('Stock já reposto'), 'link': f'{base_url}?ops_queue=ready-to-reactivate'},
            ],
        }
        return super().changelist_view(request, extra_context=extra_context)

    class Media:
        css = {
            'all': ('css/admin/product_editor.css',),
        }
        js = ('js/admin/product_slug_autofill.js', 'js/admin/product_editor.js')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category').prefetch_related(
            translation_prefetch(ProductTranslation),
            translation_prefetch(CategoryTranslation, related_name='category__translations'),
        ).annotate(
            translation_count=Count('translations', distinct=True),
            pt_translation_count=Count('translations', filter=Q(translations__language='pt'), distinct=True),
            image_count=Count('images', distinct=True),
            primary_image_count=Count('images', filter=Q(images__is_primary=True), distinct=True),
            location_count=Count('available_locations', distinct=True),
        )

    def get_changeform_custom_tools(self, request, obj):
        return [
            {
                'title': _('Imagens do produto'),
                'link': reverse('admin:catalog_productimage_changelist') + f'?product__id__exact={obj.pk}',
                'icon': 'photo_library',
                'blank': False,
            },
            {
                'title': _('Abrir categoria'),
                'link': reverse('admin:catalog_category_change', args=[obj.category_id]),
                'icon': 'category',
                'blank': False,
            },
            {
                'title': _('Fila de reposição'),
                'link': reverse('admin:catalog_product_changelist') + '?ops_queue=low-stock',
                'icon': 'inventory_2',
                'blank': False,
            },
        ]

    def get_changeform_submit_actions(self, request, obj):
        actions = []
        if obj.is_active and obj.stock == 0 and not obj.is_preview_only:
            actions.append({'action_name': '_deactivate_until_restock', 'description': _('Desativar até reposição')})
        if not obj.is_active and self._can_reactivate_product(obj):
            actions.append({'action_name': '_reactivate_product', 'description': _('Reativar produto')})
        return actions

    def handle_changeform_submit_action(self, request, obj, action_name):
        if action_name == '_deactivate_until_restock' and obj.is_active and obj.stock == 0 and not obj.is_preview_only:
            obj.is_active = False
            obj.save(update_fields=['is_active', 'updated_at'])
            self.message_user(request, _('Produto desativado até reposição.'), level=messages.SUCCESS)
            return HttpResponseRedirect(request.path)

        if action_name == '_reactivate_product' and not obj.is_active and self._can_reactivate_product(obj):
            obj.is_active = True
            obj.save(update_fields=['is_active', 'updated_at'])
            self.message_user(request, _('Produto reativado no catálogo.'), level=messages.SUCCESS)
            return HttpResponseRedirect(request.path)

        return None

    def save_model(self, request, obj, form, change):
        product_form = cast(ProductAdminForm, form)
        product = cast(Product, product_form.instance)
        if not product_form.cleaned_data.get('slug') and not product.slug:
            product.slug = f'{self.TEMP_SLUG_PREFIX}{uuid.uuid4().hex[:8]}'
        super().save_model(request, product, form, change)

    def save_related(self, request, form, formsets, change):
        product_form = cast(ProductAdminForm, form)
        super().save_related(request, form, formsets, change)
        if product_form.cleaned_data.get('slug'):
            return

        product = cast(Product, product_form.instance)
        generated_slug = self._build_generated_slug(product)
        if generated_slug and product.slug != generated_slug:
            product.slug = generated_slug
            product.save(update_fields=['slug'])

    def _build_generated_slug(self, obj):
        translation = obj.translations.filter(language='pt').first()
        parts = []
        if translation and translation.name:
            parts.append(translation.name)
        if obj.quantity:
            parts.append(obj.quantity)

        base_slug = slugify(' '.join(parts))
        if not base_slug:
            base_slug = slugify(obj.brand) or f'produto-{obj.pk}'

        return self._make_unique_slug(obj, base_slug)

    def _make_unique_slug(self, obj, base_slug):
        slug = base_slug
        suffix = 2
        queryset = Product.objects.exclude(pk=obj.pk)
        while queryset.filter(slug=slug).exists():
            slug = f'{base_slug}-{suffix}'
            suffix += 1
        return slug

    @admin.display(ordering='stock', description=_('Stock'))
    def stock_badge(self, obj):
        if obj.is_preview_only and obj.stock <= 0:
            return render_status_badge(_('Pré-visualização'), 'info')
        if obj.stock <= 0:
            return render_status_badge(_('Sem stock'), 'danger')
        if obj.stock < 5:
            return render_status_badge(_('Baixo (%(stock)s)') % {'stock': obj.stock}, 'warning')
        return render_status_badge(_('OK (%(stock)s)') % {'stock': obj.stock}, 'success')

    @admin.display(description=_('Disponibilidade'))
    def availability_badge(self, obj):
        if obj.is_preview_only:
            return render_status_badge(_('Pré-visualização'), 'info')
        if obj.is_active:
            return render_status_badge(_('Comprável'), 'success')
        return render_status_badge(_('Oculto'), 'warning')

    @admin.display(description=_('Reposição'))
    def replenishment_priority(self, obj):
        if obj.is_preview_only:
            return render_status_badge(_('Em vitrina'), 'info')
        if obj.stock <= 0 and obj.is_active:
            return render_status_badge(_('Rutura'), 'danger')
        if obj.stock < 5 and obj.is_active:
            return render_status_badge(_('Repor esta semana'), 'warning')
        if not obj.is_active and self._can_reactivate_product(obj):
            return render_status_badge(_('Reativável'), 'info')
        return render_status_badge(_('Coberto'), 'success')

    @admin.display(description=_('Prontidão'))
    def catalog_health_display(self, obj):
        if getattr(obj, 'pt_translation_count', 0) == 0:
            return render_status_badge(_('Sem PT'), 'danger')
        if getattr(obj, 'primary_image_count', 0) == 0:
            return render_status_badge(_('Sem imagem'), 'warning')
        if getattr(obj, 'location_count', 0) == 0:
            return render_status_badge(_('Sem localizações'), 'warning')
        if obj.is_preview_only:
            return render_status_badge(_('Pré-visualização'), 'info')
        if obj.stock <= 0:
            return render_status_badge(_('Sem stock'), 'danger')
        return render_status_badge(_('Pronto'), 'success')

    @admin.display(description=_('Checklist de publicação'))
    def catalog_readiness_panel(self, obj):
        translation_state = _('%(count)s tradução(ões)') % {'count': getattr(obj, 'translation_count', obj.translations.count())}
        pt_state = _('Sim') if getattr(obj, 'pt_translation_count', obj.translations.filter(language='pt').count()) else _('Não')
        image_count = getattr(obj, 'image_count', obj.images.count())
        primary_image = _('Sim') if getattr(obj, 'primary_image_count', obj.images.filter(is_primary=True).count()) else _('Não')
        locations = ', '.join(obj.available_locations.values_list('name', flat=True)) or _('Sem localizações atribuídas')
        return render_summary_panel(
            _('Checklist de publicação'),
            [
                (_('Slug final'), obj.slug or _('A gerar')),
                (_('Traduções'), translation_state),
                (_('Tradução PT'), pt_state),
                (_('Imagens'), image_count),
                (_('Imagem principal'), primary_image),
                (_('Localizações'), locations),
            ],
            footer=_('Antes de publicar, confirme imagem principal, tradução PT e stock disponível.'),
        )

    @admin.display(description=_('Plano de reposição'))
    def replenishment_panel(self, obj):
        location_count = getattr(obj, 'location_count', obj.available_locations.count())
        if obj.stock <= 0:
            next_step = _('Desativar ou repor imediatamente.') if obj.is_active else _('Aguardar reposição antes de reativar.')
        elif obj.stock < 5:
            next_step = _('Repor nesta semana para evitar rutura.')
        else:
            next_step = _('Cobertura confortável para operação diária.')

        if not obj.is_active and self._can_reactivate_product(obj):
            next_step = _('Produto pronto para regressar ao catálogo.')

        return render_summary_panel(
            _('Plano de reposição'),
            [
                (_('Estado de catálogo'), _('Ativo') if obj.is_active else _('Inativo')),
                (_('Stock atual'), obj.stock),
                (_('Nível operacional'), self.replenishment_priority(obj)),
                (_('Envio disponível'), _('Sim') if obj.allow_shipping else _('Apenas levantamento')),
                (_('Localizações'), location_count),
                (_('Próximo passo'), next_step),
            ],
            footer=_('Use os atalhos laterais para abrir a categoria ou a fila de reposição sem sair deste contexto.'),
        )

    def _can_reactivate_product(self, obj):
        return not obj.get_activation_blockers()


@admin.register(ProductImage)
class ProductImageAdmin(OrderableAdminMixin, EditLinkAdminMixin, ModelAdmin):
    list_display = ('order_controls', 'product', 'is_primary', 'order', 'image_preview', 'edit_link')
    list_filter = ('is_primary', 'product__category')
    search_fields = ('product__slug', 'product__translations__name', 'alt_text')
    autocomplete_fields = ('product',)
    fields = ('product', 'image', 'image_preview', 'alt_text', 'order', 'is_primary')
    readonly_fields = ('image_preview',)
    list_filter_submit = True
    compressed_fields = True

    @admin.display(description='Pré-visualização')
    def image_preview(self, obj):
        return render_image_preview(getattr(obj, 'image', None), width=96, height=96)
