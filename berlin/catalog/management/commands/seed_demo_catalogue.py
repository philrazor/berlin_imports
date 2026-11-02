import re
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError

from catalog.models import Brand, Category, Product


class Command(BaseCommand):
    help = 'Add clearly labelled development-only sample products to the catalogue.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--currency',
            required=True,
            help='Three-letter currency code for these demo-only product prices (use XXX if undecided).',
        )

    def handle(self, *args, **options):
        currency = options['currency']
        if not re.fullmatch(r'[A-Z]{3}', currency):
            raise CommandError('Currency must be a three-letter uppercase code.')

        demo_products = [
            {
                'brand_name': 'BMW',
                'category_name': 'Brake pads',
                'name': 'Demo Brake Pad Set',
                'sku': 'DEMO-BP-001',
                'description': 'Development sample only. Replace with verified product information.',
                'price': Decimal('149.95'),
                'stock_quantity': 8,
                'is_featured': True,
            },
            {
                'brand_name': 'Audi',
                'category_name': 'Engines',
                'name': 'Demo Engine Air Filter',
                'sku': 'DEMO-AF-001',
                'description': 'Development sample only. Replace with verified product information.',
                'price': Decimal('39.50'),
                'stock_quantity': 12,
                'is_featured': True,
            },
        ]
        created_count = 0
        for values in demo_products:
            brand = Brand.objects.get(name=values.pop('brand_name'))
            category = Category.objects.get(name=values.pop('category_name'))
            product, created = Product.objects.get_or_create(
                sku=values['sku'],
                defaults={
                    **values,
                    'brand': brand,
                    'category': category,
                    'currency': currency,
                },
            )
            if not created and product.currency != currency:
                raise CommandError(
                    f'{product.sku} already exists with currency {product.currency}; '
                    'it was not changed.'
                )
            created_count += int(created)

        self.stdout.write(
            self.style.SUCCESS(
                f'{created_count} demo product(s) added (or already present). '
                'These are development data, not approved sale listings.'
            )
        )
