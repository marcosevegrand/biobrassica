from django.urls import path

from apps.payments import views

urlpatterns = [
    path('ifthenpay/', views.ifthenpay_callback, name='ifthenpay_callback'),
]
