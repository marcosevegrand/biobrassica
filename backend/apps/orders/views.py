import logging

from django.contrib.auth.views import redirect_to_login
from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.translation import get_language, gettext as _
from django.views.decorators.http import require_http_methods

from apps.cart.services import adjust_cart_items_for_stock, clear_cart, get_cart_for_request, get_cart_items_queryset, remove_inactive_cart_items
from apps.orders.forms import CheckoutForm, PaymentSelectionForm
from apps.orders.models import Order
from apps.orders.services import CartStateChangedError, StockValidationError, cancel_unpaid_order, create_order_from_cart, transition_order_status
from apps.core.site_content import payments_are_enabled
from apps.payments.models import Payment
from apps.payments.services import (
    PaymentDisabledError,
    configure_stripe_checkout,
    expire_pending_payment,
    finalize_successful_payment,
    reset_payment,
    stripe_service,
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


def _payment_select_context(order, form):
    return {
        'order': order,
        'form': form,
        'payments_enabled': payments_are_enabled(),
    }


def _checkout_context(request, cart, items, cart_can_ship, form):
    return {
        'cart': cart,
        'items': items,
        'form': form,
        'pickup_locations': list(form.fields['pickup_location'].choices),
        'cart_can_ship': cart_can_ship,
        'payments_enabled': payments_are_enabled(),
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
        if order.status == Order.Status.PAID and payment:
            return redirect(_order_url('orders:complete', order))
        if payment is not None:
            return redirect(_order_url('orders:payment_status', order))
        return redirect(_order_url('orders:payment_select', order))

    cart = get_cart_for_request(request)

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
    order = None
    payment = None

    try:
        order = create_order_from_cart(
            cart=cart,
            cart_items=cart_items,
            user=request.user,
            language=lang,
            name=cleaned_data['name'],
            email=cleaned_data['email'],
            phone=cleaned_data['phone'],
            fulfillment_method=cleaned_data['fulfillment_method'],
            pickup_location=cleaned_data['pickup_location'],
            shipping_address_line1=cleaned_data['shipping_address_line1'],
            shipping_address_line2=cleaned_data['shipping_address_line2'],
            shipping_city=cleaned_data['shipping_city'],
            shipping_postal_code=cleaned_data['shipping_postal_code'],
            notes=cleaned_data['notes'],
            clear_cart_items=False,
        )

        payment = Payment.objects.create(
            order=order,
            method=Payment.Method.STRIPE,
            status=Payment.Status.PENDING,
            amount=order.total,
        )

        transition_order_status(order, Order.Status.PAYMENT_PENDING)

        success_url = request.build_absolute_uri(
            f"{_order_url('orders:payment_status', order)}?session_id={{CHECKOUT_SESSION_ID}}"
        )
        cancel_url = request.build_absolute_uri(_order_url('orders:checkout_order', order))
        response = stripe_service.create_checkout_session(
            order=order,
            payment=payment,
            success_url=success_url,
            cancel_url=cancel_url,
        )
        configure_stripe_checkout(
            payment,
            session_id=response['session_id'],
            payment_intent_id=response.get('payment_intent_id', ''),
            checkout_url=response['checkout_url'],
            expires_at=response.get('expires_at'),
        )
        clear_cart(cart)
        return redirect(payment.checkout_url)
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
    except PaymentDisabledError:
        if order is not None:
            try:
                cancel_unpaid_order(order)
            except Exception:
                logger.exception('Failed to cancel order %s after payments were disabled', order.pk)
        if payment is not None:
            payment.delete()
        return _handle_payments_disabled(request=request, redirect_to='orders:checkout')
    except Exception:
        if order is not None:
            try:
                cancel_unpaid_order(order)
            except Exception:
                logger.exception('Failed to cancel order %s after Stripe setup failure', order.pk)
        if payment is not None:
            payment.delete()
        logger.exception('Failed to initiate Stripe payment for order %s', order.pk if order else 'new')
        messages.error(request, _('Não foi possível iniciar o pagamento. Tente novamente.'))
        return redirect('orders:checkout')


@require_http_methods(['GET', 'POST'])
def payment_select(request, order_id):
    login_redirect = _require_authenticated_user(request)
    if login_redirect is not None:
        return login_redirect

    order = _get_order_for_request(request, order_id)
    current_payment = _get_order_payment(order)

    if order.status == Order.Status.PAID and current_payment:
        return redirect(_order_url('orders:complete', order))

    if request.method == 'GET':
        form = PaymentSelectionForm(initial={'payment_method': Payment.Method.STRIPE})
        return render(request, 'orders/payment_select.html', _payment_select_context(order, form))

    if not payments_are_enabled():
        return _handle_payments_disabled(request=request, redirect_to=_order_url('orders:payment_select', order))

    form = PaymentSelectionForm(request.POST)
    if not form.is_valid():
        return render(request, 'orders/payment_select.html', _payment_select_context(order, form), status=200)

    payment_method = form.cleaned_data['payment_method']
    existing_payment = current_payment
    if existing_payment and existing_payment.status == Payment.Status.PAID:
        return redirect(_order_url('orders:complete', order))

    try:
        if existing_payment and existing_payment.status == Payment.Status.PENDING and existing_payment.method == payment_method:
            if payment_method == Payment.Method.STRIPE and existing_payment.checkout_url:
                return redirect(_order_url('orders:payment_status', order))

        payment = reset_payment(order, payment_method)

        if payment_method == Payment.Method.STRIPE:
            success_url = request.build_absolute_uri(
                f"{_order_url('orders:payment_status', order)}?session_id={{CHECKOUT_SESSION_ID}}"
            )
            cancel_url = request.build_absolute_uri(_order_url('orders:payment_select', order))
            response = stripe_service.create_checkout_session(
                order=order,
                payment=payment,
                success_url=success_url,
                cancel_url=cancel_url,
            )
            configure_stripe_checkout(
                payment,
                session_id=response['session_id'],
                payment_intent_id=response.get('payment_intent_id', ''),
                checkout_url=response['checkout_url'],
                expires_at=response.get('expires_at'),
            )
            return redirect(payment.checkout_url)
    except PaymentDisabledError:
        messages.error(request, PAYMENTS_DISABLED_MESSAGE)
        return redirect(_order_url('orders:payment_select', order))
    except Exception:
        logger.exception('Failed to initiate payment for order %s', order.pk)
        messages.error(request, _('Não foi possível iniciar o pagamento. Tente novamente.'))
        return redirect(_order_url('orders:payment_select', order))


def payment_status(request, order_id):
    login_redirect = _require_authenticated_user(request)
    if login_redirect is not None:
        return login_redirect

    order = _get_order_for_request(request, order_id)
    payment = _get_order_payment(order)

    if not payment:
        messages.error(request, _('Ainda não existe um pagamento associado a esta encomenda.'))
        return redirect(_order_url('orders:payment_select', order))

    if payment.status == Payment.Status.PAID or order.status == Order.Status.PAID:
        return redirect(_order_url('orders:complete', order))

    if payment.method == Payment.Method.STRIPE and payment.stripe_session_id and payment.status == Payment.Status.PENDING:
        try:
            session = stripe_service.retrieve_checkout_session(payment.stripe_session_id)
        except Exception:
            logger.exception('Failed to fetch Stripe Checkout session for payment %s', payment.pk)
        else:
            if getattr(session, 'payment_status', '') == 'paid':
                with transaction.atomic():
                    locked_payment = Payment.objects.select_for_update().select_related('order').get(pk=payment.pk)
                    finalize_successful_payment(locked_payment, source='stripe_checkout_poll')
                messages.success(request, _('Pagamento confirmado com sucesso.'))
                return redirect(_order_url('orders:complete', order))
            if getattr(session, 'status', '') == 'expired':
                with transaction.atomic():
                    locked_payment = Payment.objects.select_for_update().select_related('order').get(pk=payment.pk)
                    expire_pending_payment(locked_payment, reason='stripe checkout expired (poll)')
                payment.refresh_from_db()
                messages.error(request, _('A sessão de pagamento expirou. Pode iniciar novamente.'))

    return render(request, 'orders/payment_status.html', {
        'order': order,
        'payment': payment,
    })


def order_complete(request, order_id):
    login_redirect = _require_authenticated_user(request)
    if login_redirect is not None:
        return login_redirect

    order = _get_order_for_request(request, order_id)
    payment = _get_order_payment(order)

    if not payment or order.status != Order.Status.PAID or payment.status != Payment.Status.PAID:
        return redirect(_order_url('orders:payment_status', order))

    return render(request, 'orders/complete.html', {
        'order': order,
    })
