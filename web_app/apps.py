from django.apps import AppConfig
import os
import sys

class WebAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'web_app'
    
    def ready(self):

        from . import signals

        import os
        import sys
        from django.db.models.signals import post_migrate
        
        post_migrate.connect(create_default_user, sender=self)

        if any(cmd in sys.argv for cmd in ['collectstatic', 'migrate', 'makemigrations', 'check']):
            return 

        if os.environ.get('RUN_MAIN') != 'true' and 'runserver' in sys.argv:
            return
        
        if os.environ.get('DISABLE_SCHEDULER') == 'True':
            print("Scheduler no s'ha executat doncs s'ha especificat DISABLE_SCHEDULER=True")
            return

        try:
            from . import scheduler
            scheduler.start()
            print("Scheduler arrancado con éxito en producción.")
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