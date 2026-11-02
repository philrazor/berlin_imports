from decimal import Decimal
from io import StringIO

from django.contrib import admin
from django.core.management import call_command, CommandError
from django.test import TestCase
from django.urls import reverse

from .forms import CatalogFilterForm
from .models import Brand, Category, Product, ProductImage, VehicleFitment


class CatalogTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.bmw, _ = Brand.objects.get_or_create(name='BMW', defaults={'slug': 'bmw'})
        cls.audi, _ = Brand.objects.get_or_create(name='Audi', defaults={'slug': 'audi'})
        cls.brakes, _ = Category.objects.get_or_create(
            name='Brake pads',
            defaults={'slug': 'brake-pads'},
        )
        cls.engines, _ = Category.objects.get_or_create(
            name='Engines',
            defaults={'slug': 'engines'},
        )
        cls.brake_product = Product.objects.create(
            brand=cls.bmw,
            category=cls.brakes,
            name='Premium Brake Pad Set',
            sku='BP-100',
            description='Front brake pad set.',
            price=Decimal('125.00'),
            currency='EUR',
            stock_quantity=8,
            is_featured=True,
        )
        cls.engine_product = Product.objects.create(
            brand=cls.audi,
            category=cls.engines,
            name='Engine Air Filter',
            sku='AF-200',
            description='Replacement engine air filter.',
            price=Decimal('25.00'),
            currency='EUR',
            stock_quantity=0,
        )
        VehicleFitment.objects.create(
            product=cls.brake_product,
            make='Mercedes-Benz',
            model='C-Class',
            year_start=2017,
            year_end=2021,
            engine='2.0L',
        )

    def test_seed_categories_and_brands_are_present(self):
        self.assertTrue(Brand.objects.filter(name='Mercedes-Benz').exists())
        self.assertTrue(Brand.objects.filter(name='Porsche').exists())
        self.assertTrue(Category.objects.filter(name='Wheels').exists())
        self.assertTrue(Category.objects.filter(name='Rims').exists())
        self.assertTrue(
            Category.objects.filter(name='Engine management and control units').exists()
        )

    def test_catalogue_page_renders_products_and_filters(self):
        response = self.client.get(reverse('catalog:product_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.brake_product.name)
        self.assertContains(response, self.engine_product.name)
        self.assertContains(response, 'Apply filters')

    def test_search_matches_sku(self):
        response = self.client.get(reverse('catalog:product_list'), {'q': 'BP-100'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['products']), [self.brake_product])

    def test_search_matches_vehicle_fitment(self):
        response = self.client.get(
            reverse('catalog:product_list'),
            {'q': 'Mercedes-Benz C-Class'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['products']), [self.brake_product])

    def test_search_matches_vehicle_year(self):
        response = self.client.get(reverse('catalog:product_list'), {'q': '2020'})

        self.assertEqual(list(response.context['products']), [self.brake_product])

    def test_vehicle_filters_match_fitment_year_range(self):
        matches = self.client.get(
            reverse('catalog:product_list'),
            {'vehicle_make': 'Mercedes-Benz', 'vehicle_model': 'C-Class', 'vehicle_year': '2020'},
        )
        outside_range = self.client.get(
            reverse('catalog:product_list'),
            {'vehicle_make': 'Mercedes-Benz', 'vehicle_year': '2022'},
        )

        self.assertEqual(list(matches.context['products']), [self.brake_product])
        self.assertEqual(list(outside_range.context['products']), [])

    def test_category_and_brand_routes_filter_active_products(self):
        category_response = self.client.get(self.brakes.get_absolute_url())
        brand_response = self.client.get(self.audi.get_absolute_url())

        self.assertEqual(list(category_response.context['products']), [self.brake_product])
        self.assertEqual(list(brand_response.context['products']), [self.engine_product])

    def test_price_and_availability_filters(self):
        response = self.client.get(
            reverse('catalog:product_list'),
            {'min_price': '20', 'max_price': '30', 'availability': 'out_of_stock'},
        )

        self.assertEqual(list(response.context['products']), [self.engine_product])

    def test_price_sorting(self):
        response = self.client.get(
            reverse('catalog:product_list'),
            {'sort': 'price_asc'},
        )

        self.assertEqual(
            list(response.context['products']),
            [self.engine_product, self.brake_product],
        )

    def test_price_filter_requires_currency_when_catalogue_has_multiple(self):
        self.engine_product.currency = 'USD'
        self.engine_product.save(update_fields=['currency'])

        response = self.client.get(
            reverse('catalog:product_list'),
            {'min_price': '10', 'max_price': '200'},
        )

        self.assertContains(response, 'Choose a currency before filtering or sorting by price.')
        self.assertEqual(response.context['filter_form'].is_valid(), False)

    def test_price_filter_applies_only_to_selected_currency(self):
        self.engine_product.currency = 'USD'
        self.engine_product.save(update_fields=['currency'])

        response = self.client.get(
            reverse('catalog:product_list'),
            {'currency': 'EUR', 'min_price': '100'},
        )

        self.assertEqual(list(response.context['products']), [self.brake_product])

    def test_invalid_price_range_shows_validation_error(self):
        response = self.client.get(
            reverse('catalog:product_list'),
            {'min_price': '50', 'max_price': '10'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('Maximum price must be at least the minimum price.', response.text)

    def test_product_detail_shows_fitment_and_price(self):
        response = self.client.get(self.brake_product.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Mercedes-Benz C-Class')
        self.assertContains(response, '125.00 EUR')
        self.assertNotContains(response, 'No confirmed vehicle compatibility')

    def test_product_without_fitment_does_not_claim_compatibility(self):
        response = self.client.get(self.engine_product.get_absolute_url())

        self.assertContains(response, 'No confirmed vehicle compatibility details')

    def test_inactive_product_is_hidden_from_catalogue_and_detail(self):
        self.brake_product.is_active = False
        self.brake_product.save(update_fields=['is_active'])

        response = self.client.get(reverse('catalog:product_list'))

        self.assertNotContains(response, self.brake_product.name)
        self.assertEqual(self.client.get(self.brake_product.get_absolute_url()).status_code, 404)

    def test_inactive_brand_and_category_are_not_listed(self):
        self.audi.is_active = False
        self.audi.save(update_fields=['is_active'])
        self.engines.is_active = False
        self.engines.save(update_fields=['is_active'])

        response = self.client.get(reverse('catalog:product_list'))

        self.assertNotContains(response, self.engine_product.name)
        self.assertEqual(self.client.get(self.audi.get_absolute_url()).status_code, 404)
        self.assertEqual(self.client.get(self.engines.get_absolute_url()).status_code, 404)

    def test_brand_category_and_product_are_registered_in_admin(self):
        self.assertTrue(admin.site.is_registered(Brand))
        self.assertTrue(admin.site.is_registered(Category))
        self.assertTrue(admin.site.is_registered(Product))

    def test_product_image_and_fitment_are_attached_to_product(self):
        self.assertTrue(
            ProductImage._meta.get_field('product').remote_field.related_name == 'images'
        )
        self.assertTrue(
            VehicleFitment._meta.get_field('product').remote_field.related_name == 'fitments'
        )


class CatalogFilterFormTests(TestCase):
    def test_minimum_price_cannot_exceed_maximum_price(self):
        form = CatalogFilterForm({'min_price': '50', 'max_price': '10'})

        self.assertFalse(form.is_valid())
        self.assertIn('max_price', form.errors)

    def test_price_values_must_be_nonnegative(self):
        form = CatalogFilterForm({'min_price': '-1'})

        self.assertFalse(form.is_valid())
        self.assertIn('min_price', form.errors)


class DemoCatalogueCommandTests(TestCase):
    def test_seed_command_is_idempotent_and_requires_currency_explicitly(self):
        output = StringIO()

        call_command('seed_demo_catalogue', currency='XXX', stdout=output)
        call_command('seed_demo_catalogue', currency='XXX', stdout=output)

        self.assertEqual(Product.objects.filter(sku__startswith='DEMO-').count(), 2)
        self.assertIn('2 demo product(s) added', output.getvalue())
        self.assertIn('0 demo product(s) added', output.getvalue())
        self.assertTrue(Product.objects.filter(currency='XXX').exists())

    def test_seed_command_rejects_invalid_currency(self):
        with self.assertRaises(CommandError):
            call_command('seed_demo_catalogue', currency='eur')
