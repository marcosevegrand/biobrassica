from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


PAYMENT_STATUS_TRANSITIONS = {
    'pending': {'paid', 'failed', 'expired'},
    'failed': {'pending'},
    'expired': {'pending'},
    'paid': {'refunded'},
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
        MULTIBANCO = 'multibanco', 'Multibanco'
        MBWAY = 'mbway', 'MB WAY'
        CREDIT_CARD = 'credit_card', 'Cartão de Crédito'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pendente'
        PAID = 'paid', 'Pago'
        FAILED = 'failed', 'Falhado'
        EXPIRED = 'expired', 'Expirado'
        REFUNDED = 'refunded', 'Reembolsado'

    order = models.OneToOneField(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='payment',
        verbose_name='encomenda',
    )
    method = models.CharField('método', max_length=20, choices=Method.choices)
    status = models.CharField('estado', max_length=20, choices=Status.choices, default=Status.PENDING)
    amount = models.DecimalField('valor', max_digits=10, decimal_places=2)
    ifthenpay_request_id = models.CharField('ID do pedido Ifthenpay', max_length=255, blank=True, db_index=True)

    # Multibanco
    mb_entity = models.CharField('entidade MB', max_length=10, blank=True)
    mb_reference = models.CharField('referência MB', max_length=20, blank=True, db_index=True)

    # MBWay
    mbway_phone = models.CharField('telefone MB WAY', max_length=20, blank=True)
    mbway_transaction_id = models.CharField('ID da transação MB WAY', max_length=255, blank=True)
    checkout_url = models.URLField('URL de checkout', blank=True)
    last_error = models.TextField('último erro', blank=True)

    expires_at = models.DateTimeField('expira em', null=True, blank=True)
    paid_at = models.DateTimeField('pago em', null=True, blank=True)
    created_at = models.DateTimeField('criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'pagamento'
        verbose_name_plural = 'pagamentos'
        constraints = [
            models.UniqueConstraint(
                fields=['ifthenpay_request_id'],
                condition=~Q(ifthenpay_request_id=''),
                name='payments_unique_ifthenpay_request_id',
            ),
            models.UniqueConstraint(
                fields=['mb_entity', 'mb_reference'],
                condition=~Q(mb_entity='') & ~Q(mb_reference=''),
                name='payments_unique_mb_entity_reference',
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
        result = super().save(*args, **kwargs)
        self._original_status = self.status
        return result

    def valid_next_statuses(self):
        return PAYMENT_STATUS_TRANSITIONS.get(self.status, set())

    def can_transition_to(self, new_status):
        return new_status == self.status or new_status in self.valid_next_statuses()

    def clean(self):
        super().clean()

        errors = {}
        original_status = getattr(self, '_original_status', None)

        if original_status and self.status != original_status and not self.can_transition_to(self.status):
            errors['status'] = 'Transição de estado inválida para o pagamento.'

        if self.status == self.Status.PAID and self.paid_at is None:
            errors['paid_at'] = 'Defina a data de pagamento quando o pagamento está confirmado.'

        if self.status != self.Status.PAID and self.paid_at is not None:
            errors['paid_at'] = 'A data de pagamento só pode estar preenchida em pagamentos pagos.'

        if errors:
            raise ValidationError(errors)

    @property
    def method_label(self):
        return self.Method(self.method).label

    @property
    def status_label(self):
        return self.Status(self.status).label

    def __str__(self):
        return f'Pagamento #{self.pk} ({self.method_label}) - {self.status_label}'

    @property
    def masked_mbway_phone(self):
        return _mask_value(self.mbway_phone, keep_start=3, keep_end=2)

    @property
    def masked_reference(self):
        return _mask_value(self.mb_reference, keep_start=3, keep_end=2)

    @property
    def masked_request_id(self):
        return _mask_value(self.ifthenpay_request_id, keep_start=4, keep_end=4)


class PaymentCallback(models.Model):
    payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        related_name='callbacks',
        verbose_name='pagamento',
    )
    raw_payload = models.JSONField('carga útil bruta')
    ip_address = models.GenericIPAddressField('endereço IP')
    is_valid = models.BooleanField('válido', default=False)
    validation_message = models.CharField('motivo da validação', max_length=255, blank=True)
    created_at = models.DateTimeField('criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'callback de pagamento'
        verbose_name_plural = 'callbacks de pagamento'

    def __str__(self):
        return f'Callback {self.pk} - {"válido" if self.is_valid else "inválido"}'
