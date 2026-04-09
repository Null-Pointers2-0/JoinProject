import os
import requests
from django.utils import timezone
from dotenv import load_dotenv
from .models import SyncLog

load_dotenv()

def download_catalog_data():
    """
    Recorre las 3 APIs de streaming, descarga los catálogos y registra el resumen.
    """
    log = SyncLog.objects.create(
        status="Running",
        summary="Iniciando sincronización múltiple..."
    )

    platforms = [
        {"name": "API_8080", "url": "http://localhost:8080/catalog", "key": os.getenv("API_KEY_8080")},
        {"name": "API_8081", "url": "http://localhost:8081/catalog", "key": os.getenv("API_KEY_8081")},
        {"name": "API_8082", "url": "http://localhost:8082/catalog", "key": os.getenv("API_KEY_8082")},
    ]

    resumen_final = []
    hay_errores = False

    for plat in platforms:
        if not plat["key"]:
            resumen_final.append(f"🔴 {plat['name']}: Falta la API Key en el .env")
            hay_errores = True
            continue

        try:
            headers = {'Authorization': f'Bearer {plat["key"]}'}
            response = requests.get(plat["url"], headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            resumen_final.append(f"🟢 {plat['name']}: OK")

        except requests.exceptions.RequestException as e:
            resumen_final.append(f"🔴 {plat['name']}: Error de conexión ({str(e)})")
            hay_errores = True

    log.status = "Error" if hay_errores else "Success"
    log.summary = " | ".join(resumen_final)
    log.end_time = timezone.now()
    log.save()