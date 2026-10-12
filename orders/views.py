from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import JsonResponse, Http404
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import ListView, FormView, DetailView

from common.files import ranged_file_response
from orders.forms import CheckoutForm, PaymentForm
from orders.models import OrderModel, OrderItemModel, Wishlist, PromoCodeModel
from orders.utils import (
    compute_cart, get_cart_entries, make_key, clean_format, safe_next_url,
)
from products.models import ProductModel, BundleOfferModel


def _is_ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'


def _wish_ids(request):
    ids = set(int(i) for i in request.session.get('wishlist', []))
    if request.user.is_authenticated:
        ids |= set(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))
    return ids


def _cart_payload(request, **extra):
    cart = compute_cart(request)
    data = {
        'ok': True,
        'cart_count': cart['count'],
        'cart_total': float(cart['total']),
        'wish_count': len(_wish_ids(request)),
    }
    data.update(extra)
    return JsonResponse(data)


def _save_cart(request, keys, quantities):
    request.session['cart'] = keys
    request.session['cart_quantities'] = quantities


# ─────────────────────────────────────────
# SAVAT: qo'shish / olib tashlash (format bilan)
# ─────────────────────────────────────────
@require_POST
def add_or_remove_cart(request, pk):
    product = get_object_or_404(ProductModel, pk=pk)
    fmt = clean_format(request.POST.get('fmt', 'paper'))
    key = make_key(pk, fmt)
    keys = [str(k) for k in request.session.get('cart', [])]
    quantities = dict(request.session.get('cart_quantities', {}))
    in_cart = False

    if key in keys:
        keys.remove(key)
        quantities.pop(key, None)
        message = "Savatdan olib tashlandi"
    elif not product.format_available(fmt):
        message = "Afsuski, bu format hozir sotuvda yo'q"
        if _is_ajax(request):
            return JsonResponse({'ok': False, 'message': message}, status=409)
        messages.warning(request, message)
        return redirect(safe_next_url(request, product.get_absolute_url()))
    else:
        keys.append(key)
        quantities[key] = 1
        in_cart = True
        message = "Savatga qo'shildi"

    _save_cart(request, keys, quantities)
    if _is_ajax(request):
        return _cart_payload(request, in_cart=in_cart, message=message, fmt=fmt)
    messages.success(request, message)
    return redirect(safe_next_url(request, reverse_lazy('products:list')))


@require_POST
def add_bundle(request, pk):
    """Aksiya to'plamidagi barcha kitoblarni savatga qo'shadi (chegirma savatda avtomatik qo'llanadi)."""
    offer = get_object_or_404(BundleOfferModel.running(), pk=pk)
    books = offer.book_list
    unavailable = [b.title for b in books if not b.is_available]
    if unavailable:
        message = "To'plamdagi ba'zi kitoblar tugagan: " + ", ".join(unavailable)
        if _is_ajax(request):
            return JsonResponse({'ok': False, 'message': message}, status=409)
        messages.warning(request, message)
        return redirect(safe_next_url(request, reverse_lazy('pages:home')))

    keys = [str(k) for k in request.session.get('cart', [])]
    quantities = dict(request.session.get('cart_quantities', {}))
    for b in books:
        key = make_key(b.pk, 'paper')
        if key not in keys:
            keys.append(key)
            quantities[key] = 1
    _save_cart(request, keys, quantities)
    message = f"«{offer.label}» to'plami savatga qo'shildi — chegirma −{offer.discount_percent}%"
    if _is_ajax(request):
        return _cart_payload(request, message=message, redirect=str(reverse_lazy('orders:cart')))
    messages.success(request, message)
    return redirect('orders:cart')


