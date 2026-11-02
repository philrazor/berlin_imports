from django.conf import settings
from django.db import models

from catalog.models import Product


class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Cart for {self.user.get_username()}'


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='cart_items',
    )
    product_name = models.CharField(max_length=200)
    sku = models.CharField(max_length=64)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3)
    quantity = models.PositiveIntegerField()
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['added_at', 'pk']
        constraints = [
            models.UniqueConstraint(
                fields=['cart', 'product'],
                name='cart_unique_product_per_user',
            ),
            models.CheckConstraint(
                condition=models.Q(quantity__gte=1),
                name='cart_item_quantity_gte_one',
            ),
        ]

    def __str__(self):
        return f'{self.product_name} × {self.quantity}'
