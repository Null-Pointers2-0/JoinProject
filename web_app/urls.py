from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from . import views
urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register_view, name="register"),
    path("login/", auth_views.lo)
]