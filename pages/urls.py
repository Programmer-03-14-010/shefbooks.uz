from django.urls import path

from pages.views import home_page_view, ContactCreateView, about_page_view

app_name = "pages"

urlpatterns = [
    path('contact/', ContactCreateView.as_view(), name='contact'),
    path('about/', about_page_view, name='about'),
    path('', home_page_view, name='home'),
]
