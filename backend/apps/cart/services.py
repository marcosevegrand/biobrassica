from collections.abc import Iterable
from decimal import Decimal

from django.db import transaction
from django.db.models import DecimalField, ExpressionWrapper, F, Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.cart.models import Cart, CartItem
from apps.catalog.models import Product
from apps.core.limits import MAX_PURCHASE_QUANTITY


def _cap_quantity_to_stock(product, requested_quantity):
    available_stock = min(max(product.stock, 0), MAX_PURCHASE_QUANTITY)
    final_quantity = min(requested_quantity, available_stock)
    was_capped = final_quantity != requested_quantity
    return final_quantity, was_capped


def get_cart_for_request(request):
    if request.user.is_authenticated:
        return Cart.objects.filter(user=request.user).first()
    return None


def get_or_create_cart_for_request(request):
    if not request.user.is_authenticated:
        return None

    cart, _ = Cart.objects.get_or_create(user=request.user)
    return cart


def get_cart_items_queryset(cart):
    return (
        cart.items.filter(product__is_active=True, product__is_preview=False)
        .select_related('product')
        .prefetch_related('product__translations', 'product__pickup_locations')
    )


def get_cart_preview_items(cart, *, limit=3):
    return list(get_cart_items_queryset(cart)[:limit])


def get_cart_totals(cart):
    if cart is None:
        return {
            'cart_item_count': 0,
            'cart_total': Decimal('0'),
        }

    totals = cart.items.filter(product__is_active=True, product__is_preview=False).aggregate(
        cart_item_count=Coalesce(Sum('quantity'), 0),
        cart_total=Coalesce(
            Sum(
                ExpressionWrapper(
                    F('quantity') * F('product__price'),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                ),
            ),
            Decimal('0'),
        ),
    )

    return {
        'cart_item_count': totals['cart_item_count'],
        'cart_total': totals['cart_total'],
    }


def get_cart_summary(cart, *, preview_limit=3):
    totals = get_cart_totals(cart)
    preview_items = [] if cart is None else get_cart_preview_items(cart, limit=preview_limit)

    return {
        'cart_item_count': totals['cart_item_count'],
        'cart_preview_items': preview_items,
        'cart_total': totals['cart_total'],
    }


def add_product_to_cart(cart, product, *, quantity):
    if not product.is_active or product.is_preview:
        raise ValueError('Cannot add an unavailable product to cart.')

    with transaction.atomic():
        item = CartItem.objects.select_for_update().filter(cart=cart, product=product).first()
        current_quantity = item.quantity if item else 0
        final_quantity, was_capped = _cap_quantity_to_stock(product, current_quantity + quantity)

        if final_quantity <= 0:
            if item:
                item.delete()
            return None, was_capped

        if item:
            item.quantity = final_quantity
            item.save(update_fields=['quantity'])
            return item, was_capped

        item = CartItem.objects.create(cart=cart, product=product, quantity=final_quantity)
        return item, was_capped


def set_cart_item_quantity(item, *, quantity):
    with transaction.atomic():
        locked_item = CartItem.objects.select_for_update().select_related('product').get(pk=item.pk)
        if not locked_item.product.is_active or locked_item.product.is_preview:
            locked_item.delete()
            return None, False
        final_quantity, was_capped = _cap_quantity_to_stock(locked_item.product, quantity)

        if final_quantity <= 0:
            locked_item.delete()
            return None, was_capped

        locked_item.quantity = final_quantity
        locked_item.save(update_fields=['quantity'])
        return locked_item, was_capped


def merge_anonymous_cart_into_user_cart(request, user):
    """Anonymous carts no longer exist; this is now a no-op that returns the user's cart."""
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


def clear_cart(cart):
    cart.items.all().delete()


def remove_inactive_cart_items(cart):
    deleted_count, _ = cart.items.filter(
        Q(product__is_active=False) | Q(product__is_preview=True)
    ).delete()
    return deleted_count


def cart_allows_shipping(cart_items: Iterable):
    return all(item.product.allow_shipping for item in cart_items)


