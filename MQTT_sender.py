import paho.mqtt.client as mqtt

BROKER = "localhost"   # Pi is running its own broker
PORT = 1883
TOPIC = "kotilabra/chat"

client = mqtt.Client()
client.connect(BROKER, PORT)
client.loop_start()

print(f"Connected to broker at {BROKER}:{PORT}")
print(f"Publishing to topic: {TOPIC}")
print("Type a message and press Enter to send. Ctrl+C to quit.\n")

try:
    while True:
        msg = input("> ")
        client.publish(TOPIC, msg)
except KeyboardInterrupt:
    print("\nStopping...")
finally:
    client.loop_stop()
    client.disconnect()