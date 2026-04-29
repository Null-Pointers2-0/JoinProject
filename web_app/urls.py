from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView

from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register_view, name="register"),
    path("login/", auth_views.LoginView.as_view(template_name="identify/login.html"), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),

    path("user_setting/", views.user_setting, name="user_setting"),
    path("movie/<int:pk>/", views.movie_detail, name="movie_detail"),
    path("series/<int:pk>/", views.series_detail, name="series_detail"),

    path("api/user/profile/", views.api_user_profile, name="api_user_profile"),
    path('favorite/toggle/<int:pk>/', views.toggle_favorite, name='toggle_favorite'),

    path('terms-use/', views.terms_use, name='terms_use'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),

    #path('user/profile', views.profile, name='profile'),
    #path('user/history', views.history, name='history'),

    #path("catalog/", views.catalog_view, name="catalog"),
]