import uuid
import re
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.accounts.validators import normalize_portuguese_nif, normalize_portuguese_phone, validate_portuguese_nif
from apps.catalog.models import Location
from apps.core.limits import MAX_PURCHASE_QUANTITY
from apps.core.translations import normalized_language

if TYPE_CHECKING:
    from apps.payments.models import Payment


PT_POSTAL_CODE_RE = re.compile(r'^\d{4}-\d{3}$')


# Order lifecycle:
#   pending → preparing → ready → in_transit → delivered
#   pending → cancelled
#   preparing → cancelled
#   ready → cancelled
#   in_transit → cancelled
# Shipping orders skip 'ready', pickup orders skip 'in_transit'
ORDER_STATUS_TRANSITIONS = {
    'pending': {'preparing', 'cancelled'},
    'preparing': {'ready', 'in_transit', 'cancelled'},
    'ready': {'in_transit', 'delivered', 'cancelled'},
    'in_transit': {'delivered', 'cancelled'},
    'delivered': set(),
    'cancelled': set(),
}

# Payment lifecycle:
#   pending → confirmed → refunded
#   pending → cancelled → pending  (restartable)
# Cancelled payments are separate from cancelled orders — both
# are manual actions. A cancelled payment can be restarted by
# the customer if the order is still pending.
PAYMENT_STATE_TRANSITIONS = {
    'pending': {'confirmed', 'cancelled'},
    'confirmed': {'refunded'},
    'cancelled': {'pending'},
    'refunded': set(),
}


