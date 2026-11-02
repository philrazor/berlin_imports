from django.contrib import admin

from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['product_name', 'sku', 'unit_price', 'currency', 'quantity']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at', 'updated_at']
    search_fields = ['user__username', 'user__email']
    list_select_related = ['user']
    inlines = [CartItemInline]
