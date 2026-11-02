from django import forms
from django.db.models import TextChoices

from .models import Brand, Category, Product


class CatalogFilterForm(forms.Form):
    class Availability(TextChoices):
        ALL = '', 'All products'
        IN_STOCK = 'in_stock', 'In stock'
        OUT_OF_STOCK = 'out_of_stock', 'Out of stock'

    SORT_CHOICES = [
        ('', 'Relevance'),
        ('price_asc', 'Price: low to high'),
        ('price_desc', 'Price: high to low'),
        ('newest', 'Newest'),
    ]

    q = forms.CharField(
        required=False,
        max_length=120,
        label='Search parts',
        widget=forms.SearchInput(attrs={'placeholder': 'Name, SKU, brand, or vehicle'}),
    )
    vehicle_make = forms.CharField(required=False, max_length=100, label='Vehicle make')
    vehicle_model = forms.CharField(required=False, max_length=100, label='Vehicle model')
    vehicle_year = forms.IntegerField(
        required=False,
        min_value=1886,
        max_value=2100,
        label='Vehicle year',
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        to_field_name='slug',
        required=False,
        empty_label='All categories',
    )
    brand = forms.ModelChoiceField(
        queryset=Brand.objects.filter(is_active=True),
        to_field_name='slug',
        required=False,
        empty_label='All brands',
    )
    currency = forms.ChoiceField(
        choices=[('', 'All currencies')],
        required=False,
    )
    min_price = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=12,
        decimal_places=2,
        label='Minimum price',
    )
    max_price = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=12,
        decimal_places=2,
        label='Maximum price',
    )
    availability = forms.ChoiceField(
        choices=Availability.choices,
        required=False,
    )
    sort = forms.ChoiceField(choices=SORT_CHOICES, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        currencies = (
            Product.objects.filter(is_active=True, brand__is_active=True, category__is_active=True)
            .values_list('currency', flat=True)
            .distinct()
            .order_by('currency')
        )
        self.fields['currency'].choices = [
            ('', 'All currencies'),
            *((currency, currency) for currency in currencies),
        ]
        for field in self.fields.values():
            field.widget.attrs.setdefault(
                'class',
                'w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm',
            )

    def clean(self):
        cleaned_data = super().clean()
        min_price = cleaned_data.get('min_price')
        max_price = cleaned_data.get('max_price')
        if min_price is not None and max_price is not None and min_price > max_price:
            self.add_error('max_price', 'Maximum price must be at least the minimum price.')
        needs_currency = (
            min_price is not None
            or max_price is not None
            or cleaned_data.get('sort') in {'price_asc', 'price_desc'}
        )
        if needs_currency and len(self.fields['currency'].choices) > 2 and not cleaned_data.get('currency'):
            self.add_error('currency', 'Choose a currency before filtering or sorting by price.')
        return cleaned_data
