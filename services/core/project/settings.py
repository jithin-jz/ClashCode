import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv(BASE_DIR / ".env", override=False)

# Security
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ImproperlyConfigured("SECRET_KEY is not set")

DEBUG = os.getenv("DEBUG", "false").lower() == "true"


def _parse_csv(value: str | None, default: list[str]) -> list[str]:
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


ALLOWED_HOSTS = _parse_csv(
    os.getenv("ALLOWED_HOSTS"),
    ["localhost", "127.0.0.1", "core", "api.localhost"],
)

cloudinary_cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME", "").strip()
cloudinary_api_key = os.getenv("CLOUDINARY_API_KEY", "").strip()
cloudinary_api_secret = os.getenv("CLOUDINARY_API_SECRET", "").strip()
USE_CLOUDINARY = all(
    [cloudinary_cloud_name, cloudinary_api_key, cloudinary_api_secret]
)

# Applications
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "drf_spectacular",
    "auth",
    "rewards",
    "users",
    "xpoint",
    "payments",
    "store",
    "challenges",
    "learning",
    "certificates",
    "django_celery_beat",
    "django_celery_results",
    "administration",
    "posts",
    "notifications",
    "achievements",
]

if USE_CLOUDINARY:
    staticfiles_index = INSTALLED_APPS.index("django.contrib.staticfiles")
    INSTALLED_APPS.insert(staticfiles_index, "cloudinary_storage")
    INSTALLED_APPS.append("cloudinary")

# Middleware
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# URLs
ROOT_URLCONF = "project.urls"

# Templates
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

# WSGI
WSGI_APPLICATION = "project.wsgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT"),
        "CONN_MAX_AGE": int(os.getenv("DB_CONN_MAX_AGE", "60")),
        "CONN_HEALTH_CHECKS": _parse_bool(
            os.getenv("DB_CONN_HEALTH_CHECKS"), default=True
        ),
    }
}

# Validate database configuration
if not all(
    [
        os.getenv("DB_NAME"),
        os.getenv("DB_USER"),
        os.getenv("DB_PASSWORD"),
        os.getenv("DB_HOST"),
        os.getenv("DB_PORT"),
    ]
):
    raise ImproperlyConfigured(
        "Database configuration incomplete. Ensure DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, and DB_PORT are set."
    )


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Indian Timezone
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
WHITENOISE_MANIFEST_STRICT = False


# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

if USE_CLOUDINARY:
    CLOUDINARY_STORAGE = {
        "CLOUD_NAME": cloudinary_cloud_name,
        "API_KEY": cloudinary_api_key,
        "API_SECRET": cloudinary_api_secret,
        "SECURE": _parse_bool(os.getenv("CLOUDINARY_SECURE"), default=True),
    }
    STORAGES["default"] = {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage"
    }

# Backend URL (for absolute media paths)
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Firebase
FIREBASE_SERVICE_ACCOUNT_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
if FIREBASE_SERVICE_ACCOUNT_PATH and not os.path.isabs(FIREBASE_SERVICE_ACCOUNT_PATH):
    FIREBASE_SERVICE_ACCOUNT_PATH = os.path.join(
        BASE_DIR, FIREBASE_SERVICE_ACCOUNT_PATH
    )


# Cache Configuration
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.getenv("REDIS_URL", "redis://redis:6379/0"),
        "OPTIONS": {
            "db": 1,  # Use different Redis DB than Celery
        },
        "KEY_PREFIX": "coc",
        "TIMEOUT": 300,  # Default timeout: 5 minutes
    }
}

# Default primary key
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# CORS
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
CORS_ALLOWED_ORIGINS = _parse_csv(
    os.getenv("CORS_ALLOWED_ORIGINS"),
    [
        FRONTEND_URL,
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
    ],
)
CORS_ALLOWED_ORIGIN_REGEXES = _parse_csv(
    os.getenv("CORS_ALLOWED_ORIGIN_REGEXES"),
    [r"^https://.*\.vercel\.app$"],
)
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = _parse_csv(
    os.getenv("CSRF_TRUSTED_ORIGINS"),
    [
        FRONTEND_URL,
        "http://localhost",
        "http://127.0.0.1",
        "https://localhost",
        "https://127.0.0.1",
    ],
)

# drf_spectacular

SPECTACULAR_SETTINGS = {
    "TITLE": "CLASHCODE API",
    "DESCRIPTION": "Internal API documentation for the CLASHCODE platform. This API handles authentication, user profiles, challenges, store purchases, and real-time notifications.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": r"/api/",
    "ENUM_NAME_OVERRIDES": {
        "UserProgressStatus": "challenges.models.UserProgress.Status",
    },
    "SORT_OPERATIONS": True,
    "CAMELIZE_NAMES": False,
}

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "auth.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": os.getenv("THROTTLE_ANON_RATE", "20/minute"),  # General anonymous limit
        "user": os.getenv(
            "THROTTLE_USER_RATE", "100/minute"
        ),  # General authenticated user limit
        "otp": os.getenv(
            "THROTTLE_OTP_RATE", "5/minute"
        ),  # Strict limit for OTP requests (SMS cost)
        "auth": os.getenv(
            "THROTTLE_AUTH_RATE", "10/minute"
        ),  # Login/register attempts (brute force protection)
        "store": os.getenv(
            "THROTTLE_STORE_RATE", "30/minute"
        ),  # Store/purchase operations
        "notifications": os.getenv(
            "THROTTLE_NOTIFICATIONS_RATE", "180/minute"
        ),  # Notification polling/read operations
        "sensitive": os.getenv(
            "THROTTLE_SENSITIVE_RATE", "5/minute"
        ),  # Password reset, email change
        "burst": os.getenv(
            "THROTTLE_BURST_RATE", "10/second"
        ),  # Short burst protection
    },
}

