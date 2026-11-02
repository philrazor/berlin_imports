from django.conf import settings
from django.db import models


class CustomerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='customer_profile',
    )
    phone = models.CharField(max_length=32, blank=True)
    address_line_1 = models.CharField(max_length=200, blank=True)
    address_line_2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=32, blank=True)
    country = models.CharField(max_length=100, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Profile for {self.user.get_username()}'
