import csv
import os
from django.http import HttpResponse
import csv
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from .services import (
    get_content_analytics, 
    format_analytics_for_csv,
    get_genre_distribution,
    get_age_rating_distribution,
    get_director_top_list
)
from django.shortcuts import render, redirect
from django.contrib import messages
from web_app.forms import CustomUserChangeForm
from web_app.models import Movie, Series
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from django.shortcuts import render, redirect, get_object_or_404
from web_app.forms import CustomUserAdminCreationForm
from web_app.models import CustomUser, Movie, UserProfile, Series
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from web_app.models import Movie, Series, Contingut, API, CustomUser
from django.urls import reverse

def is_consumer(user):
    return user.type == 'Consumer'

@login_required(login_url='login')
@user_passes_test(is_consumer)
def user_profile(request):
        
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Perfil actualizado correctamente!')
            return redirect(request.path)
    else:
        form = CustomUserChangeForm(instance=request.user)

    return render(request, 'users/profile/user_profile.html', {'form': form})

@login_required(login_url='login')
@user_passes_test(is_consumer)
def history(request):
    movies = Movie.objects.all()
    return render(request, 'users/parts/history.html', {'movies': movies})

@login_required(login_url='login')
@user_passes_test(is_consumer)
def followed(request):
    profile, _ = request.user.profile, True
    preferits_ids = profile.preferits.values_list('id', flat=True)
    movies = Movie.objects.filter(contingut_id__in=preferits_ids)
    series_list = Series.objects.filter(contingut_id__in=preferits_ids)
    return render(request, 'users/parts/followed.html', {'movies': movies, 'series_list': series_list})

@login_required(login_url='login')
@user_passes_test(is_consumer)
def subscription(request):
    all_apis = API.objects.all().order_by('port')
    user_subscription_ids = set(request.user.subscriptions.values_list('id', flat=True))

    if request.method == 'POST':
        selected_ids = request.POST.getlist('subscriptions')
        request.user.subscriptions.set(API.objects.filter(id__in=selected_ids))
        messages.success(request, '¡Suscripciones actualizadas correctamente!')
        return redirect('suscription')

    return render(request, 'users/parts/subscription.html', {
        'all_apis': all_apis,
        'user_subscription_ids': user_subscription_ids,
    })

@user_passes_test(lambda u: u.is_superuser)
def gestion_usuarios(request):
    if not request.user.is_authenticated:
        return redirect('login')
    users = CustomUser.objects.all()
    exclude_staff_admin = users.exclude(type='Staff Admin')
    return render(request, 'users/parts/users_table.html', {'users': exclude_staff_admin})

