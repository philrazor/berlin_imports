from django.db.models import Case, IntegerField, Q, Value, When
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView

from .forms import CatalogFilterForm
from .models import Brand, Category, Product


class ProductListView(ListView):
    template_name = 'catalog/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_filter_form(self):
        if not hasattr(self, '_filter_form'):
            self._filter_form = CatalogFilterForm(self.request.GET)
        return self._filter_form

    def get_route_category(self):
        if not hasattr(self, '_route_category'):
            slug = self.kwargs.get('category_slug')
            self._route_category = (
                get_object_or_404(Category, slug=slug, is_active=True) if slug else None
            )
        return self._route_category

    def get_route_brand(self):
        if not hasattr(self, '_route_brand'):
            slug = self.kwargs.get('brand_slug')
            self._route_brand = (
                get_object_or_404(Brand, slug=slug, is_active=True) if slug else None
            )
        return self._route_brand

    def get_queryset(self):
        queryset = (
            Product.objects.filter(
                is_active=True,
                brand__is_active=True,
                category__is_active=True,
            )
            .select_related('brand', 'category')
            .prefetch_related('images', 'fitments')
        )

        route_category = self.get_route_category()
        route_brand = self.get_route_brand()
        form = self.get_filter_form()

        route_category = self.get_route_category()
        route_brand = self.get_route_brand()
        if form.is_valid():
            filters = form.cleaned_data
            category = filters.get('category') or route_category
            brand = filters.get('brand') or route_brand
            query = filters.get('q', '').strip()

            currency = filters.get('currency')
            if currency:
                queryset = queryset.filter(currency=currency)

            vehicle_make = filters.get('vehicle_make', '').strip()
            vehicle_model = filters.get('vehicle_model', '').strip()
            vehicle_year = filters.get('vehicle_year')
            fitment_filter = Q()
            if vehicle_make:
                fitment_filter &= Q(fitments__make__icontains=vehicle_make)
            if vehicle_model:
                fitment_filter &= Q(fitments__model__icontains=vehicle_model)
            if vehicle_year:
                fitment_filter &= (
                    Q(fitments__year_start__lte=vehicle_year)
                    & (
                        Q(fitments__year_end__isnull=True)
                        | Q(fitments__year_end__gte=vehicle_year)
                    )
                )
            if vehicle_make or vehicle_model or vehicle_year:
                queryset = queryset.filter(fitment_filter).distinct()

            min_price = filters.get('min_price')
            max_price = filters.get('max_price')
            if min_price is not None:
                queryset = queryset.filter(price__gte=min_price)
            if max_price is not None:
                queryset = queryset.filter(price__lte=max_price)

            availability = filters.get('availability')
            if availability == CatalogFilterForm.Availability.IN_STOCK:
                queryset = queryset.filter(stock_quantity__gt=0)
            elif availability == CatalogFilterForm.Availability.OUT_OF_STOCK:
                queryset = queryset.filter(stock_quantity=0)

            if query:
                for term in query.split():
                    term_matches = (
                        Q(name__icontains=term)
                        | Q(sku__icontains=term)
                        | Q(brand__name__icontains=term)
                        | Q(category__name__icontains=term)
                        | Q(fitments__make__icontains=term)
                        | Q(fitments__model__icontains=term)
                        | Q(fitments__engine__icontains=term)
                        | Q(fitments__trim__icontains=term)
                    )
                    if term.isdigit():
                        year = int(term)
                        term_matches |= (
                            Q(fitments__year_start__lte=year)
                            & (
                                Q(fitments__year_end__isnull=True)
                                | Q(fitments__year_end__gte=year)
                            )
                        )
                    queryset = queryset.filter(
                        term_matches
                    )
                queryset = queryset.distinct().annotate(
                    relevance=Case(
                        When(sku__iexact=query, then=Value(0)),
                        When(name__iexact=query, then=Value(1)),
                        When(sku__istartswith=query, then=Value(2)),
                        When(name__icontains=query, then=Value(3)),
                        default=Value(4),
                        output_field=IntegerField(),
                    )
                )

            sort = filters.get('sort')
        else:
            query = ''
            sort = ''
            category = route_category
            brand = route_brand

        if category:
            queryset = queryset.filter(category=category)
        if brand:
            queryset = queryset.filter(brand=brand)

        if sort == 'price_asc':
            return queryset.order_by('price', 'pk')
        if sort == 'price_desc':
            return queryset.order_by('-price', 'pk')
        if sort == 'newest':
            return queryset.order_by('-created_at', '-pk')
        if query:
            return queryset.order_by('relevance', '-created_at', '-pk')
        return queryset.order_by('-created_at', '-pk')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        route_category = self.get_route_category()
        route_brand = self.get_route_brand()
        context.update(
            {
                'filter_form': self.get_filter_form(),
                'categories': Category.objects.filter(is_active=True),
                'brands': Brand.objects.filter(is_active=True),
                'current_category': route_category,
                'current_brand': route_brand,
                'page_title': (
                    route_category.name
                    if route_category
                    else route_brand.name
                    if route_brand
                    else 'Shop all parts'
                ),
                'search_query': self.request.GET.get('q', '').strip(),
            }
        )
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'catalog/product_detail.html'
    context_object_name = 'product'
    queryset = (
        Product.objects.filter(
            is_active=True,
            brand__is_active=True,
            category__is_active=True,
        )
        .select_related('brand', 'category')
        .prefetch_related('images', 'fitments')
    )
