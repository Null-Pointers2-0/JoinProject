import os
from django.utils import timezone
from .models import SyncLog
from .utils import store_data 

def download_catalog_data():
    log = SyncLog.objects.create(
        status="Running",
        summary="Iniciando sincronización de catálogo (Directores, Géneros, Películas y Series)..."
    )

    try:
        store_data()

        log.status = "Success"
        log.summary = "Sincronización completada exitosamente para todos los puertos (8080, 8081, 8082)."
    
    except Exception as e:
        log.status = "Error"
        log.summary = f"Error crítico durante la sincronización: {str(e)}"

    log.end_time = timezone.now()
    log.save()