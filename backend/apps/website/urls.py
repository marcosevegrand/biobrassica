from django.urls import path

from apps.website import views

app_name = 'website'

urlpatterns = [
    path('', views.home, name='home'),
    path('quem-somos/', views.about, name='about'),
    path('agricultura-bio/', views.agriculture, name='agriculture'),
    path('contactos/', views.contacts, name='contacts'),
    path('privacidade/', views.privacy, name='privacy'),
    path('termos/', views.terms, name='terms'),
]
