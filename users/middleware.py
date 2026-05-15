from django.shortcuts import redirect
from django.urls import resolve, reverse

class AdminRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and getattr(request.user, 'type', None) == 'Staff Admin':
            
            try:
                current_url_name = resolve(request.path_info).url_name
            except Exception:
                current_url_name = None

            exempt_url_names = [
                'gestion_usuarios', 
                'crear_usuario_admin', 
                'logout', 
                'eliminar_usuario'
                ]
            
            if current_url_name not in exempt_url_names and not request.path.startswith('/static/'):
                return redirect(reverse('gestion_usuarios'))
        if request.user.is_authenticated and getattr(request.user, 'type', None) == 'Admin':
            try:
                current_url_name = resolve(request.path_info).url_name
            except Exception:
                current_url_name = None

            exempt_url_names = [
                'admin_dashboard', 
                'admin_dashboard_overview', 
                'admin_dashboard_genres', 
                'admin_dashboard_age_ratings', 
                'admin_dashboard_directors', 
                'export_analytics_csv',
                'logout',
                ]
            
            if current_url_name not in exempt_url_names and not request.path.startswith('/static/'):
                return redirect(reverse('admin_dashboard'))
        return self.get_response(request)