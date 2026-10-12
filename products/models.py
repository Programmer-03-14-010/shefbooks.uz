from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from decimal import Decimal, ROUND_HALF_UP

from django.db import models
from django.db.models import Avg
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from common.models import BaseModel
from common.storage import private_storage


UserModel = get_user_model()


class ProductCategoryModel(BaseModel):
    title = models.CharField(max_length=128, verbose_name=_('title'))
    parent = models.ForeignKey(
        'self', on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='children',
        verbose_name=_('parent')
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _('Mahsulot Turkumi')
        verbose_name_plural = _('Mahsulot Turkumlari')


class ProductTagModel(BaseModel):
    title = models.CharField(max_length=128, verbose_name=_('title'))

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _('Mahsulot tag')
        verbose_name_plural = _('Mahsulot taglari')


#class ProductSizeModel(BaseModel):
 #   title = models.CharField(max_length=128, verbose_name=_('title'))
#
#    def __str__(self):
 #       return self.title
#
  #  class Meta:
   #     verbose_name = _('product size')
    #    verbose_name_plural = _('product sizes')


#    class ProductManufactureModel(BaseModel):
#        logo = models.ImageField(upload_to='brands/', null=True, blank=True, verbose_name=_('title'))
#        name = models.CharField(max_length=128, verbose_name=_('title'))
#
#        def __str__(self):
#            return self.name
#
#        class Meta:
#            verbose_name = _('product manufacture')
#            verbose_name_plural = _('product manufactures')


#class ProductColorModel(BaseModel):
#    code = models.CharField(max_length=7, verbose_name=_('code'))
#    title = models.CharField(max_length=64, verbose_name=_('title'))

#    def __str__(self):
#        return self.title

 #   class Meta:
 #       verbose_name = _('product color')
  #      verbose_name_plural = _('product colors')


class ProductModel(BaseModel):
    class Language(models.TextChoices):
        UZ = 'uz', "O'zbekcha"
        RU = 'ru', 'Ruscha'
        EN = 'en', 'Inglizcha'
        OTHER = 'other', 'Boshqa'

    class CoverType(models.TextChoices):
        SOFT = 'soft', 'Yumshoq muqova'
        HARD = 'hard', 'Qattiq muqova'

    image1 = models.ImageField(
        upload_to='products',
        verbose_name=_('image1'),
        validators=[
            FileExtensionValidator(
                allowed_extensions=[
                    'png',
                    'jpg',
                    'jpeg',
                    'webp'
                ]
            )
        ]
    )
    image2 = models.ImageField(upload_to='products', verbose_name=_('image2'), blank=True)
    title = models.CharField(max_length=128, verbose_name=_('title'))
    short_description = models.TextField(verbose_name=_('short_description'))
    long_description = models.TextField(verbose_name=_('long_description'))
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('price'))
    old_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        verbose_name="Eski narx (chegirma uchun)",
        help_text="Chegirma ko'rsatish uchun: eski narxni kiriting, u joriy narxdan katta bo'lishi kerak."
    )
    in_stock = models.BooleanField(default=True, verbose_name=_('in_stock'))
    quantity = models.PositiveSmallIntegerField(verbose_name=_('quantity'))
    categories = models.ManyToManyField(ProductCategoryModel, verbose_name='categories', related_name='products')

    # ── Kitobga xos maydonlar ──
    author = models.CharField("Muallif", max_length=128, blank=True)
    publisher = models.CharField("Nashriyot", max_length=128, blank=True)
    language = models.CharField("Til", max_length=8, choices=Language.choices, default=Language.UZ)
    pages = models.PositiveSmallIntegerField("Sahifalar soni", null=True, blank=True)
    year = models.PositiveSmallIntegerField("Nashr yili", null=True, blank=True)
    cover_type = models.CharField("Muqova", max_length=8, choices=CoverType.choices, blank=True)
    isbn = models.CharField("ISBN", max_length=32, blank=True)
    is_featured = models.BooleanField("Bosh sahifada ko'rsatish", default=False)

    # ── Parcha va mundarija ──
    excerpt = models.TextField("Parcha (kitobdan lavha)", blank=True)
    table_of_contents = models.TextField("Mundarija", blank=True, help_text="Har bir bo'lim yangi qatordan yoziladi.")

    # ── Raqamli formatlar ──
    ebook_price = models.DecimalField("E-kitob narxi", max_digits=10, decimal_places=2, null=True, blank=True)
    ebook_file = models.FileField(
        "E-kitob fayli (PDF/EPUB)", upload_to='ebooks', storage=private_storage, blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'epub'])],
        help_text="Faqat sotib olgan mijozlarga ko'rinadi."
    )
    audio_price = models.DecimalField("Audio kitob narxi", max_digits=10, decimal_places=2, null=True, blank=True)
    audio_file = models.FileField(
        "Audio kitob (to'liq)", upload_to='audiobooks', storage=private_storage, blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['mp3', 'm4a', 'wav', 'ogg', 'aac'])],
        help_text="To'liq audio. Faqat sotib olgan mijozlar tinglay oladi."
    )
    audio_sample = models.FileField(
        "Audio parcha (hamma uchun, ixtiyoriy)", upload_to='audio_samples', blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['mp3', 'm4a', 'wav', 'ogg', 'aac'])],
        help_text="Qisqa namuna — kitob sahifasida hamma tinglashi mumkin."
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Kitob'
        verbose_name_plural = 'Kitoblar'

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.quantity == 0:
            self.in_stock = False
            update_fields = kwargs.get('update_fields')
            if update_fields is not None and 'in_stock' not in update_fields:
                kwargs['update_fields'] = list(update_fields) + ['in_stock']
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('products:detail', kwargs={'pk': self.pk})

    @property
    def cover(self):
        return self.image1

    @property
    def hover_image(self):
        return self.image2 if self.image2 else self.image1

    @property
    def has_ebook(self):
        return bool(self.ebook_price and self.ebook_file)

    @property
    def has_audio(self):
        return bool(self.audio_price and self.audio_file)

    @property
    def has_digital(self):
        return self.has_ebook or self.has_audio

    def format_available(self, fmt):
        if fmt == 'ebook':
            return self.has_ebook
        if fmt == 'audio':
            return self.has_audio
        return self.is_available

    def price_for(self, fmt='paper'):
        if fmt == 'ebook' and self.ebook_price:
            return self.ebook_price
        if fmt == 'audio' and self.audio_price:
            return self.audio_price
        return self.price

    @property
    def formats(self):
        """Kitob sahifasi va tez ko'rish oynasidagi format tugmalari."""
        items = [{'code': 'paper', 'label': "Qog'oz", 'icon': 'fa-book', 'price': self.price,
                  'old_price': self.old_price if self.discount_percent else None, 'available': self.is_available}]
        if self.has_ebook:
            items.append({'code': 'ebook', 'label': 'E-Book', 'icon': 'fa-tablet', 'price': self.ebook_price,
                          'old_price': None, 'available': True})
        if self.has_audio:
            items.append({'code': 'audio', 'label': 'Audio', 'icon': 'fa-headphones', 'price': self.audio_price,
                          'old_price': None, 'available': True})
        return items

    @property
    def contents_list(self):
        return [line.strip() for line in self.table_of_contents.splitlines() if line.strip()]

    @property
    def is_available(self):
        return self.in_stock and self.quantity > 0

    @property
    def discount_percent(self):
        if self.old_price and self.old_price > self.price:
            return int(round((self.old_price - self.price) / self.old_price * 100))
        return 0

    @property
    def avg_rating(self):
        value = self.comments.aggregate(avg=Avg('rating'))['avg']
        return round(value, 1) if value else 0

    @property
    def reviews_count(self):
        return self.comments.count()

    @property
    def is_new(self):
        from django.utils import timezone
        return (timezone.now() - self.created_at).days <= 30