class Order(models.Model):
    if TYPE_CHECKING:
        items: models.Manager['OrderItem']
        payment: 'Payment'

    class Status(models.TextChoices):
        PENDING = 'pending', _('Pendente')
        PREPARING = 'preparing', _('Em Preparação')
        READY = 'ready', _('Pronta para levantamento')
        IN_TRANSIT = 'in_transit', _('Em trânsito')
        DELIVERED = 'delivered', _('Entregue')
        CANCELLED = 'cancelled', _('Cancelada')

    class PaymentState(models.TextChoices):
        PENDING = 'pending', _('Pendente')
        CONFIRMED = 'confirmed', _('Confirmado')
        CANCELLED = 'cancelled', _('Cancelado')
        REFUNDED = 'refunded', _('Reembolsado')

    class PickupLocation(models.TextChoices):
        BRAGA = 'braga', _('Loja Braga')
        GUIMARAES = 'guimaraes', _('Loja Guimarães')

    class FulfillmentMethod(models.TextChoices):
        PICKUP = 'pickup', _('Levantamento na loja')
        SHIPPING = 'shipping', _('Envio ao domicílio')

    class Language(models.TextChoices):
        PT = 'pt', _('Português')
        EN = 'en', _('Inglês')
        FR = 'fr', _('Francês')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name=_('utilizador'),
    )
    access_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    email = models.EmailField(_('email'))
    phone = models.CharField(_('telefone'), max_length=20, blank=True)
    nif = models.CharField(_('NIF'), max_length=9, blank=True)
    name = models.CharField(_('nome'), max_length=255)
    status = models.CharField(_('estado'), max_length=20, choices=Status.choices, default=Status.PENDING)
    payment_state = models.CharField(
        _('estado do pagamento'),
        max_length=20,
        choices=PaymentState.choices,
        default=PaymentState.PENDING,
    )
    fulfillment_method = models.CharField(
        _('método de entrega'),
        max_length=20,
        choices=FulfillmentMethod.choices,
        default=FulfillmentMethod.PICKUP,
    )
    pickup_location = models.CharField(_('local de levantamento'), max_length=100, blank=True)
    shipping_address_line1 = models.CharField(_('morada'), max_length=255, blank=True)
    shipping_address_line2 = models.CharField(_('morada (cont.)'), max_length=255, blank=True)
    shipping_city = models.CharField(_('cidade'), max_length=100, blank=True)
    shipping_postal_code = models.CharField(_('código postal'), max_length=10, blank=True)
    language = models.CharField(_('idioma'), max_length=2, choices=Language.choices, default=Language.PT)
    subtotal = models.DecimalField(_('subtotal'), max_digits=10, decimal_places=2)
    total = models.DecimalField(_('total'), max_digits=10, decimal_places=2)
    notes = models.TextField(_('notas'), blank=True)
    created_at = models.DateTimeField(_('criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('atualizado em'), auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('encomenda')
        verbose_name_plural = _('encomendas')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_status = None if self._state.adding else self.status
        self._original_payment_state = None if self._state.adding else self.payment_state

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        instance._original_status = instance.status
        instance._original_payment_state = instance.payment_state
        return instance

    def __str__(self):
        return f'Encomenda #{self.pk} - {self.name}'

    def save(self, *args, **kwargs):
        self.full_clean()
        result = super().save(*args, **kwargs)
        self._original_status = self.status
        self._original_payment_state = self.payment_state
        return result

    def clean_fields(self, exclude=None):
        self.name = str(self.name or '').strip()
        self.email = str(self.email or '').strip().lower()
        self.phone = str(self.phone or '').strip()
        self.nif = str(self.nif or '').strip()
        self.pickup_location = str(self.pickup_location or '').strip()
        self.shipping_address_line1 = str(self.shipping_address_line1 or '').strip()
        self.shipping_address_line2 = str(self.shipping_address_line2 or '').strip()
        self.shipping_city = str(self.shipping_city or '').strip()
        self.shipping_postal_code = str(self.shipping_postal_code or '').strip()
        self.notes = str(self.notes or '').strip()
        self.language = normalized_language(self.language, fallback=self.Language.PT).lower()
        return super().clean_fields(exclude=exclude)

    def valid_next_statuses(self):
        next_statuses = set(ORDER_STATUS_TRANSITIONS.get(self.status, set()))
        if self.status == self.Status.PREPARING:
            if self.fulfillment_method == self.FulfillmentMethod.SHIPPING:
                next_statuses.discard(self.Status.READY)
            else:
                next_statuses.discard(self.Status.IN_TRANSIT)
        elif self.status == self.Status.READY and self.fulfillment_method != self.FulfillmentMethod.SHIPPING:
            next_statuses.discard(self.Status.IN_TRANSIT)
        return next_statuses

    def can_transition_to(self, new_status):
        return new_status == self.status or new_status in self.valid_next_statuses()

    def valid_next_payment_states(self):
        return PAYMENT_STATE_TRANSITIONS.get(self.payment_state, set())

    def can_payment_transition_to(self, new_state):
        return new_state == self.payment_state or new_state in self.valid_next_payment_states()

    def clean(self):
        super().clean()

        errors = {}
        original_status = getattr(self, '_original_status', None)
        original_payment_state = getattr(self, '_original_payment_state', None)
        self.language = normalized_language(self.language, fallback=self.Language.PT).lower()

        if self.language not in self.Language.values:
            errors['language'] = _('Selecione um idioma suportado.')

        try:
            self.phone = normalize_portuguese_phone(self.phone)
        except ValidationError as error:
            errors['phone'] = error.messages

        self.nif = normalize_portuguese_nif(self.nif)
        try:
            validate_portuguese_nif(self.nif)
        except ValidationError as error:
            errors['nif'] = error.messages

        if original_status and self.status != original_status and not self.can_transition_to(self.status):
            errors['status'] = _('Transição de estado inválida para a encomenda.')

        if original_payment_state and self.payment_state != original_payment_state and not self.can_payment_transition_to(self.payment_state):
            errors['payment_state'] = _('Transição de estado de pagamento inválida.')

        if self.fulfillment_method == self.FulfillmentMethod.PICKUP:
            if not self.pickup_location:
                errors['pickup_location'] = _('Selecione um local de levantamento.')
        elif self.fulfillment_method == self.FulfillmentMethod.SHIPPING:
            for field_name in ('shipping_address_line1', 'shipping_city', 'shipping_postal_code'):
                value = getattr(self, field_name, '')
                if not value or not value.strip():
                    errors[field_name] = _('Este campo é obrigatório para envio.')

            postal_code = (self.shipping_postal_code or '').strip()
            if postal_code and not PT_POSTAL_CODE_RE.match(postal_code):
                errors['shipping_postal_code'] = _('Use o formato 1234-123.')

        status_changed = original_status is None or self.status != original_status
        if status_changed and self.status in {
            self.Status.PREPARING,
            self.Status.READY,
            self.Status.IN_TRANSIT,
            self.Status.DELIVERED,
        }:
            if self.payment_state != self.PaymentState.CONFIRMED:
                errors['status'] = _('A encomenda só pode avançar após pagamento confirmado.')

        if errors:
            raise ValidationError(errors)

    @property
    def status_display_class(self):
        status_classes = {
            self.Status.PENDING: 'bg-stone-100 text-stone-700',
            self.Status.PREPARING: 'bg-sky-100 text-sky-800',
            self.Status.READY: 'bg-blue-100 text-blue-800',
            self.Status.IN_TRANSIT: 'bg-indigo-100 text-indigo-800',
            self.Status.DELIVERED: 'bg-green-100 text-green-800',
            self.Status.CANCELLED: 'bg-rose-100 text-rose-800',
        }
        return status_classes.get(self.status, 'bg-stone-100 text-stone-700')

    @property
    def payment_state_display_class(self):
        state_classes = {
            self.PaymentState.PENDING: 'bg-amber-100 text-amber-800',
            self.PaymentState.CONFIRMED: 'bg-emerald-100 text-emerald-800',
            self.PaymentState.CANCELLED: 'bg-rose-100 text-rose-800',
            self.PaymentState.REFUNDED: 'bg-sky-100 text-sky-800',
        }
        return state_classes.get(self.payment_state, 'bg-stone-100 text-stone-700')

    @property
    def is_shipping(self):
        return self.fulfillment_method == self.FulfillmentMethod.SHIPPING

    @property
    def shipping_address_display(self):
        parts = [self.shipping_address_line1, self.shipping_address_line2, self.shipping_postal_code, self.shipping_city]
        return ', '.join(part for part in parts if part)

    def get_pickup_location_display(self):
        if not self.pickup_location:
            return ''
        location = Location.objects.filter(pickup_location_code=self.pickup_location).only('name').first()
        return location.name if location is not None else self.pickup_location

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

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name=_('encomenda'))
    product = models.ForeignKey(
        'catalog.Product',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('produto'),
    )
    product_name = models.CharField(_('nome do produto'), max_length=255)
    price = models.DecimalField(_('preço'), max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField(
        _('quantidade'),
        validators=[MinValueValidator(1), MaxValueValidator(MAX_PURCHASE_QUANTITY)],
    )

    class Meta:
        verbose_name = _('item da encomenda')
        verbose_name_plural = _('itens da encomenda')
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gte=1) & Q(quantity__lte=MAX_PURCHASE_QUANTITY),
                name='orders_item_quantity_range',
            ),
        ]

    def __str__(self):
        return f'{self.quantity}x {self.product_name}'

    @property
    def subtotal(self):
        return self.price * self.quantity
