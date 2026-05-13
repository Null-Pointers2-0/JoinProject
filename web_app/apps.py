from django.apps import AppConfig
import os
import sys

class WebAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'web_app'
    
    def ready(self):
        if any(cmd in sys.argv for cmd in ['collectstatic', 'migrate', 'makemigrations', 'check']):
            return 

        if os.environ.get('RUN_MAIN') != 'true' and 'runserver' in sys.argv:
            return

        try:
            from . import scheduler
            if not sys.stdin.isatty():
                scheduler.start()
                print("Scheduler arrancado con éxito en producción.")
        except Exception as e:
            print(f"Scheduler no pudo arrancar (ignorar si es build): {e}")