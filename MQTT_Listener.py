import paho.mqtt.client as mqtt

BROKER = "10.120.36.61"   # replace with your Pi's IP address
PORT = 1883
TOPIC = "kotilabra/chat"

def on_connect(client, userdata, flags, rc):
    print(f"Connected: {rc}")
    client.subscribe(TOPIC)
    print(f"Subscribed to: {TOPIC}. Waiting for messages... Ctrl+C to quit.\n")

def on_message(client, userdata, msg):
    print(f"{msg.topic}  {msg.payload.decode()}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT)
client.loop_forever()