def adjust_cart_items_for_stock(cart_items: Iterable, *, lang=None):
    out_of_stock_items = []

    for cart_item in cart_items:
        product = cart_item.product
        if cart_item.quantity <= product.stock:
            continue

        out_of_stock_items.append({
            'product_name': product.get_name(lang),
            'requested': cart_item.quantity,
            'available': product.stock,
        })

        if product.stock > 0:
            cart_item.quantity = product.stock
            cart_item.save(update_fields=['quantity'])
            continue

        cart_item.delete()

    return bool(out_of_stock_items), out_of_stock_items


def reserve_cart_stock(cart, *, timeout_minutes=None):
    """Reserve stock for every item in the cart without creating an order.

    Locks products and cart items, deducts stock from each product,
    and records the reserved quantity on each CartItem. If stock is
    already reserved from a previous visit to checkout, the old
    reservation is released first.

    Returns False when timeout_minutes resolves to <= 0 or the cart
    is empty — no reservation is created and the caller falls back
    to deducting stock at order-creation time.
    """
    from apps.core.models import ShopSettings

    settings_obj = ShopSettings.objects.filter(pk=1).only('checkout_reservation_minutes').first()
    timeout_minutes = getattr(settings_obj, 'checkout_reservation_minutes', 30) if settings_obj else 30

    if timeout_minutes <= 0:
        return False
    with transaction.atomic():
        locked_items = list(
            cart.items.select_for_update()
            .select_related('product')
            .filter(product__is_active=True, product__is_preview=False)
        )

        if not locked_items:
            return False

        product_ids = [item.product_id for item in locked_items]
        locked_products = {
            p.pk: p
            for p in Product.objects.select_for_update().filter(pk__in=product_ids)
        }

        for item in locked_items:
            if item.reserved_quantity > 0:
                product = locked_products.get(item.product_id)
                if product is not None:
                    product.stock += item.reserved_quantity
                    product.save(update_fields=['stock', 'updated_at'])
                item.reserved_quantity = 0

        for item in locked_items:
            product = locked_products.get(item.product_id)
            if product is None or not product.is_purchasable or product.stock < item.quantity:
                for prev_item in locked_items:
                    prev_item.reserved_quantity = 0
                CartItem.objects.bulk_update(locked_items, ['reserved_quantity'])
                return False

        for item in locked_items:
            product = locked_products[item.product_id]
            product.stock -= item.quantity
            product.save(update_fields=['stock', 'updated_at'])
            item.reserved_quantity = item.quantity

        CartItem.objects.bulk_update(locked_items, ['reserved_quantity'])

        cart.reserved_until = timezone.now() + timezone.timedelta(minutes=timeout_minutes)
        cart.save(update_fields=['reserved_until'])
        return True


def release_cart_reservation(cart):
    """Return reserved stock back to products and clear the reservation.

    Used when a cart is abandoned or the checkout reservation
    expires, so other customers can purchase the stock.
    """
    with transaction.atomic():
        locked_items = list(
            cart.items.select_for_update()
            .select_related('product')
            .filter(reserved_quantity__gt=0)
        )

        if not locked_items:
            return False

        product_ids = [item.product_id for item in locked_items]
        locked_products = {
            p.pk: p
            for p in Product.objects.select_for_update().filter(pk__in=product_ids)
        }

        for item in locked_items:
            product = locked_products.get(item.product_id)
            if product is not None and item.reserved_quantity > 0:
                product.stock += item.reserved_quantity
                product.save(update_fields=['stock', 'updated_at'])
            item.reserved_quantity = 0
            item.save(update_fields=['reserved_quantity'])

        cart.reserved_until = None
        cart.save(update_fields=['reserved_until'])
        return True


def release_expired_reservations():
    from django.db.models import Prefetch

    expired_carts = Cart.objects.filter(
        reserved_until__isnull=False,
        reserved_until__lt=timezone.now(),
    ).prefetch_related(
        Prefetch('items', queryset=CartItem.objects.filter(reserved_quantity__gt=0).select_related('product')),
    )

    released = 0
    for cart in expired_carts:
        if release_cart_reservation(cart):
            released += 1
    return released
