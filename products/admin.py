from django.contrib import admin

from .models import (
    ProductCategoryModel,
    ProductTagModel,
    ProductModel,
    ProductCommentModel, ProductImageModel
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
    list_display = ('title', 'author', 'price', 'old_price', 'in_stock', 'quantity', 'is_featured')
    list_editable = ('price', 'quantity', 'is_featured')
    search_fields = ('title', 'author', 'publisher', 'isbn')
    list_filter = ('in_stock', 'is_featured', 'language', 'categories')
    filter_horizontal = ('categories',)
    inlines = [ProductImageAdmin]
    fieldsets = (
        ("Asosiy", {'fields': ('title', 'author', 'categories', 'short_description', 'long_description')}),
        ("Narx va ombor", {'fields': ('price', 'old_price', 'quantity', 'in_stock', 'is_featured')}),
        ("Rasmlar", {'fields': ('image1', 'image2')}),
        ("Kitob haqida", {'fields': ('publisher', 'language', 'pages', 'year', 'cover_type', 'isbn'),
                          'classes': ('collapse',)}),
    )


@admin.register(ProductCommentModel)
class ProductCommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'rating', 'comment', 'created_at')
    list_filter = ('rating',)
    search_fields = ('user__username', 'product__title', 'comment')
