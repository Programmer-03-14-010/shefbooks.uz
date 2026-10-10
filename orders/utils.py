from decimal import Decimal

from django.conf import settings
from django.utils.http import url_has_allowed_host_and_scheme

from products.models import ProductModel


def get_cart_quantities(request):
    """{product_id(int): qty(int)} — sessiyadagi savat."""
    cart = request.session.get('cart', [])
    quantities = request.session.get('cart_quantities', {})
    result = {}
    for pk in cart:
        try:
            result[int(pk)] = max(1, int(quantities.get(str(pk), 1)))
        except (TypeError, ValueError):
            continue
    return result


def get_products_in_cart(request):
    """Savatdagi mahsulotlar (o'chirib yuborilganlari tushib qoladi)."""
    quantities = get_cart_quantities(request)
    if not quantities:
        return []
    found = {p.pk: p for p in ProductModel.objects.filter(pk__in=quantities.keys())}
    return [found[pk] for pk in quantities if pk in found]


def build_cart_items(request):
    """[{'product', 'quantity', 'subtotal'}], total — miqdor va ombor qoldig'i hisobga olingan."""
    quantities = get_cart_quantities(request)
    items, total = [], Decimal('0')
    for product in get_products_in_cart(request):
        qty = quantities.get(product.pk, 1)
        subtotal = product.price * qty
        total += subtotal
        items.append({'product': product, 'quantity': qty, 'subtotal': subtotal})
    return items, total


def calculate_total_price(products):
    return sum((p.price for p in products), Decimal('0'))


def safe_next_url(request, default):
    """`next` parametri faqat shu saytning ichki manzili bo'lsa qabul qilinadi (open-redirect himoyasi)."""
    nxt = request.POST.get('next') or request.GET.get('next') or ''
    if nxt and url_has_allowed_host_and_scheme(
        nxt, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return nxt
    return default


def delivery_fee_for_address(address):
    """UZPOST punktlari uchun yetkazib berish haqi alohida to'lanadi."""
    if 'UZPOST' in (address or '').upper():
        return Decimal(str(getattr(settings, 'UZPOST_DELIVERY_FEE', 20000)))
    return Decimal('0')
