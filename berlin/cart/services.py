from dataclasses import dataclass
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from catalog.models import Product

from .models import Cart, CartItem

SESSION_CART_KEY = 'cart'


@dataclass(frozen=True)
class CartLine:
    product_id: int | None
    cart_item_id: int | None
    name: str
    sku: str
    image_url: str | None
    product_url: str | None
    unit_price: Decimal
    currency: str
    quantity: int
    max_stock: int
    is_available: bool

    @property
    def line_total(self):
        if not self.is_available:
            return Decimal('0.00')
        return self.unit_price * self.quantity


@dataclass(frozen=True)
class CartSummary:
    lines: list[CartLine]
    subtotals: dict[str, Decimal]


def _product_is_available(product):
    return (
        product is not None
        and product.is_active
        and product.brand.is_active
        and product.category.is_active
        and product.stock_quantity > 0
    )


def _get_guest_items(session):
    data = session.get(SESSION_CART_KEY, {})
    if not isinstance(data, dict):
        session[SESSION_CART_KEY] = {}
        return {}

    items = {}
    for product_id, quantity in data.items():
        product_id = str(product_id)
        if not product_id.isdecimal() or isinstance(quantity, bool):
            continue
        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            continue
        if int(product_id) > 0 and quantity > 0:
            items[int(product_id)] = quantity
    return items


def _save_guest_items(session, items):
    session[SESSION_CART_KEY] = {
        str(product_id): quantity for product_id, quantity in items.items()
    }
    session.modified = True


def _available_product(product_id, *, lock=False):
    queryset = Product.objects.select_related('brand', 'category')
    if lock:
        queryset = queryset.select_for_update()
    try:
        product = queryset.get(pk=product_id)
    except Product.DoesNotExist as error:
        raise ValidationError('This product is no longer available.') from error
    if not _product_is_available(product):
        raise ValidationError('This product is currently unavailable.')
    return product


def merge_guest_cart(request, user=None):
    user = user or request.user
    guest_items = _get_guest_items(request.session)
    if not guest_items:
        request.session.pop(SESSION_CART_KEY, None)
        request.session.modified = True
        return {'skipped': 0, 'adjusted': 0}

    skipped = 0
    adjusted = 0
    with transaction.atomic():
        cart, _ = Cart.objects.get_or_create(user=user)
        for product_id, guest_quantity in guest_items.items():
            try:
                product = _available_product(product_id, lock=True)
            except ValidationError:
                skipped += 1
                continue

            item = CartItem.objects.select_for_update().filter(
                cart=cart,
                product=product,
            ).first()
            previous_quantity = item.quantity if item else 0
            quantity = min(previous_quantity + guest_quantity, product.stock_quantity)
            if quantity < previous_quantity + guest_quantity:
                adjusted += 1

            if item is None:
                CartItem.objects.create(
                    cart=cart,
                    product=product,
                    product_name=product.name,
                    sku=product.sku,
                    unit_price=product.price,
                    currency=product.currency,
                    quantity=quantity,
                )
            else:
                item.product_name = product.name
                item.sku = product.sku
                item.unit_price = product.price
                item.currency = product.currency
                item.quantity = quantity
                item.save(
                    update_fields=[
                        'product_name',
                        'sku',
                        'unit_price',
                        'currency',
                        'quantity',
                        'updated_at',
                    ]
                )

    request.session.pop(SESSION_CART_KEY, None)
    request.session.modified = True
    return {'skipped': skipped, 'adjusted': adjusted}


@transaction.atomic
def add_item(request, product_id, quantity):
    if request.user.is_authenticated:
        product = _available_product(product_id, lock=True)
        cart, _ = Cart.objects.get_or_create(user=request.user)
        item = CartItem.objects.select_for_update().filter(
            cart=cart,
            product=product,
        ).first()
        new_quantity = quantity + (item.quantity if item else 0)
        if new_quantity > product.stock_quantity:
            raise ValidationError(
                f'Only {product.stock_quantity} of this product are currently available.'
            )
        if item is None:
            CartItem.objects.create(
                cart=cart,
                product=product,
                product_name=product.name,
                sku=product.sku,
                unit_price=product.price,
                currency=product.currency,
                quantity=new_quantity,
            )
        else:
            _update_item_snapshot(item, product, new_quantity)
        return

    product = _available_product(product_id, lock=True)
    items = _get_guest_items(request.session)
    new_quantity = quantity + items.get(product.pk, 0)
    if new_quantity > product.stock_quantity:
        raise ValidationError(
            f'Only {product.stock_quantity} of this product are currently available.'
        )
    items[product.pk] = new_quantity
    _save_guest_items(request.session, items)


