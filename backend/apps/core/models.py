"""Core models module."""

import re

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.accounts.validators import normalize_portuguese_mobile_phone


IBAN_RE = re.compile(r'^[A-Z]{2}\d{2}[A-Z0-9]{1,30}$')
BIC_RE = re.compile(r'^[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?$')


class ShopSettings(models.Model):
    """Singleton (pk=1) holding shop-wide operational configuration.

    Controls:
    - Shop active toggle (pause payments during deployments)
    - Brevemente mode (coming-soon page on loja.* subdomain, CTA changes on main site)
    - Minimum order total enforcement
    - Payment methods (MB WAY, bank transfer) with validation
    - Payment timeout and checkout reservation timeout
    - Bank transfer beneficiary / IBAN / BIC details
    """

    is_shop_active = models.BooleanField(
        _('loja ativa'),
        default=True,
        help_text=_(
            'Quando desativado, os clientes não conseguem avançar do carrinho para o pagamento. '
            'Ideal para pausar a loja entre deployments ou em períodos de inatividade.'
        ),
    )
    is_shop_brevemente = models.BooleanField(
        _('modo brevemente'),
        default=False,
        help_text=_(
            'Quando ativo, o subdomínio loja.* mostra uma página "Brevemente" e '
            'os botões da loja no site principal passam a dizer "Brevemente" em vez de linkarem para a loja.'
        ),
    )
    min_order_total = models.DecimalField(
        _('valor mínimo de encomenda (€)'),
        max_digits=8,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_('Encomendas com total inferior a este valor são bloqueadas no checkout.'),
    )

    mbway_enabled = models.BooleanField(_('aceitar MB WAY'), default=True)
    mbway_number = models.CharField(
        _('número MB WAY'),
        max_length=20,
        blank=True,
        help_text=_('Telemóvel mostrado ao cliente para pagar manualmente por MB WAY.'),
    )

    payment_timeout_minutes = models.PositiveIntegerField(
        _('tempo limite para pagamento (minutos)'),
        default=30,
        help_text=_('Após este tempo, o pagamento expirado é cancelado. A encomenda permanece pendente — o cliente pode reiniciar o pagamento. Defina 0 para desativar.'),
    )

    checkout_reservation_minutes = models.PositiveIntegerField(
        _('tempo limite para reserva no checkout (minutos)'),
        default=30,
        help_text=_('Quanto tempo o stock fica reservado enquanto o cliente preenche o checkout. Após expirar, o stock é libertado e o cliente tem de recomeçar. Defina 0 para desativar.'),
    )

    bank_transfer_enabled = models.BooleanField(_('aceitar transferência bancária'), default=False)
    bank_beneficiary = models.CharField(_('nome do beneficiário'), max_length=120, blank=True)
    bank_iban = models.CharField(_('IBAN'), max_length=34, blank=True)
    bank_bic = models.CharField(_('BIC/SWIFT'), max_length=11, blank=True)

    updated_at = models.DateTimeField(_('atualizado em'), auto_now=True)

    class Meta:
        verbose_name = _('configurações da loja')
        verbose_name_plural = _('configurações da loja')
        constraints = [
            models.CheckConstraint(condition=models.Q(pk=1), name='core_shopsettings_singleton_pk_1'),
        ]

    def __str__(self):
        return 'Configurações da loja'

    def clean_fields(self, exclude=None):
        for field in self._meta.fields:
            value = getattr(self, field.attname, None)
            if isinstance(value, str):
                setattr(self, field.attname, value.strip())
        return super().clean_fields(exclude=exclude)

    def clean(self):
        super().clean()
        errors = {}

        if self.mbway_number:
            try:
                self.mbway_number = normalize_portuguese_mobile_phone(self.mbway_number)
            except ValidationError as error:
                errors['mbway_number'] = error.messages

        if self.mbway_enabled and not self.mbway_number:
            errors['mbway_number'] = [_('Indique o número MB WAY para mostrar ao cliente.')]

        if self.bank_transfer_enabled:
            if not self.bank_beneficiary:
                errors['bank_beneficiary'] = [_('Indique o nome do beneficiário.')]
            if not self.bank_iban:
                errors['bank_iban'] = [_('Indique o IBAN para transferência.')]
            elif not IBAN_RE.match(self.bank_iban):
                errors['bank_iban'] = [_('Formato de IBAN inválido. Use o formato PT50...')]
            if self.bank_bic and not BIC_RE.match(self.bank_bic):
                errors['bank_bic'] = [_('Formato de BIC/SWIFT inválido.')]

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.pk = 1
        if kwargs.get('force_insert') and type(self).objects.filter(pk=1).exists():
            kwargs['force_insert'] = False
        self.full_clean(validate_unique=False, validate_constraints=False)
        return super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        instance, _created = cls.objects.get_or_create(pk=1)
        return instance

    @property
    def has_any_payment_method(self):
        return self.mbway_enabled or self.bank_transfer_enabled

