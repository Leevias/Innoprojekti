import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Tuotannossa SECRET_KEY annetaan ymparistomuuttujana (ks. deploy/pid_ui.service).
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-insecure-key")
DEBUG = os.environ.get("DJANGO_DEBUG", "0") == "1"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",")

# Tietokantaa ei tarvita: kaikki tila tulee MQTT:sta.
INSTALLED_APPS = [
    "controller",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "pid_ui.urls"
WSGI_APPLICATION = "pid_ui.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": ["django.template.context_processors.request"]},
    },
]

DATABASES = {}

LANGUAGE_CODE = "fi"
TIME_ZONE = "Europe/Helsinki"
USE_I18N = False
USE_TZ = True

# --- MQTT: Django ajetaan samalla palvelimella kuin Mosquitto ---
MQTT_HOST = os.environ.get("MQTT_HOST", "localhost")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))

TOPIC_TEMP = "plc/pid/temp"
TOPIC_SETPOINT = "plc/pid/setpoint"
TOPIC_KP = "plc/pid/kp"
TOPIC_KI = "plc/pid/ki"

# Sallitut arvoalueet kayttoliittymasta lahetettaville arvoille.
PARAM_LIMITS = {
    "setpoint": (0.0, 100.0),
    "kp": (0.0, 100.0),
    "ki": (0.0, 100.0),
}

# Jos lampotilaa ei ole tullut tata kauemmin, PLC naytetaan "ei vastaa" -tilassa.
TEMP_STALE_SECONDS = 5

# Kuvaajan historia muistissa: 3600 pistetta = 1 tunti, kun PLC lahettaa kerran sekunnissa.
HISTORY_MAX_POINTS = 3600
