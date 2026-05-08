import logging

from django.contrib.auth.views import redirect_to_login
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.translation import get_language, gettext as _
from django.views.decorators.http import require_http_methods

from apps.cart.services import adjust_cart_items_for_stock, clear_cart, get_cart_for_request, get_cart_items_queryset, remove_inactive_cart_items, reserve_cart_stock
from apps.orders.forms import CheckoutForm
from apps.orders.models import Order
from apps.orders.services import (
    CartStateChangedError,
    OrderWorkflowError,
    StockValidationError,
    create_order_from_cart,
    discard_pending_order,
)
from apps.core.site_content import payments_are_enabled
from apps.payments.models import Payment
from apps.payments.services import (
    available_payment_services,
    PaymentDisabledError,
    PaymentProcessingError,
    get_payment_service,
    reset_payment,
)

logger = logging.getLogger(__name__)
PAYMENTS_DISABLED_MESSAGE = _('Os pagamentos estão temporariamente indisponíveis. Tente novamente dentro de instantes.')


def _cart_allows_shipping(items):
    return all(item.product.allow_shipping for item in items)


def _order_url(view_name, order):
    return reverse(view_name, kwargs={'order_id': order.pk})


def _require_authenticated_user(request, *, next_url=None):
    if request.user.is_authenticated:
        return None
    return redirect_to_login(next_url or request.get_full_path(), reverse('accounts:login'))


def _get_order_for_request(request, order_id):
    return get_object_or_404(Order.objects.select_related('payment', 'user'), pk=order_id, user=request.user)


def _get_order_payment(order):
    try:
        return order.payment
    except Payment.DoesNotExist:
        return None


def _get_pending_checkout_order(user):
    if not user.is_authenticated:
        return None
    return (
        Order.objects.filter(user=user, status=Order.Status.PENDING, payment_state=Order.PaymentState.PENDING)
        .filter(payment__isnull=True)
        .order_by('-created_at')
        .first()
    )


def _start_order_payment(request, order, *, payment_method=None):
    current_payment = _get_order_payment(order)

    if order.payment_state == Order.PaymentState.CONFIRMED and current_payment:
        return redirect(_order_url('orders:complete', order))
    if order.status == Order.Status.CANCELLED:
        messages.error(request, _('Esta encomenda foi cancelada e já não aceita pagamentos.'))
        if current_payment is not None:
            return redirect(_order_url('orders:payment_status', order))
        return redirect('orders:checkout')
    if not payments_are_enabled():
        return _handle_payments_disabled(request=request, redirect_to='orders:checkout')

    payment = None
    payment_service = get_payment_service(payment_method)
    payment_method = payment_service.method

    try:
        if current_payment and current_payment.status == Payment.Status.CONFIRMED:
            return redirect(_order_url('orders:complete', order))

        if current_payment and current_payment.status == Payment.Status.PENDING and current_payment.method == payment_method:
            if current_payment.checkout_url:
                return redirect(current_payment.checkout_url)
            if payment_method in {Payment.Method.MBWAY_MANUAL, Payment.Method.BANK_TRANSFER}:
                return redirect(_order_url('orders:payment_status', order))

        payment = reset_payment(order, payment_method)
        success_url = request.build_absolute_uri(
            f"{_order_url('orders:payment_status', order)}?session_id={{CHECKOUT_SESSION_ID}}"
        )
        status_url = request.build_absolute_uri(_order_url('orders:payment_status', order))
        cancel_url = request.build_absolute_uri(_order_url('orders:checkout_order', order))
        redirect_url = payment_service.initiate_payment(
            order=order,
            payment=payment,
            success_url=success_url,
            cancel_url=cancel_url,
            status_url=status_url,
        )
        cart = get_cart_for_request(request)
        if cart is not None:
            clear_cart(cart)
        return redirect(redirect_url)
    except PaymentDisabledError:
        messages.error(request, PAYMENTS_DISABLED_MESSAGE)
        return redirect('orders:checkout')
    except PaymentProcessingError as error:
        messages.error(request, str(error) or _('Não foi possível iniciar o pagamento. Tente novamente.'))
        return redirect(_order_url('orders:checkout_order', order))
    except Exception:
        logger.exception('Failed to initiate payment for order %s', order.pk)
        messages.error(request, _('Não foi possível iniciar o pagamento. Tente novamente.'))
        return redirect(_order_url('orders:checkout_order', order))


