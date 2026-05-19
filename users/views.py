import csv
import os
import resend

from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.crypto import get_random_string

from web_app.forms import CustomUserChangeForm, CustomUserAdminCreationForm
from web_app.models import CustomUser, Movie, Series, UserProfile, API, Visualitzacio
from .services import (
    get_content_analytics, 
    format_analytics_for_csv,
    get_genre_distribution,
    get_age_rating_distribution,
    get_director_top_list,
    PII_COLUMNS,
    validate_gdpr_compliance,
)
from django.core.paginator import Paginator
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

# --- UTILS ---

def is_consumer(user):
    return user.type == 'Consumer'

def is_admin_or_staff(user):
    return user.type in ['Staff', 'Admin', 'Staff Admin']

def get_active_platform_ids(user):
    """
    Devuelve de forma segura una lista con los IDs de las plataformas
    a las que el administrador/staff tiene acceso.
    """
    subscribed_ports = list(user.subscriptions.values_list('port', flat=True))
    if not subscribed_ports:
        return []
    return list(API.objects.filter(port__in=subscribed_ports).values_list('id', flat=True))


# --- VISTAS DE CONSUMIDOR ---

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
    # OPTIMIZACIÓN: Buscamos en el modelo real de visualizaciones y hacemos Eager Loading
    visualizaciones = Visualitzacio.objects.filter(user=request.user).select_related(
        'contingut__movie', 'contingut__series'
    ).prefetch_related('contingut__apis').order_by('-data_visualitzacio')
    
    return render(request, 'users/parts/history.html', {'visualizaciones': visualizaciones})

@login_required(login_url='login')
@user_passes_test(is_consumer)
def followed(request):
    profile = request.user.profile
    preferits_ids = profile.preferits.values_list('id', flat=True)
    
    # OPTIMIZACIÓN N+1: Aplicamos prefetch y select_related para evitar cuellos de botella
    movies = Movie.objects.filter(contingut_id__in=preferits_ids).select_related(
        'contingut__genere', 'contingut__director'
    ).prefetch_related('contingut__apis')
    
    series_list = Series.objects.filter(contingut_id__in=preferits_ids).select_related(
        'contingut__genere', 'contingut__director'
    ).prefetch_related('contingut__apis')
    
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
        return redirect('subscription') # Corregido typo en el nombre de la URL ('suscription' a 'subscription')

    return render(request, 'users/parts/subscription.html', {
        'all_apis': all_apis,
        'user_subscription_ids': user_subscription_ids,
    })

@login_required(login_url='login')
@user_passes_test(lambda u: u.is_superuser)
def staff_admin_panel(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return redirect('gestion_usuarios')

@user_passes_test(lambda u: u.is_superuser)
def gestion_usuarios(request):
    if not request.user.is_authenticated:
        return redirect('login')
    users = CustomUser.objects.all()
    exclude_staff_admin = users.exclude(type='Staff Admin')
    filter_type = request.GET.get('tipo')
    if filter_type:
        exclude_staff_admin = exclude_staff_admin.filter(type=filter_type)

    paginator = Paginator(exclude_staff_admin, 20)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'users/parts/users_table.html', {'users': page_obj})

