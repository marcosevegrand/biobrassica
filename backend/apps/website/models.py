from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Max
from django.utils import translation
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from apps.accounts.validators import (
    normalize_portuguese_nif,
    validate_portuguese_nif,
)
from apps.core.translations import DEFAULT_LANGUAGE, normalized_language


def normalize_whatsapp_number(value):
    digits = ''.join(character for character in str(value or '') if character.isdigit())
    if digits == '':
        return ''

    national_number = ''
    if len(digits) == 9 and digits.startswith('9'):
        national_number = digits
    elif len(digits) == 12 and digits.startswith('351') and digits[3] == '9':
        national_number = digits[3:]

    if not national_number:
        raise ValidationError(_('Indique um número WhatsApp português válido.'))

    return f'+351 {national_number[:3]} {national_number[3:6]} {national_number[6:]}'


class LocalizedWebsiteContent:
    TRANSLATABLE_FIELDS = {
        'home_hero_title_line1',
        'home_hero_title_line2',
        'home_hero_tagline',
        'home_quote_text',
        'home_quote_author',
        'home_quote_role',
        'home_shop_cta_title',
        'home_shop_cta_body',
        'about_hero_title',
        'about_hero_subtitle',
        'about_meaning_title',
        'about_meaning_body',
        'about_selection_title',
        'about_selection_body',
        'about_farm_title',
        'about_farm_body',
        'about_video_title',
        'about_video_body',
        'agriculture_intro_text',
        'agriculture_why_title',
        'agriculture_why_body',
        'contacts_hero_title',
        'contacts_hero_body',
    }

    def __init__(self, instance, *, lang=None):
        self.instance = instance
        self.lang = normalized_language(lang)

    def __getattr__(self, attribute):
        value = getattr(self.instance, attribute)
        if attribute not in self.TRANSLATABLE_FIELDS or not isinstance(value, str) or not value:
            return value

        if self.lang == DEFAULT_LANGUAGE:
            return value

        with translation.override(self.lang):
            return gettext(value)

    def __bool__(self):
        return bool(self.instance)


class TeamMember(models.Model):
    """Admin-managed team members shown on the 'A Nossa Equipa' section."""
    name = models.CharField(_('nome'), max_length=255, help_text=_('Nome do membro da equipa'))
    role = models.CharField(_('função'), max_length=255, help_text=_('Cargo / Função'))
    photo = models.ImageField(_('foto'), upload_to='team/', help_text=_('Foto do membro'))
    is_active = models.BooleanField(_('ativo'), default=True)

    def __init__(self, *args, **kwargs):
        self._pending_order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)

    class Meta:
        verbose_name = _('membro da equipa')
        verbose_name_plural = _('membros da equipa')

    def clean(self):
        super().clean()
        self.name = str(self.name or '').strip()
        self.role = ' '.join(str(self.role or '').split())

    @property
    def position(self):
        return getattr(getattr(self, 'sort_order', None), 'position', 0)

    @property
    def order(self):
        return self.position

    @order.setter
    def order(self, value):
        self._pending_order = value

    def save(self, *args, **kwargs):
        self.full_clean()
        result = super().save(*args, **kwargs)
        position_value = self._pending_order if self._pending_order is not None else TeamMemberPosition.next_position()
        sort_order, created = TeamMemberPosition.objects.get_or_create(
            team_member=self,
            defaults={'position': position_value},
        )
        if not created and self._pending_order is not None and sort_order.position != self._pending_order:
            sort_order.position = self._pending_order
            sort_order.save(update_fields=['position'])
        self._pending_order = None
        return result

    def __str__(self):
        return self.name


class TeamMemberPosition(models.Model):
    team_member = models.OneToOneField(
        TeamMember,
        on_delete=models.CASCADE,
        related_name='sort_order',
        verbose_name=_('membro da equipa'),
    )
    position = models.PositiveIntegerField(_('posição'), default=0)

    class Meta:
        ordering = ['position', 'pk']
        verbose_name = _('ordem de membro da equipa')
        verbose_name_plural = _('ordens de membros da equipa')

    @classmethod
    def next_position(cls):
        return (cls.objects.aggregate(max_position=Max('position'))['max_position'] or 0) + 1

    def __str__(self):
        return f'{self.team_member} ({self.position})'


