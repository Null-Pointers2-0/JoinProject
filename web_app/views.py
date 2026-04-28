from django.shortcuts import render, redirect, get_object_or_404
from web_app.forms import CustomUserCreationForm
from web_app.models import AgeRating, Director, Genre, Movie, UserProfile
from web_app import utils
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from django.core.paginator import Paginator

def home(request):
    movies = Movie.objects.all()

    search_query = request.GET.get('q', '')
    genre_filter = request.GET.get('genre', '')
    director_filter = request.GET.get('director', '')
    age_rating_filter = request.GET.get('age_rating', '')

    if search_query:
        movies = movies.filter(title__icontains=search_query)

    if genre_filter:
        movies = movies.filter(genre__name=genre_filter)

    if director_filter:
        movies = movies.filter(director__name=director_filter)

    if age_rating_filter:
        movies = movies.filter(age_rating__description=age_rating_filter)

    genres = Genre.objects.values_list('name', flat=True).distinct()
    directors = Director.objects.values_list('name', flat=True).distinct()
    age_ratings = AgeRating.objects.values_list('description', flat=True).distinct()

    # Paginació
    paginator = Paginator(movies, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'movies': page_obj,
        'genres': genres,
        'directors': directors,
        'age_ratings': age_ratings,
        'search_query': search_query,
        }

    return render(request, "home/home.html", context)


def register_view(request):
    form = CustomUserCreationForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('login')
    return render(request, 'identify/register.html', {'form': form})


def user_setting(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'User/user_types/user_client.html')


def movie_detail(request, movie_id):
    movie = get_object_or_404(Movie, pk=movie_id)

    context = {
        'movie': movie,
        'recommendations': movie.get_similar_by_genre(limit=5)
    }
    return render(request, 'movie_detail.html', context)


def movie_detail(request, pk):
    movie = get_object_or_404(Movie, id=pk)

    is_favorite = False
    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        if isinstance(movie, Movie):
            is_favorite = movie in profile.favorite_movies.all()
        else:
            is_favorite = movie in profile.favorite_series.all()

    return render(request, 'details.html', {
        'content': movie,
        'is_favorite': is_favorite
    })

def series_detail(request, pk):
    series = get_object_or_404(Series, id=pk)

    is_favorite = False
    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        if isinstance(series, Movie):
            is_favorite = series in profile.favorite_movies.all()
        else:
            is_favorite = series in profile.favorite_series.all()

    return render(request, 'details.html', {
        'content': series,
        'is_favorite': is_favorite
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
        "linked_platforms": [],  # Pendiente: crear modelo de plataformas en el futuro
        "followed_content_ids": followed_movie_ids
    }

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from .models import Movie, Series, UserProfile

@login_required
def toggle_favorite(request, pk):
    if request.method == 'POST':
        # 1. Intentamos determinar si es película o serie
        # Podríamos pasar un parámetro extra o intentar buscar en ambos modelos
        movie = Movie.objects.filter(id=pk).first()
        series = Series.objects.filter(id=pk).first()
        
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        status = ""

        if movie:
            if movie in profile.favorite_movies.all():
                profile.favorite_movies.remove(movie)
                status = "removed"
            else:
                profile.favorite_movies.add(movie)
                status = "added"
        elif series:
            if series in profile.favorite_series.all():
                profile.favorite_series.remove(series)
                status = "removed"
            else:
                profile.favorite_series.add(series)
                status = "added"
        else:
            return JsonResponse({'error': 'Contenido no encontrado'}, status=404)

        return JsonResponse({'status': status})
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)
