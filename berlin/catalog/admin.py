from django.contrib import admin

from .models import Brand, Category, Product, ProductImage, VehicleFitment


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active']
    list_filter = ['is_active']
    prepopulated_fields = {'slug': ['name']}
    search_fields = ['name']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'is_active']
    list_filter = ['is_active', 'parent']
    prepopulated_fields = {'slug': ['name']}
    search_fields = ['name', 'description']


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class VehicleFitmentInline(admin.TabularInline):
    model = VehicleFitment
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'sku',
        'brand',
        'category',
        'price',
        'currency',
        'stock_quantity',
        'is_active',
        'is_featured',
    ]
    list_filter = ['is_active', 'is_featured', 'brand', 'category', 'condition']
    prepopulated_fields = {'slug': ['name', 'sku']}
    search_fields = ['name', 'sku', 'brand__name', 'category__name']
    list_select_related = ['brand', 'category']
    inlines = [ProductImageInline, VehicleFitmentInline]
