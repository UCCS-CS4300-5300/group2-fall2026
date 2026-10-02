import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = os.environ.get("DEBUG", "true").lower() == "true"
SECRET_KEY = os.environ.get("SECRET_KEY", "local-development-key-do-not-use-in-production")

ALLOWED_HOSTS = [host.strip() for host in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if host.strip()]
render_hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if render_hostname:
	ALLOWED_HOSTS.append(render_hostname)

default_csrf_origins = "https://localhost:8000" if DEBUG else ""
CSRF_TRUSTED_ORIGINS = [
	origin.strip()
	for origin in os.environ.get("CSRF_TRUSTED_ORIGINS", default_csrf_origins).split(",")
	if origin.strip()
]
if render_hostname:
	CSRF_TRUSTED_ORIGINS.append(f"https://{render_hostname}")

INSTALLED_APPS = [
	"django.contrib.admin",
	"django.contrib.auth",
	"django.contrib.contenttypes",
	"django.contrib.sessions",
	"django.contrib.messages",
	"django.contrib.staticfiles",
	"core",
]
MIDDLEWARE = [
	"django.middleware.security.SecurityMiddleware",
	"django.contrib.sessions.middleware.SessionMiddleware",
	"django.middleware.common.CommonMiddleware",
	"django.middleware.csrf.CsrfViewMiddleware",
	"django.contrib.auth.middleware.AuthenticationMiddleware",
	"django.contrib.messages.middleware.MessageMiddleware",
	"django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
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
			]
		},
	}
]
WSGI_APPLICATION = "config.wsgi.application"
DATABASES = {
	"default": dj_database_url.config(
		default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
		conn_max_age=600,
	)
}
AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/Denver"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
	"default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
	"staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
if not DEBUG:
	MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
	SECURE_SSL_REDIRECT = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
