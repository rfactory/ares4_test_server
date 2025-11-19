import logging
import os
import ssl
import hvac
import time
import threading
import json
import redis
import concurrent.futures
from paho.mqtt import client as mqtt

from app.core.config import Settings
from app.database import SessionLocal
from app.domains.mqtt import processor

logger = logging.getLogger(__name__)

class MqttListener:
    def __init__(self, settings: Settings):
        logger.info("Initializing MqttListener...")
        self.settings = settings
        self.vault_client = self._init_vault_client()
        self._stop_event = threading.Event()
        
        self.redis_client = redis.Redis(
            host=self.settings.REDIS_HOST, 
            port=self.settings.REDIS_PORT, 
            db=self.settings.REDIS_DB, 
            decode_responses=True
        )

        self.db_executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.settings.MQTT_LISTENER_MAX_WORKERS)

        self.client = mqtt.Client(
            client_id=self.settings.MQTT_LISTENER_CLIENT_ID, 
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2
        )
        self._setup_tls_from_vault()
        self.client.username_pw_set(self.settings.MQTT_USERNAME, self.settings.MQTT_PASSWORD)

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

    def _init_vault_client(self) -> hvac.Client:
        logger.info(f"Initializing Vault client at {self.settings.VAULT_ADDR}")
        client = hvac.Client(url=self.settings.VAULT_ADDR)

        try:
            role_id = self.settings.VAULT_APPROLE_ROLE_ID
            secret_id = self.settings.VAULT_APPROLE_SECRET_ID

            if not role_id or not secret_id:
                raise ValueError("VAULT_APPROLE_ROLE_ID or VAULT_APPROLE_SECRET_ID not set.")

            logger.info("Attempting AppRole login...")
            login_response = client.auth.approle.login(role_id=role_id, secret_id=secret_id)
            client.token = login_response['auth']['client_token']
            logger.info("Vault client authenticated successfully using AppRole.")
        except Exception as e:
            logger.error(f"AppRole authentication failed: {e}")
            raise ConnectionError(f"Vault AppRole authentication failed: {e}")

        return client

    def _setup_tls_from_vault(self):
        logger.info("Setting up TLS from Vault...")
        try:
            # Generate client certificate from Vault
            cert_response = self.vault_client.secrets.pki.generate_certificate(
                mount_point=self.settings.VAULT_PKI_MOUNT_POINT,
                name=self.settings.VAULT_PKI_LISTENER_ROLE,
                common_name=self.settings.MQTT_LISTENER_CLIENT_ID
            )
            cert_pem = cert_response['data']['certificate']
            key_pem = cert_response['data']['private_key']
            
            # Paths for temporary files
            # The full CA chain is read from the pre-generated file in the shared volume.
            ca_file_path = "/vault/file/full_chain_ca.crt"
            cert_file_path = "/tmp/client.crt"
            key_file_path = "/tmp/client.key"

            # Write the client cert and key to temporary files
            with open(cert_file_path, "w") as f:
                f.write(cert_pem)
            with open(key_file_path, "w") as f:
                f.write(key_pem)

            self.client.tls_set(
                ca_certs=ca_file_path, 
                certfile=cert_file_path, 
                keyfile=key_file_path,
                tls_version=ssl.PROTOCOL_TLS
            )
            self.client.tls_insecure_set(False)

            logger.info("TLS context successfully created and set from Vault certificates.")

        except Exception as e:
            logger.error(f"Failed to set up TLS from Vault: {e}", exc_info=True)
            raise

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            logger.info(f"MQTT Listener connected to broker at {self.settings.MQTT_BROKER_HOST}")
            # Clean up temporary certificate files after successful connection
            try:
                os.remove("/tmp/client.crt")
                os.remove("/tmp/client.key")
                logger.info("Temporary certificate files removed.")
            except OSError as e:
                logger.warning(f"Error removing temporary certificate files: {e}")

            self.client.subscribe("telemetry/#", qos=1)
            self.client.subscribe("client/request_state/#", qos=1)
            self.client.subscribe("device/lwt/status/#", qos=1)
            logger.info("MQTT Listener subscribed to `telemetry/#`, `client/request_state/#`, and `device/lwt/status/#`")
        else:
            logger.error(f"MQTT Listener failed to connect, return code {rc}")

    def _on_disconnect(self, client, userdata, rc, properties=None):
        logger.warning(f"MQTT Listener disconnected with code: {rc}. Reconnection will be attempted by loop_forever.")

    def _on_message(self, client, userdata, msg):
        """Delegates message processing to a background thread."""
        future = self.db_executor.submit(self._process_message_task, msg)
        future.add_done_callback(self._task_done_callback)

    def _process_message_task(self, msg):
        """Acts as a router to delegate tasks to the processor module."""
        db = SessionLocal()
        try:
            topic = msg.topic
            try:
                payload = json.loads(msg.payload.decode('utf-8'))
            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON payload from topic {topic}")
                return

            logger.info(f"Routing message from topic: {topic}")
            topic_parts = topic.split('/')

            # Pass necessary clients and data to the processor
            context = {
                "db": db,
                "redis_client": self.redis_client,
                "mqtt_client": self.client
            }

            if topic_parts[0] == 'telemetry':
                processor.handle_telemetry(context, topic, payload)
            elif topic_parts[0] == 'client' and topic_parts[1] == 'request_state':
                processor.handle_state_request(context, topic, payload)
            elif topic_parts[0] == 'device' and topic_parts[1] == 'lwt' and topic_parts[2] == 'status':
                processor.handle_lwt_message(context, topic, payload)
            else:
                logger.warning(f"No handler for topic: {topic}")

        except Exception as e:
            logger.error(f"Error in message processing task for topic {msg.topic}: {e}", exc_info=True)
        finally:
            db.close()

    def _task_done_callback(self, future):
        """Logs exceptions from background tasks."""
        if future.exception() is not None:
            logger.error(f"An error occurred in a background task: {future.exception()}", exc_info=True)

    def run(self):
        """Connects to the MQTT broker and starts the listening loop."""
        logger.info("Attempting to connect MQTT Listener...")
        try:
            self.client.connect(
                self.settings.MQTT_BROKER_HOST, 
                self.settings.MQTT_BROKER_PORT, 
                self.settings.MQTT_KEEPALIVE
            )
            logger.info("Starting MQTT listener loop...")
            self.client.loop_forever()
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, stopping listener.")
        except Exception as e:
            logger.error(f"An error occurred in the listener loop: {e}")
        finally:
            self.stop()

    def stop(self):
        """Stops the MQTT listener gracefully."""
        if not self._stop_event.is_set():
            logger.info("MqttListener is stopping...")
            self._stop_event.set()
            self.db_executor.shutdown(wait=True)
            self.client.disconnect()
            logger.info("MqttListener has stopped.")

if __name__ == '__main__':
    listener = None
    try:
        app_settings = Settings()
        listener = MqttListener(app_settings)
        listener.run()
    except KeyboardInterrupt:
        print("Interrupted by user, shutting down.")
    except Exception as e:
        logger.error(f"Failed to start listener: {e}")
    finally:
        if listener:
            listener.stop()
