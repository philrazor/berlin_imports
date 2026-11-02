from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import CustomerProfile
from cart.models import Cart, CartItem
from catalog.models import Brand, Category, Product

User = get_user_model()


class CartTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.brand, _ = Brand.objects.get_or_create(
            name='BMW',
            defaults={'slug': 'bmw'},
        )
        cls.category, _ = Category.objects.get_or_create(
            name='Brake pads',
            defaults={'slug': 'brake-pads'},
        )
        cls.product = Product.objects.create(
            brand=cls.brand,
            category=cls.category,
            name='Demo Brake Pad Set',
            sku='CART-BP-001',
            description='Development test part.',
            price=Decimal('19.95'),
            currency='XXX',
            stock_quantity=5,
        )
        cls.other_product = Product.objects.create(
            brand=cls.brand,
            category=cls.category,
            name='Demo Rotor',
            sku='CART-RT-002',
            description='Development test part.',
            price=Decimal('25.00'),
            currency='USD',
            stock_quantity=4,
        )

    def add_product(self, client=None, product=None, quantity=1):
        client = client or self.client
        product = product or self.product
        return client.post(
            reverse('cart:add', kwargs={'product_id': product.pk}),
            {'quantity': quantity},
        )

    def test_guest_cart_persists_and_calculates_server_side_totals(self):
        self.add_product(quantity=2)
        first_response = self.client.get(reverse('cart:detail'))
        self.assertEqual(len(first_response.context['cart'].lines), 1)

        response = self.client.get(reverse('cart:detail'))

        line = response.context['cart'].lines[0]
        self.assertEqual(line.quantity, 2)
        self.assertEqual(line.line_total, Decimal('39.90'))
        self.assertEqual(response.context['cart'].subtotals, {'XXX': Decimal('39.90')})
        self.assertContains(response, 'CART-BP-001')
        self.assertContains(response, '39.90 XXX')

    def test_cart_add_rejects_nonpositive_invalid_and_excess_quantities(self):
        for quantity in ('0', '-1', 'not-an-integer', '6'):
            response = self.add_product(quantity=quantity)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(self.client.get(reverse('cart:detail')).context['cart'].lines, [])

    def test_repeated_additions_cannot_exceed_current_stock(self):
        self.add_product(quantity=3)
        response = self.add_product(quantity=3)
        response = self.client.get(response.url)

        self.assertContains(response, 'Only 5 of this product are currently available.')
        line = self.client.get(reverse('cart:detail')).context['cart'].lines[0]
        self.assertEqual(line.quantity, 3)

    def test_guest_can_update_and_remove_cart_items(self):
        self.add_product(quantity=2)
        self.client.post(
            reverse('cart:update', kwargs={'product_id': self.product.pk}),
            {'quantity': '4'},
        )
        line = self.client.get(reverse('cart:detail')).context['cart'].lines[0]
        self.assertEqual(line.quantity, 4)
        self.assertEqual(line.line_total, Decimal('79.80'))

        self.client.post(reverse('cart:remove', kwargs={'product_id': self.product.pk}))
        self.assertEqual(self.client.get(reverse('cart:detail')).context['cart'].lines, [])

    def test_cart_update_rejects_quantity_above_current_stock(self):
        self.add_product(quantity=2)
        response = self.client.post(
            reverse('cart:update', kwargs={'product_id': self.product.pk}),
            {'quantity': '6'},
        )

        self.assertEqual(response.status_code, 302)
        response = self.client.get(response.url)
        self.assertContains(response, 'Only 5 of this product are currently available.')
        self.assertEqual(
            response.context['cart'].lines[0].quantity,
            2,
        )

    def test_product_stock_change_marks_cart_line_unavailable(self):
        self.add_product(quantity=2)
        self.product.stock_quantity = 1
        self.product.save(update_fields=['stock_quantity'])

        response = self.client.get(reverse('cart:detail'))

        self.assertFalse(response.context['cart'].lines[0].is_available)
        self.assertEqual(response.context['cart'].subtotals, {})
        self.assertContains(response, 'excluded from subtotal')

    def test_cart_separates_currency_subtotals(self):
        self.add_product(quantity=2)
        self.add_product(product=self.other_product, quantity=2)

        summary = self.client.get(reverse('cart:detail')).context['cart']

        self.assertEqual(
            summary.subtotals,
            {'XXX': Decimal('39.90'), 'USD': Decimal('50.00')},
        )

    def test_inactive_product_cannot_be_added_and_existing_line_can_be_removed(self):
        self.add_product()
        self.product.is_active = False
        self.product.save(update_fields=['is_active'])

        response = self.client.get(reverse('cart:detail'))
        self.assertFalse(response.context['cart'].lines[0].is_available)

        self.client.post(reverse('cart:remove', kwargs={'product_id': self.product.pk}))
        self.assertEqual(self.client.get(reverse('cart:detail')).context['cart'].lines, [])

    def test_cart_mutations_require_post(self):
        response = self.client.get(
            reverse('cart:add', kwargs={'product_id': self.product.pk})
        )
        self.assertEqual(response.status_code, 405)

    def test_add_product_detail_includes_cart_form(self):
        response = self.client.get(self.product.get_absolute_url())

        self.assertContains(response, 'Add to cart')
        self.assertContains(response, reverse('cart:add', kwargs={'product_id': self.product.pk}))

    def test_guest_cart_is_merged_into_authenticated_cart_after_login(self):
        user = User.objects.create_user(
            username='cart-customer',
            email='cart-customer@example.test',
            password='Secure-test-password-42!',
        )
        CustomerProfile.objects.create(user=user)
        self.add_product(quantity=2)

        response = self.client.post(
            reverse('accounts:login'),
            {'username': user.username, 'password': 'Secure-test-password-42!'},
        )

        self.assertEqual(response.status_code, 302)
        item = CartItem.objects.get(cart__user=user, product=self.product)
        self.assertEqual(item.quantity, 2)
        self.assertNotIn('cart', self.client.session)

    def test_guest_cart_merge_combines_and_caps_authenticated_items_to_stock(self):
        user = User.objects.create_user(
            username='merge-customer',
            email='merge-customer@example.test',
            password='Secure-test-password-42!',
        )
        cart = Cart.objects.create(user=user)
        CartItem.objects.create(
            cart=cart,
            product=self.product,
            product_name=self.product.name,
            sku=self.product.sku,
            unit_price=self.product.price,
            currency=self.product.currency,
            quantity=4,
        )
        self.add_product(quantity=3)

        self.client.post(
            reverse('accounts:login'),
            {'username': user.username, 'password': 'Secure-test-password-42!'},
        )

        self.assertEqual(CartItem.objects.get(cart=cart, product=self.product).quantity, 5)

    def test_authenticated_cart_is_private_to_current_user(self):
        first_user = User.objects.create_user(
            username='first-customer',
            email='first@example.test',
            password='Secure-test-password-42!',
        )
        second_user = User.objects.create_user(
            username='second-customer',
            email='second@example.test',
            password='Secure-test-password-42!',
        )
        first_cart = Cart.objects.create(user=first_user)
        second_cart = Cart.objects.create(user=second_user)
        CartItem.objects.create(
            cart=first_cart,
            product=self.product,
            product_name=self.product.name,
            sku=self.product.sku,
            unit_price=self.product.price,
            currency=self.product.currency,
            quantity=1,
        )
        CartItem.objects.create(
            cart=second_cart,
            product=self.other_product,
            product_name=self.other_product.name,
            sku=self.other_product.sku,
            unit_price=self.other_product.price,
            currency=self.other_product.currency,
            quantity=1,
        )

        self.client.force_login(first_user)
        response = self.client.get(reverse('cart:detail'))

        self.assertContains(response, self.product.name)
        self.assertNotContains(response, self.other_product.name)

    def test_guest_cart_merge_skips_unavailable_products(self):
        user = User.objects.create_user(
            username='unavailable-customer',
            email='unavailable@example.test',
            password='Secure-test-password-42!',
        )
        self.add_product()
        self.product.stock_quantity = 0
        self.product.save(update_fields=['stock_quantity'])

        self.client.post(
            reverse('accounts:login'),
            {'username': user.username, 'password': 'Secure-test-password-42!'},
        )

        self.assertFalse(Cart.objects.filter(user=user, items__isnull=False).exists())
        self.assertNotIn('cart', self.client.session)

    def test_csrf_protects_guest_cart_mutations(self):
        csrf_client = Client(enforce_csrf_checks=True)
        response = csrf_client.post(
            reverse('cart:add', kwargs={'product_id': self.product.pk}),
            {'quantity': 1},
        )

        self.assertEqual(response.status_code, 403)
