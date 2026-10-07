import logging
import os
import threading
import time

import paho.mqtt.client as mqtt
from django.conf import settings

log = logging.getLogger("controller.mqtt")

# Yksi MQTT-yhteys per prosessi. Se kaynnistetaan vasta ensimmaisella
# HTTP-pyynnolla, jotta manage.py-komennot (check, runserverin
# automaattinen uudelleenlataus) eivat avaa ylimaaraisia yhteyksia.
_lock = threading.Lock()
_client = None

_state = {
    "connected": False,
    "temp": None,
    "temp_time": None,     # time.time() kun viimeisin lampotila saapui
    "setpoint": None,
    "kp": None,
    "ki": None,
}

_TOPIC_TO_KEY = {
    settings.TOPIC_TEMP: "temp",
    settings.TOPIC_SETPOINT: "setpoint",
    settings.TOPIC_KP: "kp",
    settings.TOPIC_KI: "ki",
}
_KEY_TO_TOPIC = {key: topic for topic, key in _TOPIC_TO_KEY.items()}


def _on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        log.error("MQTT-yhteys epaonnistui: %s", reason_code)
        return
    log.info("Yhdistetty %s:%s", settings.MQTT_HOST, settings.MQTT_PORT)
    with _lock:
        _state["connected"] = True
    # Retained-viestien ansiosta setpoint/kp/ki saadaan heti tilaamisen jalkeen.
    for topic in _TOPIC_TO_KEY:
        client.subscribe(topic)


def _on_disconnect(client, userdata, flags, reason_code, properties):
    log.warning("MQTT-yhteys katkesi (%s), yritetaan uudelleen...", reason_code)
    with _lock:
        _state["connected"] = False


def _on_message(client, userdata, msg):
    key = _TOPIC_TO_KEY.get(msg.topic)
    if key is None:
        return
    try:
        value = float(msg.payload.decode().strip())
    except ValueError:
        log.warning("Ohitetaan virheellinen arvo %s: %r", msg.topic, msg.payload)
        return
    with _lock:
        _state[key] = value
        if key == "temp":
            _state["temp_time"] = time.time()


def get_client():
    global _client
    with _lock:
        if _client is None:
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"pid-ui-{os.getpid()}")
            client.on_connect = _on_connect
            client.on_disconnect = _on_disconnect
            client.on_message = _on_message
            client.reconnect_delay_set(min_delay=1, max_delay=30)
            # connect_async: Django kaynnistyy vaikka brokeri ei olisi viela paalla.
            client.connect_async(settings.MQTT_HOST, settings.MQTT_PORT)
            client.loop_start()
            _client = client
        return _client


def get_state():
    get_client()
    with _lock:
        state = dict(_state)
    temp_time = state.pop("temp_time")
    state["temp_age"] = None if temp_time is None else round(time.time() - temp_time, 1)
    state["plc_alive"] = state["temp_age"] is not None and state["temp_age"] < settings.TEMP_STALE_SECONDS
    return state


def publish_param(key, value):
    """Julkaisee setpointin, Kp:n tai Ki:n PLC:lle. Palauttaa False jos yhteys puuttuu."""
    client = get_client()
    with _lock:
        if not _state["connected"]:
            return False
    # retain=True: brokeri muistaa viimeisimman arvon, joten PLC saa sen
    # uudelleenkaynnistyksen jalkeen ja kayttoliittyma nayttaa sen heti.
    info = client.publish(_KEY_TO_TOPIC[key], f"{value:g}", qos=1, retain=True)
    if info.rc != mqtt.MQTT_ERR_SUCCESS:
        return False
    with _lock:
        _state[key] = value
    return True
