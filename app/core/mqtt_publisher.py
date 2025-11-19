import logging
import json
import paho.mqtt.client as mqtt
import ssl
import time

from app.core.config import settings

logger = logging.getLogger(__name__)

# Basic persistent MQTT client for publishing
class MqttPersistentPublisher:
    def __init__(self):
        self.client = mqtt.Client(
            client_id="server2-status-publisher",
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            protocol=mqtt.MQTTv311
        )
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self._connected = False
        self._connect_mqtt() # Connect on initialization

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            logger.info("MQTT Publisher: Successfully connected to Broker.")
            self._connected = True
        else:
            logger.error(f"MQTT Publisher: Failed to connect, return code {rc}")
            self._connected = False

    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        logger.warning(f"MQTT Publisher: Disconnected from Broker. Reason: {reason_code}")
        self._connected = False
        if reason_code != 0:
            logger.warning("MQTT Publisher: Unexpected disconnection occurred. Auto-reconnect will be attempted.")

    def _connect_mqtt(self):
        try:
            if settings.MQTT_TLS_ENABLED:
                logger.info("MQTT Publisher: TLS is enabled. Configuring TLS.")
                self.client.tls_set(
                    ca_certs=settings.MQTT_CA_CERTS,
                    certfile=settings.MQTT_CLIENT_CERT,
                    keyfile=settings.MQTT_CLIENT_KEY,
                    tls_version=ssl.PROTOCOL_TLSv1_2
                )
                if settings.MQTT_TLS_INSECURE:
                    logger.warning("MQTT Publisher: TLS insecure mode is enabled. Skipping hostname verification.")
                    self.client.tls_insecure_set(True)
            
            self.client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)
            self.client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, settings.MQTT_KEEPALIVE)
            self.client.loop_start() # Start a background thread to handle MQTT network traffic
            logger.info(f"MQTT Publisher: Attempting to connect to {settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}")
        except Exception as e:
            logger.error(f"MQTT Publisher: An error occurred while connecting: {e}")

    def publish(self, topic: str, payload: dict | str):
        if not self._connected:
            logger.warning("MQTT Publisher: Not connected. Attempting to wait for connection...")
            for _ in range(5): # Try 5 times with 1s delay
                if self._connected:
                    break
                time.sleep(1)
            if not self._connected:
                logger.error("MQTT Publisher: Still not connected. Cannot publish message.")
                return False
        
        try:
            payload_str = payload if isinstance(payload, str) else json.dumps(payload)
            result = self.client.publish(topic, payload_str, qos=1)
            logger.debug(f"MQTT Publisher: Queued message for topic {topic}: {payload_str}. Result: {result}")
            return True
        except Exception as e:
            logger.error(f"MQTT Publisher: An error occurred while publishing: {e}", exc_info=True)
            return False

# Create a global instance for re-use
mqtt_publisher_instance = MqttPersistentPublisher()

# Expose a simple function for convenience
def publish_device_status(user_email: str, device_uuid: str, status_payload: dict):
    topic = f"client/state/{user_email}/{device_uuid}"
    # Ensure payload has device_uuid and status to be consistent
    full_payload = {"device_uuid": device_uuid, "status": status_payload.get("status"), "user_email": user_email}
    return mqtt_publisher_instance.publish(topic, full_payload)
