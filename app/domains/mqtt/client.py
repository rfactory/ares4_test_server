import asyncio
import logging
from paho.mqtt import client as mqtt
from app.core.config import Settings

logger = logging.getLogger(__name__)

_mqtt_client = None
_connection_event = asyncio.Event()
is_mqtt_connected = False

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("MQTT client connected successfully.")
        global is_mqtt_connected
        is_mqtt_connected = True
        _connection_event.set()
    else:
        logger.error(f"MQTT connection failed with code: {rc}")
        _connection_event.clear()

def on_disconnect(client, userdata, rc):
    logger.warning(f"MQTT client disconnected with code: {rc}. Reconnection will be attempted.")
    global is_mqtt_connected
    is_mqtt_connected = False
    _connection_event.clear()

async def connect_mqtt_background():
    global _mqtt_client
    settings = Settings()
    
    logger.info(f"Initial {settings.MQTT_INITIAL_CONNECT_DELAY}-second delay before first MQTT connection attempt...")
    await asyncio.sleep(settings.MQTT_INITIAL_CONNECT_DELAY)

    retry_count = 0

    while retry_count < settings.MQTT_MAX_RETRIES:
        try:
            _connection_event.clear()
            logger.info(f"MQTT Config: Host={settings.MQTT_BROKER_HOST}, Port={settings.MQTT_BROKER_PORT}, User={settings.MQTT_USERNAME}")
            _mqtt_client = mqtt.Client(
                client_id=settings.MQTT_CLIENT_ID,
                callback_api_version=mqtt.CallbackAPIVersion.VERSION1
            )
            _mqtt_client.on_connect = on_connect
            _mqtt_client.on_disconnect = on_disconnect
            _mqtt_client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)

            # mTLS 설정 추가
            if settings.MQTT_CA_CERTS and settings.MQTT_CLIENT_CERT and settings.MQTT_CLIENT_KEY:
                logger.info("Configuring MQTT client for mTLS.")
                _mqtt_client.tls_set(
                    ca_certs=settings.MQTT_CA_CERTS,
                    certfile=settings.MQTT_CLIENT_CERT,
                    keyfile=settings.MQTT_CLIENT_KEY
                )
            else:
                logger.warning("mTLS certificates not fully configured. Attempting non-TLS connection.")

            logger.info(f"Attempting to connect to MQTT broker at {settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}...")
            _mqtt_client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, settings.MQTT_KEEPALIVE)
            _mqtt_client.loop_start()

            await asyncio.wait_for(_connection_event.wait(), timeout=60.0)
            
            while _connection_event.is_set():
                await asyncio.sleep(1)

        except asyncio.TimeoutError:
            logger.error("Timeout waiting for MQTT connection.")
            retry_count += 1
        except Exception as e:
            logger.error(f"Error in MQTT connection loop: {str(e)}")
            retry_count += 1
        finally:
            if _mqtt_client:
                _mqtt_client.loop_stop()

        logger.info(f"Retrying MQTT connection in {settings.MQTT_RECONNECT_DELAY} seconds... (Attempt {retry_count}/{settings.MQTT_MAX_RETRIES})")
        await asyncio.sleep(settings.MQTT_RECONNECT_DELAY)

    if not _connection_event.is_set():
        logger.error("Max retries exceeded. Continuing without MQTT.")

def disconnect_mqtt():
    global _mqtt_client
    logger.info("Disconnecting MQTT client.")
    if _mqtt_client:
        _mqtt_client.disconnect()
        _mqtt_client.loop_stop()