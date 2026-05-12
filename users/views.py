import csv
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
from web_app.models import Movie, Series, Contingut, API, CustomUser
from django.urls import reverse

# Create your views here.

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

def is_admin_or_staff(user):
    return user.type == 'Staff' or user.type == 'Admin'

@login_required(login_url='login')
@user_passes_test(is_admin_or_staff)
def export_analytics_csv(request):
    platform_id = request.GET.get('platform')
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    report_type = request.GET.get('type', 'internal') 

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
    platform_id = request.GET.get('platform')

    # 2. Obtener los ports de las plataformas suscritas
    subscribed_ports = list(request.user.subscriptions.values_list('port', flat=True))

    # 3. Si hay filtro de plataforma en la URL, verificar que pertenece a sus suscripciones
    if platform_id:
        try:
            platform_port = int(platform_id)
            # Solo usar ese filtro si el usuario tiene acceso
            active_ports = platform_port if platform_port in subscribed_ports else subscribed_ports
        except ValueError:
            active_ports = subscribed_ports[0]
    else:
        active_ports = API.objects.get(port=subscribed_ports[0]).id


    # 4. Obtener datos filtrados por las plataformas activas
    content_list = get_content_analytics(start_date, end_date, active_ports)
    genre_stats = get_genre_distribution(start_date, end_date, active_ports)
    age_stats = get_age_rating_distribution(start_date, end_date, active_ports)
    director_stats = get_director_top_list(start_date, end_date, active_ports)

    # 5. Pasar al template las plataformas suscritas (para el selector de filtros)
    subscribed_apis = request.user.subscriptions.all()

    context = {
        'content_list': content_list,
        'genre_stats': genre_stats,
        'age_stats': age_stats,
        'director_stats': director_stats,
        'platforms': subscribed_apis,       # Para el <select> del template
        'filters': {
            'start': start_date,
            'end': end_date,
            'platform': platform_id,        # El valor seleccionado actualmente
        }
    }

    return render(request, 'users/parts/dashboard_overview.html', context)

@login_required(login_url='login')
@user_passes_test(is_admin_or_staff)
def admin_dashboard_genres(request):
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    platform_id = request.GET.get('platform')
    print(API.objects.all())
    
    genre_stats = get_genre_distribution(start_date, end_date, platform_id)
    
    return render(request, 'users/parts/dashboard_genres.html', {
        'genre_stats': genre_stats,
        'filters': {'start': start_date, 'end': end_date, 'platform': platform_id},
        'platforms': API.objects.all()
    })

@login_required(login_url='login')
@user_passes_test(is_admin_or_staff)
def admin_dashboard_age_ratings(request):
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    platform_id = request.GET.get('platform')
    
    age_stats = get_age_rating_distribution(start_date, end_date, platform_id)
    
    return render(request, 'users/parts/dashboard_age_ratings.html', {
        'age_stats': age_stats,
        'filters': {'start': start_date, 'end': end_date, 'platform': platform_id},
        'platforms': API.objects.all()
    })

@login_required(login_url='login')
@user_passes_test(is_admin_or_staff)
def admin_dashboard_directors(request):
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    platform_id = request.GET.get('platform')
    
    director_stats = get_director_top_list(start_date, end_date, platform_id)
    
    return render(request, 'users/parts/dashboard_directors.html', {
        'director_stats': director_stats,
        'filters': {'start': start_date, 'end': end_date, 'platform': platform_id},
        'platforms': API.objects.all()
    })
