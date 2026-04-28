from django.shortcuts import render, redirect, get_object_or_404
from web_app.forms import CustomUserCreationForm
from web_app.models import AgeRating, Director, Genre, Movie
from web_app import utils
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login

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
        user = form.save()
        login(request, user)
        return redirect('home')
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

def catalog_view(request):
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

    context = {
        'movies': movies,
        'genres': genres,
        'directors': directors,
        'age_ratings': age_ratings,
    }

    return render(request, 'catalog.html', context)

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


def terms_use(request):
    return render(request, 'footer_legal/terms_use.html')

def privacy_policy(request):
    return render(request, 'footer_legal/privacy_policy.html')