class ProductCommentModel(BaseModel):
    comment = models.CharField(max_length=500, verbose_name=_('comment'))
    rating = models.PositiveSmallIntegerField(
        'Baho', default=5,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    user = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name='product_comments',
        verbose_name=_('user')
    )
    product = models.ForeignKey(
        ProductModel,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_('product')
    )

    def __str__(self):
        return self.user.username

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Mahsulotga fikr')
        verbose_name_plural = _('Mahsulotga fikrlar')


class ProductImageModel(models.Model):
    image = models.ImageField(upload_to='products', verbose_name=_('image'))
    product = models.ForeignKey(ProductModel, on_delete=models.CASCADE, related_name='images', verbose_name='product')


class BundleOfferModel(BaseModel):
    """Vaqt bilan cheklangan aksiya: bir nechta kitobdan iborat to'plam, to'plamga chegirma."""
    label = models.CharField("Yorliq", max_length=64, default="Hafta aksiyasi")
    title = models.CharField("Aksiya nomi", max_length=160, help_text='Masalan: "Muvaffaqiyatli Shaxs" 3 talik Kitob To\'plami')
    discount_percent = models.PositiveSmallIntegerField(
        "Chegirma (%)", validators=[MinValueValidator(1), MaxValueValidator(90)], default=35
    )
    products = models.ManyToManyField(ProductModel, related_name='bundle_offers', verbose_name="To'plamdagi kitoblar")
    starts_at = models.DateTimeField("Boshlanishi", default=timezone.now)
    ends_at = models.DateTimeField("Tugashi")
    is_active = models.BooleanField("Faol", default=True)

    class Meta:
        ordering = ['-ends_at']
        verbose_name = "Vaqtli aksiya (to'plam)"
        verbose_name_plural = "Vaqtli aksiyalar (to'plamlar)"

    def __str__(self):
        return self.title

    @classmethod
    def running(cls):
        now = timezone.now()
        return cls.objects.filter(is_active=True, starts_at__lte=now, ends_at__gt=now).prefetch_related('products')

    @property
    def is_running(self):
        now = timezone.now()
        return self.is_active and self.starts_at <= now < self.ends_at

    @property
    def book_list(self):
        return list(self.products.all())

    @property
    def books_line(self):
        return ' + '.join(p.title for p in self.book_list)

    @property
    def original_total(self):
        return sum((p.price for p in self.book_list), Decimal('0'))

    @property
    def saving(self):
        return (self.original_total * self.discount_percent / Decimal('100')).quantize(Decimal('1'), rounding=ROUND_HALF_UP)

    @property
    def bundle_price(self):
        return self.original_total - self.saving

    @property
    def in_stock(self):
        books = self.book_list
        return bool(books) and all(p.is_available for p in books)
