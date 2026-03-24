from django.urls import path

from apps.cart import views

app_name = 'cart'

urlpatterns = [
    path('', views.cart_detail, name='detail'),
    path('adicionar/<int:product_id>/', views.add_to_cart, name='add'),
    path('atualizar/<int:item_id>/', views.update_cart_item, name='update'),
    path('remover/<int:item_id>/', views.remove_from_cart, name='remove'),
]
