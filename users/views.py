from django.shortcuts import render, redirect

# Create your views here.
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