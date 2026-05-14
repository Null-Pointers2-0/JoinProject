from django.apps import AppConfig

class WebAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'web_app'
    
    def ready(self):
        from . import signals

        import os
        import sys
        
        if any(cmd in sys.argv for cmd in ['collectstatic', 'migrate', 'makemigrations', 'check']):
            return 

        if 'runserver' in sys.argv and os.environ.get('RUN_MAIN') != 'true':
            return

        try:
            from . import scheduler
            scheduler.start()
        except Exception as e:
            print(f"Scheduler no pudo arrancar (ignorar si es build): {e}")