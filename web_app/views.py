from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from django.shortcuts import render, redirect, get_object_or_404
from web_app.forms import CustomUserAdminCreationForm, CustomUserCreationForm
from web_app.models import AgeRating, API, CustomUser, Director, Genre, Movie, UserProfile, Series, Contingut, AgeRating, Valoracio
from web_app import utils
from itertools import chain
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import login
from django.core.paginator import Paginator
from django.db.models import Avg, Count
from django.template.loader import render_to_string

def home(request):
    """Carga instantánea del esqueleto de la página."""
    context = {
        'genres': Genre.objects.values_list('name', flat=True).distinct(),
        'directors': Director.objects.values_list('name', flat=True).distinct(),
        'platforms': API.objects.all(),
        'age_ratings': AgeRating.objects.values_list('codi', flat=True).distinct(),
    }
    return render(request, "home/home.html", context)

def search_content_ajax(request):
    """Procesamiento asíncrono optimizado."""
    try:
        search_query = request.GET.get('q', '')
        genre_filter = request.GET.get('genre', '')
        director_filter = request.GET.get('director', '')
        platform_filter = request.GET.get('platform', '')
        age_rating_filter = request.GET.get('age_rating', '')


        movies = Movie.objects.select_related('contingut__genere', 'contingut__director', 'contingut__age_rating', 'contingut__api').all()
        series = Series.objects.select_related('contingut__genere', 'contingut__director', 'contingut__age_rating', 'contingut__api').all()

        if search_query:
            movies = movies.filter(contingut__titol__icontains=search_query)
            series = series.filter(contingut__titol__icontains=search_query)
        if genre_filter:
            movies = movies.filter(contingut__genere__name=genre_filter)
            series = series.filter(contingut__genere__name=genre_filter)
        if director_filter:
            movies = movies.filter(contingut__director__name=director_filter)
            series = series.filter(contingut__director__name=director_filter)
        if platform_filter: 
            movies = movies.filter(contingut__api__port=platform_filter)
            series = series.filter(contingut__api__port=platform_filter)
        if age_rating_filter:
            movies = movies.filter(contingut__age_rating__codi=age_rating_filter)
            series = series.filter(contingut__age_rating__codi=age_rating_filter)

        all_content = list(chain(movies, series))
        unique_results = []
        seen = set()

        for item in all_content:
            title_key = item.contingut.titol.lower()
            if title_key not in seen:
                item.content_type = 'movie' if isinstance(item, Movie) else 'series'
                item.available_platforms = [m.contingut.api for m in type(item).objects.filter(contingut__titol__iexact=item.title).select_related('contingut__api') if m.contingut.api]
                unique_results.append(item)
                seen.add(title_key)

        paginator = Paginator(unique_results, 20)
        page_obj = paginator.get_page(request.GET.get('page', 1))

        html_cards = render_to_string('home/includes/result_fragment.html', {'items': page_obj}, request=request)
        html_pagination = render_to_string('home/home_parts/paginator.html', {'items': page_obj}, request=request)

        return JsonResponse({
            'html': html_cards,
            'pagination_html': html_pagination
        })

    except Exception as e:
        import logging
        logging.error(f"Error en AJAX: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

def register_view(request):
    form = CustomUserCreationForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        platforms = form.cleaned_data.get('platforms')
        if platforms:
            user.subscriptions.set(platforms)
        login(request, user)
        return redirect('home')
    return render(request, 'identify/register.html', {'form': form})

@login_required(login_url='login')
def redirect_by_role(request):
    user = request.user

    if user.type == 'Admin':
        return redirect('admin_dashboard')
    elif user.type == 'Staff':
        return redirect('user_profile')
    elif user.type == 'Consumer':
        return redirect('home')
    elif user.type == 'Staff Admin':
        return redirect('gestion_usuarios')
    else:
        return redirect('home')


def user_setting(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'User/user_types/user_client.html')

def movie_detail(request, pk):
    movie = get_object_or_404(Movie, id=pk)
    
    available_apis = [m.contingut.api for m in Movie.objects.filter(contingut__titol__iexact=movie.title).select_related('contingut__api') if m.contingut.api]
    
    is_favorite = False
    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        is_favorite = movie.contingut in profile.preferits.all()

    reviews = Valoracio.objects.filter(contingut=movie.contingut).order_by('-creada_a')
    review_stats = reviews.aggregate(avg_rating=Avg('puntuacio'), total_reviews=Count('id'))

    return render(request, 'Details/details_movie.html', {
        'content': movie,
        'is_favorite': is_favorite,
        'available_apis': available_apis,
        'reviews': reviews,
        'avg_rating': review_stats['avg_rating'],
        'total_reviews': review_stats['total_reviews'],
        'recommendations': movie.get_similar_by_genre(limit=4)
    })

def series_detail(request, pk):
    series = get_object_or_404(Series, id=pk)

    available_apis = [s.contingut.api for s in Series.objects.filter(contingut__titol__iexact=series.title).select_related('contingut__api') if s.contingut.api]

    is_favorite = False
    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        is_favorite = series.contingut in profile.preferits.all()

    reviews = Valoracio.objects.filter(contingut=series.contingut).order_by('-creada_a')
    review_stats = reviews.aggregate(avg_rating=Avg('puntuacio'), total_reviews=Count('id'))

    return render(request, 'Details/details_serie.html', {
        'content': series,
        'is_favorite': is_favorite,
        'available_apis': available_apis,
        'reviews': reviews,
        'avg_rating': review_stats['avg_rating'],
        'total_reviews': review_stats['total_reviews'],
    })


@login_required(login_url='/login/')
def api_user_profile(request):
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)
    followed_contingut_ids = list(profile.preferits.values_list('id', flat=True))
    response_data = {
        "personal_info": {
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name
        },
        "linked_platforms": [],
        "followed_content_ids": followed_contingut_ids
    }
    return JsonResponse(response_data)

    #return JsonResponse(response_data)

@login_required
def toggle_movie_favorite(request, pk):
    if request.method == 'POST':
        movie = get_object_or_404(Movie, id=pk)
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        
        if movie.contingut in profile.preferits.all():
            profile.preferits.remove(movie.contingut)
            status = "removed"
        else:
            profile.preferits.add(movie.contingut)
            status = "added"
        return JsonResponse({'status': status})
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@login_required
def toggle_series_favorite(request, pk):
    if request.method == 'POST':
        series = get_object_or_404(Series, id=pk)
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        
        if series.contingut in profile.preferits.all():
            profile.preferits.remove(series.contingut)
            status = "removed"
        else:
            profile.preferits.add(series.contingut)
            status = "added"
        return JsonResponse({'status': status})
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required
def submit_review(request, contingut_id):
    if request.method == 'POST':
        puntuacio = request.POST.get('rating')
        comentari = request.POST.get('comment', '')

        contingut = get_object_or_404(Contingut, id=contingut_id)

        if puntuacio:
            Valoracio.objects.update_or_create(
                user=request.user,
                contingut=contingut,
                defaults={
                    'puntuacio': int(puntuacio),
                    'comentari': comentari
                }
            )

    return redirect(request.META.get('HTTP_REFERER', 'home'))

def terms_use(request):
    return render(request, 'footer_legal/terms_use.html')

def privacy_policy(request):
    return render(request, 'footer_legal/privacy_policy.html')