# ─────────────────────────────────────────
# PROMOKOD
# ─────────────────────────────────────────
@require_POST
def apply_promo(request):
    code = (request.POST.get('code') or '').strip().upper()
    cart = compute_cart(request)
    back = redirect(safe_next_url(request, reverse_lazy('orders:cart')))
    if not cart['items']:
        messages.warning(request, "Avval savatga kitob qo'shing.")
        return back
    if not code:
        messages.warning(request, "Promokodni kiriting.")
        return back
    promo = PromoCodeModel.objects.filter(code=code).first()
    if not promo:
        messages.error(request, "Bunday promokod topilmadi.")
        return back
    after_bundle = cart['subtotal'] - cart['bundle_discount']
    error = promo.validate_for(after_bundle, request.user)
    if error:
        messages.error(request, error)
        return back
    request.session['promo_code'] = promo.code
    messages.success(request, f"Promokod qo'llandi! Chegirma: {promo.discount_for(after_bundle):,.0f} so'm".replace(',', ' '))
    return back


@require_POST
def remove_promo(request):
    request.session.pop('promo_code', None)
    messages.info(request, "Promokod olib tashlandi.")
    return redirect(safe_next_url(request, reverse_lazy('orders:cart')))


# ─────────────────────────────────────────
# MIQDOR (faqat qog'oz kitoblar)
# ─────────────────────────────────────────
@require_POST
def increase_quantity(request, pk):
    product = get_object_or_404(ProductModel, pk=pk)
    key = make_key(pk, 'paper')
    quantities = dict(request.session.get('cart_quantities', {}))
    current = int(quantities.get(key, 1))
    if current >= product.quantity:
        messages.warning(request, f"Kechirasiz, bu kitobdan faqat {product.quantity} ta mavjud!")
        return redirect('orders:cart')
    quantities[key] = current + 1
    request.session['cart_quantities'] = quantities
    return redirect('orders:cart')


@require_POST
def decrease_quantity(request, pk):
    key = make_key(pk, 'paper')
    quantities = dict(request.session.get('cart_quantities', {}))
    current = int(quantities.get(key, 1))
    if current > 1:
        quantities[key] = current - 1
    request.session['cart_quantities'] = quantities
    return redirect('orders:cart')


def mini_cart(request):
    """Sarlavhadagi mini-savat HTML bo'lagi (AJAX yangilash uchun)."""
    return render(request, 'components/mini_cart.html')


# ─────────────────────────────────────────
# WISHLIST
# ─────────────────────────────────────────
@require_POST
def add_or_remove_wishlist(request, pk):
    product = get_object_or_404(ProductModel, pk=pk)
    wishlist = [int(i) for i in request.session.get('wishlist', [])]

    if pk in _wish_ids(request):
        wishlist = [i for i in wishlist if i != pk]
        if request.user.is_authenticated:
            Wishlist.objects.filter(user=request.user, product_id=pk).delete()
        liked, message = False, "Xohishlardan olib tashlandi"
    else:
        wishlist.append(pk)
        if request.user.is_authenticated:
            Wishlist.objects.get_or_create(user=request.user, product=product)
        liked, message = True, "Xohishlarga qo'shildi"

    request.session['wishlist'] = wishlist
    if _is_ajax(request):
        return _cart_payload(request, liked=liked, message=message)
    messages.success(request, message)
    return redirect(safe_next_url(request, reverse_lazy('orders:wishlist')))


class WishlistListView(ListView):
    template_name = 'shop/wishlist.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        ids = _wish_ids(self.request)
        self.request.session['wishlist'] = list(ids)
        if self.request.user.is_authenticated:
            existing = set(Wishlist.objects.filter(user=self.request.user).values_list('product_id', flat=True))
            valid = set(ProductModel.objects.filter(pk__in=ids - existing).values_list('pk', flat=True))
            Wishlist.objects.bulk_create(
                [Wishlist(user=self.request.user, product_id=i) for i in valid], ignore_conflicts=True
            )
        return ProductModel.objects.filter(pk__in=ids)


