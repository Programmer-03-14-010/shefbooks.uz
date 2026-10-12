from django.contrib import admin

from .models import (
    ProductCategoryModel,
    ProductTagModel,
    ProductModel,
    ProductCommentModel, BundleOfferModel, ProductImageModel
)


@admin.register(ProductCategoryModel)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'parent')
    search_fields = ('title',)
    list_filter = ('parent',)


@admin.register(ProductTagModel)
class ProductTagAdmin(admin.ModelAdmin):
    list_display = ('title',)
    search_fields = ('title',)


#@admin.register(ProductSizeModel)
#class ProductSizeAdmin(admin.ModelAdmin):
#    list_display = ('title',)
#    search_fields = ('title',)


#@admin.register(ProductManufactureModel)
#class ProductManufactureAdmin(admin.ModelAdmin):
#    list_display = ('name', 'logo')
#    search_fields = ('name',)


#@admin.register(ProductColorModel)
#class ProductColorAdmin(admin.ModelAdmin):
#    list_display = ('title', 'code')
#    search_fields = ('title', 'code')


class ProductImageAdmin(admin.StackedInline):
    model = ProductImageModel


@admin.register(ProductModel)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'price', 'old_price', 'in_stock', 'quantity', 'is_featured', 'has_audio', 'has_ebook')
    list_editable = ('price', 'quantity', 'is_featured')
    search_fields = ('title', 'author', 'publisher', 'isbn')
    list_filter = ('in_stock', 'is_featured', 'language', 'categories')
    filter_horizontal = ('categories',)
    inlines = [ProductImageAdmin]
    fieldsets = (
        ("Asosiy", {'fields': ('title', 'author', 'categories', 'short_description', 'long_description')}),
        ("Narx va ombor", {'fields': ('price', 'old_price', 'quantity', 'in_stock', 'is_featured')}),
        ("Rasmlar", {'fields': ('image1', 'image2')}),
        ("Parcha va mundarija", {'fields': ('excerpt', 'table_of_contents')}),
        ("Audio kitob", {'fields': ('audio_price', 'audio_file', 'audio_sample'),
                         'description': "Audio faylni shu yerdan yuklang. Narxni kiritsangiz, sahifada «Audio» formati paydo bo'ladi."}),
        ("E-kitob", {'fields': ('ebook_price', 'ebook_file'),
                     'description': "PDF yoki EPUB. Narxni kiritsangiz, sahifada «E-Book» formati paydo bo'ladi."}),
        ("Kitob haqida", {'fields': ('publisher', 'language', 'pages', 'year', 'cover_type', 'isbn'),
                          'classes': ('collapse',)}),
    )


@admin.register(ProductCommentModel)
class ProductCommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'rating', 'comment', 'created_at')
    list_filter = ('rating',)
    search_fields = ('user__username', 'product__title', 'comment')


@admin.register(BundleOfferModel)
class BundleOfferAdmin(admin.ModelAdmin):
    list_display = ('title', 'label', 'discount_percent', 'starts_at', 'ends_at', 'is_active', 'status')
    list_filter = ('is_active',)
    filter_horizontal = ('products',)
    fieldsets = (
        (None, {'fields': ('label', 'title', 'products', 'discount_percent')}),
        ("Muddat", {'fields': ('starts_at', 'ends_at', 'is_active')}),
    )

    @admin.display(description="Holati")
    def status(self, obj):
        return "Davom etmoqda" if obj.is_running else "Faol emas / tugagan"
