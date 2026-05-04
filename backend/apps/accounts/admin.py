from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Count
from django.forms import CharField, ModelForm, PasswordInput
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline

from apps.accounts.models import Address, CustomerAccount, StaffAccount, User
from apps.core.admin_helpers import EditLinkAdminMixin


class AddressInline(TabularInline):
    model = Address
    extra = 0
    fields = ('name', 'line1', 'city', 'postal_code', 'country', 'is_default')
    show_change_link = True


@admin.register(User)
class CustomerAdmin(EditLinkAdminMixin, BaseUserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'phone', 'nif', 'is_active', 'edit_link')
    list_filter = ('is_active', 'preferred_language')
    search_fields = ('email', 'username', 'first_name', 'last_name', 'phone', 'nif')
    search_help_text = _('Pesquise por email, username, nome, telefone ou NIF do cliente.')
    ordering = ('email',)
    list_filter_submit = True
    compressed_fields = True
    inlines = [AddressInline]

    fieldsets = (
        (None, {
            'fields': ('username', 'password', 'first_name', 'last_name', 'email', 'phone', 'nif', 'preferred_language', 'is_active'),
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'first_name', 'last_name', 'phone', 'nif', 'preferred_language', 'is_active'),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_staff=False).annotate(address_count=Count('addresses', distinct=True))

    def save_model(self, request, obj, form, change):
        obj.is_staff = False
        obj.is_superuser = False
        super().save_model(request, obj, form, change)


class StaffAccountAdminForm(ModelForm):
    password_plain = CharField(
        label=_('password'),
        required=False,
        widget=PasswordInput(render_value=False),
        help_text=_('Preencha para definir ou alterar a password.'),
    )

    class Meta:
        model = StaffAccount
        fields = ('username', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password_plain'].required = self.instance.pk is None

    def save(self, commit=True):
        instance = super().save(commit=False)
        password = self.cleaned_data.get('password_plain')
        if password:
            instance.set_password(password)
        elif instance.pk is None:
            instance.set_unusable_password()
        instance.is_staff = True
        instance.is_superuser = True
        instance.is_active = True
        if commit:
            instance.save()
        return instance


@admin.register(StaffAccount)
class StaffAccountAdmin(EditLinkAdminMixin, ModelAdmin):
    form = StaffAccountAdminForm
    list_display = ('username', 'email', 'edit_link')
    search_fields = ('username', 'email')
    search_help_text = _('Pesquise por username ou email da staff.')
    list_filter_submit = True
    compressed_fields = True
    fields = ('username', 'email', 'password_plain')

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_staff=True)

    def save_model(self, request, obj, form, change):
        obj.is_staff = True
        obj.is_superuser = True
        obj.is_active = True
        super().save_model(request, obj, form, change)


@admin.register(Address)
class AddressAdmin(EditLinkAdminMixin, ModelAdmin):
    list_display = ('name', 'user', 'city', 'postal_code', 'country', 'is_default', 'edit_link')
    list_filter = ('city', 'country', 'is_default')
    search_fields = ('name', 'line1', 'city', 'postal_code', 'user__email')
    search_help_text = _('Pesquise por cliente, nome da morada, cidade ou código postal.')
    list_filter_submit = True
    compressed_fields = True
    fields = ('user', 'name', 'line1', 'line2', 'city', 'postal_code', 'country', 'is_default')