class WebsiteContent(models.Model):
    company_legal_name = models.CharField(_('designação legal'), max_length=255, blank=True)
    company_address = models.TextField(_('morada legal'), blank=True)
    company_nif = models.CharField(_('NIF da empresa'), max_length=20, blank=True)
    support_email = models.EmailField(_('email de apoio'), blank=True)
    home_hero_image = models.ImageField(_('imagem hero home'), upload_to='website/', blank=True)
    home_hero_title_line1 = models.CharField(_('título home linha 1'), max_length=120, blank=True)
    home_hero_title_line2 = models.CharField(_('título home linha 2'), max_length=120, blank=True)
    home_hero_tagline = models.CharField(_('subtítulo home'), max_length=255, blank=True)
    home_quote_text = models.TextField(_('citação home'), blank=True)
    home_quote_author = models.CharField(_('autor da citação'), max_length=120, blank=True)
    home_quote_role = models.CharField(_('função do autor'), max_length=120, blank=True)
    home_quote_image = models.ImageField(_('imagem da citação'), upload_to='website/', blank=True)
    home_shop_cta_title = models.CharField(_('título CTA loja'), max_length=120, blank=True)
    home_shop_cta_body = models.TextField(_('texto CTA loja'), blank=True)

    about_hero_image = models.ImageField(_('imagem hero quem somos'), upload_to='website/', blank=True)
    about_hero_title = models.CharField(_('título hero quem somos'), max_length=160, blank=True)
    about_hero_subtitle = models.CharField(_('subtítulo hero quem somos'), max_length=255, blank=True)
    about_meaning_title = models.CharField(_('título bloco significado'), max_length=160, blank=True)
    about_meaning_body = models.TextField(_('texto bloco significado'), blank=True)
    about_meaning_image = models.ImageField(_('imagem bloco significado'), upload_to='website/', blank=True)
    about_selection_title = models.CharField(_('título bloco seleção'), max_length=160, blank=True)
    about_selection_body = models.TextField(_('texto bloco seleção'), blank=True)
    about_selection_image = models.ImageField(_('imagem bloco seleção'), upload_to='website/', blank=True)
    about_farm_title = models.CharField(_('título bloco quinta'), max_length=160, blank=True)
    about_farm_body = models.TextField(_('texto bloco quinta'), blank=True)
    about_farm_image = models.ImageField(_('imagem bloco quinta'), upload_to='website/', blank=True)
    about_video_title = models.CharField(_('título vídeo quem somos'), max_length=160, blank=True)
    about_video_body = models.TextField(_('texto vídeo quem somos'), blank=True)

    agriculture_hero_image = models.ImageField(_('imagem hero agricultura'), upload_to='website/', blank=True)
    agriculture_intro_text = models.TextField(_('introdução agricultura'), blank=True)
    agriculture_why_title = models.CharField(_('título porquê biológico'), max_length=160, blank=True)
    agriculture_why_body = models.TextField(_('texto porquê biológico'), blank=True)
    agriculture_why_image = models.ImageField(_('imagem porquê biológico'), upload_to='website/', blank=True)

    contacts_hero_title = models.CharField(_('título contactos'), max_length=160, blank=True)
    contacts_hero_body = models.TextField(_('texto contactos'), blank=True)
    whatsapp_number = models.CharField(_('número WhatsApp'), max_length=20, blank=True)

    updated_at = models.DateTimeField(_('atualizado em'), auto_now=True)

    class Meta:
        verbose_name = _('conteúdo do website')
        verbose_name_plural = _('conteúdo do website')
        constraints = [
            models.CheckConstraint(
                condition=models.Q(pk=1),
                name='website_singleton_pk_1',
            ),
        ]

    def __str__(self):
        return 'Conteúdo do website'

    def clean_fields(self, exclude=None):
        for field in self._meta.fields:
            value = getattr(self, field.attname, None)
            if isinstance(value, str):
                setattr(self, field.attname, value.strip())
        self.support_email = str(self.support_email or '').lower()
        return super().clean_fields(exclude=exclude)

    def clean(self):
        super().clean()
        errors = {}
        self.company_nif = normalize_portuguese_nif(self.company_nif)
        try:
            validate_portuguese_nif(self.company_nif)
        except ValidationError as error:
            errors['company_nif'] = error.messages

        try:
            self.whatsapp_number = normalize_whatsapp_number(self.whatsapp_number)
        except ValidationError as error:
            errors['whatsapp_number'] = error.messages

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.pk = 1
        if kwargs.get('force_insert') and type(self).objects.filter(pk=1).exists():
            kwargs['force_insert'] = False
        self.full_clean(validate_unique=False, validate_constraints=False)
        return super().save(*args, **kwargs)

    def for_language(self, lang=None):
        return LocalizedWebsiteContent(self, lang=lang)
