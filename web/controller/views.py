import json
import math

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from . import mqtt_client

PARAM_LABELS = {
    "setpoint": "Asetusarvo (°C)",
    "kp": "Kp (vahvistus)",
    "ki": "Ki (integraali)",
}


@require_GET
def index(request):
    mqtt_client.get_client()
    params = [
        {"key": key, "label": PARAM_LABELS[key], "min": lo, "max": hi}
        for key, (lo, hi) in settings.PARAM_LIMITS.items()
    ]
    return render(request, "controller/index.html", {"params": params})


@require_GET
def api_state(request):
    return JsonResponse(mqtt_client.get_state())


@require_POST
def api_set(request):
    try:
        body = json.loads(request.body)
        key = body["param"]
        value = float(body["value"])
    except (ValueError, KeyError, TypeError):
        return JsonResponse({"error": "Virheellinen pyynto"}, status=400)

    if key not in settings.PARAM_LIMITS:
        return JsonResponse({"error": f"Tuntematon parametri: {key}"}, status=400)
    lo, hi = settings.PARAM_LIMITS[key]
    if not math.isfinite(value) or not lo <= value <= hi:
        return JsonResponse({"error": f"Arvon pitaa olla valilla {lo:g}-{hi:g}"}, status=400)

    if not mqtt_client.publish_param(key, value):
        return JsonResponse({"error": "Ei yhteytta MQTT-brokeriin"}, status=503)
    return JsonResponse(mqtt_client.get_state())
