from django.shortcuts import render, redirect, get_object_or_404
from web_app.forms import CustomUserCreationForm
from web_app.models import AgeRating, API, Director, Genre, Movie, UserProfile, Series, Contingut
from web_app import utils
from itertools import chain
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.core.paginator import Paginator

def home(request):
    movies = Movie.objects.select_related('contingut', 'contingut__genere', 'contingut__director', 'contingut__age_rating').prefetch_related('contingut__api').all()
    series = Series.objects.select_related('contingut', 'contingut__genere', 'contingut__director', 'contingut__age_rating').prefetch_related('contingut__api').all()

    search_query = request.GET.get('q', '')
    genre_filter = request.GET.get('genre', '')
    director_filter = request.GET.get('director', '')
    age_rating_filter = request.GET.get('age_rating', '')
    platform_filter = request.GET.get('platform', '')  # value = API port

    if search_query:
        movies = movies.filter(contingut__titol__icontains=search_query)
        series = series.filter(contingut__titol__icontains=search_query)

    if genre_filter:
        movies = movies.filter(contingut__genere__name=genre_filter)
        series = series.filter(contingut__genere__name=genre_filter)

    if director_filter:
        movies = movies.filter(contingut__director__name=director_filter)
        series = series.filter(contingut__director__name=director_filter)

    if age_rating_filter:
        movies = movies.filter(contingut__age_rating__codi=age_rating_filter)
        series = series.filter(contingut__age_rating__codi=age_rating_filter)

    if platform_filter:
        movies = movies.filter(api__port=platform_filter)
        series = series.filter(api__port=platform_filter)

    unique_results = []
    seen_keys = set()

    for cont in chain(movies, series):
        is_movie = isinstance(cont, Movie)
        type_str = 'movie' if is_movie else 'series'
        key = (cont.title.lower(), type_str)
        if key not in seen_keys:
            cont.content_type = type_str
            cont.available_platforms = [cont.contingut.api] if cont.contingut.api else []
            unique_results.append(cont)
            seen_keys.add(key)
    '''
    for m in movies:
        key = (m.title.lower(), 'movie')
        if key not in seen_keys:
            m.content_type = 'movie'
            # Collect all platforms (API objects) this title is available on
            m.available_platforms = list(
                API.objects.filter(
                    contingut__titol__iexact=m.title
                ).distinct()
            )
            unique_results.append(m)
            seen_keys.add(key)

    for s in series:
        key = (s.title.lower(), 'series')
        if key not in seen_keys:
            s.content_type = 'series'
            # Collect all platforms (API objects) this title is available on
            s.available_platforms = list(
                API.objects.filter(
                    contingut__titol__iexact=s.title
                ).distinct()
            )
            unique_results.append(s)
            seen_keys.add(key)
'''
    paginator = Paginator(unique_results, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    genres = Genre.objects.values_list('name', flat=True).distinct()
    directors = Director.objects.values_list('name', flat=True).distinct()
    age_ratings = AgeRating.objects.values_list('codi', flat=True).distinct()
    platforms = API.objects.all()

    context = {
        'items': page_obj,
        'genres': genres,
        'directors': directors,
        'age_ratings': age_ratings,
        'platforms': platforms,
        'search_query': search_query,
    }

    return render(request, "home/home.html", context)

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

    return render(request, 'Details/details_movie.html', {
        'content': movie,
        'is_favorite': is_favorite,
        'available_apis': available_apis
    })

def series_detail(request, pk):
    series = get_object_or_404(Series, id=pk)

    available_apis = [s.contingut.api for s in Series.objects.filter(contingut__titol__iexact=series.title).select_related('contingut__api') if s.contingut.api]

    is_favorite = False
    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        is_favorite = series.contingut in profile.preferits.all()

    return render(request, 'Details/details_serie.html', {
        'content': series,
        'is_favorite': is_favorite,
        'available_apis': available_apis
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

def terms_use(request):
    return render(request, 'footer_legal/terms_use.html')

def privacy_policy(request):
    return render(request, 'footer_legal/privacy_policy.html')
