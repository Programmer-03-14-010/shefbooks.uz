from decimal import Decimal

from django.conf import settings
from django.utils.http import url_has_allowed_host_and_scheme

from products.models import ProductModel, BundleOfferModel

FORMATS = {'paper': "Qog'oz", 'ebook': 'E-Book', 'audio': 'Audio'}
FORMAT_ICONS = {'paper': 'fa-book', 'ebook': 'fa-tablet', 'audio': 'fa-headphones'}


# ───────── Savat kalitlari: "12" (qog'oz) | "12:ebook" | "12:audio" ─────────
def make_key(pk, fmt='paper'):
    return str(pk) if fmt == 'paper' else f'{pk}:{fmt}'


def parse_key(key):
    s = str(key)
    pk, _, fmt = s.partition(':')
    fmt = fmt or 'paper'
    if not pk.isdigit() or fmt not in FORMATS:
        return None
    return int(pk), fmt


def clean_format(value):
    return value if value in FORMATS else 'paper'


def get_cart_entries(request):
    """[(key, pk, fmt, qty)] — sessiyadagi savat tartibi bilan."""
    quantities = request.session.get('cart_quantities', {})
    entries, seen = [], set()
    for raw in request.session.get('cart', []):
        parsed = parse_key(raw)
        if not parsed:
            continue
        pk, fmt = parsed
        key = make_key(pk, fmt)
        if key in seen:
            continue
        seen.add(key)
        try:
            qty = max(1, int(quantities.get(key, quantities.get(str(raw), 1))))
        except (TypeError, ValueError):
            qty = 1
        entries.append((key, pk, fmt, 1 if fmt != 'paper' else qty))
    return entries


def get_cart_quantities(request):
    """{key: qty}"""
    return {key: qty for key, _, _, qty in get_cart_entries(request)}


def build_cart_items(request):
    entries = get_cart_entries(request)
    if not entries:
        return [], Decimal('0')
    found = {p.pk: p for p in ProductModel.objects.filter(pk__in={e[1] for e in entries})}
    items, total = [], Decimal('0')
    for key, pk, fmt, qty in entries:
        product = found.get(pk)
        if not product:
            continue
        unit = product.price_for(fmt)
        subtotal = unit * qty
        total += subtotal
        items.append({
            'key': key, 'product': product, 'format': fmt, 'format_label': FORMATS[fmt],
            'format_icon': FORMAT_ICONS[fmt], 'quantity': qty, 'unit_price': unit, 'subtotal': subtotal,
            'available': product.format_available(fmt),
            'max_qty': product.quantity if fmt == 'paper' else 1,
        })
    return items, total


def get_products_in_cart(request):
    items, _ = build_cart_items(request)
    return [i['product'] for i in items]


# ───────── Chegirmalar ─────────
def bundle_discounts(items):
    """Faol to'plam aksiyalari: to'plamdagi barcha (qog'oz) kitoblar savatda bo'lsa chegirma beriladi."""
    paper = {i['product'].pk: i for i in items if i['format'] == 'paper'}
    result, missing = [], []
    if not paper:
        return result, missing
    for offer in BundleOfferModel.running():
        books = offer.book_list
        if not books:
            continue
        have = [b for b in books if b.pk in paper]
        if len(have) == len(books):
            sets = min(paper[b.pk]['quantity'] for b in books)
            base = sum((paper[b.pk]['unit_price'] for b in books), Decimal('0')) * sets
            amount = (base * offer.discount_percent / Decimal('100')).quantize(Decimal('1'))
            result.append({'offer': offer, 'amount': amount, 'sets': sets})
        elif have:
            missing.append({'offer': offer, 'missing': [b for b in books if b.pk not in paper]})
    return result, missing


def get_promo(request):
    from orders.models import PromoCodeModel
    code = request.session.get('promo_code')
    if not code:
        return None
    return PromoCodeModel.objects.filter(code=code).first()


def compute_cart(request):
    """Savatning to'liq hisob-kitobi: kitoblar, to'plam chegirmasi, promokod, jami."""
    items, subtotal = build_cart_items(request)
    bundles, bundle_missing = bundle_discounts(items)
    bundle_total = sum((b['amount'] for b in bundles), Decimal('0'))
    after_bundle = subtotal - bundle_total

    promo, promo_discount, promo_error = None, Decimal('0'), None
    if items:
        promo = get_promo(request)
        if request.session.get('promo_code') and promo is None:
            request.session.pop('promo_code', None)
        if promo:
            promo_error = promo.validate_for(after_bundle, request.user)
            if promo_error:
                request.session.pop('promo_code', None)
                promo = None
            else:
                promo_discount = promo.discount_for(after_bundle)

    total = after_bundle - promo_discount
    return {
        'items': items, 'subtotal': subtotal,
        'bundles': bundles, 'bundle_missing': bundle_missing, 'bundle_discount': bundle_total,
        'promo': promo, 'promo_discount': promo_discount, 'promo_error': promo_error,
        'discount': bundle_total + promo_discount, 'total': max(total, Decimal('0')),
        'has_paper': any(i['format'] == 'paper' for i in items),
        'has_digital': any(i['format'] != 'paper' for i in items),
        'count': sum(i['quantity'] for i in items),
    }


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
