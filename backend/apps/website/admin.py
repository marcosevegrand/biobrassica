"""Website admin customisations."""

from django.conf import settings
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from apps.core.admin_helpers import EditLinkAdminMixin, OrderableAdminMixin, WorkflowAdminMixin, render_image_preview, render_status_badge, render_summary_panel
from apps.core.site_content import get_manual_mbway_details, get_payments_availability  # noqa: F401  # legacy public API
from apps.website.forms import TeamMemberAdminForm, WebsiteContentAdminForm
from apps.website.models import TeamMember, WebsiteContent


@admin.register(TeamMember)
class TeamMemberAdmin(WorkflowAdminMixin, OrderableAdminMixin, EditLinkAdminMixin, ModelAdmin):
	form = TeamMemberAdminForm
	list_before_template = 'admin/website/teammember/workflow_overview.html'
	list_display = ('order_controls', 'name', 'role', 'visibility_badge', 'is_active', 'edit_link')
	list_editable = ('is_active',)
	list_filter = ('is_active',)
	search_fields = ('name', 'role')
	search_help_text = _('Pesquise por nome ou função na equipa.')
	readonly_fields = ('team_member_panel', 'photo_preview')
	list_filter_submit = True
	compressed_fields = True

	fieldsets = (
		(_('Presença pública'), {
			'fields': ('name', ('role_choice', 'role_custom'), 'is_active', 'team_member_panel'),
		}),
		(_('Imagem'), {
			'fields': ('photo', 'photo_preview'),
		}),
	)

	def changelist_view(self, request, extra_context=None):
		queryset = self.get_queryset(request)
		base_url = reverse('admin:website_teammember_changelist')
		extra_context = {
			**(extra_context or {}),
			'workflow_metric_cards': [
				{'label': _('Equipa ativa'), 'value': queryset.filter(is_active=True).count(), 'context': _('Visível na página pública'), 'link': f'{base_url}?is_active__exact=1'},
				{'label': _('Ocultos'), 'value': queryset.filter(is_active=False).count(), 'context': _('Fora da página pública'), 'link': f'{base_url}?is_active__exact=0'},
				{'label': _('Primeiros quatro'), 'value': queryset.filter(is_active=True, order__lt=4).count(), 'context': _('Topo da grelha pública'), 'link': base_url},
				{'label': _('Total gerido'), 'value': queryset.count(), 'context': _('Backoffice do website'), 'link': base_url},
			],
		}
		return super().changelist_view(request, extra_context=extra_context)

	def get_changeform_submit_actions(self, request, obj):
		if obj.is_active:
			return [{'action_name': '_hide_from_website', 'description': _('Ocultar da equipa')}]
		return [{'action_name': '_show_on_website', 'description': _('Mostrar na equipa')}]

	def handle_changeform_submit_action(self, request, obj, action_name):
		if action_name == '_hide_from_website' and obj.is_active:
			obj.is_active = False
			obj.save(update_fields=['is_active'])
			self.message_user(request, _('Membro ocultado da página pública.'), level=messages.SUCCESS)
			return HttpResponseRedirect(request.path)

		if action_name == '_show_on_website' and not obj.is_active:
			obj.is_active = True
			obj.save(update_fields=['is_active'])
			self.message_user(request, _('Membro publicado na página pública.'), level=messages.SUCCESS)
			return HttpResponseRedirect(request.path)

		return None

	@admin.display(description=_('Estado'))
	def visibility_badge(self, obj):
		if obj.is_active:
			return render_status_badge(_('No website'), 'success')
		return render_status_badge(_('Oculto'), 'warning')

	@admin.display(description=_('Resumo da presença'))
	def team_member_panel(self, obj):
		if obj is None:
			return _('Guarde o membro para ver o resumo de presença pública.')

		return render_summary_panel(
			_('Presença pública'),
			[
				(_('Nome'), obj.name),
				(_('Função'), obj.role),
				(_('Estado'), _('Publicado') if obj.is_active else _('Oculto')),
				(_('Ordem'), obj.order),
				(_('Página'), _('Quem Somos')),
			],
			footer=_('A página pública usa a ordem configurada aqui para apresentar a equipa.'),
		)

	@admin.display(description=_('Pré-visualização'))
	def photo_preview(self, obj):
		return render_image_preview(getattr(obj, 'photo', None), width=112, height=112)


