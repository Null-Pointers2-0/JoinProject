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


def subscription(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'users/parts/subscription.html')