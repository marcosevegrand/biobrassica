from urllib.parse import urlsplit

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


PAYMENT_STATUS_TRANSITIONS = {
    'pending': {'confirmed', 'cancelled'},
    'confirmed': {'refunded'},
    'cancelled': {'pending'},
    'refunded': set(),
}


def _mask_value(value, *, keep_start=2, keep_end=2):
    text = str(value or '').strip()
    if not text:
        return ''
    if len(text) <= keep_start + keep_end:
        return '*' * len(text)
    return f'{text[:keep_start]}***{text[-keep_end:]}'


class Payment(models.Model):
    class Method(models.TextChoices):
        MBWAY_MANUAL = 'mbway_manual', _('MB WAY')
        BANK_TRANSFER = 'bank_transfer', _('Transferência bancária')

    class Status(models.TextChoices):
        PENDING = 'pending', _('Pendente')
        CONFIRMED = 'confirmed', _('Confirmado')
        CANCELLED = 'cancelled', _('Cancelado')
        REFUNDED = 'refunded', _('Reembolsado')

    order = models.OneToOneField(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='payment',
        verbose_name=_('encomenda'),
    )
    method = models.CharField(_('método'), max_length=20, choices=Method.choices)
    status = models.CharField(_('estado'), max_length=20, choices=Status.choices, default=Status.PENDING)
    amount = models.DecimalField(_('valor'), max_digits=10, decimal_places=2)
    provider_reference = models.CharField(_('referência do provedor'), max_length=255, blank=True, db_index=True)
    provider_payment_id = models.CharField(_('ID do pagamento no provedor'), max_length=255, blank=True, db_index=True)
    provider_data = models.JSONField(_('dados do provedor'), default=dict, blank=True)
    checkout_url = models.URLField(_('URL de checkout'), max_length=500, blank=True)
    last_error = models.TextField(_('último erro'), blank=True)
    expires_at = models.DateTimeField(_('expira em'), null=True, blank=True)
    paid_at = models.DateTimeField(_('pago em'), null=True, blank=True)
    created_at = models.DateTimeField(_('criado em'), auto_now_add=True)

    class Meta:
        verbose_name = _('pagamento')
        verbose_name_plural = _('pagamentos')
        constraints = [
            models.UniqueConstraint(
                fields=['method', 'provider_reference'],
                condition=~Q(provider_reference=''),
                name='payments_unique_provider_reference',
            ),
            models.UniqueConstraint(
                fields=['method', 'provider_payment_id'],
                condition=~Q(provider_payment_id=''),
                name='payments_unique_provider_payment_id',
            ),
        ]
        indexes = [
            models.Index(fields=['status', 'expires_at'], name='payments_status_expires_idx'),
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_status = None if self._state.adding else self.status

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        instance._original_status = instance.status
        return instance

    def save(self, *args, **kwargs):
        self.full_clean()
        result = super().save(*args, **kwargs)
        self._original_status = self.status
        return result

    def clean_fields(self, exclude=None):
        self.provider_reference = str(self.provider_reference or '').strip()
        self.provider_payment_id = str(self.provider_payment_id or '').strip()
        self.checkout_url = str(self.checkout_url or '').strip()
        self.last_error = str(self.last_error or '').strip()
        return super().clean_fields(exclude=exclude)

    def valid_next_statuses(self):
        return PAYMENT_STATUS_TRANSITIONS.get(self.status, set())

    def can_transition_to(self, new_status):
        return new_status == self.status or new_status in self.valid_next_statuses()

    def clean(self):
        super().clean()

        errors = {}
        original_status = getattr(self, '_original_status', None)

        if original_status and self.status != original_status and not self.can_transition_to(self.status):
            errors['status'] = _('Transição de estado inválida para o pagamento.')

        if self.status == self.Status.CONFIRMED and self.paid_at is None:
            self.paid_at = timezone.now()

        if self.status != self.Status.CONFIRMED and self.paid_at is not None:
            errors['paid_at'] = _('A data de pagamento só pode estar preenchida em pagamentos confirmados.')

        if self.checkout_url and urlsplit(self.checkout_url).scheme != 'https':
            errors['checkout_url'] = _('Use um URL https:// válido para o checkout.')

        if self.provider_data is None:
            self.provider_data = {}
        elif not isinstance(self.provider_data, dict):
            errors['provider_data'] = _('Os dados do provedor devem ser um objeto JSON.')

        if errors:
            raise ValidationError(errors)

    @property
    def method_label(self):
        return dict(self.Method.choices).get(self.method, self.method)

    @property
    def status_label(self):
        return dict(self.Status.choices).get(self.status, self.status)

    def __str__(self):
        return f'Pagamento #{self.pk} ({self.method_label}) - {self.status_label}'

    @property
    def masked_provider_reference(self):
        return _mask_value(self.provider_reference, keep_start=6, keep_end=4)

    @property
    def masked_provider_payment_id(self):
        return _mask_value(self.provider_payment_id, keep_start=6, keep_end=4)

    @property
    def masked_provider_identifier(self):
        return self.masked_provider_reference or self.masked_provider_payment_id
