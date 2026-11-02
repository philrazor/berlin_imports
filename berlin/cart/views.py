from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from catalog.models import Product

from .forms import CartQuantityForm
from .services import add_item, get_cart_summary, remove_item, set_item_quantity


def detail(request):
    return render(request, 'cart/detail.html', {'cart': get_cart_summary(request)})


@require_POST
def add(request, product_id):
    product = get_object_or_404(
        Product.objects.select_related('brand', 'category'),
        pk=product_id,
        is_active=True,
        brand__is_active=True,
        category__is_active=True,
    )
    form = CartQuantityForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Enter a valid quantity to add this part.')
        return redirect(product.get_absolute_url())
    try:
        add_item(request, product.pk, form.cleaned_data['quantity'])
    except ValidationError as error:
        for message in error.messages:
            messages.error(request, message)
        return redirect(product.get_absolute_url())

    messages.success(request, f'{product.name} was added to your cart.')
    return redirect('cart:detail')


@require_POST
def update(request, product_id):
    form = CartQuantityForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Enter a quantity of at least one.')
        return redirect('cart:detail')
    try:
        set_item_quantity(request, product_id, form.cleaned_data['quantity'])
    except ValidationError as error:
        for message in error.messages:
            messages.error(request, message)
        return redirect('cart:detail')

    messages.success(request, 'Your cart quantity was updated.')
    return redirect('cart:detail')


@require_POST
def remove(request, product_id):
    if remove_item(request, product_id):
        messages.success(request, 'The part was removed from your cart.')
    else:
        messages.info(request, 'That part was no longer in your cart.')
    return redirect('cart:detail')
