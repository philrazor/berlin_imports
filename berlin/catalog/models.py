from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


currency_code_validator = RegexValidator(
    regex=r'^[A-Z]{3}$',
    message='Enter a three-letter uppercase currency code.',
)


class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=110, unique=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='brands/logos/', blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('catalog:brand_detail', kwargs={'brand_slug': self.slug})


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=110, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        related_name='children',
        blank=True,
        null=True,
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'categories'
        indexes = [models.Index(fields=['is_active', 'name'])]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('catalog:category_detail', kwargs={'category_slug': self.slug})


class Product(models.Model):
    class Condition(models.TextChoices):
        NEW = 'new', 'New'
        USED = 'used', 'Used'
        REFURBISHED = 'refurbished', 'Refurbished'

    brand = models.ForeignKey(
        Brand,
        on_delete=models.PROTECT,
        related_name='products',
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products',
    )
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=64, unique=True)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField()
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    currency = models.CharField(
        max_length=3,
        validators=[currency_code_validator],
        help_text='Three-letter ISO currency code; set the actual currency per product.',
    )
    stock_quantity = models.PositiveIntegerField(default=0)
    condition = models.CharField(
        max_length=12,
        choices=Condition.choices,
        blank=True,
    )
    warranty = models.CharField(max_length=200, blank=True)
    specifications = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', 'category']),
            models.Index(fields=['is_active', 'brand']),
            models.Index(fields=['is_active', 'price']),
            models.Index(fields=['is_active', '-created_at']),
        ]

    def __str__(self):
        return f'{self.name} ({self.sku})'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f'{self.name}-{self.sku}')[:220]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('catalog:product_detail', kwargs={'slug': self.slug})

    @property
    def is_available(self):
        return self.stock_quantity > 0


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
    )
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'pk']

    def __str__(self):
        return f'{self.product.name} image'


class VehicleFitment(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='fitments',
    )
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year_start = models.PositiveSmallIntegerField()
    year_end = models.PositiveSmallIntegerField(blank=True, null=True)
    engine = models.CharField(max_length=120, blank=True)
    trim = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ['make', 'model', 'year_start']
        indexes = [
            models.Index(fields=['make', 'model']),
            models.Index(fields=['year_start', 'year_end']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(year_end__isnull=True)
                    | models.Q(year_end__gte=models.F('year_start'))
                ),
                name='catalog_fitment_year_end_gte_start',
            ),
        ]

    def __str__(self):
        years = f'{self.year_start}–{self.year_end or "present"}'
        return f'{self.make} {self.model} ({years})'
