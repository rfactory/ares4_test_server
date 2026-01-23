import logging
import asyncio
import ssl
import tempfile
import os
import sys
import uuid 
from typing import Dict, Optional
from gmqtt import Client as MQTTClient
from app.core.config import Settings

logger = logging.getLogger(__name__)

class MqttConnectionManager:
    """
    gmqtt 클라이언트의 기술적인 생명주기(연결/해제)를 관리하는 단순 래퍼입니다.
    인증서 데이터는 외부(Policy)로부터 주입받습니다.
    """
    def __init__(self, settings: Settings, client_id: str):
        self.settings = settings
        random_suffix = uuid.uuid4().hex[:8]
        self.client_id = f"{client_id}-{random_suffix}"
        
        self.client: Optional[MQTTClient] = None
        self.cert_data: Optional[Dict] = None
        self.is_connected = False
        self._is_manually_disconnecting = False # 로테이션 중인지 판별하는 플래그
        self._connection_lock = asyncio.Lock()
        
        logger.info(f"🆔 Initialized MqttConnectionManager with Unique ID: {self.client_id}")

    def set_certificate_data(self, cert_data: Dict):
        """
        Policy로부터 유효한 인증서 데이터를 (문자열 형태로) 주입받습니다.
        """
        self.cert_data = cert_data
        logger.info(f"Certificate data set for MQTT client '{self.client_id}'.")

    def _on_connect(self, client, flags, rc, properties):
        if rc == 0:
            self.is_connected = True
            logger.info(f"✅ MQTT client '{self.client_id}' connected successfully.")
            try:
                target_topic = "test/topic"
                client.subscribe(target_topic, qos=0)
                logger.info(f"📡 Subscribed to '{target_topic}' to trigger ACL check.")
            except Exception as e:
                logger.error(f"Failed to subscribe in on_connect: {e}")
        else:
            self.is_connected = False
            logger.error(f"❌ MQTT client '{self.client_id}' failed to connect, return code {rc}")

    def _on_disconnect(self, client, packet, exc=None):
        self.is_connected = False
        logger.warning(f"⚠️ MQTT client '{self.client_id}' disconnected. (exc={exc})")

    def _configure_tls(self) -> ssl.SSLContext:
        if not self.cert_data:
            raise RuntimeError("Certificate data is not set. Cannot configure TLS.")
        
        logger.info("Configuring TLS for MQTT client...")
        cert_file_path, key_file_path = None, None
        
        # 리눅스 환경(Docker)인 경우 /dev/shm (RAM Disk) 사용
        temp_dir = '/dev/shm' if sys.platform.startswith('linux') and os.path.exists('/dev/shm') else None
        
        try:
            # 1. SSL 컨텍스트 생성 (기본값: Strict Mode)
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            
            # 2. [Strict Mode] 족보(Full Chain CA) 파일 로드
            ca_bundle_path = "/app/temp_certs/full_chain_ca.crt"
            
            if os.path.exists(ca_bundle_path):
                context.load_verify_locations(cafile=ca_bundle_path)
                logger.info(f"Loaded Full CA Bundle from {ca_bundle_path}")
            else:
                logger.warning(f"Full CA Bundle not found at {ca_bundle_path}. Falling back to issuing_ca string.")
                context.load_verify_locations(cadata=self.cert_data['issuing_ca'])
                
            # 3. 엄격한 검사 유지 (보안 강화)
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED
            
            # 4. 클라이언트 인증서(Temp File) 로드
            with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.crt', dir=temp_dir) as cert_file, \
                tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.key', dir=temp_dir) as key_file:
                
                os.chmod(cert_file.name, 0o600)
                os.chmod(key_file.name, 0o600)
                
                cert_file.write(self.cert_data['certificate'])
                key_file.write(self.cert_data['private_key'])
                
                cert_file.flush()
                key_file.flush()
                
                cert_file_path = cert_file.name
                key_file_path = key_file.name
                
                context.load_cert_chain(certfile=cert_file_path, keyfile=key_file_path)
                
            return context
            
        except Exception as e:
            logger.error(f"Failed to configure MQTT TLS for client '{self.client_id}': {e}", exc_info=True)
            raise
        finally:
            # 생성된 임시 파일을 즉시 삭제하여 보안 강화
            if cert_file_path and os.path.exists(cert_file_path):
                try: os.unlink(cert_file_path)
                except: pass
            if key_file_path and os.path.exists(key_file_path):
                try: os.unlink(key_file_path)
                except: pass

    async def _do_connect(self):
        """실제 브로커 연결을 수행하는 내부 메서드"""
        self.client = MQTTClient(self.client_id)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        
        if self.settings.MQTT_USERNAME:
            self.client.set_auth_credentials(self.settings.MQTT_USERNAME, self.settings.MQTT_PASSWORD)
            logger.info(f"Auth credentials set for user: {self.settings.MQTT_USERNAME}")
        
        ssl_context = self._configure_tls()
        
        logger.info(f"Attempting to connect MQTT client '{self.client_id}'...")
        await self.client.connect(
            host=self.settings.MQTT_BROKER_HOST, 
            port=self.settings.MQTT_BROKER_PORT, 
            ssl=ssl_context,
            keepalive=self.settings.MQTT_KEEPALIVE
        )

    async def connect(self):
        """
        MQTT 브로커에 비동기적으로 연결을 시도합니다. (Blocking: 실패 시 에러 발생)
        """
        async with self._connection_lock:
            if self.is_connected:
                logger.info(f"MQTT client '{self.client_id}' is already connected.")
                return
            
            if not self.cert_data:
                raise ConnectionError("Cannot connect MQTT client: Certificate data is not set.")
            
            try:
                await self._do_connect()
            except Exception as e:
                logger.error(f"MQTT Connection failed for client '{self.client_id}': {e}", exc_info=True)
                raise

    async def rotate_certificate(self, new_cert_data: dict):
        """세션을 유지하며 새로운 mTLS 인증서로 교체"""
        async with self._connection_lock:
            logger.info(f"🔄 Rotating certificate for {self.client_id}...")
            self.cert_data = new_cert_data
            
            if self.client and self.is_connected:
                self._is_manually_disconnecting = True
                await self.client.disconnect()
                await asyncio.sleep(2) # 브로커 세션 정리를 위한 잠시 대기
                self._is_manually_disconnecting = False
            
            # 새 인증서로 즉시 연결 시도
            await self._do_connect()

    async def disconnect(self):
        """
        MQTT 클라이언트 연결을 비동기적으로 중지합니다.
        """
        if self.client and self.is_connected:
            await self.client.disconnect()
            logger.info(f"MQTT client '{self.client_id}' disconnected.")