def _checkout_context(request, cart, items, cart_can_ship, form):
    payment_services = available_payment_services()
    return {
        'cart': cart,
        'items': items,
        'form': form,
        'pickup_locations': list(form.fields['pickup_location'].choices),
        'cart_can_ship': cart_can_ship,
        'payments_enabled': payments_are_enabled(),
        'payment_options': [service.checkout_option() for service in payment_services],
        'pickup_available': getattr(form, 'pickup_available', False),
        'shipping_available': getattr(form, 'shipping_available', False),
    }


def _handle_payments_disabled(*, redirect_to, request):
    messages.error(request, PAYMENTS_DISABLED_MESSAGE)
    return redirect(redirect_to)


def checkout(request, order_id=None):
    login_redirect = _require_authenticated_user(request)
    if login_redirect is not None:
        return login_redirect

    if order_id:
        order = _get_order_for_request(request, order_id)

        payment = _get_order_payment(order)
        if order.payment_state == Order.PaymentState.CONFIRMED and payment:
            return redirect(_order_url('orders:complete', order))
        if payment is not None:
            return redirect(_order_url('orders:payment_status', order))
        return redirect(_order_url('orders:payment_select', order))

    cart = get_cart_for_request(request)
    pending_checkout_order = _get_pending_checkout_order(request.user)
    if pending_checkout_order is not None:
        return redirect(_order_url('orders:payment_select', pending_checkout_order))

    if not cart or cart.item_count == 0:
        messages.warning(request, _('O seu carrinho está vazio.'))
        return redirect('cart:detail')

    removed_count = remove_inactive_cart_items(cart)
    if removed_count:
        messages.warning(request, _('Alguns produtos deixaram de estar disponíveis para compra e foram removidos do carrinho.'))
    items = list(get_cart_items_queryset(cart))
    if not items:
        messages.warning(request, _('O seu carrinho está vazio.'))
        return redirect('cart:detail')

    cart_can_ship = _cart_allows_shipping(items)
    initial = {'fulfillment_method': Order.FulfillmentMethod.PICKUP}

    if request.user.is_authenticated:
        initial.update({
            'name': request.user.get_full_name(),
            'email': request.user.email,
            'phone': request.user.phone,
        })

    form = CheckoutForm(cart_can_ship=cart_can_ship, cart_items=items, initial=initial)

    reserve_cart_stock(cart)

    return render(request, 'orders/checkout.html', _checkout_context(request, cart, items, cart_can_ship, form))


def checkout_confirm(request):
    if request.method != 'POST':
        return redirect('orders:checkout')

    login_redirect = _require_authenticated_user(request, next_url=reverse('orders:checkout'))
    if login_redirect is not None:
        return login_redirect

    if not payments_are_enabled():
        return _handle_payments_disabled(request=request, redirect_to='orders:checkout')

    cart = get_cart_for_request(request)

    if not cart or cart.item_count == 0:
        return redirect('cart:detail')

    removed_count = remove_inactive_cart_items(cart)
    if removed_count:
        messages.warning(request, _('Alguns produtos deixaram de estar disponíveis para compra e foram removidos do carrinho.'))
    cart_items = list(get_cart_items_queryset(cart))
    if not cart_items:
        messages.warning(request, _('O seu carrinho está vazio.'))
        return redirect('cart:detail')

    cart_can_ship = _cart_allows_shipping(cart_items)
    form = CheckoutForm(request.POST, cart_can_ship=cart_can_ship, cart_items=cart_items)

    if not form.is_valid():
        return render(request, 'orders/checkout.html', _checkout_context(request, cart, cart_items, cart_can_ship, form), status=200)

    cleaned_data = form.cleaned_data
    lang = get_language() or 'pt'

    try:
        order = create_order_from_cart(
            cart=cart,
            cart_items=cart_items,
            user=request.user,
            language=lang,
            name=cleaned_data['name'],
            email=cleaned_data['email'],
            phone=cleaned_data['phone'],
            nif=cleaned_data['nif'],
            fulfillment_method=cleaned_data['fulfillment_method'],
            pickup_location=cleaned_data['pickup_location'],
            shipping_address_line1=cleaned_data['shipping_address_line1'],
            shipping_address_line2=cleaned_data['shipping_address_line2'],
            shipping_city=cleaned_data['shipping_city'],
            shipping_postal_code=cleaned_data['shipping_postal_code'],
            notes=cleaned_data['notes'],
            clear_cart_items=False,
        )
        return _start_order_payment(request, order, payment_method=cleaned_data['payment_method'])
    except CartStateChangedError:
        cart_items = list(get_cart_items_queryset(cart))
        if not cart_items:
            messages.warning(request, _('O seu carrinho está vazio.'))
            return redirect('cart:detail')

        cart_can_ship = _cart_allows_shipping(cart_items)
        form = CheckoutForm(request.POST, cart_can_ship=cart_can_ship, cart_items=cart_items)
        form.is_valid()
        form.add_error(None, _('O carrinho foi atualizado durante o checkout. Revise os produtos e tente novamente.'))
        return render(request, 'orders/checkout.html', _checkout_context(request, cart, cart_items, cart_can_ship, form), status=200)
    except StockValidationError:
        adjust_cart_items_for_stock(cart_items, lang=lang)
        form.add_error(None, _('Alguns produtos já não têm stock suficiente. Revise o carrinho e tente novamente.'))
        cart_items = list(get_cart_items_queryset(cart))
        cart_can_ship = _cart_allows_shipping(cart_items) if cart_items else False
        return render(request, 'orders/checkout.html', _checkout_context(request, cart, cart_items, cart_can_ship, form), status=200)
    except Exception:
        logger.exception('Failed to create checkout order for user %s', request.user.pk)
        messages.error(request, _('Não foi possível criar a encomenda. Tente novamente.'))
        return redirect('orders:checkout')


