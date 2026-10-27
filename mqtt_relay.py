import asyncio
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("mqtt_relay")

# TCP-rele PLC:n ja palvelimen valilla.
# PLC (FB_IotMqttClient) yhdistaa taman koneen porttiin 1883, ja skripti
# valittaa kaikki tavut sellaisenaan palvelimen Mosquittolle. PLC luulee
# puhuvansa suoraan palvelimen brokerille. 

# --- PLC-puoli: kuunnellaan kaikilla verkkokorteilla ---
LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = 1883

# --- Server-puoli: Linux-palvelimen MQTT-brokeri ---
SERVER_HOST = "10.120.36.74"
SERVER_PORT = 1883

BUFFER_SIZE = 4096


async def pipe(reader, writer):
    """Kopioi dataa yhteen suuntaan, kunnes toinen paa sulkee yhteyden."""
    try:
        while data := await reader.read(BUFFER_SIZE):
            writer.write(data)
            await writer.drain()
    except (ConnectionError, OSError):
        pass
    finally:
        writer.close()


async def handle_client(plc_reader, plc_writer):
    peer = plc_writer.get_extra_info("peername")
    log.info("[PLC] Uusi yhteys: %s", peer)
    try:
        srv_reader, srv_writer = await asyncio.open_connection(SERVER_HOST, SERVER_PORT)
    except OSError as e:
        log.error("[SERVER] Ei yhteytta %s:%s (%s), suljetaan %s", SERVER_HOST, SERVER_PORT, e, peer)
        plc_writer.close()
        return

    log.info("Valitetaan %s <-> %s:%s", peer, SERVER_HOST, SERVER_PORT)
    await asyncio.gather(
        pipe(plc_reader, srv_writer),
        pipe(srv_reader, plc_writer),
    )
    log.info("[PLC] Yhteys suljettu: %s", peer)


async def main():
    try:
        server = await asyncio.start_server(handle_client, LISTEN_HOST, LISTEN_PORT)
    except OSError as e:
        log.error("Porttia %s ei saatu kayttoon (%s). Onko Mosquitto tai toinen rele jo kaynnissa?",
                  LISTEN_PORT, e)
        return
    log.info("Rele kaynnissa: %s:%s -> %s:%s. Ctrl+C lopettaa.",
             LISTEN_HOST, LISTEN_PORT, SERVER_HOST, SERVER_PORT)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Pysaytetaan...")
