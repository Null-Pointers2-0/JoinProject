from django.shortcuts import render, redirect
from django.contrib import messages
from web_app.forms import CustomUserChangeForm
from web_app.models import Movie, Series
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from django.shortcuts import render, redirect, get_object_or_404
from web_app.forms import CustomUserAdminCreationForm
from web_app.models import CustomUser, Movie, UserProfile, Series
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages

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
    profile, _ = request.user.profile, True
    preferits_ids = profile.preferits.values_list('id', flat=True)
    movies = Movie.objects.filter(contingut_id__in=preferits_ids)
    series_list = Series.objects.filter(contingut_id__in=preferits_ids)
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

@user_passes_test(lambda u: u.is_superuser)
def gestion_usuarios(request):
    if not request.user.is_authenticated:
        return redirect('login')
    users = CustomUser.objects.all()
    return render(request, 'users/parts/users_table.html', {'users': users})

@user_passes_test(lambda u: u.is_superuser)
def eliminar_usuario(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        user.delete()
        messages.success(request, f"Usuario '{user.username}' eliminado correctamente.")
        return redirect('gestion_usuarios')


@user_passes_test(lambda u: u.is_superuser)
def crear_usuario_admin(request):
    if request.method == 'POST':
        form = CustomUserAdminCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            
            temp_password = get_random_string(length=12)
            user.set_password(temp_password)
            user.save()
            
            UserProfile.objects.get_or_create(user=user)
            
            asunto = 'Bienvenido a StreamSync - Tus Credenciales'
            mensaje = f"""
            Hola {user.username},
            
            Se ha creado una cuenta para ti en StreamSync.
            Aquí tienes tus credenciales de acceso:
            
            Usuario: {user.username}
            Contraseña temporal: {temp_password}
            
            Por seguridad, te recomendamos cambiarla en tu perfil tras iniciar sesión.
            """
            
            try:
                send_mail(
                    asunto,
                    mensaje,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                messages.success(request, f"Usuario creado y correo enviado a {user.email}")
            except Exception as e:
                messages.warning(request, "Usuario creado, pero hubo un error al enviar el correo.")

            return redirect('gestion_usuarios')
    else:
        form = CustomUserAdminCreationForm()
    
    return render(request, 'users/parts/create_user.html', {'form': form})