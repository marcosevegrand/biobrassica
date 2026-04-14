from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.cart.services import clear_cart
from apps.catalog.models import Product
from apps.orders.models import Order, OrderItem


class OrderWorkflowError(Exception):
    pass


class OrderStateTransitionError(OrderWorkflowError):
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


def cancel_unpaid_order(order):
    from apps.payments.models import Payment

    with transaction.atomic():
        locked_order = (
            Order.objects.select_for_update()
            .prefetch_related('items__product')
            .get(pk=order.pk)
        )

        payment = Payment.objects.select_for_update().filter(order_id=locked_order.pk).first()
        if payment is not None and payment.status == payment.Status.PAID:
            raise OrderStateTransitionError('As encomendas pagas não podem ser canceladas por este fluxo.')

        if locked_order.status in {Order.Status.PREPARING, Order.Status.READY, Order.Status.DELIVERED}:
            raise OrderStateTransitionError('A encomenda já entrou em preparação e não pode ser cancelada aqui.')

        if locked_order.status == Order.Status.CANCELLED:
            return False

        product_ids = [item.product.pk for item in locked_order.items.all() if item.product is not None]
        locked_products = {
            product.pk: product
            for product in Product.objects.select_for_update().filter(pk__in=product_ids)
        }

        transition_order_status(locked_order, Order.Status.CANCELLED)

        for item in locked_order.items.all():
            if item.product is None:
                continue
            product = locked_products.get(item.product.pk)
            if product is None:
                continue
            product.stock += item.quantity
            product.save(update_fields=['stock', 'updated_at'])

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
    fulfillment_method,
    pickup_location,
    shipping_address_line1,
    shipping_address_line2,
    shipping_city,
    shipping_postal_code,
    notes,
    clear_cart_items=True,
):
    with transaction.atomic():
        if not cart_items:
            raise StockValidationError([])

        product_ids = [cart_item.product_id for cart_item in cart_items if cart_item.product_id]
        locked_products = {
            product.pk: product
            for product in Product.objects.select_for_update().filter(pk__in=product_ids)
        }
        stock_errors = []

        for cart_item in cart_items:
            product = locked_products.get(cart_item.product_id)
            if product is None or not product.is_active or product.stock < cart_item.quantity:
                stock_errors.append(cart_item.product.get_name(language))

        if stock_errors:
            raise StockValidationError(stock_errors)

        total = cart.total
        order = Order(
            user=user,
            name=name,
            email=email,
            phone=phone,
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
        )
        try:
            order.full_clean()
        except ValidationError as error:
            _raise_validation_error(error)
        order.save()

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

        if clear_cart_items:
            clear_cart(cart)
        return order