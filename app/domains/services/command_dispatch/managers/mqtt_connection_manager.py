import logging
import asyncio
import ssl
import tempfile
import os
import sys
import uuid 
import socket
from typing import Dict, Optional, Any
from gmqtt import Client as MQTTClient
from app.core.config import Settings

logger = logging.getLogger(__name__)

class MqttConnectionManager:
    """
    gmqtt 클라이언트의 기술적인 생명주기를 관리하는 래퍼입니다.
    객체 싱글톤 유지 및 mTLS 보안 설정을 담당합니다.
    """
    def __init__(self, settings: Settings, client_id: str):
        self.settings = settings
        # 1. 고유한 Client ID 생성 (인스턴스 생명주기 동안 고정)
        random_suffix = uuid.uuid4().hex[:8]
        self.client_id = f"{client_id}-{random_suffix}"
        
        # 2. [핵심] 클라이언트 객체는 여기서 '딱 한 번'만 생성합니다.
        self.client = MQTTClient(self.client_id) 
        
        # 3. gmqtt 표준 시그니처에 따른 콜백 등록
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        
        self.is_connected = False
        self._is_manually_disconnecting = False
        self._connection_lock = asyncio.Lock()
        self.cert_data: Optional[Dict] = None
        
        logger.info(f"🆔 Initialized MqttConnectionManager with Unique ID: {self.client_id}")

    def set_certificate_data(self, cert_data: Dict):
        """Policy로부터 mTLS 인증서 데이터를 주입받습니다."""
        self.cert_data = cert_data
        logger.info(f"Certificate data set for MQTT client '{self.client_id}'.")

    # --- gmqtt 표준 콜백 구현 ---

    def _on_connect(self, client: Any, flags: Any, rc: Any, properties: Any):
        if rc == 0:
            self.is_connected = True
            logger.info(f"✅ MQTT client '{self.client_id}' connected successfully. (rc={rc})")
        else:
            self.is_connected = False
            logger.error(f"❌ MQTT connection failed. (rc={rc})")

    def _on_disconnect(self, client: Any, packet: Any, exc: Any = None):
        self.is_connected = False
        if not self._is_manually_disconnecting:
            logger.warning(f"⚠️ Unexpected disconnect for '{self.client_id}'. (exc={exc})")
        else:
            logger.info(f"ℹ️ Manual disconnect finalized for '{self.client_id}'.")

    # --- 내부 로직 및 연결 관리 ---

    def _configure_tls(self) -> ssl.SSLContext:
        """메모리 내 인증서를 임시 파일로 작성하여 SSL Context를 생성합니다."""
        if not self.cert_data:
            raise RuntimeError("Certificate data is not set. Cannot configure TLS.")
        
        cert_file_path, key_file_path = None, None
        temp_dir = '/dev/shm' if sys.platform.startswith('linux') and os.path.exists('/dev/shm') else None
        
        try:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ca_bundle_path = "/app/temp_certs/full_chain_ca.crt"
            
            if os.path.exists(ca_bundle_path):
                context.load_verify_locations(cafile=ca_bundle_path)
            else:
                context.load_verify_locations(cadata=self.cert_data['issuing_ca'])
                
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED
            
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
            logger.error(f"TLS Configuration error: {e}")
            raise
        finally:
            if cert_file_path and os.path.exists(cert_file_path):
                try: os.unlink(cert_file_path)
                except: pass
            if key_file_path and os.path.exists(key_file_path):
                try: os.unlink(key_file_path)
                except: pass

    async def _do_connect(self):
        """[중요] 이미 생성된 self.client를 사용하여 연결만 수행합니다."""
        if self.settings.MQTT_USERNAME:
            self.client.set_auth_credentials(
                self.settings.MQTT_USERNAME, 
                self.settings.MQTT_PASSWORD
            )
        
        ssl_context = self._configure_tls()
        
        logger.info(f"🚀 Attempting connection to {self.settings.MQTT_BROKER_HOST}:{self.settings.MQTT_BROKER_PORT}")
        await self.client.connect(
            host=self.settings.MQTT_BROKER_HOST, 
            port=self.settings.MQTT_BROKER_PORT, 
            ssl=ssl_context,
            keepalive=self.settings.MQTT_KEEPALIVE
        )

    async def connect(self):
        """브로커 가용성을 체크하며 연결될 때까지 재시도 루프를 돕니다."""
        retry_interval = 5
        while True:
            async with self._connection_lock:
                if self.is_connected:
                    return
                
                try:
                    await self._do_connect()
                    return # 연결 성공 시 루프 탈출
                except (socket.gaierror, ConnectionRefusedError, OSError) as e:
                    logger.warning(f"⏳ Broker not ready ({e}). Retrying in {retry_interval}s...")
                except Exception as e:
                    logger.error(f"💥 Critical connection error: {e}", exc_info=True)
            
            await asyncio.sleep(retry_interval)

    async def rotate_certificate(self, new_cert_data: dict):
        """세션 교체 시 안전하게 기존 연결을 끊고 새 인증서로 다시 연결합니다."""
        async with self._connection_lock:
            logger.info(f"🔄 Rotating certificate for {self.client_id}...")
            self.cert_data = new_cert_data
            
            if self.is_connected:
                self._is_manually_disconnecting = True
                await self.client.disconnect()
                await asyncio.sleep(2) # 브로커 세션 정리 시간 확보
                self._is_manually_disconnecting = False
            
            await self._do_connect()

    async def disconnect(self):
        """명시적으로 연결을 해제합니다."""
        if self.is_connected:
            self._is_manually_disconnecting = True
            await self.client.disconnect()
            logger.info(f"👋 MQTT client '{self.client_id}' disconnected by manager.")