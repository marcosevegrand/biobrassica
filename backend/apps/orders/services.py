from dataclasses import dataclass
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.cart.services import clear_cart
from apps.cart.models import CartItem
from apps.catalog.models import Product
from apps.orders.models import Order, OrderItem


class OrderWorkflowError(Exception):
    pass


class OrderStateTransitionError(OrderWorkflowError):
    pass


class CartStateChangedError(OrderWorkflowError):
    pass


@dataclass(slots=True)
class StockValidationError(OrderWorkflowError):
    items: list[str]

    def __str__(self):
        if not self.items:
            return 'O stock disponível mudou durante o checkout.'
        return 'Sem stock suficiente para: ' + ', '.join(self.items)


def _raise_validation_error(error):
    if hasattr(error, 'message_dict'):
        message = '; '.join(
            f'{field}: {", ".join(messages)}'
            for field, messages in error.message_dict.items()
        )
    else:
        message = '; '.join(error.messages)
    raise OrderStateTransitionError(message)


def _cart_item_snapshot(cart_items):
    return {
        cart_item.pk: (cart_item.product_id, cart_item.quantity)
        for cart_item in cart_items
    }


def transition_order_status(order, new_status):
    if order.status == new_status:
        return False

    if not order.can_transition_to(new_status):
        raise OrderStateTransitionError('Transição de estado inválida para a encomenda.')

    order.status = new_status
    try:
        order.full_clean()
    except ValidationError as error:
        _raise_validation_error(error)
    order.save(update_fields=['status', 'updated_at'])
    return True


def transition_payment_state(order, new_state):
    if order.payment_state == new_state:
        return False

    if not order.can_payment_transition_to(new_state):
        raise OrderStateTransitionError('Transição de estado de pagamento inválida.')

    order.payment_state = new_state
    order.save(update_fields=['payment_state', 'updated_at'])
    return True


def _restore_stock_from_order_items(locked_order):
    product_ids = [item.product_id for item in locked_order.items.all() if item.product_id]
    if not product_ids:
        return

    locked_products = {
        product.pk: product
        for product in Product.objects.select_for_update().filter(pk__in=product_ids)
    }

    for item in locked_order.items.all():
        if item.product_id is None:
            continue
        product = locked_products.get(item.product_id)
        if product is None:
            continue
        product.stock += item.quantity
        product.save(update_fields=['stock', 'updated_at'])


def cancel_order(order):
    with transaction.atomic():
        locked_order = (
            Order.objects.select_for_update()
            .prefetch_related('items__product')
            .get(pk=order.pk)
        )

        if locked_order.status == Order.Status.CANCELLED:
            return False
        if locked_order.status == Order.Status.DELIVERED:
            raise OrderStateTransitionError('A encomenda já foi entregue e não pode ser cancelada.')

        transition_order_status(locked_order, Order.Status.CANCELLED)
        _restore_stock_from_order_items(locked_order)
        return True


def cancel_order_for_expired_payment(order):
    from apps.payments.models import Payment
    from apps.payments.services import transition_payment_status

    with transaction.atomic():
        locked_order = Order.objects.select_for_update().get(pk=order.pk)

        payment = Payment.objects.select_for_update().filter(order_id=locked_order.pk).first()
        if payment is None:
            raise OrderStateTransitionError('A encomenda não tem pagamento associado para este cancelamento automático.')
        if payment.status != Payment.Status.PENDING:
            return False

        transition_payment_status(
            payment,
            Payment.Status.CANCELLED,
            reason='Pagamento cancelado por expiração.',
            source='payment_timeout',
        )
        transition_payment_state(locked_order, Order.PaymentState.CANCELLED)

        return True


