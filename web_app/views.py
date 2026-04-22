from django.shortcuts import render, redirect, get_object_or_404
from web_app.forms import CustomUserCreationForm
from web_app.models import AgeRating, Director, Genre, Movie
from web_app import utils
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


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

    context = {
        'movies': movies,
        'genres': genres,
        'directors': directors,
        'age_ratings': age_ratings,
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


