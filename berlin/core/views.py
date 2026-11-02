from django.shortcuts import render

from catalog.models import Brand, Category, Product


def home(request):
    context = {
        'featured_products': (
            Product.objects.filter(
                is_active=True,
                is_featured=True,
                brand__is_active=True,
                category__is_active=True,
            )
            .select_related('brand', 'category')
            .prefetch_related('images')
        ),
        'categories': Category.objects.filter(is_active=True, parent__isnull=True),
        'brands': Brand.objects.filter(is_active=True),
    }
    return render(request, 'core/home.html', context)
