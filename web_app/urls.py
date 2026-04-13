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
    path('user/profile', views.profile, name='profile'),
    path('user/history', views.history, name='history'),
]