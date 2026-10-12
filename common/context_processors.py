from django.conf import settings

from orders.models import Wishlist
from orders.utils import compute_cart
from products.models import ProductCategoryModel


def shop(request):
    """Sarlavha va footer uchun umumiy ma'lumotlar (savat, xohishlar, aloqa, menyu turkumlari)."""
    session = getattr(request, 'session', None)
    cart = {'items': [], 'total': 0, 'count': 0}
    wish_ids = set()
    if session is not None:
        cart = compute_cart(request)
        wish_ids = {int(i) for i in session.get('wishlist', [])}
        user = getattr(request, 'user', None)
        if user is not None and user.is_authenticated:
            wish_ids |= set(Wishlist.objects.filter(user=user).values_list('product_id', flat=True))

    return {
        'cart_header_items': cart['items'],
        # savatdagi (qog'oz) kitoblar va (kitob, format) kalitlari
        'cart_ids': {i['product'].pk for i in cart['items'] if i['format'] == 'paper'},
        'cart_keys': {i['key'] for i in cart['items']},
        'cart_count': cart['count'],
        'cart_lines': len(cart['items']),
        'cart_total_header': cart['total'],
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
