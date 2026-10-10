from django.urls import path
from .views import BlogListView, blog_detail

app_name = 'blogs'

urlpatterns = [
    path('', BlogListView.as_view(), name='list'),
    path('<int:pk>/', blog_detail, name='blog_detail'),  # slug o'rniga id
]