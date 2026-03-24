import uuid
import re
from collections.abc import Mapping
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

if TYPE_CHECKING:
    from apps.payments.models import Payment


PT_POSTAL_CODE_RE = re.compile(r'^\d{4}-\d{3}$')


ORDER_STATUS_TRANSITIONS = {
    'pending': {'payment_pending', 'cancelled'},
    'payment_pending': {'pending', 'paid', 'cancelled'},
    'paid': {'preparing'},
    'preparing': {'ready'},
    'ready': {'delivered'},
    'delivered': set(),
    'cancelled': set(),
}


class Order(models.Model):
    if TYPE_CHECKING:
        items: models.Manager['OrderItem']
        payment: 'Payment'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pendente'
        PAYMENT_PENDING = 'payment_pending', 'Aguarda Pagamento'
        PAID = 'paid', 'Pago'
        PREPARING = 'preparing', 'Em Preparação'
        READY = 'ready', 'Pronto para Levantamento'
        DELIVERED = 'delivered', 'Entregue'
        CANCELLED = 'cancelled', 'Cancelado'

    class PickupLocation(models.TextChoices):
        BRAGA = 'braga', 'Loja Braga'
        GUIMARAES = 'guimaraes', 'Loja Guimarães'

    class FulfillmentMethod(models.TextChoices):
        PICKUP = 'pickup', 'Levantamento na loja'
        SHIPPING = 'shipping', 'Envio ao domicílio'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name='utilizador',
    )
    access_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    email = models.EmailField('email')
    phone = models.CharField('telefone', max_length=20, blank=True)
    name = models.CharField('nome', max_length=255)
    status = models.CharField('estado', max_length=20, choices=Status.choices, default=Status.PENDING)
    fulfillment_method = models.CharField(
        'método de entrega',
        max_length=20,
        choices=FulfillmentMethod.choices,
        default=FulfillmentMethod.PICKUP,
    )
    pickup_location = models.CharField('local de levantamento', max_length=20, choices=PickupLocation.choices, blank=True)
    shipping_address_line1 = models.CharField('morada', max_length=255, blank=True)
    shipping_address_line2 = models.CharField('morada (cont.)', max_length=255, blank=True)
    shipping_city = models.CharField('cidade', max_length=100, blank=True)
    shipping_postal_code = models.CharField('código postal', max_length=10, blank=True)
    language = models.CharField('idioma', max_length=2, default='pt')
    subtotal = models.DecimalField('subtotal', max_digits=10, decimal_places=2)
    total = models.DecimalField('total', max_digits=10, decimal_places=2)
    notes = models.TextField('notas', blank=True)
    created_at = models.DateTimeField('criado em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizado em', auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'encomenda'
        verbose_name_plural = 'encomendas'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_status = None if self._state.adding else self.status

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        instance._original_status = instance.status
        return instance

    def __str__(self):
        return f'Encomenda #{self.pk} - {self.name}'

    def save(self, *args, **kwargs):
        result = super().save(*args, **kwargs)
        self._original_status = self.status
        return result

    def valid_next_statuses(self):
        return ORDER_STATUS_TRANSITIONS.get(self.status, set())

    def can_transition_to(self, new_status):
        return new_status == self.status or new_status in self.valid_next_statuses()

    def clean(self):
        super().clean()

        errors = {}
        original_status = getattr(self, '_original_status', None)

        if original_status and self.status != original_status and not self.can_transition_to(self.status):
            errors['status'] = 'Transição de estado inválida para a encomenda.'

        if self.fulfillment_method == self.FulfillmentMethod.PICKUP:
            if not self.pickup_location:
                errors['pickup_location'] = 'Selecione um local de levantamento.'
        elif self.fulfillment_method == self.FulfillmentMethod.SHIPPING:
            for field_name in ('shipping_address_line1', 'shipping_city', 'shipping_postal_code'):
                value = getattr(self, field_name, '')
                if not value or not value.strip():
                    errors[field_name] = 'Este campo é obrigatório para envio.'

            postal_code = (self.shipping_postal_code or '').strip()
            if postal_code and not PT_POSTAL_CODE_RE.match(postal_code):
                errors['shipping_postal_code'] = 'Use o formato 1234-123.'

        payment = None
        try:
            payment = self.payment
        except Exception:
            payment = None

        if self.status in {self.Status.PREPARING, self.Status.READY, self.Status.DELIVERED}:
            if payment is None or payment.status != payment.Status.PAID:
                errors['status'] = 'A encomenda só pode avançar após pagamento confirmado.'

        if self.status == self.Status.CANCELLED and payment is not None and payment.status == payment.Status.PAID:
            errors['status'] = 'As encomendas pagas não podem ser canceladas por este fluxo.'

        if errors:
            raise ValidationError(errors)

    @property
    def status_display_class(self):
        status_classes: Mapping[str, str] = {
            self.Status.PENDING: 'bg-stone-100 text-stone-700',
            self.Status.PAYMENT_PENDING: 'bg-amber-100 text-amber-800',
            self.Status.PAID: 'bg-emerald-100 text-emerald-800',
            self.Status.PREPARING: 'bg-sky-100 text-sky-800',
            self.Status.READY: 'bg-blue-100 text-blue-800',
            self.Status.DELIVERED: 'bg-green-100 text-green-800',
            self.Status.CANCELLED: 'bg-rose-100 text-rose-800',
        }
        return status_classes.get(self.status, 'bg-stone-100 text-stone-700')

    @property
    def is_shipping(self):
        return self.fulfillment_method == self.FulfillmentMethod.SHIPPING

    @property
    def shipping_address_display(self):
        parts = [self.shipping_address_line1, self.shipping_address_line2, self.shipping_postal_code, self.shipping_city]
        return ', '.join(part for part in parts if part)

    @property
    def masked_contact(self):
        if not self.email:
            return self.phone
        local, _, domain = self.email.partition('@')
        if len(local) <= 2:
            local = '*' * len(local)
        else:
            local = f'{local[:2]}***'
        return f'{local}@{domain}' if domain else local


class OrderItem(models.Model):
    if TYPE_CHECKING:
        product_id: int | None

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='encomenda')
    product = models.ForeignKey(
        'catalog.Product',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='produto',
    )
    product_name = models.CharField('nome do produto', max_length=255)
    price = models.DecimalField('preço', max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField('quantidade')

    class Meta:
        verbose_name = 'item da encomenda'
        verbose_name_plural = 'itens da encomenda'

    def __str__(self):
        return f'{self.quantity}x {self.product_name}'

    @property
    def subtotal(self):
        return self.price * self.quantity
