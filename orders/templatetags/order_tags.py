from django import template
from orders.models import Wishlist
from orders.utils import get_products_in_cart, calculate_total_price

register = template.Library()


@register.filter
def multiply(price, quantity):
    try:
        return float(price) * int(quantity)
    except (ValueError, TypeError):
        return 0


@register.filter
def in_cart(request, pk):
    return pk in request.session.get('cart', [])


@register.filter
def in_wishlist(request, pk):
    return pk in request.session.get('wishlist', [])


@register.simple_tag
def get_user_cart(request):
    return get_products_in_cart(request)


@register.simple_tag
def get_product_count(request):
    return len(request.session.get('cart', []))


@register.simple_tag
def get_cart_total(request):
    products = get_products_in_cart(request)
    return calculate_total_price(products=products)


@register.simple_tag
def wishlist_count(request):
    user = getattr(request, 'user', None)
    if user and user.is_authenticated:
        return Wishlist.objects.filter(user=user).count()
    return 0