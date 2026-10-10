from django.urls import path

from products.views import ProductListView, ProductDetailView, add_review

app_name = 'products'

urlpatterns = [
    path('<int:pk>/', ProductDetailView.as_view(), name='detail'),
    path('<int:pk>/review/', add_review, name='add-review'),
    path('', ProductListView.as_view(), name='list')
]
