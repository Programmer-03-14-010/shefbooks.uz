from django import template
from django.utils.html import format_html

register = template.Library()


@register.simple_tag
def get_lang_url(request, lang):
    url = request.path
    url = url.split('/')
    url[1] = lang
    res = '/'.join(url)
    return res


@register.simple_tag
def get_lang_flag(lang):
    if lang == "uz":
        return "🇺🇿"
    return "🇺🇸"


@register.simple_tag
def qs_update(request, **kwargs):
    """Joriy so'rov parametrlarini saqlagan holda yangilari bilan URL query yaratadi (page har doim o'chadi)."""
    params = request.GET.copy()
    params.pop('page', None)
    for key, value in kwargs.items():
        if value in (None, ''):
            params.pop(key, None)
        else:
            params[key] = value
    qs = params.urlencode()
    return f'?{qs}' if qs else '?'


@register.simple_tag
def qs_page(request, page):
    params = request.GET.copy()
    params['page'] = page
    return f'?{params.urlencode()}'


@register.filter
def money(value):
    """12500.00 -> '12 500'"""
    try:
        return f"{int(round(float(value))):,}".replace(',', ' ')
    except (TypeError, ValueError):
        return value


@register.filter
def initial(value):
    value = (value or '?').strip()
    return value[:1].upper() if value else '?'


@register.filter
def range_to(value):
    try:
        return range(1, int(value) + 1)
    except (TypeError, ValueError):
        return range(0)


@register.simple_tag
def stars(rating, size=''):
    """★★★★☆ — 0–5 oralig'idagi baho uchun yulduzchalar (yarim yulduz bilan)."""
    try:
        r = float(rating)
    except (TypeError, ValueError):
        r = 0
    html = []
    for i in range(1, 6):
        if r >= i - 0.25:
            html.append('<i class="fa fa-star"></i>')
        elif r >= i - 0.75:
            html.append('<i class="fa fa-star-half-o"></i>')
        else:
            html.append('<i class="fa fa-star off"></i>')
    return format_html('<span class="stars" aria-label="{} / 5">{}</span>', r, format_html(''.join(html)))
