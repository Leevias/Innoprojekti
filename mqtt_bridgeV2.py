import logging
import time

import paho.mqtt.client as mqtt

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("mqtt_bridge")

# Skripti ajetaan "dual-homed" sillalla (kone jolla on kaksi verkkokorttia):
# yksi kortti CX7000:n eristetyssa verkossa, toinen palvelimen verkossa.

# --- PLC-puoli: CX7000:n oma / sen verkossa oleva MQTT-brokeri ---
# HUOM: taytä oikea IP kun TwinCAT IoT Communicator / broker-sijainti on paatetty.
PLC_BROKER = "192.168.0.69"        # CX7000-verkon brokerin IP
PLC_PORT = 1883

# --- Server-puoli: Linux-palvelimen MQTT-brokeri ---
SERVER_BROKER = "10.120.36.74"     # Linux-palvelimen IP -- vaihda oikeaan
SERVER_PORT = 1883

TOPICS = ["plc/pid/temp", "plc/pid/setpoint", "plc/pid/kp", "plc/pid/ki"]

RECONNECT_DELAY_MIN = 1
RECONNECT_DELAY_MAX = 30

# Estaa loputtoman edestakaisin kaikumisen: kun viesti julkaistaan toiselle
# puolelle, sen (topic, payload) muistetaan hetken ajan, jotta silta ei
# julkaise samaa viestia takaisin nahdessaan oman julkaisunsa kaiun.
ECHO_TTL_SECONDS = 5.0
_recent_forwards = {}


def _was_just_forwarded(topic, payload):
    key = (topic, payload)
    now = time.monotonic()
    ts = _recent_forwards.get(key)
    if ts is not None and now - ts < ECHO_TTL_SECONDS:
        return True
    _recent_forwards[key] = now
    if len(_recent_forwards) > 256:
        cutoff = now - ECHO_TTL_SECONDS
        for k, t in list(_recent_forwards.items()):
            if t < cutoff:
                del _recent_forwards[k]
    return False


def make_client(name):
    client = mqtt.Client(client_id=f"lamppu-bridge-{name}", clean_session=True)
    client.reconnect_delay_set(min_delay=RECONNECT_DELAY_MIN, max_delay=RECONNECT_DELAY_MAX)
    return client


plc_client = make_client("plc")
server_client = make_client("server")


def on_plc_connect(client, userdata, flags, rc):
    if rc != 0:
        log.error("[PLC] Yhteys epaonnistui, rc=%s", rc)
        return
    log.info("[PLC] Yhdistetty %s:%s", PLC_BROKER, PLC_PORT)
    for topic in TOPICS:
        client.subscribe(topic)
    log.info("[PLC] Kuunnellaan: %s", TOPICS)


def on_plc_disconnect(client, userdata, rc):
    log.warning("[PLC] Yhteys katkesi (rc=%s), yritetaan uudelleen...", rc)


def on_plc_message(client, userdata, msg):
    payload = msg.payload
    if _was_just_forwarded(msg.topic, payload):
        return
    log.info("[PLC -> SERVER] %s: %s", msg.topic, payload.decode(errors="replace"))
    server_client.publish(msg.topic, payload)


plc_client.on_connect = on_plc_connect
plc_client.on_disconnect = on_plc_disconnect
plc_client.on_message = on_plc_message


def on_server_connect(client, userdata, flags, rc):
    if rc != 0:
        log.error("[SERVER] Yhteys epaonnistui, rc=%s", rc)
        return
    log.info("[SERVER] Yhdistetty %s:%s", SERVER_BROKER, SERVER_PORT)
    for topic in TOPICS:
        client.subscribe(topic)
    log.info("[SERVER] Kuunnellaan: %s", TOPICS)


def on_server_disconnect(client, userdata, rc):
    log.warning("[SERVER] Yhteys katkesi (rc=%s), yritetaan uudelleen...", rc)


def on_server_message(client, userdata, msg):
    payload = msg.payload
    if _was_just_forwarded(msg.topic, payload):
        return
    log.info("[SERVER -> PLC] %s: %s", msg.topic, payload.decode(errors="replace"))
    plc_client.publish(msg.topic, payload)


server_client.on_connect = on_server_connect
server_client.on_disconnect = on_server_disconnect
server_client.on_message = on_server_message


def main():
    plc_client.connect(PLC_BROKER, PLC_PORT)
    server_client.connect(SERVER_BROKER, SERVER_PORT)

    plc_client.loop_start()
    server_client.loop_start()

    log.info("Silta kaynnissa. Ctrl+C lopettaa.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Pysaytetaan...")
    finally:
        plc_client.loop_stop()
        server_client.loop_stop()
        plc_client.disconnect()
        server_client.disconnect()


if __name__ == "__main__":
    main()
