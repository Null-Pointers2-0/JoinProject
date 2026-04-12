from django.shortcuts import render, redirect
from web_app.forms import CustomUserCreationForm

def home(request):
    return render(request, "home/home.html")

def register_view(request):
    form = CustomUserCreationForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('login')
    return render(request, 'identify/register.html', {'form': form})

def profile(request):
    if not request.user.is_authenticated:
        return redirect('login')
    '''if request.user.is_client:
        return render(request, 'User/user_types/user_client.html')
    elif request.user.is_admin:
        return render(request, 'User/user_types/user_admin.html')
    elif request.user.is_tecnical:
        return render(request, 'User/user_types/user_tecnical.html')'''
    return render(request, 'Profile/profile.html')
    #return render(request, 'User/user_setting.html')
