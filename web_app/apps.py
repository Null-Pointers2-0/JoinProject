from django.apps import AppConfig

class WebAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'web_app'
    
    def ready(self):
        import os
        import sys
        from django.db.models.signals import post_migrate
        
        post_migrate.connect(create_default_user, sender=self)

        if any(cmd in sys.argv for cmd in ['collectstatic', 'migrate', 'makemigrations', 'check']):
            return 

        if 'runserver' in sys.argv and os.environ.get('RUN_MAIN') != 'true':
            return

        try:
            from . import scheduler
            scheduler.start()
        except Exception as e:
            print(f"Scheduler no pudo arrancar (ignorar si es build): {e}")

def create_default_user(sender, **kwargs):
    from django.contrib.auth import get_user_model
    from .models import UserType
    
    User = get_user_model()

    username = 'admin'
    email = 'admin@admin.com'
    password = 'adminpassword'

    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            type=UserType.STAFF_ADMIN
        )
        print(f"✅ Superusuario '{username}' creado correctamente.")