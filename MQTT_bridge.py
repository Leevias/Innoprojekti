import paho.mqtt.client as mqtt

# Pi #1 -- toimii "PLC:nä", brokeri paikallisesti sen omalla koneella
LOCAL_BROKER = "192.168.0.63"      # Pi #1:n IP
LOCAL_PORT = 1883

# Pi #2 -- toimii "serverinä", brokeri sen omalla koneella
REMOTE_BROKER = "192.168.0.9"     # Pi #2:n IP -- vaihda oikeaan
REMOTE_PORT = 1883

TOPICS = ["plc/pid/temp", "plc/pid/setpoint", "plc/pid/kp", "plc/pid/ki"]

# --- Yhteys Pi #1:n brokeriin (PLC-puoli) ---
local_client = mqtt.Client()

def on_local_connect(client, userdata, flags, rc):
    print(f"[LOCAL] Connected: {rc}")
    for topic in TOPICS:
        client.subscribe(topic)
    print(f"[LOCAL] Kuunnellaan: {TOPICS}")

def on_local_message(client, userdata, msg):
    print(f"[LOCAL -> REMOTE] {msg.topic}: {msg.payload.decode()}")
    remote_client.publish(msg.topic, msg.payload)

local_client.on_connect = on_local_connect
local_client.on_message = on_local_message

# --- Yhteys Pi #2:n brokeriin (server-puoli) ---
remote_client = mqtt.Client()

def on_remote_connect(client, userdata, flags, rc):
    print(f"[REMOTE] Connected: {rc}")
    for topic in TOPICS:
        client.subscribe(topic)
    print(f"[REMOTE] Kuunnellaan: {TOPICS}")

def on_remote_message(client, userdata, msg):
    print(f"[REMOTE -> LOCAL] {msg.topic}: {msg.payload.decode()}")
    local_client.publish(msg.topic, msg.payload)

remote_client.on_connect = on_remote_connect
remote_client.on_message = on_remote_message

# --- Yhdistä molemmat ja pyöritä ---
local_client.connect(LOCAL_BROKER, LOCAL_PORT)
remote_client.connect(REMOTE_BROKER, REMOTE_PORT)

local_client.loop_start()
remote_client.loop_forever()