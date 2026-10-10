from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from common.models import BaseModel


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
