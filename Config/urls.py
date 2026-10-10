from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve

handler404 = 'pages.views.custom_404'
handler500 = 'pages.views.custom_500'

urlpatterns = i18n_patterns(
    path('hahaha/', admin.site.urls),
    path('blogs/', include('blogs.urls', namespace='blogs')),
    path('products/', include('products.urls', namespace='products')),
    path('orders/', include('orders.urls', namespace='orders')),
    path('users/', include('users.urls', namespace='users')),
    path('', include('pages.urls', namespace='pages')),
    prefix_default_language=True,
)

# Media (kitob rasmlari) — DEBUG=False bo'lganda ham ishlashi uchun serve() to'g'ridan-to'g'ri ulangan
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]