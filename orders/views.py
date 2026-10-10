from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import ListView, FormView, DetailView

from orders.forms import CheckoutForm, PaymentForm
from orders.models import OrderModel, OrderItemModel, Wishlist
from orders.utils import (
    build_cart_items, get_cart_quantities, safe_next_url,
)
from products.models import ProductModel


def _is_ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'


def _cart_payload(request, **extra):
    items, total = build_cart_items(request)
    data = {
        'ok': True,
        'cart_count': sum(i['quantity'] for i in items),
        'cart_total': float(total),
        'wish_count': _wish_count(request),
    }
    data.update(extra)
    return JsonResponse(data)


def _wish_ids(request):
    ids = set(int(i) for i in request.session.get('wishlist', []))
    if request.user.is_authenticated:
        ids |= set(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))
    return ids


def _wish_count(request):
    return len(_wish_ids(request))


# ─────────────────────────────────────────
# SAVAT: qo'shish / olib tashlash
# ─────────────────────────────────────────
@require_POST
def add_or_remove_cart(request, pk):
    product = get_object_or_404(ProductModel, pk=pk)
    cart = [int(i) for i in request.session.get('cart', [])]
    quantities = request.session.get('cart_quantities', {})
    in_cart = False
    message = None

    if pk in cart:
        cart.remove(pk)
        quantities.pop(str(pk), None)
        message = "Savatdan olib tashlandi"
    elif not product.is_available:
        message = "Afsuski, bu kitob hozir sotuvda yo'q"
        if _is_ajax(request):
            return JsonResponse({'ok': False, 'message': message}, status=409)
        messages.warning(request, message)
        return redirect(safe_next_url(request, product.get_absolute_url()))
    else:
        cart.append(pk)
        quantities[str(pk)] = 1
        in_cart = True
        message = "Savatga qo'shildi"

    request.session['cart'] = cart
    request.session['cart_quantities'] = quantities

    if _is_ajax(request):
        return _cart_payload(request, in_cart=in_cart, message=message)
    messages.success(request, message)
    return redirect(safe_next_url(request, reverse_lazy('products:list')))


def mini_cart(request):
    """Sarlavhadagi mini-savat HTML bo'lagi (AJAX yangilash uchun)."""
    return render(request, 'components/mini_cart.html')


# ─────────────────────────────────────────
# MIQDOR
# ─────────────────────────────────────────
@require_POST
def increase_quantity(request, pk):
    product = get_object_or_404(ProductModel, pk=pk)
    quantities = request.session.get('cart_quantities', {})
    current = int(quantities.get(str(pk), 1))
    if current >= product.quantity:
        msg = f"Kechirasiz, bu kitobdan faqat {product.quantity} ta mavjud!"
        if _is_ajax(request):
            return JsonResponse({'ok': False, 'message': msg}, status=409)
        messages.warning(request, msg)
        return redirect('orders:cart')
    quantities[str(pk)] = current + 1
    request.session['cart_quantities'] = quantities
    return redirect('orders:cart')


@require_POST
def decrease_quantity(request, pk):
    quantities = request.session.get('cart_quantities', {})
    current = int(quantities.get(str(pk), 1))
    if current > 1:
        quantities[str(pk)] = current - 1
    request.session['cart_quantities'] = quantities
    return redirect('orders:cart')


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
        # Sessiya va bazani sinxronlashtirish (login qilgandan keyin ham yo'qolmasligi uchun)
        self.request.session['wishlist'] = list(ids)
        if self.request.user.is_authenticated:
            existing = set(Wishlist.objects.filter(user=self.request.user).values_list('product_id', flat=True))
            valid = set(ProductModel.objects.filter(pk__in=ids - existing).values_list('pk', flat=True))
            Wishlist.objects.bulk_create(
                [Wishlist(user=self.request.user, product_id=i) for i in valid], ignore_conflicts=True
            )
        return ProductModel.objects.filter(pk__in=ids)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['wishlist_count'] = ctx['paginator'].count if ctx.get('paginator') else 0
        return ctx


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
        cart_items, total = build_cart_items(self.request)
        # Ombor qoldig'idan oshib ketgan miqdorni to'g'rilash
        quantities = self.request.session.get('cart_quantities', {})
        for entry in cart_items:
            p = entry['product']
            if entry['quantity'] > p.quantity > 0:
                quantities[str(p.pk)] = p.quantity
                messages.warning(self.request, f"«{p.title}» dan faqat {p.quantity} ta mavjud, miqdor yangilandi.")
        self.request.session['cart_quantities'] = quantities
        cart_items, total = build_cart_items(self.request)
        context['cart_items'] = cart_items
        context['cart_total'] = total
        context['has_unavailable'] = any(not i['product'].is_available for i in cart_items)
        return context


# ─────────────────────────────────────────
# CHECKOUT
# ─────────────────────────────────────────
class CheckoutTemplateView(LoginRequiredMixin, FormView):
    template_name = 'shop/product-checkout.html'
    form_class = CheckoutForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not get_cart_quantities(request):
            messages.info(request, "Savatingiz bo'sh. Avval kitob tanlang.")
            return redirect('products:list')
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        user = self.request.user
        initial = super().get_initial()
        if user.is_authenticated:
            initial['full_name'] = user.get_full_name()
            initial['email'] = user.email
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart_items, total = build_cart_items(self.request)
        context['cart_items'] = cart_items
        context['cart_total'] = total
        return context

    @transaction.atomic
    def form_valid(self, form):
        quantities = get_cart_quantities(self.request)
        products = list(
            ProductModel.objects.select_for_update().filter(pk__in=quantities.keys())
        )
        if not products:
            messages.info(self.request, "Savat bo'sh")
            return redirect("products:list")

        # Ombor qoldig'ini qayta tekshirish
        problems = []
        for product in products:
            qty = quantities[product.pk]
            if not product.in_stock or product.quantity < qty:
                problems.append(f"«{product.title}» — mavjud: {product.quantity} ta")
        if problems:
            messages.error(
                self.request,
                "Ba'zi kitoblar yetarli emas: " + "; ".join(problems) + ". Savatni yangilang."
            )
            return redirect('orders:cart')

        total = sum(p.price * quantities[p.pk] for p in products)
        total_qty = sum(quantities[p.pk] for p in products)

        order = OrderModel.objects.create(
            user=self.request.user,
            full_name=form.cleaned_data['full_name'],
            email=form.cleaned_data.get('email', ''),
            phone_number=form.cleaned_data['phone_number'],
            address=form.cleaned_data['address'],
            total_amount=total,
            total_products=total_qty,
        )

        for product in products:
            qty = quantities[product.pk]
            OrderItemModel.objects.create(
                order=order,
                product=product,
                product_title=product.title,
                product_price=product.price,
                product_quantity=qty,
            )
            product.quantity = max(0, product.quantity - qty)
            if product.quantity == 0:
                product.in_stock = False
            product.save(update_fields=['quantity', 'in_stock'])

        self.request.session['cart'] = []
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
        from django.conf import settings
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
        # is_paid ni o'zgartirmaymiz — admin chekni ko'rib, o'zi belgilaydi
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
