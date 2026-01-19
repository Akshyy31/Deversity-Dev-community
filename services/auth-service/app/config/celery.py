import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("auth_service")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# ✅ WINDOWS FIX
app.conf.worker_pool = "solo"
app.conf.worker_concurrency = 1
