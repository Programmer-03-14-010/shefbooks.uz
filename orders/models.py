from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from products.models import ProductModel

UserModel = get_user_model()


class OrderModel(models.Model):
    class OrderStatus(models.TextChoices):
        PENDING = "PENDING", "Kutilmoqda"
        ACCEPTED = "ACCEPTED", "Qabul qilindi"
        DELIVERING = "DELIVERING", "Yetkazilmoqda"
        DELIVERED = "DELIVERED", "Yetkazildi"
        CANCELED = "CANCELED", "Bekor qilindi"

    user = models.ForeignKey(
        UserModel,
        on_delete=models.PROTECT,
        related_name="orders",
        null=True,
        blank=True
    )

    phone_number = models.CharField(max_length=13)
    email = models.EmailField(blank=True)
    full_name = models.CharField(max_length=128)
    address = models.CharField(max_length=255)

    total_products = models.PositiveSmallIntegerField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Mahsulot to'lov cheki
    payment_receipt = models.ImageField(
        upload_to='payments/',
        null=True,
        blank=True
    )

    # ✅ YANGI: Pochta to'lov cheki (faqat UZPOST uchun)
    post_receipt = models.ImageField(
        upload_to='post_payments/',
        null=True,
        blank=True
    )

    is_paid = models.BooleanField(default=False)

    status = models.CharField(
        max_length=128,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Buyurtma'
        verbose_name_plural = 'Buyurtmalar'

    def __str__(self):
        return f"Order #{self.id}"

    @property
    def is_uzpost(self):
        return 'UZPOST' in (self.address or '').upper()

    @property
    def delivery_fee(self):
        from orders.utils import delivery_fee_for_address
        return delivery_fee_for_address(self.address)

    @property
    def total_with_delivery(self):
        return self.total_amount + self.delivery_fee

    @property
    def awaiting_receipt(self):
        return not self.payment_receipt and self.status != self.OrderStatus.CANCELED


class OrderItemModel(models.Model):
    order = models.ForeignKey(OrderModel, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        ProductModel, on_delete=models.SET_NULL,
        related_name="orders", null=True, blank=True
    )
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    product_title = models.CharField(max_length=255)
    product_quantity = models.PositiveSmallIntegerField()

    def __str__(self):
        return f"{self.product_title} × {self.product_quantity}"

    class Meta:
        verbose_name = "Buyurtma Mahsuloti"
        verbose_name_plural = "Buyurtma Mahsulotlari"


class Wishlist(models.Model):
    user = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name='wishlists',
        null=True,
        blank=True
    )
    product = models.ForeignKey(
        'products.ProductModel',
        on_delete=models.CASCADE,
        related_name='wishlisted_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-created_at']
        verbose_name = 'Wishlist'
        verbose_name_plural = 'Wishlists'

    def __str__(self):
        return f"{self.user} — {self.product}"