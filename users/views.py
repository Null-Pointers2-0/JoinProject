from django.shortcuts import render, redirect
from django.contrib import messages
from web_app.forms import CustomUserChangeForm
from web_app.models import Movie

# Create your views here.
def profile(request):
    if not request.user.is_authenticated:
        return redirect('login')
        
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Perfil actualizado correctamente!')
            return redirect(request.path)
    else:
        form = CustomUserChangeForm(instance=request.user)

    return render(request, 'users/profile/profile.html', {'form': form})

def history(request):
    if not request.user.is_authenticated:
        return redirect('login')
    movies = Movie.objects.all()
    return render(request, 'users/parts/history.html', {'movies': movies})

def followed(request):
    if not request.user.is_authenticated:
        return redirect('login')
    try:
        movies = request.user.profile.favorite_movies.all()
        series_list = request.user.profile.favorite_series.all()
    except:
        movies = []
        series_list = []
    return render(request, 'users/parts/followed.html', {'movies': movies, 'series_list': series_list})


def subscription(request):
    if not request.user.is_authenticated:
        return redirect('login')

    from web_app.models import API
    from django.contrib import messages as django_messages

    all_apis = API.objects.all().order_by('port')
    user_subscription_ids = set(request.user.subscriptions.values_list('id', flat=True))

    if request.method == 'POST':
        selected_ids = request.POST.getlist('subscriptions')
        request.user.subscriptions.set(API.objects.filter(id__in=selected_ids))
        django_messages.success(request, '¡Suscripciones actualizadas correctamente!')
        return redirect('suscription')

    return render(request, 'users/parts/subscription.html', {
        'all_apis': all_apis,
        'user_subscription_ids': user_subscription_ids,
    })