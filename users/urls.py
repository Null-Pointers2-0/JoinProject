from django.urls import path
from . import views

urlpatterns = [
    # Staff Admin URLs
    path('gestion/', views.gestion_usuarios, name='gestion_usuarios'),
    path('crear_admin/', views.crear_usuario_admin, name='crear_usuario_admin'),
    path('eliminar/<int:user_id>', views.eliminar_usuario, name='eliminar_usuario'),
    path('api/update-role/', views.update_user_role, name='update_user_role'),

    # User URLs
    path('profile/', views.user_profile, name='user_profile'),
    path('history/', views.history, name='history'),
    path('followed/', views.followed, name='followed'),
    path('subscription/', views.subscription, name='suscription'),

    # Admin URLs
    path('admin/export-csv/', views.export_analytics_csv, name='export_analytics_csv'),
    path('admin/dashboard/', views.admin_dashboard_overview, name='admin_dashboard'),
    path('admin/dashboard/genres/', views.admin_dashboard_genres, name='admin_dashboard_genres'),
    path('admin/dashboard/age-ratings/', views.admin_dashboard_age_ratings, name='admin_dashboard_age_ratings'),
    path('admin/dashboard/directors/', views.admin_dashboard_directors, name='admin_dashboard_directors'),
]