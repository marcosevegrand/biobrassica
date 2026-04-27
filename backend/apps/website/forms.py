from django import forms
from typing import Any, cast
from django.utils.translation import gettext_lazy as _

from apps.website.models import TeamMember, WebsiteContent


class TeamMemberAdminForm(forms.ModelForm):
    ROLE_CUSTOM_CHOICE = '__custom__'
    CURATED_ROLE_CHOICES = [
        'Fundadora',
        'Coordenadora',
        'Backoffice',
        'Atendimento',
        'Agricultura',
        'Produção',
        'Loja',
    ]

    role_choice = forms.ChoiceField(
        label=_('Função existente'),
        required=False,
        help_text=_('Escolha uma função já usada para manter a apresentação da equipa consistente.'),
    )
    role_custom = forms.CharField(
        label=_('Nova função'),
        required=False,
        help_text=_('Preencha apenas se a função ainda não existir.'),
    )

    class Meta:
        model = TeamMember
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'role' in self.fields:
            self.fields['role'].required = False
            self.fields['role'].widget = forms.HiddenInput()

        current_role = self._normalize_role(getattr(self.instance, 'role', ''))
        suggestions = self._role_suggestions(current_role)
        self._existing_roles = {role.casefold(): role for role in suggestions}
        choices = [
            ('', str(_('Selecione uma função'))),
            *[(role, role) for role in suggestions],
            (self.ROLE_CUSTOM_CHOICE, str(_('Outra função'))),
        ]
        cast(forms.ChoiceField, self.fields['role_choice']).choices = choices

        if current_role:
            if current_role in {value for value, _ in choices}:
                self.initial.setdefault('role_choice', current_role)
                self.initial.setdefault('role_custom', '')
            else:
                self.initial.setdefault('role_choice', self.ROLE_CUSTOM_CHOICE)
                self.initial.setdefault('role_custom', current_role)

        self.fields['name'].widget.attrs.setdefault('placeholder', _('Ex: Ângela Pereira'))
        self.fields['role_choice'].widget.attrs.setdefault('autocomplete', 'off')
        self.fields['role_custom'].widget.attrs.setdefault('placeholder', _('Ex: Coordenadora de loja'))
        self.fields['role_custom'].widget.attrs.setdefault('autocomplete', 'off')
        self.fields['photo'].widget.attrs.setdefault('accept', 'image/*')

    def _normalize_role(self, value):
        return ' '.join(str(value or '').split())

    def _role_suggestions(self, current_role):
        cached_roles = getattr(self, '_cached_role_suggestions', None)
        if cached_roles is None:
            roles = set(self.CURATED_ROLE_CHOICES)
            roles.update(
                self._normalize_role(role)
                for role in TeamMember.objects.exclude(role='').order_by().values_list('role', flat=True).distinct()
            )
            cached_roles = tuple(sorted(role for role in roles if role))
            self._cached_role_suggestions = cached_roles

        roles = set(cached_roles)
        if current_role:
            roles.add(current_role)
        return sorted(role for role in roles if role)

    def clean(self):
        cleaned_data: dict[str, Any] = super().clean() or {}
        role_choice = str(cleaned_data.get('role_choice') or '').strip()
        role_custom = self._normalize_role(cleaned_data.get('role_custom', ''))
        existing_roles = dict(getattr(self, '_existing_roles', {}))

        if role_choice == self.ROLE_CUSTOM_CHOICE:
            if not role_custom:
                self.add_error('role_custom', _('Indique a nova função para este membro.'))
            cleaned_role = existing_roles.get(role_custom.casefold(), role_custom)
        elif role_choice:
            cleaned_role = role_choice
        elif role_custom:
            cleaned_role = existing_roles.get(role_custom.casefold(), role_custom)
        else:
            cleaned_role = ''
            self.add_error('role_choice', _('Selecione uma função existente ou indique uma nova função.'))

        cleaned_data['role'] = cleaned_role
        return cleaned_data

    def save(self, commit=True):
        self.instance.role = str(self.cleaned_data.get('role') or '').strip()
        return super().save(commit=commit)


class WebsiteContentAdminForm(forms.ModelForm):
    class Meta:
        model = WebsiteContent
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        placeholders = {
            'company_legal_name': _('Ex: Biobrassica, Lda.'),
            'company_nif': _('Ex: 123456789'),
            'support_email': _('Ex: apoio@biobrassica.pt'),
            'home_hero_title_line1': _('Linha principal da hero home'),
            'home_hero_title_line2': _('Complemento da hero home'),
            'contacts_hero_title': _('Ex: Encontre-nos'),
            'whatsapp_number': _('Ex: +351 912 345 678'),
        }
        for field_name, placeholder in placeholders.items():
            self.fields[field_name].widget.attrs.setdefault('placeholder', placeholder)

        textarea_rows = {
            'company_address': 3,
            'home_quote_text': 3,
            'home_shop_cta_body': 3,
            'about_meaning_body': 4,
            'about_selection_body': 4,
            'about_farm_body': 4,
            'about_video_body': 4,
            'agriculture_intro_text': 4,
            'agriculture_why_body': 4,
            'contacts_hero_body': 3,
        }
        for field_name, rows in textarea_rows.items():
            self.fields[field_name].widget.attrs.setdefault('rows', rows)

        self.fields['company_nif'].help_text = _('Use um NIF português válido com 9 dígitos.')
        self.fields['support_email'].help_text = _('Endereço usado no rodapé, páginas legais e contactos.')
        self.fields['whatsapp_number'].help_text = _('Aceita 912345678, 351912345678 ou +351 912 345 678.')