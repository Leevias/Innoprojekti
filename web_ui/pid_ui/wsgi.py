import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pid_ui.settings")

application = get_wsgi_application()

# Tuotannossa (gunicorn) MQTT-yhteys avataan heti, jotta kuvaajan historia
# kertyy, vaikka kukaan ei olisi viela avannut sivua.
from controller import mqtt_client  # noqa: E402

mqtt_client.get_client()