# ─────────────────────────────────────────
# SAVAT KO'RINISHI
# ─────────────────────────────────────────
class CartListView(ListView):
    template_name = 'shop/product-cart.html'
    context_object_name = "items"

    def get_queryset(self):
        return ProductModel.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ombor qoldig'idan oshib ketgan miqdorni to'g'rilash
        quantities = dict(self.request.session.get('cart_quantities', {}))
        changed = False
        for item in compute_cart(self.request)['items']:
            if item['format'] == 'paper' and item['quantity'] > item['product'].quantity > 0:
                quantities[item['key']] = item['product'].quantity
                changed = True
                messages.warning(self.request, f"«{item['product'].title}» dan faqat {item['product'].quantity} ta mavjud, miqdor yangilandi.")
        if changed:
            self.request.session['cart_quantities'] = quantities

        cart = compute_cart(self.request)
        if cart['promo_error']:
            messages.warning(self.request, cart['promo_error'])
        context.update({
            'cart': cart,
            'cart_items': cart['items'],
            'cart_total': cart['total'],
            'has_unavailable': any(not i['available'] for i in cart['items']),
        })
        return context


# ─────────────────────────────────────────
# CHECKOUT
# ─────────────────────────────────────────
class CheckoutTemplateView(LoginRequiredMixin, FormView):
    template_name = 'shop/product-checkout.html'
    form_class = CheckoutForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not get_cart_entries(request):
            messages.info(request, "Savatingiz bo'sh. Avval kitob tanlang.")
            return redirect('products:list')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['require_address'] = compute_cart(self.request)['has_paper']
        return kwargs

    def get_initial(self):
        user = self.request.user
        initial = super().get_initial()
        if user.is_authenticated:
            initial['full_name'] = user.get_full_name()
            initial['email'] = user.email
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = compute_cart(self.request)
        context.update({'cart': cart, 'cart_items': cart['items'], 'cart_total': cart['total']})
        return context

    @transaction.atomic
    def form_valid(self, form):
        cart = compute_cart(self.request)
        items = cart['items']
        if not items:
            messages.info(self.request, "Savat bo'sh")
            return redirect("products:list")

        # Qog'oz kitoblar: qulflab, ombor qoldig'ini qayta tekshirish
        paper_pks = [i['product'].pk for i in items if i['format'] == 'paper']
        locked = {p.pk: p for p in ProductModel.objects.select_for_update().filter(pk__in=paper_pks)}
        problems = []
        for i in items:
            if i['format'] == 'paper':
                p = locked[i['product'].pk]
                if not p.in_stock or p.quantity < i['quantity']:
                    problems.append(f"«{p.title}» — mavjud: {p.quantity} ta")
            elif not i['product'].format_available(i['format']):
                problems.append(f"«{i['product'].title}» ({i['format_label']}) hozir mavjud emas")
        if problems:
            messages.error(self.request, "Ba'zi kitoblar yetarli emas: " + "; ".join(problems) + ". Savatni yangilang.")
            return redirect('orders:cart')

        # Promokod: tranzaksiya ichida qayta tekshirish va hisoblash
        promo_code, promo_discount = '', Decimal('0')
        if cart['promo']:
            promo = PromoCodeModel.objects.select_for_update().get(pk=cart['promo'].pk)
            after_bundle = cart['subtotal'] - cart['bundle_discount']
            error = promo.validate_for(after_bundle, self.request.user)
            if error:
                self.request.session.pop('promo_code', None)
                messages.error(self.request, error)
                return redirect('orders:cart')
            promo_code, promo_discount = promo.code, promo.discount_for(after_bundle)
            promo.used_count += 1
            promo.save(update_fields=['used_count'])

        discount = cart['bundle_discount'] + promo_discount
        total = max(cart['subtotal'] - discount, Decimal('0'))

        order = OrderModel.objects.create(
            user=self.request.user,
            full_name=form.cleaned_data['full_name'],
            email=form.cleaned_data.get('email', ''),
            phone_number=form.cleaned_data['phone_number'],
            address=form.cleaned_data['address'],
            total_amount=total,
            total_products=cart['count'],
            promo_code=promo_code,
            discount_amount=discount,
        )

        for i in items:
            product = i['product']
            OrderItemModel.objects.create(
                order=order, product=product, product_title=product.title,
                product_price=i['unit_price'], product_quantity=i['quantity'], format=i['format'],
            )
            if i['format'] == 'paper':
                p = locked[product.pk]
                p.quantity = max(0, p.quantity - i['quantity'])
                if p.quantity == 0:
                    p.in_stock = False
                p.save(update_fields=['quantity', 'in_stock'])

        for k in ('cart', 'promo_code'):
            self.request.session.pop(k, None)
        self.request.session['cart_quantities'] = {}
        return redirect('orders:payment', pk=order.id)


