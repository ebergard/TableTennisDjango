from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('success/', views.success, name='success'),
    path('failure/', views.failure, name='failure'),
    path('participants/', views.participants, name='participants'),
    path('rating/', views.rating, name='rating'),
    path('games/', views.games, name='games'),
    path('accounts/register/', views.account_register, name='account_register'),
    path('accounts/login/', views.account_login, name='account_login'),
    path('accounts/logout/', views.account_logout, name='account_logout'),
    path('accounts/me/', views.me, name='me'),
    path('accounts/me/register/', views.me_register, name='me_register'),
    path('accounts/me/games/', views.me_games, name='me_games'),
    path('accounts/me/games/<game>/', views.me_games, name='me_game'),
    path('accounts/me/before_draw/', views.me_before_draw, name='me_before_draw'),
]
