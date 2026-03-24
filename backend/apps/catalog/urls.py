from django.urls import path

from apps.catalog import views

app_name = 'catalog'

urlpatterns = [
    path('', views.shop_home, name='shop_home'),
    path('produtos/', views.product_list, name='product_list'),
    path('categoria/<slug:slug>/', views.category_detail, name='category_detail'),
    path('produto/<slug:slug>/', views.product_detail, name='product_detail'),
]
