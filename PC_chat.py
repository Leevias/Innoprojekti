import paho.mqtt.client as mqtt

BROKER = "192.168.0.63"     # Pin IP-osoite, koska broker on siellä
PORT = 1883

MY_TOPIC = "chat/to_pi"        # minne laptop julkaisee
LISTEN_TOPIC = "chat/to_laptop"  # mitä laptop kuuntelee

def on_connect(client, userdata, flags, rc):
    print(f"Connected: {rc}")
    client.subscribe(LISTEN_TOPIC)
    print(f"Kuunnellaan topicia: {LISTEN_TOPIC}")
    print("Kirjoita viesti ja paina Enter lähettääksesi. Ctrl+C lopettaa.\n")

def on_message(client, userdata, msg):
    print(f"\n[{msg.topic}] {msg.payload.decode()}\n> ", end="", flush=True)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT)
client.loop_start()

try:
    while True:
        msg = input("> ")
        client.publish(MY_TOPIC, msg)
except KeyboardInterrupt:
    print("\nSuljetaan...")
finally:
    client.loop_stop()
    client.disconnect()