@transaction.atomic
def set_item_quantity(request, product_id, quantity):
    product = _available_product(product_id, lock=True)
    if quantity > product.stock_quantity:
        raise ValidationError(
            f'Only {product.stock_quantity} of this product are currently available.'
        )

    if request.user.is_authenticated:
        try:
            item = CartItem.objects.select_for_update().get(
                cart__user=request.user,
                product=product,
            )
        except CartItem.DoesNotExist as error:
            raise ValidationError('This item is no longer in your cart.') from error
        _update_item_snapshot(item, product, quantity)
        return

    items = _get_guest_items(request.session)
    if product.pk not in items:
        raise ValidationError('This item is no longer in your cart.')
    items[product.pk] = quantity
    _save_guest_items(request.session, items)


@transaction.atomic
def remove_item(request, product_id):
    if request.user.is_authenticated:
        deleted, _ = CartItem.objects.filter(
            cart__user=request.user,
            product_id=product_id,
        ).delete()
        return bool(deleted)

    items = _get_guest_items(request.session)
    if product_id not in items:
        return False
    del items[product_id]
    _save_guest_items(request.session, items)
    return True


def _update_item_snapshot(item, product, quantity):
    item.product_name = product.name
    item.sku = product.sku
    item.unit_price = product.price
    item.currency = product.currency
    item.quantity = quantity
    item.save(
        update_fields=[
            'product_name',
            'sku',
            'unit_price',
            'currency',
            'quantity',
            'updated_at',
        ]
    )


def get_cart_summary(request):
    if request.user.is_authenticated:
        if SESSION_CART_KEY in request.session:
            merge_guest_cart(request)
        items = list(
            CartItem.objects.filter(cart__user=request.user)
            .select_related('product', 'product__brand', 'product__category')
            .prefetch_related('product__images')
        )
        lines = []
        for item in items:
            product = item.product
            available = (
                _product_is_available(product)
                and item.quantity <= product.stock_quantity
            )
            image = product.images.first() if product else None
            lines.append(
                CartLine(
                    product_id=product.pk if product else None,
                    cart_item_id=item.pk,
                    name=product.name if product else item.product_name,
                    sku=product.sku if product else item.sku,
                    image_url=image.image.url if image else None,
                    product_url=(
                        product.get_absolute_url()
                        if product
                        and product.is_active
                        and product.brand.is_active
                        and product.category.is_active
                        else None
                    ),
                    unit_price=product.price if product else item.unit_price,
                    currency=product.currency if product else item.currency,
                    quantity=item.quantity,
                    max_stock=product.stock_quantity if product else 0,
                    is_available=available,
                )
            )
    else:
        guest_items = _get_guest_items(request.session)
        products = (
            Product.objects.filter(pk__in=guest_items)
            .select_related('brand', 'category')
            .prefetch_related('images')
        )
        products_by_id = {product.pk: product for product in products}
        lines = []
        for product_id, quantity in guest_items.items():
            product = products_by_id.get(product_id)
            if product is None:
                continue
            image = product.images.first()
            available = _product_is_available(product) and quantity <= product.stock_quantity
            lines.append(
                CartLine(
                    product_id=product.pk,
                    cart_item_id=None,
                    name=product.name,
                    sku=product.sku,
                    image_url=image.image.url if image else None,
                    product_url=(
                        product.get_absolute_url()
                        if product.is_active
                        and product.brand.is_active
                        and product.category.is_active
                        else None
                    ),
                    unit_price=product.price,
                    currency=product.currency,
                    quantity=quantity,
                    max_stock=product.stock_quantity,
                    is_available=available,
                )
            )

        if len(products_by_id) != len(guest_items):
            valid_items = {
                product_id: quantity
                for product_id, quantity in guest_items.items()
                if product_id in products_by_id
            }
            _save_guest_items(request.session, valid_items)

    subtotals = {}
    for line in lines:
        if line.is_available:
            subtotals[line.currency] = (
                subtotals.get(line.currency, Decimal('0.00')) + line.line_total
            )
    return CartSummary(lines=lines, subtotals=subtotals)
