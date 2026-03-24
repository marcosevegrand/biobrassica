from django.urls import path

from apps.website import views

app_name = 'website'

urlpatterns = [
    path('privacidade/', views.privacy, name='privacy'),
    path('termos/', views.terms, name='terms'),
]
