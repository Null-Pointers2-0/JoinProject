from django.apps import AppConfig

class WebAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'web_app'

    def ready(self):
        from . import signals
        # Delay scheduler start to avoid database access during app initialization
        import threading
        def start_scheduler():
            from . import scheduler
            scheduler.start()
        threading.Thread(target=start_scheduler).start()