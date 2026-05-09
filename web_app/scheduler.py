from time import timezone

from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from .services import download_catalog_data
import sys


def start():
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

    download_catalog_data()

    scheduler.start()