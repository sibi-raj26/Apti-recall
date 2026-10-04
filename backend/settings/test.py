from . import base
from .base import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

SECRET_KEY = "test-secret-key-please-replace-in-production-32chars"
SIMPLE_JWT = {
    **base.SIMPLE_JWT,
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": SECRET_KEY,
    "ALGORITHM": "HS256",
}
