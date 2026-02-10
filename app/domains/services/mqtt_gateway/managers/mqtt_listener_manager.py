import logging
import ssl
import tempfile
import os
import sys
import uuid
import asyncio
from typing import Dict, Optional, Callable

from gmqtt import Client as MQTTClient
from app.core.config import Settings

logger = logging.getLogger(__name__)

class MqttListenerManager:
    """
    gmqtt 클라이언트의 기술적인 생명주기(연결, TLS, 루프)만 관리합니다.
    메시지 처리에 대한 로직은 포함하지 않습니다.
    """
    def __init__(self, settings: Settings, client_id: str):
        self.settings = settings
        random_suffix = uuid.uuid4().hex[:8]
        self.client_id = f"{client_id}-{random_suffix}"
        self.client: Optional[MQTTClient] = None
        self.cert_data: Optional[Dict] = None
        self.is_connected = False
        self._connection_lock = asyncio.Lock()
        logger.info(f"🆔 Initialized MqttListenerManager with Unique ID: {self.client_id}")

    def set_certificate_data(self, cert_data: Dict):
        """
        Policy로부터 유효한 인증서 데이터를 (문자열 형태로) 주입받습니다.
        """
        self.cert_data = cert_data
        logger.info(f"Certificate data set for MQTT listener '{self.client_id}'.")

    def _configure_tls(self) -> ssl.SSLContext:
        if not self.cert_data:
            raise RuntimeError("Certificate data is not set. Cannot configure TLS.")

        logger.info("Configuring TLS for MQTT listener...")
        
        cert_file_path, key_file_path = None, None
        temp_dir = '/dev/shm' if sys.platform.startswith('linux') and os.path.exists('/dev/shm') else None

        try:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ca_bundle_path = "/app/temp_certs/full_chain_ca.crt"
            
            if os.path.exists(ca_bundle_path):
                context.load_verify_locations(cafile=ca_bundle_path)
                logger.info(f"Loaded Full CA Bundle from {ca_bundle_path}")
            else:
                logger.warning(f"Full CA Bundle not found at {ca_bundle_path}. Falling back to issuing_ca string.")
                context.load_verify_locations(cadata=self.cert_data['issuing_ca'])

            context.check_hostname = True 
            context.verify_mode = ssl.CERT_REQUIRED

            with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.crt', dir=temp_dir) as cert_file, \
                tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.key', dir=temp_dir) as key_file:

                os.chmod(cert_file.name, 0o600)
                os.chmod(key_file.name, 0o600)

                cert_file.write(self.cert_data['certificate'])
                cert_file_path = cert_file.name

                key_file.write(self.cert_data['private_key'])
                key_file_path = key_file.name
                
                cert_file.flush()
                key_file.flush()

                context.load_cert_chain(certfile=cert_file_path, keyfile=key_file_path)

            logger.info("TLS context successfully created for listener.")
            return context
            
        except Exception as e:
            logger.error(f"Failed to configure MQTT TLS for listener '{self.client_id}': {e}", exc_info=True)
            raise
        finally:
            if cert_file_path and os.path.exists(cert_file_path):
                try: os.unlink(cert_file_path)
                except: pass
            if key_file_path and os.path.exists(key_file_path):
                try: os.unlink(key_file_path)
                except: pass
            logger.debug("Temporary certificate files for MQTT listener have been deleted.")

    def _on_connect(self, client, flags, rc, properties):
        if rc == 0:
            self.is_connected = True
            logger.info(f"MQTT Listener '{self.client_id}' connected successfully.")
            
            # 1. 명령 및 상태 요청
            client.subscribe("client/request_state/#", qos=1)
            client.subscribe("commands/response/#", qos=1)
            
            # 2. [부활!] 실시간 모니터링(Frontend용 Redis 캐싱)을 위해 텔레메트리도 듣습니다.
            # 부하 걱정 NO! Redis 저장은 매우 빠릅니다.
            client.subscribe("ares4/+/telemetry", qos=1)
            
            logger.info(f"📡 MQTT Listener subscribed to Commands AND Telemetry (Hot Path for Redis).")
        else:
            self.is_connected = False
            logger.error(f"MQTT Listener '{self.client_id}' failed to connect, return code {rc}")
    
    def _on_disconnect(self, client, packet, exc=None):
        self.is_connected = False
        logger.warning(f"MQTT Listener '{self.client_id}' disconnected with exception: {exc}.")

    async def connect(self, on_message_callback: Callable):
        """
        MQTT 브로커에 비동기적으로 연결을 시도합니다. on_message 콜백은 외부에서 주입받습니다.
        """
        async with self._connection_lock:
            if self.is_connected:
                logger.info(f"MQTT listener '{self.client_id}' is already connected.")
                return

            if not self.cert_data:
                raise ConnectionError("Cannot connect MQTT listener: Certificate data is not set.")
            
            self.client = MQTTClient(self.client_id)
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = on_message_callback

            if self.settings.MQTT_USERNAME and self.settings.MQTT_PASSWORD:
                self.client.set_auth_credentials(
                    username=self.settings.MQTT_USERNAME, 
                    password=self.settings.MQTT_PASSWORD
                )
                logger.info(f"Auth credentials set for listener user: {self.settings.MQTT_USERNAME}")

            ssl_context = self._configure_tls()

            try:
                logger.info(f"Attempting to connect MQTT listener '{self.client_id}'...")
                await self.client.connect(
                    host=self.settings.MQTT_BROKER_HOST,
                    port=self.settings.MQTT_BROKER_PORT,
                    ssl=ssl_context,
                    keepalive=self.settings.MQTT_KEEPALIVE
                )
            except Exception as e:
                logger.error(f"MQTT Connection failed for listener '{self.client_id}': {e}", exc_info=True)
                raise
    
    async def disconnect(self):
        """
        Stops the network loop and disconnects.
        """
        if self.client and self.is_connected:
            logger.info("Stopping MQTT listener...")
            await self.client.disconnect()