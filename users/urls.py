from django.urls import path
from . import views

urlpatterns = [
    path('user/profile', views.profile, name='profile'),
    path('user/history', views.history, name='history'),
    path('user/subscription', views.subscription, name='suscription')
]