from django.shortcuts import render, redirect, get_object_or_404
from web_app.forms import CustomUserCreationForm
from web_app.models import AgeRating, Director, Genre, Movie, UserProfile, Series
from web_app import utils
from itertools import chain
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.core.paginator import Paginator

def home(request):
    movies = Movie.objects.all()
    series = Series.objects.all()

    search_query = request.GET.get('q', '')
    genre_filter = request.GET.get('genre', '')
    director_filter = request.GET.get('director', '')
    age_rating_filter = request.GET.get('age_rating', '')

    if search_query:
        movies = movies.filter(title__icontains=search_query)
        series = series.filter(title__icontains=search_query)

    if genre_filter:
        movies = movies.filter(genre__name=genre_filter)
        series = series.filter(genre__name=genre_filter)

    if director_filter:
        movies = movies.filter(director__name=director_filter)
        series = series.filter(director__name=director_filter)

    if age_rating_filter:
        movies = movies.filter(age_rating__description=age_rating_filter)
        series = series.filter(age_rating__description=age_rating_filter)

    movies_list = list(movies)
    for m in movies_list:
        m.content_type = 'movie'
        
    series_list = list(series)
    for s in series_list:
        s.content_type = 'series'

    combined_results = list(chain(movies_list, series_list))

    paginator = Paginator(combined_results, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    genres = Genre.objects.values_list('name', flat=True).distinct()
    directors = Director.objects.values_list('name', flat=True).distinct()
    age_ratings = AgeRating.objects.values_list('description', flat=True).distinct()

    context = {
        'items': page_obj,
        'genres': genres,
        'directors': directors,
        'age_ratings': age_ratings,
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
    
    available_apis = [m.api for m in Movie.objects.filter(title__iexact=movie.title).select_related('api') if m.api]
    
    is_favorite = False
    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        is_favorite = movie in profile.favorite_movies.all()

    return render(request, 'Details/details_movie.html', {
        'content': movie,
        'is_favorite': is_favorite,
        'available_apis': available_apis
    })

def series_detail(request, pk):
    series = get_object_or_404(Series, id=pk)

    available_apis = [s.api for s in Series.objects.filter(title__iexact=series.title).select_related('api') if s.api]

    is_favorite = False
    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        is_favorite = series in profile.favorite_series.all()

    return render(request, 'Details/details_serie.html', {
        'content': series,
        'is_favorite': is_favorite,
        'available_apis': available_apis
    })

@login_required(login_url='/login/')
def api_user_profile(request):
    user = request.user
    followed_movie_ids = list(user.favorite_movies.values_list('movie_id', flat=True))
    response_data = {
        "personal_info": {
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name
        },
        "linked_platforms": [],
        "followed_content_ids": followed_movie_ids
    }

@login_required
def toggle_movie_favorite(request, pk):
    if request.method == 'POST':
        movie = get_object_or_404(Movie, id=pk)
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        
        if movie in profile.favorite_movies.all():
            profile.favorite_movies.remove(movie)
            status = "removed"
        else:
            profile.favorite_movies.add(movie)
            status = "added"
        return JsonResponse({'status': status})
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@login_required
def toggle_series_favorite(request, pk):
    if request.method == 'POST':
        series = get_object_or_404(Series, id=pk)
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        
        if series in profile.favorite_series.all():
            profile.favorite_series.remove(series)
            status = "removed"
        else:
            profile.favorite_series.add(series)
            status = "added"
        return JsonResponse({'status': status})
    return JsonResponse({'error': 'Método no permitido'}, status=405)

def terms_use(request):
    return render(request, 'footer_legal/terms_use.html')

def privacy_policy(request):
    return render(request, 'footer_legal/privacy_policy.html')


