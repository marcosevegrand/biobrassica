from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.accounts.validators import normalize_portuguese_nif, validate_portuguese_nif


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

    class Meta:
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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses', verbose_name=_('utilizador'))
    name = models.CharField(_('nome'), max_length=255)
    line1 = models.CharField(_('Morada'), max_length=255)
    line2 = models.CharField(_('Morada (cont.)'), max_length=255, blank=True)
    city = models.CharField(_('Cidade'), max_length=100)
    postal_code = models.CharField(_('Código Postal'), max_length=10)
    country = models.CharField(_('País'), max_length=2, default='PT')
    is_default = models.BooleanField(_('morada predefinida'), default=False)

    class Meta:
        verbose_name = _('morada')
        verbose_name_plural = _('moradas')

    def __str__(self):
        return f'{self.name} - {self.line1}, {self.city}'
