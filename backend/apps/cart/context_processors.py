from apps.cart.services import get_cart_for_request, get_cart_summary


def cart_count(request):
    cart = get_cart_for_request(request)
    return get_cart_summary(cart)
