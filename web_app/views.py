from django.shortcuts import render, redirect, get_object_or_404
from web_app.forms import CustomUserCreationForm
from web_app.models import Movie


def home(request):
    return render(request, "home/home.html")


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