from django.conf import settings

from orders.models import Wishlist
from orders.utils import build_cart_items
from products.models import ProductCategoryModel


def shop(request):
    """Sarlavha va footer uchun umumiy ma'lumotlar (savat, xohishlar, aloqa, menyu turkumlari)."""
    session = getattr(request, 'session', None)
    cart_items, cart_total = [], 0
    wish_ids = set()
    if session is not None:
        cart_items, cart_total = build_cart_items(request)
        wish_ids = {int(i) for i in session.get('wishlist', [])}
        user = getattr(request, 'user', None)
        if user is not None and user.is_authenticated:
            wish_ids |= set(Wishlist.objects.filter(user=user).values_list('product_id', flat=True))

    return {
        'cart_header_items': cart_items,
        'cart_ids': {i['product'].pk for i in cart_items},
        'cart_count': sum(i['quantity'] for i in cart_items),
        'cart_lines': len(cart_items),
        'cart_total_header': cart_total,
        'wish_ids': wish_ids,
        'wish_count': len(wish_ids),
        'nav_categories': ProductCategoryModel.objects.filter(parent__isnull=True)[:8],
        'SHOP': {
            'phone': settings.SHOP_PHONE,
            'phone_href': settings.SHOP_PHONE.replace(' ', ''),
            'email': settings.SHOP_EMAIL,
            'instagram': settings.SHOP_INSTAGRAM,
            'youtube': settings.SHOP_YOUTUBE,
            'telegram': settings.SHOP_TELEGRAM,
            'uzpost_fee': settings.UZPOST_DELIVERY_FEE,
        },
    }
