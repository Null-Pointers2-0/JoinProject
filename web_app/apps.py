from django.apps import AppConfig

class WebAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'web_app'

    def ready(self):
        from . import signals
        from . import scheduler
        scheduler.start()