def discard_pending_order(order):
    from apps.payments.models import Payment

    with transaction.atomic():
        locked_order = (
            Order.objects.select_for_update()
            .prefetch_related('items__product')
            .get(pk=order.pk)
        )

        if Payment.objects.select_for_update().filter(order_id=locked_order.pk).exists():
            raise OrderStateTransitionError('A encomenda já tem um pagamento associado e não pode ser apagada.')

        product_ids = [item.product.pk for item in locked_order.items.all() if item.product is not None]
        locked_products = {
            product.pk: product
            for product in Product.objects.select_for_update().filter(pk__in=product_ids)
        }

        for item in locked_order.items.all():
            if item.product is None:
                continue
            product = locked_products.get(item.product.pk)
            if product is None:
                continue
            product.stock += item.quantity
            product.save(update_fields=['stock', 'updated_at'])

        locked_order.delete()
        return True


def create_order_from_cart(
    *,
    cart,
    cart_items,
    user,
    language,
    name,
    email,
    phone,
    nif,
    fulfillment_method,
    pickup_location,
    shipping_address_line1,
    shipping_address_line2,
    shipping_city,
    shipping_postal_code,
    notes,
    clear_cart_items=True,
):
    snapshot = _cart_item_snapshot(cart_items)

    with transaction.atomic():
        locked_cart_items = list(
            cart.items.select_for_update().select_related('product').order_by('pk')
        )

        if not locked_cart_items:
            raise StockValidationError([])

        if snapshot != _cart_item_snapshot(locked_cart_items):
            raise CartStateChangedError('O carrinho foi atualizado durante o checkout.')

        cart_items = locked_cart_items
        reservation_active = (
            cart.reserved_until is not None
            and cart.reserved_until > timezone.now()
        )

        product_ids = [cart_item.product_id for cart_item in cart_items if cart_item.product_id]
        locked_products = {
            product.pk: product
            for product in Product.objects.select_for_update().filter(pk__in=product_ids)
        }

        if reservation_active:
            stock_errors = []
            for cart_item in cart_items:
                if cart_item.reserved_quantity != cart_item.quantity:
                    stock_errors.append(cart_item.product.get_name(language))
            if stock_errors:
                raise StockValidationError(stock_errors)
        else:
            stock_errors = []
            for cart_item in cart_items:
                product = locked_products.get(cart_item.product_id)
                if product is None or not product.is_purchasable or product.stock < cart_item.quantity:
                    stock_errors.append(cart_item.product.get_name(language))
            if stock_errors:
                raise StockValidationError(stock_errors)

        total = sum(
            (cart_item.product.price * cart_item.quantity for cart_item in cart_items),
            Decimal('0.00'),
        )
        order = Order(
            user=user,
            name=name,
            email=email,
            phone=phone,
            nif=nif,
            fulfillment_method=fulfillment_method,
            pickup_location=pickup_location,
            shipping_address_line1=shipping_address_line1,
            shipping_address_line2=shipping_address_line2,
            shipping_city=shipping_city,
            shipping_postal_code=shipping_postal_code,
            language=language,
            notes=notes,
            subtotal=total,
            total=total,
            status=Order.Status.PENDING,
            payment_state=Order.PaymentState.PENDING,
        )
        try:
            order.full_clean()
        except ValidationError as error:
            _raise_validation_error(error)
        order.save()

        if not reservation_active:
            for cart_item in cart_items:
                product = locked_products[cart_item.product_id]
                product.stock -= cart_item.quantity
                product.save(update_fields=['stock', 'updated_at'])

        OrderItem.objects.bulk_create([
            OrderItem(
                order=order,
                product=cart_item.product,
                product_name=cart_item.product.get_name(language),
                price=cart_item.product.price,
                quantity=cart_item.quantity,
            )
            for cart_item in cart_items
        ])

        for cart_item in cart_items:
            cart_item.reserved_quantity = 0
        CartItem.objects.bulk_update(cart_items, ['reserved_quantity'])

        cart.reserved_until = None
        cart.save(update_fields=['reserved_until'])

        if clear_cart_items:
            clear_cart(cart)
        return order
