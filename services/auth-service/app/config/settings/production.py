from .base import *

DEBUG = False

ALLOWED_HOSTS = ["your-domain.com"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "auth_db",
        "USER": "auth_user",
        "PASSWORD": "strong-password",
        "HOST": "db",
        "PORT": 5432,
    }
}
