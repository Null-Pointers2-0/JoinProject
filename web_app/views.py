from django.shortcuts import render, redirect
from web_app.forms import CustomUserCreationForm

def home(request):
    return render(request, "home/home.html")

def register_view(request):
    form = CustomUserCreationForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('login')
    return render(request, 'register.html', {'form': form})