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
    path("movie/<int:movie_id>/", views.movie_detail, name="movie_detail"),
    path("catalog/", views.catalog_view, name="catalog"),

    path("api/user/profile/", views.api_user_profile, name="api_user_profile"),
]