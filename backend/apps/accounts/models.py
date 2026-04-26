import re

from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.accounts.validators import normalize_portuguese_nif, validate_portuguese_nif


PT_POSTAL_CODE_RE = re.compile(r'^\d{4}-\d{3}$')


class User(AbstractUser):
    email = models.EmailField(_('email'), unique=True)
    phone = models.CharField(_('telefone'), max_length=20, blank=True)
    preferred_language = models.CharField(
        _('idioma preferido'),
        max_length=2,
        choices=[('pt', _('Português')), ('en', _('Inglês')), ('fr', _('Francês'))],
        default='pt',
    )
    nif = models.CharField(_('NIF'), max_length=9, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        verbose_name = _('utilizador')
        verbose_name_plural = _('utilizadores')

    def __str__(self):
        return self.email

    def clean(self):
        super().clean()
        self.nif = normalize_portuguese_nif(self.nif)
        validate_portuguese_nif(self.nif)

    def save(self, *args, **kwargs):
        self.nif = normalize_portuguese_nif(self.nif)
        try:
            validate_portuguese_nif(self.nif)
        except ValidationError:
            raise
        return super().save(*args, **kwargs)


class Address(models.Model):
    class Country(models.TextChoices):
        PORTUGAL = 'PT', _('Portugal')

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses', verbose_name=_('utilizador'))
    name = models.CharField(_('nome'), max_length=255)
    line1 = models.CharField(_('Morada'), max_length=255)
    line2 = models.CharField(_('Morada (cont.)'), max_length=255, blank=True)
    city = models.CharField(_('Cidade'), max_length=100)
    postal_code = models.CharField(_('Código Postal'), max_length=10)
    country = models.CharField(_('País'), max_length=2, choices=Country.choices, default=Country.PORTUGAL)
    is_default = models.BooleanField(_('morada predefinida'), default=False)

    class Meta:
        verbose_name = _('morada')
        verbose_name_plural = _('moradas')

    def clean_fields(self, exclude=None):
        self.name = str(self.name or '').strip()
        self.line1 = str(self.line1 or '').strip()
        self.line2 = str(self.line2 or '').strip()
        self.city = str(self.city or '').strip()
        self.postal_code = str(self.postal_code or '').strip()
        self.country = str(self.country or self.Country.PORTUGAL).strip().upper() or self.Country.PORTUGAL
        return super().clean_fields(exclude=exclude)

    def clean(self):
        super().clean()
        self.name = str(self.name or '').strip()
        self.line1 = str(self.line1 or '').strip()
        self.line2 = str(self.line2 or '').strip()
        self.city = str(self.city or '').strip()
        self.postal_code = str(self.postal_code or '').strip()
        self.country = str(self.country or self.Country.PORTUGAL).strip().upper() or self.Country.PORTUGAL

        errors = {}
        if self.country != self.Country.PORTUGAL:
            errors['country'] = _('De momento apenas suportamos moradas em Portugal.')

        if self.postal_code and not PT_POSTAL_CODE_RE.match(self.postal_code):
            errors['postal_code'] = _('Use o formato 1234-123.')

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.name} - {self.line1}, {self.city}'
