from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django.utils.translation import get_language
from django.views.decorators.http import require_POST

from apps.cart.forms import AddToCartForm, UpdateCartItemForm
from apps.cart.models import CartItem
from apps.cart.services import (
    add_product_to_cart,
    get_cart_items_queryset,
    get_cart_summary,
    get_or_create_cart_for_request,
    remove_inactive_cart_items,
    set_cart_item_quantity,
)
from apps.catalog.models import Product


UNAVAILABLE_CART_ITEMS_MESSAGE = _('Alguns produtos deixaram de estar disponíveis para compra e foram removidos do carrinho.')


def _render_cart_count(cart_summary, request):
    return render_to_string(
        'cart/_cart_count.html',
        {
            'cart_item_count': cart_summary['cart_item_count'],
            'oob': True,
        },
        request=request,
    )


def _render_cart_popup(cart_summary, request, open_popup=False):
    return render_to_string(
        'cart/_cart_popup.html',
        {
            'cart_preview_items': cart_summary['cart_preview_items'],
            'cart_total': cart_summary['cart_total'],
            'oob': True,
            'open': open_popup,
        },
        request=request,
    )


def _render_cart_messages(request):
    return render_to_string(
        'cart/_messages.html',
        {
            'oob': True,
        },
        request=request,
    )


def _render_cart_item(item, request):
    lang = get_language() or 'pt'
    return render_to_string(
        'cart/_cart_item.html',
        {
            'item': item,
            'lang': lang,
        },
        request=request,
    )


def _render_cart_items(cart, request):
    items = get_cart_items_queryset(cart)
    lang = get_language() or 'pt'
    return render_to_string('cart/_cart_items.html', {
        'items': items,
        'lang': lang,
    }, request=request)


def _render_cart_summary(cart_summary, request):
    return render_to_string(
        'cart/_cart_summary.html',
        {
            'cart_summary': cart_summary,
            'oob': True,
        },
        request=request,
    )


def _cart_htmx_response(*, request, cart, cart_summary, item=None, open_popup=False, delete_target=False, retarget_items=False):
    fragments = []

    if item is not None:
        fragments.append(_render_cart_item(item, request))
    elif retarget_items:
        fragments.append(_render_cart_items(cart, request))

    fragments.extend([
        _render_cart_messages(request),
        _render_cart_summary(cart_summary, request),
        _render_cart_count(cart_summary, request),
        _render_cart_popup(cart_summary, request, open_popup=open_popup),
    ])

    response = HttpResponse(''.join(fragments))
    if delete_target:
        response['HX-Reswap'] = 'delete'
    if retarget_items:
        response['HX-Retarget'] = '#cart-items'
        response['HX-Reswap'] = 'innerHTML'
    return response


def cart_detail(request):
    lang = get_language() or 'pt'
    cart = get_or_create_cart_for_request(request)
    removed_count = remove_inactive_cart_items(cart)
    if removed_count:
        messages.warning(request, UNAVAILABLE_CART_ITEMS_MESSAGE)
    items = get_cart_items_queryset(cart)
    cart_summary = get_cart_summary(cart)

    return render(request, 'cart/detail.html', {
        'cart': cart,
        'items': items,
        'cart_summary': cart_summary,
        'lang': lang,
    })


@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    cart = get_or_create_cart_for_request(request)
    form = AddToCartForm(request.POST)

    if not form.is_valid():
        if request.htmx:
            messages.error(request, _('Indique uma quantidade válida.'))
            response = HttpResponse(_render_cart_messages(request), status=400)
            response['HX-Retarget'] = '#cart-messages'
            response['HX-Reswap'] = 'outerHTML'
            return response
        messages.error(request, _('Indique uma quantidade válida.'))
        return redirect('cart:detail')

    try:
        item, was_capped = add_product_to_cart(cart, product, quantity=form.cleaned_data['quantity'])
    except ValueError:
        if product.is_preview_only:
            messages.error(request, _('Este produto está disponível apenas para pré-visualização.'))
        else:
            messages.error(request, _('Este produto já não está disponível.'))
        return redirect('cart:detail')

    if item is None:
        messages.warning(request, _('Este produto está esgotado.'))
    elif was_capped:
        messages.warning(request, _('A quantidade foi ajustada ao stock disponível.'))

    if request.htmx:
        cart_summary = get_cart_summary(cart)
        return _cart_htmx_response(request=request, cart=cart, cart_summary=cart_summary, open_popup=True)

    return redirect('cart:detail')


@require_POST
def update_cart_item(request, item_id):
    cart = get_or_create_cart_for_request(request)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    form = UpdateCartItemForm(request.POST)

    if not form.is_valid():
        if request.htmx:
            messages.error(request, _('Indique uma quantidade válida.'))
            cart_summary = get_cart_summary(cart)
            return _cart_htmx_response(request=request, cart=cart, cart_summary=cart_summary, item=item)
        messages.error(request, _('Indique uma quantidade válida.'))
        return redirect('cart:detail')

    updated_item, was_capped = set_cart_item_quantity(item, quantity=form.cleaned_data['quantity'])
    if updated_item is None and (not item.product.is_active or item.product.is_preview_only):
        messages.warning(request, UNAVAILABLE_CART_ITEMS_MESSAGE)
    elif updated_item is None and item.product.stock <= 0:
        messages.warning(request, _('Este produto está esgotado.'))
    elif was_capped:
        messages.warning(request, _('A quantidade foi ajustada ao stock disponível.'))

    if request.htmx:
        cart_summary = get_cart_summary(cart)
        if updated_item is not None:
            return _cart_htmx_response(request=request, cart=cart, cart_summary=cart_summary, item=updated_item)

        if cart_summary['cart_item_count'] == 0:
            return _cart_htmx_response(request=request, cart=cart, cart_summary=cart_summary, retarget_items=True)

        return _cart_htmx_response(request=request, cart=cart, cart_summary=cart_summary, delete_target=True)

    return redirect('cart:detail')


@require_POST
def remove_from_cart(request, item_id):
    cart = get_or_create_cart_for_request(request)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    item.delete()

    if request.htmx:
        cart_summary = get_cart_summary(cart)
        if cart_summary['cart_item_count'] == 0:
            return _cart_htmx_response(request=request, cart=cart, cart_summary=cart_summary, retarget_items=True)

        return _cart_htmx_response(request=request, cart=cart, cart_summary=cart_summary, delete_target=True)

    return redirect('cart:detail')
