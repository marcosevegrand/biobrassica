from django.urls import path

from apps.payments import views

urlpatterns = [
    path('stripe/', views.stripe_callback, name='stripe_callback'),
]
