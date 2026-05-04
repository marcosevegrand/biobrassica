from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline

from apps.catalog.forms import (
    CategoryAdminForm,
    CategoryTranslationInlineForm,
    DeliveryMethodAdminForm,
    LocationAdminForm,
    ProductAdminForm,
    ProductTranslationInlineForm,
)
from apps.catalog.models import (
    Category,
    CategoryPosition,
    CategoryTranslation,
    DeliveryMethod,
    DeliveryMethodPosition,
    Location,
    LocationPosition,
    Product,
    ProductTranslation,
)
from apps.core.admin_helpers import EditLinkAdminMixin, render_image_preview


class CategoryTranslationInline(TabularInline):
    model = CategoryTranslation
    form = CategoryTranslationInlineForm
    extra = 0
    max_num = 2
    fields = ('language', 'name', 'featured_message')
    verbose_name = _('tradução')
    verbose_name_plural = _('Traduções EN/FR')


class ProductTranslationInline(TabularInline):
    model = ProductTranslation
    form = ProductTranslationInlineForm
    extra = 0
    max_num = 2
    fields = ('language', 'name', 'description', 'allergens')
    verbose_name = _('tradução')
    verbose_name_plural = _('Traduções EN/FR')


@admin.register(Location)
class LocationAdmin(EditLinkAdminMixin, ModelAdmin):
    form = LocationAdminForm
    list_display = ('name', 'address', 'phone', 'is_active', 'edit_link')
    list_filter = ('is_active',)
    search_fields = ('name', 'address', 'phone')
    fields = ('name', 'address', 'phone', 'is_active', 'pickup_hours')
    readonly_fields = ()
    list_filter_submit = True
    compressed_fields = True


@admin.register(LocationPosition)
class LocationPositionAdmin(EditLinkAdminMixin, ModelAdmin):
    list_display = ('location', 'position', 'edit_link')
    autocomplete_fields = ('location',)
    search_fields = ('location__name',)
    fields = ('location', 'position')
    list_per_page = 100


@admin.register(DeliveryMethod)
class DeliveryMethodAdmin(EditLinkAdminMixin, ModelAdmin):
    form = DeliveryMethodAdminForm
    list_display = ('name', 'is_active', 'edit_link')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    fields = ('name', 'description', 'is_active')
    list_filter_submit = True
    compressed_fields = True


@admin.register(DeliveryMethodPosition)
class DeliveryMethodPositionAdmin(EditLinkAdminMixin, ModelAdmin):
    list_display = ('delivery_method', 'position', 'edit_link')
    autocomplete_fields = ('delivery_method',)
    search_fields = ('delivery_method__name',)
    fields = ('delivery_method', 'position')
    list_per_page = 100


@admin.register(Category)
class CategoryAdmin(EditLinkAdminMixin, ModelAdmin):
    form = CategoryAdminForm
    inlines = [CategoryTranslationInline]
    list_display = ('name', 'slug', 'is_active', 'is_special', 'image_preview', 'edit_link')
    list_filter = ('is_active', 'is_special')
    search_fields = ('name', 'slug', 'translations__name')
    fields = ('name', 'slug', 'is_active', 'is_special', 'featured_message', 'image', 'image_preview')
    readonly_fields = ('image_preview',)
    list_filter_submit = True
    compressed_fields = True

    @admin.display(description=_('Pré-visualização'))
    def image_preview(self, obj):
        return render_image_preview(getattr(obj, 'image', None), width=112, height=84)


@admin.register(CategoryPosition)
class CategoryPositionAdmin(EditLinkAdminMixin, ModelAdmin):
    list_display = ('category', 'position', 'edit_link')
    autocomplete_fields = ('category',)
    search_fields = ('category__name',)
    fields = ('category', 'position')
    list_per_page = 100


@admin.register(Product)
class ProductAdmin(EditLinkAdminMixin, ModelAdmin):
    form = ProductAdminForm
    inlines = [ProductTranslationInline]
    list_display = (
        'name',
        'category',
        'brand',
        'price',
        'quantity',
        'stock',
        'is_active',
        'is_highlight',
        'is_preview',
        'allow_shipping',
        'allow_pickup',
        'image_preview',
        'edit_link',
    )
    list_filter = ('category', 'is_active', 'is_highlight', 'is_preview', 'allow_shipping', 'allow_pickup')
    search_fields = ('name', 'slug', 'brand', 'bio_code', 'translations__name')
    fields = (
        'category',
        'slug',
        'name',
        'brand',
        'bio_code',
        'description',
        'allergens',
        'price',
        'quantity',
        'stock',
        'is_active',
        'is_highlight',
        'is_preview',
        'allow_shipping',
        'allow_pickup',
        'pickup_locations',
        'image',
        'image_preview',
    )
    readonly_fields = ('image_preview',)
    filter_vertical = ()
    list_filter_submit = True
    compressed_fields = True

    @admin.display(description=_('Pré-visualização'))
    def image_preview(self, obj):
        return render_image_preview(getattr(obj, 'image', None), width=112, height=112)