# ─────────────────────────────────────────
# TO'LOV
# ─────────────────────────────────────────
class PaymentView(LoginRequiredMixin, FormView):
    template_name = "shop/product-cart-check.html"
    form_class = PaymentForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            qs = OrderModel.objects.all() if request.user.is_staff else OrderModel.objects.filter(user=request.user)
            self.order = get_object_or_404(qs, pk=self.kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['require_post_receipt'] = self.order.is_uzpost
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order'] = self.order
        context['delivery_type'] = 'uzpost' if self.order.is_uzpost else 'bts'
        context['total_with_delivery'] = self.order.total_with_delivery
        context['card_number'] = settings.PAYMENT_CARD_NUMBER
        context['card_holder'] = settings.PAYMENT_CARD_HOLDER
        return context

    def form_valid(self, form):
        self.order.payment_receipt = form.cleaned_data['payment_receipt']
        if form.cleaned_data.get('post_receipt'):
            self.order.post_receipt = form.cleaned_data['post_receipt']
        self.order.save()
        return redirect("orders:success", pk=self.order.pk)


class OrderSuccessView(LoginRequiredMixin, DetailView):
    template_name = 'shop/order-success.html'
    context_object_name = 'order'

    def get_queryset(self):
        qs = OrderModel.objects.prefetch_related('items__product')
        return qs if self.request.user.is_staff else qs.filter(user=self.request.user)


class MyOrdersListView(LoginRequiredMixin, ListView):
    template_name = 'shop/my-orders.html'
    context_object_name = 'orders'

    def get_queryset(self):
        return OrderModel.objects.filter(
            user=self.request.user
        ).prefetch_related('items__product').order_by('-created_at')


# ─────────────────────────────────────────
# KUTUBXONAM: sotib olingan e-kitob va audio kitoblar
# ─────────────────────────────────────────
class LibraryView(LoginRequiredMixin, ListView):
    template_name = 'shop/library.html'
    context_object_name = 'entries'

    def get_queryset(self):
        return (OrderItemModel.objects
                .filter(order__user=self.request.user, order__is_paid=True, format__in=['ebook', 'audio'])
                .exclude(order__status='CANCELED')
                .select_related('order', 'product').order_by('-order__created_at'))


def digital_file(request, pk):
    """Pullik faylni faqat to'lovi tasdiqlangan buyurtma egasi (yoki admin) ochadi."""
    if not request.user.is_authenticated:
        return redirect(f"{reverse_lazy('users:login')}?next={request.path}")
    item = get_object_or_404(OrderItemModel.objects.select_related('order', 'product'), pk=pk, format__in=['ebook', 'audio'])
    if not (request.user.is_staff or (item.order.user_id == request.user.pk and item.order.is_paid
                                       and item.order.status != 'CANCELED')):
        raise Http404
    product = item.product
    field = (product.ebook_file if item.format == 'ebook' else product.audio_file) if product else None
    if not field:
        raise Http404
    try:
        path = field.path
    except Exception:
        raise Http404
    import os
    if not os.path.exists(path):
        raise Http404
    ext = os.path.splitext(path)[1]
    return ranged_file_response(request, path, f"{product.title}{ext}", inline=(ext.lower() != '.epub'))
