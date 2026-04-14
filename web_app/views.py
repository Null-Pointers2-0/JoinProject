from django.shortcuts import render, redirect
from web_app.forms import CustomUserCreationForm
from web_app.models import AgeRating, Director, Genre, Movie

def home(request):
    return render(request, "home/home.html")

def register_view(request):
    form = CustomUserCreationForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('login')
    return render(request, 'identify/register.html', {'form': form})

""" 
def profile(request):
    if not request.user.is_authenticated:
        return redirect('login')
    '''if request.user.is_client:
        return render(request, 'User/user_types/user_client.html')
    elif request.user.is_admin:
        return render(request, 'User/user_types/user_admin.html')
    elif request.user.is_tecnical:
        return render(request, 'User/user_types/user_tecnical.html')'''
    return render(request, 'User/user_parts/profile.html')
    #return render(request, 'User/user_setting.html')

def history(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'User/user_parts/history.html') 
"""

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
    
    return render(request, 'catalog/catalog.html', context)
