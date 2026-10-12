from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from products.models import ProductModel

UserModel = get_user_model()


class PromoCodeModel(models.Model):
    class DiscountType(models.TextChoices):
        PERCENT = 'percent', 'Foiz (%)'
        FIXED = 'fixed', "Aniq summa (so'm)"

    code = models.CharField("Promokod", max_length=32, unique=True, help_text="Masalan: SHEF15 (katta-kichik harf farqi yo'q)")
    description = models.CharField("Izoh (ichki)", max_length=160, blank=True)
    discount_type = models.CharField("Chegirma turi", max_length=8, choices=DiscountType.choices, default=DiscountType.PERCENT)
    value = models.DecimalField("Chegirma qiymati", max_digits=10, decimal_places=2, help_text="Foiz bo'lsa 15, summa bo'lsa 20000")
    max_discount = models.DecimalField("Maksimal chegirma (so'm)", max_digits=10, decimal_places=2, null=True, blank=True,
                                       help_text="Foizli promokod uchun yuqori chegara (ixtiyoriy)")
    min_order_amount = models.DecimalField("Minimal buyurtma summasi", max_digits=10, decimal_places=2, default=0)
    max_uses = models.PositiveIntegerField("Umumiy foydalanish limiti", null=True, blank=True, help_text="Bo'sh = cheksiz")
    used_count = models.PositiveIntegerField("Ishlatilgan", default=0)
    once_per_user = models.BooleanField("Bitta foydalanuvchi faqat 1 marta", default=True)
    valid_from = models.DateTimeField("Boshlanishi", null=True, blank=True)
    valid_to = models.DateTimeField("Tugashi", null=True, blank=True)
    is_active = models.BooleanField("Faol", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Promokod'
        verbose_name_plural = 'Promokodlar'

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        self.code = (self.code or '').strip().upper()
        super().save(*args, **kwargs)

    @property
    def label(self):
        if self.discount_type == self.DiscountType.PERCENT:
            return f"−{int(self.value)}%"
        return f"−{int(self.value):,}".replace(',', ' ') + " so'm"

    def validate_for(self, amount, user=None):
        """None — yaroqli, aks holda xato matni."""
        from django.utils import timezone
        now = timezone.now()
        if not self.is_active:
            return "Bu promokod hozir faol emas."
        if self.valid_from and now < self.valid_from:
            return "Bu promokod hali boshlanmagan."
        if self.valid_to and now > self.valid_to:
            return "Bu promokodning muddati tugagan."
        if self.max_uses is not None and self.used_count >= self.max_uses:
            return "Bu promokodning limiti tugagan."
        if amount < self.min_order_amount:
            return f"Bu promokod uchun buyurtma kamida {int(self.min_order_amount):,} so'm bo'lishi kerak.".replace(',', ' ')
        if self.once_per_user and user is not None and getattr(user, 'is_authenticated', False):
            used = OrderModel.objects.filter(user=user, promo_code=self.code).exclude(status='CANCELED').exists()
            if used:
                return "Siz bu promokoddan avval foydalangansiz."
        return None

    def discount_for(self, amount):
        from decimal import Decimal, ROUND_HALF_UP
        amount = Decimal(amount)
        if self.discount_type == self.DiscountType.PERCENT:
            d = amount * self.value / Decimal('100')
            if self.max_discount:
                d = min(d, self.max_discount)
        else:
            d = self.value
        d = min(d, amount)
        return d.quantize(Decimal('1'), rounding=ROUND_HALF_UP)


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

    promo_code = models.CharField("Promokod", max_length=32, blank=True)
    discount_amount = models.DecimalField("Chegirma summasi", max_digits=10, decimal_places=2, default=0)

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
    def subtotal_before_discount(self):
        return self.total_amount + self.discount_amount

    @property
    def has_physical(self):
        return any(i.format == 'paper' for i in self.items.all())

    @property
    def has_digital(self):
        return any(i.format != 'paper' for i in self.items.all())

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
    format = models.CharField("Format", max_length=8, default='paper',
                              choices=[('paper', "Qog'oz"), ('ebook', 'E-Book'), ('audio', 'Audio')])

    @property
    def format_label(self):
        return dict(self._meta.get_field('format').choices).get(self.format, self.format)

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