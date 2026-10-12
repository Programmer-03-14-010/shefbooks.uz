from django.urls import path

from products.views import ProductListView, ProductDetailView, add_review, delete_review, quick_view

app_name = 'products'

urlpatterns = [
    path('<int:pk>/', ProductDetailView.as_view(), name='detail'),
    path('<int:pk>/review/', add_review, name='add-review'),
    path('<int:pk>/review/<int:comment_id>/delete/', delete_review, name='delete-review'),
    path('<int:pk>/quick/', quick_view, name='quick'),
    path('', ProductListView.as_view(), name='list')
]
