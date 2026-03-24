import logging

from django.contrib import messages
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.translation import get_language, gettext as _
from django.views.decorators.http import require_http_methods
from requests import RequestException

from apps.cart.models import Cart, CartItem
from apps.orders.models import Order, OrderItem
from apps.payments.models import Payment
from apps.payments.services import (
    PAYMENT_FAILURE_STATUSES,
    PAYMENT_SUCCESS_STATUSES,
    ifthenpay_service,
    mark_payment_failed,
    mark_payment_paid,
    normalize_provider_status,
)

logger = logging.getLogger(__name__)


def _cart_allows_shipping(items):
    return all(item.product.allow_shipping for item in items)


def _order_url(view_name, order):
    return f"{reverse(view_name, kwargs={'order_id': order.pk})}?token={order.access_token}"


def _get_order_for_request(request, order_id):
    order = get_object_or_404(Order.objects.select_related('payment', 'user'), pk=order_id)

    if request.user.is_authenticated and order.user and order.user.pk == request.user.pk:
        return order

    token = request.GET.get('token') or request.POST.get('token')
    if token and token == str(order.access_token):
        return order

    raise Http404


def _get_order_payment(order):
    try:
        return order.payment
    except Payment.DoesNotExist:
        return None


def _reset_payment(order, method):
    payment, _ = Payment.objects.get_or_create(
        order=order,
        defaults={
            'method': method,
            'amount': order.total,
        },
    )
    payment.method = method
    payment.amount = order.total
    payment.status = Payment.Status.PENDING
    payment.ifthenpay_request_id = ''
    payment.mb_entity = ''
    payment.mb_reference = ''
    payment.mbway_phone = ''
    payment.mbway_transaction_id = ''
    payment.checkout_url = ''
    payment.last_error = ''
    payment.paid_at = None
    payment.expires_at = None
    payment.save()

    if order.status != Order.Status.PAYMENT_PENDING:
        order.status = Order.Status.PAYMENT_PENDING
        order.save(update_fields=['status', 'updated_at'])

    return payment


def checkout(request):
    lang = get_language() or 'pt'

    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
    else:
        cart = Cart.objects.filter(session_key=request.session.session_key).first() if request.session.session_key else None

    if not cart or cart.item_count == 0:
        messages.warning(request, _('O seu carrinho está vazio.'))
        return redirect('cart:detail')

    items = CartItem.objects.filter(cart=cart).select_related('product').prefetch_related('product__translations', 'product__images')
    cart_can_ship = _cart_allows_shipping(items)

    return render(request, 'orders/checkout.html', {
        'cart': cart,
        'items': items,
        'lang': lang,
        'pickup_locations': Order.PickupLocation.choices,
        'cart_can_ship': cart_can_ship,
        'fulfillment_methods': Order.FulfillmentMethod.choices,
    })


def checkout_confirm(request):
    if request.method != 'POST':
        return redirect('orders:checkout')

    lang = get_language() or 'pt'

    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
    else:
        cart = Cart.objects.filter(session_key=request.session.session_key).first() if request.session.session_key else None

    if not cart or cart.item_count == 0:
        return redirect('cart:detail')

    cart_items = list(CartItem.objects.filter(cart=cart).select_related('product'))
    cart_can_ship = _cart_allows_shipping(cart_items)

    name = request.POST.get('name', '')
    email = request.POST.get('email', '')
    phone = request.POST.get('phone', '')
    fulfillment_method = request.POST.get('fulfillment_method', Order.FulfillmentMethod.PICKUP)
    pickup_location = request.POST.get('pickup_location', '')
    shipping_address_line1 = request.POST.get('shipping_address_line1', '')
    shipping_address_line2 = request.POST.get('shipping_address_line2', '')
    shipping_city = request.POST.get('shipping_city', '')
    shipping_postal_code = request.POST.get('shipping_postal_code', '')
    notes = request.POST.get('notes', '')

    if not all([name, email]):
        messages.error(request, _('Por favor preencha todos os campos obrigatórios.'))
        return redirect('orders:checkout')

    valid_methods = {choice for choice, _label in Order.FulfillmentMethod.choices}
    if fulfillment_method not in valid_methods:
        messages.error(request, _('Selecione um método de entrega válido.'))
        return redirect('orders:checkout')

    if fulfillment_method == Order.FulfillmentMethod.SHIPPING:
        if not cart_can_ship:
            messages.error(request, _('Este carrinho contém produtos disponíveis apenas para levantamento em loja.'))
            return redirect('orders:checkout')
        if not all([shipping_address_line1, shipping_city, shipping_postal_code]):
            messages.error(request, _('Preencha a morada de envio completa.'))
            return redirect('orders:checkout')
        pickup_location = ''
    elif not pickup_location:
        messages.error(request, _('Selecione um local de levantamento.'))
        return redirect('orders:checkout')

    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        name=name,
        email=email,
        phone=phone,
        fulfillment_method=fulfillment_method,
        pickup_location=pickup_location,
        shipping_address_line1=shipping_address_line1,
        shipping_address_line2=shipping_address_line2,
        shipping_city=shipping_city,
        shipping_postal_code=shipping_postal_code,
        language=lang,
        notes=notes,
        subtotal=cart.total,
        total=cart.total,
        status=Order.Status.PENDING,
    )

    for cart_item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=cart_item.product,
            product_name=cart_item.product.get_name(lang),
            price=cart_item.product.price,
            quantity=cart_item.quantity,
        )

    CartItem.objects.filter(cart=cart).delete()

    return redirect(_order_url('orders:payment_select', order))


