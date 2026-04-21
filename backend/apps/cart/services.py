from collections.abc import Iterable
from decimal import Decimal

from django.db import transaction
from django.db.models import DecimalField, ExpressionWrapper, F, Q, Sum
from django.db.models.functions import Coalesce

from apps.cart.models import Cart, CartItem


def _cap_quantity_to_stock(product, requested_quantity):
    available_stock = max(product.stock, 0)
    final_quantity = min(requested_quantity, available_stock)
    was_capped = final_quantity != requested_quantity
    return final_quantity, was_capped


def get_cart_for_request(request):
    if request.user.is_authenticated:
        return Cart.objects.filter(user=request.user).first()

    session = getattr(request, 'session', None)
    if session and session.session_key:
        return Cart.objects.filter(session_key=session.session_key).first()

    return None


def get_or_create_cart_for_request(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart

    if not request.session.session_key:
        request.session.create()

    cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
    return cart


def get_cart_items_queryset(cart):
    return (
        cart.items.filter(product__is_active=True, product__is_preview_only=False)
        .select_related('product')
        .prefetch_related('product__translations', 'product__images')
    )


def get_cart_preview_items(cart, *, limit=3):
    return list(get_cart_items_queryset(cart)[:limit])


def get_cart_totals(cart):
    if cart is None:
        return {
            'cart_item_count': 0,
            'cart_total': Decimal('0'),
        }

    totals = cart.items.filter(product__is_active=True, product__is_preview_only=False).aggregate(
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
    if not product.is_active or product.is_preview_only:
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
        if not locked_item.product.is_active or locked_item.product.is_preview_only:
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
    session_key = getattr(request.session, 'session_key', None)

    with transaction.atomic():
        user_cart, _ = Cart.objects.get_or_create(user=user)
        if not session_key:
            return user_cart

        anonymous_cart = Cart.objects.select_for_update().filter(session_key=session_key).exclude(pk=user_cart.pk).first()
        if not anonymous_cart:
            return user_cart

        anonymous_items = list(anonymous_cart.items.select_related('product').order_by('pk'))
        product_ids = [item.product.pk for item in anonymous_items]
        existing_items = {
            item.product.pk: item
            for item in user_cart.items.select_related('product').filter(product_id__in=product_ids)
        }

        for item in anonymous_items:
            if not item.product.is_active or item.product.is_preview_only:
                item.delete()
                continue

            existing_item = existing_items.get(item.product.pk)

            if existing_item:
                merged_quantity, _ = _cap_quantity_to_stock(item.product, existing_item.quantity + item.quantity)
                if merged_quantity > 0:
                    existing_item.quantity = merged_quantity
                    existing_item.save(update_fields=['quantity'])
                else:
                    existing_item.delete()
                item.delete()
                continue

            merged_quantity, _ = _cap_quantity_to_stock(item.product, item.quantity)
            if merged_quantity <= 0:
                item.delete()
                continue

            item.quantity = merged_quantity
            item.cart = user_cart
            item.save(update_fields=['quantity', 'cart'])

        anonymous_cart.delete()
        return user_cart


def clear_cart(cart):
    cart.items.all().delete()


def remove_inactive_cart_items(cart):
    deleted_count, _ = cart.items.filter(
        Q(product__is_active=False) | Q(product__is_preview_only=True)
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