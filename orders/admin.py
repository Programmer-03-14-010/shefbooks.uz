from django.contrib import admin
from django.utils.html import format_html

from .models import OrderModel, OrderItemModel, PromoCodeModel


class OrderItemInline(admin.StackedInline):
    model = OrderItemModel
    extra = 1

    readonly_fields = (
        'product_title',
        'product_price',
    )
    fields = ('product', 'format', 'product_title', 'product_price', 'product_quantity')

    can_delete = True
    show_change_link = True


@admin.register(OrderModel)
class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline]

    list_display = (
        'id',
        'full_name',
        'phone_number',
        'total_amount',
        'promo_code',
        'is_paid',
        'status',
        'created_at',
    )

    list_filter = (
        'status',
        'is_paid',
        'created_at',
    )

    search_fields = (
        'id',
        'full_name',
        'phone_number',
        'email',
    )

    readonly_fields = (
        'total_amount',
        'promo_code',
        'discount_amount',
        'total_products',
        'receipt_preview',
        'post_receipt_preview',
        'created_at',
    )

    fieldsets = (
        ("Buyurtma ma'lumotlari", {
            'fields': (
                'user',
                'full_name',
                'phone_number',
                'email',
                'address',
            )
        }),

        ("To'lov", {
            'fields': (
                'is_paid',
                'payment_receipt',
                'receipt_preview',       # Mahsulot cheki preview
                'post_receipt',
                'post_receipt_preview',  # Pochta cheki preview
            )
        }),

        ("Hisob-kitob", {
            'fields': (
                'total_products',
                'promo_code',
                'discount_amount',
                'total_amount',
                'status',
            )
        }),

        ('Sana', {
            'fields': (
                'created_at',
            )
        }),
    )

    # ✅ Mahsulot to'lov cheki preview
    def receipt_preview(self, obj):
        if obj.payment_receipt:
            return format_html(
                '<a href="{}" target="_blank">'
                '<img src="{}" width="300" '
                'style="border-radius:10px;border:1px solid #ddd;margin-top:6px;">'
                '</a>',
                obj.payment_receipt.url,
                obj.payment_receipt.url,
            )
        return "Mahsulot cheki yuklanmagan"

    receipt_preview.short_description = "Mahsulot cheki rasmi"

    # ✅ Pochta to'lov cheki preview
    def post_receipt_preview(self, obj):
        if obj.post_receipt:
            return format_html(
                '<a href="{}" target="_blank">'
                '<img src="{}" width="300" '
                'style="border-radius:10px;border:1px solid #fcd34d;margin-top:6px;">'
                '</a>',
                obj.post_receipt.url,
                obj.post_receipt.url,
            )
        return "Pochta cheki yuklanmagan"

    post_receipt_preview.short_description = "Pochta (UZPOST) cheki rasmi"


@admin.register(OrderItemModel)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'order',
        'product_title',
        'product_quantity',
        'product_price',
    )

    search_fields = (
        'product_title',
        'order__id',
    )


@admin.register(PromoCodeModel)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'label', 'min_order_amount', 'used_count', 'max_uses', 'once_per_user',
                    'valid_from', 'valid_to', 'is_active')
    list_editable = ('is_active',)
    list_filter = ('is_active', 'discount_type')
    search_fields = ('code', 'description')
    readonly_fields = ('used_count', 'created_at')
    fieldsets = (
        (None, {'fields': ('code', 'description', 'is_active')}),
        ('Chegirma', {'fields': ('discount_type', 'value', 'max_discount', 'min_order_amount')}),
        ('Cheklovlar', {'fields': ('max_uses', 'used_count', 'once_per_user', 'valid_from', 'valid_to')}),
    )