# JWT Configuration
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "RS256").upper()
JWT_SHARED_SECRET = os.getenv("JWT_SHARED_SECRET", "").strip()

# Private key for signing tokens (keep secure!)
JWT_PRIVATE_KEY = os.getenv("JWT_PRIVATE_KEY", "").replace("\\n", "\n").strip()

# Public key for verifying tokens (can be shared with other services)
JWT_PUBLIC_KEY = os.getenv("JWT_PUBLIC_KEY", "").replace("\\n", "\n").strip()

if not JWT_PRIVATE_KEY and not JWT_PUBLIC_KEY:
    fallback_secret = JWT_SHARED_SECRET or (SECRET_KEY if DEBUG else "")
    if not fallback_secret:
        raise ImproperlyConfigured(
            "JWT configuration incomplete. Set JWT_PRIVATE_KEY/JWT_PUBLIC_KEY "
            "for RS256 or JWT_SHARED_SECRET for local HS256."
        )
    JWT_ALGORITHM = "HS256"
    JWT_PRIVATE_KEY = fallback_secret
    JWT_PUBLIC_KEY = fallback_secret
elif not JWT_PRIVATE_KEY or not JWT_PUBLIC_KEY:
    raise ImproperlyConfigured(
        "JWT configuration incomplete. Both JWT_PRIVATE_KEY and JWT_PUBLIC_KEY "
        "must be set for asymmetric signing."
    )

JWT_ACCESS_TOKEN_LIFETIME = 60 * 60
JWT_REFRESH_TOKEN_LIFETIME = 60 * 60 * 24 * 7

# HttpOnly JWT cookie settings
JWT_COOKIE_SECURE = _parse_bool(os.getenv("JWT_COOKIE_SECURE"), default=not DEBUG)
JWT_COOKIE_SAMESITE = os.getenv("JWT_COOKIE_SAMESITE", "Lax")
JWT_ACCESS_COOKIE_NAME = os.getenv("JWT_ACCESS_COOKIE_NAME", "access_token")
JWT_REFRESH_COOKIE_NAME = os.getenv("JWT_REFRESH_COOKIE_NAME", "refresh_token")
JWT_RETURN_TOKENS_IN_BODY = _parse_bool(
    os.getenv("JWT_RETURN_TOKENS_IN_BODY"), default=False
)

if JWT_COOKIE_SECURE:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SECURE_SSL_REDIRECT = _parse_bool(os.getenv("SECURE_SSL_REDIRECT"), default=not DEBUG)
SESSION_COOKIE_SECURE = JWT_COOKIE_SECURE
CSRF_COOKIE_SECURE = JWT_COOKIE_SECURE
SECURE_HSTS_SECONDS = int(
    os.getenv("SECURE_HSTS_SECONDS", "0" if DEBUG else "31536000")
)
SECURE_HSTS_INCLUDE_SUBDOMAINS = _parse_bool(
    os.getenv("SECURE_HSTS_INCLUDE_SUBDOMAINS"), default=not DEBUG
)
SECURE_HSTS_PRELOAD = _parse_bool(os.getenv("SECURE_HSTS_PRELOAD"), default=not DEBUG)
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
USE_X_FORWARDED_HOST = True

# OAuth
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
GITHUB_REDIRECT_URI = f"{FRONTEND_URL}/auth/github/callback"

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = f"{FRONTEND_URL}/auth/google/callback"

EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = _parse_bool(os.getenv("EMAIL_USE_TLS"), default=True)
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "CLASHCODE <no-reply@localhost>")
OTP_EMAIL_ASYNC = os.getenv("OTP_EMAIL_ASYNC", "true").lower() == "true"

# Razorpay
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET")

# Celery Configuration
CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# Celery Result Backend — django-db stores results in PostgreSQL
CELERY_RESULT_BACKEND = "django-db"
CELERY_CACHE_BACKEND = "django-cache"  # Cache backend for result metadata
CELERY_RESULT_EXTENDED = True  # Store task args, kwargs, worker, etc.
CELERY_RESULT_EXPIRES = 60 * 60 * 24  # Auto-expire results after 24 hours
CELERY_TASK_TRACK_STARTED = True  # Track STARTED state in result backend
CELERY_TASK_STORE_ERRORS_EVEN_IF_IGNORED = True  # Always persist error tracebacks

# Celery Beat
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

CELERY_BEAT_SCHEDULE = {
    "cleanup-celery-results-daily": {
        "task": "project.tasks.cleanup_old_task_results",
        "schedule": 60 * 60 * 24,  # Every 24 hours
    },
}

# --- Test Overrides ---
if "test" in sys.argv:
    # Use SQLite for tests
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test_db.sqlite3",
    }
    # Use memory cache for tests
    CACHES["default"] = {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
    # Celery settings for tests
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_BROKER_URL = "memory://"
    CELERY_RESULT_BACKEND = "cache+memory://"
    # Use memory email backend
    EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
