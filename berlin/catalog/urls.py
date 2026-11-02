from django.urls import path

from .views import ProductDetailView, ProductListView

app_name = 'catalog'

urlpatterns = [
    path('', ProductListView.as_view(), name='product_list'),
    path('category/<slug:category_slug>/', ProductListView.as_view(), name='category_detail'),
    path('brand/<slug:brand_slug>/', ProductListView.as_view(), name='brand_detail'),
    path('<slug:slug>/', ProductDetailView.as_view(), name='product_detail'),
]
