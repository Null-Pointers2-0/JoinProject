from django.urls import path
from . import views

urlpatterns = [
    path('user/profile', views.user_profile, name='user_profile'),
    path('user/history', views.history, name='history'),
    path('user/subscription', views.subscription, name='suscription'),
    path('user/followed', views.followed, name='followed'),
    path('admin/dashboard', views.admin_dashboard, name='admin_dashboard'),
    path('admin/profile', views.admin_profile, name='admin_profile'),
    path('admin/export', views.export_analytics_csv, name='export_csv')
]