from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Avg, Min, Max
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView

from products.models import ProductModel, ProductCategoryModel, ProductCommentModel, BundleOfferModel

SORT_OPTIONS = [
    ('new', 'Yangi qo\'shilganlar'),
    ('popular', 'Ommabop'),
    ('price', 'Arzonroq'),
    ('-price', 'Qimmatroq'),
    ('title', 'Nomi bo\'yicha (A–Z)'),
    ('discount', 'Chegirmadagilar'),
]


def _to_decimal(value):
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError):
        return None


class ProductListView(ListView):
    template_name = 'shop/product-list.html'
    model = ProductModel
    context_object_name = "products"
    paginate_by = 12

    def get_queryset(self):
        qs = ProductModel.objects.all().prefetch_related('categories')
        g = self.request.GET

        cat = g.get('cat')
        if cat and cat.isdigit():
            # Asosiy turkum tanlansa — uning ichki turkumlari ham kiradi
            qs = qs.filter(
                Q(categories=cat) | Q(categories__parent=cat)
            ).distinct()

        q = (g.get('q') or '').strip()
        if q:
            qs = qs.filter(
                Q(title__icontains=q) | Q(author__icontains=q) |
                Q(publisher__icontains=q) | Q(short_description__icontains=q)
            )

        pmin, pmax = _to_decimal(g.get('price_min')), _to_decimal(g.get('price_max'))
        if pmin is not None:
            qs = qs.filter(price__gte=pmin)
        if pmax is not None:
            qs = qs.filter(price__lte=pmax)

        if g.get('available') == '1':
            qs = qs.filter(in_stock=True, quantity__gt=0)

        lang = g.get('lang')
        if lang in dict(ProductModel.Language.choices):
            qs = qs.filter(language=lang)

        sort = g.get('sort', 'new')
        if sort == 'popular':
            qs = qs.annotate(sold=Count('orders', distinct=True)).order_by('-sold', '-created_at')
        elif sort in ('price', '-price', 'title'):
            qs = qs.order_by(sort)
        elif sort == 'discount':
            qs = qs.filter(old_price__isnull=False).order_by('-old_price', '-created_at')
        else:
            qs = qs.order_by('-created_at')
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        g = self.request.GET
        parents = ProductCategoryModel.objects.filter(parent__isnull=True).prefetch_related('children')
        counts = dict(
            ProductCategoryModel.objects.annotate(n=Count('products')).values_list('pk', 'n')
        )
        for parent in parents:
            parent.product_count = counts.get(parent.pk, 0) + sum(
                counts.get(ch.pk, 0) for ch in parent.children.all()
            )
            for child in parent.children.all():
                child.product_count = counts.get(child.pk, 0)

        bounds = ProductModel.objects.aggregate(lo=Min('price'), hi=Max('price'))
        active_cat = None
        if g.get('cat', '').isdigit():
            active_cat = ProductCategoryModel.objects.filter(pk=g['cat']).first()

        params = g.copy()
        params.pop('page', None)

        context.update({
            'categories': parents,
            'active_cat': active_cat,
            'sort_options': SORT_OPTIONS,
            'current_sort': g.get('sort', 'new'),
            'total_count': context['paginator'].count if context.get('paginator') else 0,
            'price_bounds': bounds,
            'query': (g.get('q') or '').strip(),
            'languages': ProductModel.Language.choices,
            'querystring': params.urlencode(),
            'has_filters': any(g.get(k) for k in ('cat', 'q', 'price_min', 'price_max', 'available', 'lang')),
        })
        return context


class ProductDetailView(DetailView):
    template_name = 'shop/product-detail.html'
    model = ProductModel
    context_object_name = "product"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object

        gallery = [product.image1.url]
        if product.image2:
            gallery.append(product.image2.url)
        gallery += [img.image.url for img in product.images.all()]
        # dublikatlarni olib tashlash
        seen, uniq = set(), []
        for url in gallery:
            if url not in seen:
                seen.add(url)
                uniq.append(url)

        related = (
            ProductModel.objects.filter(categories__in=product.categories.all())
            .exclude(pk=product.pk).distinct().order_by('-created_at')[:4]
        )
        if related.count() < 4:
            extra = ProductModel.objects.exclude(
                pk__in=[product.pk] + [r.pk for r in related]
            ).order_by('-created_at')[:4 - related.count()]
            related = list(related) + list(extra)

        reviews = product.comments.select_related('user')
        rating_stats = reviews.aggregate(avg=Avg('rating'), n=Count('id'))
        distribution = {i: reviews.filter(rating=i).count() for i in range(5, 0, -1)}

        owned = []
        if self.request.user.is_authenticated:
            from orders.models import OrderItemModel
            owned = list(OrderItemModel.objects.filter(
                order__user=self.request.user, order__is_paid=True, product=product, format__in=['ebook', 'audio']
            ).exclude(order__status='CANCELED'))
        context.update({
            'offer': BundleOfferModel.running().filter(products=product).first(),
            'owned_items': owned,
            'gallery': uniq,
            'related_products': related,
            'reviews': reviews[:20],
            'rating_avg': round(rating_stats['avg'], 1) if rating_stats['avg'] else 0,
            'rating_count': rating_stats['n'],
            'rating_distribution': distribution,
            'cart_qty': int(self.request.session.get('cart_quantities', {}).get(str(product.pk), 0))
            if product.pk in [int(i) for i in self.request.session.get('cart', [])] else 0,
        })
        return context


MAX_COMMENTS_PER_PRODUCT = 5


@login_required
@require_POST
def add_review(request, pk):
    product = get_object_or_404(ProductModel, pk=pk)
    comment = (request.POST.get('comment') or '').strip()
    try:
        rating = int(request.POST.get('rating', 5))
    except ValueError:
        rating = 5
    rating = min(5, max(1, rating))

    if len(comment) < 3:
        messages.error(request, "Fikr juda qisqa. Kamida bir necha so'z yozing.")
    elif ProductCommentModel.objects.filter(user=request.user, product=product).count() >= MAX_COMMENTS_PER_PRODUCT:
        messages.warning(request, f"Bitta kitobga {MAX_COMMENTS_PER_PRODUCT} tadan ortiq fikr yozib bo'lmaydi.")
    elif ProductCommentModel.objects.filter(user=request.user, product=product, comment=comment[:500]).exists():
        messages.info(request, "Bu fikr allaqachon yuborilgan.")
    else:
        ProductCommentModel.objects.create(user=request.user, product=product, comment=comment[:500], rating=rating)
        messages.success(request, "Fikringiz uchun rahmat!")
    return redirect(product.get_absolute_url() + '#reviews')


@login_required
@require_POST
def delete_review(request, pk, comment_id):
    comment = get_object_or_404(ProductCommentModel, pk=comment_id, product_id=pk)
    if comment.user_id == request.user.pk or request.user.is_staff:
        comment.delete()
        messages.success(request, "Fikr o'chirildi.")
    return redirect(comment.product.get_absolute_url() + '#reviews')


def quick_view(request, pk):
    """Kitobning «tez ko'rish» oynasi uchun HTML bo'lak (AJAX)."""
    product = get_object_or_404(ProductModel, pk=pk)
    reviews = product.comments.select_related('user')
    stats = reviews.aggregate(avg=Avg('rating'), n=Count('id'))
    return render(request, 'components/quick_view.html', {
        'product': product,
        'reviews': reviews[:3],
        'rating_avg': round(stats['avg'], 1) if stats['avg'] else 0,
        'rating_count': stats['n'],
        'offer': BundleOfferModel.running().filter(products=product).first(),
    })
