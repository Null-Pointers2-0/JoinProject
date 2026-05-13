from django.urls import path
from . import views

urlpatterns = [
    path('user/profile', views.profile, name='profile'),
    path('user/history', views.history, name='history'),
    path('user/subscription', views.subscription, name='suscription'),
    path('user/followed', views.followed, name='followed'),
    path('user/gestion', views.gestion_usuarios, name='gestion_usuarios'),
    path('user/crear_admin', views.crear_usuario_admin, name='crear_usuario_admin'),
    path('user/eliminar/<int:user_id>', views.eliminar_usuario, name='eliminar_usuario'),
]