@user_passes_test(lambda u: u.is_superuser)
def eliminar_usuario(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        user.delete()
        messages.success(request, f"Usuario '{user.username}' eliminado correctamente.")
        return redirect('gestion_usuarios')

@user_passes_test(lambda u: u.is_superuser)
def crear_usuario_admin(request):
    if request.method == 'POST':
        form = CustomUserAdminCreationForm(request.POST)
        if form.is_valid():
            # 1. Creamos la instancia en memoria (sin enviarla a PostgreSQL aún)
            user = form.save(commit=False)
            
            # 2. Generamos y encriptamos la contraseña temporal
            temp_password = get_random_string(length=12)
            user.set_password(temp_password)
            
            # 3. Guardamos el usuario en la BD (ahora ya tiene un ID asignado)
            user.save()
            
            # 4. MAGIA DE DJANGO: Ejecutamos el guardado de la relación ManyToMany (Suscripciones)
            form.save_m2m()
            
            # 5. Creamos su perfil base
            UserProfile.objects.get_or_create(user=user)

            resend.api_key = os.getenv('RESEND_KEY')
            
            try:
                r = resend.Emails.send({
                    "from": "onboarding@resend.dev",
                    "to": [user.email],
                    "subject": "Bienvenido a StreamSync - Tus Credenciales",
                    "html": f"""
                    <p>Hola {user.username},</p>
                    <p>Se ha creado una cuenta para ti en StreamSync.</p>
                    <p>Aquí tienes tus credenciales de acceso:</p>
                    <ul>
                        <li>Usuario: {user.username}</li>
                        <li>Contraseña temporal: {temp_password}</li>
                    </ul>
                    <p>Por seguridad, te recomendamos cambiarla en tu perfil tras iniciar sesión.</p>
                    """
                })
                messages.success(request, f"Usuario '{user.username}' creado correctamente y correo enviado.")
            except Exception as e:
                import logging
                logging.error(f"Fallo enviando correo Resend: {e}")
                messages.warning(request, "Usuario creado, pero hubo un error al enviar el correo.")

            return redirect('gestion_usuarios')
    else:
        form = CustomUserAdminCreationForm()
    
    return render(request, 'users/parts/create_user.html', {'form': form})

# --- DASHBOARDS Y ANALÍTICAS ---

@login_required(login_url='login')
@user_passes_test(is_admin_or_staff)
def export_analytics_csv(request):
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    report_type = request.GET.get('type', 'internal') 
    
    platform_ids = get_active_platform_ids(request.user)

    raw_data = get_content_analytics(
        start_date=start_date,
        end_date=end_date,
        plataform_id=platform_ids # Ahora pasamos una lista de IDs segura
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
    
    for item in clean_data:
        leaked = PII_COLUMNS & item.keys()
        if leaked:
            raise ValueError(f"CRITICAL: PII columns {leaked} would be exported!")
    
    validate_gdpr_compliance(clean_data, is_b2b_report=is_b2b)
    
    return response


@login_required(login_url='login')
@user_passes_test(is_admin_or_staff)
def admin_dashboard_overview(request):
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')

    platform_ids = get_active_platform_ids(request.user)

    content_list = get_content_analytics(start_date, end_date, platform_ids)
    genre_stats = get_genre_distribution(start_date, end_date, platform_ids)
    age_stats = get_age_rating_distribution(start_date, end_date, platform_ids)
    director_stats = get_director_top_list(start_date, end_date, platform_ids)

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
    platform_ids = get_active_platform_ids(request.user)
    
    genre_stats = get_genre_distribution(start_date, end_date, platform_ids)
    
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
    platform_ids = get_active_platform_ids(request.user)
    
    age_stats = get_age_rating_distribution(start_date, end_date, platform_ids)
    
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
    platform_ids = get_active_platform_ids(request.user)
    
    director_stats = get_director_top_list(start_date, end_date, platform_ids)
    
    return render(request, 'users/parts/dashboard_directors.html', {
        'director_stats': director_stats,
        'filters': {'start': start_date, 'end': end_date},
        'platforms': API.objects.all()
    })

@user_passes_test(lambda u: u.is_superuser)
def gestion_cartelleres(request):
    if not request.user.is_authenticated:
        return redirect('login')

    plataforma_id = request.GET.get('plataforma')
    search_query = request.GET.get('q', '')
    contenidos_qs = Contingut.objects.all().order_by('titol')

    if plataforma_id:
        contenidos_qs = contenidos_qs.filter(apis__id=plataforma_id)
    if search_query:
        contenidos_qs = contenidos_qs.filter(titol__icontains=search_query)

    # Agrupar per títol perquè la base de dades pot tenir duplicats per plataforma
    seen = {}
    grouped_contenidos = []
    for c in contenidos_qs.prefetch_related('apis'):
        if c.titol not in seen:
            c.all_apis = list(c.apis.all())
            seen[c.titol] = c
            grouped_contenidos.append(c)
        else:
            for api in c.apis.all():
                if api not in seen[c.titol].all_apis:
                    seen[c.titol].all_apis.append(api)

    paginator = Paginator(grouped_contenidos, 20)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    plataformas = API.objects.all()

    return render(request, 'users/parts/gestion_cartelleres.html', {
        'contenidos': page_obj,
        'plataformas': plataformas,
        'selected_plataforma': plataforma_id,
        'search_query': search_query,
    })


@user_passes_test(lambda u: u.is_superuser)
def editar_cartellera(request, contingut_id):
    if not request.user.is_authenticated:
        return redirect('login')

    contingut = get_object_or_404(Contingut, id=contingut_id)

    if request.method == 'POST':
        poster_path = request.POST.get('poster_path', '').strip()
        contingut.poster_path = poster_path if poster_path else None
        contingut.save()
        messages.success(request, f"Cartellera actualitzada per a '{contingut.titol}'")
        return redirect('gestion_cartelleres')

    return render(request, 'users/parts/editar_cartellera.html', {
        'contingut': contingut,
    })
