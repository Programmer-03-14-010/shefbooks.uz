from django.urls import path

from orders.views import (
    add_or_remove_cart, MyOrdersListView, WishlistListView, add_or_remove_wishlist,
    CartListView, CheckoutTemplateView, increase_quantity, decrease_quantity,
    PaymentView, OrderSuccessView, mini_cart,
)

app_name = "orders"

urlpatterns = [
    path("add-or-remove-cart/<int:pk>/", add_or_remove_cart, name="add-or-remove-cart"),
    path("my-orders/", MyOrdersListView.as_view(), name="my-orders"),
    path("add-or-remove-wishlist/<int:pk>/", add_or_remove_wishlist, name="add-or-remove-wishlist"),
    path("cart/", CartListView.as_view(), name="cart"),
    path("cart/mini/", mini_cart, name="mini-cart"),
    path("wishlist/", WishlistListView.as_view(), name="wishlist"),
    path("checkout/", CheckoutTemplateView.as_view(), name="checkout"),
    path("increase-quantity/<int:pk>/", increase_quantity, name="increase-quantity"),
    path("decrease-quantity/<int:pk>/", decrease_quantity, name="decrease-quantity"),
    path("payment/<int:pk>/", PaymentView.as_view(), name="payment"),
    path("success/<int:pk>/", OrderSuccessView.as_view(), name="success"),
]
