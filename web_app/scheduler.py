from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from .services import download_catalog_data
import sys


def start():
    if "runserver" not in sys.argv:
        return

    download_catalog_data()

    scheduler = BackgroundScheduler(timezone="Europe/Madrid")
    scheduler.add_jobstore(DjangoJobStore(), "default")

    scheduler.add_job(
        download_catalog_data,
        trigger="cron",
        hour=3,
        minute=0,
        id="sync_streaming_apis",
        max_instances=1,
        replace_existing=True,
    )

    scheduler.start()
    print("Cron Job configured at 03:00 AM.")