@admin.register(WebsiteContent)
class WebsiteContentAdmin(WorkflowAdminMixin, EditLinkAdminMixin, ModelAdmin):
	form = WebsiteContentAdminForm
	list_display = ('__str__', 'updated_at', 'edit_link')
	readonly_fields = ('website_operations_panel',)
	compressed_fields = True
	fieldsets = (
		(_('Operação'), {
			'fields': ('website_operations_panel',),
		}),
		(_('Empresa e apoio'), {
			'fields': ('company_legal_name', 'company_address', ('company_nif', 'support_email')),
		}),
		(_('Home'), {
			'fields': (
				'home_hero_image', 'home_hero_title_line1', 'home_hero_title_line2', 'home_hero_tagline',
				'home_quote_image', 'home_quote_text', 'home_quote_author', 'home_quote_role',
				'home_shop_cta_title', 'home_shop_cta_body',
			),
		}),
		(_('Quem Somos'), {
			'fields': (
				'about_hero_image', 'about_hero_title', 'about_hero_subtitle',
				'about_meaning_title', 'about_meaning_body', 'about_meaning_image',
				'about_selection_title', 'about_selection_body', 'about_selection_image',
				'about_farm_title', 'about_farm_body', 'about_farm_image',
				'about_video_title', 'about_video_body',
			),
		}),
		(_('Agricultura'), {
			'fields': (
				'agriculture_hero_image', 'agriculture_intro_text',
				'agriculture_why_title', 'agriculture_why_body', 'agriculture_why_image',
			),
		}),
		(_('Contactos'), {
			'fields': (('contacts_hero_title', 'whatsapp_number'), 'contacts_hero_body'),
		}),
	)

	def has_add_permission(self, request):
		if WebsiteContent.objects.exists():
			return False
		return super().has_add_permission(request)

	def has_delete_permission(self, request, obj=None):
		return False

	def get_changeform_submit_actions(self, request, obj):
		return []

	def handle_changeform_submit_action(self, request, obj, action_name):
		return None

	def get_changeform_custom_tools(self, request, obj):
		return [
			{
				'title': _('Gerir equipa'),
				'link': reverse('admin:website_teammember_changelist'),
				'icon': 'groups',
				'blank': False,
			},
			{
				'title': _('Gerir lojas'),
				'link': reverse('admin:catalog_location_changelist'),
				'icon': 'storefront',
				'blank': False,
			},
		]

	@admin.display(description=_('Resumo do website'))
	def website_operations_panel(self, obj):
		if obj is None:
			return _('Guarde o conteúdo para centralizar a gestão editorial do website.')

		return render_summary_panel(
			_('Operação editorial'),
			[
				(_('Empresa'), obj.company_legal_name or _('Usa fallback')),
				(_('Morada legal'), obj.company_address or _('Usa fallback')),
				(_('Email de apoio'), obj.support_email or _('Usa fallback')),
				(_('NIF'), obj.company_nif or _('Usa fallback')),
				(_('Home hero'), _('Configurado') if obj.home_hero_title_line1 else _('Usa fallback')),
				(_('Citação home'), _('Configurada') if obj.home_quote_text else _('Usa fallback')),
				(_('Quem Somos'), _('Configurado') if obj.about_hero_title else _('Usa fallback')),
				(_('Agricultura'), _('Configurado') if obj.agriculture_intro_text else _('Usa fallback')),
				(_('Contactos'), _('Configurado') if obj.contacts_hero_title else _('Usa fallback')),
				(_('WhatsApp'), obj.whatsapp_number or _('Usa fallback')),
			],
			footer=_('Este registo centraliza os principais blocos estáticos do website, o número MB WAY manual e a pausa de pagamentos no backoffice.'),
		)