@require_http_methods(['GET', 'POST'])
def payment_select(request, order_id):
    order = _get_order_for_request(request, order_id)
    current_payment = _get_order_payment(order)
    valid_methods = {Payment.Method.MBWAY}

    if order.status == Order.Status.PAID and current_payment:
        return redirect(_order_url('orders:complete', order))

    if request.method == 'GET':
        return render(request, 'orders/payment_select.html', {
            'order': order,
            'lang': get_language() or 'pt',
        })

    payment_method = request.POST.get('payment_method', '')
    if payment_method not in valid_methods:
        messages.error(request, _('Selecione um método de pagamento válido.'))
        return redirect(_order_url('orders:payment_select', order))

    existing_payment = current_payment
    if existing_payment and existing_payment.status == Payment.Status.PAID:
        return redirect(_order_url('orders:complete', order))

    try:
        if existing_payment and existing_payment.status == Payment.Status.PENDING and existing_payment.method == payment_method:
            if payment_method == Payment.Method.MBWAY and existing_payment.ifthenpay_request_id:
                return redirect(_order_url('orders:payment_status', order))

        payment = _reset_payment(order, payment_method)

        if payment_method == Payment.Method.MBWAY:
            mbway_phone = (request.POST.get('mbway_phone') or '').strip()
            if not mbway_phone:
                messages.error(request, _('Indique o número de telemóvel para MB WAY.'))
                return redirect(_order_url('orders:payment_select', order))

            response = ifthenpay_service.create_mbway_payment(str(order.pk), order.total, mbway_phone)
            payment.ifthenpay_request_id = response['request_id']
            payment.mbway_phone = mbway_phone
            payment.mbway_transaction_id = response.get('transaction_id', '')
            payment.save(update_fields=['ifthenpay_request_id', 'mbway_phone', 'mbway_transaction_id'])
            return redirect(_order_url('orders:payment_status', order))
    except RequestException:
        logger.exception('Failed to initiate payment for order %s', order.pk)
        if 'payment' in locals():
            mark_payment_failed(payment, reason='provider request failed during initiation')
        messages.error(request, _('Não foi possível iniciar o pagamento. Tente novamente.'))
        return redirect(_order_url('orders:payment_select', order))


def payment_status(request, order_id):
    order = _get_order_for_request(request, order_id)
    payment = _get_order_payment(order)

    if not payment:
        messages.error(request, _('Ainda não existe um pagamento associado a esta encomenda.'))
        return redirect(_order_url('orders:payment_select', order))

    if payment.status == Payment.Status.PAID or order.status == Order.Status.PAID:
        return redirect(_order_url('orders:complete', order))

    if payment.method == Payment.Method.MBWAY and payment.ifthenpay_request_id and payment.status == Payment.Status.PENDING:
        try:
            provider_status = normalize_provider_status(
                ifthenpay_service.check_mbway_status(payment.ifthenpay_request_id),
            )
        except RequestException:
            logger.exception('Failed to poll MB WAY status for payment %s', payment.pk)
        else:
            if provider_status in PAYMENT_SUCCESS_STATUSES:
                mark_payment_paid(payment, source='mbway_status_poll')
                messages.success(request, _('Pagamento confirmado com sucesso.'))
                return redirect(_order_url('orders:complete', order))
            if provider_status in PAYMENT_FAILURE_STATUSES:
                mark_payment_failed(payment, reason=f'MB WAY status: {provider_status}')
                messages.error(request, _('O pagamento MB WAY não foi confirmado. Pode tentar novamente.'))

    return render(request, 'orders/payment_status.html', {
        'order': order,
        'payment': payment,
        'lang': get_language() or 'pt',
    })


def order_complete(request, order_id):
    order = _get_order_for_request(request, order_id)
    payment = _get_order_payment(order)

    if not payment or order.status != Order.Status.PAID or payment.status != Payment.Status.PAID:
        return redirect(_order_url('orders:payment_status', order))

    return render(request, 'orders/complete.html', {
        'order': order,
        'lang': get_language() or 'pt',
    })
