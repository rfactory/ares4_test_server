import asyncio
import os
import ssl
import tempfile
from paho.mqtt import client as mqtt
from app.core.config import settings

# Global list to keep track of temporary certificate files
_temp_cert_files = []

async def connect_mqtt_background():
    broker = settings.MQTT_BROKER_HOST
    port = settings.MQTT_BROKER_PORT
    username = settings.MQTT_USERNAME
    password = settings.MQTT_PASSWORD
    client_id = settings.MQTT_CLIENT_ID

    mqtt_client = mqtt.Client(client_id=client_id)
    mqtt_client.username_pw_set(username, password)

    # --- Configure TLS using certificate contents from settings ---
    if settings.MQTT_CA_CERT_CONTENT and settings.MQTT_CLIENT_CERT_CONTENT and settings.MQTT_CLIENT_KEY_CONTENT:
        try:
            # Write certificate contents to temporary files
            ca_cert_file = tempfile.NamedTemporaryFile(delete=False, mode='w')
            ca_cert_file.write(settings.MQTT_CA_CERT_CONTENT)
            ca_cert_file.close()
            _temp_cert_files.append(ca_cert_file.name)

            client_cert_file = tempfile.NamedTemporaryFile(delete=False, mode='w')
            client_cert_file.write(settings.MQTT_CLIENT_CERT_CONTENT)
            client_cert_file.close()
            _temp_cert_files.append(client_cert_file.name)

            client_key_file = tempfile.NamedTemporaryFile(delete=False, mode='w')
            client_key_file.write(settings.MQTT_CLIENT_KEY_CONTENT)
            client_key_file.close()
            _temp_cert_files.append(client_key_file.name)

            mqtt_client.tls_set(
                ca_certs=ca_cert_file.name, 
                certfile=client_cert_file.name, 
                keyfile=client_key_file.name,
                tls_version=ssl.PROTOCOL_TLS_CLIENT
            )
            print("MQTT TLS configured successfully using Vault secrets and temporary files.")

        except Exception as e:
            print(f"Error configuring MQTT TLS: {e}. Proceeding without TLS.")
            # Clean up any files created if TLS setup fails
            disconnect_mqtt() # This will clean up temp files

    else:
        print("MQTT TLS not configured: Certificate contents not found in settings.")

    connected = False
    while not connected:
        try:
            mqtt_client.connect(broker, port, 60)
            connected = True
            print("MQTT connected successfully.")
        except Exception as e:
            print(f"Error: {e}. Retrying in 10 seconds...")
            await asyncio.sleep(10)

    mqtt_client.loop_start()
    return mqtt_client

def disconnect_mqtt():
    """
    Disconnects the global MQTT client and cleans up temporary certificate files.
    """
    print("Disconnecting MQTT client and cleaning up temporary files...")
    for path in _temp_cert_files:
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError as e:
                print(f"Error removing temp file {path}: {e}")
    _temp_cert_files.clear()
    # Add actual MQTT client disconnect logic here if needed