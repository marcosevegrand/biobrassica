from django.urls import path

from apps.orders import views

app_name = 'orders'

urlpatterns = [
    path('', views.checkout, name='checkout'),
    path('<int:order_id>/', views.checkout, name='checkout_order'),
    path('confirmar/', views.checkout_confirm, name='confirm'),
    path('pagamento/<int:order_id>/', views.payment_select, name='payment_select'),
    path('pagamento/<int:order_id>/estado/', views.payment_status, name='payment_status'),
    path('concluido/<int:order_id>/', views.order_complete, name='complete'),
]
