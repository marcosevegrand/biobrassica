from django.urls import path

from apps.content import views

app_name = 'content'

urlpatterns = [
    # Blog
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog_detail'),
    # Recipes
    path('receitas/', views.recipe_list, name='recipe_list'),
    path('receitas/<slug:slug>/', views.recipe_detail, name='recipe_detail'),
]
