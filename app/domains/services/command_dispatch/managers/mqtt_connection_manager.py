import logging
import asyncio
import ssl
import tempfile
import os
import sys
import uuid # [추가] 고유 ID 생성을 위해 필요
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
        
        # ==================================================================
        # [수정 1] Client ID 중복 방지 (가장 중요!)
        # 기존 ID 뒤에 랜덤한 UUID를 붙여서 다른 컨테이너(리스너 등)와 충돌을 방지합니다.
        # ==================================================================
        random_suffix = uuid.uuid4().hex[:8]
        self.client_id = f"{client_id}-{random_suffix}"
        
        self.client: Optional[MQTTClient] = None
        self.cert_data: Optional[Dict] = None
        self.is_connected = False
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
            
            # ==================================================================
            # [수정 2] ACL 테스트를 위한 구독(SUBSCRIBE) 요청
            # 연결 즉시 구독을 시도하여 EMQX가 /acl 웹훅을 호출하게 만듭니다.
            # ==================================================================
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
            # Docker Volume을 통해 공유된 'full_chain_ca.crt' (Root + Intermediate) 파일을 직접 로드합니다.
            ca_bundle_path = "/app/temp_certs/full_chain_ca.crt"
            
            if os.path.exists(ca_bundle_path):
                context.load_verify_locations(cafile=ca_bundle_path)
                logger.info(f"Loaded Full CA Bundle from {ca_bundle_path}")
            else:
                logger.warning(f"Full CA Bundle not found at {ca_bundle_path}. Falling back to issuing_ca string (Might fail strict check).")
                context.load_verify_locations(cadata=self.cert_data['issuing_ca'])

            # 3. 엄격한 검사 유지 (보안 강화)
            context.check_hostname = True 
            context.verify_mode = ssl.CERT_REQUIRED

            # 4. 클라이언트 인증서(Temp File) 로드
            with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.crt', dir=temp_dir) as cert_file, \
                tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.key', dir=temp_dir) as key_file:

                # 파일 권한을 600 (나만 읽기/쓰기)으로 제한하여 보안 강화
                os.chmod(cert_file.name, 0o600)
                os.chmod(key_file.name, 0o600)

                cert_file.write(self.cert_data['certificate'])
                cert_file_path = cert_file.name

                key_file.write(self.cert_data['private_key'])
                key_file_path = key_file.name
                
                # 버퍼를 확실히 비워 내용이 파일시스템에 잡히도록 함
                cert_file.flush()
                key_file.flush()

                # 임시 파일 경로 로딩
                context.load_cert_chain(certfile=cert_file_path, keyfile=key_file_path)

            logger.info("TLS context successfully created.")
            return context
            
        except Exception as e:
            logger.error(f"Failed to configure MQTT TLS for client '{self.client_id}': {e}", exc_info=True)
            raise
        finally:
            # 생성된 임시 파일을 즉시 삭제합니다.
            if cert_file_path and os.path.exists(cert_file_path):
                try: os.unlink(cert_file_path)
                except: pass
            if key_file_path and os.path.exists(key_file_path):
                try: os.unlink(key_file_path)
                except: pass
            logger.debug("Temporary certificate files for MQTT client have been deleted.")

    async def connect(self):
        """
        MQTT 브로커에 비동기적으로 연결을 시도합니다. (Blocking: 실패 시 에러 발생)
        """
        logger.info(f"[Connect] Attempting to acquire connection lock for '{self.client_id}'...")
        async with self._connection_lock:
            if self.is_connected:
                logger.info(f"MQTT client '{self.client_id}' is already connected.")
                return

            if not self.cert_data:
                raise ConnectionError("Cannot connect MQTT client: Certificate data is not set.")

            self.client = MQTTClient(self.client_id)
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect

            # ==================================================================
            # 사용자 인증 정보 설정
            # ==================================================================
            if self.settings.MQTT_USERNAME and self.settings.MQTT_PASSWORD:
                self.client.set_auth_credentials(
                    username=self.settings.MQTT_USERNAME, 
                    password=self.settings.MQTT_PASSWORD
                )
                logger.info(f"Auth credentials set for user: {self.settings.MQTT_USERNAME}")

            ssl_context = self._configure_tls()
            
            try:
                logger.info(f"Attempting to connect MQTT client '{self.client_id}'...")
                await self.client.connect(
                    host=self.settings.MQTT_BROKER_HOST,
                    port=self.settings.MQTT_BROKER_PORT,
                    ssl=ssl_context,
                    keepalive=self.settings.MQTT_KEEPALIVE
                )
            except Exception as e:
                logger.error(f"MQTT Connection failed for client '{self.client_id}': {e}", exc_info=True)
                raise


    async def disconnect(self):
        """
        MQTT 클라이언트 연결을 비동기적으로 중지합니다.
        """
        if self.client and self.is_connected:
            await self.client.disconnect()
            logger.info(f"MQTT client '{self.client_id}' disconnected.")
