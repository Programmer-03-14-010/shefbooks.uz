from django.contrib import messages
from django.db.models import Count
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView

from blogs.models import BlogModel
from pages.forms import ContactForm
from products.models import ProductModel, ProductCategoryModel


def home_page_view(request):
    available = ProductModel.objects.filter(in_stock=True, quantity__gt=0)

    featured = list(available.filter(is_featured=True)[:8])
    featured = featured[:len(featured) - len(featured) % 4] or featured[:4]
    new_arrivals = list(available.order_by('-created_at')[:8])
    bestsellers = list(
        available.annotate(sold=Count('orders', distinct=True)).order_by('-sold', '-created_at')[:8]
    )
    discounted = list(available.filter(old_price__isnull=False).order_by('-created_at')[:8])
    discounted = [p for p in discounted if p.discount_percent > 0][:4]

    categories = list(
        ProductCategoryModel.objects.filter(parent__isnull=True)
        .annotate(n=Count('products', distinct=True))
        .order_by('-n')[:6]
    )
    hero_books = (featured or new_arrivals)[:3]

    return render(request, 'home.html', {
        'featured': featured or new_arrivals[:4],
        'new_arrivals': new_arrivals,
        'bestsellers': bestsellers,
        'discounted': discounted,
        'categories': categories,
        'hero_books': hero_books,
        'latest_blogs': BlogModel.objects.order_by('-created_at')[:3],
        'books_total': ProductModel.objects.count(),
    })


class ContactCreateView(CreateView):
    template_name = 'pages/contact.html'
    form_class = ContactForm

    def get_success_url(self):
        return reverse_lazy('pages:contact')

    def form_valid(self, form):
        messages.success(self.request, _("Xabaringiz yuborildi! Tez orada javob beramiz."))
        return super().form_valid(form)


def about_page_view(request):
    return render(request, 'pages/about-us.html', {
        'books_total': ProductModel.objects.count(),
    })


def custom_404(request, exception=None):
    return render(request, 'pages/404.html', status=404)


def custom_500(request):
    return render(request, 'pages/404.html', status=500)
