import csv
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from .services import get_content_analytics, format_analytics_for_csv
from django.shortcuts import render, redirect
from django.contrib import messages
from web_app.forms import CustomUserChangeForm
from web_app.models import Movie, Series, Contingut, API

# Create your views here.
@login_required(login_url='login')
def user_profile(request):
        
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Perfil actualizado correctamente!')
            return redirect(request.path)
    else:
        form = CustomUserChangeForm(instance=request.user)

    return render(request, 'users/profile/user_profile.html', {'form': form})

@login_required(login_url='login')
def admin_profile(request):
    return render(request, 'users/profile/admin_profile.html')

@login_required(login_url='login')
def history(request):
    movies = Movie.objects.all()
    return render(request, 'users/parts/history.html', {'movies': movies})

@login_required(login_url='login')
def followed(request):
    profile, _ = request.user.profile, True
    preferits_ids = profile.preferits.values_list('id', flat=True)
    movies = Movie.objects.filter(contingut_id__in=preferits_ids)
    series_list = Series.objects.filter(contingut_id__in=preferits_ids)
    return render(request, 'users/parts/followed.html', {'movies': movies, 'series_list': series_list})

@login_required(login_url='login')
def subscription(request):
    all_apis = API.objects.all().order_by('port')
    user_subscription_ids = set(request.user.subscriptions.values_list('id', flat=True))

    if request.method == 'POST':
        selected_ids = request.POST.getlist('subscriptions')
        request.user.subscriptions.set(API.objects.filter(id__in=selected_ids))
        messages.success(request, '¡Suscripciones actualizadas correctamente!')
        return redirect('suscription')

    return render(request, 'users/parts/subscription.html', {
        'all_apis': all_apis,
        'user_subscription_ids': user_subscription_ids,
    })

def is_admin_or_staff(user):
    return user.is_staff or user.type == 'Admin'

@login_required(login_url='login')
@user_passes_test(is_admin_or_staff)
def export_analytics_csv(request):
    platform_id = request.GET.get('platform')
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    report_type = request.GET.get('type', 'internal') 

    raw_data = get_content_analytics(
        start_date=start_date,
        end_date=end_date,
        plataform_id=platform_id
    )

    is_b2b = (report_type == 'b2b')
    clean_data = format_analytics_for_csv(raw_data, is_b2b_report=is_b2b)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="analytics_report.csv"'

    writer = csv.writer(response)

    writer.writerow(['Title', 'Genre', 'Age Rating', 'Year', 'Director', 'Platform', 'Total Views', 'Total Favorites'])

    for item in clean_data:
        writer.writerow([
            item['title'], item['genre'], item['age_rating'], 
            item['year'], item['director'], item['platform'], 
            item['views'], item['favorites']
        ])
    
    return response


@login_required(login_url='login')
@user_passes_test(is_admin_or_staff)
def admin_dashboard(request):
    return render(request, 'users/parts/dashboard_platform.html')