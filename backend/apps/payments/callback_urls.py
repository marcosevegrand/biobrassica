from django.urls import path

from apps.payments import views

urlpatterns = [
    path('stripe/', views.stripe_callback, name='stripe_callback'),
    path('ifthenpay/mbway/', views.ifthenpay_mbway_callback, name='ifthenpay_mbway_callback'),
]