@user_passes_test(lambda u: u.is_superuser)
def eliminar_usuario(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        user.delete()
        messages.success(request, f"Usuario '{user.username}' eliminado correctamente.")
        return redirect('gestion_usuarios')

def test_env_vars(request):
    # Esto leerá las variables directamente del servidor de Render
    mail_user = os.getenv('MAIL')
    mail_pw = os.getenv('MAIL_PW')
    
    # Comprobamos la longitud de la contraseña por seguridad en lugar de imprimirla
    pw_status = "NO CONFIGURADA" if not mail_pw else f"Configurada ({len(mail_pw)} caracteres)"
    
    debug_info = f"""
    ESTADO DE VARIABLES DE ENTORNO EN PRODUCCIÓN:
    ---------------------------------------------
    MAIL: {mail_user}
    MAIL_PW: {pw_status}
    DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}
    """
    
    return HttpResponse(debug_info, content_type="text/plain")

@user_passes_test(lambda u: u.is_superuser)
def crear_usuario_admin(request):
    if request.method == 'POST':
        test_env_vars(request)  # Llamada a la función de prueba para verificar las variables de entorno
        form = CustomUserAdminCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            
            temp_password = get_random_string(length=12)
            user.set_password(temp_password)
            user.save()
            
            UserProfile.objects.get_or_create(user=user)
            
            asunto = 'Bienvenido a StreamSync - Tus Credenciales'
            mensaje = f"""
            Hola {user.username},
            
            Se ha creado una cuenta para ti en StreamSync.
            Aquí tienes tus credenciales de acceso:
            
            Usuario: {user.username}
            Contraseña temporal: {temp_password}
            
            Por seguridad, te recomendamos cambiarla en tu perfil tras iniciar sesión.
            """
            
            try:
                send_mail(
                    asunto,
                    mensaje,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                messages.success(request, f"Usuario creado y correo enviado a {user.email}")
            except Exception as e:
                messages.warning(request, "Usuario creado, pero hubo un error al enviar el correo.")

            return redirect('gestion_usuarios')
    else:
        form = CustomUserAdminCreationForm()
    
    return render(request, 'users/parts/create_user.html', {'form': form})



def is_admin_or_staff(user):
    return user.type == 'Staff' or user.type == 'Admin'

@login_required(login_url='login')
@user_passes_test(is_admin_or_staff)
def export_analytics_csv(request):
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    report_type = request.GET.get('type', 'internal') 
    
    # Obtener la plataforma del usuario (ya que solo tiene una)
    subscribed_ports = list(request.user.subscriptions.values_list('port', flat=True))
    platform_id = API.objects.get(port=subscribed_ports[0]).id if subscribed_ports else None

    raw_data = get_content_analytics(
        start_date=start_date,
        end_date=end_date,
        plataform_id=platform_id
    )


    is_b2b = (report_type == 'b2b')
    clean_data = format_analytics_for_csv(raw_data, is_b2b_report=is_b2b)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="analytics_report.csv"'

    writer = csv.writer(response)

    writer.writerow(['Title', 'Genre', 'Age Rating', 'Year', 'Director', 'Platform', 'Total Views', 'Total Favorites'])

    for item in clean_data:
        writer.writerow([
            item['title'], item['genre'], item['age_rating'], 
            item['year'], item['director'], item['platform'], 
            item['views'], item['favorites']
        ])
    
    return response


@login_required(login_url='login')
@user_passes_test(is_admin_or_staff)
def admin_dashboard_overview(request):
    # 1. Capturar filtros de la URL
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')

    # 2. Obtener el port de la plataforma suscrita
    subscribed_ports = list(request.user.subscriptions.values_list('port', flat=True))
    active_ports = API.objects.get(port=subscribed_ports[0]).id if subscribed_ports else None

    # 4. Obtener datos filtrados por las plataformas activas
    content_list = get_content_analytics(start_date, end_date, active_ports)
    genre_stats = get_genre_distribution(start_date, end_date, active_ports)
    age_stats = get_age_rating_distribution(start_date, end_date, active_ports)
    director_stats = get_director_top_list(start_date, end_date, active_ports)

    # 5. Pasar al template las plataformas suscritas
    subscribed_apis = request.user.subscriptions.all()

    context = {
        'content_list': content_list,
        'genre_stats': genre_stats,
        'age_stats': age_stats,
        'director_stats': director_stats,
        'platforms': subscribed_apis,
        'filters': {
            'start': start_date,
            'end': end_date,
        }
    }

    return render(request, 'users/parts/dashboard_overview.html', context)

@login_required(login_url='login')
@user_passes_test(is_admin_or_staff)
def admin_dashboard_genres(request):
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    
    subscribed_ports = list(request.user.subscriptions.values_list('port', flat=True))
    active_ports = API.objects.get(port=subscribed_ports[0]).id if subscribed_ports else None
    
    genre_stats = get_genre_distribution(start_date, end_date, active_ports)
    
    return render(request, 'users/parts/dashboard_genres.html', {
        'genre_stats': genre_stats,
        'filters': {'start': start_date, 'end': end_date},
        'platforms': API.objects.all()
    })

@login_required(login_url='login')
@user_passes_test(is_admin_or_staff)
def admin_dashboard_age_ratings(request):
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    
    subscribed_ports = list(request.user.subscriptions.values_list('port', flat=True))
    active_ports = API.objects.get(port=subscribed_ports[0]).id if subscribed_ports else None
    
    age_stats = get_age_rating_distribution(start_date, end_date, active_ports)
    
    return render(request, 'users/parts/dashboard_age_ratings.html', {
        'age_stats': age_stats,
        'filters': {'start': start_date, 'end': end_date},
        'platforms': API.objects.all()
    })

@login_required(login_url='login')
@user_passes_test(is_admin_or_staff)
def admin_dashboard_directors(request):
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')

    subscribed_ports = list(request.user.subscriptions.values_list('port', flat=True))
    active_ports = API.objects.get(port=subscribed_ports[0]).id if subscribed_ports else None
    
    director_stats = get_director_top_list(start_date, end_date, active_ports)
    
    return render(request, 'users/parts/dashboard_directors.html', {
        'director_stats': director_stats,
        'filters': {'start': start_date, 'end': end_date},
        'platforms': API.objects.all()
    })
