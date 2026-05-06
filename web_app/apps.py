from django.apps import AppConfig
import sys

class WebAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'web_app'
    
    def ready(self):
        import os
        import sys
        
        # 1. Ignorar comandos de gestión
        comandos_ignorados = ['collectstatic', 'makemigrations', 'migrate', 'check']
        if any(comando in sys.argv for comando in comandos_ignorados):
            return 

        # 2. EVITAR EL DOBLE ARRANQUE:
        # Solo arranca el scheduler si NO es el auto-reloader (proceso secundario)
        if os.environ.get('RUN_MAIN') != 'true':
            from . import scheduler
            scheduler.start()