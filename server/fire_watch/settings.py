import os
import sys
from pathlib import Path

import patches
from dotenv import load_dotenv

import fire_watch
from fire_watch.config_utils import (
    init_flags,
    init_print_utils,
    sanitized_configs,
    set_db_name,
    set_debug_flags,
)

load_dotenv()
_path = Path(__file__).resolve()

BASE_DIR = _path.parent.parent

# Initialize configuration
conf = sanitized_configs(base_path=_path.parent)

# Initialize application wide flags
init_flags()

# initialize print utils
init_print_utils(file=sys.stderr)

SECRET_KEY = os.getenv("SECRET_KEY")

DEBUG = conf.developer

if not DEBUG:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[DjangoIntegration()])
    fire_watch.print("[bold cyan blue]Sentry Enabled :rocket:")

set_db_name(conf)

if DEBUG:
    set_debug_flags()

fire_watch.flags.use_secret = False if os.getenv("CI") else True
ALLOWED_HOSTS = conf.allowed_hosts


INSTALLED_APPS = [
    "channels",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "alerts",
    "apis",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "authentication.middleware.AuthMiddleWare",
]

AUTH_PASSWORD_VALIDATORS = [
    "django.contrib.auth.password_validation.MinimumLengthValidator",
    "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    "django.contrib.auth.password_validation.CommonPasswordValidator",
    "django.contrib.auth.password_validation.NumericPasswordValidator",
]


ROOT_URLCONF = "fire_watch.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

ASGI_APPLICATION = "fire_watch.asgi.application"
WSGI_APPLICATION = "fire_watch.wsgi.application"

throttle_rate = (
    conf.throttle_rate["debug"] if DEBUG else conf.throttle_rate["production"]
)
fire_watch.flags.throttle_rate = throttle_rate
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_RATES": {
        "basic_throttle": throttle_rate,
    },
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    "DEFAULT_PARSER_CLASSES": (("rest_framework.parsers.JSONParser",)),
}


DATABASE = {
    "Production": {
        "MONGO_URI": os.getenv("MONGO_URI"),
        "DB": os.getenv("DB"),
    },
    "Test": {"MONGO_URI": os.getenv("MONGO_URI"), "DB": os.getenv("TESTDB")},
}

fire_watch.print("[bold green]Current server configurations")

fire_watch.print(f"[blue]DEBUG: {DEBUG} USING-DB: {fire_watch.flags.db_name}")
fire_watch.print(f"[blue]Current throttle setting {fire_watch.flags.throttle_rate}")

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


STATIC_URL = "/static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
