from django.contrib import admin
from .models import Order, OrderItem, Coupon


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'full_name',
        'city',
        'total_price',
        'coupon_code',
        'status',
        'paid',
        'created'
    )
    list_filter = ('status', 'paid', 'created')
    search_fields = ('full_name', 'city', 'user__username', 'user__email')
    list_editable = ('status', 'paid')
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'price', 'quantity')


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'active', 'created_at')
    list_filter = ('active', 'discount_type')
    search_fields = ('code',)