@require_http_methods(['GET', 'POST'])
def payment_select(request, order_id):
    login_redirect = _require_authenticated_user(request)
    if login_redirect is not None:
        return login_redirect

    order = _get_order_for_request(request, order_id)
    return _start_order_payment(request, order)


@require_http_methods(['POST'])
def discard_checkout_order(request, order_id):
    login_redirect = _require_authenticated_user(request)
    if login_redirect is not None:
        return login_redirect

    order = _get_order_for_request(request, order_id)
    try:
        discard_pending_order(order)
    except OrderWorkflowError as error:
        messages.warning(request, str(error))
        return redirect(_order_url('orders:payment_select', order))

    messages.success(request, _('A encomenda pendente foi apagada e o stock foi reposto.'))
    return redirect('orders:checkout')


def payment_status(request, order_id):
    login_redirect = _require_authenticated_user(request)
    if login_redirect is not None:
        return login_redirect

    order = _get_order_for_request(request, order_id)
    payment = _get_order_payment(order)

    if not payment:
        messages.error(request, _('Ainda não existe um pagamento associado a esta encomenda.'))
        return _start_order_payment(request, order)

    if order.payment_state == Order.PaymentState.CONFIRMED:
        return redirect(_order_url('orders:complete', order))

    if order.status == Order.Status.CANCELLED:
        return render(request, 'orders/payment_status.html', {
            'order': order,
            'payment': payment,
            'payment_provider': get_payment_service(payment.method).payment_status_context(payment),
        })

    payment_service = get_payment_service(payment.method)

    if payment.status == Payment.Status.PENDING:
        try:
            refresh_state = payment_service.refresh_pending_payment(payment)
        except Exception:
            logger.exception('Failed to refresh payment state for payment %s', payment.pk)
        else:
            if refresh_state == 'confirmed':
                messages.success(request, _('Pagamento confirmado com sucesso.'))
                return redirect(_order_url('orders:complete', order))
            if refresh_state == 'cancelled':
                payment.refresh_from_db()
                messages.error(request, _('O pagamento foi cancelado. Pode iniciar novamente.'))

    timeout_minutes = None
    expires_at_iso = None
    if payment.expires_at and payment.status == Payment.Status.PENDING:
        from django.utils import timezone

        remaining = payment.expires_at - timezone.now()
        timeout_minutes = max(int(remaining.total_seconds() // 60), 0)
        if remaining.total_seconds() > 0:
            expires_at_iso = payment.expires_at.isoformat()

    return render(request, 'orders/payment_status.html', {
        'order': order,
        'payment': payment,
        'payment_provider': payment_service.payment_status_context(payment),
        'payment_timeout_minutes': timeout_minutes,
        'expires_at_iso': expires_at_iso,
    })


def order_complete(request, order_id):
    login_redirect = _require_authenticated_user(request)
    if login_redirect is not None:
        return login_redirect

    order = _get_order_for_request(request, order_id)
    payment = _get_order_payment(order)

    if order.payment_state != Order.PaymentState.CONFIRMED:
        return redirect(_order_url('orders:payment_status', order))

    return render(request, 'orders/complete.html', {
        'order': order,
        'payment': payment,
    })
